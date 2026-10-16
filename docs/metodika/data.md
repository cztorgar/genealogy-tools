# Data a datace

- **Formát GEDCOM / Gramps:** `3 MAY 1853`, `ABT 1853`, `BEF 1860`, `AFT 1850`, `BET 1850 AND 1855`,
  `EST 1853` (odhad výpočtem).
- **Křest ≠ narození.** Pokud pramen uvádí jen křest, zapisuje se událost *Křest*, ne *Narození*.
  Narození lze doplnit jako `BEF <datum křtu>` nebo `ABT` se zdůvodněním.
- **Rok narození z věku** = rozsah: věk 60 při úmrtí 1890 → `BET 1829 AND 1830`; u starých lidí a
  odhadovaných věků rozšířit (`EST 1830`, rozsah ± 5 let v poznámce). Nástroj: `birth_year_from_age`.
- **Kalendář:** v českých zemích gregoriánský od roku 1584; juliánský se objevuje jen výjimečně
  (pravoslavní, cizina). Pro přepočty a data podle svátků („na sv. Václava“) `convert_calendar`
  a `feast_date` z `igormel81/genealogy-mcp`.
- Datum v textu matriky bývá slovy, podle svátků nebo latinsky (`die 3tia Maji`) — v přepisu
  doslovně, v datech normalizovaně.
