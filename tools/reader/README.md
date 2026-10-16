# reader — nezávislá čtení snímků a jejich porovnání

Přepis ze session (Claude) je první čtení. Tady jsou nástroje na **druhé, nezávislé čtení** přes OpenAI
(`openai_read.py`) a na **porovnání po polích** (`compare.py`), volitelně i s textem PERO OCR
(`pero_web.py` — samostatný nástroj). Metodika: [`docs/metodika/prepis.md`](../../docs/metodika/prepis.md),
měření a doporučení: [`docs/nastroje/reader.md`](../../docs/nastroje/reader.md).

Závislosti: jen Python 3 + Pillow (HTTP přes standardní knihovnu).
Klíč: `OPENAI_API_KEY`, jinak `~/.config/openai/genealogie.json` (pole `.api_key.value`, práva 600).
Klíč se nikde nevypisuje ani neukládá — nekopíruj ho do příkazů ani souborů.

## Postup v osobní session

1. **Přepiš zápis sám** (Claude) → `sources/<ID>/<zápis>.md` + `.json` jako dosud.
2. **Najdi výřez zápisu** (pixely originálu `x,y,w,h`; celá šířka dvojstrany, výška jednoho řádku
   tabulky + kousek okolí). Výřez je spolehlivější a levnější než celá stránka. Kontrola bez volání API:

   ```bash
   python3 tools/reader/openai_read.py read <snímek.jpg> --type N --crop 0,500,2000,240 \
       --dry-run --out /tmp/x.json        # uloží /tmp/x.sent.jpg — podívej se, že je tam celý zápis
   ```

   Bez výřezu použij `--hint "Žiželice 1882, Josef, otec František Vrbický, č. 224"` — nápověda slouží
   jen k nalezení zápisu na stránce (model nesmí z ní doplňovat obsah; kontroluj `umisteni`).
3. **Druhé čtení:**

   ```bash
   python3 tools/reader/openai_read.py read <snímek.jpg> --type N --crop x,y,w,h \
       --hint "obec, rok" --out ../genealogy-trees/<strom>/sources/<ID>/<zápis>.openai.json
   ```

   Typy: `N` (narození/křty), `O` (oddaní), `Z` (zemřelí), `scitani` (arch po osobách), `doklad`.
   Volby: `--model auto|<id>` (auto = nejnovější vlajkový GPT z `GET /v1/models`, teď `gpt-6.1-sol`;
   `openai_read.py models` vypíše kandidáty), `--effort low|medium|high` (výchozí medium),
   `--detail original|high` (výchozí original = bez zmenšení na straně API), `--max-side 3200`,
   `--enhance` (šedotón + autokontrast pro vybledlé snímky).
4. **Porovnej:**

   ```bash
   python3 tools/reader/compare.py --claude sources/<ID>/<zápis>.json \
       --openai sources/<ID>/<zápis>.openai.json [--pero <snímek>.pero.txt --pero-lines 40-62] \
       --out sources/<ID>/<zápis>.compare        # → .compare.md + .compare.json
   ```

   `--claude` bere JSON přepis (`pole: [{pole|rubrika, raw, value, confidence}]`), Markdown přepis
   s tabulkou rubrik nebo i jiný výstup `openai_read`. `--pero` je prostý text po řádcích;
   `--pero-lines` omezí hledání na řádky zápisu (jinak hrozí falešná shoda se sousedním zápisem).
5. **Projdi `needs_review`** a pole s ✗ / ≈ / ⚠ ověř proti výřezu snímku. Rozhodnutí zapiš do přepisu
   (oprava čtení, `[?]`, nižší confidence) — výstup OpenAI se do stromu nepřebírá jako fakt.

## Jak číst výsledek

| značka | význam | co dělat |
|---|---|---|
| ✓✓ jisté | Claude = OpenAI a PERO text obsahuje totéž | přesto jméno a datum zkontrolovat okem |
| ✓ shoda | Claude = OpenAI (PERO chybí / nenalezeno) | běžná kontrola |
| ✓? pravděpodobné | Claude ≠ OpenAI, PERO podporuje jedno z nich; menšinové čtení je uvedeno | ověřit menšinové čtení |
| ≈ podobné | liší se drobně (písmeno, koncovka, pravopis) | **ověřit** — typicky právě jména |
| ✗ neshoda | různé čtení | **ověřit** |
| ∅ chybí | pole má jen jedno čtení | doplnit nebo ověřit, zda tam rubrika je |
| ⚠ | `[?]` v čtení nebo confidence low | ověřit |

Normalizace jen pro porovnání: diakritika, velikost písmen, staropis (w→v, ss→s, th→t), koncovky
(Novotný ~ Novotná ~ Novotného, Klicpera ~ Klicperová), zkratky s tečkou jako prefix (Frant. ~ František),
data na den/měsíc/rok, č. p. na číslo. **Shoda dvou modelů není důkaz** — oba umí jméno „znormalizovat“
stejně.

## Cena

Odhad se ukládá do výstupu (`usage.cost_usd_est`) a do `~/.cache/genealogy-workbench/reader/usage.jsonl`
(tokeny, model, snímek, výřez — bez klíče). Ceník v `openai_read.py` (`PRICES`) je odhad, ověřit na
https://developers.openai.com/api/docs/pricing. Řádově: výřez zápisu ≈ 500–1 500 obrazových dlaždic
(32×32 px) + ~4 k tokenů prompt/schéma, výstup 2–6 k tokenů včetně reasoning → u `gpt-6.1-sol`
($2 / $10 za 1M) zhruba **$0.02–0.08 za zápis**; celá dvojstrana bez výřezu ~3× víc vstupu.
Souhrn útraty: `jq -s 'map(.cost_usd_est // 0) | add' ~/.cache/genealogy-workbench/reader/usage.jsonl`.
