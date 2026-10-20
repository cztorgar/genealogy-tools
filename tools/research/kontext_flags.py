#!/usr/bin/env python3
"""Označí ve front-matter dossierů `kontext: chybí`, když zkoumané osobě (stav ≠ zmínka/převzato) chybí sekce
`## Kontext` nebo příběh `research/pribehy/<ID>.md` (docs/metodika/pribehy.md); u doplněných příznak odstraní.

Použití: kontext_flags.py <strom-dir>     (opakovatelné)
"""
import os
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wbconfig  # noqa: E402


def main(tree: str) -> int:
    people = Path(tree) / "research" / "people"
    stories = Path(tree) / "research" / "pribehy"
    marked, ok = [], 0
    for f in sorted(people.glob("*.md")):
        m = re.match(r"(K\d{4}(?:-[SCP]\d+)*)-[a-z]", f.name)
        if not m:
            continue
        pid, t = m.group(1), f.read_text(encoding="utf-8")
        st = re.search(r"^stav:\s*(\S+)", t, re.M)
        if not st or st.group(1) in ("zmínka", "převzato"):
            continue
        has_k = re.search(r"^## Kontext\s*\n(?:\s*\n)*[-*\w]", t, re.M) is not None
        has_p = (stories / f"{pid}.md").exists()
        if has_k and has_p:
            t2 = re.sub(r"^kontext:.*\n", "", t, flags=re.M)
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
            ok += 1
            continue
        miss = [x for x, h in (("Kontext", has_k), ("příběh", has_p)) if not h]
        line = f"kontext: chybí          # chybí: {', '.join(miss)} — doplnit (docs/metodika/pribehy.md)\n"
        if re.search(r"^kontext:", t, re.M):
            t = re.sub(r"^kontext:.*\n", line, t, count=1, flags=re.M)
        else:
            t = re.sub(r"^(stav:.*\n)", r"\1" + line, t, count=1, flags=re.M)
        f.write_text(t, encoding="utf-8")
        marked.append(f"{pid} [{st.group(1)}] chybí {', '.join(miss)}")
    print(f"kompletní: {ok}, označeno `kontext: chybí`: {len(marked)}")
    print("\n".join("  " + x for x in marked))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(wbconfig.tree_dir())))
