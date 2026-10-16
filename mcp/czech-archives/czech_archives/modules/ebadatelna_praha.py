"""SOA v Praze — eBadatelna: matriky Středočeského kraje (bez přihlášení, HTML Apache Wicket).

Portál: https://ebadatelna.soapraha.cz/ — server-side Wicket aplikace, žádné JSON API. Stránky:
popis svazku `/pages/MatrikaPage/matrikaId/<ID>`, prohlížeč snímku `/d/<ID>/<snímek>`, hledání
`/pages/SearchMatrikaPage` (Wicket AJAX POST). Popis a ověřené chování:
docs/archivy/ebadatelna-praha.md.

Princip získání snímku (inspirováno README projektu lioilsources/genealogy-matriky, kód vlastní):
v jedné session načíst HTML prohlížeče `/d/<ID>/<snímek>` a z něj vzít odkaz tlačítka „stáhnout“
(`wicket/resource/org.apache.wicket.Application/<soubor>.jpg`) — to je originální JPG. Samotné
`?N--scanImage` závisí na stavu session, proto se nikdy neskládá ručně.
"""

from __future__ import annotations

import hashlib
import html as _html
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..core import (
    USER_AGENT, Citation, HttpError, Page, RateLimitedClient, Register, citation_text, copy_to,
    today, write_sidecar,
)

BASE = "https://ebadatelna.soapraha.cz"
ARCHIVE = "Státní oblastní archiv v Praze"
GAZETTEER_DIR = Path(__file__).resolve().parents[2] / "gazetteer"

_CONFESSION = {
    "Římskokatolická církev": "řkt",
    "Evangelická církev": "ev.",
    "Československá církev": "čsl.",
    "Okresní úřad": "civ.",
    "Židovská náboženská obec": "izr.",
    "Pravoslavná církev": "pravosl.",
    "Starokatolická církev": "stkat.",
}
# řádky tabulky popisu: label → druh (hodnoty: [matrika, index])
_KIND_ROWS = {"Narození / index": "N", "Oddaní / index": "O", "Zemřelí / index": "Z"}
# sloupce tabulky výsledků hledání (po názvu knihy)
_RESULT_COLS = ["originator_type", "district", "places_count", "places",
                "N", "O", "Z", "IN", "IO", "IZ", "scans"]

_RE_TITLE = re.compile(r'dataPageTitle"[\s\S]*?<h1>([^<]+)</h1>')
_RE_DL = re.compile(r'href="([^"]*wicket/resource/org\.apache\.wicket\.Application/[^"]+\.(?:jpe?g|png|tiff?))"', re.I)
_RE_SCAN = re.compile(r'id="scanImage"[^>]*\bsrc="([^"]+)"')
_RE_SIZE = re.compile(r'footerDataPageText">\s*([\d.,]+\s*[kMG]?B)\s*<')
_RE_OPTION = re.compile(r"<option\b")
_RE_JSESSION = re.compile(r";jsessionid=[0-9A-Fa-f]+")
_RE_YEARS = re.compile(r"(\d{4})\s*-\s*(\d{4})")
_RE_SECTION = re.compile(
    r"^(?P<label>.+?)\s+(?P<period>[\d/ .-]*\d{4}(?:\s*-\s*[\d/]*\d{4})?)?,?\s*"
    r"(?:fol\.\s*)?(?P<fol>\d+(?:\s*-\s*\d+)?)\s*\[(?P<img>\d+(?:\s*-\s*\d+)?)\]\s*$")


def _clean(s: str | None) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s).replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in s.split("\n")]
    s = "\n".join(line for line in lines if line).strip()
    return "" if s.strip("- ") == "" else s


def _range(text: str | None) -> tuple[int, int] | None:
    m = _RE_YEARS.search(text or "")
    if m:
        return int(m[1]), int(m[2])
    m = re.search(r"\b(\d{4})\b", text or "")
    return (int(m[1]), int(m[1])) if m else None


