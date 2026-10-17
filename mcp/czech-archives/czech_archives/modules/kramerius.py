"""Kramerius 7 — Česká digitální knihovna (CDK): fulltext v digitalizovaném tisku.

Noviny, adresáře, věstníky, vlastivědy, schematismy. Výsledky jsou **nápovědy** (jistota 0), ne fakta.
Ověřené chování API: docs/prameny/kramerius.md. Shrnutí:
- `q` musí mít pole: `text_ocr:"Novák Lučice"~10`; diakritika se ignoruje, skloňování ne → vyjmenovat tvary,
- `title.search` (hledání titulů) je naopak citlivé na diakritiku i skloňování,
- OCR stránky: `items/<pid>/ocr/text` bez `Accept: application/json`.
"""

from __future__ import annotations

import csv
import re
import unicodedata
import urllib.parse
from pathlib import Path

from ..core import Citation, RateLimitedClient, today

API = "https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0"
VIEW = "https://ceskadigitalniknihovna.cz/view/"
ARCHIVE = "Česká digitální knihovna (Kramerius)"
WORKBENCH = Path(__file__).resolve().parents[4]   # …/genealogy
DIGITALIZOVANE = WORKBENCH / "docs" / "prameny" / "digitalizovane"

CACHE_TTL = 21 * 86400.0        # odpovědi se cachují týdny
MAX_TERMS = 40
MAX_ROWS = 50
LAST_YEAR = 1950                # po 1950 je veřejného tisku málo (DNNT jen po přihlášení)
ADULT_AGE = 18
UNKNOWN_DEATH_SPAN = 60         # neznámé úmrtí: dospělost + 60 let

# Obce, které jsou zároveň obecnými slovy nebo mají mnoho jmenovců — hledat jen s příjmením
# v těsné blízkosti (proximity 5). Seznam není vyčerpávající; `plan` navíc označí i obce
# s předložkovým přívlastkem (Chlumec nad Cidlinou → „Chlumec“ je nejednoznačné).
NOISY_PLACES = {
    "kolesa", "vapno", "lhotka", "lhota", "tune", "ujezd", "hory", "doly", "bor", "zbyslav",
    "nova ves", "stara ves", "nove mesto", "hradec", "bezdekov", "vinice", "dubina", "luka",
    "lipa", "lipany", "skalka", "zahorí", "zahori", "podoli", "horka", "dolni", "horni",
}

_FL = ("pid,root.pid,root.title,model,date.str,title.search,rels_ext_index.sort,"
       "accessibility,date_range_start.year,cdk.collection")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _phrase(s: str) -> str:
    return s.replace("\\", " ").replace('"', " ").strip()


# --- tvary příjmení ----------------------------------------------------------------------

def surname_forms(surname: str) -> dict:
    """Tvary příjmení pro fulltext: {"sex": "m"|"f", "forms": [...]}.

    Mužské příjmení → mužské pády + ženské tvary (manželka, dcery se v tisku objevují s ním).
    Ženské příjmení (-ová, -á) → jen ženské tvary: mužskou podobu nelze spolehlivě odvodit
    (Kolářová → Kolář, Novotná → Novotný, Dvořáková → Dvořák).
    Pád jednotného čísla: 1.–7.; množné číslo jen „Novákovi / Novákové“ (rodina, manželé).
    """
    s = " ".join(surname.split())
    low = s.lower()
    forms: list[str] = []
    if low.endswith("ová"):
        stem = s[:-3]
        forms = [stem + "ová", stem + "ové", stem + "ovou", stem + "ovými"]
        return {"sex": "f", "forms": _uniq(forms)}
    if low.endswith("á"):
        stem = s[:-1]
        forms = [stem + "á", stem + "é", stem + "ou", stem + "ých"]
        return {"sex": "f", "forms": _uniq(forms)}
    if low.endswith("ý"):
        stem = s[:-1]
        forms = [s, stem + "ého", stem + "ému", stem + "ým", stem + "í"]
        female = [stem + "á", stem + "é", stem + "ou"]
        return {"sex": "m", "forms": _uniq(forms + female)}
    if low.endswith("a"):                     # Svoboda, Hora
        stem = s[:-1]
        forms = [s, stem + "y", stem + "ovi", stem + "u", stem + "ou"]
        female_stem = stem
    else:
        base = s
        if low.endswith("ek") and len(s) > 3:   # Jiránek → Jiránka
            base = s[:-2] + "k"
        elif low.endswith("ec") and len(s) > 3:  # Němec → Němce
            base = s[:-2] + "c"
        elif low.endswith("el") and len(s) > 3:  # Havel → Havla (i Havele) — oba tvary
            forms.append(s[:-2] + "la")
        if low.endswith("ec") and len(s) > 3:   # Němec → Němce, Němci
            forms += [s, base + "e", base + "ovi", base + "i", base + "em"]
        else:
            forms += [s, base + "a", base + "ovi", base + "u", base + "em"]
        female_stem = base
    female = [female_stem + "ová", female_stem + "ové", female_stem + "ovou"]
    forms += [female_stem + "ovi", female_stem + "ové"]   # Novákovi / Novákové (manželé, rodina)
    return {"sex": "m", "forms": _uniq(forms + female)}


