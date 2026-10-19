# Fronta fáze I

Jedna společná fronta osob, které ještě nejsou zelené (fáze I neuzavřená). Počítá ji
`tools/research/fronta.py`. Dashboard ji ukazuje živě v záložce **Fronta**. Snímek `research/fronta.md` stromu
přegeneruje manager po dávkách (`uv run tools/research/fronta.py <strom>`) a commitne ho.

## Pořadí

1. **Šedí**: `zmínka`, `převzato`, bez dossieru. Na osobě se ještě nezkoumalo.
2. **Nezelení**: všichni ostatní kromě `uzavřeno` (zapsáno, pozastaveno, dokončeno…). Mají otevřené
   položky základního checklistu.

Uvnitř skupiny jdou nejdřív přímí předci (Kekule K-čísla a od kotvy K0001-S2 řetězce -P1/-P2), pak vedlejší
linie. V obou se řadí podle generace od K0001 (blíž dřív), pak podle ID. Strom tak roste po úrovních.

## Co znamená „osoba prozkoumána“

Každá osoba z fronty skončí jedním ze dvou způsobů:

- **další úroveň**: rodiče z pramene jsou založení ve stromu (REQ skript + patch), nebo
- **závora**: sekce `## Závora` s platným důvodem (formát ve [`workflow-sessions.md`](workflow-sessions.md))
  **a s obtížností**.

Ostatní položky základního checklistu ([`checklist-osoby.md`](checklist-osoby.md)) se uzavřou `[x]`, nebo `[-]`
s důvodem. Pak je osoba zelená a z fronty vypadne.

## Obtížnost závory

Jak těžké je závoru prolomit, ne jak velká je šance:

| obtížnost | kdy |
|---|---|
| **nízká** | pramen je online a známý, jen se do něj ještě nepodívalo (svazek s rejstříkem, pár snímků) |
| **střední** | online jen pracně (bez rejstříku, desítky až stovky snímků, nejistá fara), nebo je potřeba dopis do archivu / matriční úřad / doklad od rodiny |
| **velká** | matriky nedochované nebo nedostupné; zbývají nepřímé prameny (pozemkové knihy, katastry, soupisy) nebo jen malá šance |

Odhady z 2026-10-19 doplnil skript `tools/research/zavory_obtiznost.py` podle textu závory. Jsou
označené „(odhad managera …)“ a session nebo uživatel je přepíše. Nová závora má obtížnost vždy od session.

Závora, jejíž „proč“ říká *nehledáno / rozpočet*, není závora. Neuzavírá osobu a ve frontě má štítek
„závora = nehledáno“.

## Zafixování stavu

Před velkou změnou nebo na konci dne udělá manager tohle:

1. aplikuje čekající patche,
2. spustí syncy (`stav_sync`, `kolapsy_graf`, `kontext_flags`, `checklist_sync`) a `fronta.py`,
3. exportuje Gramps: `uv run tools/gramps/export_snapshot.py <strom>` → `data/gramps/stav-YYYY-MM-DD.gramps`,
4. commitne strom i workbench a nad stromem vytvoří tag `stav-YYYY-MM-DD`.
