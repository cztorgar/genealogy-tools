#!/usr/bin/env python3
"""Zapíše schválený patch (patches/P-<ID>-<nn>.yml) do Gramps (strom berescak).

Patch musí mít `status: schváleno` (schvaluje uživatel), jinak `--approve` (manager po výslovném
souhlasu uživatele v session) — status se pak nastaví sám. Po zápisu: `status: aplikováno`,
`applied:` s handly; v dossieru `stav: zapsáno` jen pokud byl `dokončeno` (průběžné patche stav nemění).

Podporované operace: add_event (osoba nebo `family: [K6, K7]`), update_event (type/description/date/place
existující události), add_citation / remove_citation (k existující události), update_citation
(page/confidence podle Gramps ID citace), add_note (k události nebo osobě), add_media. Zdroj = dokument
ze sidecaru (`sources/<ID>/<doklad>.yml`), jeden Gramps Source na doklad (Gramps ID `S-<doklad>`),
citace s jistotou, k citaci se připojí médium. Místa se zakládají podle názvu (hierarchie později).

Použití: apply_patch.py <strom-dir> <patches/P-K0007-01.yml> [--approve] [--dry-run]
"""
from __future__ import annotations

import mimetypes
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gw import GrampsWeb  # noqa: E402

MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
MODIFIERS = {"BEF": 1, "AFT": 2, "ABT": 3, "EST": 3, "CAL": 3}
QUALITY = {"EST": 1, "CAL": 2}


def norm_id(pid: str) -> str:
    """K7 → K0007, K0001-S1 zůstává."""
    m = re.fullmatch(r"K?0*(\d+)(-.*)?", str(pid).strip().upper())
    return f"K{int(m[1]):04d}{m[2] or ''}" if m else str(pid)


def _dmy(parts: list[str]) -> list:
    day = month = 0
    year = int(parts[-1])
    if len(parts) >= 2:
        month = MONTHS[parts[-2]]
    if len(parts) == 3:
        day = int(parts[0])
    return [day, month, year, False]


def gramps_date(text: str | None) -> dict | None:
    """GEDCOM-like datum → Gramps Date: '18 SEP 1940', 'ABT 1853', 'MAR 1990',
    'FROM 1882 TO 1921' (období, span), 'BET 1850 AND 1855' (rozmezí, range), 'FROM 1882' / 'TO 1921'."""
    if not text:
        return None
    up = str(text).upper().split()
    if up[0] in ("FROM", "BET") and ("TO" in up or "AND" in up):
        sep = "TO" if up[0] == "FROM" else "AND"
        i = up.index(sep)
        return {"_class": "Date", "calendar": 0, "modifier": 5 if sep == "TO" else 4, "quality": 0,
                "dateval": _dmy(up[1:i]) + _dmy(up[i + 1:]), "text": "", "sortval": 0, "newyear": 0}
    if up[0] in ("FROM", "TO"):
        return {"_class": "Date", "calendar": 0, "modifier": 7 if up[0] == "FROM" else 8, "quality": 0,
                "dateval": _dmy(up[1:]), "text": "", "sortval": 0, "newyear": 0}
    parts = up
    mod = MODIFIERS.get(parts[0], 0)
    qual = QUALITY.get(parts[0], 0)
    if parts[0] in MODIFIERS:
        parts = parts[1:]
    day = month = 0
    year = int(parts[-1])
    if len(parts) >= 2:
        month = MONTHS[parts[-2]]
    if len(parts) == 3:
        day = int(parts[0])
    return {"_class": "Date", "calendar": 0, "modifier": mod, "quality": qual,
            "dateval": [day, month, year, False], "text": "", "sortval": 0, "newyear": 0}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()


# typy událostí, které v české lokalizaci Gramps znamenají něco jiného, než se čeká
TYPE_FORBIDDEN = {
    "Baptism": "v češtině Gramps = „Baptistické křtiny“; ř. k. (i evangelický) křest dítěte = Christening („Křest“)",
}

BOOKS = {"N": "matrika narozených", "O": "matrika oddaných", "Z": "matrika zemřelých", "I": "index"}


def source_title(meta: dict) -> str:
    """Název zdroje: oficiální citace svazku od archivu (sidecar z czech-archives), jinak matrika = svazek
    (archiv, farnost, kniha, roky), doklad = typ + zápis."""
    if meta.get("official_citation"):
        return f"{meta.get('type', '')}: {meta['official_citation']}".strip(": ")
    if meta.get("type") == "matrika":
        book = BOOKS.get(str(meta.get("book", "")), str(meta.get("book", "")))
        parish = str(meta.get("parish", ""))
        par = parish if "f. ú." in parish else f"{meta.get('confession', '')} f. ú. {parish}"
        return (f"{meta.get('archive', '')}, {par} — "
                f"{book} {meta.get('years', '')} ({meta.get('volume', '')})").replace("  ", " ")
    return f"{meta.get('document', 'doklad')} — {meta.get('entry', '')}".strip(" —")