def _uniq(items: list[str]) -> list[str]:
    seen, out = set(), []
    for i in items:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


# --- modul -------------------------------------------------------------------------------

class Kramerius:
    """Kramerius 7 / Česká digitální knihovna — fulltext v digitalizovaném tisku (nápovědy)."""

    id = "kramerius"
    archive = ARCHIVE
    capabilities = {"search", "page_text", "titles", "plan"}

    def __init__(self, min_interval: float = 1.5):
        self.http = RateLimitedClient("kramerius", min_interval=min_interval)

    # --- dotazy ---
    @staticmethod
    def build_query(terms: list[str], proximity: int = 10) -> str:
        """`text_ocr:"A B"~N` OR … — víceslovný tvar s proximity, jednoslovný bez ní."""
        parts = []
        for t in terms[:MAX_TERMS]:
            t = _phrase(t)
            if not t:
                continue
            parts.append(f'text_ocr:"{t}"~{int(proximity)}' if " " in t else f'text_ocr:"{t}"')
        if not parts:
            raise ValueError("terms: žádný použitelný tvar")
        return " OR ".join(parts)

    def _get(self, path: str, params: list[tuple[str, str]]) -> dict:
        return self.http.json(f"{API}/{path}?{urllib.parse.urlencode(params)}", ttl=CACHE_TTL)

    def search(self, terms: list[str], years: list[int] | tuple[int, int] | None = None,
               title_pid: str | None = None, proximity: int = 10, rows: int = 20,
               public_only: bool = True) -> dict:
        if len(terms) > MAX_TERMS:
            raise ValueError(f"terms: nejvýše {MAX_TERMS} tvarů najednou")
        rows = max(1, min(int(rows), MAX_ROWS))
        q = self.build_query(terms, proximity)
        params = [("q", q), ("fq", "model:page"), ("rows", str(rows)), ("fl", _FL),
                  ("hl", "true"), ("hl.fl", "text_ocr"), ("hl.fragsize", "120"), ("hl.snippets", "2")]
        if public_only:
            params.append(("fq", "accessibility:public"))
        if years:
            a, b = int(years[0]), int(years[1])
            params.append(("fq", f"date_range_start.year:[{a} TO {b}]"))
        if title_pid:
            params.append(("fq", f'root.pid:"{_phrase(title_pid)}"'))
        data = self._get("search", params)
        resp = data.get("response", {})
        hl = data.get("highlighting", {})
        pages = []
        for d in resp.get("docs", []):
            key = f"{d.get('root.pid')}!{d.get('pid')}"
            snippets = [re.sub(r"</?em>", "**", s).strip() for s in hl.get(key, {}).get("text_ocr", [])]
            pages.append(self._page_dict(d, snippets))
        return {"query": q, "num_found": resp.get("numFound", 0), "returned": len(pages), "pages": pages}

    def _page_dict(self, d: dict, snippets: list[str] | None = None) -> dict:
        cite = self._citation(d)
        out = {
            "pid": d.get("pid"),
            "title": d.get("root.title"),
            "root_pid": d.get("root.pid"),
            "date": d.get("date.str"),
            "page": d.get("title.search"),
            "page_index": d.get("rels_ext_index.sort"),
            "accessibility": d.get("accessibility"),
            "url": VIEW + str(d.get("pid")),
            "citation": cite.text,
        }
        if snippets is not None:
            out["snippets"] = snippets
        return {k: v for k, v in out.items() if v not in (None, "", [])}

    def page_meta(self, pid: str) -> dict:
        data = self._get("search", [("q", f'pid:"{_phrase(pid)}"'), ("fl", _FL), ("rows", "1")])
        docs = data.get("response", {}).get("docs", [])
        return docs[0] if docs else {}

    def page_text(self, pid: str, max_chars: int = 30000) -> dict:
        pid = _phrase(pid)
        if not re.fullmatch(r"uuid:[0-9a-fA-F-]{36}", pid):
            raise ValueError(f"pid musí mít tvar uuid:<UUID>, dostal jsem {pid!r}")
        text = self.http.text(f"{API}/items/{pid}/ocr/text", ttl=CACHE_TTL, accept="text/plain")
        meta = self.page_meta(pid)
        out = self._page_dict(meta) if meta else {"pid": pid, "url": VIEW + pid}
        out.update({"chars": len(text), "truncated": len(text) > max_chars, "text": text[:max_chars],
                    "note": "OCR je draft: jména a data ověřit proti snímku (jistota 0)."})
        return out

    def titles(self, query: str, rows: int = 15, public_only: bool = True) -> dict:
        """Titul (periodikum / monografie) podle slov v názvu → `root_pid` pro `title_pid`.

        `title.search` je citlivé na diakritiku a skloňování („Adresář Prahy“, ne „adresar Praha“).
        """
        words = [_phrase(w) for w in query.split()]
        words = [w for w in words if w and w.upper() not in ("AND", "OR", "NOT")]
        if not words:
            raise ValueError("query: prázdný dotaz")
        params = [("q", "title.search:(" + " ".join(words) + ")"),
                  ("fq", "model:(periodical OR monograph)"),
                  ("rows", str(max(1, min(int(rows), MAX_ROWS)))),
                  ("fl", "pid,root.title,model,date.str,accessibility,cdk.collection")]
        if public_only:
            params.append(("fq", "accessibility:public"))
        resp = self._get("search", params).get("response", {})
        found = [{
            "root_pid": d.get("pid"), "title": d.get("root.title"), "model": d.get("model"),
            "date": d.get("date.str"), "accessibility": d.get("accessibility"),
            "collections": d.get("cdk.collection"), "url": VIEW + str(d.get("pid")),
        } for d in resp.get("docs", [])]
        return {"num_found": resp.get("numFound", 0), "titles": [{k: v for k, v in t.items() if v} for t in found]}

    # --- citace ---
    def _citation(self, d: dict) -> Citation:
        pid = str(d.get("pid"))
        title = d.get("root.title") or "(titul neuveden)"
        date = d.get("date.str")
        page = d.get("title.search")
        if isinstance(page, list):
            page = page[0] if page else None
        text = f"{title}"
        if date:
            text += f", {date}"
        if page:
            text += f", s. {page}"
        text += f". {ARCHIVE}, {VIEW}{pid} [cit. {today()}]."
        return Citation(
            type="tisk (Kramerius)", archive=ARCHIVE, fond=None, parish=None, confession=None,
            book=title, years=str(date) if date else None, volume=None,
            image=d.get("rels_ext_index.sort"), url=VIEW + pid, accessed=today(),
            folio=str(page) if page else None, module=self.id, register_id=d.get("root.pid"),
            text=text)

    def citation(self, pid: str) -> dict:
        meta = self.page_meta(pid)
        if not meta:
            raise KeyError(f"stránka {pid} nenalezena")
        return self._citation(meta).to_dict()

    # --- plán dotazů ---
    def plan(self, tree_dir: str | Path, person_id: str) -> dict:
        """Z dossieru a aplikovaných patchů osoby sestaví dotazy (jen generuje, nespouští)."""
        tree = Path(tree_dir).expanduser()
        info = _person_info(tree, person_id)
        window, window_note = _window(info)
        out = {"person": person_id, "name": info["name"], "birth_year": info["birth"],
               "death_year": info["death"], "places": info["places"], "window": window,
               "window_note": window_note, "queries": [], "recommended_titles": [], "notes": []}
        if not info["surnames"]:
            out["notes"].append("v dossieru nenalezeno příjmení")
            return out
        if window is None:
            out["notes"].append("časové okno je prázdné (osoba narozená po ~1932 nebo žijící; veřejný tisk "
                                f"po {LAST_YEAR} je řídký a osobní údaje žijících do hledání nepatří)")
            return out
        forms: list[dict] = []
        for sn in info["surnames"]:
            f = surname_forms(sn["name"])
            forms.append({"surname": sn["name"], "kind": sn["kind"], **f})
        out["surname_forms"] = forms
        all_forms = _uniq([x for f in forms for x in f["forms"]])
        places = info["places"]
        if not places:
            out["notes"].append("v dossieru/patchích není žádná obec — samotné příjmení se nehledá "
                                "(příliš mnoho šumu); doplň obec a spusť plán znovu")
        for pl in places:
            variants = _place_variants(pl["place"])
            noisy = pl["noisy"]
            for var in variants:
                prox = 5 if (noisy or var["ambiguous"]) else 10
                terms = [f"{form} {var['text']}" for form in all_forms]
                # dávky po ≤ MAX_TERMS tvarech
                for i in range(0, len(terms), MAX_TERMS):
                    out["queries"].append({
                        "label": pl["place"] if var["text"] == pl["place"] else f"{pl['place']} → „{var['text']}“",
                        "terms": terms[i:i + MAX_TERMS], "years": window, "proximity": prox,
                        "noise": ("obec = obecné slovo / jmenovci — jen s příjmením v proximity 5" if noisy else
                                  "zkrácený název je nejednoznačný (jmenovci) — proximity 5, ověřit okres"
                                  if var["ambiguous"] else None),
                        "years_seen": pl["years"],
                    })
        out["queries"] = [{k: v for k, v in q.items() if v not in (None, [])} for q in out["queries"]]
        out["recommended_titles"] = _recommended_titles([p["place"] for p in places], window)
        out["notes"].append("Dotazy jen generuje; spouštěj je po jednom přes kramerius_search (rozestup ≥ 1,5 s). "
                            "Každý dotaz i „nenalezeno“ zapiš do research/log.md stromu.")
        return out


