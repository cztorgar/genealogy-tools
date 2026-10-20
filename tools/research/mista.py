#!/usr/bin/env python3
"""Přehled obcí, kde se předci stromu vyskytují (z aplikovaných patchů) → `research/mista.md` ve stromu.

Pro každé místo: počet osob a událostí, rozpětí let, příjmení, strana stromu (uživatel / partnerka podle kotvy
K0001-S2), čísla popisná, a z místopisu workbenche (docs/mistopis/*/obce.md) fara a okres, pokud jsou.
Seskupeno podle oblasti (místopisná kapitola, jinak „mimo místopis“). Spouštět po dávce patchů.

Použití: mista.py [strom-dir]
"""
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wbconfig  # noqa: E402

WB = Path(__file__).resolve().parents[2]
CP = re.compile(r"(?:č\.\s*p\.|čp\.|č\.)\s*(\d+(?:/[IVX]+)?)")
YEAR = re.compile(r"(1[5-9]\d\d|20\d\d)")


def fold(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def gazetteer() -> dict:
    """název obce → (oblast, fara, okres) z tabulek obce.md (sloupce: obec | dnes | kód | GPS | fara | panství | …)."""
    out = {}
    for f in sorted((WB / "docs/mistopis").glob("*/obce.md")):
        area = f.parent.name
        for line in f.read_text(encoding="utf-8").splitlines():
            cells = [c.strip(" *") for c in line.strip().strip("|").split("|")]
            if len(cells) < 5 or not re.search(r"\d+\.\d+,\s*\d+\.\d+", line):
                continue
            name = re.sub(r"\s*\(.*?\)", "", cells[0]).strip()
            out.setdefault(fold(name), (area, cells[4], cells[1]))
    return out


def side(pid: str) -> str:
    return wbconfig.side(pid)


def main(tree: Path) -> int:
    gaz = gazetteer()
    places = defaultdict(lambda: {"ids": set(), "events": 0, "years": [], "cps": set(), "sides": set(), "names": set()})
    names = {}
    for f in (tree / "research/people").glob("*.md"):
        m = re.match(r"(K\d{4}(?:-[SCP]\d+)*)-[a-z]", f.name)
        t = re.search(r"^# (.+?) \(", f.read_text(encoding="utf-8"), re.M) if m else None
        if m and t:
            names[m.group(1)] = t.group(1).split()[-1]
    for p in sorted((tree / "patches").glob("P-*.yml")):
        try:
            d = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(d, dict) or d.get("status") != "aplikováno":
            continue
        pid = re.match(r"P-(.+)-\d+\.yml", p.name).group(1)
        for ch in d.get("changes") or []:
            if not isinstance(ch, dict) or ch.get("op") != "add_event" or not ch.get("place"):
                continue
            pl = str(ch["place"]).strip()
            e = places[pl]
            ids = [str(x) for x in ch["family"]] if ch.get("family") else [pid]
            for i in ids:
                e["ids"].add(i)
                e["sides"].add(side(i))
                if i in names:
                    e["names"].add(names[i])
            e["events"] += 1
            y = YEAR.search(str(ch.get("date") or ""))
            if y:
                e["years"].append(int(y.group(1)))
            for c in CP.findall(str(ch.get("description") or "")):
                e["cps"].add(c)
    region = {}
    oy = WB / "docs/mistopis/oblasti.yml"
    if oy.exists():
        for area, lst in (yaml.safe_load(oy.read_text(encoding="utf-8")) or {}).items():
            for n in lst or []:
                region[fold(n)] = area
    groups = defaultdict(list)
    for pl, e in places.items():
        g = gaz.get(fold(pl))
        groups[region.get(fold(pl)) or (g[0] if g else "nezařazeno")].append((pl, e, g))
    lines = [f"# Místa předků — {tree.name}", "",
             f"*Generováno `tools/research/mista.py` {date.today().isoformat()} z aplikovaných patchů (události s místem). "
             f"Neupravovat ručně — přegenerovat. Fara/okres z `docs/mistopis/*/obce.md`.*", "",
             f"Celkem **{len(places)} míst**, {sum(e['events'] for e in places.values())} událostí.", ""]
    for area in sorted(groups, key=lambda a: (a in ("nezařazeno", "mimo region"), -sum(len(r[1]["ids"]) for r in groups[a]))):
        rows = sorted(groups[area], key=lambda r: -len(r[1]["ids"]))
        lines += [f"## {area} ({len(rows)})", "",
                  "| Místo | Osob | Událostí | Roky | Strana | Příjmení | Č. p. | Fara (místopis) |",
                  "|---|---|---|---|---|---|---|---|"]
        for pl, e, g in rows:
            yrs = f"{min(e['years'])}–{max(e['years'])}" if e["years"] else "—"
            cps = ", ".join(sorted(e["cps"], key=lambda c: int(re.match(r"\d+", c).group())))[:60] or "—"
            nm = ", ".join(sorted(e["names"]))[:80] or "—"
            lines.append(f"| {pl} | {len(e['ids'])} | {e['events']} | {yrs} | {' + '.join(sorted(e['sides']))} | {nm} | {cps} | "
                         f"{(g[1] if g else '—')[:40]} |")
        lines.append("")
    out = tree / "research/mista.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(places)} míst, oblasti: " + ", ".join(f"{a} {len(r)}" for a, r in groups.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else wbconfig.tree_dir()))