class Applier:
    def __init__(self, tree: Path, dry: bool):
        self.tree, self.dry = tree, dry
        self.gw = GrampsWeb()
        self.log: list[str] = []

    def find(self, kind: str, gid: str) -> dict | None:
        try:
            res = self.gw.get(f"/{kind}/?gramps_id={gid}")
        except RuntimeError as e:
            if "HTTP 404" in str(e):
                return None
            raise
        return res[0] if res else None

    def create(self, kind: str, obj: dict, cls: str) -> str:
        if self.dry:
            self.log.append(f"[dry] +{cls} {obj.get('gramps_id', '')} {obj.get('title', obj.get('page', ''))}")
            return f"DRY-{cls}-{len(self.log)}"
        res = self.gw.post(f"/{kind}/", obj)
        return next(o["handle"] for o in res if o["_class"] == cls)

    def place(self, name: str | None) -> str | None:
        if not name:
            return None
        gid = "P-" + slug(name)
        p = self.find("places", gid)
        if p:
            return p["handle"]
        self.log.append(f"+ místo {name}")
        return self.create("places", {"_class": "Place", "gramps_id": gid, "title": name,
                                      "name": {"_class": "PlaceName", "value": name}}, "Place")

    def source(self, sidecar: Path, pid: str) -> str:
        meta = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
        gid = f"S-{sidecar.stem}"   # jeden zdroj na doklad (sdílí ho všechny osoby, které cituje)
        s = self.find("sources", gid)
        if s:
            return s["handle"]
        title = source_title(meta)
        self.log.append(f"+ zdroj {gid}: {title[:80]}")
        return self.create("sources", {"_class": "Source", "gramps_id": gid, "title": title,
                                       "author": meta.get("issuer", meta.get("archive", "")),
                                       "pubinfo": f"{meta.get('register', '')}; vydáno {meta.get('issued', '?')}; "
                                                  f"uloženo: {meta.get('custody', '?')}"}, "Source")

    def citation(self, c: dict, pid: str) -> str:
        """Citace zdroje; existuje-li už citace téhož zdroje se stejným `page` a jistotou, použije se znovu
        (dřív každý patch zakládal novou → duplikáty)."""
        src = self.source(self.tree / c["source_sidecar"], pid)
        page, conf = c.get("page", ""), int(c.get("confidence", 2))
        if not self.dry and not src.startswith("DRY"):
            for ex in self.gw.get("/citations/?pagesize=10000"):
                if ex["source_handle"] == src and ex.get("page", "") == page and ex.get("confidence") == conf:
                    self.log.append(f"= citace {ex['gramps_id']} použita znovu")
                    return ex["handle"]
        return self.create("citations", {"_class": "Citation", "source_handle": src, "page": page,
                                         "confidence": conf}, "Citation")

    def citation_by_gid(self, gid: str) -> dict:
        c = self.find("citations", gid)
        if not c:
            sys.exit(f"citace {gid} v Gramps není")
        return c

    def media(self, path: Path, cit: str, desc: str) -> str:
        if self.dry:
            return self.create("media", {"gramps_id": path.name}, "Media")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        res = self.gw.upload("/media/", path.read_bytes(), mime)
        h = next(o["handle"] for o in res if o["_class"] == "Media")
        m = self.gw.get(f"/media/{h}")
        m["desc"] = desc
        m["citation_list"].append(cit)
        self.gw.put(f"/media/{h}", m)
        self.log.append(f"+ médium {path.name}")
        return h

    def context_note(self, ev_handle: str, text: str) -> None:
        """Kontext záznamu (domácnost, rodiče, kmotři…) → Event Note k události, aby popis zůstal jen o osobě."""
        if self.dry or not text:
            return
        res = self.gw.post("/notes/", {"_class": "Note", "type": "Event Note",
                                       "text": {"_class": "StyledText", "string": "Kontext záznamu:\n" + str(text).strip(),
                                                "tags": []}})
        ev = self.gw.get(f"/events/{ev_handle}")
        ev["note_list"].append(next(o["handle"] for o in res if o["_class"] == "Note"))
        self.gw.put(f"/events/{ev_handle}", ev)

    def attach_event(self, kind: str, obj: dict, ev: str, role: str) -> None:
        if self.dry:
            return
        fresh = self.gw.get(f"/{kind}/{obj['handle']}")
        fresh["event_ref_list"].append({"_class": "EventRef", "ref": ev, "role": role})
        self.gw.put(f"/{kind}/{obj['handle']}", fresh)

    def attach_media(self, kind: str, obj: dict, media: str) -> None:
        if self.dry:
            return
        fresh = self.gw.get(f"/{kind}/{obj['handle']}")
        fresh["media_list"].append({"_class": "MediaRef", "ref": media})
        self.gw.put(f"/{kind}/{obj['handle']}", fresh)


