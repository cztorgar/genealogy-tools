"""SOA v Hradci Králové (dř. SOA Zámrsk) — ARchiv ONline (ARON), matriky a sčítací operáty.

Portál: https://aron.vychodoceskearchivy.cz/ — React SPA nad nedokumentovaným JSON API
`/api/aron` (Spring). Popis API a ověřené chování: docs/archivy/aron-zamrsk.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..core import (
    Citation, HttpError, Page, RateLimitedClient, Register, citation_text, copy_to, today,
    write_sidecar,
)

BASE = "https://aron.vychodoceskearchivy.cz"
API = BASE + "/api/aron"

# RECORD~TYPE hodnoty (ověřeno pro N; O/Z podle stejného vzoru, ověřeno testem v README)
_RECORD_TYPE = {
    "N": "záznamy narozených",
    "O": "záznamy oddaných",
    "Z": "záznamy zemřelých",
}
_KIND_WORDS = {"NAROZENÝCH": "N", "ODDANÝCH": "O", "ZEMŘELÝCH": "Z"}
_CONFESSION = {
    "římskokatolická": "řkt",
    "evangelická": "ev.",
    "civilní": "civ.",
    "československá": "čsl.",
    "židovská": "izr.",
    "izraelitská": "izr.",
    "starokatolická": "stkat.",
    "pravoslavná": "pravosl.",
    # indexy mají mužský rod („římskokatolický index NAROZENÝCH“)
    "římskokatolický": "řkt",
    "evangelický": "ev.",
    "československý": "čsl.",
    "židovský": "izr.",
    "izraelitský": "izr.",
}
_NAME_RE = re.compile(r"^(?P<archive>[^:]+):\s*(?P<fond>.+?),\s*sign\.:\s*(?P<sign>.+?\)),\s*(?P<years>[^,]+)$")
_ANY_SIG_RE = re.compile(r"(?P<label>sign\.|inv\. ?č\.|poř\. ?č\.):\s*(?P<value>[^,]+)")


def _years(text: str | None) -> tuple[int | None, int | None]:
    ys = [int(y) for y in re.findall(r"(?<!\d)(\d{4})(?!\d)", text or "")]
    return (min(ys), max(ys)) if ys else (None, None)


def _parse_listing(item: dict) -> Register:
    """Rychlé parsování položky výsledku hledání (bez dalšího požadavku).

    Matrika:  name = "<archiv>: <fond>, sign.: 55-8 (poř.č. 3849), 1855-1859"
              description = "římskokatolická matrika NAROZENÝCH, <obce>"
    Ostatní:  name = "<archiv>: <fond>, inv. č.: 1435, 1910", description = volný text
    """
    name = item.get("name") or ""
    desc = item.get("description") or ""
    archive, fond, sign, years = None, None, None, None
    m = _NAME_RE.match(name)
    if m:
        archive, fond, sign, years = m["archive"], m["fond"], m["sign"], m["years"].strip()
    else:
        if ":" in name:
            archive, rest = name.split(":", 1)
            fond = rest.strip().split(", ", 1)[0]
        s = _ANY_SIG_RE.search(name)
        sign = f"{s['label']} {s['value'].strip()}" if s else None
        years = name.rsplit(",", 1)[-1].strip() if "," in name else None
    words = desc.split(", ", 1)[0].split()
    unit = words[1] if len(words) > 1 else None
    confession, kinds, places = None, [], desc
    if unit in ("matrika", "index"):
        confession = _CONFESSION.get(words[0], words[0])
        head = desc.split("(")[0][:120]
        kinds = (["I"] if unit == "index" else []) + [k for w, k in _KIND_WORDS.items() if w in head]
        places = desc.split(", ", 1)[1] if ", " in desc else ""
        # odříznout další druhy („NAROZENÝCH, ODDANÝCH, …“) na začátku seznamu obcí
        while places.split(", ", 1)[0].strip() in _KIND_WORDS:
            places = places.split(", ", 1)[1] if ", " in places else ""
    yf, yt = _years(years)
    return Register(
        module="aron_zamrsk",
        id=item["id"],
        title=name,
        archive=(archive or "Státní oblastní archiv v Hradci Králové").strip(),
        fond=fond,
        confession=confession,
        kinds=kinds,
        year_from=yf,
        year_to=yt,
        years_text=years,
        places=places or desc,
        signature=sign,
        url=f"{BASE}/apu/{item['id']}",
    )


class AronZamrsk:
    """SOA v Hradci Králové / Zámrsk — ARON: matriky východních Čech, sčítací operáty, ZIP celých sad."""

    id = "aron_zamrsk"
    archive = "Státní oblastní archiv v Hradci Králové"
    capabilities = {"registers", "census", "fetch_page", "register_zip_info", "official_citation"}

    def __init__(self, client: RateLimitedClient | None = None):
        self.http = client or RateLimitedClient(self.id, min_interval=2.5)

    # --- hledání --------------------------------------------------------------------------
    def _search(self, filters: list[dict], limit: int = 300, page_size: int = 100) -> tuple[int, list[dict]]:
        items: list[dict] = []
        offset, count = 0, 0
        while True:
            body = {"filters": filters, "offset": offset, "size": page_size}
            data = self.http.json(f"{API}/apu/listview?listType=ARCH_DESC", "POST", body, ttl=86400)
            count = data.get("count") or 0
            batch = data.get("items") or []
            items.extend(batch)
            offset += len(batch)
            if not batch or offset >= count or len(items) >= limit:
                return count, items[:limit]

    def find_registers(self, place: str, year_from: int | None = None, year_to: int | None = None,
                       kind: str | None = None, limit: int = 300) -> list[Register]:
        """Svazky, jejichž popis / zeměpisný rejstřík obsahuje `place` a jejichž datace se
        překrývá s intervalem. kind: N/O/Z/I (matriky) nebo S (sčítací operáty)."""
        kind = (kind or "").upper() or None
        unit_type = "sčítací operát" if kind == "S" else "matrika"
        filters: list[dict] = [
            {"field": "type", "operation": "EQ", "value": "ARCH_DESC"},
            {"field": "UNIT~TYPE", "operation": "EQ", "value": unit_type},
            {"operation": "FTX", "value": place},
        ]
        if kind in _RECORD_TYPE:
            filters.append({"field": "RECORD~TYPE", "operation": "EQ", "value": _RECORD_TYPE[kind]})
        if year_from or year_to:
            filters.append({
                "field": "UNIT~DATE", "operation": "RANGE",
                "gte": f"{int(year_from or 1):04d}-01-01T00:00:00.000Z",
                "lte": f"{int(year_to or 2100):04d}-12-31T23:59:59.999Z",
            })
        _, items = self._search(filters, limit=limit)
        regs = [_parse_listing(i) for i in items]
        if kind == "I":
            regs = [r for r in regs if "I" in r.kinds]
        if kind == "S":
            for r in regs:
                r.kinds = ["S"]
        # obec přímo v popisu svazku napřed; ostatní (shoda jen přes rejstřík, např. místní část)
        # nech na konci — fulltext ARONu hledá i v názvech hesel zeměpisného rejstříku
        pl = place.lower()
        regs.sort(key=lambda r: (pl not in (r.places or "").lower(), r.year_from or 0, r.signature or ""))
        return regs

    # --- detail svazku --------------------------------------------------------------------
    def _apu(self, apu_id: str) -> dict:
        return self.http.json(f"{API}/apu/{apu_id}", ttl=7 * 86400)

    def _view(self, apu_id: str) -> dict:
        return self.http.json(f"{API}/apu/{apu_id}/view", ttl=30 * 86400)

    @staticmethod
    def _items(parts: list[dict], acc: dict | None = None) -> dict[str, list[dict]]:
        acc = {} if acc is None else acc
        for p in parts or []:
            for it in p.get("items") or []:
                acc.setdefault(it["type"], []).append(it)
            AronZamrsk._items(p.get("childParts") or [], acc)
        return acc

    def register_info(self, register_id: str, resolve: bool = True) -> Register:
        d = self._apu(register_id)
        if d.get("type") != "ARCH_DESC":
            raise ValueError(f"{register_id} není archiválie (type={d.get('type')})")
        reg = _parse_listing({"id": d["id"], "name": d.get("name"), "description": d.get("description")})
        items = self._items(d.get("parts") or [])

        def first(t):
            v = items.get(t)
            return v[0]["value"] if v else None

        reg.signature = first("OTHERID~SIG") or reg.signature
        reg.signature_orig = first("OTHERID~SIG~ORIG")
        reg.storage = first("STORAGE")
        reg.content_note = "; ".join(i["value"] for i in items.get("UNIT~CONTENT", [])) or None
        reg.size_note = first("SIZE")
        ud = first("UNIT~DATE")
        if ud:
            try:
                u = json.loads(ud)
                reg.year_from = int(u["from"][:4])
                reg.year_to = int(u["to"][:4])
            except (ValueError, KeyError, TypeError):
                pass
        rts = [i["value"] for i in items.get("RECORD~TYPE", [])]
        kinds = [k for k, v in _RECORD_TYPE.items() if v in rts]
        if kinds:
            reg.kinds = (["I"] if "I" in reg.kinds else []) + kinds
        if "sčítací operát" in [i["value"] for i in items.get("UNIT~TYPE", [])]:
            reg.kinds = ["S"]
        for u in items.get("URL", []):
            if (u.get("href") or "").endswith(".zip"):
                reg.zip_url = u["href"]
        reg.digitized = (first("DIGITAL") or "").lower() == "ano" or bool(d.get("digitalObjects"))

        # snímky: soubory typu PUBLISHED, řazeno podle DAO a pořadí
        pages: list[Page] = []
        for dao in sorted(d.get("digitalObjects") or [], key=lambda x: x.get("order") or 0):
            pub = sorted((f for f in dao.get("files") or [] if f.get("type") == "PUBLISHED"),
                         key=lambda f: f.get("order") or 0)
            for f in pub:
                pages.append(Page(image=len(pages) + 1, file_id=f["id"], name=f.get("name"),
                                  size=f.get("size"), content_type=f.get("contentType")))
        reg.pages = pages
        reg.image_count = len(pages) or None
        if pages and pages[0].name and pages[0].name.startswith("CZ_"):
            bits = pages[0].name.split("_")
            if len(bits) > 3:
                reg.set_id = bits[3]

        # farnost / matriční úřad = popis rodičovského uzlu stromu sbírky
        parent = d.get("parent") or {}
        reg.parish = parent.get("description") or None
        if resolve:
            orig_id = None
            p = d
            while p and not orig_id:
                orig_id = (self._items(p.get("parts") or []).get("ORIGINATOR~REF") or [{}])[0].get("value")
                p = p.get("parent")
            if orig_id:
                try:
                    reg.originator = self._view(orig_id).get("name")
                except HttpError:
                    pass
            try:
                cit = self.http.json(f"{API}/script/citation/{register_id}", ttl=30 * 86400)
                reg.official_citation = cit.get("citation")
                m = re.search(r"\(NAD (\d+)\)", reg.official_citation or "")
                reg.fond_nad = m.group(1) if m else None
            except HttpError:
                pass
        return reg

    # --- snímky ---------------------------------------------------------------------------
    def _page(self, reg: Register, image: int) -> Page:
        if not reg.pages:
            raise ValueError(f"svazek {reg.id} nemá zveřejněné snímky")
        if not 1 <= image <= len(reg.pages):
            raise ValueError(f"snímek {image} mimo rozsah 1–{len(reg.pages)}")
        return reg.pages[image - 1]

    def page_url(self, register_id: str, image: int) -> str:
        reg = self.register_info(register_id, resolve=False)
        return f"{API}/referencedfiles/{self._page(reg, image).file_id}"

    def viewer_url(self, reg: Register, image: int) -> str:
        p = self._page(reg, image)
        # trasa SPA /apu/:id/dao/:daoId/file/:fileId (DAO id = id záznamu u matrik)
        return f"{BASE}/apu/{reg.id}/dao/{reg.id}/file/{p.file_id}"

    def fetch_page(self, register_id: str, image: int, dest: Path, sidecar: bool = True,
                   entry: str | None = None) -> Path:
        """Stáhne jeden snímek (přes cache) do `dest` (adresář nebo soubor) + sidecar .yml."""
        reg = self.register_info(register_id)
        p = self._page(reg, image)
        name = p.name or f"{register_id}_{image:05d}.jpg"
        cached = self.http.download(f"{API}/referencedfiles/{p.file_id}", f"{register_id}/{name}")
        dest = Path(dest).expanduser()
        if dest.suffix.lower() not in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
            dest.mkdir(parents=True, exist_ok=True)   # dest = adresář
        out = copy_to(cached, dest)
        if sidecar:
            write_sidecar(out, self.citation(reg, image, entry), {"source_file": p.name})
        return out

    def register_zip_info(self, register_id: str) -> dict:
        """Jen HEAD na oficiální ZIP celé sady snímků — nic nestahuje."""
        reg = self.register_info(register_id, resolve=False)
        if not reg.zip_url:
            return {"zip_url": None, "note": "svazek nemá odkaz na ZIP"}
        h = self.http.head(reg.zip_url)
        size = int(h.get("content-length") or 0)
        return {"zip_url": reg.zip_url, "status": h.get("status"), "bytes": size,
                "mb": round(size / 1e6, 1), "last_modified": h.get("last-modified"),
                "images": reg.image_count}

    # --- citace ---------------------------------------------------------------------------
    def citation(self, register: Register, image: int | None, entry: str | None = None) -> Citation:
        r = register
        conf = {"řkt": "ř. k. f. ú.", "ev.": "ev. f. ú.", "civ.": "civilní matrika", "čsl.": "čsl. n. o."}
        parish = r.parish
        if parish and r.confession in conf and r.confession != "civ.":
            parish = f"{conf[r.confession]} {parish}"
        years = (f"{r.year_from}–{r.year_to}" if r.year_from and r.year_to and r.year_from != r.year_to
                 else str(r.year_from or "") or r.years_text)
        volume = f"sign. {r.signature}" if r.signature else None
        if r.signature_orig:
            volume = f"{volume}, sign. pův. {r.signature_orig}" if volume else f"sign. pův. {r.signature_orig}"
        url = r.url
        file_name = None
        if image is not None and r.pages:
            url = self.viewer_url(r, image)
            file_name = self._page(r, image).name
        c = Citation(
            type="matrika" if "S" not in r.kinds else "sčítání lidu",
            archive=r.archive,
            fond=r.fond,
            parish=parish,
            confession=r.confession,
            book=None if "S" in r.kinds else ("+".join(r.kinds) or None),
            years=years,
            volume=volume,
            image=image,
            url=url,
            accessed=today(),
            entry=entry,
            module=self.id,
            register_id=r.id,
            image_file=file_name,
            set_id=r.set_id,
            fond_nad=r.fond_nad,
            official_citation=r.official_citation,
        )
        c.text = citation_text(c)
        return c


MODULE = AronZamrsk
