"""SOA v Třeboni — DigiArchiv (digi.ceskearchivy.cz): matriky jižních Čech a dalších fondů.

Stavová PHP aplikace (DigiArchiv © Martin Hankovec), bez veřejného API. Portál **blokuje
robota podle User-Agentu „genealogy"**, proto modul chodí s browserovým UA a cs hlavičkami
(soukromý rodinný výzkum, snímky po jednom, bez přihlášení — pravidlo AGENTS.md §4). Ověřené
chování a URL tvary: docs/archivy/trebon.md.

Přístupové body:
- hledání: POST `pages/search_result.php` s `sparam` (PHP-serializovaný dotaz) → z výsledku
  se vyberou `id` svazků (`otevridet("mtyp=2&id=<id>…")`),
- popis svazku: `description.php?id=<id>` (farnost, druh matriky + roky „Datace NOZ", fond, NAD,
  počet snímků),
- prohlížeč: `view.php?menu=3&id=<id>&page=<snímek>&r=0` (snímky od 1); hlavní obrázek je
  v JS `Z.showImage("myContainer","<expirace>/<HMAC>/data1/<imgnum>", …)`.

Snímek = Zoomify dlaždice přes `cgi-bin/isrv8.cgi?<expirace>/<HMAC>/data1/<imgnum>.0.<suffix>`.
Token je podepsaný, časově omezený a platí pro **celý obrázek** (sdílí ho `.0.desc`
= IMAGE_PROPERTIES i jednotlivé dlaždice `.0.<tier>-<col>-<row>`). Oficiální export celého JPG
je jen pro přihlášené, proto se plný snímek skládá z dlaždic nejvyšší úrovně (Pillow).
"""

from __future__ import annotations

import hashlib
import html as _html
import http.cookiejar
import io
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..core import (
    Citation, HttpError, RateLimitedClient, Register, citation_text, copy_to, today, write_sidecar,
)

BASE = "https://digi.ceskearchivy.cz"
ARCHIVE = "Státní oblastní archiv v Třeboni"
# Portál odmítá UA „genealogy" → vydáváme se za běžný prohlížeč (jen soukromý výzkum, snímky po jednom).
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")

_CONFESSION = {
    "římskokatolická církev": "řkt",
    "evangelická církev augšpurského vyznání": "ev. a. v.",
    "evangelická církev helvetského vyznání": "ev. h. v.",
    "evangelická církev": "ev.",
    "českobratrská církev evangelická": "čce",
    "církev československá husitská": "čsl.",
    "církev československá": "čsl.",
    "židovská náboženská obec": "izr.",
    "izraelitská": "izr.",
    "pravoslavná církev": "pravosl.",
    "starokatolická církev": "stkat.",
}

_RE_SHOWIMAGE = re.compile(r'Z\.showImage\("myContainer","([^"]+/data1/\d+)"')
_RE_OTEVRIDET = re.compile(r'otevridet\("mtyp=2&id=(\d+)&')
_RE_IMGPROPS = re.compile(r'WIDTH="(\d+)"\s+HEIGHT="(\d+)".*?TILESIZE="(\d+)"', re.S)
# description.php: řádky tabulky popisu „<td>Label</td><td>Hodnota</td>"
_RE_ROW = re.compile(r'<t[dh][^>]*>\s*([^<][^<]{1,40}?)\s*:?\s*</t[dh]>\s*<t[dh][^>]*>(.*?)</t[dh]>', re.S)
# „Datace NOZ": např. „O 1913-1932", „N 1850-1870", „NOZ 1700-1750", „index 1850-1900"
_RE_DATACE = re.compile(r'\b([NOZIi]|index)\s*(\d{4})\s*(?:[-–]\s*(\d{4}))?')
_KIND_LETTER = {"N": "N", "O": "O", "Z": "Z", "I": "I", "i": "I", "index": "I"}


