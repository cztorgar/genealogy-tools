#!/usr/bin/env python3
"""Založí / doplní rodinu v Gramps (strom berescak): rodiče + děti, s citací ústního sdělení uživatele.

Vazby, které uživatel zná, jsou vždy správně (docs/metodika/gramps-vs-workbench.md) → zakládají se hned,
s citací „Ústní sdělení — Vojtěch Bereščák“ (jistota 3). Gramps ID rodiny = F-<otec>-<matka>.
Osoby musí v Gramps existovat (ensure_persons.py). Opakované spuštění jen doplní chybějící děti.

Použití: ensure_family.py --father K0002 --mother K0003 [--children K0001,K0002-C1] [--married]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gw import GrampsWeb  # noqa: E402

ORAL_SOURCE_ID = "S-USTNE-K0001"
ORAL_TITLE = "Ústní sdělení — Vojtěch Bereščák"


def by_gid(gw: GrampsWeb, kind: str, gid: str) -> dict | None:
    try:
        res = gw.get(f"/{kind}/?gramps_id={gid}")
    except RuntimeError as e:
        if "HTTP 404" in str(e):
            return None
        raise
    return res[0] if res else None


def oral_citation(gw: GrampsWeb, page: str) -> str:
    """Vrátí handle nové citace ústního sdělení (zdroj se založí jednou)."""
    src = by_gid(gw, "sources", ORAL_SOURCE_ID)
    if not src:
        gw.post("/sources/", {"_class": "Source", "gramps_id": ORAL_SOURCE_ID, "title": ORAL_TITLE,
                              "author": "Vojtěch Bereščák"})
        src = by_gid(gw, "sources", ORAL_SOURCE_ID)
    res = gw.post("/citations/", {"_class": "Citation", "source_handle": src["handle"], "page": page,
                                  "confidence": 3})
    return next(o["handle"] for o in res if o["_class"] == "Citation")


def person(gw: GrampsWeb, gid: str) -> dict:
    p = gw.person_by_gramps_id(gid)
    if not p:
        sys.exit(f"osoba {gid} v Gramps není — nejdřív ensure_persons.py")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--father")
    ap.add_argument("--mother")
    ap.add_argument("--children", default="")
    ap.add_argument("--married", action="store_true", help="typ rodiny Married (jinak Unknown)")
    a = ap.parse_args()
    gw = GrampsWeb()
    father = person(gw, a.father) if a.father else None
    mother = person(gw, a.mother) if a.mother else None
    kids = [person(gw, c) for c in a.children.split(",") if c]
    fid = f"F-{a.father or 'X'}-{a.mother or 'X'}"
    today = date.today().isoformat()

    fam = by_gid(gw, "families", fid)
    if not fam:
        cit = oral_citation(gw, f"rodinné vazby {fid}, sděleno {today}")
        gw.post("/families/", {
            "_class": "Family", "gramps_id": fid,
            "father_handle": father["handle"] if father else None,
            "mother_handle": mother["handle"] if mother else None,
            "type": "Married" if a.married else "Unknown",
            "citation_list": [cit],
            "child_ref_list": [],
        })
        fam = by_gid(gw, "families", fid)
        print(f"+ rodina {fid}")
    have = {c["ref"] for c in fam["child_ref_list"]}
    added = [k for k in kids if k["handle"] not in have]
    if added:
        fam["child_ref_list"] += [{"_class": "ChildRef", "ref": k["handle"], "frel": "Birth", "mrel": "Birth"}
                                  for k in added]
        gw.put(f"/families/{fam['handle']}", fam)
    # Gramps drží vazbu i na straně osob — doplnit, pokud ji API nedoplnilo samo
    for p, field in [(father, "family_list"), (mother, "family_list")] + [(k, "parent_family_list") for k in kids]:
        if not p:
            continue
        fresh = gw.get(f"/people/{p['handle']}")
        if fam["handle"] not in fresh[field]:
            fresh[field].append(fam["handle"])
            gw.put(f"/people/{p['handle']}", fresh)
    print(f"  {fid}: děti +{len(added)} ({', '.join(k['gramps_id'] for k in added) or '—'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
