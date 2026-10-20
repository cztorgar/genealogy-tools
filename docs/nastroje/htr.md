# Lokální HTR bez LLM — stav testu

**Stav (2026-10-17): rozpracováno, pozastaveno** (limit účtu).

## Zjištěno zatím

- **PERO lokálně:** README `DCGM/pero-ocr` (ověřeno 2026-10-17) nabízí ke stažení jen layout (tisk + rukopis) a tiskový OCR
  model pro české noviny (nextcloud.fit.vutbr.cz/s/NtAbHTNkZFpapdJ). Releases i Packages na GitHubu prázdné; pro rukopis/fraktur
  „contact the authors“. Kurrent se nezmiňuje. → rukopisné modely lokálně **stále nejsou veřejné**; zbývá REST API
  (pero-ocr.fit.vutbr.cz/api, klíč od M. Hradiše). Nezkoumáno: HTR-United / projekty „Kroniky“, SemANT.
- **Kraken – kandidáti (z vyhledávání, nestaženo, licence neověřena):**
  - „Kraken HTR recognition model, Bohemian provenance 19th century“ (D. Baránek, Zenodo 10.5281/zenodo.11673242, 2024;
    ≈62 000 řádků, hlavně německé židovské matriky) — kandidát na kurent/němčinu 19. st.
  - „HTR model for German manuscripts trained from several datasets“ (Zenodo 7933463).
  - McCATMuS (Zenodo 13788177, 16.–21. st., hlavně francouzština); PP-OCRv6 pro kraken (Zenodo 21788405, i medieval Czech).
  - Pro češtinu 20. st. latinkou zatím nic konkrétního nenalezeno.
- Nezmapováno: TrOCR, PyLaia, Loghi, Transkribus (ceny/modely).

## Stav prostředí

- `~/.cache/genealogy-workbench/htr-venv/.venv` (Python 3.11 přes uv); instalace `kraken` byla při pauze přerušena —
  zkontrolovat/zopakovat `uv pip install kraken`.
- `htr-models/` zatím prázdné.

## Testovací data (vyřešeno 2026-10-17)

Modul `ebadatelna_praha` rozšířen o archiválie (`archivalie_info`, `fetch_archivalie_page`; prohlížeč `/a/<ID>/<snímek>`).
Staženo 13 stran do `~/.cache/genealogy-workbench/htr-test/` (se sidecary `.yml`):
`kouty/` snímky 10, 30, 60, 90, 110 (archivalieId 3480); `liten/` 6, 20, 40, 60, 85 (238); `ziz/` 20, 60, 120 (1612).

## Testovací sada `evals/htr/` (2026-10-17)

- `evals/htr/manifest.yml` — 19 výřezů z archiválií (latinka20: Kouty, Liteň, Horčápsko, Chraštice = 12; kurent19: Úmyslovice = 4,
  **písmo u snímků 45 a 60 ověřit** — z náhledu to vypadá spíš na latinku; kurent18: Žiželice = 3) + 4 matrikové výřezy ze stromu
  (jen odkaz na soubor ve stromu; přepis uživatelem ověřený je prokazatelně jen u `mat-K0112-1815`, u ostatních hlavička
  souboru říká draft / rozhodnuto uživatelem).
- Snímky jsou v `~/.cache/genealogy-workbench/htr-test/{kouty,liten,horcapsko,chrastice,umyslovice,ziz}/`, výřezy se
  generují `uv run tools/htr/eval.py prepare` do `htr-test/crops/<id>.jpg` (souřadnice `vyrez: [x,y,w,h]` v manifestu).
- `evals/htr/ref/` — **referenční přepisy a klíčové tokeny zatím chybí** (zadá Opus session, formát v `ref/README.md`).
- `tools/htr/eval.py score <dir> --tool NAME [--md FILE]` — CER/WER a recall klíčových tokenů po skupinách; ověřeno na
  syntetických datech (bez referencí se položka přeskočí).

## Výsledky měření: Kraken 7.1.1 na CPU (2026-10-17)

Sada `evals/htr/` (19 výřezů archiválií; ref. přepisy od Opus session), segmentace výchozím `segment -bl`, bez úprav obrazu.
Modely (obojí CC-BY-4.0, v `~/.cache/genealogy-workbench/htr-models/`):
`rec_bohemica.mlmodel` (D. Baránek, Zenodo 10.5281/zenodo.11673242; 19. st., převážně německé židovské matriky; 62 000 řádků) a
`McCATMuS_nfd_nofix_V1.mlmodel` (Zenodo 10.5281/zenodo.13788177; 16.–21. st., 7 jazyků, bez češtiny).

