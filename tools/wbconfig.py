#!/usr/bin/env python3
"""Lokální konfigurace workbenche: `genealogy.toml` v kořeni (gitignored, vzor `genealogy.example.toml`).

Pořadí: proměnná prostředí (GENEALOGY_TREE, GENEALOGY_RESEARCHER) > genealogy.toml > výchozí hodnoty.
Z shellu: `python3 tools/wbconfig.py get strom.adresar` (vypíše hodnotu; seznam po řádcích).
"""
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[1]
CONFIG = WORKBENCH / "genealogy.toml"
DEFAULTS = {
    "strom": {"adresar": "", "gramps_strom": "", "strany": {}},
    "badatel": {"jmeno": ""},
    "sessions": {"ucty": [], "ucty_bez_chrome": []},
}


def load() -> dict:
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    if CONFIG.exists():
        for sec, vals in tomllib.loads(CONFIG.read_text(encoding="utf-8")).items():
            cfg.setdefault(sec, {}).update(vals)
    return cfg


def get(key: str, default=None):
    node = load()
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def tree_dir() -> Path:
    """Adresář aktivního stromu: GENEALOGY_TREE, jinak `strom.adresar` (relativně ke kořeni workbenche)."""
    raw = os.environ.get("GENEALOGY_TREE") or get("strom.adresar")
    if not raw:
        sys.exit("není nastaven strom: vyplň strom.adresar v genealogy.toml (vzor genealogy.example.toml), "
                 "nebo GENEALOGY_TREE, nebo předej cestu ke stromu argumentem")
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (WORKBENCH / p).resolve()


def researcher() -> str:
    """Jméno badatele — informátor u ústního sdělení (citace „Ústní sdělení — <jméno>“)."""
    return os.environ.get("GENEALOGY_RESEARCHER") or get("badatel.jmeno") or "badatel"


def side(pid: str) -> str:
    """Popisek strany rodu podle nejdelšího prefixu ID ze `strom.strany` (např. K0001-S2 = manželka)."""
    sides = get("strom.strany") or {}
    best = max((p for p in sides if p != "K0001" and (pid == p or pid.startswith(p + "-"))), key=len, default=None)
    return sides[best] if best else sides.get("K0001", "K0001")   # Kekule čísla = strana výchozí osoby


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "get":
        v = tree_dir() if sys.argv[2] == "strom.adresar" else get(sys.argv[2], "")
        print("\n".join(map(str, v)) if isinstance(v, list) else v)
    else:
        sys.exit(__doc__)
