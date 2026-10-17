# Přepis pramenů

Každý přepsaný záznam = `transcriptions/<id>.md` + `transcriptions/<id>.json` ve stromu.

## Čtyři vrstvy (nikdy nemíchat)

1. **Doslovný přepis** — přesně jak je napsáno, včetně pravopisu, zkratek a chyb. Značky (jednotně pro Claude, OpenAI
   i ruční přepis — porovnání čtení na nich stojí):

   | značka | význam |
|---|---|
   | `[?]` | nečitelné slovo / znaky (`Wa[?]lav` = část slova) |
   | `[Wáclaw?]` | nejisté čtení jedné varianty |
   | `[Jan/Jiří?]` | dvě (víc) možná čtení, nerozhodnuto |
   | `[…]` | doplněno přepisovatelem (zkratka, chybějící písmeno) |
   | `{^Vávra^}` | vpisek nad řádkem / dodatečně vepsáno |
   | `[přeškrtnuto: Wáclaw]` | přeškrtnutý text (pokud čitelný; jinak `[přeškrtnuto: ?]`) |
   | `[okraj: …]` | přípisek na okraji / v jiné rubrice |
   | `[jiná ruka: …]` | zápis jinou rukou nebo inkoustem (pozdější přípisek) |
   | `[vybledlé: …]`, `[poškozeno]` | čitelnost omezená stavem listu |

   Nejistotu nikdy neskrývat normalizací — nejisté místo zůstane označené i v `raw`.
2. **Normalizace** — rozvedené zkratky, dnešní pravopis jmen a míst.
3. **Překlad** — z latiny / němčiny do češtiny.
4. **Interpretace** — co z toho plyne pro strom (kdo je kdo, vazby). Jen tady je místo pro úvahy.

## Strukturovaná data (`.json`)

Pole podle typu matriky (rubriky jozefínských matrik od 1784): datum narození / křtu, č. p., jméno,
náboženství, pohlaví, manželské / nemanželské, otec (jméno, povolání, původ, rodiče), matka (totéž),
kmotři, porodní bába, křtitel, poznámky. Každé pole má `value`, `raw` (doslovně) a `confidence`.

## Reader (obrázek → text)

- Běží **paralelně více backendů** (Claude + OpenAI; volitelně PERO OCR jako třetí hlas s jiným typem
  chyb) a porovnává se **po polích**.
- Shoda → `confidence: high`, přesto jména a data kontroluje člověk proti výřezu snímku.
- Neshoda → pole označené `needs_review` s oběma čteními.
- Známé chyby LLM: „normalizují“ jména na běžnější tvar, vynechávají řádky, vymýšlejí věrohodná data,
  špatně čtou vpisky na okraji. Pozor na tabulkové matriky — model může přiřadit údaj do špatného řádku.
- Kvalita se měří na `evals/` (ručně přepsané stránky) při každé změně promptu nebo modelu.

### Použití v osobní session ([`tools/reader/`](../../tools/reader/README.md))

1. Session zápis přepíše sama (`.md` + `.json`) — to je první čtení.
2. Druhé čtení: `tools/reader/openai_read.py read <snímek> --type N|O|Z|scitani|doklad --crop x,y,w,h
   [--hint "obec, rok, osoba"] --out sources/<ID>/<zápis>.openai.json` — přednostně s výřezem zápisu
   (zkontrolovat `--dry-run`); hint jen k nalezení zápisu na stránce.
3. `tools/reader/compare.py --claude <zápis>.json --openai <zápis>.openai.json [--pero <snímek>.pero.txt]
   --out sources/<ID>/<zápis>.compare` → tabulka `.compare.md` + `.compare.json` s `needs_review`.
4. Pole `needs_review` (✗, ≈, ∅, ⚠) ověřit proti výřezu a výsledek promítnout do vlastního přepisu.
   Čtení OpenAI je jen kontrolní hlas — do stromu se nepřebírá. Cena a měření:
   [`docs/nastroje/reader.md`](../nastroje/reader.md).