| model | skupina | výřezů | CER | recall přesně | recall ±1 | jména | příjmení | letopočty |
|---|---|---|---|---|---|---|---|---|
| rec_bohemica | latinka20 | 12 | 57,3 % | 7,6 % | 14,4 % | 1/29 | 0/34 | 5/13 |
| rec_bohemica | latinka19 | 2 | 66,2 % | 9,1 % | 9,1 % | 0/2 | 0/1 | 1/2 |
| rec_bohemica | kurent19 | 2 | 65,4 % | 28,6 % | 28,6 % | 0/1 | 0/1 | 2/2 |
| rec_bohemica | kurent18 | 3 | 86,7 % | 0 % | 0 % | 0/2 | 0/1 | 0/3 |
| rec_bohemica | **celkem** | 19 | 63,7 % | 8,2 % | 13,7 % | 1/34 | 0/37 | 8/20 |
| McCATMuS | latinka20 | 12 | 47,0 % | 13,6 % | 23,7 % | 5/29 | 3/34 | 3/13 |
| McCATMuS | latinka19 | 2 | 51,5 % | 18,2 % | 36,4 % | 0/2 | 0/1 | 1/2 |
| McCATMuS | kurent19 | 2 | 68,1 % | 42,9 % | 42,9 % | 0/1 | 0/1 | 2/2 |
| McCATMuS | kurent18 | 3 | 96,3 % | 0 % | 0 % | 0/2 | 0/1 | 0/3 |
| McCATMuS | **celkem** | 19 | 57,2 % | 14,4 % | 24,0 % | 5/34 | 3/37 | 6/20 |

(Matrikové výřezy `mat-*` neměřeny — chybí jim ref. `.txt`. U `ziz-0060` a `ziz-0120` je reference jen částečná → CER orientační;
skupiny kurent19/latinka19 mají 2 výřezy, čísla jsou jen indikativní.)

**Rychlost** (14 jader, bez GPU): 86 s (rec_bohemica) / 116 s (McCATMuS) na výřez = půlka dvoustrany, 12–25 řádků.
Vlastní rozpoznání je ~5 s, zbytek je segmentace `blla` a načtení modelů v každém spuštění. Celá dvoustrana v jednom běhu
neměřena; hrubý odhad pro ≈1 100 stran je desítky hodin (přes noc na několik nocí), šlo by zrychlit segmentací jednou a
jedním procesem na dávku.

**Závěr:** žádný z veřejně dostupných Kraken modelů **není použitelný pro hledání příjmení** v těchto kronikách: příjmení se
našla ve 0 % (rec_bohemica) a 8 % (McCATMuS) případů, jména ≤ 17 %. Lepší je McCATMuS; na kurent 18. století (Žiželice)
oba modely selhaly úplně. Letopočty vycházejí lépe (30–40 %), ale na vyhledávání nestačí. Kvalita závisí na písmu: nejlépe
čitelná latinka 20. st., nejhůř kurent.

**Nezmapováno / další kroky:** PERO přes REST API (klíč u M. Hradiše) nebo web (viz `pero.md`) — rukopisné modely PERO jsou podle
všeho jediný, co by mohl být použitelný; TrOCR, PyLaia, Loghi a Transkribus (ceny, modely na kurent) nezkoumány;
doladění Krakenu (`ketos`) na vlastních referencích by bylo vlastní projekt (potřeba stovky ručně přepsaných řádků).

## Předání

Hotovo: kroky 1 (PERO lokálně — rukopisné modely nejsou veřejné), část 2 (Kraken, 2 modely změřeny), 3, 4 (na sadě `evals/htr/`).
Kraken venv: `~/.cache/genealogy-workbench/htr-venv/.venv` (CPU torch; instalace bez `--extra-index-url …/whl/cpu` visela, s ním doběhla
za pár minut). Výstupy měření v adresáři scratchpadu session (nejsou trvalé). Nezbývá: `tools/htr/htr.py` (nedělal jsem — žádný
model nestojí za nástroj), zmapování PERO API / TrOCR / PyLaia / Loghi / Transkribus. Nic necommitnuto.
