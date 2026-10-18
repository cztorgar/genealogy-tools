"""Matricula Online (ICARUS) — matriky diecézí a farností Rakouska, Německa, Polska aj. (bez přihlášení, HTML).

Portál: https://data.matricula-online.eu/ — server-side HTML. Stránky: diecéze `/de/<země>/<diecéze>/`
(seznam všech farností), farnost `/de/<země>/<diecéze>/<farnost>/` (tabulka svazků), svazek
`/de/<země>/<diecéze>/<farnost>/<signatura>/` (inicializace prohlížeče se seznamem snímků `files`
a jejich jmény `labels`). Snímek = `https://img.data.matricula-online.eu` + položka `files` — ale obrazový
server vrací 403 každému požadavku mimo prohlížeč na stránce `?pg=` (kontrola Origin/Referer, ověřeno
2026-10-18). Podvrhnout hlavičku = obcházení ochrany → modul snímky NESTAHUJE, jen popisuje svazky a skládá
odkaz pro člověka.

robots.txt zakazuje `/*?pg=` (prohlížeč na konkrétní straně), `/*/suchen` a `/*/accounts` — modul je
nikdy nevolá; URL s `?pg=` se jen skládá jako odkaz pro člověka. Podmínky užití: jen soukromé nebo
vědecké účely, rozmnožování / publikace / předání třetím stranám jen se souhlasem archivu.
Popis a ověřené chování: docs/archivy/matricula.md.
"""

from __future__ import annotations

import html as _html
import json
import re
import unicodedata
from pathlib import Path

from ..core import Citation, Page, RateLimitedClient, Register, citation_text, today

BASE = "https://data.matricula-online.eu"
IMG = "https://img.data.matricula-online.eu"   # jen pro dokumentaci; modul odtud nestahuje

# Diecéze, ve kterých find_registers hledá obec podle jména (seznam farností = jedna stránka na diecézi).
# Jiné diecéze: zadat cestu přímo („oesterreich/linz/…“) nebo `dioceses=`.
DEFAULT_DIOCESES = ["oesterreich/wien", "oesterreich/st-poelten"]

_BOOK_KINDS = {"Taufen": "N", "Trauungen": "O", "Sterben": "Z", "Index": "I", "Firmungen": "F"}
_RE_ROW = re.compile(
    r'<a class="mr-2[^"]*"\s+href="(?P<href>/de/[^"]+/)"[^>]*>.*?</a>.*?'
    r'href="#details-(?P<did>\d+)".*?</td>\s*<td[^>]*>(?P<sig>[^<]*)</td>\s*<td>(?P<book>[^<]*)</td>\s*'
    r'<td>(?P<years>[^<]*)</td>', re.S)
