#!/usr/bin/env python3
"""Doplní do sekce `## Závora` řádek `- **obtížnost:** nízká | střední | velká — proč`, kde chybí.

Odhad je hrubý (podle textu „proč“ a „co by závoru prolomilo“) a značí se `(odhad managera <datum>)`;
session nebo uživatel ho přepíše. Existující obtížnost se nemění. Škála: docs/metodika/fronta.md.
Použití: zavory_obtiznost.py <strom-dir> [--dry-run]
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checklist as cl  # noqa: E402

SEC_RE = re.compile(r"^## Závora\n(.*?)(?=^## |\Z)", re.M | re.S)
FIELD_RE = r"\*\*{}[^*]*\*\*:?\s*([^\n·]*)"
CHANCES = ["prakticky žádná", "žádná", "nízká", "malá", "střední", "vysoká"]
OFFLINE = re.compile(r"badateln|dotaz|žádost|výpis|matriční úřad|rodin|doklad|ústní|návštěv|soka|\bvúa\b|kmenov", re.I)
INDIRECT = re.compile(r"pozemkov|katastr|soupis|urbář|gruntovn|poddansk|pamětní kniha", re.I)
UNSEARCHED = re.compile(r"rozpočet|nezkoum|hranice dávky|konec dávky|mimo rozsah", re.I)


def field(body: str, name: str) -> str:
    m = re.search(FIELD_RE.format(name), body, re.I)
    return m.group(1).strip() if m else ""


def estimate(body: str) -> tuple[str, str] | None:
    proc, prol = field(body, "proč"), field(body, "co by")
    if len(proc.strip(" —–-.")) < 3 and len(prol.strip(" —–-.")) < 3:
        return None
    found = [c for c in CHANCES if re.search(rf"\b{c}\b", prol, re.I)]
    best = max(found, key=CHANCES.index) if found else None
    unsearched = bool(cl.NOT_SEARCHED.search(proc) or UNSEARCHED.search(proc))
    if unsearched and best in ("vysoká", None) and not OFFLINE.search(prol):
        return "nízká", "pramen je online, jen se do něj ještě nepodívalo"
    if best in ("prakticky žádná", "žádná", "nízká", "malá"):
        if INDIRECT.search(prol):
            return "velká", "matriky došly; zbývají jen nepřímé prameny (pozemkové knihy, katastry, soupisy)"
        return "velká", "malá šance i podle session; cesty nejisté"
    if OFFLINE.search(prol) and not re.search(r"online|digitaliz", prol, re.I):
        return "střední", "online nic není; potřeba dopis do archivu / matriční úřad / doklad od rodiny"
    if unsearched:
        return "střední", "online, ale bez rejstříku nebo s nejistým místem — více snímků"
    if best == "vysoká":
        return "nízká", "známý online svazek, který by měl zápis obsahovat"
    return "střední", "online cesty existují, ale bez jistoty (jiná fara, listování bez rejstříku)"


def main() -> int:
    tree = Path(sys.argv[1])
    dry = "--dry-run" in sys.argv
    today = dt.date.today().isoformat()
    stats: dict[str, int] = {}
    missing = []
    for f in sorted((tree / "research/people").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        m = SEC_RE.search(t)
        if not m or not m.group(1).strip() or cl.OBTIZNOST_RE.search(m.group(1)):
            continue
        body = m.group(1)
        est = estimate(body)
        if not est:
            missing.append(f.name)
            continue
        level, why = est
        stats[level] = stats.get(level, 0) + 1
        line = f"- **obtížnost:** {level} — {why} (odhad managera {today})\n"
        # za blok „co by závoru prolomilo“ (včetně pokračovacích řádků), jinak na konec výčtu
        lines = body.splitlines(keepends=True)
        at = next((i for i, ln in enumerate(lines) if re.match(r"^\s*[-*]\s+\*\*datum", ln, re.I)), None)
        if at is None:
            at = len(lines)
            while at and not lines[at - 1].strip():
                at -= 1
            if lines and not lines[at - 1].endswith("\n"):
                lines[at - 1] += "\n"
        lines.insert(at, line)
        if not dry:
            f.write_text(t[:m.start(1)] + "".join(lines) + t[m.end(1):], encoding="utf-8")
    print(f"doplněno: {stats}" + (" (dry-run)" if dry else ""))
    if missing:
        print(f"bez podkladů pro odhad ({len(missing)}): " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
