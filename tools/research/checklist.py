"""Checklist osoby — strojová podoba docs/metodika/checklist-osoby.md.

Dvě úrovně: **základní** (fáze I výzkumu, docs/metodika/faze-vyzkumu.md) a **rozšířený**. Která položka na osobu
padá, se počítá vždy znovu z jejích údajů (Gramps → dossier → odhad), takže nová položka v `ITEMS` se hned
objeví u všech, kterých se týká. Dossier drží jen ruční stavy podle klíče (`- [-] z: … — důvod`).

Stav položky: `[ ]` neprohledáno · `[x]` nalezeno · `[-]` nenalezeno (prohledáno, co šlo — důvod / závora).
`[x]` se doplní samo, když má osoba v Gramps odpovídající událost s citací.

Přidat položku = jeden řádek v `ITEMS` (+ případně pravidlo v `auto_found`).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

TODAY_YEAR = 2026
GEN_YEARS = 30            # odhad roku narození podle generace (bez data)

ZAKLADNI, ROZSIRENY = "základní", "rozšířený"
NEPROHLEDANO, NALEZENO, NENALEZENO = " ", "x", "-"
LEGACY = {"~": NALEZENO, "n": NENALEZENO}     # staré stavy: slabý pramen = nalezeno, neexistuje = nenalezeno
STATE_CS = {NEPROHLEDANO: "neprohledáno", NALEZENO: "nalezeno", NENALEZENO: "nenalezeno"}


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    tier: str = ROZSIRENY
    start: int | None = None      # první rok, kdy pramen existuje
    end: int | None = None        # poslední rok
    when: str = "always"          # always | married | dead | male | situational
    hint: str = ""                # kde hledat (do dossieru jako výchozí poznámka)
    aliases: tuple = ()           # starší štítky ze sessions (převod starého formátu)


CENSUS_YEARS = (1857, 1869, 1880, 1890, 1900, 1910, 1921)
CENSUS_DAY = {1857: (10, 31), 1921: (2, 15)}           # rozhodný den (měsíc, den); ostatní 31. 12.

ITEMS = [
    # --- základní (fáze I)
    Item("n", "narození / křest", ZAKLADNI, hint="matrika N, online starší 100 let", aliases=("narození", "křest")),
    Item("rodice", "rodiče", ZAKLADNI, hint="jména z N/O → osoby ve stromu, jinak závora"),
    Item("o", "sňatek", ZAKLADNI, when="married", hint="matrika O, online starší 75 let", aliases=("vlastní sňatek",)),
    Item("z", "úmrtí / pohřeb", ZAKLADNI, when="dead", hint="matrika Z, online starší 75 let", aliases=("úmrtí",)),
    *[Item(f"scitani{y}", f"sčítání lidu {y}", ZAKLADNI, y, y, hint="SOA/SOkA; nedochováno → nenalezeno")
      for y in CENSUS_YEARS],
    # --- rozšířený
    Item("o_parents", "sňatek rodičů", hint="matrika O — ověřuje vazbu na rodiče"),
    Item("siblings", "narození sourozenců", hint="matrika N — kontrola rodiny, č. p., kmotrů"),
    Item("soupis1651", "soupis poddaných podle víry 1651", start=1651, end=1651),
    Item("bernirula", "berní rula 1654 (Čechy) / lánové rejstříky (Morava)", start=1654, end=1679,
         when="situational", hint="jen držitel usedlosti"),
    Item("terez", "tereziánský katastr", start=1748, end=1757, when="situational", hint="jen držitel usedlosti"),
    Item("josef", "josefský katastr", start=1785, end=1789, when="situational", hint="jen držitel usedlosti"),
    Item("stabilni", "stabilní katastr (indikační skica)", start=1824, end=1843, when="situational",
         hint="jen držitel usedlosti"),
    Item("grunt", "pozemková / gruntovní kniha", start=1550, end=1950, when="situational", hint="jen držitel usedlosti"),
    Item("prihlasky", "policejní přihláška Praha", start=1850, end=1914, when="situational", hint="jen pobyt v Praze"),
    Item("kmenovy", "vojenský kmenový list (VÚA)", start=1820, end=1918, when="male", hint="odvodní věk"),
    Item("ww1", "Verlustlisten / kartotéka padlých 1. sv. v.", start=1914, end=1918, when="male"),
    Item("legie", "legionáři (VÚA)", start=1914, end=1920, when="male"),
    Item("ww2", "padlí 2. sv. v. / odboj / holocaust.cz", start=1938, end=1945),
    Item("domovske", "domovský list / domovská obec", start=1863, end=1948),
    Item("skola", "školní matriky / katalogy", start=1800, end=1990, when="situational", hint="dítě školního věku"),
    Item("hrob", "hrob (BillionGraves, hřbitovní evidence)", start=1800, when="dead", aliases=("hrob",)),
    Item("tisk", "parte, noviny (Kramerius)", start=1800, when="situational"),
    Item("emigrace", "vystěhování (lodní seznamy)", start=1850, end=1939, when="situational",
         hint="jen při podezření na emigraci"),
    Item("rodina", "rodinné doklady (rodný/oddací/úmrtní list, fotky)", start=1880, aliases=("rodinné doklady",)),
]
BY_KEY = {it.key: it for it in ITEMS}


# ---------------------------------------------------------------- údaje o osobě

@dataclass
class Facts:
    """Co víme o osobě pro výběr položek a automatické `[x]`. Roky mohou být odhad (`*_est`)."""
    birth: int | None = None
    death: int | None = None
    birth_est: bool = False
    birth_md: tuple[int, int] | None = None              # (měsíc, den), je-li datum známé
    death_md: tuple[int, int] | None = None
    male: bool | None = None
    married: bool = False
    dead: bool = False
    marriage: int | None = None
    parents: tuple[bool, bool] = (False, False)          # otec, matka ve stromu
    child_birth: int | None = None                       # narození nejstaršího dítěte (pro odhad)
    found: dict[str, str] = field(default_factory=dict)  # klíč → doklad (Gramps událost s citací)


def generation(pid: str) -> int:
    """Generace vůči K0001: Kekule n → ⌊log2 n⌋, přípona -P +1, -C −1, -S 0."""
    head, *rest = pid.split("-")
    g = int(math.log2(int(head[1:]))) if re.fullmatch(r"K\d+", head) and int(head[1:]) > 0 else 0
    for r in rest:
        g += {"P": 1, "C": -1}.get(r[0], 0)
    return g


def finish(f: Facts, pid: str, root_birth: int | None) -> Facts:
    """Doplní odhady: rok narození z generace, „zemřel“ u narozených před 100+ lety."""
    if f.birth is None and f.child_birth:
        f.birth, f.birth_est = f.child_birth - 28, True
    if f.birth is None and root_birth:
        f.birth, f.birth_est = root_birth - GEN_YEARS * generation(pid), True
    f.dead = f.dead or f.death is not None or bool(f.birth and f.birth < TODAY_YEAR - 100)
    head, *rest = pid.split("-")
    ancestor = (re.fullmatch(r"K\d+", head) and int(head[1:]) > 1 and not any(r[0] == "C" for r in rest)) \
        or bool(rest and rest[-1][0] in "SP")
    f.married = f.married or f.marriage is not None or bool(ancestor)
    return f


def lifespan(birth: int | None, death: int | None) -> tuple[int | None, int | None]:
    if birth is None:
        return None, death
    return birth, death if death else min(birth + 80, TODAY_YEAR)


def alive_at_census(y: int, f: Facts) -> bool:
    """Žil v rozhodný den sčítání? Rok narození / úmrtí = rok sčítání rozhoduje den; úmrtí bez dne → nežil."""
    day = CENSUS_DAY.get(y, (12, 31))
    if f.death == y and (f.death_md is None or f.death_md < day):
        return False
    if f.birth == y and not f.birth_est and f.birth_md and f.birth_md > day:
        return False
    return True


# ---------------------------------------------------------------- výběr a vyhodnocení

def applicable(facts: Facts, tier: str | None = None) -> list[Item]:
    start, end = lifespan(facts.birth, facts.death)
    out = []
    for it in ITEMS:
        if tier and it.tier != tier:
            continue
        if it.when == "male" and facts.male is False:
            continue
        if it.when == "married" and not facts.married:
            continue
        if it.when == "dead" and not facts.dead:
            continue
        if start is not None and (it.start or it.end):
            lo, hi = it.start or -10_000, it.end or 10_000
            s, e = (start + 18, start + 22) if it.key == "kmenovy" else (start, end)   # kmenový list: odvod
            if it.key.startswith("scitani"):
                s = start                                                          # sčítá se i novorozenec
            if e < lo or s > hi:
                continue
            if it.key.startswith("scitani") and not alive_at_census(lo, facts):
                continue
        out.append(it)
    return out


def auto_closed(it: Item, f: Facts) -> str | None:
    """Pramen veřejně nedostupný (lhůty matrik) → nenalezeno s důvodem, bez hledání."""
    if it.key == "n" and f.birth and f.birth > TODAY_YEAR - 100 and not f.birth_est:
        return "mladší 100 let — jen rodný list / matriční úřad"
    if it.key == "o" and f.marriage and f.marriage > TODAY_YEAR - 75:
        return "mladší 75 let — jen oddací list / matriční úřad"
    if it.key == "z" and f.death and f.death > TODAY_YEAR - 75:
        return "mladší 75 let — jen úmrtní list / matriční úřad"
    return None


def auto_found(it: Item, f: Facts) -> str | None:
    if it.key == "rodice":
        return "otec i matka ve stromu" if all(f.parents) else None
    return f.found.get(it.key)


@dataclass
class Entry:
    item: Item
    state: str
    note: str = ""
    auto: bool = False


def evaluate(facts: Facts, marks: dict[str, tuple[str, str]], tier: str | None = None) -> list[Entry]:
    """Položky osoby se stavem: Gramps (nalezeno) > ruční značka > lhůta > neprohledáno."""
    out = []
    items = applicable(facts, tier)
    # ruční nález u položky, která podle (odhadnutých) let nepadá, nezahazovat
    extra = {it.key for it in ITEMS if (marks.get(it.key) or ("",))[0] == NALEZENO and (not tier or it.tier == tier)}
    items += [it for it in ITEMS if it.key in extra and it not in items]
    items.sort(key=ITEMS.index)
    for it in items:
        mark, note = marks.get(it.key, (NEPROHLEDANO, ""))
        found = auto_found(it, facts)
        if found and mark == NALEZENO and note:
            out.append(Entry(it, NALEZENO, note))                         # ruční doklad má přednost
        elif found:                                                       # ruční poznámka zůstane za „·“
            out.append(Entry(it, NALEZENO, found + (f" · {note}" if note else ""), auto=True))
        elif mark != NEPROHLEDANO:
            out.append(Entry(it, mark, note))
        elif (why := auto_closed(it, facts)):
            out.append(Entry(it, NENALEZENO, why, auto=True))
        else:
            out.append(Entry(it, NEPROHLEDANO, ""))
    return out


# „[-] … nehledáno“ není negativní nález — pramen existuje, jen se do něj nepodívalo
NOT_SEARCHED = re.compile(r"nehledán|neprohledán|neprocház|neprošl|nečten", re.I)


def closed(e: Entry, has_zavora: bool) -> bool:
    """Položka uzavřená pro fázi I: nalezeno, nebo nenalezeno s důvodem, který neříká „nehledáno“."""
    if e.state == NALEZENO:
        return True
    return e.state == NENALEZENO and bool(e.note or has_zavora) and not NOT_SEARCHED.search(e.note)


def phase1_done(entries: list[Entry], has_zavora: bool) -> bool:
    """Fáze I uzavřena: každá základní položka nalezena, nebo nenalezena s důvodem (na řádku či závora)."""
    base = [e for e in entries if e.item.tier == ZAKLADNI]
    return bool(base) and all(closed(e, has_zavora) for e in base)


def summary(entries: list[Entry]) -> dict:
    out = {}
    for tier in (ZAKLADNI, ROZSIRENY):
        es = [e for e in entries if e.item.tier == tier]
        out[tier] = {s: sum(e.state == s for e in es) for s in (NALEZENO, NENALEZENO, NEPROHLEDANO)}
    return out


# ---------------------------------------------------------------- dossier: sekce Checklist

MARK_RE = re.compile(r"^\s*- \[(.)\]\s*(.*)$")
KEY_RE = re.compile(r"^([a-z_0-9]+):\s*(.*)$")


def _legacy_key(text: str) -> tuple[str | None, str]:
    """Starý řádek bez klíče (`narození / křest — matrika N — …`) → (klíč, zbytek po štítku)."""
    best, blen = None, 0
    for it in ITEMS:
        for lab in (it.label, *it.aliases):
            ok = text.startswith(lab) and (len(text) == len(lab) or text[len(lab)] in " —(")
            if ok and len(lab) > blen:
                best, blen = it, len(lab)
    if not best:
        return None, text
    rest = text[blen:].strip()
    # starý šablonový text („— matrika N — online jen …“) není důvod — zahodit
    for tmpl in (" — matrika N", " — matrika O", " — matrika Z", "— matrika N", "— matrika O", "— matrika Z",
                 "— online jen starší 100 let", "— online jen starší 75 let", "— ověřuje vazbu na rodiče",
                 "— kontrola rodiny, č. p., kmotrů", "— jen držitel usedlosti", "— jen pobyt v Praze",
                 "— odvodní věk", "— dítě školního věku", "— jen při podezření na emigraci"):
        rest = rest.replace(tmpl.strip(), "").strip()
    rest = re.sub(r"^(—\s*)+", "", rest).strip()
    return best.key, rest


OTHER = "_jine"     # řádky mimo šablonu (vlastní položky sessions) — zachovají se doslova


def parse_marks(section_text: str) -> dict:
    """Sekce Checklist → {klíč: (stav, poznámka)}, {OTHER: [řádky]}; přijímá nový (`- [x] n: …`) i starý formát."""
    out: dict = {OTHER: []}
    for ln in section_text.splitlines():
        m = MARK_RE.match(ln)
        if not m:
            continue
        mark, text = m.group(1), m.group(2).strip()
        mark = LEGACY.get(mark, mark if mark in (NALEZENO, NENALEZENO) else NEPROHLEDANO)
        km = KEY_RE.match(text)
        if km and km.group(1) in BY_KEY:
            key = km.group(1)
            note = km.group(2)
            label = BY_KEY[key].label
            note = note[len(label):].strip() if note.startswith(label) else note
            note = re.sub(r"^—\s*", "", note).strip()
            hint = f"({BY_KEY[key].hint})"
            if BY_KEY[key].hint and note.startswith(hint):   # výchozí nápověda není důvod
                note = re.sub(r"^—\s*", "", note[len(hint):].strip()).strip()
        else:
            key, note = _legacy_key(text)
            if not key:
                out[OTHER].append(ln.strip())
                continue
        if note.startswith("auto:"):          # automatický doklad se při syncu obnoví z Gramps; ruční zbytek za „·“
            _, _, note = note.partition(" · ")
            if mark == NALEZENO:
                mark = NEPROHLEDANO
        prev = out.get(key)
        if prev is None or (prev[0] == NEPROHLEDANO and mark != NEPROHLEDANO):
            out[key] = (mark, note)
        elif mark != NEPROHLEDANO:            # druhý řádek téže položky (2. sňatek…) — zachovat doslova
            out[OTHER].append(ln.strip())
    return out


LEGEND = ("`[ ]` neprohledáno · `[x]` nalezeno · `[-]` nenalezeno (prohledáno, co šlo — důvod na řádku nebo "
          "závora). `[x]` z Gramps se doplní samo (`auto:`). Generuje `tools/research/checklist_sync.py` — "
          "měň jen značku a text za pomlčkou.")


def render(entries: list[Entry], facts: Facts, other: list[str] = ()) -> str:
    lines = [LEGEND, ""]
    if facts.birth_est:
        lines += [f"*Rok narození odhadem ({facts.birth}, z dětí / generace) — položky se upřesní s datem.*", ""]
    for tier in (ZAKLADNI, ROZSIRENY):
        es = [e for e in entries if e.item.tier == tier]
        if not es:
            continue
        lines += [f"### {tier.capitalize()}", ""]
        for e in es:
            note = e.note
            if e.auto and e.state == NALEZENO:
                note = f"auto: {note}"
            elif e.auto and e.state == NENALEZENO:
                note = f"{note}"
            tail = f" — {note}" if note else (f" ({e.item.hint})" if e.item.hint else "")
            lines.append(f"- [{e.state}] {e.item.key}: {e.item.label}{tail}")
        lines.append("")
    if other:
        lines += ["### Jiné (mimo šablonu)", "", *other, ""]
    return "\n".join(lines).rstrip() + "\n"
