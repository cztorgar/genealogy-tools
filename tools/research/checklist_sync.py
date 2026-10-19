#!/usr/bin/env python3
"""Přepíše sekci `## Checklist` dossierů podle aktuální šablony (`checklist.py`) a údajů z Gramps.

Ruční stavy (`[x]`, `[-]` a text za pomlčkou) zůstanou, nové položky přibudou jako `[ ]`, `[x]` z Gramps
se doplní jako `auto:`. Starý formát (bez klíčů, `[~]`, `[n]`) se převede. Nic jiného v dossieru nemění.

Použití: checklist_sync.py <strom-dir> [ID …] [--dry-run] [--offline]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checklist as cl  # noqa: E402

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def dossier_facts(text: str) -> tuple[int | None, int | None]:
    """Rok narození / úmrtí z nápověd dossieru (MyHeritage, ústně) — když osoba v Gramps data nemá."""
    birth = death = None
    for m in re.finditer(r"\*\*narození:\*\*([^\n]*)", text):
        y = re.search(r"\b(1[0-9]{3}|20[0-2][0-9])\b", m.group(1))
        birth = birth or (int(y.group(1)) if y else None)
    for m in re.finditer(r"\*\*úmrtí:\*\*([^\n]*)", text):
        y = re.search(r"\b(1[0-9]{3}|20[0-2][0-9])\b", m.group(1))
        death = death or (int(y.group(1)) if y else None)
    return birth, death


def section_span(text: str, title: str) -> tuple[int, int] | None:
    m = re.search(rf"^## {re.escape(title)}[^\n]*\n", text, re.M)
    if not m:
        return None
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return m.start(), m.end() + (nxt.start() if nxt else len(text) - m.end())


def has_zavora(text: str) -> bool:
    sp = section_span(text, "Závora")
    return bool(sp) and cl.zavora_valid(text[sp[0]:sp[1]].split("\n", 1)[1])


def person_facts(pid: str, text: str, gf: dict, manual: dict, root_birth: int | None) -> cl.Facts:
    f = gf.get(pid) or cl.Facts()
    f = cl.Facts(**{k: getattr(f, k) for k in f.__dataclass_fields__})        # kopie
    b, d = dossier_facts(text)
    f.birth = f.birth or b or (manual.get(pid) or {}).get("birth")
    f.death = f.death or d
    if f.male is None and (manual.get(pid) or {}).get("sex") in ("M", "F"):
        f.male = manual[pid]["sex"] == "M"
    return cl.finish(f, pid, root_birth)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--offline", action="store_true", help="bez Gramps (jen dossier + odhad)")
    a = ap.parse_args()
    root = Path(a.tree)
    people = root / "research/people"
    mpath = people / "manual.json"
    manual = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    if a.offline:
        gf = {}
    else:
        import gramps_facts
        gf = gramps_facts.load()
    root_birth = (gf.get("K0001") or cl.Facts()).birth or 1985

    changed, done, total = [], [], 0
    for p in sorted(people.glob("K*.md")):
        text = p.read_text(encoding="utf-8")
        fm = FM_RE.match(text)
        m = re.search(r"^id:\s*(\S+)", fm.group(1), re.M) if fm else None
        pid = m.group(1) if m else p.stem.split("-")[0]
        if a.ids and pid not in a.ids:
            continue
        total += 1
        facts = person_facts(pid, text, gf, manual, root_birth)
        sp = section_span(text, "Checklist")
        marks = cl.parse_marks(text[sp[0]:sp[1]]) if sp else {}
        entries = cl.evaluate(facts, marks)
        if cl.phase1_done(entries, has_zavora(text)):
            done.append(pid)
        new_sec = "## Checklist\n\n" + cl.render(entries, facts, marks.get(cl.OTHER, [])) + "\n"
        if sp:
            new = text[:sp[0]] + new_sec + text[sp[1]:]
        else:                                # dossier bez checklistu → před log / výzkum / konec
            ins = section_span(text, "Log hledání") or section_span(text, "Výzkum")
            at = ins[0] if ins else len(text)
            new = text[:at] + ("" if text[:at].endswith("\n\n") else "\n") + new_sec + text[at:]
        if new != text:
            changed.append(pid)
            if not a.dry_run:
                p.write_text(new, encoding="utf-8")
    print(f"checklist: {len(changed)}/{total} dossierů {'by se změnilo' if a.dry_run else 'upraveno'}; "
          f"fáze I uzavřena: {len(done)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
