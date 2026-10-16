#!/usr/bin/env python3
"""Založí osobu, která není v exportu MyHeritage (nalezena v pramenu nebo ústně): dossier + záznam
v `research/people/manual.json` + osoba v Gramps (jen jméno a pohlaví, ensure_persons.py).

ID podle schématu kotvy: `<kotva>-S<n>` manžel/ka, `<kotva>-C<n>` dítě, `<kotva>-P1/P2` rodič.

Použití: add_person.py <strom-dir> <ID> --name "Marie Pospíšilová" --sex F --puvod pramen \\
           --rel "2. manželka — Josef Vrbický (K0028)" [--birth 1888] [--hint "…"]
"""
import argparse
import json
import subprocess
import sys
import unicodedata
import re
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_queue import DEFERRED_HEADING, DEFERRED_HINT, DOCS_HEADING, DOCS_HINT, STATES_HINT  # noqa: E402
from checklist import applicable  # noqa: E402


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree"); ap.add_argument("pid")
    ap.add_argument("--name", required=True); ap.add_argument("--sex", choices=["M", "F"], required=True)
    ap.add_argument("--puvod", choices=["pramen", "ústně", "myheritage"], default="pramen")
    ap.add_argument("--rel", required=True); ap.add_argument("--birth", type=int)
    ap.add_argument("--hint", default="")
    a = ap.parse_args()
    people = Path(a.tree) / "research" / "people"
    mpath = people / "manual.json"
    manual = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    if a.pid in manual or list(people.glob(f"{a.pid}-[a-z]*.md")):
        sys.exit(f"{a.pid} už existuje")
    items = applicable(a.birth, None, male=a.sex == "M", married="manžel" in a.rel, dead=bool(a.birth and a.birth < 1930))
    lines = ["---", f"id: {a.pid}", f"původ: {a.puvod}       # myheritage | pramen | ústně", "myheritage: null",
             "gramps_id: null", f"stav: zmínka          # {STATES_HINT}", "---", "",
             f"# {a.name} ({a.pid})", "", f"*{a.rel}*", "",
             f"## Nápovědy ({a.puvod}, {date.today().isoformat()})", "", f"- {a.hint}" if a.hint else "- —", "",
             "## Checklist", "",
             "`[x]` doloženo · `[~]` slabý pramen · `[-]` hledáno, nenalezeno · `[n]` neexistuje · `[ ]` nehledáno", ""]
    lines += [f"- [ ] {it.label}{' — ' + note if note else ''}" for it, note in items]
    lines += ["", DOCS_HEADING, "", DOCS_HINT, "", DEFERRED_HEADING, "", DEFERRED_HINT, "",
              "## Log hledání", "", "*Formát: `- YYYY-MM-DD | pramen | výsledek | odkaz`. Zapisovat i „nenalezeno“.*", "",
              "## Výzkum", "", ""]
    path = people / f"{a.pid}-{slug(a.name)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    manual[a.pid] = {"name": a.name, "sex": a.sex, "původ": a.puvod, "rel": a.rel, "birth": a.birth,
                     "created": date.today().isoformat()}
    mpath.write_text(json.dumps(manual, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"+ dossier {path.name}")
    wb = Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, str(wb / "tools/gramps/ensure_persons.py"), a.tree, a.pid], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
