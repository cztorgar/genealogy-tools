# Playbook: kontroly (otázky na uživatele)

**Kdy:** neshoda čtení klíčového pole, dva kandidáti na totožnost, rozpor mezi prameny, chyba nástroje.
Rozhodnutí patří uživateli. Ty připravíš podklad.
**Formát:** [`docs/metodika/autonomie.md`](../metodika/autonomie.md) § 5.

## Založení

1. Soubor `research/kontroly/<ID>-<nn>.yml` (u obecné věci `G-<nn>.yml`), číslování navazuje.
2. `otazka` musí být rozhodnutelná jedním výběrem. `kontext` má 2–5 vět: proč na tom záleží, co už víme.
3. `varianty` se svou oporou (kdo co přečetl, který údaj sedí), `doporuceni` s důvodem.
4. `snimek` a `vyrez` jako cesta do `sources/<ID>/` stromu, ne do cache. `url` na portál.
5. `blokuje: true`, jen když na tom stojí další postup (totožnost, klíčové jméno).
6. Než založíš novou, **zkontroluj rozhodnuté kontroly** osoby. Uživatelovo rozhodnutí platí a nenavrhuj
   proti němu.

## Zapracování rozhodnutí

Uživatel rozhoduje v dashboardu (Kontroly) → `stav: rozhodnuto`, `rozhodnuti: {volba, poznamka}`.
Promítni to **novým patchem** (`update_citation`, `update_event`, rodina) a vyplň
`zapracovano: {patch, kdy}`, `stav: zapracováno`.
Varianta „nerozhodnutelné“ = závora (typ nejistá totožnost), ne fakt.
