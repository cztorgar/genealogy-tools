# Reader — druhé čtení přes OpenAI a porovnání po polích

Nástroje: [`tools/reader/`](../../tools/reader/README.md) — `openai_read.py` (čtení snímku modelem
s viděním do strukturovaného JSON po rubrikách), `compare.py` (porovnání 2–3 čtení: Claude, OpenAI,
volitelně text PERO OCR).

## Jak to funguje

- **Model:** `--model auto` vybere z `GET /v1/models` nejnovější vlajkový GPT (bez mini/nano/pro/codex…;
  u řady 6.x varianta `-sol`). Ke dni 2026-10-16 → `gpt-6.1-sol`. Seznam se cachuje na den.
  Název skutečně použitého modelu (z odpovědi API) je ve výstupu.
- **Volání:** Responses API, `input_image` s `detail: original` (API obrázek nezmenšuje), structured
  outputs (`json_schema`, `strict`) podle typu záznamu: N / O / Z / scitani / doklad. Každé pole
  `{raw, value, confidence}`; osoby `{jmeno, povolani_stav, bydliste}`; kmotři / svědci jako seznam.
  Navíc `zapis_nalezen`, `umisteni`, `nejista_mista`. `store: false`.
- **Prompt:** doslovné čtení (zachovat w/ss/koncovky), nenormalizovat jména v `raw`, nečitelné `[?]`,
  nevymýšlet, nebrat údaje ze sousedních řádků tabulky; `value` = normalizace pro stroj (ISO datum,
  číslo domu, dnešní pravopis — ale ne jiné jméno). Nápověda `--hint` jen k nalezení zápisu.
- **Obrázek:** výřez `--crop x,y,w,h` (pixely originálu), zmenšení na delší stranu 3200 px (výřez
  řádku dvojstrany pak má ~350–450 px výšky — písmo zůstává čitelné, viz `--dry-run`), JPEG q90,
  volitelně `--enhance`.
- **Spotřeba:** tokeny (vč. reasoning) a odhad ceny → výstup + `~/.cache/genealogy-workbench/reader/usage.jsonl`.
- **Porovnání:** viz README (značky ✓✓ / ✓ / ✓? / ≈ / ✗ / ∅, `needs_review`). PERO nemá strukturu
  polí — čtení Claude i OpenAI se v jeho textu hledají fuzzy; rozhodne 2/3.

## Měření (2026-10-16)

**Neproběhlo — OpenAI účet nemá kredit.** První skutečné volání `POST /v1/responses` vrátilo
`429 insufficient_quota` („You have no credits remaining“). Spotřebováno: 1× `GET /v1/models`
(zdarma), 1× odmítnuté čtení (bez útraty). Kód je odladěný offline: schémata prošla kontrolou pravidel
strict structured outputs, výřezy jsou připravené a zkontrolované (`--dry-run`), `compare.py` je
otestovaný na ověřených přepisech (JSON × MD téhož zápisu: N 1882 6/6, N 1910 6/6 klíčových polí)
a na umělém výstupu ve formátu `openai_read` + umělém textu PERO (ověřena logika 2/3, menšinové čtení,
`needs_review`).

### Připravený test (spustit po dobití kreditu, 4–8 volání)

Výřezy (celá šířka dvojstrany, jeden řádek tabulky):

| zápis | snímek | `--crop` | ověřený přepis pro `--claude` |
|---|---|---|---|
| N 1882 | `sources/K0028/N-1882-zizelice17-s14.jpg` | `0,500,2000,240` | `N-1882-zizelice17-s14.json` |
| N 1848 | `sources/K0056/10056_0066.jpg` | `0,560,3300,450` | `N-1848-zizelice04-f63.md` |
| N 1846 | `sources/K0057/10056_0050.jpg` | `0,1090,3300,360` | `N-1846-zizelice04-f47.md` |
| N 1910 | `sources/K0014/N-1910-zizelice26-s32.jpg` | `0,500,4110,450` | `N-1910-zizelice26-s32.json` |

Pro každý: 1× s výřezem, 1× celá stránka s `--hint` (obec, rok, hledaná osoba) → porovnat, zda
model najde správný řádek a o kolik se zhorší čtení. Klíčová pole: jméno dítěte, datum narození,
č. p., otec, matka, kmotři. Výsledky zapsat sem ve tvaru bez jmen, např.
„zápis N 1882 (výřez): jméno ✓, datum ✓, č. p. ✓, otec ✓, matka ✓, kmotři ≈ — $0.03“.

| zápis | výřez | celá stránka + hint | cena / snímek |
|---|---|---|---|
| N 1882 | — | — | — |
| N 1848 | — | — | — |
| N 1846 | — | — | — |
| N 1910 | — | — | — |

## Cena (odhad bez měření)

Ceník `gpt-6.1-sol` dle veřejných zdrojů $2 vstup / $10 výstup za 1M tokenů (oficiálně neověřeno —
v `PRICES` v `openai_read.py`). Výřez řádku: ~500–1 400 dlaždic 32×32 + prompt a schéma ~4 k tokenů;
výstup se strukturou N ~2–3 k + reasoning (medium) ~1–3 k → **≈ $0.02–0.08 za zápis**. Celá
dvojstrana (3300×2352 → 3200×2281, ~7 200 dlaždic) ≈ +$0.015 vstupu navíc. Levná varianta
`--model gpt-6-luna` (~20× levnější) — kvalitu na kurentu ověřit stejným testem.

## Doporučení

- Používat **s výřezem** zápisu; celou stránku s `--hint` jen když výřez nejde určit (a hlídat
  `umisteni` — riziko přečtení sousedního zápisu).
- Druhé čtení pouštět u zápisů, ze kterých jde do stromu jméno / datum / vazba (N, O, Z předků),
  ne u každého prohledávaného snímku.
- `compare.py` → ověřit okem všechna pole `needs_review`; ✓ neznamená ověřeno.
- Po dobití kreditu doplnit tabulku měření výše a podle výsledku rozhodnout výchozí model a effort.

## Test modelů (session K0056, 2026-10-16)

| Model / effort | Cena na výřez | Kvalita na kurentu (žiželické matriky 1846–1882) |
|---|---|---|
| `gpt-6.1-sol`, effort **low** | ≈ 0,04–0,05 USD | dobrá — **výchozí volba** |
| `gpt-5.5`, effort medium | ≈ 0,25 USD | dobrá, ale drahé (většina tokenů na reasoning) |
| `gpt-5.1`, `gpt-4.1`, `gpt-4.1-mini` | o 1–2 centy levnější | pletou jména a data — nepoužívat |

Obecně: OpenAI na kurentu občas vymýšlí jména (Wejmola, Skorvindová…) — jako kontrolní hlas je užitečné
(odhalilo záměnu ohlášky a sňatku), jako jediný zdroj ne.
