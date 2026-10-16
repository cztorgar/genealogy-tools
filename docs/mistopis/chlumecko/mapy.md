# Chlumecko — historické mapy

Rešerše 2026-10-16. Jen místopis, bez osob. Zasazení osob do map patří ke stromu, návrh je v oddílu 4.
Jistota: **doloženo** · **pravděpodobně** · **neověřeno** · **nenalezeno**.

Souřadnice (WGS84) a kódy dnešních katastrálních území (KÚ, RÚIAN) má každá obec v [obce.md](obce.md)
a strojově v `mcp/czech-archives/gazetteer/chlumecko.yml` (oddíl `places`).

## 1. Stabilní katastr — císařské povinné otisky (1:2880)

- **Kde:** Ústřední archiv zeměměřictví a katastru (ČÚZK), aplikace **https://ags.cuzk.gov.cz/archiv/**.
  Stará adresa `archivnimapy.cuzk.cz` končí na 404. **Doloženo.**
- **Datace:** otisky pro Čechy pocházejí z let 1826–1843 (metadata
  https://geoportal.gov.cz/php/micka/record/basic/CZ-CUZK-COC-R). Pro Chlumecko lze čekat kolem roku
  1840 — **neověřeno**.
- **Konkrétní listy (signatura, rok) pro Chlumec, Lučice, Kladruby, Žiželice a další obce:
  nenalezeno.** Bez prohlížeče to nejde:
  - mapové služby `ags.cuzk.gov.cz/arcgis4/rest/services/Archiv/*` chtějí token aplikace;
  - digitální badatelna ÚAZK má anti-bot ochranu, kterou jsem neobcházel.
- **Postup ručně:**
  1. Otevřít aplikaci a vyhledat název KÚ (vyhledávání nad RÚIAN, tvar „název (kód)“).
  2. Zapnout vrstvu *Císařské otisky*.
  3. Kliknout do obce funkcí „hledání bodem“.
  4. Karty listů ukážou datum (`cio_DAT_OD`), signaturu (`cio_SIGN`, `cio_SIGN_INV`) a území.
     Objednací kód listu má tvar `NNNN-NNN` (číslo mapy, číslo listu). **Doloženo** z kódu aplikace,
     hodnoty jsem nevyplňoval.
  5. Rok a signaturu zapsat do tabulky níže a do `chlumecko.yml`.
- **Pozor:** katastrální obec ze 40. let 19. stol. se nemusí krýt s dnešním KÚ. Kladruby dnes leží
  v KÚ Chlumec nad Cidlinou (651800), tehdy mohly mít vlastní katastrální obec — **neověřeno**.
- **Licence:** dataset je poskytován podle zákona 645/2004 (e-shop ČÚZK, produkt 63811). Prohlížení
  je volné, převzetí rastrů pro vlastní web je třeba ověřit. **Pravděpodobně.**

| KÚ (dnes) | kód | rok otisku | signatura / list | pozn. |
|---|---|---|---|---|
| Chlumec nad Cidlinou | 651800 | ? | ? | vč. Kladrub |
| Lučice u Chlumce nad Cidlinou | 688291 | ? | ? | „Lučice“ 688282 je jiná obec |
| Pamětník | 717533 | ? | ? | |
| Žiželice nad Cidlinou | 797481 | ? | ? | |
| … ostatní viz [obce.md](obce.md) | | | | doplnit ručně |

## 2. Vojenská mapování

| Mapa | Služba | Stav 2026-10-16 | Podmínky |
|---|---|---|---|
| **II. vojenské (Františkovo) mapování** 1836–1852, 1:28 800 | WMTS CENIA: `https://gis.cenia.cz/mapcache/II_vojenske_mapovani/wmts?SERVICE=WMTS&REQUEST=GetCapabilities` | **funguje** (GetCapabilities 200). Jediná matice `jtsk:epsg:5514` (S-JTSK), dlaždice 512 px, úrovně 0–12 | metadata CENIA „bez omezení“. **Doloženo:** https://micka.cenia.cz/en/record/full/4e678953-ba1c-49a2-a61e-3b96c0a80137 |
| **III. vojenské mapování** 1876–1880, 1:25 000 | WMTS CENIA: `https://gis.cenia.cz/mapcache/III_vojenske_mapovani/wmts?SERVICE=WMTS&REQUEST=GetCapabilities` | **funguje**, stejná struktura | **pravděpodobně** totéž |
| II. VM — starý WMS geoportal.gov.cz | `…/cenia_rt_II_vojenske_mapovani/MapServer/WMSServer` | **404**, zrušeno | — |
| oldmaps.geolab.cz (UJEP), mapire.eu (Arcanum) | prohlížení | netestováno | licence **neověřena**; dlaždice Arcanum obvykle nejsou volně k vkládání |
| Historické ortofoto ČÚZK (od 1950) | `https://geoportal.cuzk.gov.cz/WMS_ORTOFOTO_ARCHIV/WMService.aspx` | netestováno | neověřeno |

Číslo sekce II. VM a listu III. VM pro Chlumec: **nenalezeno**. Zjistit ho jde v oldmaps.geolab.cz
(vyhledání podle místa).

## 3. Stabilní katastr ↔ čísla popisná

Matriky a sčítání (viz [ostatni-prameny.md](ostatni-prameny.md)) uvádějí **číslo popisné**. Na
otisku čp. obvykle nejsou, jsou tam čísla parcel a stavební parcely jsou číslované zvlášť.
**Pravděpodobně.** Propojení:

1. Z matriky nebo sčítání vzít obec a čp. Pozor na přečíslování domů a na rozdíl mezi matriční
   osadou a katastrální obcí.
2. Najít čp. ve **stavební parcele**:
   - **indikační skica** (NA), kde stavební parcely často nesou čp.;
   - nebo **parcelní protokol** s **abecedním seznamem držitelů** (držitel → čp. → parcela).
3. Najít parcelu na georeferencovaném otisku a vzít její souřadnice (bod domu).
4. Domy postavené po 1840 doplnit podle sčítání 1869–1921 (po čp.) a III. vojenského mapování.

## 4. Návrh pro managera: osoby v historické mapě

Tohle je mimo místopis (pracuje se s daty stromu), proto jen návrh:

- **Data:**
  - každé místo v Gramps (strom `berescak`) dostane souřadnice z `gazetteer/chlumecko.yml`
    (úroveň obec a osada);
  - kde je známé čp., přidat „dům“ jako podřízené místo (`Chlumec n. C. čp. 53`) se souřadnicemi
    podle bodu 3.
- **Vrstva:** statická webová mapa (Leaflet) ve stromu, ne ve workbenchi:
  - podklad III. a II. vojenského mapování z WMTS CENIA; ten je jen v S-JTSK (EPSG:5514), takže
    je potřeba **Proj4Leaflet**;
  - nad podkladem body osob a rodů (událost N/O/Z, rok, čp.) s filtrem podle osoby, rodu a roku.
- **Soukromí:** žijící osoby jen v neveřejné verzi (CLAUDE.md, oddíl Soukromí).
- **Předpoklad:** ručně doplnit rok a list císařského otisku pro KÚ, kde rod žil (tabulka v oddílu 1).
