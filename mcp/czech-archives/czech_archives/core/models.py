"""Datové typy sdílené všemi moduly: Register, Page, Citation, ArchiveModule."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable

# Druhy matričních knih (zkratky podle docs/metodika/citace.md)
KINDS = {
    "N": "narození",
    "O": "oddaní",
    "Z": "zemřelí",
    "I": "index",
    "S": "sčítací operát",  # není matrika, ale moduly ho mohou vracet stejným rozhraním
}


@dataclass
class Page:
    """Jeden snímek svazku (číslování snímků od 1, tak jak je ukazuje prohlížeč portálu)."""

    image: int
    file_id: str
    name: str | None = None
    size: int | None = None
    content_type: str | None = None


@dataclass
class Register:
    """Svazek (matrika, index, sčítací operát) tak, jak ho popisuje portál."""

    module: str
    id: str
    title: str                      # název záznamu na portálu
    archive: str                    # archiv (instituce)
    fond: str | None = None         # archivní soubor
    fond_nad: str | None = None     # číslo NAD
    parish: str | None = None       # farnost / matriční úřad / obec
    originator: str | None = None   # původce podle rejstříku portálu
    confession: str | None = None   # řkt, ev. a. v., civ. …
    kinds: list[str] = field(default_factory=list)   # N/O/Z/I/S
    year_from: int | None = None
    year_to: int | None = None
    years_text: str | None = None   # datace tak, jak ji uvádí portál (např. „2.1906-1949“)
    places: str | None = None       # obce (popis svazku)
    signature: str | None = None    # sign. (poř. č.)
    signature_orig: str | None = None
    storage: str | None = None      # ukládací jednotka
    content_note: str | None = None
    size_note: str | None = None
    digitized: bool = False
    image_count: int | None = None
    set_id: str | None = None       # identifikátor sady snímků (je i v názvu souborů)
    url: str | None = None          # odkaz na záznam v prohlížeči
    zip_url: str | None = None      # oficiální stažení celé sady snímků
    official_citation: str | None = None
    pages: list[Page] = field(default_factory=list, repr=False)

    def to_dict(self, with_pages: bool = False) -> dict:
        d = asdict(self)
        if not with_pages:
            d.pop("pages", None)
        return d


@dataclass
class Citation:
    """Strukturovaná citace snímku (vzor: docs/metodika/citace.md)."""

    type: str
    archive: str
    fond: str | None
    parish: str | None
    confession: str | None
    book: str | None
    years: str | None
    volume: str | None
    image: int | None
    url: str | None
    accessed: str
    folio: str | None = None
    entry: str | None = None
    # rozšíření oproti vzoru — pomáhají snímek najít znovu
    module: str | None = None
    register_id: str | None = None
    image_file: str | None = None
    set_id: str | None = None
    fond_nad: str | None = None
    official_citation: str | None = None
    text: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "")}


@runtime_checkable
class ArchiveModule(Protocol):
    id: str
    archive: str
    capabilities: set[str]

    def find_registers(
        self,
        place: str,
        year_from: int | None = None,
        year_to: int | None = None,
        kind: str | None = None,
    ) -> list[Register]: ...

    def register_info(self, register_id: str) -> Register: ...

    def page_url(self, register_id: str, image: int) -> str: ...

    def fetch_page(self, register_id: str, image: int, dest: Path) -> Path: ...

    def citation(self, register: Register, image: int | None, entry: str | None = None) -> Citation: ...


def describe(mod: ArchiveModule) -> dict:
    return {
        "id": mod.id,
        "archive": mod.archive,
        "capabilities": sorted(mod.capabilities),
        "doc": (mod.__doc__ or "").strip().splitlines()[0] if mod.__doc__ else "",
    }


def iter_ok(items: Iterable) -> list:
    return [i for i in items if i is not None]
