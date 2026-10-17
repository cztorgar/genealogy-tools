"""Doložení údajů: u každé události osoby počet nezávislých pramenů a nejvyšší jistota.

Pravidla `docs/metodika/autonomie.md`, kap. 3 (D2): počet nezávislých pramenů = počet různých
**zápisů** v citacích události. Jeden zápis = jeden sidecar; sidecar s `pair` (dvě fotky téhož zápisu)
a jeho dvojče jsou jeden zápis. Rejstřík se nepočítá (je podpůrný, ne nezávislý).

Události se berou z **aplikovaných** patchů:
- `add_event` — handle události z `applied.items` (páruje se podle pořadí op + typ),
- `add_citation` / `update_event` s `citation` — další citace k události (i z patche jiné osoby),
- `update_event` s `type` — změna typu.
Citace odkazem na Gramps (`C0013`, handle) bez sidecaru se počítá jako jeden zápis „citace v Gramps“.
"""
from __future__ import annotations

import re
from pathlib import Path

PATCH_RE = re.compile(r"^P-(K\d+(?:-[SCP]\d+)*)-(\d+)\.ya?ml$")
INDEX_RE = re.compile(r"rejst|index", re.I)


def _cit_keys(ch: dict) -> list[str]:
    keys = ch.get("citations") if ch.get("citations") is not None else ch.get("citation")
    if keys is None:
        return []
    return [str(k) for k in (keys if isinstance(keys, list) else [keys])]


def _match_applied(changes: list, applied: list) -> list:
    """K changes[i] najde odpovídající applied item (stejná op, u add_event i typ), postupně."""
    out, j = [], 0
    for ch in changes:
        hit = None
        if isinstance(ch, dict):
            for k in range(j, len(applied)):
                a = applied[k]
                if isinstance(a, dict) and a.get("op") == ch.get("op") and (
                        ch.get("op") != "add_event" or a.get("type") == ch.get("type")):
                    hit, j = a, k + 1
                    break
        out.append(hit)
    return out


def events(patch_files: list[Path], cache, load_yaml, root: Path, norm_any) -> dict[str, list[dict]]:
    """→ {ID osoby: [události s prameny]}."""
    evs: dict[str, dict] = {}            # handle → událost
    order: list[str] = []
    pending: list[tuple[str, dict, str]] = []   # (handle, citace, patch) pro události z jiných patchů

    def sidecar(rel: str):
        p = (root / rel)
        data = cache.get(p, "yaml", load_yaml) if p.exists() else None
        return data if isinstance(data, dict) else None

    def resolve(cit, patch: str) -> dict:
        if not isinstance(cit, dict):        # odkaz na citaci v Gramps
            return {"key": f"gramps:{cit}", "label": f"citace v Gramps {cit}", "confidence": None,
                    "patch": patch, "index": False}
        sc_rel = str(cit.get("source_sidecar") or "")
        sc = sidecar(sc_rel) if sc_rel else None
        key = sc_rel or f"{patch}:{cit.get('page')}"
        label = cit.get("page") or sc_rel
        index = False
        if sc:
            d = str(Path(sc_rel).parent)
            if sc.get("pair") and sc.get("file"):
                key = f"{d}/" + min(str(sc["file"]), str(sc["pair"]))
            label = sc.get("entry") or sc.get("document") or label
            index = bool(INDEX_RE.search(str(sc.get("type") or "")) or INDEX_RE.search(str(sc.get("form") or "")[:40]))
        conf = cit.get("confidence")
        return {"key": key, "label": str(label), "confidence": conf if isinstance(conf, int) else None,
                "sidecar": sc_rel or None, "url": (sc or {}).get("url"), "patch": patch, "index": index}

    for p in patch_files:
        m = PATCH_RE.match(p.name)
        data = cache.get(p, "yaml", load_yaml)
        if not m or not isinstance(data, dict) or not str(data.get("status") or "").startswith("aplikov"):
            continue
        pid = m.group(1)
        changes = data.get("changes") or []
        applied = ((data.get("applied") or {}).get("items")) or []
        cits = data.get("citations") or {}
        for ch, ap in zip(changes, _match_applied(changes, applied)):
            if not isinstance(ch, dict):
                continue
            op = ch.get("op")
            handle = (ap or {}).get("event") or ch.get("event")
            refs = [resolve(cits.get(k, k), p.name) for k in _cit_keys(ch)]
            if op == "add_event":
                handle = handle or f"{p.name}#{len(order)}"
                fam = ch.get("family")
                persons = [pid]
                if isinstance(fam, list):
                    persons = [x for x in (norm_any(f) for f in fam) if x] or [pid]
                if handle not in evs:
                    order.append(handle)
                evs[handle] = {"handle": handle, "type": ch.get("type"), "date": str(ch.get("date") or ""),
                               "place": str(ch.get("place") or ""), "description": str(ch.get("description") or ""),
                               "persons": persons, "family": bool(fam), "patch": p.name, "refs": refs}
            elif op in ("add_citation", "update_event") and handle:
                for r in refs:
                    pending.append((handle, r, p.name))
                if op == "update_event" and ch.get("type"):
                    pending.append((handle, {"type": ch["type"]}, p.name))

    for handle, r, patch in pending:
        ev = evs.get(handle)
        if ev is None:                       # událost vznikla mimo patche (import) — znám jen handle
            m = PATCH_RE.match(patch)
            ev = evs[handle] = {"handle": handle, "type": None, "date": "", "place": "", "description": "",
                                "persons": [m.group(1)] if m else [], "family": False, "patch": None, "refs": []}
            order.append(handle)
        if "type" in r and "key" not in r:
            ev["type"] = r["type"]
        else:
            ev["refs"].append(r)

    out: dict[str, list[dict]] = {}
    for handle in order:
        ev = evs[handle]
        records: dict[str, dict] = {}
        support = 0
        for r in ev["refs"]:
            if r["index"]:
                support += 1
                continue
            rec = records.setdefault(r["key"], dict(r))
            if (r["confidence"] or -1) > (rec["confidence"] or -1):
                rec["confidence"] = r["confidence"]
        confs = [r["confidence"] for r in records.values() if r["confidence"] is not None]
        ev = dict(ev, sources=len(records), confidence=max(confs) if confs else None,
                  records=list(records.values()), support=support)
        del ev["refs"]
        for pid in ev["persons"]:
            out.setdefault(pid, []).append(ev)
    return out
