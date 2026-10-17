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
- `title.search` (hledání **titulů**) je naopak citlivé na diakritiku i skloňování: `Adresář Prahy` ano, `adresar Praha` nic. Slova v dotazu se spojují (AND).
- Odpověď stránky nese: `pid`, `root.pid`, `root.title`, `date.str`, `title.search` (= označení strany, např. „134“), `rels_ext_index.sort` (pořadí strany v titulu). Zobrazení: `https://ceskadigitalniknihovna.cz/view/<pid>`.
- Úryvky jsou v `highlighting["<root.pid>!<pid>"].text_ocr`, hledané výrazy v `<em>`.

## Modul `kramerius` v MCP czech-archives (hotovo 2026-10-18)

Soubor `mcp/czech-archives/czech_archives/modules/kramerius.py`, tooly `kramerius_search`, `kramerius_page_text`,
`kramerius_titles`, `kramerius_plan` (popis v `mcp/czech-archives/README.md`).

- Rozestup ≥ 1,5 s mezi dotazy (sdílený zámek mezi procesy), cache odpovědí 3 týdny, max 40 tvarů v dotazu, max 50 řádků.
- `plan` jen generuje: tvary příjmení × obce, okno od 18 let do úmrtí (jinak +60 let, nejvýše 1950), tituly z `digitalizovane/*.csv`
  (`sken+ocr`, veřejné). Obec nikdy samotná; u šumových obcí a zkrácených názvů (Chlumec nad Cidlinou → „Chlumec“) proximity 5.
- Známá omezení: ženské příjmení → jen ženské tvary (mužskou podobu nejde spolehlivě odvodit); místní pády obcí
  („v Lučicích“) se negenerují, jen základní tvar; výjimky ve skloňování (Havel, Němec) jsou ošetřeny jen základně.
- Ukázkový šum z testu: seznamy členů spolků a zpravodajů, kde proximity spojí sousední hesla (`Jan Novák … Lnáře … Lučice`).