# --- podpora plánu: dossier, patche, okno, tituly ---------------------------------------

_SKIP_SURNAME_WORDS = {"roz.", "rozená", "rozen."}


def _read(path: Path) -> str:
    try:
        return path.read_text("utf-8")
    except OSError:
        return ""


def _person_files(tree: Path, person_id: str) -> tuple[Path | None, list[Path]]:
    people = tree / "research" / "people"
    dossier = None
    if people.is_dir():
        exact = people / f"{person_id}.md"
        if exact.exists():
            dossier = exact
        else:   # K0001-S2-P1-frantisek-svarc.md (ID + „-“ + slug s malými písmeny)
            for p in sorted(people.glob(f"{person_id}-*.md")):
                if re.fullmatch(r"[a-z0-9-]+", p.stem[len(person_id) + 1:]):
                    dossier = p
                    break
    patches = []
    pdir = tree / "patches"
    if pdir.is_dir():
        for p in sorted(pdir.glob(f"P-{person_id}-*.yml")):
            if re.search(rf"^person:\s*{re.escape(person_id)}\s*$", _read(p), re.M):
                patches.append(p)
    return dossier, patches


def _person_info(tree: Path, person_id: str) -> dict:
    dossier, patches = _person_files(tree, person_id)
    if dossier is None and not patches:
        raise FileNotFoundError(f"osoba {person_id} nenalezena v {tree}/research/people ani v patches")
    name = None
    maiden = None
    if dossier:
        m = re.search(r"^#\s+(.+?)\s+\(" + re.escape(person_id) + r"\)", _read(dossier), re.M)
        if m:
            name = m.group(1)
    summaries = []
    events: list[dict] = []
    for p in patches:
        txt = _read(p)
        m = re.search(r'^summary:\s*"?(.+?)"?\s*$', txt, re.M)
        if m:
            summaries.append(m.group(1))
        events += _patch_events(txt)
    if not name and summaries:
        name = re.split(r",\s|\s\*|\s+\(", summaries[0])[0].strip()
    name = name or person_id
    mm = re.search(r"\broz(?:\.|ená)\s+([A-ZÁ-Ž][\wÁ-ž-]+)", name)
    parts = [w for w in re.sub(r"\(.*?\)", " ", name).split() if w.lower() not in _SKIP_SURNAME_WORDS]
    surnames = []
    if mm:
        maiden = mm.group(1)
        idx = [w for w in parts]
        base = parts[:idx.index(maiden) - 1] if maiden in idx and idx.index(maiden) >= 1 else parts
        if base:
            surnames.append({"name": base[-1], "kind": "příjmení"})
        surnames.append({"name": maiden, "kind": "rozené"})
    elif parts:
        surnames.append({"name": parts[-1], "kind": "příjmení"})
    birth = death = None
    for e in events:
        if e.get("type") == "Birth" and e.get("year"):
            birth = birth or e["year"]
        if e.get("type") == "Death" and e.get("year"):
            death = death or e["year"]
    if birth is None:
        for s in summaries:
            m = re.search(r"\*\s*(?:\d+\.\s*)?(?:\d+\.\s*)?(\d{4})", s)
            if m:
                birth = int(m.group(1))
                break
    if death is None:
        for s in summaries:
            m = re.search(r"[†✝]\s*(?:\d+\.\s*)?(?:\d+\.\s*)?(\d{4})", s)
            if m:
                death = int(m.group(1))
                break
    # obce: z událostí (rok → obec); Residence i rodiště
    places: dict[str, dict] = {}
    for e in events:
        pl = (e.get("place") or "").strip()
        if not pl:
            continue
        rec = places.setdefault(pl, {"place": pl, "years": [], "noisy": _fold(pl) in NOISY_PLACES})
        if e.get("year") and e["year"] not in rec["years"]:
            rec["years"].append(e["year"])
    for rec in places.values():
        rec["years"].sort()
    return {"name": name, "surnames": surnames, "birth": birth, "death": death,
            "places": list(places.values()), "events": events}


