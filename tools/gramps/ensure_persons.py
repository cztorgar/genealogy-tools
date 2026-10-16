#!/usr/bin/env python3
"""Založí v Gramps (strom berescak) osoby podle ID workbenche — **jen jméno a pohlaví**.

Existence osoby je důvod ji založit; data, místa a vazby se přidávají až po ověření (patche).
Gramps ID = ID workbenche (K0001, K0001-S1 …); atributy `workbench ID` a `MyHeritage _UID` pro párování.
Jméno se bere z nadpisu dossieru (session ho mohla opravit, např. na rodné příjmení),
pohlaví z exportu MyHeritage. Do dossieru se doplní `gramps_id`. Existující osoby se přeskočí.

Použití: ensure_persons.py <strom-dir> <ID> [<ID> …]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gedcom"))
from gedparse import parse  # noqa: E402
from gw import GrampsWeb  # noqa: E402

TITLE_RE = re.compile(r"^# (.+?) \(([^)]+)\)\s*$", re.M)
GENDER = {"F": 0, "M": 1}


def dossier_for(people: Path, pid: str) -> Path:
    hits = [p for p in people.glob(f"{pid}-*.md") if re.match(rf"{re.escape(pid)}-[a-z]", p.name)]
    if not hits:
        sys.exit(f"dossier {pid} neexistuje")
    return hits[0]


def main(tree_dir: str, pids: list[str]) -> int:
    tree = Path(tree_dir)
    people = tree / "research" / "people"
    ids = json.loads((people / "ids.json").read_text(encoding="utf-8"))
    by_id = {v: x for x, v in ids.items()}
    mpath = people / "manual.json"
    manual = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    ged = parse(sorted((tree / "data" / "exports" / "myheritage").glob("*.ged"))[-1])
    gw = GrampsWeb()
    for pid in pids:
        path = dossier_for(people, pid)
        text = path.read_text(encoding="utf-8")
        m = TITLE_RE.search(text)
        full = m[1].strip() if m else pid
        given, _, surname = full.rpartition(" ") if " " in full else ("", "", full)
        indi = ged.get(by_id.get(pid, ""))
        sex = indi.val("SEX") if indi else manual.get(pid, {}).get("sex", "")
        uid = indi.val("_UID") if indi else ""
        existing = gw.person_by_gramps_id(pid)
        if existing:
            print(f"= {pid} {full} — už existuje")
            continue
        attrs = [{"_class": "Attribute", "type": "workbench ID",
                  "value": pid}]
        if uid:
            attrs.append({"_class": "Attribute", "type": "MyHeritage _UID",
                          "value": uid})
        gw.post("/people/", {
            "_class": "Person",
            "gramps_id": pid,
            "gender": GENDER.get(sex, 2),
            "primary_name": {"_class": "Name", "first_name": given,
                             "surname_list": [{"_class": "Surname", "surname": surname, "primary": True}]},
            "attribute_list": attrs,
        })
        text = re.sub(r"^gramps_id:.*$", f"gramps_id: {pid}", text, count=1, flags=re.M)
        path.write_text(text, encoding="utf-8")
        print(f"+ {pid} {given} / {surname} ({sex or '?'})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
