#!/usr/bin/env python3
"""Založí nový strom ze šablony `templates/strom/` (adresářová struktura, TREE.md, logy) a `git init`.

Použití: init_tree.py <adresář-stromu> --nazev novak --k0001 "Jan Novák (*1980)"
Potom: nastav `strom.adresar` v genealogy.toml a založ osoby (docs/prirucka.md, kap. Založení stromu).
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "strom"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    ap.add_argument("--nazev", required=True, help="krátký název stromu (malá písmena, bez diakritiky)")
    ap.add_argument("--k0001", default="(doplnit)", help="výchozí osoba — jméno a rok narození")
    a = ap.parse_args()
    if a.tree.exists() and any(a.tree.iterdir()):
        sys.exit(f"{a.tree} už existuje a není prázdný")
    shutil.copytree(TEMPLATE, a.tree, dirs_exist_ok=True)
    tree_md = a.tree / "TREE.md"
    tree_md.write_text(tree_md.read_text(encoding="utf-8").replace("{{NAZEV}}", a.nazev)
                       .replace("{{K0001}}", a.k0001).replace("{{DATUM}}", dt.date.today().isoformat()), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(a.tree)], check=True)
    print(f"strom založen: {a.tree.resolve()}\n"
          f"dál: genealogy.toml → [strom] adresar = \"{a.tree}\", gramps_strom = \"{a.nazev}\"; "
          f"pak osoby (build_queue.py z GEDCOM, nebo add_person.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
