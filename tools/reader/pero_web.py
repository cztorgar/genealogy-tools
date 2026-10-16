#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31", "pillow>=10"]
# ///
"""Klient webové aplikace PERO OCR (https://pero-ocr.fit.vutbr.cz/) přes uživatelský účet.

Nezávislé „třetí čtení“ rukopisu pro reader. Postup odpovídá UI aplikace (DCGM/pero_ocr_web):
login (CSRF) → nový dokument → upload snímku → layout analýza → OCR → export PAGE XML + text → smazání.

Přístupy: ~/.config/pero/credentials (email=…, password=…, práva 600). Cookie relace se drží
v ~/.config/pero/session.json (600). Heslo se nikdy nevypisuje ani neloguje.

Šetrně: jeden dokument najednou, prodleva mezi požadavky, stav se dotazuje po POLL_S sekundách.
Podmínky: aplikace je zdarma pro osobní použití a použití s ruční opravou textu.

  uv run tools/reader/pero_web.py engines
  uv run tools/reader/pero_web.py ocr snimek.jpg [--engine …] [--layout …] [--crop x,y,w,h] [--out DIR] [--keep]

Výstup (pro skills/read-record a tools/reader/compare.py):
  <snímek>.pero.xml   PAGE XML (regiony, řádky, polygony, baseline, conf řádku) — souřadnice vždy
                      v pixelech PŮVODNÍHO snímku (u --crop posunuté zpět)
  <snímek>.pero.txt   jeden řádek textu = jeden řádek, za tabulátorem confidence řádku (0–1)
  <snímek>.pero.json  metadata běhu (enginy, dokument, crop) + řádky s bbox
  uv run tools/reader/pero_web.py documents | delete <document_id>
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE = "https://pero-ocr.fit.vutbr.cz"
CONF_DIR = Path.home() / ".config" / "pero"
CREDENTIALS = CONF_DIR / "credentials"
SESSION_FILE = CONF_DIR / "session.json"
USER_AGENT = "genealogy-workbench/0.1 (pero_web.py; osobni pouziti)"

MIN_INTERVAL_S = 2.0      # mezi dvěma požadavky na server
POLL_S = 15.0             # dotaz na stav zpracování
TIMEOUT_S = 30 * 60       # max. čekání na layout / OCR

# Výchozí enginy podle názvu (case-insensitive podřetězec) — ověřeno na živém webu, viz docs/nastroje/pero.md.
DEFAULT_LAYOUT = "Complex printed and handwritten layout"
DEFAULT_OCR = "czech handwritten"
DEFAULT_LM = "none"

# Stavy dokumentu (app/db/model.py: DocumentState)
ST_NEW = "New"
ST_LAYOUT_DONE = "Layout analysis completed."
ST_OCR_DONE = "OCR completed."
ST_WAITING = {"Waiting on start of layout analysis.", "Running layout analysis.",
              "Waiting on start of OCR.", "Running OCR."}

PAGE_NS = {"pc": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}


class PeroError(RuntimeError):
    pass


def _read_credentials() -> tuple[str, str]:
    if not CREDENTIALS.exists():
        raise PeroError(f"Chybí {CREDENTIALS} (email=…, password=…, chmod 600).")
    if CREDENTIALS.stat().st_mode & 0o077:
        raise PeroError(f"{CREDENTIALS} musí mít práva 600.")
    vals = {}
    for line in CREDENTIALS.read_text(encoding="utf-8").splitlines():
        k, sep, v = line.partition("=")
        if sep:
            vals[k.strip()] = v.strip()
    if not vals.get("email") or not vals.get("password"):
        raise PeroError(f"{CREDENTIALS}: chybí email nebo password.")
    return vals["email"], vals["password"]


def _hidden_csrf(page: str) -> str | None:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)
    return m.group(1) if m else None


def _check_bot_protection(resp: requests.Response) -> None:
    low = resp.text[:20000].lower() if "text" in resp.headers.get("content-type", "") else ""
    if resp.status_code in (403, 429) or any(s in low for s in ("captcha", "cf-challenge", "turnstile")):
        raise PeroError(f"Server vrátil {resp.status_code} / ochranu proti robotům ({resp.url}) — "
                        "zastavuji, neobcházet.")


def _options(page: str, select_name: str) -> list[dict]:
    """<select name=…> → [{id, name, description, selected}] (bez HTML parseru)."""
    m = re.search(rf'<select[^>]*name="{select_name}"[^>]*>(.*?)</select>', page, re.S)
    if not m:
        return []
    out = []
    for om in re.finditer(r"<option([^>]*)>(.*?)</option>", m.group(1), re.S):
        attrs, label = om.group(1), om.group(2)
        val = re.search(r'value="([^"]*)"', attrs)
        desc = re.search(r'data-description="([^"]*)"', attrs)
        out.append({"id": val.group(1) if val else "",
                    "name": html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", "", label))).strip(),
                    "description": html.unescape(desc.group(1)).strip() if desc else "",
                    "selected": "selected" in attrs})
    return out


def _pick(options: list[dict], wanted: str | None, what: str) -> dict:
    if not options:
        raise PeroError(f"Na stránce není nabídka {what}.")
    if wanted:
        for o in options:                         # přesné ID
            if o["id"] == wanted:
                return o
        hits = [o for o in options if wanted.lower() in o["name"].lower()]
        if len(hits) == 1:
            return hits[0]
        if hits:
            exact = [o for o in hits if o["name"].lower() == wanted.lower()]
            if exact:
                return exact[0]
            raise PeroError(f"{what}: '{wanted}' je nejednoznačné: {[o['name'] for o in hits]}")
        raise PeroError(f"{what}: '{wanted}' nenalezeno; dostupné: {[o['name'] for o in options]}")
    return next((o for o in options if o["selected"]), options[0])


class PeroWeb:
    def __init__(self, verbose: bool = True):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self._last = 0.0
        self.verbose = verbose
        self._load_session()

    # --- HTTP ------------------------------------------------------------------------------------
    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[pero] {msg}", file=sys.stderr)

    def _req(self, method: str, path: str, **kw) -> requests.Response:
        wait = MIN_INTERVAL_S - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        kw.setdefault("timeout", 120)
        r = self.s.request(method, BASE + path, **kw)
        self._last = time.monotonic()
        _check_bot_protection(r)
        return r

    def _load_session(self) -> None:
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            for c in data.get("cookies", []):
                self.s.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/"))
        except (OSError, ValueError, KeyError):
            pass

    def _save_session(self) -> None:
        CONF_DIR.mkdir(mode=0o700, exist_ok=True)
        cookies = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path} for c in self.s.cookies]
        fd = os.open(SESSION_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"saved": dt.datetime.now().isoformat(timespec="seconds"), "cookies": cookies}, f)

    # --- přihlášení ------------------------------------------------------------------------------
    def _logged_in(self) -> bool:
        r = self._req("GET", "/document/user_documents", allow_redirects=False)
        return r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json")

    def login(self) -> None:
        if self.s.cookies and self._logged_in():
            return
        self.s.cookies.clear()
        email, password = _read_credentials()
        page = self._req("GET", "/").text
        token = _hidden_csrf(page)
        if not token:
            raise PeroError("Login formulář bez csrf_token — změnil se web?")
        self._req("POST", "/auth/login", data={"csrf_token": token, "email": email,
                                                 "password": password, "submit": "Login"})
        del password
        if not self._logged_in():
            raise PeroError("Přihlášení selhalo (špatné údaje nebo změněný formulář).")
        self._save_session()
        self._log("přihlášeno")

    # --- dokumenty -------------------------------------------------------------------------------
    def documents(self) -> list[dict]:
        r = self._req("GET", "/document/user_documents", allow_redirects=False)
        if r.status_code != 200:
            raise PeroError(f"user_documents: HTTP {r.status_code}")
        return r.json()

    def document(self, document_id: str) -> dict:
        for d in self.documents():
            if d["id"] == document_id:
                return d
        raise PeroError(f"Dokument {document_id} nenalezen.")

    def ensure_document(self, name: str) -> str:
        for d in self.documents():
            if d["name"] == name:
                return d["id"]
        page = self._req("GET", "/document/new_document").text
        token = _hidden_csrf(page)
        r = self._req("POST", "/document/new_document",
                      data={"csrf_token": token or "", "document_name": name, "submit": "Create"})
        m = re.search(r"/document/upload_images_to_document/([0-9a-f-]{36})", r.url)
        if m:
            doc_id = m.group(1)
        else:
            doc_id = next((d["id"] for d in self.documents() if d["name"] == name), None)
            if not doc_id:
                raise PeroError(f"Dokument '{name}' se nepodařilo vytvořit.")
        self._log(f"dokument {name} = {doc_id}")
        return doc_id

    def upload(self, document_id: str, images: list[Path]) -> list[str]:
        for img in images:
            with img.open("rb") as f:
                r = self._req("POST", f"/document/upload_image_to_document/{document_id}",
                              files={"file": (img.name, f, "image/jpeg" if img.suffix.lower() in
                                              (".jpg", ".jpeg") else "application/octet-stream")})
            if r.status_code == 409 and "already uploaded" in r.text:
                self._log(f"{img.name}: už nahráno")
            elif r.status_code != 200:
                raise PeroError(f"upload {img.name}: HTTP {r.status_code} {r.text[:200]}")
            else:
                self._log(f"nahráno {img.name}")
        return self.image_ids(document_id)

    def image_ids(self, document_id: str) -> list[str]:
        return self._req("GET", f"/document/get_document_image_ids/{document_id}").json()

    def delete(self, document_id: str) -> None:
        r = self._req("GET", f"/document/delete_document/{document_id}")
        if r.status_code != 200:
            raise PeroError(f"delete: HTTP {r.status_code}")
        self._log(f"dokument {document_id} smazán")

    # --- enginy a zpracování ---------------------------------------------------------------------
    def engines(self, document_id: str) -> dict:
        lp = self._req("GET", f"/layout_analysis/select_layout/{document_id}").text
        op = self._req("GET", f"/ocr/select_ocr/{document_id}").text
        return {"layout": _options(lp, "layout_detector_id"), "baseline": _options(op, "baseline_id"),
                "ocr": _options(op, "ocr_id"), "language_model": _options(op, "language_model_id")}

    def run_layout(self, document_id: str, layout: str | None = DEFAULT_LAYOUT) -> dict:
        lp = self._req("GET", f"/layout_analysis/select_layout/{document_id}").text
        det = _pick(_options(lp, "layout_detector_id"), layout, "layout detektor")
        data = {"layout_detector_id": det["id"]}
        if tok := _hidden_csrf(lp):
            data["csrf_token"] = tok
        self._req("POST", f"/layout_analysis/start_layout/{document_id}", data=data)
        self._log(f"layout: {det['name']}")
        return det

    def run_ocr(self, document_id: str, engine: str | None = DEFAULT_OCR, lm: str | None = DEFAULT_LM) -> dict:
        op = self._req("GET", f"/ocr/select_ocr/{document_id}").text
        ocr = _pick(_options(op, "ocr_id"), engine, "OCR engine")
        lmo = _pick(_options(op, "language_model_id"), lm, "jazykový model")
        data = {"ocr_id": ocr["id"], "language_model_id": lmo["id"]}
        # baseline_id formulář posílá jen u dokumentu bez layoutu; po layout analýze ho vynecháme.
        if tok := _hidden_csrf(op):
            data["csrf_token"] = tok
        self._req("POST", f"/ocr/start_ocr/{document_id}", data=data)
        self._log(f"OCR: {ocr['name']} (LM: {lmo['name']})")
        return {"ocr": ocr, "language_model": lmo}

    def wait(self, document_id: str, target: str, timeout: float = TIMEOUT_S) -> dict:
        t0 = time.monotonic()
        last = None
        while True:
            d = self.document(document_id)
            if d["state"] != last:
                self._log(f"stav: {d['state']}")
                last = d["state"]
            if d["state"] == target:
                return d
            if d["state"] not in ST_WAITING and time.monotonic() - t0 > 3 * POLL_S:
                raise PeroError(f"Neočekávaný stav '{d['state']}' (čekám na '{target}').")
            if time.monotonic() - t0 > timeout:
                raise PeroError(f"Timeout {timeout:.0f} s, stav '{d['state']}'.")
            time.sleep(POLL_S)

    # --- export ----------------------------------------------------------------------------------
    def export(self, document_id: str) -> list[dict]:
        """Pro každý snímek: PAGE XML (řádky, polygony, baseline, confidence), text a řádky s confidence."""
        out = []
        for image_id in self.image_ids(document_id):
            xml = self._req("GET", f"/document/get_page_xml_lines/{image_id}").text
            text = self._req("GET", f"/document/get_text/{image_id}").text
            out.append({"image_id": image_id, "page_xml": xml, "text": text, "lines": page_lines(xml)})
        return out


def page_lines(page_xml: str) -> list[dict]:
    """PAGE XML → [{region, id, text, conf, bbox}] v pořadí aplikace (conf = 15% kvantil znaků)."""
    root = ET.fromstring(page_xml.encode("utf-8"))
    ns = {"pc": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else PAGE_NS
    lines = []
    for reg in root.iter(f"{{{ns['pc']}}}TextRegion"):
        for tl in reg.findall("pc:TextLine", ns):
            te = tl.find("pc:TextEquiv", ns)
            uni = te.find("pc:Unicode", ns) if te is not None else None
            conf = te.get("conf") if te is not None else None
            coords = tl.find("pc:Coords", ns)
            bbox = None
            if coords is not None and coords.get("points"):
                pts = [tuple(map(float, p.split(","))) for p in coords.get("points").split()]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                bbox = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
            lines.append({"region": reg.get("id"), "id": tl.get("id"),
                          "text": (uni.text or "") if uni is not None else "",
                          "conf": float(conf) if conf else None, "bbox": bbox})
    return lines


def shift_page_xml(page_xml: str, dx: int, dy: int, width: int, height: int, filename: str) -> str:
    """Posune všechny points="x,y …" o (dx, dy) a nastaví rozměry/název původního snímku."""
    def pts(m: re.Match) -> str:
        moved = []
        for p in m.group(1).split():
            x, y = p.split(",")
            moved.append(f"{round(float(x)) + dx},{round(float(y)) + dy}")
        return f'points="{" ".join(moved)}"'
    s = re.sub(r'points="([^"]*)"', pts, page_xml)
    s = re.sub(r'imageWidth="\d+"', f'imageWidth="{width}"', s, count=1)
    s = re.sub(r'imageHeight="\d+"', f'imageHeight="{height}"', s, count=1)
    return re.sub(r'imageFilename="[^"]*"', f'imageFilename="{html.escape(filename)}"', s, count=1)


def _crop(image: Path, crop: tuple[int, int, int, int], tmp_dir: Path) -> tuple[Path, tuple[int, int]]:
    from PIL import Image
    x, y, w, h = crop
    with Image.open(image) as im:
        size = im.size
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > size[0] or y + h > size[1]:
            raise PeroError(f"--crop {crop} mimo snímek {size[0]}×{size[1]}.")
        out = tmp_dir / f"{image.stem}-crop-{x}-{y}-{w}-{h}.jpg"
        im.crop((x, y, x + w, y + h)).convert("RGB").save(out, quality=95)
    return out, size


def ocr_image(image: Path, out_dir: Path, engine: str | None, layout: str | None, lm: str | None,
              keep: bool = False, crop: tuple[int, int, int, int] | None = None) -> dict:
    import tempfile
    pw = PeroWeb()
    pw.login()
    name = f"workbench-{dt.date.today().isoformat()}-{uuid.uuid4().hex[:8]}"
    tmp = tempfile.TemporaryDirectory(prefix="pero-")
    upload_img, orig_size = image, None
    if crop:
        upload_img, orig_size = _crop(image, crop, Path(tmp.name))
    doc_id = pw.ensure_document(name)
    try:
        pw.upload(doc_id, [upload_img])
        det = pw.run_layout(doc_id, layout)
        pw.wait(doc_id, ST_LAYOUT_DONE)
        used = pw.run_ocr(doc_id, engine, lm)
        pw.wait(doc_id, ST_OCR_DONE)
        pages = pw.export(doc_id)
    finally:
        if not keep:
            try:
                pw.delete(doc_id)
            except Exception as e:  # noqa: BLE001 — smazání je best-effort
                pw._log(f"smazání selhalo: {e}")
        tmp.cleanup()
    page = pages[0]
    xml = page["page_xml"]
    if crop:
        xml = shift_page_xml(xml, crop[0], crop[1], orig_size[0], orig_size[1], image.name)
    lines = page_lines(xml)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / image.stem
    Path(f"{stem}.pero.xml").write_text(xml, encoding="utf-8")
    Path(f"{stem}.pero.txt").write_text(
        "".join(f"{l['text']}\t{l['conf']:.3f}\n" if l["conf"] is not None else f"{l['text']}\n" for l in lines),
        encoding="utf-8")
    meta = {"backend": "pero-web", "url": BASE, "source_image": str(image),
            "date": dt.datetime.now().isoformat(timespec="seconds"),
            "crop": list(crop) if crop else None,
            "document": {"name": name, "id": doc_id, "kept": keep},
            "layout": det["name"], "ocr": used["ocr"]["name"], "language_model": used["language_model"]["name"],
            "lines": lines}
    Path(f"{stem}.pero.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ocr", help="přečíst jeden snímek")
    o.add_argument("image", type=Path)
    o.add_argument("--engine", default=DEFAULT_OCR, help=f"OCR engine (podřetězec názvu nebo ID; {DEFAULT_OCR!r})")
    o.add_argument("--layout", default=DEFAULT_LAYOUT, help=f"layout detektor ({DEFAULT_LAYOUT!r})")
    o.add_argument("--lm", default=DEFAULT_LM, help=f"jazykový model ({DEFAULT_LM!r})")
    o.add_argument("--out", type=Path, help="výstupní adresář (výchozí: vedle snímku)")
    o.add_argument("--crop", help="výřez x,y,w,h v pixelech původního snímku (odešle se jen výřez)")
    o.add_argument("--keep", action="store_true", help="dokument na serveru nemazat")
    sub.add_parser("engines", help="vypsat dostupné enginy (vytvoří a smaže prázdný dokument)")
    sub.add_parser("documents", help="vypsat dokumenty účtu")
    d = sub.add_parser("delete", help="smazat dokument")
    d.add_argument("document_id")
    a = ap.parse_args()

    try:
        if a.cmd == "ocr":
            crop = None
            if a.crop:
                try:
                    crop = tuple(int(v) for v in a.crop.split(","))
                    assert len(crop) == 4
                except (ValueError, AssertionError):
                    raise PeroError("--crop čeká x,y,w,h (celá čísla).")
            meta = ocr_image(a.image, a.out or a.image.parent, a.engine, a.layout, a.lm, a.keep, crop)
            print(f"{len(meta['lines'])} řádků → {(a.out or a.image.parent) / a.image.stem}.pero.(xml|txt|json)")
            return 0
        pw = PeroWeb()
        pw.login()
        if a.cmd == "documents":
            for doc in pw.documents():
                print(f"{doc['id']}  {doc['state']:<38} {doc['name']}")
        elif a.cmd == "delete":
            pw.delete(a.document_id)
        elif a.cmd == "engines":
            doc_id = pw.ensure_document(f"workbench-{dt.date.today().isoformat()}-engines")
            try:
                for kind, opts in pw.engines(doc_id).items():
                    print(f"## {kind}")
                    for op in opts:
                        print(f"  {'*' if op['selected'] else ' '} {op['id']}  {op['name']}"
                              + (f"\n      {op['description']}" if op["description"] else ""))
            finally:
                pw.delete(doc_id)
        return 0
    except PeroError as e:
        print(f"pero_web: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
