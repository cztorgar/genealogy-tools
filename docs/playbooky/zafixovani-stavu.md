# Playbook: zafixování stavu

**Kdy:** před velkou změnou (hromadná úprava, nová metodika), na konci týdne, na pokyn uživatele.
Gramps Web je master. Bez exportu jeho obsah v gitu není.

## Kroky

1. Dávka managera ([`manager.md`](manager.md)): nic nečeká, syncy proběhly, stavy srovnané (žádné osiřelé
   `rozpracováno`).
2. `uv run tools/research/fronta.py` → `research/fronta.md`.
3. `uv run tools/gramps/export_snapshot.py <strom>` → `data/gramps/stav-YYYY-MM-DD.gramps`.
4. Commit repa stromu, `git tag stav-YYYY-MM-DD`, push s tagy. Případně commit workbenche.
5. Do `research/rozhodnuti-managera.md` jeden odstavec: co se zafixovalo, počty (zelených / ve frontě).

## Obnova

Snímek `.gramps` se importuje do prázdného stromu v Gramps Web (Import). Soubory stromu vrátí `git checkout stav-…`.
