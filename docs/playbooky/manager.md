# Playbook: manager

**Kdy:** session nebo uživatel ohlásí hotový patch nebo žádost o založení osob; průběžně po dávkách práce;
na konci dne.
**Role:** jediný, kdo zapisuje do Gramps, zakládá osoby a rodiny, commituje a mění workbench.
Podrobně: [`docs/metodika/workflow-sessions.md`](../metodika/workflow-sessions.md).

## Dávka

1. **Najdi čekající práci:** `grep -l "^status: *\(navrženo\|schváleno\)" <strom>/patches/*.yml` a skripty
   `patches/REQ-*.sh` (žádosti session o založení osob).
2. **Zkontroluj REQ skript** (jen `add_person.py`, `ensure_persons.py`, `ensure_family.py`; ID dávají smysl;
   rodina má citovaný pramen) a spusť ho z kořene workbenche. **REQ vždy před patchi**, které na nové osoby odkazují.
3. **Zkontroluj patch:** osoby a rodiny existují; citace mají sidecar a URL; jistota odpovídá čtení
   (jen Claude ≤ 1); popis je o osobě, kontext v `context`; nic neodporuje rozhodnuté kontrole.
4. **Aplikuj:** `uv run tools/gramps/apply_patch.py <strom> patches/P-<ID>-<nn>.yml --approve`.
   Selže-li, patch neupravuj ručně v Gramps. Vrať ho session s chybou, nebo napiš opravný patch.
5. **Syncy** (pořadí na tom nezáleží, všechny jsou opakovatelné):
   ```sh
   uv run tools/research/stav_sync.py          # dokončeno + vše aplikováno → zapsáno
   uv run tools/research/checklist_sync.py <strom>
   uv run tools/research/kontext_flags.py
   uv run tools/research/kolapsy_graf.py       # zhroucení předků (společní předci ve dvou liniích)
   uv run tools/research/fronta.py             # snímek fronty research/fronta.md
   ```
6. **Zásah zapiš** do `research/rozhodnuti-managera.md`: zamítnutý patch, vazba podle I0, oprava dat.
   Chybu v metodice nebo nástroji zapiš do `docs/metodika/review.md`.
7. **Commit** repa stromu (a workbenche, pokud se měnil), případně push.

## Další povinnosti

- **Konzistence stavů:** `rozpracováno` smí mít jen osoba, na které právě někdo pracuje. Osiřelé stavy srovnej
  (→ `pozastaveno`).
- **Zamítnutí patche:** `status: zamítnuto` + `zamitnuto: {kdy, proc}`; důvod pošli session.
- **Rozhodnuté kontroly** bez zapracování: zapracuj je novým patchem, nebo je předej session osoby.
- **Další práce:** podle fronty (dashboard → Fronta). Otevři osobu nebo větev, jednu session na každou.

## Nesmíš

Schvalovat to, co patří uživateli (kontroly, totožnost, odeslání dopisů); upravovat aplikovaný patch;
zapisovat fakta mimo patch; mazat data bez zálohy.

## Hotovo, když

Žádný patch nečeká, syncy proběhly, `research/fronta.md` je čerstvá, deník je doplněný a změny jsou commitnuté.
