# Co patří do Gramps a co do workbenche

Rozhoduje, **o čem data jsou**: Gramps drží *strom* (osoby a fakty s citacemi), workbench drží *proces*
(co hledám, co jsem zkoušel, co je rozpracované).

| Gramps (master stromu) | Workbench — `genealogy-trees/<strom>/` |
|---|---|
| osoby, rodiny, události, které považuji za **pravděpodobné nebo jisté** | otázky (`research/questions/`) |
| každý fakt **s citací a jistotou** (0 velmi nízká … 4 velmi vysoká) | hypotézy, kandidátní osoby, „možná je to tentýž Jan“ |
| zdroje a citace, odkaz na snímek | log hledání vč. negativních výsledků (`research/log.md`) |
| štítky stavu: `neověřeno`, `rozpracováno`, `ověřeno` | přepisy a extrahovaná data (`transcriptions/`) |
| média (fotky, dokumenty) | snímky pramenů se sidecar citací (`sources/`) |
| | nápovědy z MyHeritage, cizích stromů, fór (`research/hints/`) |
| | rozbory rozporů a důkazů k osobám (`research/people/<ID>.md`) |
| | navržené změny (`patches/`) |

## Pravidla přechodu

- **Rodinné vazby** (rodiče, partneři, děti, sourozenci), které uživatel zná, se zakládají hned — jsou vždy
  správně. Citace: zdroj „Ústní sdělení — <badatel>“, jistota 3.

- **Osoba se v Gramps zakládá, jakmile o ní mluvíme** (otevře se její session) — jen jméno a pohlaví,
  Gramps ID = ID workbenche (`K0001`, `K0001-S1`), atributy `workbench ID` a `MyHeritage _UID`.
  Skript `tools/gramps/ensure_persons.py`; volá ho `tools/sessions/open_person.sh` automaticky.
- **Jakékoli další údaje** (události, místa, vazby, fotky) až po ověření — přes patch.

- **Hypotéza ani nápověda do Gramps nesmí**, dokud nemá aspoň jeden pramen. Spekulativní vazby by se
  propsaly do exportů a grafik.
- Data převzatá z MyHeritage, která už ve stromu jsou, zůstávají — s citací „cizí strom MyHeritage
  (autor)“ a jistotou 0–1 a štítkem `neověřeno`. Ověřování je postupně povýší.
- Změny jdou přes **patch** (`patches/P-<nnn>.yml`): osoba, změna, citace, jistota, odkaz na přepis.
  Stav `navrženo → schváleno → aplikováno`.

## Stupně jistoty citace (Gramps)

| Stupeň | Kdy |
|---|---|
| 4 velmi vysoká | primární záznam, přímo o události, zapsaný v době události (matrika N u křtu) |
| 3 vysoká | primární záznam, údaj nepřímý nebo pozdější (věk v úmrtním záznamu → rok narození) |
| 2 normální | odvozený pramen (index, druhopis, sčítání s údaji z paměti) |
| 3 vysoká | **přímé ústní sdělení uživatele** (badatel z `genealogy.toml`) — bere se jako pravdivé; doklad pak povýší na 4 |
| 1 nízká | ústní tradice z doslechu, rodinná paměť třetích osob, sekundární literatura bez odkazu |
| 0 velmi nízká | cizí strom bez pramene, Smart Match |

## Checklist osoby

Neudržuje se ručně — generuje se z citací v Gramps × šablona podle období. Viz
[`checklist-osoby.md`](checklist-osoby.md). Ručně se do `research/people/<ID>.md` píšou jen výjimky
(„sčítání 1869 pro obec nedochováno“).
