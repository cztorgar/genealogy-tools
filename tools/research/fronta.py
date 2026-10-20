#!/usr/bin/env python3
"""Fronta osob fáze I — v jakém pořadí se osoby zkoumají (docs/metodika/fronta.md).

Pořadí: 1. šedí (zmínka / převzato / bez dossieru), 2. všichni ostatní nezelení (zapsáno, pozastaveno, dokončeno…).
Uvnitř skupiny nejdřív přímí předci, pak vedlejší linie; v obou podle generace od K0001 (blíž → dřív), pak ID.
Každá osoba se prozkoumá tak, že buď přibude další úroveň (rodiče ve stromu), nebo se sepíše závora s obtížností.

Živě ji počítá dashboard (záložka Fronta, `/api/state` → `fronta`). Tenhle skript uloží snímek do
`research/fronta.md` stromu (pro sessions a pro zafixování stavu v gitu).
Použití: fronta.py [strom-dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checklist as cl  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wbconfig  # noqa: E402

GREY = {None, "zmínka", "převzato"}
ANC_RE = re.compile(r"^K\d+(?:-S\d+)?(?:-P[12])*$")
TIERS = {1: "šedí — ještě nezkoumaní", 2: "nezelení — rozpracovaní, chybí položky fáze I"}


def is_ancestor(pid: str, ids: set[str]) -> bool:
    """Přímá linie: Kekule K-čísla a od kotvy manželky (K0001-S2) řetězce -P1/-P2 (jako filtr „jen předci“)."""
    if not ANC_RE.match(pid):
        return False
    if not re.search(r"-S\d+$", pid):
        return True
    return any(k.startswith(pid + "-P") for k in ids)


def tier(d: dict) -> int | None:
    if d.get("stav") == "uzavřeno":
        return None
    return 1 if d.get("stav") in GREY else 2


def build(people: dict[str, dict]) -> list[dict]:
    ids = set(people)
    rows = []
    for pid, d in people.items():
        t = tier(d)
        if t is None:
            continue
        rows.append({"id": pid, "tier": t, "gen": cl.generation(pid), "anc": is_ancestor(pid, ids),
                     "stav": d.get("stav"), "open": d.get("open_items") or [],
                     "parents": d.get("parents_in_tree"), "zavora": (d.get("zavora") or {}).get("obtiznost"),
                     "zavora_fake": bool((d.get("zavora") or {}).get("nehledano")),
                     "blocking": (d.get("kontroly") or {}).get("blocking", 0),
                     "waiting": any(k in ("navrženo", "schváleno") for k in (d.get("patches") or {}))})
    rows.sort(key=lambda r: (r["tier"], not r["anc"], r["gen"], r["id"]))
    for i, r in enumerate(rows, 1):
        r["pos"] = i
    return rows


def todo(r: dict) -> str:
    """Co s osobou udělat — krátce, pro výpis."""
    if r["waiting"]:
        return "čeká na aplikaci patche (manager)"
    if r["blocking"]:
        return "čeká na blokující kontrolu (uživatel)"
    parts = []
    if r["parents"] is False and "rodice" in r["open"]:
        parts.append("rodiče: založit další úroveň, nebo závora")
    rest = [k for k in r["open"] if k != "rodice"]
    if rest:
        parts.append("otevřené: " + ", ".join(rest))
    if r["zavora_fake"]:
        parts.append("závora říká „nehledáno“ — není to závora")
    return "; ".join(parts) or "zkontrolovat checklist"


def snapshot(tree: Path) -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))
    import server  # noqa: E402
    st = server.Tree(tree.resolve(), "http://localhost:5055").state()
    rows, people = st["fronta"], st["people"]
    green = sum(d.get("stav") == "uzavřeno" for d in people.values())
    out = [f"# Fronta fáze I — snímek", "",
           f"*Generuje `tools/research/fronta.py`; živě v dashboardu (záložka Fronta). Pořadí a pravidla: "
           f"`docs/metodika/fronta.md`. Zelených {green} z {len(people)}, ve frontě {len(rows)}.*", ""]
    for t, label in TIERS.items():
        rs = [r for r in rows if r["tier"] == t]
        out += [f"## {t}. {label} ({len(rs)})", "", "| # | ID | jméno | gen. | stav | závora | co udělat |", "|---|---|---|---|---|---|---|"]
        for r in rs:
            d = people[r["id"]]
            out.append(f"| {r['pos']} | {r['id']}{'' if r['anc'] else ' ·'} | {d.get('name') or ''} | {r['gen']} | "
                       f"{r['stav'] or 'bez dossieru'} | {r['zavora'] or ''} | {todo(r)} |")
        out.append("")
    out.append("*`·` = vedlejší linie (ne přímý předek).*")
    return "\n".join(out) + "\n"


def main() -> int:
    tree = Path(sys.argv[1]) if len(sys.argv) > 1 else wbconfig.tree_dir()
    (tree / "research/fronta.md").write_text(snapshot(tree), encoding="utf-8")
    print(tree / "research/fronta.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
