# Referenční přepisy testovací sady HTR

Pro každou položku `evals/htr/manifest.yml` (typ `archivalie`) sem patří dva soubory:

- `<id>.txt` — doslovný přepis výřezu (obrázek `<cache>/crops/<id>.jpg`, vytvoří `tools/htr/eval.py prepare`),
  ~15–20 řádků, jeden řádek textu = jeden řádek přepisu, původní pravopis; nečitelné `[?]`.
  Dělá Opus (ne Sonnet) a **přečte to jen pro test** — viz zadání.
- `<id>.json` — klíčové tokeny, podle kterých se měří recall (vyhledávání jmen a letopočtů):
  `{"tokens": [{"t": "Novák", "typ": "prijmeni"}, {"t": "1808", "typ": "letopocet"}]}`
  typ: `jmeno` | `prijmeni` | `letopocet` | `cp` | `misto`.

Matrikové výřezy (`mat-*`) mají doslovný přepis ve stromě (`prepis_ve_strome` v manifestu); pro skórování
CER/WER sem může přibýt `<id>.txt` vytažený z té tabulky, `<id>.json` s klíčovými tokeny je vhodné doplnit vždy.
Žádná osobní data stromu se sem nekopírují.
