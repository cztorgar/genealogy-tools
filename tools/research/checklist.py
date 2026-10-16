"""Šablona checklistu osoby podle období — strojová podoba docs/metodika/checklist-osoby.md.

Položka se nabídne, když se období pramene překrývá s (odhadnutým) životem osoby a sedí podmínka.
"""
from __future__ import annotations

from dataclasses import dataclass

TODAY_YEAR = 2026


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    start: int | None = None      # první rok, kdy pramen existuje
    end: int | None = None        # poslední rok
    when: str = "always"          # always | married | dead | male | situational
    note: str = ""


ITEMS = [
    Item("n", "narození / křest — matrika N", note="online jen starší 100 let"),
    Item("o_parents", "sňatek rodičů — matrika O", note="ověřuje vazbu na rodiče"),
    Item("siblings", "narození sourozenců — matrika N", note="kontrola rodiny, č. p., kmotrů"),
    Item("o", "sňatek — matrika O", when="married", note="online jen starší 75 let"),
    Item("z", "úmrtí / pohřeb — matrika Z", when="dead", note="online jen starší 75 let"),
    Item("soupis1651", "soupis poddaných podle víry 1651", 1651, 1651),
    Item("bernirula", "berní rula 1654 (Čechy) / lánové rejstříky (Morava)", 1654, 1679, "situational",
         "jen držitel usedlosti"),
    Item("terez", "tereziánský katastr", 1748, 1757, "situational", "jen držitel usedlosti"),
    Item("josef", "josefský katastr", 1785, 1789, "situational", "jen držitel usedlosti"),
    Item("stabilni", "stabilní katastr (indikační skica)", 1824, 1843, "situational", "jen držitel usedlosti"),
    Item("grunt", "pozemková / gruntovní kniha", 1550, 1950, "situational", "jen držitel usedlosti"),
    *[Item(f"scitani{y}", f"sčítání lidu {y}", y, y) for y in (1857, 1869, 1880, 1890, 1900, 1910, 1921)],
    Item("prihlasky", "policejní přihláška Praha", 1850, 1914, "situational", "jen pobyt v Praze"),
    Item("kmenovy", "vojenský kmenový list (VÚA)", 1820, 1918, "male", "odvodní věk"),
    Item("ww1", "Verlustlisten / kartotéka padlých 1. sv. v.", 1914, 1918, "male"),
    Item("legie", "legionáři (VÚA)", 1914, 1920, "male"),
    Item("ww2", "padlí 2. sv. v. / odboj / holocaust.cz", 1938, 1945),
    Item("domovske", "domovský list / domovská obec", 1863, 1948),
    Item("skola", "školní matriky / katalogy", 1800, 1990, "situational", "dítě školního věku"),
    Item("hrob", "hrob (BillionGraves, hřbitovní evidence)", 1800, None, "dead"),
    Item("tisk", "parte, noviny (Kramerius)", 1800, None, "situational"),
    Item("emigrace", "vystěhování (lodní seznamy)", 1850, 1939, "situational", "jen při podezření na emigraci"),
    Item("rodina", "rodinné doklady (rodný/oddací/úmrtní list, fotky)", 1900, None),
]


def lifespan(birth: int | None, death: int | None) -> tuple[int | None, int | None]:
    if birth is None:
        return None, death
    end = death if death else min(birth + 80, TODAY_YEAR)
    return birth, end


def applicable(birth: int | None, death: int | None, *, male: bool | None, married: bool, dead: bool):
    """Vrátí seznam (item, poznámka) položek, které dávají smysl pro danou osobu."""
    start, end = lifespan(birth, death)
    out = []
    for it in ITEMS:
        if it.when == "male" and male is False:
            continue
        if it.when == "married" and not married:
            continue
        if it.when == "dead" and not dead:
            continue
        if start is not None and (it.start or it.end):
            lo, hi = it.start or -10_000, it.end or 10_000
            # kmenový list: rozhoduje rok odvodu (~20 let), ne celý život
            s, e = (start + 18, start + 22) if it.key == "kmenovy" else (start, end)
            if e < lo or s > hi:
                continue
        note = it.note
        if it.key == "n" and birth and birth > TODAY_YEAR - 100:
            note = "mladší 100 let → rodný list / matriční úřad"
        if it.key in ("o", "z") and birth and birth > TODAY_YEAR - 75 - 20:
            note = "pravděpodobně mladší 75 let → doklad / matriční úřad"
        if it.key == "rodina" and start and start < 1880:
            continue
        out.append((it, note))
    return out
