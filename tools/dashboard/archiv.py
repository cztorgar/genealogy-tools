"""Listiny a domy pro dashboard — jen čtení, nic se negeneruje.

Listiny: každý sidecar `T/sources/**/*.yml` (matriky, sčítání, pozemkové knihy, smlouvy, artefakty…).
Osoby listiny = `persons` ze sidecaru + osoby patchů, které ho citují (`source_sidecar`).

Domy: dům = obec + číslo popisné. Skládá se ze dvou zdrojů:
- automaticky z událostí v patchích (`add_event` / `update_event` s č. p. v popisu): narození, úmrtí,
  bydliště, sčítání, povolání, držba — role „výminek“, když popis zmiňuje výminek / výměnek;
- ručně vedený soubor `T/research/domy/<obec>-<cp>.yml` (název, aliasy obce, držba a výminky
  od–do z pozemkové knihy, listiny, poznámky). Aliasy sjednotí různé tvary názvu obce (např. Lhota / Lhoty).
Listiny domu = ručně uvedené + sidecary, jejichž text zmiňuje obec a „č. <cp>“, nebo leží ve složce `…/cp<cp>/`.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

HOUSE_TYPES = {"Birth": "narození", "Death": "úmrtí", "Residence": "bydliště", "Census": "sčítání",
               "Occupation": "povolání", "Property": "držba"}
CP_RE = re.compile(r"(?:čp\.|č\.\s?p\.|č\.\s?d\.|č\.|No\.?|Nro)\s*(\d+)\b")
CP_SKIP_BEFORE = ("poř", "pluk", "zápis", "kniha", "matr", "list ", "ohled", "fasc", "č. j", "sn.", "kat.", "parc")
VYMINEK_RE = re.compile(r"výmin|výměn|vejmin|výminek|výměnek", re.I)
WORD_BEFORE_RE = re.compile(r"(?:\(([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\wáčďéěíňóřšťúůýž]+)\)|([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][\wáčďéěíňóřšťúůýž]+))\s*$")
ID_IN_PATCH = re.compile(r"^P-(K\d+(?:-[SCP]\d+)*)-(\d+)\.ya?ml$")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def years(value) -> tuple[int | None, int | None]:
    s = str(value or "").upper()
    ys = [int(y) for y in re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)]
    if not ys:
        return None, None
    if ("FROM" in s and "TO" in s) or ("BET" in s and "AND" in s):
        return ys[0], ys[-1]
    if s.startswith("TO"):
        return None, ys[0]
    return ys[0], None


# ------------------------------------------------------------------ listiny

def _rel(p: Path, root: Path) -> str:
    return str(p.relative_to(root))


def listiny(root: Path, patch_files: list[Path], cache, load_yaml) -> list[dict]:
    src = root / "sources"
    if not src.is_dir():
        return []
    cited: dict[str, set[str]] = {}
    for p in patch_files:
        m = ID_IN_PATCH.match(p.name)
        data = cache.get(p, "yaml", load_yaml)
        if not m or not isinstance(data, dict):
            continue
        for c in (data.get("citations") or {}).values():
            if isinstance(c, dict) and c.get("source_sidecar"):
                cited.setdefault(str(c["source_sidecar"]).lstrip("./"), set()).add(m.group(1))
    out = []
    for y in sorted(src.rglob("*.yml")):
        if "_metodika" in y.parts:
            continue
        meta = cache.get(y, "yaml", load_yaml)
        if not isinstance(meta, dict):
            continue
        rel = _rel(y, root)
        files = meta.get("files") or ([meta["file"]] if meta.get("file") else [])
        files = [_rel(y.parent / f, root) for f in files if (y.parent / str(f)).is_file()]
        if not files:
            files = [_rel(f, root) for f in sorted(y.parent.glob(y.stem + ".*")) if f.suffix.lower() != ".yml"]
        crops = []
        for c in meta.get("crops") or []:
            name = str(c).split(" — ")[0].strip()
            if (y.parent / name).is_file():
                crops.append(_rel(y.parent / name, root))
        persons = {str(x) for x in (meta.get("persons") or []) if x}
        persons |= cited.get(rel, set())
        title = meta.get("document") or ""
        if not title:
            bits = [meta.get("parish") or meta.get("obec") or "", meta.get("book") or "", meta.get("volume") or ""]
            title = " · ".join(str(b) for b in bits if b) or y.stem
        ystr = " ".join(str(meta.get(k) or "") for k in ("rok_scitani", "datace", "issued", "date", "entry", "text"))
        yrs = sorted({int(v) for v in re.findall(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", ystr)})
        out.append({
            "file": rel, "folder": _rel(y.parent, root), "type": str(meta.get("type") or "?"), "title": str(title),
            "archive": str(meta.get("archive") or ""), "entry": str(meta.get("entry") or meta.get("popis") or ""),
            "text": str(meta.get("text") or ""), "url": str(meta.get("url") or ""),
            "files": files, "crops": crops, "persons": sorted(persons),
            "year": yrs[0] if yrs else None, "years": yrs,
            "image": str(meta.get("image") or ""), "page": str(meta.get("page") or ""),
            "accessed": str(meta.get("accessed") or ""),
        })
    out.sort(key=lambda d: (d["type"], d["year"] or 9999, d["file"]))
    return out


# ------------------------------------------------------------------ domy

def _curated(root: Path, cache, load_yaml) -> list[dict]:
    d = root / "research/domy"
    out = []
    for p in sorted(d.glob("*.yml")) if d.is_dir() else []:
        meta = cache.get(p, "yaml", load_yaml)
        if isinstance(meta, dict) and meta.get("obec") and meta.get("cp") is not None:
            meta = dict(meta)
            meta["_file"] = _rel(p, root)
            out.append(meta)
    return out


def _village(desc: str, start: int, place: str) -> str:
    m = WORD_BEFORE_RE.search(desc[max(0, start - 40):start].rstrip(" ,"))
    if m:
        return m.group(1) or m.group(2)
    return re.sub(r"\s*\(.*?\)", "", place or "").strip()


def _house_refs(desc: str, place: str) -> list[tuple[str, str]]:
    refs = []
    for m in CP_RE.finditer(desc):
        before = desc[max(0, m.start() - 14):m.start()].lower()
        if any(w in before for w in CP_SKIP_BEFORE):
            continue
        v = _village(desc, m.start(), place)
        if v:
            refs.append((v, m.group(1)))
        break   # první č. p. v popisu = dům osoby
    return refs


def domy(root: Path, patch_files: list[Path], cache, load_yaml, people: dict, sources: list[dict]) -> list[dict]:
    curated = _curated(root, cache, load_yaml)
    alias: dict[str, str] = {}
    for c in curated:
        for a in [c["obec"]] + list(c.get("aliasy") or []):
            alias[fold(a)] = str(c["obec"])
    # známé obce = místa z patchů (bez závorky); tvar z popisu („z Lhoty“, „Lhot“) se přiřadí podle prvních 4 písmen
    known: dict[str, str] = {}
    for p in patch_files:
        data = cache.get(p, "yaml", load_yaml)
        for ch in (data or {}).get("changes") or [] if isinstance(data, dict) else []:
            if isinstance(ch, dict) and ch.get("place"):
                name = re.sub(r"\s*\(.*?\)", "", str(ch["place"])).strip()
                known.setdefault(fold(name), name)

    def canon(v: str) -> str:
        f = fold(v)
        if f in alias:
            return alias[f]
        if f in known:
            return alias.get(f, known[f])
        cand = [k for k in known if len(f) >= 4 and k[:4] == f[:4]]
        return alias.get(cand[0], known[cand[0]]) if len(cand) == 1 else v
    houses: dict[tuple[str, str], dict] = {}

    def house(v: str, cp: str) -> dict:
        key = (fold(canon(v)), str(cp))
        if key not in houses:
            houses[key] = {"obec": canon(v), "cp": str(cp), "events": [], "drzba": [], "listiny": [],
                           "nazev": "", "popis": "", "file": None}
        return houses[key]

    for p in patch_files:
        m = ID_IN_PATCH.match(p.name)
        data = cache.get(p, "yaml", load_yaml)
        if not m or not isinstance(data, dict):
            continue
        pid = m.group(1)
        for ch in data.get("changes") or []:
            if not isinstance(ch, dict) or ch.get("op") not in ("add_event", "update_event"):
                continue
            typ = ch.get("type")
            if not typ and ch.get("op") == "update_event":   # úprava bez typu: úmrtí poznáme podle věku / příčiny
                typ = "Death" if re.search(r"\b\d+\s*let\b|souchot|zemř|†", str(ch.get("description") or ""), re.I) else "Residence"
            if typ not in HOUSE_TYPES or ch.get("family"):
                continue
            desc = str(ch.get("description") or "")
            for v, cp in _house_refs(desc, str(ch.get("place") or "")):
                y, y2 = years(ch.get("date"))
                role = HOUSE_TYPES[typ]
                if VYMINEK_RE.search(desc):
                    role = "výminek"
                elif typ == "Property":
                    role = "vlastník"
                house(v, cp)["events"].append({
                    "id": pid, "name": (people.get(pid) or {}).get("name") or "", "role": role, "type": typ,
                    "date": str(ch.get("date") or ""), "year": y, "year_to": y2, "desc": desc, "patch": p.name,
                })

    for c in curated:
        h = house(str(c["obec"]), str(c["cp"]))
        h.update({"nazev": str(c.get("nazev") or ""), "popis": str(c.get("popis") or ""), "file": c["_file"]})
        for d in c.get("drzba") or []:
            kdo = d.get("kdo") or []
            kdo = kdo if isinstance(kdo, list) else [kdo]
            h["drzba"].append({"od": d.get("od"), "do": d.get("do"), "role": str(d.get("role") or ""),
                               "kdo": [{"id": str(k), "name": (people.get(str(k)) or {}).get("name") or str(k)}
                                       if re.match(r"^K\d", str(k)) else {"id": None, "name": str(k)} for k in kdo],
                               "pramen": str(d.get("pramen") or ""), "pozn": str(d.get("pozn") or "")})
        h["listiny"] += [str(x) for x in c.get("listiny") or []]
        for d in h["drzba"]:   # od/do do JSON vždy jako text nebo číslo (YAML může dát datum)
            for k in ("od", "do"):
                if d[k] is not None and not isinstance(d[k], (int, str)):
                    d[k] = str(d[k])

    by_file = {s["file"]: s for s in sources}
    for (vk, cp), h in houses.items():
        rx = re.compile(r"(?:č\.\s?(?:p\.|d\.)?|čp\.?|No\.?|Nro)\s*" + re.escape(cp) + r"\b")
        vnames = {fold(h["obec"])} | {a for a, c in alias.items() if fold(c) == vk}
        for s in sources:
            blob = s["title"] + " " + s["entry"] + " " + s["text"]
            fb = fold(blob)
            in_folder = re.search(rf"/cp0*{cp}$", s["folder"]) and any(v.split()[0] in fold(s["folder"]) for v in vnames)
            if in_folder or (any(v in fb for v in vnames) and rx.search(blob)):
                h["listiny"].append(s["file"])
        h["listiny"] = [f for f in dict.fromkeys(h["listiny"]) if f in by_file or (root / f).exists()]
        h["events"].sort(key=lambda e: (e["year"] or 9999, e["date"], e["id"]))
        h["drzba"].sort(key=lambda d: years(d["od"])[0] or 0)   # od může být číslo, „ABT 1838“ i datum
        ids = {e["id"] for e in h["events"]} | {k["id"] for d in h["drzba"] for k in d["kdo"] if k["id"]}
        ys = [e["year"] for e in h["events"] if e["year"]] + [y for d in h["drzba"] if (y := years(d["od"])[0])]
        h["persons"] = sorted(ids)
        h["od"], h["do"] = (min(ys), max(ys)) if ys else (None, None)
        h["key"] = f"{fold(h['obec']).replace(' ', '-')}-{cp}"
    out = [h for h in houses.values() if h["events"] or h["drzba"] or h["file"]]
    out.sort(key=lambda h: (fold(h["obec"]), int(h["cp"]) if h["cp"].isdigit() else 0))
    return out


# ------------------------------------------------------------------ povolání (třetí řádek karty osoby)

OCC_TYPES = {"Occupation": 3, "Residence": 2, "Property": 1, "Census": 1}
OCC_SKIP = re.compile(r"^(syn|dcera|manžel|manželka|svobodn|ženat|vdan|vdov|nevl|tchán|tchyně|švakr|žák|"
                      r"podnájem|čeledín.*škol|\[|nepřímo|vypočteno|ř\. k|hřbitov|výminek pro|domkářská chalupa|"
                      r"koupě|spoluvlastn|vlastník \(|věno|v dětství|matka |otec |sestra |bratr |„|majitel bytu$)", re.I)


def occupations(patch_files: list[Path], cache, load_yaml) -> dict[str, str]:
    """ID → všechna povolání chronologicky, oddělená „ / “ (z `Occupation`; jinak první část popisu bydliště,
    držby nebo sčítání: „chalupník, Lhota č. 7“ → „chalupník“). Popisy bez povolání (vztah v domácnosti, místo) se přeskočí."""
    found: dict[str, list[tuple[int, str]]] = {}
    for p in patch_files:
        m = ID_IN_PATCH.match(p.name)
        data = cache.get(p, "yaml", load_yaml)
        if not m or not isinstance(data, dict):
            continue
        pid = m.group(1)
        for ch in data.get("changes") or []:
            if not isinstance(ch, dict) or ch.get("op") != "add_event" or ch.get("family"):
                continue
            desc = str(ch.get("description") or "").strip()
            if ch.get("type") not in OCC_TYPES or not desc:
                continue
            occ = re.split(r"[,;]| č\.| v [A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]| z [A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]", desc)[0].strip(" .")
            if not occ or OCC_SKIP.match(occ) or len(occ) > 40 or occ[0].isupper() and ch.get("type") != "Occupation":
                continue
            y = years(ch.get("date"))
            for part in occ.split("/"):           # „chalupník / domkář“ v jednom popisu = dvě povolání
                hedge = "?" if re.search(r"pravděpodob|\[\?\]|\?", part) else ""
                part = re.sub(r"\s*[\(\[].*?[\)\]]", "", part).strip(" .?") + hedge   # „domkář (chalupník)“ → „domkář“
                if part:
                    found.setdefault(pid, []).append((y[0] or y[1] or 9999, part))
    out = {}
    for pid, items in found.items():
        seen: list[str] = []
        for _, occ in sorted(items, key=lambda x: x[0]):
            if occ.lower() not in (s.lower() for s in seen):
                seen.append(occ)
        out[pid] = " / ".join(seen)
    return out


# ------------------------------------------------------------------ zajímavosti (research/todo-zajimavosti.md)

ZAJ_REL = "research/todo-zajimavosti.md"
ZAJ_CLOSED = ("hotovo", "uzavřeno", "vyřešeno")


def zajimavosti(root: Path, ids_in) -> list[dict]:
    """Sekce `## otázka` se řádky `- proč:`, `- kde hledat:`, `- osoby:`, `- stav:`. Relativní odkazy v textu se
    převedou na `/api/file?p=<cesta ve stromu>`, aby šly otevřít z dashboardu."""
    p = root / ZAJ_REL
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    base = p.parent

    def links(s: str) -> str:
        def fix(m):
            target = m.group(2)
            if re.match(r"^[a-z]+:", target) or target.startswith("/"):
                return m.group(0)
            rel = (base / target).resolve()
            try:
                rel = rel.relative_to(root.resolve())
            except ValueError:
                return m.group(0)
            from urllib.parse import quote
            return f"[{m.group(1)}](/api/file?p={quote(str(rel))})"
        return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, s)

    out = []
    heads = list(re.finditer(r"^## (.+)$", text, re.M))
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        field = lambda k: next((m.group(1).strip() for m in re.finditer(rf"^- {k}:\s*(.+)$", body, re.M)), "")  # noqa: E731
        stav = field("stav") or "otevřeno"
        out.append({"n": i + 1, "title": h.group(1).strip(), "proc": links(field("proč")), "kde": links(field("kde hledat")),
                    "osoby": ids_in(field("osoby")), "osoby_text": field("osoby"), "stav": stav,
                    "open": not stav.lower().startswith(ZAJ_CLOSED)})
    return out