def main(tree_dir: str, patch_file: str, approve: bool, dry: bool) -> int:
    tree = Path(tree_dir)
    ppath = tree / patch_file if not Path(patch_file).is_absolute() else Path(patch_file)
    text = ppath.read_text(encoding="utf-8")
    try:
        patch = yaml.safe_load(text)
    except yaml.YAMLError as e:
        sys.exit(f"{ppath.name}: neplatný YAML — {e}\n(tip: hodnoty s dvojtečkou dej do uvozovek, např. summary: \"…: …\")")
    status = str(patch.get("status", "")).strip()
    if status == "aplikováno":
        sys.exit(f"{ppath.name} už je aplikovaný")
    if status != "schváleno" and not approve:
        sys.exit(f"{ppath.name} má status '{status}' — potřeba schválení uživatele (--approve)")
    bad = [c for c in patch["changes"] if c.get("type") in TYPE_FORBIDDEN]
    if bad:
        sys.exit("\n".join(f"{ppath.name}: typ {c['type']} nepoužívat — {TYPE_FORBIDDEN[c['type']]}" for c in bad))
    pid = norm_id(patch["person"])
    a = Applier(tree, dry)
    person = a.find("people", pid)
    if not person:
        sys.exit(f"osoba {pid} v Gramps není (ensure_persons.py)")
    cites = {k: a.citation(v, pid) for k, v in (patch.get("citations") or {}).items()}
    applied = []
    for ch in patch["changes"]:
        op = ch["op"]
        if op == "add_event":
            keys = ([ch["citation"]] if ch.get("citation") else []) + list(ch.get("citations") or [])
            ev = {"_class": "Event", "type": ch["type"], "description": ch.get("description", ""),
                  "citation_list": list(dict.fromkeys(cites[k] for k in keys))}
            d = gramps_date(ch.get("date"))
            if d:
                ev["date"] = d
            pl = a.place(ch.get("place"))
            if pl:
                ev["place"] = pl
            h = a.create("events", ev, "Event")
            a.context_note(h, ch.get("context", ""))
            if ch.get("family"):
                f, m = (norm_id(x) for x in ch["family"])
                fam = a.find("families", f"F-{f}-{m}")
                if not fam:
                    sys.exit(f"rodina F-{f}-{m} v Gramps není")
                a.attach_event("families", fam, h, "Family")
            else:
                a.attach_event("people", person, h, "Primary")
            a.log.append(f"+ událost {ch['type']} {ch.get('date', '')} {ch.get('place', '')}")
            applied.append({"op": op, "type": ch["type"], "event": h})
        elif op == "update_event":
            # úprava existující události: description / date / place (+ volitelně citace)
            if not dry:
                ev = a.gw.get(f"/events/{ch['event']}")
                if ch.get("type"):
                    ev["type"] = ch["type"]
                if "description" in ch:
                    ev["description"] = ch["description"]
                if ch.get("date"):
                    ev["date"] = gramps_date(ch["date"])
                if ch.get("place"):
                    ev["place"] = a.place(ch["place"])
                for k in ([ch["citation"]] if ch.get("citation") else []) + list(ch.get("citations") or []):
                    if cites[k] not in ev["citation_list"]:
                        ev["citation_list"].append(cites[k])
                a.gw.put(f"/events/{ch['event']}", ev)
                a.context_note(ch["event"], ch.get("context", ""))
                a.log.append(f"~ událost {ev['type']} {ch['event']}: {', '.join(k for k in ('type', 'description', 'date', 'place', 'context') if k in ch)}")
            applied.append({"op": op, "event": ch["event"]})
        elif op == "add_note":
            # poznámka (Gramps Note) k události, nebo k osobě, když `event` chybí. Note v Gramps citace nemá,
            # proto se `citation` z patche připíše na konec textu jako odkaz na pramen.
            text = str(ch["text"]).rstrip()
            if ch.get("citation"):
                text += f"\n\nPramen: {patch['citations'][ch['citation']].get('page', '')}"
            ntype = "Event Note" if ch.get("event") else "Person Note"
            h = a.create("notes", {"_class": "Note", "type": ntype,
                                   "text": {"_class": "StyledText", "string": text, "tags": []}}, "Note")
            if not dry:
                kind, handle = ("events", ch["event"]) if ch.get("event") else ("people", person["handle"])
                obj = a.gw.get(f"/{kind}/{handle}")
                obj["note_list"].append(h)
                a.gw.put(f"/{kind}/{handle}", obj)
            a.log.append(f"+ poznámka ({ntype}) {text[:60]!r}…")
            applied.append({"op": op, "note": h, "event": ch.get("event")})
        elif op == "remove_citation":
            # odebrat citaci z události; smazat ji, pokud ji už nic jiného neodkazuje
            c = a.citation_by_gid(ch["citation_gramps_id"])
            if not dry:
                ev = a.gw.get(f"/events/{ch['event']}")
                if c["handle"] in ev["citation_list"]:
                    ev["citation_list"].remove(c["handle"])
                    a.gw.put(f"/events/{ch['event']}", ev)
                refs = a.gw.get(f"/citations/{c['handle']}?backlinks=1").get("backlinks", {})
                if not any(refs.values()):
                    a.gw.delete(f"/citations/{c['handle']}")
                    a.log.append(f"- citace {c['gramps_id']} odebrána a smazána (bez dalších odkazů)")
                else:
                    a.log.append(f"- citace {c['gramps_id']} odebrána z události (dál odkazována: {refs})")
            applied.append({"op": op, "event": ch["event"], "citation": c["gramps_id"]})
        elif op == "update_citation":
            c = a.citation_by_gid(ch["citation_gramps_id"])
            if not dry:
                if "page" in ch:
                    c["page"] = ch["page"]
                if "confidence" in ch:
                    c["confidence"] = int(ch["confidence"])
                a.gw.put(f"/citations/{c['handle']}", c)
                a.log.append(f"~ citace {c['gramps_id']}: {', '.join(k for k in ('page', 'confidence') if k in ch)}")
            applied.append({"op": op, "citation": c["gramps_id"]})
        elif op == "add_citation":
            # doplňková citace k už zapsané události (handle z `applied:` dřívějšího patche)
            cit = cites[ch["citation"]]
            if not dry:
                ev = a.gw.get(f"/events/{ch['event']}")
                if cit not in ev["citation_list"]:
                    ev["citation_list"].append(cit)
                    a.gw.put(f"/events/{ch['event']}", ev)
                a.log.append(f"+ citace k události {ev['type']} {ch['event']}")
            applied.append({"op": op, "event": ch["event"], "citation": cit})
        elif op == "add_media":
            cit = cites[ch["citation"]]
            src_meta = patch["citations"][ch["citation"]]
            desc = Path(src_meta["source_sidecar"]).stem + " — " + str(src_meta.get("page", ""))[:80]
            h = a.media(tree / ch["file"], cit, desc)
            a.attach_media("people", person, h)
            applied.append({"op": op, "file": ch["file"], "media": h})
        else:
            sys.exit(f"neznámá operace {op}")
    print("\n".join(a.log))
    if dry:
        print("(dry-run — nic nezapsáno)")
        return 0
    # patch: status + záznam o zápisu
    text = re.sub(r"^status:.*$", "status: aplikováno", text, count=1, flags=re.M)
    text += "\napplied:\n" + yaml.safe_dump({"date": date.today().isoformat(), "items": applied},
                                            allow_unicode=True, sort_keys=False).replace("\n", "\n  ").rstrip() + "\n"
    ppath.write_text(text.replace("applied:\n", "applied:\n  ", 1), encoding="utf-8")
    # dossier: stav zapsáno
    people = tree / "research" / "people"
    for dp in people.glob(f"{pid}-*.md"):
        if re.match(rf"{re.escape(pid)}-[a-z]", dp.name):
            dt = dp.read_text(encoding="utf-8")
            # průběžné patche: `zapsáno` jen když byl výzkum dokončen, jinak stav nechat (výzkum běží dál)
            if re.search(r"^stav:\s*dokončeno", dt, re.M):
                dt = re.sub(r"^stav:\s*[^#\n]*", "stav: zapsáno          ", dt, count=1, flags=re.M)
            dp.write_text(dt, encoding="utf-8")
    print(f"✔ {ppath.name} aplikován ({pid})")
    return 0


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    sys.exit(main(args[0], args[1], "--approve" in sys.argv, "--dry-run" in sys.argv))
