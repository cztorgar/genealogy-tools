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
- `htr-models/` zatím prázdné.

## Testovací data (vyřešeno 2026-10-17)

Modul `ebadatelna_praha` rozšířen o archiválie (`archivalie_info`, `fetch_archivalie_page`; prohlížeč `/a/<ID>/<snímek>`).
Staženo 13 stran do `~/.cache/genealogy-workbench/htr-test/` (se sidecary `.yml`):
`kouty/` snímky 10, 30, 60, 90, 110 (archivalieId 3480); `liten/` 6, 20, 40, 60, 85 (238); `ziz/` 20, 60, 120 (1612).

## Předání

Hotov jen průzkum kroků 1–2 (část). Dále: (1) hotovo (13 stran staženo);
(2) doinstalovat kraken, stáhnout Baránkův model a McCATMuS, zapsat licence, změřit čas/stranu na CPU;
(3) ruční reference ~20 řádků a CER/WER + nález jmen a letopočtů; (4) případně `tools/htr/`; (5) doplnit tento dokument.
Nic necommitnuto.
