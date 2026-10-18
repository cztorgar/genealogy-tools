# Fáze výzkumu

## Fáze I — každá osoba zpracovaná

Cíl: **projít všechny osoby stromu** (přímé předky, manžele i zmínky — sourozence, děti, kmotry s dossierem) tak,
že každá má **celý základní checklist uzavřený** ([`checklist-osoby.md`](checklist-osoby.md)):

- položka **nalezena** (doloženo pramenem, zapsáno v Gramps), nebo
- **nenalezena** s důvodem — prohledáno vše, co šlo (řádek checklistu nebo `## Závora`: kde se hledalo, proč to dál
  nejde, co by závoru prolomilo).

Negativní výsledek s doloženým hledáním je **platný konec** fáze I. Zmínky často skončí jen se závorami — i tak jsou
zpracované.

Výsledkem je u každé osoby: **rodiče ve stromu, nebo závora** proč ne — strom tak buď roste o generaci, nebo má
zdokumentovaný konec.

### Zelená = uzavřeno

Dashboard ukáže osobu zeleně (stav **uzavřeno**, počítá se, do dossieru se nepíše), když:

1. každá položka základního checklistu je `[x]`, nebo `[-]` s důvodem / závorou,
2. na osobě nikdo nepracuje (`stav` ≠ `rozpracováno`),
3. nečeká žádný její patch (`navrženo` / `schváleno`).

Přibude-li položka do základního checklistu, osoby bez ní zelenou ztratí — tak to má být. Cíl fáze I: **celý strom
zelený**. Pruh v boxu osoby ukazuje postup základního checklistu.

### Pořadí práce

Session větve bere osoby, které nejsou zelené: nejdřív `n` → `rodice` → `o` → `z` (posouvají strom), sčítání
podle obce najednou (jeden operát pokryje celou domácnost — u více osob naráz).

## Fáze II — rozšířený checklist

Katastry, pozemkové knihy, vojenské záznamy, hroby, tisk, sourozenci — až po fázi I, podle zájmu (příběhy, knihy).