def _patch_events(txt: str) -> list[dict]:
    """Události z `changes:` patche (type/date/place) bez PyYAML — bloky začínající `- op: add_event`."""
    events = []
    for block in re.split(r"^\s*-\s+op:\s*", txt, flags=re.M)[1:]:
        if not block.startswith("add_event"):
            continue
        block = re.split(r"\n(?=\S)", block, maxsplit=1)[0]   # bez navazujících klíčů (citations: …)
        ev = {}
        for key in ("type", "date", "place"):
            m = re.search(rf"^\s+{key}:\s*(.+?)\s*(?:#.*)?$", block, re.M)
            if m:
                ev[key] = m.group(1).strip().strip("'\"")
        ym = re.search(r"\b(\d{4})\b", ev.get("date", ""))
        ev["year"] = int(ym.group(1)) if ym else None
        events.append(ev)
    return events


def _window(info: dict) -> tuple[list[int] | None, str]:
    birth, death = info["birth"], info["death"]
    years = [y for p in info["places"] for y in p["years"]]
    if birth:
        start = birth + ADULT_AGE
        if death:
            end, note = death, f"od {ADULT_AGE} let (nar. {birth}) do úmrtí ({death})"
        else:
            end = birth + ADULT_AGE + UNKNOWN_DEATH_SPAN
            note = (f"od {ADULT_AGE} let (nar. {birth}); úmrtí neznámé → +{UNKNOWN_DEATH_SPAN} let "
                    f"({end}); nejvýše {LAST_YEAR}")
    elif years:
        start, end = min(years), (death or max(years) + UNKNOWN_DEATH_SPAN)
        note = f"narození neznámé → od nejstaršího doloženého roku ({start}); nejvýše {LAST_YEAR}"
    else:
        return None, "žádné roky v dossieru/patchích"
    end = min(end, LAST_YEAR)
    if start > end:
        return None, f"okno {start}–{end} je prázdné"
    return [start, end], note


