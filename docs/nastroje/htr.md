# Lokální HTR bez LLM — stav testu

**Stav (2026-10-17): rozpracováno, pozastaveno** (limit účtu). Zadání: [`ZADANI-htr-lokalne.md`](ZADANI-htr-lokalne.md).

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
- `~/.cache/genealogy-workbench/htr-test/` a `htr-models/` jsou prázdné. Žádná testovací strana nestažena.
- MCP `czech-archives`: `register_info` s `module=ebadatelna_praha` a ID z URL eBadatelny (3480, 238, 1612) vrátilo
  „Error executing tool“ — ID archiválie asi není `register_id`; zjistit přes `find_registers` / `search_registers_live`.
  Zdroje: Kouty školní kronika (archivalieId 3480, 120 snímků), Liteň kronika 1914–1940 (238, 96 snímků),
  Žiželice pamětní kniha 1752–1848 (1612, 212 snímků).

## Předání

Hotov jen průzkum kroků 1–2 (část). Dále: (1) dořešit `register_id` a stáhnout 5+5+3 strany do `htr-test/`;
(2) doinstalovat kraken, stáhnout Baránkův model a McCATMuS, zapsat licence, změřit čas/stranu na CPU;
(3) ruční reference ~20 řádků a CER/WER + nález jmen a letopočtů; (4) případně `tools/htr/`; (5) doplnit tento dokument.
Nic necommitnuto.
