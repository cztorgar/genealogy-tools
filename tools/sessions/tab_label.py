#!/usr/bin/env python3
"""Název tabu osobní session: „K0056 František Vrbický *1848“.

Rok narození: doložený z Gramps (strom berescak, událost Birth, jinak Christening), jinak nápověda
z dossieru / manual.json s otazníkem („*1848?“). Bez roku jen ID a jméno.

Použití: tab_label.py <strom-dir> <ID>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gramps"))


def main(tree: str, pid: str) -> int:
    people = Path(tree) / "research" / "people"
    hits = [p for p in people.glob(f"{pid}-*.md") if re.match(rf"{re.escape(pid)}-[a-z]", p.name)]
    text = hits[0].read_text(encoding="utf-8") if hits else ""
    m = re.search(r"^# (.+?)\s*\([^)]*\)\s*$", text, re.M)
    name = m[1].strip() if m else pid
    year = None
    try:
        from gw import GrampsWeb
        gw = GrampsWeb()
        p = gw.person_by_gramps_id(pid)
        if p:
            for want in ("Birth", "Christening"):
                for r in p["event_ref_list"]:
                    e = gw.get(f"/events/{r['ref']}")
                    y = (e.get("date") or {}).get("dateval", [0, 0, 0])[2]
                    if e["type"] == want and y:
                        year = str(y)
                        break
                if year:
                    break
    except Exception:  # noqa: BLE001 — Gramps neběží: jen nápověda
        pass
    if not year:
        h = re.search(r"\*\*(narození|křest):\*\*[^\n]*?(\d{4})", text)
        manual = people / "manual.json"
        mb = json.loads(manual.read_text(encoding="utf-8")).get(pid, {}).get("birth") if manual.exists() else None
        year = f"{h[2]}?" if h else (f"{mb}?" if mb else None)
    print(f"{pid} {name}" + (f" *{year}" if year else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