def _clean(s: str | None) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s).replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in s.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _zoomify_tiers(w: int, h: int, ts: int) -> list[tuple[int, int]]:
    """Rozměry (šířka, výška) pro jednotlivé úrovně Zoomify; index = tier, 0 = nejmenší, poslední = plný."""
    dims = [(w, h)]
    while dims[-1][0] > ts or dims[-1][1] > ts:
        cw, ch = dims[-1]
        dims.append(((cw + 1) // 2, (ch + 1) // 2))
    dims.reverse()
    return dims


class _Session:
    """Anonymní session (cookie jar) s browserovým UA nad rate-limitem core klienta.

    Žádné přihlášení — jen session, kterou portál založí sám. Každý požadavek bere slot
    sdíleného zámku (≥ min_interval zvoleného klienta, i mezi procesy).
    """

    def __init__(self, http_client: RateLimitedClient):
        self.http = http_client
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self._booted = False

    def _headers(self, referer: str | None, accept: str) -> dict:
        h = {"User-Agent": BROWSER_UA, "Accept": accept, "Accept-Language": "cs-CZ,cs;q=0.9"}
        if referer:
            h["Referer"] = referer
        return h

    def boot(self) -> None:
        if not self._booted:
            self.get(f"{BASE}/DA?lang=cs")
            self._booted = True

    def get(self, url: str, referer: str | None = None, client: RateLimitedClient | None = None,
            accept: str = "text/html,application/xhtml+xml,*/*;q=0.8") -> bytes:
        req = urllib.request.Request(url, headers=self._headers(referer, accept))
        with (client or self.http)._slot():
            try:
                with self.opener.open(req, timeout=self.http.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from None

    def post(self, url: str, body: bytes, referer: str | None = None) -> str:
        headers = self._headers(referer, "text/html,*/*;q=0.8")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["X-Requested-With"] = "XMLHttpRequest"
        req = urllib.request.Request(url, data=body, method="POST", headers=headers)
        with self.http._slot():
            try:
                with self.opener.open(req, timeout=self.http.timeout) as resp:
                    return resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                raise HttpError(e.code, url, e.read().decode("utf-8", "replace")) from None


def _php_str(v: str) -> str:
    return f's:{len(v.encode("utf-8"))}:"{v}";'


def _search_sparam(term: str) -> str:
    """PHP-serializované tělo globálního hledání (21 polí; neprázdné jen `search`, `userp`)."""
    out = "a:21:{"
    for k, v in (("searchtype", ""), ("search", term), ("autor", ""), ("evc", ""),
                 ("searcharch", ""), ("date_from", ""), ("date_to", "")):
        out += _php_str(k) + _php_str(v)
    out += _php_str("allwords") + "i:0;"
    out += _php_str("userp") + _php_str("1")
    for k in ("date_b_from", "date_b_to", "date_m_from", "date_m_to", "date_d_from", "date_d_to",
              "search_in", "subtyp", "ftx_id2", "ftx_page", "ai", "imagecontent"):
        out += _php_str(k) + _php_str("")
    return out + "}"


class DigiTrebon:
    """SOA v Třeboni — DigiArchiv: matriky jižních Čech, hledání fulltextem, snímky skládané ze Zoomify dlaždic."""

    id = "digi_trebon"
    archive = ARCHIVE
    capabilities = {"registers", "fetch_page", "search_registers_live"}

    def __init__(self, client: RateLimitedClient | None = None):
        self.http = client or RateLimitedClient(self.id, min_interval=2.5)
        # Dlaždice jednoho snímku: jemnější spacing, ale sdílený zámek (stejný klíč) → nikdy paralelně.
        self.img = RateLimitedClient(self.id, min_interval=0.5)
        self.session = _Session(self.http)

    # --- cache textu (HTML / parsované výsledky) -----------------------------------------
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

    # --- URL ------------------------------------------------------------------------------
    def register_url(self, register_id: str) -> str:
        return f"{BASE}/{int(register_id)}"

    def viewer_url(self, register_id: str, image: int) -> str:
        """Lidsky čitelný permalink na snímek (přesměruje na prohlížeč), tak jak ho sdílí uživatel."""
        return f"{BASE}/{int(register_id)}/{int(image)}"

    def page_url(self, register_id: str, image: int) -> str:
        return self.viewer_url(register_id, image)

    # --- popis svazku ---------------------------------------------------------------------
    def _description_html(self, register_id: str) -> str:
        key = f"desc:{int(register_id)}"
        hit = self._cached(key, 7 * 86400)
        if hit is not None:
            return hit
        self.session.boot()
        raw = self.session.get(
            f"{BASE}/description.php?menu=4&id={int(register_id)}&doctree=10&lang=cs",
            referer=self.register_url(register_id),
        ).decode("utf-8", "replace")
        if "Počet snímků" not in raw and "Sídlo farního úřadu" not in raw and "Archivní soubor" not in raw:
            raise ValueError(f"id {register_id}: popisná stránka neobsahuje údaje (neexistuje, nebo chyba portálu)")
        return self._store(key, raw)

    @staticmethod
    def _parse_description(register_id: str, text: str) -> Register:
        rows: dict[str, str] = {}
        for lab, val in _RE_ROW.findall(text):
            lab = _clean(lab)
            if lab and lab not in rows:
                rows[lab] = _clean(val)

        datace = rows.get("Datace NOZ") or ""
        kinds, years = [], []
        for letter, y1, y2 in _RE_DATACE.findall(datace):
            k = _KIND_LETTER.get(letter)
            if k and k not in kinds:
                kinds.append(k)
            years += [int(y1)] + ([int(y2)] if y2 else [])
        yf, yt = (min(years), max(years)) if years else (None, None)

        parish = rows.get("Sídlo farního úřadu") or None
        cirkev = (rows.get("Církev") or "").lower()
        confession = next((v for k, v in _CONFESSION.items() if k in cirkev), rows.get("Církev") or None)
        poradove = rows.get("Pořadové číslo")
        znacka = rows.get("Značka archivního souboru")
        scans = rows.get("Počet snímků")
        title = " ".join(x for x in (parish, poradove) if x) or f"id {register_id}"

        return Register(
            module="digi_trebon",
            id=str(int(register_id)),
            title=title,
            archive=rows.get("Archiv") or ARCHIVE,
            fond=rows.get("Archivní soubor"),
            fond_nad=rows.get("Číslo NAD"),
            parish=parish,
            confession=confession,
            kinds=kinds,
            year_from=yf,
            year_to=yt,
            years_text=datace or None,
            places=rows.get("Kniha vedena pro"),
            signature=poradove or znacka,
            signature_orig=znacka if poradove else None,
            storage=rows.get("Archiv"),
            content_note="; ".join(x for x in (f"okres {rows['Okres']}" if rows.get("Okres") else None,
                                               rows.get("Evidenční jednotka"),
                                               rows.get("Přístupnost")) if x) or None,
            digitized=bool(scans and scans not in ("0", "")),
            image_count=int(scans) if scans and scans.isdigit() else None,
            url=f"{BASE}/{int(register_id)}",
        )

    def register_info(self, register_id: str) -> Register:
        return self._parse_description(register_id, self._description_html(register_id))

    # --- hledání --------------------------------------------------------------------------
    def _search_ids(self, term: str, limit: int) -> list[str]:
        key = f"search:{term}:{limit}"
        hit = self._cached(key, 86400)
        if hit is not None:
            return hit
        self.session.boot()
        body = (f"sparam={urllib.parse.quote(_search_sparam(term))}"
                "&obsah_sn=0&lang=cs&sst=0&order=&ih=600&iw=800&histstore=0").encode("utf-8")
        xml = self.session.post(f"{BASE}/pages/search_result.php?id=0&queryid=&doctree=10",
                                body, referer=f"{BASE}/pages/search.php")
        ids = list(dict.fromkeys(_RE_OTEVRIDET.findall(xml)))
        return self._store(key, ids[:limit])

    def find_registers(self, place: str, year_from: int | None = None, year_to: int | None = None,
                       kind: str | None = None, limit: int = 20) -> list[Register]:
        """Svazky, v jejichž záznamech portál našel místo `place` (fulltext — tj. nápověda, ne úplný
        rejstřík farnosti). Pro každý nalezený svazek stáhne popis a filtruje podle druhu/let.

        Pozn.: fulltext vrací i svazky, kde se obec objeví jen jako bydliště osoby — farnost ověř
        podle pole „Sídlo farního úřadu" / „Kniha vedena pro" v register_info."""
        kind = (kind or "").upper() or None
        regs: list[Register] = []
        # Popis se tahá zvlášť pro každý svazek (≥ 2,5 s) → strop, ať find_registers neběží minuty.
        for rid in self._search_ids(place, min(limit, 25)):
            try:
                regs.append(self.register_info(rid))
            except (HttpError, ValueError):
                continue
        if kind:
            regs = [r for r in regs if kind in r.kinds]
        if year_from or year_to:
            lo, hi = year_from or 0, year_to or 9999
            regs = [r for r in regs
                    if r.year_from is None or (r.year_from <= hi and (r.year_to or r.year_from) >= lo)]
        pl = place.lower()
        regs.sort(key=lambda r: (pl not in (r.places or "").lower(), r.parish or "", r.year_from or 0))
        return regs

    # --- snímek (skládání Zoomify dlaždic) ------------------------------------------------
    def _page_token(self, register_id: str, image: int) -> tuple[str, str]:
        """Čerstvě načte view.php a vrátí (podepsaný základ URL „<exp>/<hmac>/data1/<imgnum>",
        viewer URL). Token je časově omezený — nikdy se necachuje."""
        url = f"{BASE}/view.php?menu=3&id={int(register_id)}&page={int(image)}&r=0"
        html_text = self.session.get(url, referer=self.viewer_url(register_id, image)).decode("utf-8", "replace")
        m = _RE_SHOWIMAGE.search(html_text)
        if not m:
            if "neexistuje" in html_text:
                raise ValueError(f"id {register_id}, snímek {image}: materiál neexistuje (mimo rozsah?)")
            raise RuntimeError(f"view.php {register_id}/{image}: v HTML není Z.showImage (změna portálu?)")
        return m.group(1), url

    def _tile(self, base: str, suffix: str, referer: str) -> bytes:
        url = f"{BASE}/cgi-bin/isrv8.cgi?{base}.0.{suffix}"
        return self.session.get(url, referer=referer, client=self.img, accept="image/*")

    def _compose(self, base: str, referer: str) -> "Image.Image":
        from PIL import Image
        desc = self._tile(base, "desc", referer).decode("utf-8", "replace")
        m = _RE_IMGPROPS.search(desc)
        if not m:
            raise RuntimeError(f"isrv8 .desc bez IMAGE_PROPERTIES: {desc[:120]!r}")
        w, h, ts = int(m[1]), int(m[2]), int(m[3])
        tier = len(_zoomify_tiers(w, h, ts)) - 1          # nejvyšší úroveň = plné rozlišení
        cols, rows = math.ceil(w / ts), math.ceil(h / ts)
        if cols * rows > 2000:
            raise RuntimeError(f"snímek {w}×{h}: {cols * rows} dlaždic přesahuje pojistku 2000")
        canvas = Image.new("RGB", (w, h))
        for r in range(rows):
            for c in range(cols):
                data = self._tile(base, f"{tier}-{c}-{r}", referer)
                if not data[:3] == b"\xff\xd8\xff":
                    raise RuntimeError(f"dlaždice {tier}-{c}-{r} není JPEG (token vypršel?)")
                with Image.open(io.BytesIO(data)) as im:
                    canvas.paste(im.convert("RGB"), (c * ts, r * ts))
        return canvas

    def fetch_page(self, register_id: str, image: int, dest: Path, sidecar: bool = True,
                   entry: str | None = None) -> Path:
        """Stáhne a složí JEDEN snímek (plné rozlišení) do `dest` + sidecar .yml s citací.
        Snímky od 1. Hotový JPEG se cachuje, token se bere vždy čerstvý."""
        reg = self.register_info(register_id)
        if reg.image_count and not 1 <= image <= reg.image_count:
            raise ValueError(f"snímek {image} mimo rozsah 1–{reg.image_count}")
        cache_rel = f"{reg.id}/{reg.id}_{int(image):04d}.jpg"
        cached = self.http.cache_dir / "files" / cache_rel
        if not (cached.exists() and cached.stat().st_size > 0):
            base, referer = self._page_token(register_id, image)
            cached.parent.mkdir(parents=True, exist_ok=True)
            tmp = cached.with_suffix(".jpg.part")
            self._compose(base, referer).save(tmp, "JPEG", quality=90)
            tmp.replace(cached)
        dest = Path(dest).expanduser()
        if dest.suffix.lower() not in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
            dest.mkdir(parents=True, exist_ok=True)
        out = copy_to(cached, dest)
        if sidecar:
            write_sidecar(out, self.citation(reg, image, entry))
        return out

    # --- citace ---------------------------------------------------------------------------
    def citation(self, register: Register, image: int | None, entry: str | None = None) -> Citation:
        r = register
        conf = {"řkt": "ř. k. f. ú.", "ev.": "ev. f. ú.", "ev. a. v.": "ev. a. v. f. ú.",
                "ev. h. v.": "ev. h. v. f. ú.", "čce": "f. ú. ČCE", "čsl.": "čsl. n. o."}
        parish = r.parish
        if parish and r.confession in conf:
            parish = f"{conf[r.confession]} {parish}"
        years = None
        if r.year_from:
            years = f"{r.year_from}–{r.year_to}" if r.year_to and r.year_to != r.year_from else str(r.year_from)
        volume_bits = [f"poř. č. {r.signature}" if r.signature else None, f"id {r.id}"]
        c = Citation(
            type="matrika",
            archive=r.archive or ARCHIVE,
            fond=r.fond,
            fond_nad=r.fond_nad,
            parish=parish,
            confession=r.confession,
            book="+".join(r.kinds) or None,
            years=years,
            volume=", ".join(b for b in volume_bits if b),
            image=image,
            url=self.viewer_url(r.id, image) if image is not None else r.url,
            accessed=today(),
            entry=entry,
            module=self.id,
            register_id=r.id,
        )
        c.text = citation_text(c)
        return c


MODULE = DigiTrebon
