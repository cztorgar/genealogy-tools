# Playbook: čtení zápisu

**Kdy:** máš snímek (matrika, sčítání, doklad) a potřebuješ z něj text a údaje.
**Podrobná verze:** [`skills/read-record/SKILL.md`](../../skills/read-record/SKILL.md) (trojí čtení Claude +
OpenAI + PERO). Pravidla: [`docs/metodika/prepis.md`](../metodika/prepis.md),
[`autonomie.md`](../metodika/autonomie.md) (pravidla R).

## Kroky

1. **Výřez.** Na stránce bývá víc zápisů. Najdi ten správný (číslo domu, jméno, datum) a ulož výřez vedle
   snímku `<snímek>.crop-<n>.jpg`. Čti **celý snímek i výřez**, u klíčových polí (jména, data, č. p.) ještě užší výřez.
2. **Přečti nezávisle.** Doslovně, nic nenormalizuj, nečitelné `[?]`, nejisté `[Jan?]`. Rubriky podle typu
   zápisu (`docs/prameny/`).
3. **Druhé čtení**, je-li dostupné a povolené: `tools/reader/openai_read.py`, PERO (`tools/reader/pero_web.py`).   
4. **Porovnej po polích** (`tools/reader/compare.py`). Shoda = kandidát na jistotu 2. Neshoda klíčového pole =
   kontrola typu `cteni` ([`kontroly.md`](kontroly.md)) s výřezem a všemi čteními.
5. **Přepis** do `transcriptions/<ID>-<typ>-<rok>.md` ve čtyřech vrstvách: doslovně → normalizace → překlad
   (latina, němčina: MCP `genealogy` → `glossary`) → interpretace.

## Jistota

| čtení | jistota v citaci |
|---|---|
| jeden model | ≤ 1, poznámka „neověřeno uživatelem“ |
| dva modely se shodou | ≤ 2 |
| ověřeno uživatelem proti snímku | 3–4 podle typu pramene ([`citace.md`](../metodika/citace.md)) |

## Nesmíš

Doplňovat chybějící písmena podle očekávání („měl by to být Jan“), opravovat matrikáře, číst víc snímků najednou
v podagentech, posílat chráněné snímky do další služby.
