"""Mapová data pro dashboard: kde kdo žil (z patchů), polohy čísel popisných, mapové vrstvy.

Vše se čte živě (cache podle mtime v serveru). Nic se negeneruje ani nezapisuje.

- Bydliště: události `add_event` v `T/patches/P-<ID>-<nn>.yml` s číslem popisným v `description`.
  Bere se jen typ, u něhož č. p. znamená bydliště osoby (narození, úmrtí, bydliště, sčítání,
  povolání „bytem…“). Sňatek a křest ne — tam bývá dům nevěsty, kmotry nebo porodní báby.
- Polohy domů: `mcp/czech-archives/gazetteer/*-cp.csv` (`cast_obce,cp,lat,lon,zdroj`, dnešní RÚIAN).
  Adresa se páruje na část obce (`resolve`): čtvrť z římské číslice za lomítkem (`66/III` → „Chlumec nad
  Cidlinou III“, čp. 66), část jmenovaná před č. p. („Chlumec nad Cidlinou, část Kladruby č. p. 40“ → Kladruby).
  Obec s více čtvrtěmi bez uvedené čtvrti se nehádá — bydliště je „čtvrť neurčena“ (jen střed obce).
- Polohy obcí: tabulky v `docs/mistopis/*/obce.md` (sloupec „lat, lon“) — pro obce bez dat o domech.
- Vrstvy: `cache/mapy/<oblast>/<vrstva>/xyz/` + `tilejson.json`, názvy a citace z `tools/mapy/vrstvy.yml`.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import yaml

RESIDENCE_TYPES = {"Birth", "Death", "Residence", "Census", "Occupation"}
CP_RE = re.compile(r"(?:čp\.|č\.\s?p\.|č\.)\s*(\d+)(?:\s*/\s*([IVX]{1,4})\b)?")
ROMAN_END_RE = re.compile(r"^(.*\S)\s+([IVX]{1,4})$")
CP_SKIP_BEFORE = ("poř", "pluk", "zápis u", "kniha", "matr")
MONTHS = {m: i for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = s.replace(" nad cidlinou", " n. c.").replace(" n.c.", " n. c.")
    return re.sub(r"\s+", " ", s.strip())


def house_number(desc: str) -> tuple[str, str | None, str] | None:
    """→ (čp., čtvrť římskou číslicí nebo None, text před č. p.)."""
    for m in CP_RE.finditer(desc):
        before = desc[max(0, m.start() - 12):m.start()].lower()
        if any(w in before for w in CP_SKIP_BEFORE):
            continue
        return m.group(1), m.group(2), desc[max(0, m.start() - 60):m.start()]
    return None


def resolve(residences: list[dict], houses: dict) -> list[dict]:
    """Doplní `place` na část obce z gazetteeru (`place_orig` = místo z patche). Viz docstring modulu."""
    names = {fold(n): n for n in houses}
    quarters: dict[str, list[str]] = {}          # fold(obec) → části s římskou číslicí
    for n in houses:
        m = ROMAN_END_RE.match(n)
        if m:
            quarters.setdefault(fold(m.group(1)), []).append(n)
    by_len = sorted(names, key=len, reverse=True)
    for r in residences:
        place = r["place_orig"] = r["place"]
        f = fold(place)
        pre = fold(r.pop("before", "")).rstrip(" ,;:")
        part = next((n for n in by_len if n != f and (pre == n or pre.endswith((" " + n, "," + n)))), None)
        quarter = r.get("quarter")
        if part:                                 # „…, část Kladruby č. p. 40“
            place = names[part]
        elif quarter and f in quarters:          # „66/III“
            place = names.get(fold(f"{place} {quarter}"), place)
            if place == r["place_orig"]:
                r["undetermined"] = f"čtvrť {quarter} není v gazetteeru"
        elif f not in names and f in quarters:
            if len(quarters[f]) == 1:            # jediná část s číslicí (Hradišťko II)
                place = quarters[f][0]
            else:                                # Chlumec I–IV bez čtvrti — nehádat
                r["undetermined"] = "čtvrť neurčena (" + ", ".join(sorted(quarters[f])) + ")"
        r["place"] = place
    return residences


def gedcom_years(value) -> tuple[int | None, int | None, str]:
    """`2 JAN 1848` → (1848, None, '1848-01-02'); `FROM 1848 TO 1881` → (1848, 1881, '')."""
    s = str(value or "").upper()
    m = re.search(r"FROM\s+(?:.*?)(\d{4})\s+TO\s+(?:.*?)(\d{4})", s)
    if m:
        return int(m.group(1)), int(m.group(2)), ""
    m = re.search(r"(?:(\d{1,2})\s+)?(?:([A-Z]{3})\s+)?(\d{4})", s)
    if not m:
        return None, None, ""
    y = int(m.group(3))
    iso = f"{y}-{MONTHS.get(m.group(2) or '', 0):02d}-{int(m.group(1) or 0):02d}" if m.group(2) else str(y)
    return y, None, iso


def residences(patch_files: list[Path], cache, load_yaml, root: Path) -> list[dict]:
    out = []
    for p in patch_files:
        m = re.match(r"^P-(K\d+(?:-[SCP]\d+)*)-(\d+)\.ya?ml$", p.name)
        if not m:
            continue
        data = cache.get(p, "yaml", load_yaml)
        if not isinstance(data, dict):
            continue
        for ch in data.get("changes") or []:
            if not isinstance(ch, dict) or ch.get("op") != "add_event" or ch.get("family"):
                continue
            if ch.get("type") not in RESIDENCE_TYPES:
                continue
            desc = str(ch.get("description") or "")
            hn = house_number(desc)
            if not hn:
                continue
            cp, quarter, before = hn
            y, y2, iso = gedcom_years(ch.get("date"))
            if not y:
                continue
            out.append({
                "id": m.group(1), "type": ch.get("type"), "date": str(ch.get("date") or ""), "iso": iso,
                "year": y, "year_to": y2, "place": str(ch.get("place") or ""), "cp": cp,
                "quarter": quarter, "before": before,
                "description": desc, "patch": p.name, "status": str(data.get("status") or "?"),
            })
    return out


def load_houses(path: Path) -> dict:
    houses: dict[str, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                houses.setdefault(row["cast_obce"], {})[row["cp"]] = [float(row["lat"]), float(row["lon"])]
            except (KeyError, ValueError):
                continue
    return houses


ROW_RE = re.compile(r"^\|\s*\**([^|*(]+?)\**\s*(?:\([^|]*\))?\s*\|.*?\|\s*(5\d\.\d+),\s*(1\d\.\d+)\s*\|", re.M)


def load_places(path: Path) -> dict:
    return {m.group(1).strip(): [float(m.group(2)), float(m.group(3))]
            for m in ROW_RE.finditer(path.read_text(encoding="utf-8"))}


def layer_years(name: str) -> list[int] | None:
    m = re.search(r"(1[789]\d\d)\s*[–-]\s*(1[89]\d\d|20\d\d)", name)
    if m:
        return [int(m.group(1)), int(m.group(2))]
    if "aktuální" in name.lower():
        return [date.today().year, date.today().year]
    return None


def layers(cache_dir: Path, vrstvy: dict) -> list[dict]:
    defs = (vrstvy or {}).get("vrstvy", {})
    out = []
    if not cache_dir.is_dir():
        return out
    for area in sorted(d for d in cache_dir.iterdir() if d.is_dir()):
        bounds = None
        for tj in area.glob("*/tilejson.json"):
            try:
                bounds = json.loads(tj.read_text(encoding="utf-8")).get("bounds")
                break
            except (OSError, json.JSONDecodeError):
                pass
        for lay in sorted(d for d in area.iterdir() if (d / "xyz").is_dir()):
            zooms = sorted(int(z.name) for z in (lay / "xyz").iterdir() if z.name.isdigit())
            if not zooms:
                continue
            sample = next((lay / "xyz" / str(zooms[0])).rglob("*.*"), None)
            d = defs.get(lay.name, {})
            name = d.get("nazev") or lay.name
            out.append({
                "area": area.name, "id": lay.name, "name": name,
                "attribution": d.get("citace") or "", "licence": d.get("licence") or "",
                "ext": sample.suffix.lstrip(".") if sample else "webp",
                "minzoom": zooms[0], "maxzoom": zooms[-1], "bounds": bounds,
                "years": layer_years(name),
            })
    return out