def _ranges_text(ranges: dict[str, tuple[int, int] | None]) -> str:
    return "; ".join(f"{k} {a}–{b}" if a != b else f"{k} {a}"
                     for k, v in ranges.items() if v for a, b in [v])


def _kinds(ranges: dict) -> list[str]:
    main = [k for k in ("N", "O", "Z") if ranges.get(k)]
    idx = [k[1] for k in ("IN", "IO", "IZ") if ranges.get(k)]
    kinds = (["I"] if idx else []) + main
    # svazek obsahující jen index (např. „Žiželice 22“, IN) — druh odvodit z indexu
    for k in idx:
        if k not in kinds:
            kinds.append(k)
    return kinds


def _span(ranges: dict, kind: str | None) -> tuple[int | None, int | None]:
    keys = list(ranges)
    if kind in ("N", "O", "Z"):
        keys = [kind, "I" + kind]
    elif kind == "I":
        keys = ["IN", "IO", "IZ"]
    vals = [ranges[k] for k in keys if ranges.get(k)]
    if not vals:
        return None, None
    return min(v[0] for v in vals), max(v[1] for v in vals)


class _Session:
    """Wicket session (cookie JSESSIONID) nad rate-limitem core klienta.

    Každý požadavek bere slot sdíleného zámku `RateLimitedClient` (≥ 2,5 s, i mezi procesy).
    Žádné přihlášení — jen anonymní session, kterou portál zakládá sám.
    """

    def __init__(self, http_client: RateLimitedClient, max_age: float = 600.0):
        self.http = http_client
        self.max_age = max_age
        self._reset()

    def _reset(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.started = time.time()

    def request(self, url: str, data: dict | None = None, ajax_base: str | None = None) -> tuple[str, str]:
        """Vrátí (finální URL, text). data → POST form-urlencoded."""
        if time.time() - self.started > self.max_age:
            self._reset()
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "cs-CZ,cs;q=0.9",
        }
        if ajax_base is not None:
            headers.update({"Wicket-Ajax": "true", "Wicket-Ajax-BaseURL": ajax_base,
                            "X-Requested-With": "XMLHttpRequest"})
        body = urllib.parse.urlencode(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
        with self.http._slot():
            try:
                with self.opener.open(req, timeout=self.http.timeout) as resp:
                    return resp.geturl(), resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from None


class EbadatelnaPraha:
    """SOA v Praze — eBadatelna: matriky Středočeského kraje, hledání podle lokality / názvu knihy, originální JPG."""

    id = "ebadatelna_praha"
    archive = ARCHIVE
    capabilities = {"registers", "fetch_page", "search_registers_live", "image_map"}

    def __init__(self, client: RateLimitedClient | None = None):
        self.http = client or RateLimitedClient(self.id, min_interval=2.5)
        self.session = _Session(self.http)

    # --- cache textu (HTML / JSON výsledky) ----------------------------------------------
    def _cache_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()[:24]
        return self.http.cache_dir / "json" / h[:2] / f"{h}.json"

    def _cached(self, key: str, ttl: float):
        p = self._cache_path(key)
        if p.exists() and time.time() - p.stat().st_mtime < ttl:
            return json.loads(p.read_text("utf-8"))
        return None

    def _store(self, key: str, value):
        p = self._cache_path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, ensure_ascii=False), "utf-8")
        return value

    # --- popis svazku ---------------------------------------------------------------------
    def register_url(self, register_id: str) -> str:
        return f"{BASE}/pages/MatrikaPage/matrikaId/{int(register_id)}"

    def viewer_url(self, register_id: str, image: int) -> str:
        """Krátký odkaz prohlížeče (stejný tvar, jaký používá uživatel)."""
        return f"{BASE}/d/{int(register_id)}/{int(image)}"

    def _matrika_html(self, register_id: str) -> str:
        key = f"matrika:{int(register_id)}"
        hit = self._cached(key, 7 * 86400)
        if hit is not None:
            return hit
        _, text = self.session.request(self.register_url(register_id))
        if "tableMatrikaBasicInfo" not in text:
            raise ValueError(f"matrikaId {register_id}: stránka popisu neobsahuje údaje o knize "
                             "(neexistuje, nebo portál vrátil chybu)")
        return self._store(key, text)

    @staticmethod
    def _parse_matrika(register_id: str, text: str) -> tuple[Register, dict]:
        title = _clean((_RE_TITLE.search(text) or [None, ""])[1])
        rows: dict[str, list[str]] = {}
        for seg in text.split('class="tableMatrikaBasicInfoRow"')[1:]:
            lab = re.search(r'tableMatrikaBasicInfoHeader1">\s*<div>([\s\S]*?)</div>', seg)
            vals = re.findall(r'tableMatrikaBasicInfoHeader2">\s*<div[^>]*>([\s\S]*?)</div>\s*</div>', seg)
            if lab:
                rows[_clean(lab[1])] = [_clean(v) for v in vals]
        desc: dict[str, str] = {}
        for seg in text.split('class="tableMatrikaDescription"')[1:]:
            spans = re.findall(r"<span>([\s\S]*?)</span>", seg)
            if len(spans) >= 2:
                desc[_clean(spans[0])] = _clean(spans[1])
        localities = [_clean(x) for x in re.findall(r'obecCastLabel">([^<]+)<', text)]

        ranges: dict[str, tuple[int, int] | None] = {}
        for label, k in _KIND_ROWS.items():
            vals = rows.get(label) or []
            ranges[k] = _range(vals[0]) if len(vals) > 0 else None
            ranges["I" + k] = _range(vals[1]) if len(vals) > 1 else None

        def first(label):
            v = rows.get(label)
            return v[0] if v and v[0] else None

        originator = first("Původce")
        otype = None
        m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", originator or "")
        parish = originator
        if m:
            parish, otype = m[1], m[2]
        yf, yt = _span(ranges, None)
        scans = first("Počet snímků")
        sheets, pages = first("Počet listů"), first("Počet stran")
        size_bits = [f"{sheets} listů" if sheets and sheets != "0" else None,
                     f"{pages} stran" if pages and pages != "0" else None,
                     first("Rozměr")]
        notes = [desc.get("Obecný popis matriky")]
        if desc.get("Informace o nematričních zápisech"):
            notes.append("Nematriční zápisy: " + desc["Informace o nematričních zápisech"])
        if desc.get("Detail původce"):
            notes.append("Původce: " + desc["Detail původce"])
        reg = Register(
            module="ebadatelna_praha",
            id=str(int(register_id)),
            title=title,
            archive=first("Místo uložení") or ARCHIVE,
            parish=parish,
            originator=originator,
            confession=_CONFESSION.get(otype or "", otype),
            kinds=_kinds(ranges),
            year_from=yf,
            year_to=yt,
            years_text=_ranges_text(ranges) or None,
            places=", ".join(x.split(" / ")[0] for x in localities) or None,
            signature=title or None,           # „název knihy“ = farnost + pořadové číslo
            signature_orig=first("Původní název"),
            storage=first("Místo uložení"),
            content_note="\n".join(n for n in notes if n) or None,
            size_note=", ".join(b for b in size_bits if b) or None,
            digitized=bool(scans and scans != "0"),
            image_count=int(scans) if scans and scans.isdigit() else None,
            url=f"{BASE}/pages/MatrikaPage/matrikaId/{int(register_id)}",
        )
        extra = {
            "district": first("Okres"),
            "originator_type": otype,
            "book_type": first("Typ knihy"),
            "language": first("Jazyk"),
            "completeness": first("Stav úplnosti"),
            "ranges": {k: f"{v[0]}–{v[1]}" for k, v in ranges.items() if v},
            "localities": localities,
            "description": desc,
        }
        return reg, extra

    def register_info(self, register_id: str) -> Register:
        reg, _ = self._parse_matrika(register_id, self._matrika_html(register_id))
        return reg

    def register_details(self, register_id: str) -> dict:
        """register_info + okres, typ knihy, rozsahy N/O/Z a indexů, lokality s variantami
        a mapa oddílů svazku (obec, období, folia → snímky) z „Obecného popisu“."""
        reg, extra = self._parse_matrika(register_id, self._matrika_html(register_id))
        d = {k: v for k, v in reg.to_dict().items() if v not in (None, [], "")}
        d.update({k: v for k, v in extra.items() if v not in (None, [], {}, "")})
        d["image_map"] = self.image_map(register_id)
        d["viewer_url_pattern"] = f"{BASE}/d/{reg.id}/<snímek>"
        return d

    def image_map(self, register_id: str) -> list[dict]:
        """Oddíly svazku z „Obecného popisu“: „Loukonosy 1/1842-12/1848, fol. 173-184 [165-176]“
        → {label, period, folio, images}. Čísla v [ ] jsou čísla snímků (ověřeno na 10056:
        fol. 2 = snímek 5); u jiných svazků to archiv nemusí dodržovat — kontrolovat na snímku."""
        reg = self.register_info(register_id)
        out = []
        for line in (reg.content_note or "").split("\n"):
            m = _RE_SECTION.match(line.strip())
            if not m:
                continue
            img = [int(x) for x in re.findall(r"\d+", m["img"])]
            out.append({"label": m["label"].strip().rstrip(","), "period": (m["period"] or "").strip() or None,
                        "folio": m["fol"].replace(" ", ""), "image_from": img[0], "image_to": img[-1]})
        return out

    # --- hledání --------------------------------------------------------------------------
    def _search_live(self, token: str, year_from: int | None, year_to: int | None,
                     in_titles: bool = False, limit: int = 300) -> list[dict]:
        key = f"search:{in_titles}:{token}:{year_from}:{year_to}:{limit}"
        hit = self._cached(key, 86400)
        if hit is not None:
            return hit
        self.session._reset()                       # čistá session = předvídatelná čísla Wicket stránek
        url, page = self.session.request(f"{BASE}/pages/SearchMatrikaPage")
        page = _RE_JSESSION.sub("", page)   # první odpověď nové session nese ;jsessionid=… v URL
        form = re.search(r'<form class="searchForm" id="([^"]+)"', page)
        btn = re.search(r'"u":"\./(SearchMatrikaPage\?[^"]*-searchForm-searchButton)"', page)
        if not form or not btn:
            raise RuntimeError("eBadatelna: formulář hledání nenalezen (změna portálu?)")
        page_ver = btn[1].split("?", 1)[1].split("-", 1)[0]
        ajax_base = f"pages/SearchMatrikaPage?{page_ver}"
        data = {
            f"{form[1]}_hf_0": "",
            "searchType": "1",
            "keywordBox:searchTokenIn": "radio1" if in_titles else "radio0",
            "keywordBox:searchToken": token,
            "dateYearFrom": str(year_from or 1000),
            "dateYearTo": str(year_to or 2100),
            "searchButton": "1",
        }
        _, xml = self.session.request(f"{BASE}/pages/{btn[1]}", data, ajax_base)
        xml = _RE_JSESSION.sub("", xml)
        rows = self._parse_results(xml)
        total = int((re.search(r"nalezeno\s+(\d+)", xml) or [0, len(rows)])[1])
        seen = {r["id"] for r in rows}
        while len(rows) < min(total, limit):
            nxt = re.search(r'"u":"\./(SearchMatrikaPage\?[^"]*-pagination-results-nextPageUrl)"', xml)
            if not nxt:
                break
            _, xml = self.session.request(f"{BASE}/pages/{nxt[1]}&_={int(time.time() * 1000)}",
                                          None, ajax_base)
            xml = _RE_JSESSION.sub("", xml)
            new = [r for r in self._parse_results(xml) if r["id"] not in seen]
            if not new:
                break
            rows.extend(new)
            seen.update(r["id"] for r in new)
        return self._store(key, rows[:limit])

    @staticmethod
    def _parse_results(xml: str) -> list[dict]:
        out = []
        for tr in re.findall(r'<tr name="dataLink"[\s\S]*?</tr>', xml):
            mid = re.search(r'matrikaLink"[^>]*href="/pages/MatrikaPage/matrikaId/(\d+)">([^<]+)</a>', tr)
            if not mid:
                continue
            cells = [_clean(c) for c in re.findall(r"<td[^>]*>\s*<span>([\s\S]*?)</span>\s*</td>", tr)]
            row = {"id": mid[1], "title": _clean(mid[2])}
            row.update(dict(zip(_RESULT_COLS, cells)))
            out.append(row)
        return out

    def _row_to_register(self, row: dict) -> Register:
        ranges = {k: _range(row.get(k)) for k in ("N", "O", "Z", "IN", "IO", "IZ")}
        yf, yt = _span(ranges, None)
        otype = row.get("originator_type")
        title = row["title"]
        parish = re.sub(r"\s+\d+\s*$", "", title)
        return Register(
            module=self.id, id=row["id"], title=title, archive=ARCHIVE,
            parish=parish, originator=f"{parish} ({otype})" if otype else None,
            confession=_CONFESSION.get(otype or "", otype), kinds=_kinds(ranges),
            year_from=yf, year_to=yt, years_text=_ranges_text(ranges) or None,
            places=row.get("places"), signature=title,
            digitized=bool(row.get("scans") and row["scans"] != "0"),
            image_count=int(row["scans"]) if (row.get("scans") or "").isdigit() else None,
            url=self.register_url(row["id"]),
        )

    def _gazetteer(self, place: str) -> list[Register]:
        """Záložní (offline) hledání v gazetteer/*.yml s `module: ebadatelna_praha`."""
        out = []
        pl = place.lower()
        for f in sorted(GAZETTEER_DIR.glob("*.yml")):
            text = f.read_text("utf-8")
            for doc in text.split("\n---"):
                if "module: ebadatelna_praha" not in doc:
                    continue
                parish = (re.search(r"^parish:\s*\"?([^\"\n]+)", doc, re.M) or [None, ""])[1].strip()
                places = (re.search(r"^places:\s*\[([^\]]*)\]", doc, re.M) or [None, ""])[1]
                if pl not in parish.lower() and pl not in places.lower():
                    continue
                conf = (re.search(r"^confession:\s*\"?([^\"\n]+)", doc, re.M) or [None, None])[1]
                for line in re.findall(r"^\s*-\s*\{(.*)\}\s*$", doc, re.M):
                    fields = dict(re.findall(r'(\w+):\s*("[^"]*"|[^,]+)', line))
                    fields = {k: v.strip().strip('"') for k, v in fields.items()}
                    if "id" not in fields:
                        continue
                    ranges = {k: _range(fields.get(k).replace("–", "-")) if fields.get(k) else None
                              for k in ("N", "O", "Z", "IN", "IO", "IZ")}
                    yf, yt = _span(ranges, None)
                    name = re.sub(r"\s*\(.*\)$", "", fields.get("name", ""))
                    out.append(Register(
                        module=self.id, id=fields["id"], title=name, archive=ARCHIVE,
                        parish=parish, confession=conf, kinds=_kinds(ranges), year_from=yf,
                        year_to=yt, years_text=_ranges_text(ranges) or None,
                        places=places.strip() or None, signature=name or None,
                        image_count=int(fields["scans"]) if fields.get("scans", "").isdigit() else None,
                        url=self.register_url(fields["id"]),
                        content_note=f"z gazetteeru {f.name} (offline, neověřeno proti portálu)",
                    ))
        return out

    def find_registers(self, place: str, year_from: int | None = None, year_to: int | None = None,
                       kind: str | None = None, limit: int = 300, in_titles: bool = False) -> list[Register]:
        """Svazky podle lokality (výchozí) nebo názvu knihy (`in_titles=True`, např. „Žiželice“
        → Žiželice 01–30), jejichž datace se překrývá s intervalem. kind: N/O/Z/I.

        Portál hledá lokalitu podle podřetězce i v historických variantách názvu („Žiželitz“).
        Při nedostupnosti portálu se použije gazetteer YAML (offline)."""
        kind = (kind or "").upper() or None
        try:
            rows = self._search_live(place, year_from, year_to, in_titles, limit)
            regs = [self._row_to_register(r) for r in rows]
        except (HttpError, OSError, RuntimeError):
            regs = self._gazetteer(place)
        if kind:
            regs = [r for r in regs if kind in r.kinds]
        if kind or year_from or year_to:
            lo, hi = year_from or 0, year_to or 9999

            def overlaps(r):
                ranges = {}
                for part in (r.years_text or "").split("; "):
                    if " " in part:
                        k, v = part.split(" ", 1)
                        ranges[k] = _range(v.replace("–", "-"))
                a, b = _span(ranges, kind) if kind else (r.year_from, r.year_to)
                return a is None or (a <= hi and b >= lo)
            regs = [r for r in regs if overlaps(r)]
        pl = place.lower()
        regs.sort(key=lambda r: (pl not in (r.title or "").lower(), r.parish or "",
                                 r.year_from or 0, r.title or ""))
        return regs[:limit]

    # --- snímky ---------------------------------------------------------------------------
    def _viewer(self, register_id: str, image: int) -> dict:
        """HTML prohlížeče /d/<ID>/<snímek> → odkaz na originál (cache 30 dní)."""
        key = f"viewer:{int(register_id)}:{int(image)}"
        hit = self._cached(key, 30 * 86400)
        if hit is not None:
            return hit
        url = self.viewer_url(register_id, image)
        final, text = self.session.request(url)
        text = _RE_JSESSION.sub("", text)
        final = _RE_JSESSION.sub("", final)
        total = len(_RE_OPTION.findall(text.split("pageDropdown", 1)[-1])) if "pageDropdown" in text else None
        if total and not 1 <= image <= total:
            raise ValueError(f"snímek {image} mimo rozsah 1–{total}")
        sel = re.search(r'<option selected="selected" value="(\d+)">(\d+)</option>', text)
        if sel and int(sel[2]) != int(image):
            raise RuntimeError(f"prohlížeč ukazuje snímek {sel[2]}, ne {image} — nestahuji")
        dl = _RE_DL.search(text)
        scan = _RE_SCAN.search(text)
        if not dl and not scan:
            raise RuntimeError(f"{url}: v HTML není odkaz na snímek (vyžaduje přihlášení? změna portálu?)")
        info = {
            "image": int(image),
            "total": total,
            "download_url": urllib.parse.urljoin(final, _html.unescape(dl[1])) if dl else None,
            "file_name": urllib.parse.unquote(dl[1].rsplit("/", 1)[-1]) if dl else None,
            "size_text": (_RE_SIZE.search(text) or [None, None])[1],
        }
        if dl:   # odkaz „stáhnout“ je bezstavový → lze cachovat
            self._store(key, info)
        else:    # jen stavový scanImage — necachovat, použít hned v téže session
            info["scan_url"] = urllib.parse.urljoin(final, _html.unescape(scan[1]))
        return info

    def page_url(self, register_id: str, image: int) -> str:
        """URL originálního JPG (tlačítko „stáhnout“ v prohlížeči). Zjištění = 1 požadavek."""
        v = self._viewer(register_id, image)
        return v.get("download_url") or v["scan_url"]

    def _download_via_session(self, url: str, cache_rel: str) -> Path:
        target = self.http.cache_dir / "files" / cache_rel
        if target.exists() and target.stat().st_size > 0:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
        with self.http._slot():
            with self.session.opener.open(req, timeout=self.http.timeout) as resp:
                data = resp.read(self.http_max + 1)
        if len(data) > self.http_max:
            raise RuntimeError(f"{url}: překročen limit {self.http_max} B")
        target.write_bytes(data)
        return target

    http_max = 50 * 1024 * 1024

    def fetch_page(self, register_id: str, image: int, dest: Path, sidecar: bool = True,
                   entry: str | None = None) -> Path:
        """Stáhne jeden snímek (originální JPG, přes cache) do `dest` + sidecar .yml."""
        reg = self.register_info(register_id)
        if reg.image_count and not 1 <= image <= reg.image_count:
            raise ValueError(f"snímek {image} mimo rozsah 1–{reg.image_count}")
        cache_name = f"{reg.id}/{reg.id}_{int(image):04d}"
        existing = sorted((self.http.cache_dir / "files" / reg.id).glob(f"{reg.id}_{int(image):04d}.*"))
        existing = [p for p in existing if p.suffix != ".part" and p.stat().st_size > 0]
        v = None
        if existing:
            cached = existing[0]
            v = self._cached(f"viewer:{int(register_id)}:{int(image)}", 365 * 86400)
        else:
            v = self._viewer(register_id, image)
            if v.get("download_url"):
                ext = Path(v["file_name"] or "x.jpg").suffix.lower() or ".jpg"
                cached = self.http.download(v["download_url"], cache_name + ext)
            else:
                cached = self._download_via_session(v["scan_url"], cache_name + ".jpg")
            head = cached.read_bytes()[:8]
            if not (head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG")):
                cached.unlink(missing_ok=True)
                raise RuntimeError("portál nevrátil obrázek (HTML / přihlášení?) — nic neuloženo")
        dest = Path(dest).expanduser()
        if dest.suffix.lower() not in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
            dest.mkdir(parents=True, exist_ok=True)
        out = copy_to(cached, dest)
        if sidecar:
            extra = {"source_file": v.get("file_name") if v else None}
            write_sidecar(out, self.citation(reg, image, entry), extra)
        return out

    def register_zip_info(self, register_id: str) -> dict:
        reg = self.register_info(register_id)
        return {"zip_url": None, "images": reg.image_count,
                "note": "ZIP celé knihy nabízí eBadatelna jen přihlášeným uživatelům; modul se "
                        "nepřihlašuje a celé svazky nestahuje."}

    # --- citace ---------------------------------------------------------------------------
    def citation(self, register: Register, image: int | None, entry: str | None = None) -> Citation:
        r = register
        conf = {"řkt": "ř. k. f. ú.", "ev.": "ev. f. ú.", "čsl.": "čsl. n. o."}
        parish = r.parish
        if parish and r.confession in conf:
            parish = f"{conf[r.confession]} {parish}"
        elif parish and r.confession == "civ.":
            parish = f"Okresní úřad {parish}"
        years = None
        if r.year_from and r.year_to:
            years = f"{r.year_from}–{r.year_to}" if r.year_from != r.year_to else str(r.year_from)
        volume = f"kniha {r.signature}" if r.signature else None
        if r.signature_orig:
            volume = f"{volume} (pův. {r.signature_orig})" if volume else f"pův. {r.signature_orig}"
        volume = f"{volume}, matrikaId {r.id}" if volume else f"matrikaId {r.id}"
        c = Citation(
            type="matrika",
            archive=r.archive or ARCHIVE,
            fond=r.fond,
            parish=parish,
            confession=r.confession,
            book="+".join(r.kinds) or None,
            years=years,
            volume=volume,
            image=image,
            url=self.viewer_url(r.id, image) if image is not None else r.url,
            accessed=today(),
            entry=entry,
            module=self.id,
            register_id=r.id,
        )
        c.text = citation_text(c)
        return c


MODULE = EbadatelnaPraha
