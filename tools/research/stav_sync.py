#!/usr/bin/env python3
"""Srovná stav dossierů s patchi: `dokončeno` + všechny patche osoby `aplikováno` → `zapsáno`.

Applier nastavuje `zapsáno` jen tehdy, když byl dossier `dokončeno` už v okamžiku aplikace; session ale často
přepne na `dokončeno` až po odeslání posledního patche → dossier zůstane „dokončeno“ (v dashboardu ne zeleně).
Použití: stav_sync.py [strom-dir]   (opakovatelné)
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wbconfig  # noqa: E402


def main(tree: Path) -> int:
    people, patches = tree / "research/people", tree / "patches"
    changed = []
    for f in sorted(people.glob("*.md")):
        m = re.match(r"(K\d{4}(?:-[SCP]\d+)*)-[a-z]", f.name)
        if not m:
            continue
        pid, t = m.group(1), f.read_text(encoding="utf-8")
        if not re.search(r"^stav:\s*dokončeno", t, re.M):
            continue
        ps = list(patches.glob(f"P-{pid}-[0-9]*.yml"))
        if not ps:
            continue
        if all(re.search(r"^status:\s*aplikováno", p.read_text(encoding="utf-8"), re.M) for p in ps):
            f.write_text(re.sub(r"^stav:\s*dokončeno\s*", "stav: zapsáno          ", t, count=1, flags=re.M), encoding="utf-8")
            changed.append(pid)
    print(f"dokončeno → zapsáno: {len(changed)}" + (": " + ", ".join(changed) if changed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else wbconfig.tree_dir()))