_RE_DETAILS = re.compile(r'id="details-(?P<did>\d+)".*?<dl[^>]*>(?P<dl>.*?)</dl>', re.S)
_RE_DTDD = re.compile(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", re.S)
_RE_TITLE = re.compile(r"<title>\s*(.*?)\s*</title>", re.S)
_RE_PARISH_LINK = re.compile(r'href="/de/(?P<path>[^/"]+/[^/"]+/[^/"]+)/">\s*<span class="fa fa-map-marker-alt">'
                             r'.*?</span>(?P<name>[^<]+)</a>', re.S)


def _clean(s: str | None) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(_html.unescape(s).replace("\xa0", " ").split())


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _years(text: str | None) -> tuple[int | None, int | None]:
    ys = [int(y) for y in re.findall(r"(?<!\d)(\d{4})(?!\d)", text or "")]
    return (min(ys), max(ys)) if ys else (None, None)


def _js_array(text: str, key: str) -> list[str]:
    m = re.search(rf'"{key}"\s*:\s*(\[.*?\])', text, re.S)
    return json.loads(m.group(1)) if m else []


class Matricula:
    """Matricula Online (ICARUS): matriky Rakouska, Německa, Polska… — svazky podle farnosti, snímky po jednom."""

    id = "matricula"
    archive = "Matricula Online (ICARUS)"
    capabilities = {"registers"}

    def __init__(self, client: RateLimitedClient | None = None):
        self.http = client or RateLimitedClient(self.id, min_interval=3.0)

    def _html(self, path: str, ttl: float) -> str:
        return self.http.text(f"{BASE}/de/{path.strip('/')}/", ttl=ttl, accept="text/html")

    # --- hledání --------------------------------------------------------------------------
    def parishes(self, diocese: str) -> list[dict]:
        """Farnosti diecéze (`oesterreich/wien`): [{path, name}]."""
        t = self._html(diocese, ttl=30 * 86400)
        return [{"path": m["path"], "name": _clean(m["name"])} for m in _RE_PARISH_LINK.finditer(t)]

    def find_parishes(self, place: str, dioceses: list[str] | None = None) -> list[dict]:
        p = _fold(place)
        out = []
        for d in dioceses or DEFAULT_DIOCESES:
            for par in self.parishes(d):
                if p in _fold(par["name"]):
                    out.append({**par, "exact": _fold(par["name"]) == p})
        return sorted(out, key=lambda x: (not x["exact"], x["name"]))

    def parish_registers(self, parish_path: str) -> list[Register]:
        t = self._html(parish_path, ttl=7 * 86400)
        title = _clean((_RE_TITLE.search(t) or [None, ""])[1])
        bits = [b.strip() for b in title.split("|")]
        parish = bits[0] if bits else parish_path.rsplit("/", 1)[-1]
        diocese = bits[1] if len(bits) > 1 else None
        details = {m["did"]: {_clean(k): _clean(v) for k, v in _RE_DTDD.findall(m["dl"])}
                   for m in _RE_DETAILS.finditer(t)}
        regs = []
        for m in _RE_ROW.finditer(t):
            d = details.get(m["did"], {})
            types = d.get("Matrikeltyp", "")
            kinds = [k for w, k in _BOOK_KINDS.items() if w in types]
            if "I" in kinds:   # Index na začátku, pak druhy
                kinds = ["I"] + [k for k in kinds if k != "I"]
            yf, yt = _years(m["years"])
            rid = m["href"].strip("/").split("/", 1)[1]           # bez „de/“
            regs.append(Register(
                module=self.id, id=rid, title=f"{_clean(m['book'])} {_clean(m['sig'])}",
                archive=diocese or self.archive, fond="Matricula Online", parish=parish,
                kinds=kinds, year_from=yf, year_to=yt, years_text=_clean(m["years"]),
                places=parish, signature=_clean(m["sig"]),
                content_note=d.get("Inhalt") or None, storage=d.get("Lagerungsort") or None,
                digitized=True, url=f"{BASE}{m['href']}",
            ))
        return regs

    def find_registers(self, place: str, year_from: int | None = None, year_to: int | None = None,
                       kind: str | None = None, limit: int = 300,
                       dioceses: list[str] | None = None) -> list[Register]:
        """`place` = cesta farnosti („oesterreich/wien/hennersdorf“) nebo jméno obce (hledá se v názvech
        farností DEFAULT_DIOCESES). Svazky, jejichž datace se překrývá s intervalem; kind N/O/Z/I."""
        if place.count("/") >= 2:
            paths = [place.strip("/")]
        else:
            paths = [p["path"] for p in self.find_parishes(place, dioceses)]
        kind = (kind or "").upper() or None
        out: list[Register] = []
        for path in paths:
            for r in self.parish_registers(path):
                if kind and kind not in r.kinds:
                    continue
                if year_from and r.year_to and r.year_to < year_from:
                    continue
                if year_to and r.year_from and r.year_from > year_to:
                    continue
                out.append(r)
        return out[:limit]

    # --- detail svazku --------------------------------------------------------------------
    def register_info(self, register_id: str) -> Register:
        rid = register_id.strip("/")
        parish_path, sig = rid.rsplit("/", 1)
        reg = next((r for r in self.parish_registers(parish_path) if r.id == rid), None)
        t = self._html(rid, ttl=30 * 86400)
        files, labels = _js_array(t, "files"), _js_array(t, "labels")
        if reg is None:
            title = _clean((_RE_TITLE.search(t) or [None, ""])[1]).split("|")
            reg = Register(module=self.id, id=rid, title=title[0].strip(), archive=self.archive,
                           fond="Matricula Online", signature=sig, digitized=True, url=f"{BASE}/de/{rid}/")
        reg.pages = [Page(image=i + 1, file_id=f, name=(labels[i] if i < len(labels) else None))
                     for i, f in enumerate(files)]
        reg.image_count = len(reg.pages) or None
        return reg

    # --- snímky ---------------------------------------------------------------------------
    def _page(self, reg: Register, image: int) -> Page:
        if not reg.pages:
            raise ValueError(f"svazek {reg.id} nemá zveřejněné snímky")
        if not 1 <= image <= len(reg.pages):
            raise ValueError(f"snímek {image} mimo rozsah 1–{len(reg.pages)}")
        return reg.pages[image - 1]

    def page_url(self, register_id: str, image: int) -> str:
        """Odkaz do prohlížeče pro člověka (snímek sám modul nestahuje)."""
        reg = self.register_info(register_id)
        self._page(reg, image)
        return self.viewer_url(reg, image)

    def viewer_url(self, reg: Register, image: int) -> str:
        # odkaz pro člověka do prohlížeče; modul ho nikdy nestahuje (robots.txt: Disallow /*?pg=)
        return f"{BASE}/de/{reg.id}/?pg={image}"

    def fetch_page(self, register_id: str, image: int, dest: Path, sidecar: bool = True,
                   entry: str | None = None) -> Path:
        """Nepodporováno: obrazový server vydává snímky jen prohlížeči na stránce `?pg=` (robots.txt ji
        automatům zakazuje) — obejít to podvržením Origin/Referer nesmíme. Snímek otevře uživatel sám
        přes `page_url` a sken/screenshot dá do `doklady/`."""
        reg = self.register_info(register_id)
        self._page(reg, image)
        raise PermissionError(
            "Matricula: snímky jen v prohlížeči (403 mimo prohlížeč, robots.txt zakazuje ?pg=). "
            f"Otevři ručně: {self.viewer_url(reg, image)} — viz docs/archivy/matricula.md")

    # --- citace ---------------------------------------------------------------------------
    def citation(self, register: Register, image: int | None, entry: str | None = None) -> Citation:
        r = register
        years = (f"{r.year_from}–{r.year_to}" if r.year_from and r.year_to and r.year_from != r.year_to
                 else str(r.year_from or "") or r.years_text)
        url = r.url
        file_name = None
        if image is not None and r.pages:
            url = self.viewer_url(r, image)
            file_name = self._page(r, image).name
        c = Citation(
            type="matrika", archive=r.archive, fond=r.fond,
            parish=f"Pfarre {r.parish}" if r.parish else None, confession="řkt",
            book="+".join(r.kinds) or None, years=years,
            volume=f"{r.title}" + (f", uloženo: {r.storage}" if r.storage else ""),
            image=image, url=url, accessed=today(), entry=entry, module=self.id,
            register_id=r.id, image_file=file_name,
        )
        c.text = citation_text(c)
        return c


MODULE = Matricula
