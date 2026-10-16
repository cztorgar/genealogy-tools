"""Citace: text podle docs/metodika/citace.md a sidecar .yml vedle snímku.

YAML se píše ručně (bez PyYAML) — jen ploché klíče, řetězce se vždy uvozují.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from .models import Citation

# Pořadí klíčů v sidecaru: nejdřív pole ze vzoru v citace.md, pak rozšíření.
_ORDER = [
    "type", "archive", "fond", "parish", "confession", "book", "years", "volume", "folio",
    "image", "url", "accessed", "entry",
    "module", "register_id", "image_file", "set_id", "fond_nad", "official_citation", "text",
]


def today() -> str:
    return _dt.date.today().isoformat()


def czech_date(iso: str) -> str:
    d = _dt.date.fromisoformat(iso)
    return f"{d.day}. {d.month}. {d.year}"


def _yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_yaml_scalar(x) for x in v) + "]"
    # JSON string je platný YAML double-quoted scalar
    return json.dumps(str(v), ensure_ascii=False)


def to_yaml(data: dict, extra: dict | None = None) -> str:
    merged = dict(data)
    if extra:
        merged.update({k: v for k, v in extra.items() if v is not None})
    keys = [k for k in _ORDER if k in merged] + [k for k in merged if k not in _ORDER]
    lines = [f"{k}: {_yaml_scalar(merged[k])}" for k in keys]
    return "\n".join(lines) + "\n"


def write_sidecar(image_path: Path, citation: Citation, extra: dict | None = None) -> Path:
    """Zapíše <snímek>.yml vedle snímku. Existující sidecar nepřepisuje (může mít ruční doplnění)."""
    yml = image_path.with_suffix(".yml")
    if yml.exists():
        return yml
    body = to_yaml(citation.to_dict(), {"file": image_path.name, **(extra or {})})
    yml.write_text(body, "utf-8")
    return yml


def citation_text(c: Citation) -> str:
    """Text citace podle vzoru:
    *SOA Zámrsk, Sbírka matrik Východočeského kraje, ř. k. f. ú. Chlumec nad Cidlinou, N 1850–1860,
    inv. č. 1234, fol. 12v, snímek 18, zápis …. Online: <url>, cit. 20. 10. 2026.*
    """
    parts = [c.archive]
    if c.fond:
        parts.append(c.fond + (f" (NAD {c.fond_nad})" if c.fond_nad else ""))
    if c.parish:
        parts.append(c.parish)
    if c.book or c.years:
        parts.append(" ".join(x for x in (c.book, c.years) if x))
    if c.volume:
        parts.append(c.volume)
    if c.folio:
        parts.append(c.folio)
    if c.image is not None:
        parts.append(f"snímek {c.image}")
    if c.entry:
        parts.append(f"zápis {c.entry}")
    text = ", ".join(parts) + "."
    if c.url:
        text += f" Online: {c.url}, cit. {czech_date(c.accessed)}."
    return text
