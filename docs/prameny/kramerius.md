# Kramerius (CDK) — fulltextové hledání v tištěných pramenech

Ověřeno 2026-10-17 (test na jedné větvi; ~80 dotazů po 1,5 s).

- Endpoint: `https://api.ceskadigitalniknihovna.cz/search/api/client/v7.0/search` (Kramerius 7, agreguje NDK, krajské knihovny).
- `q` musí mít pole: `q=text_ocr:"Novák Lučice"~10` (proximity). Holé `q=Novak` → 400. **Diakritika se ignoruje, skloňování ne** → vyjmenovat tvary (Novák, Nováka, Novákova, Nováková…).
- Filtry: `fq=accessibility:public`, `fq=model:page`, `fq=date_range_start.year:[1880 TO 1935]`, `fq=root.pid:"uuid:…"` (jeden titul).
- Úryvky: `hl=true&hl.fl=text_ocr&hl.fragsize=120&hl.snippets=2` (víc server nevrátí).
- OCR stránky: `GET /search/api/client/v7.0/items/<pid>/ocr/text` — **bez** hlavičky `Accept: application/json` (jinak 406).
- Šum: obce = obecná slova (Kolesa, Vápno, Lhotka, Tůně), stejnojmenné obce, proximity spojuje sousední hesla v seznamech.
  Po 1945 veřejného tisku málo (DNNT jen po přihlášení).
- Kvalita OCR: adresáře a úřední věstníky 1900–1935 dobré; staré noviny a německé tisky horší.
- Výsledek = **nápověda** (jistota 0), ověřit proti matrice; zapisovat dotazy i „nenalezeno“ do `research/log.md`.
- Plánovaný modul `kramerius` v `mcp/czech-archives`: `search`, `page_text`, `in_work`, `plan` (dotazy z dossieru: příjmení × obec × okno let).
