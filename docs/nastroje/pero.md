# PERO OCR — klient webové aplikace

**Stav (2026-10-16): odloženo.** Klient je hotový a přihlášení, vytvoření dokumentu, upload, layout analýza
i spuštění OCR na živém webu fungují. OCR ale v den testu **nedoběhlo**: dokument zůstal ve stavu
„Running OCR.“ (sdílená fronta demo aplikace). Srovnání s ověřenými přepisy proto zatím chybí — viz [Test](#test).

PERO OCR (FIT VUT Brno, https://pero-ocr.fit.vutbr.cz/) je nezávislé čtení rukopisu pro `reader` /
`skills/read-record` — jiný typ chyb než LLM (nenormalizuje jména, nevymýšlí, ale plete znaky).

## Podmínky užití

- „The application is free for personal use and any use which involves manual text correction.“
  Workbench = osobní genealogie s ruční kontrolou → v pořádku.
- Nahrané snímky zůstávají na VUT a **mohou být použity k trénování** jejich modelů.
- Při publikaci výsledků uvést autory (Kodym & Hradiš 2021; Kišš, Beneš & Hradiš 2021; Kohút & Hradiš 2021).
- Hromadné zpracování → jejich REST API (testovací klíč na vyžádání u M. Hradiše), ne webová aplikace.

## Jak to funguje

Webová aplikace je open source (`DCGM/pero_ocr_web`, Flask). Klient `tools/reader/pero_web.py` jde stejnou
cestou jako UI:

| krok | požadavek | pozn. |
|---|---|---|
| login | `GET /` → `csrf_token` z formuláře; `POST /auth/login` (email, password, csrf_token) | ověření: `GET /document/user_documents` vrací JSON |
| dokument | `GET/POST /document/new_document` (`document_name` + CSRF) | redirect na `upload_images_to_document/<id>` |
| upload | `POST /document/upload_image_to_document/<id>`, multipart `file` | 409 = duplicitní snímek |
| layout | `GET /layout_analysis/select_layout/<id>` → `POST /layout_analysis/start_layout/<id>` (`layout_detector_id`) | |
| OCR | `GET /ocr/select_ocr/<id>` → `POST /ocr/start_ocr/<id>` (`ocr_id`, `language_model_id`) | jen ve stavu „Layout analysis completed.“ |
| stav | `GET /document/user_documents` → `state` | New → Waiting/Running layout → Layout analysis completed. → Waiting/Running OCR → OCR completed. |
| export | `GET /document/get_document_image_ids/<id>`, pak na snímek `get_page_xml_lines/<img>`, `get_text/<img>` (příp. `get_alto_xml/<img>`, `/ocr/get_lines/<img>` s confidence po znacích) | |
| úklid | `GET /document/delete_document/<id>` | |

Bez CAPTCHA a jiné ochrany proti robotům (k 2026-10-16). Klient by se při 403/429/CAPTCHA zastavil.

### Enginy (k 2026-10-16)

- **Layout:** *Complex printed and handwritten layout* (výchozí webu i klienta; varování: „may fail on handwritten
  tables where text lines cross table boundaries“ — přesně matriky), *Handwritten layout* (dopisy, deníky),
  *Whole Page Region*, *NONE*, experimentální varianta.
- **OCR pro matriky:** *Czech Handwritten* (výchozí klienta; „also in Kurrent script“, nejlépe čitelné texty 20. st.),
  *Czech Handwritten Adaptive*, **Kurrent (German, Czech)**, *Kurrent (visual transcription style)*,
  *Universal Transformer*. Který je na kurentové matriky 19. st. nejlepší, zatím neověřeno — kandidát č. 1 je
  *Kurrent (German, Czech)*.
- **Jazykový model:** pro rukopis `NONE` (k dispozici jen Lidové noviny, angličtina, němčina, arabština).

Přehled vypíše `pero_web.py engines`.

### Lokální běh

Není možný pro rukopis: balík `pero-ocr` zveřejňuje jen model pro tisk (české noviny). Rukopisné modely
nejsou ke stažení („contact the authors“); webová aplikace je vydává jen interním workerům.

## Použití

```bash
uv run tools/reader/pero_web.py ocr snimek.jpg [--engine "Kurrent (German, Czech)"] [--crop x,y,w,h] [--out DIR]
uv run tools/reader/pero_web.py ocr snimek.jpg --document <id>   # navázat na rozběhnutý dokument
uv run tools/reader/pero_web.py documents | engines | delete <id>
```

Výstupy (vstup pro `tools/reader/compare.py`):

- `<snímek>.pero.xml` — PAGE XML: regiony, řádky (polygon, baseline), `TextEquiv/@conf` řádku
  (15% kvantil znakových confidence). U `--crop` jsou souřadnice posunuté zpět do původního snímku.
- `<snímek>.pero.txt` — jeden řádek = jeden textový řádek, za tabulátorem confidence (0–1).
- `<snímek>.pero.json` — metadata běhu (enginy, dokument, crop) + řádky s bbox.

Přístupy: `~/.config/pero/credentials` (`email=`, `password=`, 600), cookie v `~/.config/pero/session.json` (600).
Šetrnost: 2 s mezi požadavky, stav po 15 s, timeout 30 min, opakování GET po výpadku spojení,
jeden dokument `workbench-<datum>-<id>` na běh, po exportu smazán. Nedokončený běh dokument ponechá a vypíše,
jak navázat.

## Test

Plán: N 1882 (fol. 14), N 1848 (fol. 63), N 1846 (fol. 47) — srovnat jména, data, č. p. s ověřenými přepisy,
pro *Czech Handwritten* a *Kurrent (German, Czech)*, s výřezem zápisu (`--crop`) i bez.

Výsledek 2026-10-16: N 1882 — layout ✓, OCR spuštěno, po ~desítkách minut stále „Running OCR.“, pak výpadek
spojení (opraveno v klientu). Srovnání: **zatím žádné**.

## Doporučení pro reader

Zatím PERO do `read-record` nezařazovat jako povinné — volitelný třetí hlas, když server odpovídá. Až bude test:
použít s `--crop` na jednotlivý zápis (tabulka přes celou dvojstranu layout rozbíjí) a vyhodnotit, zda se
vyplatí *Kurrent* oproti *Czech Handwritten*. Pro spolehlivý provoz zvážit žádost o testovací API klíč.