def _place_variants(place: str) -> list[dict]:
    """Plný název + zkrácený před „nad/pod/u/pri“ (v tisku často jen „Chlumec“); zkrácený je nejednoznačný."""
    out = [{"text": place, "ambiguous": False}]
    m = re.match(r"^(.+?)\s+(?:nad|pod|u|pri|při|v|ve)\s+\S+", place)
    if m and m.group(1) != place:
        out.append({"text": m.group(1), "ambiguous": True})
    return out


def _years_of(obdobi: str) -> tuple[int, int] | None:
    nums = [int(n) for n in re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", obdobi or "")]
    return (min(nums), max(nums)) if nums else None


def _recommended_titles(places: list[str], window: list[int]) -> list[dict]:
    """Veřejné tituly se skenem a OCR z docs/prameny/digitalizovane/*.csv pro oblasti dané obce."""
    if not DIGITALIZOVANE.is_dir():
        return []
    want = {_fold(p) for p in places}
    rows: dict[str, list[dict]] = {}
    for f in sorted(DIGITALIZOVANE.glob("*.csv")):
        with open(f, encoding="utf-8", newline="") as fh:
            rows[f.stem] = list(csv.DictReader(fh))
    areas = {a for a, rs in rows.items() if any(_fold(r.get("obec", "")) in want for r in rs)}
    out, seen = [], set()
    for area, rs in rows.items():
        for r in rs:
            if r.get("forma") != "sken+ocr":
                continue
            note = (r.get("poznamka") or "").lower()
            if "neveřejn" in note or "dnnt" in note:
                continue
            obec_match = _fold(r.get("obec", "")) in want
            if not (obec_match or (area in areas and r.get("obec", "").startswith("("))):
                continue
            yrs = _years_of(r.get("obdobi", ""))
            if yrs and (yrs[1] < window[0] or yrs[0] > window[1]):
                continue
            url = r.get("text_url") or r.get("url") or ""
            m = re.search(r"uuid:[0-9a-f-]{36}", url)
            key = m.group(0) if m else url
            if key in seen:
                continue
            seen.add(key)
            out.append({"title": r.get("nazev"), "period": r.get("obdobi"), "area": area,
                        "root_pid": m.group(0) if m else None, "url": url,
                        "note": r.get("poznamka")})
    return out
