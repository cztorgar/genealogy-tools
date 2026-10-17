---
name: read-record
description: Trojí nezávislé čtení zápisu z matriky / dokladu (Claude + OpenAI + PERO OCR) a porovnání po polích. Použij, když má session přečíst snímek zápisu, ověřit svůj přepis, nebo když uživatel řekne „přečti to všemi třemi“, „ověř čtení“, „/read-record <snímek>“.
---

# Trojí čtení zápisu

Argumenty: cesta ke snímku (`sources/<ID>/….jpg`), typ (`N` | `O` | `Z` | `scitani` | `doklad`), nápověda
(obec, rok, hledaná osoba — kterého zápisu na stránce se to týká), volitelně výřez `x,y,w,h`.
Pravidla přepisu: `docs/metodika/prepis.md`. Nástroje: `tools/reader/` (README tamtéž).

## 1. Výřez

Na stránce bývá víc zápisů. Najdi ten správný (podle nápovědy) a urči výřez `x,y,w,h` v pixelech původního
snímku — **stejný výřez pro všechna tři čtení**. Výřez ulož vedle snímku: `<snímek>.crop-<n>.jpg`
(`magick <snímek> -crop WxH+X+Y <výstup>`).

## 2. Tři čtení — nezávisle

1. **Claude** (ty): přečti výřez **bez nahlížení** do čtení ostatních → `<snímek>.claude.json`
   (rubriky podle typu, každé pole `{raw, value, confidence}`; doslovně, nic nenormalizovat, nečitelné `[?]`).
2. **OpenAI**:
   `uv run tools/reader/openai_read.py read <výřez.jpg> --type <typ> --hint "<nápověda>" --out <snímek>.openai.json`
   (klíč z `~/.config/openai/genealogie.json` — nikdy nevypisovat).
3. **PERO OCR**:
   `uv run tools/reader/pero_web.py ocr <výřez.jpg> --out <adresář>` → `<výřez>.pero.txt` (+ `.pero.xml`).
   Když PERO selže (web nedostupný), pokračuj se dvěma čteními a zapiš to.

## 3. Porovnání

`uv run tools/reader/compare.py --claude <…>.claude.json --openai <…>.openai.json --pero <…>.pero.txt --out <snímek>.compare`
→ `<snímek>.compare.md` (tabulka po polích) + `.compare.json` (`needs_review`).

| Výsledek | Význam | Co dělat |
|---|---|---|
| 3/3 shoda | jisté | do přepisu, `confidence: high` |
| 2/3 | pravděpodobné | do přepisu s menšinovým čtením v poznámce; ukázat uživateli |
| 1/1/1, chybí | sporné | `needs_review` — ukázat uživateli výřez + všechna čtení, rozhodne on |

Pozor: shoda všech tří u **jmen** není důkaz — modely umí jméno „normalizovat“ stejně. Jména a data vždy
nech uživatele potvrdit proti výřezu — **v autonomním režimu** místo toho platí pravidla R1–R8 z
`docs/metodika/autonomie.md`: neshoda klíčového pole → rozhodčí čtení (`--model gpt-5.5 --effort medium`),
pak kontext jiného pramene, a teprve pak kontrola `cteni` do `research/kontroly/`.

**Hint nesmí obsahovat čtené jméno ani datum** (jen obec, rok, č. p., který řádek) — jinak OpenAI jméno
„přečte“ z nápovědy a shoda nic neznamená.

## 4. Výstup pro uživatele

Krátká tabulka: pole · Claude · OpenAI · PERO · výsledek; pod ní sporná pole s odkazem na výřez.
Po rozhodnutí uživatele: finální přepis do `<snímek>.md` + `.json` (4 vrstvy dle `prepis.md`), u polí
uveď zdroj čtení a rozhodnutí. Cenu volání OpenAI hlásí reader (`~/.cache/genealogy-workbench/reader/usage.jsonl`).

Stav nástrojů (2026-10-16): `openai_read.py` a `compare.py` **hotové** (výchozí `gpt-6.1-sol`, effort low,
≈ 0,04–0,05 USD/výřez). **PERO odloženo** (rozhodnutí uživatele): klient `pero_web.py` je hotový, ale OCR ve sdílené
frontě webu nedoběhlo a rukopisné modely nejsou pro lokální běh veřejné — **krok 2.3 zatím vynech** a porovnávej
dvě čtení (Claude + OpenAI). Viz `docs/nastroje/pero.md`.
