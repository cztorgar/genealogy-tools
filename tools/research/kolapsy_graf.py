#!/usr/bin/env python3
"""Graphviz schémata zhroucení předků / propojení větví → `research/grafy/<název>.{dot,png}` ve stromu.

Data (jméno, roky, adresy = obec + č. p. z událostí) bere živě z Gramps Web (jen čtení). Definice schémat
(kdo je v řetězcích) je v `research/grafy/kolapsy.yml` stromu:

    kolapsy:
      - nazev: hulovi
        titulek: "Hulovi — společní předci Vojty a Terezy"
        spolecni: [K0106, K0107]              # společný pár (nahoře)
        vetve:                                 # každá větev = řetězec potomků (dítě, jeho manžel/ka) až dolů
          - [[K0053, K0052], [K0026, K0027], …, [K0001]]
          - [[K0001-S2-…, …], …]
        svatba: [K0001, K0001-S2]             # volitelně: kde se větve potkají sňatkem (dvojice osob)

Použití: kolapsy_graf.py [strom-dir]
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gramps"))
from gw import GrampsWeb  # noqa: E402

CP = re.compile(r"(?:č\.\s*p\.|čp\.|č\.)\s*(\d+(?:/[IVX]+)?)")


class Data:
    def __init__(self):
        self.g = GrampsWeb()
        self.places, self.cache = {}, {}

    def place(self, h):
        if h and h not in self.places:
            self.places[h] = self.g.get(f"/places/{h}")["name"]["value"]
        return self.places.get(h, "")

    def person(self, pid):
        if pid in self.cache:
            return self.cache[pid]
        try:
            p = self.g.get(f"/people/?gramps_id={pid}")[0]
        except Exception:
            self.cache[pid] = None
            return None
        n = p["primary_name"]
        name = f"{n['first_name']} {n['surname_list'][0]['surname'] if n['surname_list'] else ''}".strip()
        born = died = None
        addrs = []
        for r in p["event_ref_list"]:
            e = self.g.get(f"/events/{r['ref']}")
            y = (e.get("date") or {}).get("dateval") or []
            year = y[2] if len(y) > 2 and y[2] else None
            if e["type"] in ("Birth", "Christening") and year and not born:
                born = year
            if e["type"] in ("Death", "Burial") and year and not died:
                died = year
            pl = self.place(e.get("place"))
            cp = CP.search(e.get("description") or "")
            if pl and e["type"] in ("Birth", "Residence", "Death", "Census", "Occupation"):
                a = f"{pl} č. {cp.group(1)}" if cp else pl
                if a not in [x[0] for x in addrs]:
                    addrs.append((a, year))
        life = f"{born or '?'}–{died or ''}" if (born or died) else ""
        self.cache[pid] = {"name": name, "life": life, "addrs": addrs[:3]}
        return self.cache[pid]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def label(d, pid, focus):
    if not d:
        return f"<<b>{pid}</b>>"
    adr = "<br/>".join(f'<font point-size="9">{esc(a)}{f" ({y})" if y else ""}</font>' for a, y in d["addrs"])
    who = f'<b>{esc(d["name"])}</b>' if focus else esc(d["name"])
    life = f'<br/><font point-size="10">{esc(d["life"])}</font>' if d["life"] else ""
    return f'<{who}{life}{"<br/>" + adr if adr else ""}>'


def build(k, data):
    L = ["digraph G {", 'graph [rankdir=TB, nodesep=0.35, ranksep=0.45, fontname="DejaVu Sans", labelloc=t, fontsize=16,'
         f' label="{k["titulek"]}"];',
         'node [shape=box, style="rounded,filled", fillcolor="#ffffff", fontname="DejaVu Sans", fontsize=11];',
         'edge [color="#555555", arrowsize=0.6];']
    a, b = k["spolecni"]
    for pid in (a, b):
        L.append(f'"{pid}" [label={label(data.person(pid), pid, True)}, fillcolor="#fde2b3", color="#c77700", penwidth=2];')
    L.append(f'"F0" [shape=point, width=0.08]; "{a}" -> "F0" [arrowhead=none]; "{b}" -> "F0" [arrowhead=none];'
             f' {{rank=same; "{a}"; "{b}";}}')
    colors = ["#2b6cb0", "#b83280", "#2f855a"]
    for vi, chain in enumerate(k["vetve"]):
        prev = "F0"
        for gi, gen in enumerate(chain):
            child, *spouse = gen
            fill = "#e8f1fb" if vi == 0 else "#fbe8f3"
            L.append(f'"{child}" [label={label(data.person(child), child, True)}, fillcolor="{fill}", color="{colors[vi % 3]}"];')
            L.append(f'"{prev}" -> "{child}" [color="{colors[vi % 3]}", penwidth=1.6];')
            if spouse:
                s = spouse[0]
                L.append(f'"{s}" [label={label(data.person(s), s, False)}, fillcolor="#f7f7f7", color="#aaaaaa"];')
                fam = f"F{vi}_{gi}"
                L.append(f'"{fam}" [shape=point, width=0.06]; "{child}" -> "{fam}" [arrowhead=none];'
                         f' "{s}" -> "{fam}" [arrowhead=none, color="#aaaaaa"]; {{rank=same; "{child}"; "{s}";}}')
                prev = fam
            else:
                prev = child
    if k.get("svatba"):
        x, y = k["svatba"]
        L.append(f'"{x}" -> "{y}" [dir=none, style=bold, color="#c53030", penwidth=2.5, label=" ⚭ ", fontcolor="#c53030",'
                 f' constraint=false];')
    if k.get("dite"):
        c = k["dite"]
        L.append(f'"{c}" [label={label(data.person(c), c, True)}, fillcolor="#fff5f5", color="#c53030", penwidth=2];')
        x, y = k["svatba"]
        L.append(f'"{x}" -> "{c}" [color="#c53030"]; "{y}" -> "{c}" [color="#c53030"];')
    L.append("}")
    return "\n".join(L)


def main(tree: Path) -> int:
    cfg = yaml.safe_load((tree / "research/grafy/kolapsy.yml").read_text(encoding="utf-8"))
    data = Data()
    for k in cfg["kolapsy"]:
        dot = tree / "research/grafy" / f"{k['nazev']}.dot"
        dot.write_text(build(k, data), encoding="utf-8")
        subprocess.run(["dot", "-Tpng", "-Gdpi=130", str(dot), "-o", str(dot.with_suffix(".png"))], check=True)
        print(dot.with_suffix(".png"))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "genealogy-trees/berescak")))
