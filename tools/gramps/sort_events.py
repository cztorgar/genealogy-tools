#!/usr/bin/env python3
"""Seřadí události osob a rodin v Gramps (strom berescak) chronologicky.

Gramps zobrazuje události v pořadí `event_ref_list`, ne podle data — patche je přidávají na konec.
Řazení: podle data (sortval); stejné datum → pořadí podle typu (narození, křest, … úmrtí, pohřeb);
události bez data na konec v původním pořadí. `birth_ref_index` / `death_ref_index` se přepočítají.

Použití: sort_events.py [--all | K0042 …]   (bez argumentu = --all; jen změněné se zapíšou)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gw import GrampsWeb  # noqa: E402

TYPE_ORDER = {"Birth": 0, "Christening": 1, "Baptism": 1, "Religion": 2, "Death": 90, "Burial": 91,
              "Cremation": 91, "Probate": 92}


def sorted_refs(gw: GrampsWeb, refs: list[dict], cache: dict | None = None) -> list[dict]:
    cache = {} if cache is None else cache

    def key(item):
        i, r = item
        ev = cache.get(r["ref"]) or cache.setdefault(r["ref"], gw.get(f"/events/{r['ref']}"))
        sv = (ev.get("date") or {}).get("sortval") or 0
        return (sv == 0, sv, TYPE_ORDER.get(ev.get("type"), 50), i)

    return [r for _, r in sorted(enumerate(refs), key=key)]


def sort_object(gw: GrampsWeb, kind: str, obj: dict, cache: dict | None = None) -> bool:
    """Seřadí `event_ref_list` objektu (people | families) na místě; vrátí True, když se pořadí změnilo."""
    refs = obj.get("event_ref_list") or []
    new = sorted_refs(gw, refs, cache)
    if [r["ref"] for r in new] == [r["ref"] for r in refs]:
        return False
    if kind == "people":
        for idx_key in ("birth_ref_index", "death_ref_index"):
            old = obj.get(idx_key, -1)
            if old is not None and 0 <= old < len(refs):
                obj[idx_key] = next(j for j, r in enumerate(new) if r["ref"] == refs[old]["ref"])
    obj["event_ref_list"] = new
    return True


def main(args: list[str]) -> int:
    gw = GrampsWeb()
    cache: dict = {}
    targets: list[tuple[str, dict]] = []
    if not args or args == ["--all"]:
        targets += [("people", p) for p in gw.get("/people/?pagesize=10000")]
        targets += [("families", f) for f in gw.get("/families/?pagesize=10000")]
    else:
        for gid in args:
            kind = "families" if gid.startswith("F-") else "people"
            res = gw.get(f"/{kind}/?gramps_id={gid}")
            targets += [(kind, o) for o in res]
    changed = 0
    for kind, obj in targets:
        if sort_object(gw, kind, obj, cache):
            gw.put(f"/{kind}/{obj['handle']}", obj)
            changed += 1
            print(f"↕ {obj['gramps_id']}")
    print(f"seřazeno: {changed} z {len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
