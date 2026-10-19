# Checklist osoby

Checklist říká, **co by se u osoby mělo dát ověřit**, podle doby, kdy žila. Je **dynamický**: šablona
(`tools/research/checklist.py`, seznam `ITEMS`) × údaje osoby (Gramps → dossier → odhad z dětí / generace) →
seznam položek. Dossier drží jen ruční stavy; `tools/research/checklist_sync.py` sekci `## Checklist` přepíše podle
aktuální šablony (manager po dávkách). Dashboard počítá živě.

## Dvě úrovně

- **Základní** — fáze I výzkumu ([`faze-vyzkumu.md`](faze-vyzkumu.md)); z ní se počítá postup (pruh v dashboardu)
  a zelená barva.
- **Rozšířený** — všechno ostatní (katastry, vojsko, hroby, tisk…); fáze II, do zelené se nepočítá.

## Stav položky

| značka | stav | kdy |
|---|---|---|
| `[ ]` | neprohledáno | ještě se nehledalo |
| `[x]` | nalezeno | doloženo pramenem; **doplní se samo** (`auto:`), má-li osoba v Gramps odpovídající událost s citací |
| `[-]` | nenalezeno | prohledáno vše, co šlo — **platný výsledek**, pokud má důvod: text za pomlčkou na řádku, nebo sekce `## Závora` |

Lhůty matrik (N mladší 100 let, O a Z mladší 75 let) dávají `[-]` automaticky s důvodem „jen doklad / matriční úřad“.
Starý formát se převádí: `[~]` slabý pramen → nalezeno (jistota je v citaci), `[n]` neexistuje → nenalezeno.

Řádek v dossieru: `- [-] z: úmrtí / pohřeb — Z Vrbice 1785–1813 prohledáno, nenalezeno (log 2026-10-18)`.
Klíč (`z:`) a štítek generuje sync — **měň jen značku a text za pomlčkou**.

## Základní checklist

| klíč | položka | kdy se nabízí | automaticky `[x]` |
|---|---|---|---|
| `n` | narození / křest | vždy | událost Birth / Baptism / Christening s citací |
| `rodice` | rodiče | vždy — jména z N/O → osoby ve stromu, jinak závora | otec i matka v Gramps |
| `o` | sňatek | ženatí / vdané (předci, manželé) | Marriage v rodině s citací |
| `z` | úmrtí / pohřeb | zemřelí (nebo narození před 100+ lety) | Death / Burial s citací |
| `scitaniRRRR` | sčítání lidu 1857, 1869, 1880, 1890, 1900, 1910, 1921 | žil v daném roce | Census s citací v daném roce |

Sčítání se nabízí, jen když osoba v **rozhodný den** žila (1857: 31. 10., 1921: 15. 2., ostatní 31. 12.). Kdo
zemřel v roce sčítání před tímto dnem (nebo bez známého dne), nebo se narodil po něm, sčítání nemá. Neznámé
úmrtí se bere jako narození + 80 let. Proto i nepřímé úmrtí patří do Gramps jako událost Death s datem
`BEF` / `BET … AND …` (např. „† otce“ v zápisu dítěte). Sčítání po tomto datu pak zmizí samo, a nemusí se psát
`[-] … nežil`.

Sčítání se pro obec často nedochovalo (zejm. 1857, 1880 a uherská 1880–1910) → `[-]` s důvodem „nedochováno pro
obec X (ARON / SOkA …)“. Jednou zjištěná nedochovanost platí pro všechny z té obce a roku.

## Rozšířený checklist

| Položka | Kdy se nabízí |
|---|---|
| sňatek rodičů — matrika O | vždy (ověřuje vazbu na rodiče) |
| narození sourozenců | vždy (kontrola rodiny, č. p., kmotrů) |
| soupis poddaných 1651 | žil kolem 1651 |
| berní rula 1654 (Čechy) / lánové rejstříky (Morava) | držitel usedlosti kolem 1654 |
| tereziánský / josefský / stabilní katastr | držitel usedlosti 1748–1757 / 1785–1789 / 1824–1843 |
| pozemková / gruntovní kniha | držitel usedlosti (16.–20. st.) |
| policejní přihláška Praha | pobyt v Praze 1850–1914 |
| vojenský kmenový list (VÚA) | muž, odvodní věk v 19. st. – 1918 |
| Verlustlisten / legionáři | muž, 1914–1920 |
| padlí 2. sv. v. / odboj / holocaust.cz | 1938–1945 |
| domovský list / domovská obec | 1863–1948 |
| školní matriky / katalogy | dítě v 19.–20. st. |
| hrob, parte, noviny (Kramerius) | 19.–20. st. |
| vystěhování (lodní seznamy) | podezření na emigraci |
| rodinné doklady | narození po 1880 |

## Přidání položky

Jeden řádek v `ITEMS` (`tools/research/checklist.py`): klíč, štítek, úroveň (`ZAKLADNI` / `ROZSIRENY`), období,
podmínka (`married`, `dead`, `male`, `situational`), nápověda. Má-li jít doložit z Gramps, doplnit pravidlo do
`gramps_facts.py` (`KEY_OF_TYPE`). Pak `checklist_sync.py <strom>` — položka se objeví u všech, koho se týká,
a osoby, které ji nemají uzavřenou, přestanou být zelené. Doplnit tabulku výše.
