#!/usr/bin/env python3
"""Porovnání nezávislých čtení jednoho zápisu po polích.

    compare.py --claude <přepis.json|.md> --openai <openai_read.json> [--pero <snímek.pero.txt>]
               [--pero-lines 120-160] [--type N|O|Z] --out <report>    → report.md + report.json

Vstupy:
  --claude  přepis ze session: JSON ve formátu sources/*/*.json (`pole: [{pole|rubrika, raw, value,
            confidence}]`), Markdown přepis s tabulkou rubrik (`| Rubrika | Text |`), nebo i výstup
            openai_read (pak lze porovnat dva běhy modelu).
  --openai  výstup openai_read.py (může být i druhý přepis ve formátu session).
  --pero    prostý text PERO OCR po řádcích (bez struktury polí): pro každé pole se v textu hledá
            čtení Claude/OpenAI (fuzzy) → podporuje / nenalezeno. `--pero-lines` omezí hledání na
            řádky zápisu (PERO čte celou stránku — jinak hrozí falešná shoda se sousedním zápisem).

Normalizace (JEN pro porovnání, výstup ukazuje původní čtení): bez diakritiky, malá písmena,
staropis w→v, ss→s, th→t, g před samohláskou ponecháno, koncovka „-ho“ pryč, zkratky s tečkou
jako prefix („Frant.“ ~ František), data na (den, měsíc, rok), č. p. na číslo.

Výsledek po polích: `jisté` (3/3 shoda), `shoda` (2/2, PERO chybí/nenalezeno), `pravděpodobné`
(2/3 — uvedeno menšinové čtení), `podobné` (liší se jen drobně — ověřit), `neshoda`, `chybí`
(pole má jen jedno čtení). needs_review = vše kromě jisté/shoda/pravděpodobné + pole s [?] nebo
confidence low. Shoda dvou modelů není důkaz — jména a data stejně ověřuje člověk proti snímku.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- pole

KEY_FIELDS = {
    "N": ["jmeno_ditete", "datum_narozeni", "cislo_domu", "otec", "matka", "kmotri"],
    "O": ["datum_snatku", "cislo_domu", "zenich", "nevesta", "zenich_otec", "nevesta_otec", "svedci"],
    "Z": ["zemrely", "datum_umrti", "cislo_domu", "vek", "rodice_manzel"],
}
LIST_FIELDS = {"kmotri", "svedci", "rodice_manzel"}
SKIP = {"poznamky", "osoby", "rubriky"}

# aliasy názvů polí ze session (porovnává se po odstranění diakritiky, malými písmeny)
ALIASES = [
    (r"^(narozeni|datum narozeni|datum_narozeni|den narozeni)$", "datum_narozeni"),
    (r"^(krest|datum krtu|datum_krtu)$", "datum_krtu"),
    (r"^(dite|jmeno ditete|jmeno_ditete|jmeno pokrtence)$", "jmeno_ditete"),
    (r"^(misto|cislo domu|c\. ?p\.?|cislo_domu|misto narozeni)$", "cislo_domu"),
    (r"^otec$", "otec"),
    (r"^(ded_otec|ded_otcuv|otec_otec|otcuv otec)$", "otec_otec"),
    (r"^(babicka_otec|babicka_otcova|otec_matka|otcova matka)$", "otec_matka"),
    (r"^matka$", "matka"),
    (r"^(ded_matcin|ded_matka|matka_otec|matcin otec)$", "matka_otec"),
    (r"^(babicka_matka|babicka_matcina|matka_matka|matcina matka)$", "matka_matka"),
    (r"^(kmotri|kmotr|kmotra|kmotrove)$", "kmotri"),
    (r"^(baba|porodni baba|porodni_baba)$", "porodni_baba"),
    (r"^kmotra_baba$", "kmotri+porodni_baba"),
    (r"^(krtitel|krtil)$", "krtitel"),
    (r"^(datum_snatku|datum snatku|oddani|datum_oddavek|datum oddavek)$", "datum_snatku"),
    (r"^(oddavajici|oddal|ohlasky_oddavajici)$", "oddavajici"),
    (r"^zenich$", "zenich"),
    (r"^nevesta$", "nevesta"),
    (r"^(zenich_otec|otec_zenicha|otec zenicha)$", "zenich_otec"),
    (r"^(zenich_matka|matka_zenicha|matka zenicha)$", "zenich_matka"),
    (r"^(nevesta_otec|otec_nevesty|otec nevesty)$", "nevesta_otec"),
    (r"^(nevesta_matka|matka_nevesty|matka nevesty)$", "nevesta_matka"),
    (r"^(zenich_vek|vek_zenich|vek zenicha)$", "zenich_vek"),
    (r"^(nevesta_vek|vek_nevesta|vek nevesty)$", "nevesta_vek"),
    (r"^(zenich_stav|stav_zenich)$", "zenich_stav"),
    (r"^(nevesta_stav|stav_nevesta)$", "nevesta_stav"),
    (r"^(svedci|svedek)$", "svedci"),
    (r"^svedek_?\d*$", "svedci"),
    (r"^(zemrely|zemrela)$", "zemrely"),
    (r"^(umrti|datum_umrti|datum umrti)$", "datum_umrti"),
    (r"^(pohreb|datum_pohrbu)$", "datum_pohrbu"),
    (r"^(vek|stari|let)$", "vek"),
    (r"^(rodice_manzel|rodice|manzel|manzelka|rodice / manzel)$", "rodice_manzel"),
    (r"^(pricina_smrti|pricina smrti|nemoc|pricina)$", "pricina_smrti"),
    (r"^(nabozenstvi|vira)$", "nabozenstvi"),
    (r"^pohlavi$", "pohlavi"),
    (r"^(pohrbil|pohrbivajici)$", "pohrbil"),
]

# řádky tabulky v Markdown přepisu
MD_ROWS = [
    (r"den narozeni|mesic \(datum\)|narozeni / sv\. krtu|rok, mesic|^datum$|^mesic", "DATES"),
    (r"cislo domu|haus-?nro|misto, cislo domu", "cislo_domu"),
    (r"jmeno ditete|kindes|pokrtence", "jmeno_ditete"),
    (r"^otec|^vater", "otec"),
    (r"^matka|^mutter", "matka"),
    (r"kmotr|pathen.*nam|kmotrove", "kmotri"),
    (r"^baba|^bába", "porodni_baba"),
    (r"pod jmenem", "POD"),
    (r"krtil|krticiho", "krtitel"),
]

MONTHS = [  # celé slovo po odstranění diakritiky, malými písmeny
    (1, r"led(en|na|nu)?\.?|jan(\.|uar\w*|ner)|janner"),
    (2, r"unor(a|u)?|feb(\.|r\w*)"),
    (3, r"brez(en|na|nu)|mar(\.|z|ec|tii?|tius)"),
    (4, r"dub(en|na|nu)|apr(\.|il\w*)"),
    (5, r"kvet(en|na|nu)|mai|maj(i|us)?"),
    (6, r"cerv(en|na|nu)|jun(\.|i|ii|ius)"),
    (7, r"cerven(ec|ce|ci)|jul(\.|i|ii|ius)"),
    (8, r"srp(en|na|nu)|aug(\.|ust\w*)"),
    (9, r"zari|sep(\.|t\.?|tember\w*)"),
    (10, r"rij(en|na|nu)|okt(\.|ober)|oct(\.|ob\w*)"),
    (11, r"listopad(u|e)?|nov(\.|ember\w*)"),
    (12, r"prosin(ec|ce|ci)|dez(\.|ember)|dec(\.|emb\w*)"),
]
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9,
         "x": 10, "xi": 11, "xii": 12}

STOP_LOWER = True  # jádro jména končí prvním slovem s malým písmenem


# ---------------------------------------------------------------- normalizace

def strip_diac(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_token(t: str) -> str:
    t = strip_diac(t).lower()
    t = re.sub(r"-ho$", "", t)
    t = re.sub(r"[^a-z0-9.]", "", t)
    t = t.replace("w", "v").replace("ss", "s").replace("th", "t").replace("ß", "s")
    return t


def stem(t: str) -> str:
    return re.sub(r"(ove|ova|eho|ho|ym|y|a|e|i|u)$", "", t) if len(t) > 4 else t


def tok_match(a: str, b: str) -> str:
    """'eq' | 'abbr' | 'sim' | 'no' pro dva normalizované tokeny."""
    a1, b1 = a.rstrip("."), b.rstrip(".")
    if not a1 or not b1:
        return "no"
    if a1 == b1:
        return "eq"
    if (a.endswith(".") and b1.startswith(a1)) or (b.endswith(".") and a1.startswith(b1)):
        return "abbr"
    # ženský tvar příjmení / pádové koncovky: Klicpera ~ Klicperová, Novotný ~ Novotná ~ Novotného
    if len(a1) >= 4 and len(b1) >= 4 and stem(a1) == stem(b1):
        return "eq"
    if difflib.SequenceMatcher(None, a1, b1).ratio() >= 0.8:
        return "sim"
    return "no"


def uncertain(s: str | None) -> bool:
    return bool(s) and ("[?" in s or "?]" in s or re.search(r"\[[^\]]*\?\]", s) is not None)


def clean_brackets(s: str) -> str:
    s = re.sub(r"\[\?\]", " ", s)
    return re.sub(r"[\[\]?]", "", s)


def name_core(s: str | None) -> list[str]:
    """Tokeny jména: od začátku po první čárku / slovo s malým písmenem (stav, povolání…)."""
    if not s:
        return []
    s = clean_brackets(s)
    s = re.sub(r"\(([^)]*)\)", lambda m: " " + m.group(1) + " " if not re.search(r"\b[a-zčřšžýáíéůú]{3,}", m.group(1)) else " ", s)
    s = re.split(r"[,;·]| roz\.| rozen", s)[0]
    out = []
    for raw in re.split(r"[\s/]+", s.strip()):
        if not raw:
            continue
        if raw[0].islower() and out:
            break
        if raw[0].islower() and not out:
            continue
        t = norm_token(raw)
        if t and not t.isdigit():
            out.append(t)
    return out


def split_list(s: str | None) -> list[str]:
    if not s:
        return []
    s = re.sub(r"\([^)]*\)", " ", s)
    parts = re.split(r"\s*(?:;|·| / |\n|, a | a )\s*", s)
    return [p for p in parts if name_core(p)]


def month_of(word: str) -> int | None:
    w = strip_diac(word).lower()
    if w.endswith(".") and w[:-1] in ROMAN:  # římské číslice jen s tečkou („VI.“), ne předložka „v“
        return ROMAN[w[:-1]]
    for n, pat in MONTHS:
        if re.fullmatch(pat, w):
            return n
    return None


def parse_date(s: str | None, year_hint: int | None = None) -> tuple | None:
    """(rok|None, měsíc, den) z ISO nebo z textu („23. ledna 1882“, „14/4 1910“, „6. VI. 1936“)."""
    if not s:
        return None
    m = re.search(r"\b(1[5-9]\d\d)-(\d\d)-(\d\d)\b", s)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    s2 = clean_brackets(s)
    y = re.search(r"\b(1[5-9]\d\d)\b", s2)
    year = int(y.group(1)) if y else year_hint
    m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\.?\s+(1[5-9]\d\d)\b", s2)  # 23/1 1882
    if m:
        return int(m.group(3)), int(m.group(2)), int(m.group(1))
    days = [m for m in re.finditer(r"\b(\d{1,2})\b", s2) if 1 <= int(m.group(1)) <= 31]
    words = [m for m in re.finditer(r"[^\W\d_]+\.?", s2) if month_of(m.group(0))]
    if days and words:
        mon = words[0]
        before = [d for d in days if d.start() < mon.start()]
        day = before[0] if before else days[0]
        return year, month_of(mon.group(0)), int(day.group(1))
    return None


def parse_number(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"\b(\d{1,4})\b", clean_brackets(s))
    return m.group(1) if m else None


def kind(key: str) -> str:
    if key.startswith("datum"):
        return "date"
    if key == "cislo_domu":
        return "number"
    if key in LIST_FIELDS:
        return "list"
    if key in ("vek", "nabozenstvi", "pohlavi", "manzelske", "pricina_smrti"):
        return "text"
    return "name"


# ---------------------------------------------------------------- načtení čtení

def F(raw, value=None, conf=None) -> dict:
    return {"raw": raw, "value": value, "confidence": conf}


def load_openai(d: dict) -> dict:
    z = d["cteni"].get("zapis") or {}
    out = {}
    for k, v in z.items():
        if k in SKIP:
            continue
        if isinstance(v, list):
            items = [x.get("jmeno", x) if isinstance(x, dict) else x for x in v]
            items = [i for i in items if isinstance(i, dict) and (i.get("raw") or i.get("value"))]
            if items:
                out[k] = {"items": items,
                          "confidence": min((i.get("confidence") or "high" for i in items),
                                            key=["low", "medium", "high"].index)}
        elif isinstance(v, dict) and "jmeno" in v:
            j = v["jmeno"]
            if j.get("raw") or j.get("value"):
                full = " ".join(x.get("raw") or "" for x in v.values() if isinstance(x, dict))
                out[k] = {**j, "full": full}
        elif isinstance(v, dict) and (v.get("raw") or v.get("value")):
            out[k] = v
    return out


def alias(name: str) -> str | None:
    n = strip_diac(name).lower().strip()
    for pat, key in ALIASES:
        if re.search(pat, n):
            return key
    return None


def load_session_json(d: dict) -> dict:
    out: dict = {}
    for p in d.get("pole", []):
        name = p.get("pole") or p.get("rubrika") or ""
        key = alias(name)
        if not key:
            continue
        for k in key.split("+"):
            f = F(p.get("raw"), p.get("value"), p.get("confidence"))
            if kind(k) == "list":
                src = f["value"] or f["raw"]
                raws = split_list(f["raw"])
                vals = split_list(f["value"])
                items = [F(raws[i] if i < len(raws) else None, v, f["confidence"]) for i, v in enumerate(vals or raws)]
                out.setdefault(k, {"items": [], "confidence": f["confidence"]})["items"].extend(items)
            elif k not in out:
                out[k] = f
    return out


def load_markdown(text: str) -> dict:
    yh = None
    for line in text.splitlines():
        if re.match(r"\s*(Záhlaví|Hlavička)", line) or line.startswith("# "):
            m = re.search(r"\b(1[5-9]\d\d)\b", line)
            if m:
                yh = int(m.group(1))
                break
    out: dict = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m or set(m.group(1)) <= set("-: "):
            continue
        label, cell = strip_diac(m.group(1)).lower(), m.group(2)
        cell = re.sub(r"\*\(([^)]*)\)\*", "", cell).replace("*", "").replace("`", "")
        for pat, key in MD_ROWS:
            if not re.search(pat, label):
                continue
            if key == "DATES":
                d1 = parse_date(cell, yh)
                days = re.findall(r"\b(\d{1,2})\.?\s*(?=/|\s|[a-zA-Zá-ž])", clean_brackets(cell))
                if d1:
                    out["datum_narozeni"] = F(cell, "%s-%02d-%02d" % (d1[0] or "????", d1[1], d1[2]))
                    same = re.search(r"t[eé]ž\s+den|t[yý]ž\s+den|ten\s+t", cell)
                    if same:
                        out["datum_krtu"] = F(cell, out["datum_narozeni"]["value"])
                    elif "/" in cell and len(days) >= 2:
                        out["datum_krtu"] = F(cell, "%s-%02d-%02d" % (d1[0] or "????", d1[1], int(days[1])))
            elif key == "POD":
                b = re.search(r"[Bb]aba\s+(?:zkoušená\s+)?(.+)", cell)
                if b:
                    out.setdefault("porodni_baba", F(b.group(1)))
            elif key == "kmotri":
                if "kmotri" not in out:
                    items = [F(x) for x in split_list(cell)]
                    if items:
                        out["kmotri"] = {"items": items, "confidence": None}
            elif key not in out:
                out[key] = F(cell)
            break
    return out


def load_any(path: str) -> tuple[dict, dict]:
    p = Path(path)
    if p.suffix.lower() == ".md":
        return load_markdown(p.read_text()), {"format": "markdown"}
    d = json.loads(p.read_text())
    if isinstance(d.get("cteni"), dict):   # openai_read; session JSON může mít "cteni": "claude" (jen štítek)
        return load_openai(d), {"format": "openai_read", "model": d.get("model"), "typ": d.get("typ"),
                                "zapis_nalezen": d["cteni"].get("zapis_nalezen"),
                                "umisteni": d["cteni"].get("umisteni")}
    return load_session_json(d), {"format": "session-json", "typ": d.get("typ")}


# ---------------------------------------------------------------- porovnání dvou čtení

RANK = {"eq": 3, "abbr": 3, "sim": 2, "no": 0}


def cmp_names(a: list[str], b: list[str]) -> str:
    if not a or not b:
        return "chybí"
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    best = []
    for t in short:
        best.append(max((RANK[tok_match(t, u)] for u in long_), default=0))
    if all(x == 3 for x in best):
        # jedno čtení má víc tokenů (např. jen „Marie“ × „Marie Lhotáková“) → není to shoda, jen podobné
        return "shoda" if len(a) == len(b) else "podobné"
    if all(x >= 2 for x in best):
        return "podobné"
    return "neshoda"


def disp(f: dict | None) -> str:
    if not f:
        return "—"
    if "items" in f:
        return "; ".join(disp(i) for i in f["items"])
    r, v = f.get("raw"), f.get("value")
    if r and v and norm_token(r.replace(" ", "")) != norm_token(v.replace(" ", "")):
        return f"{r} → {v}"
    return r or v or "—"


def cmp_field(key: str, a: dict | None, b: dict | None) -> str:
    if not a or not b:
        return "chybí"
    k = kind(key)
    if k == "date":
        da = parse_date(a.get("value")) or parse_date(a.get("raw"))
        db = parse_date(b.get("value")) or parse_date(b.get("raw"))
        if not da or not db:
            return "chybí"
        if da[1:] != db[1:]:
            return "neshoda"
        if da[0] and db[0] and da[0] != db[0]:
            return "neshoda"
        return "shoda"
    if k == "number":
        na = parse_number(a.get("value")) or parse_number(a.get("raw"))
        nb = parse_number(b.get("value")) or parse_number(b.get("raw"))
        if not na or not nb:
            return "chybí"
        return "shoda" if na == nb else "neshoda"
    if k == "list":
        ia, ib = a.get("items", []), b.get("items", [])
        if not ia or not ib:
            return "chybí"
        statuses = []
        free = list(ib)
        for x in ia:
            best, bi = "neshoda", None
            for j, y in enumerate(free):
                s = cmp_field("_name", x, y)
                if s == "shoda" or (s == "podobné" and best == "neshoda"):
                    best, bi = s, j
                if s == "shoda":
                    break
            statuses.append(best)
            if bi is not None:
                free.pop(bi)
        if all(s == "shoda" for s in statuses) and len(ia) == len(ib):
            return "shoda"
        if all(s in ("shoda", "podobné") for s in statuses):
            return "podobné"  # i když jedno čtení má navíc osobu
        return "neshoda"
    if k == "text":
        ta = norm_token((a.get("value") or a.get("raw") or "").replace(" ", ""))
        tb = norm_token((b.get("value") or b.get("raw") or "").replace(" ", ""))
        if ta == tb or ta.startswith(tb) or tb.startswith(ta):
            return "shoda"
        return "podobné" if difflib.SequenceMatcher(None, ta, tb).ratio() > 0.75 else "neshoda"
    # jména: value×value i raw×raw, rozhoduje HORŠÍ z dostupných (dřív nejlepší → falešné shody, kontrola G-01);
    # křížové porovnání jen když jedno čtení nemá value ani raw
    order = ["chybí", "neshoda", "podobné", "shoda"]
    digits = lambda f: re.findall(r"\d+", f.get("raw") or f.get("value") or "")
    da, db = digits(a), digits(b)
    if da and db and da != db:
        return "neshoda"          # čísla (datum ve věku, č. p.) se liší → nikdy shoda, i když jména sedí
    res = [r for r in (cmp_names(name_core(a.get("value")), name_core(b.get("value"))),
                       cmp_names(name_core(a.get("raw")), name_core(b.get("raw")))) if r != "chybí"]
    if not res:
        res = [cmp_names(name_core(a.get("value") or a.get("raw")), name_core(b.get("raw") or b.get("value")))]
    worst = min(res, key=order.index)
    if worst == "neshoda" and res[0] == "shoda" and len(res) > 1:
        return "podobné"          # normalizované hodnoty sedí, doslovná čtení se liší (pravopis, pád) → jen k ověření
    return worst


# ---------------------------------------------------------------- PERO

def pero_tokens(lines: list[str]) -> list[str]:
    return [norm_token(t) for ln in lines for t in re.split(r"[\s,;:/()]+", ln) if norm_token(t)]


def pero_supports(key: str, f: dict | None, lines: list[str], toks: list[str]) -> bool | None:
    """True = čtení nalezeno v textu PERO, False = nenalezeno, None = nelze hledat."""
    if not f:
        return None
    k = kind(key)
    if k == "number":
        n = parse_number(f.get("raw")) or parse_number(f.get("value"))
        return None if not n else n in toks
    if k == "date":
        d = parse_date(f.get("value")) or parse_date(f.get("raw"))
        if not d:
            return None
        for ln in lines:
            for m in re.finditer(r"\b(\d{1,2})\.?\s*([^\s\d.,]+)", ln):
                if int(m.group(1)) == d[2] and month_of(m.group(2)) == d[1]:
                    return True
            if re.search(rf"\b{d[2]}\s*/\s*{d[1]}\b", ln):
                return True
        return False
    if k == "list":
        items = f.get("items", [])
        res = [pero_supports("_name", i, lines, toks) for i in items]
        res = [r for r in res if r is not None]
        return None if not res else all(res)
    core = name_core(f.get("raw")) or name_core(f.get("value"))
    if k == "text":
        core = [norm_token(x) for x in (f.get("raw") or f.get("value") or "").split() if norm_token(x)]
    if not core:
        return None
    return all(any(RANK[tok_match(t, u)] >= 2 for u in toks) for t in core)


# ---------------------------------------------------------------- celkový výsledek

def verdict(key, readings: dict, pero) -> dict:
    """readings: {'claude': f, 'openai': f}; pero: (lines, toks) nebo None."""
    names = [n for n, f in readings.items() if f]
    pair = cmp_field(key, readings.get("claude"), readings.get("openai"))
    res = {"claude": disp(readings.get("claude")), "openai": disp(readings.get("openai")),
           "claude_openai": pair}
    psup = {}
    if pero is not None:
        for n, f in readings.items():
            psup[n] = pero_supports(key, f, *pero)
        res["pero"] = {n: ("nalezeno" if v else "nenalezeno" if v is False else "—") for n, v in psup.items()}
    if len(names) < 2:
        status = "chybí"
    elif pair == "shoda":
        found = [v for v in psup.values() if v is not None]
        status = "jisté" if found and all(found) else "shoda"
    elif pair == "neshoda" and pero is not None and sum(bool(v) for v in psup.values()) == 1:
        win = next(n for n, v in psup.items() if v)
        lose = next(n for n in psup if n != win)
        status = "pravděpodobné"
        res["vetsina"] = f"{win}+pero"
        res["mensinove_cteni"] = {lose: res[lose]}
    else:
        status = pair
    res["vysledek"] = status
    flags = []
    for n, f in readings.items():
        if not f:
            continue
        txt = json.dumps(f, ensure_ascii=False)
        if uncertain(txt):
            flags.append(f"{n}: [?]")
        conf = (f.get("confidence") or "")
        if str(conf).lower() in ("low", "nízká"):
            flags.append(f"{n}: confidence low")
    if flags:
        res["priznaky"] = flags
    res["needs_review"] = status not in ("jisté", "shoda", "pravděpodobné") or bool(flags)
    return res


SYMB = {"jisté": "✓✓", "shoda": "✓", "pravděpodobné": "✓?", "podobné": "≈", "neshoda": "✗", "chybí": "∅"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude", required=True, help="přepis ze session (.json / .md) nebo openai_read")
    ap.add_argument("--openai", required=True, help="výstup openai_read.py")
    ap.add_argument("--pero", help="prostý text PERO po řádcích (<snímek>.pero.txt)")
    ap.add_argument("--pero-lines", help="rozsah řádků PERO patřících k zápisu, např. 40-62 (1 = první)")
    ap.add_argument("--type", choices=["N", "O", "Z", "scitani", "doklad"])
    ap.add_argument("--fields", help="porovnat jen tato pole (čárkou); výchozí = všechna společná")
    ap.add_argument("--out", required=True, help="základ názvu výstupu → .md + .json")
    a = ap.parse_args()

    ca, ma = load_any(a.claude)
    ob, mb = load_any(a.openai)
    typ = a.type or mb.get("typ") or ("N" if "jmeno_ditete" in ca or "jmeno_ditete" in ob else "N")
    if typ not in ("N", "O", "Z", "scitani", "doklad"):
        typ = "N"
    pero = None
    if a.pero:
        lines = Path(a.pero).read_text().splitlines()
        if a.pero_lines:
            s, e = (int(x) for x in a.pero_lines.split("-"))
            lines = lines[s - 1:e]
        pero = (lines, pero_tokens(lines))

    keys = KEY_FIELDS.get(typ, [])
    rest = [k for k in list(ca) + list(ob) if k not in keys]
    allk = list(dict.fromkeys(keys + rest))
    if a.fields:
        allk = [k.strip() for k in a.fields.split(",")]

    fields = {}
    for k in allk:
        fields[k] = verdict(k, {"claude": ca.get(k), "openai": ob.get(k)}, pero)
        fields[k]["klicove"] = k in keys

    keyres = [fields[k]["vysledek"] for k in keys if k in fields]
    summary = {
        "typ": typ,
        "klicova_pole": len(keyres),
        "klicova_shoda": sum(r in ("jisté", "shoda") for r in keyres),
        "klicova_prehled": {k: fields[k]["vysledek"] for k in keys if k in fields},
        "needs_review": [k for k, v in fields.items() if v["needs_review"]],
    }
    report = {"vstupy": {"claude": {"soubor": a.claude, **ma}, "openai": {"soubor": a.openai, **mb},
                         **({"pero": {"soubor": a.pero, "radky": a.pero_lines}} if a.pero else {})},
              "souhrn": summary, "pole": fields}

    md = [f"# Porovnání čtení — {Path(a.claude).name} × {Path(a.openai).name}", ""]
    if mb.get("model"):
        md.append(f"OpenAI model: `{mb['model']}`" + (f", zápis: {mb.get('umisteni')}" if mb.get("umisteni") else ""))
    md.append(f"Klíčová pole ve shodě: **{summary['klicova_shoda']}/{summary['klicova_pole']}**"
              + (" · PERO: " + Path(a.pero).name if a.pero else ""))
    md += ["", "| pole | Claude | OpenAI | " + ("PERO | " if pero else "") + "výsledek | ověřit |",
           "|---|---|---|" + ("---|" if pero else "") + "---|---|"]
    for k, v in fields.items():
        cell = lambda s: (s or "—").replace("|", "\\|")
        name = f"**{k}**" if v["klicove"] else k
        prow = ""
        if pero:
            prow = cell(", ".join(f"{n[0].upper()}: {s}" for n, s in v.get("pero", {}).items())) + " | "
        note = v["vysledek"]
        if v.get("mensinove_cteni"):
            note += " (menšina: " + "; ".join(f"{n} „{t}“" for n, t in v["mensinove_cteni"].items()) + ")"
        md.append(f"| {name} | {cell(v['claude'])} | {cell(v['openai'])} | {prow}{SYMB.get(v['vysledek'], '')} "
                  f"{note} | {'⚠ ' + ', '.join(v.get('priznaky', [])) if v['needs_review'] else ''} |")
    md += ["", "Legenda: ✓✓ jisté (3/3) · ✓ shoda (2/2) · ✓? pravděpodobné (2/3) · ≈ podobné · ✗ neshoda · ∅ chybí.",
           "Shoda není důkaz — jména a data ověř proti výřezu snímku.", ""]

    out = Path(a.out)
    base = out.with_suffix("") if out.suffix in (".md", ".json") else out
    base.parent.mkdir(parents=True, exist_ok=True)
    Path(str(base) + ".md").write_text("\n".join(md))
    Path(str(base) + ".json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(f"{base}.md / .json — klíčová pole {summary['klicova_shoda']}/{summary['klicova_pole']}, "
          f"k ověření: {', '.join(summary['needs_review']) or '—'}")


if __name__ == "__main__":
    main()
