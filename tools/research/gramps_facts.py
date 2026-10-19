"""Údaje osob z Gramps pro checklist: roky, pohlaví, rodiče a události s citací (→ automatické `[x]`).

Jen čtení přes Gramps Web API (`tools/gramps/gw.py`). Gramps ID osoby = ID ve workbenchi.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklist import CENSUS_YEARS, Facts  # noqa: E402

KEY_OF_TYPE = {"Birth": "n", "Baptism": "n", "Christening": "n", "Death": "z", "Burial": "z", "Marriage": "o"}


def _exact(ev: dict) -> bool:
    """Přesné datum (ne „asi“, „před“, „mezi“, odhad) — jen takové dokládá, že zápis byl nalezen."""
    d = ev.get("date") or {}
    return bool(d.get("year")) and not d.get("modifier") and not d.get("quality")


def _year(ev: dict) -> int | None:
    y = ((ev.get("date") or {}).get("year")) or 0
    return y or None


def _md(ev: dict, late: bool = False) -> tuple[int, int] | None:
    """(měsíc, den) data události; u rozmezí s `late` konec rozmezí. Bez měsíce → None."""
    dv = (ev.get("date") or {}).get("dateval") or []
    if late and len(dv) >= 7 and dv[6]:
        dv = dv[4:]
    return (dv[1], dv[0] or 1) if len(dv) >= 3 and dv[1] else None


def _late_year(ev: dict) -> int | None:
    """Nejpozdější rok data (u rozmezí konec) — pro úmrtí; „po“ (AFT, FROM) nedává horní mez → None."""
    d = ev.get("date") or {}
    if d.get("modifier") in (2, 7):                # AFT, FROM
        return None
    dv = d.get("dateval") or []
    return (dv[6] if d.get("modifier") in (4, 5) and len(dv) >= 7 and dv[6] else None) or _year(ev)


def load(g=None) -> dict[str, Facts]:
    """→ {Gramps ID: Facts} (bez odhadů — ty doplní `checklist.finish`)."""
    if g is None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gramps"))
        from gw import GrampsWeb  # noqa: E402
        g = GrampsWeb()
    people = g.get("/people/?keys=handle,gramps_id,gender,event_ref_list,family_list,parent_family_list&pagesize=100000")
    families = g.get("/families/?keys=handle,father_handle,mother_handle,event_ref_list,child_ref_list&pagesize=100000")
    events = {e["handle"]: e for e in g.get("/events/?keys=handle,gramps_id,type,date,citation_list&pagesize=100000")}
    fams = {f["handle"]: f for f in families}

    def cited(ref: dict) -> dict | None:
        ev = events.get(ref.get("ref"))
        if ev and (ev.get("citation_list") or ref.get("citation_list")):
            return ev
        return None

    born: dict[str, int] = {}
    for p in people:
        for ref in p.get("event_ref_list") or []:
            ev = events.get(ref.get("ref"))
            if ev and ev.get("type") in ("Birth", "Baptism", "Christening") and _year(ev):
                born[p["handle"]] = min(born.get(p["handle"], 9999), _year(ev))

    out: dict[str, Facts] = {}
    for p in people:
        f = Facts(male={1: True, 0: False}.get(p.get("gender")))
        evs = [(ref, events.get(ref.get("ref"))) for ref in p.get("event_ref_list") or []]
        for ref, ev in evs:
            if not ev or ref.get("role", "Primary") != "Primary":
                continue
            t, y = ev.get("type"), _year(ev)
            if t in ("Birth", "Baptism", "Christening") and y and (f.birth is None or t == "Birth"):
                f.birth, f.birth_md = y, _md(ev)
            if t in ("Death", "Burial") and _late_year(ev) and (f.death is None or t == "Death"):
                f.death, f.death_md = _late_year(ev), _md(ev, late=True)
            if t in ("Death", "Burial"):
                f.dead = True
            if not cited(ref) or not _exact(ev):
                continue
            key = KEY_OF_TYPE.get(t)
            if t == "Census" and y in CENSUS_YEARS:
                key = f"scitani{y}"
            if key and key not in f.found:
                f.found[key] = f"{ev.get('gramps_id')} ({t}{' ' + str(y) if y else ''})"
        for fh in p.get("family_list") or []:
            fam = fams.get(fh)
            if not fam:
                continue
            f.married = True
            kids = [born[c["ref"]] for c in fam.get("child_ref_list") or [] if c.get("ref") in born]
            if kids:
                f.child_birth = min([f.child_birth or 9999] + kids)
            for ref in fam.get("event_ref_list") or []:
                ev = events.get(ref.get("ref"))
                if ev and ev.get("type") == "Marriage":
                    f.marriage = f.marriage or _year(ev)
                    if cited(ref) and _exact(ev) and "o" not in f.found:
                        f.found["o"] = f"{ev.get('gramps_id')} (Marriage{' ' + str(_year(ev)) if _year(ev) else ''})"
        for fh in p.get("parent_family_list") or []:
            fam = fams.get(fh)
            if fam:
                f.parents = (f.parents[0] or bool(fam.get("father_handle")), f.parents[1] or bool(fam.get("mother_handle")))
        out[p["gramps_id"]] = f
    return out
