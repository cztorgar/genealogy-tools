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
- **Konkrétní listy (signatura, rok):** doplněny 2026-10-17 přes prohlížeč (tabulka níže). Z příkazové
  řádky to nejde:
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
- **Pozor:** katastrální obec ze 40. let 19. stol. se nekryje s dnešním KÚ. Kladruby dnes leží
  v KÚ Chlumec nad Cidlinou (651800), roku 1841 ale patřily (i s Pamětníkem) do **k. o. Lučice**;
  Tetov a Bílé Vchynice do k. o. Kundratice — **doloženo** (tabulka níže).
- **Licence:** dataset je poskytován podle zákona 645/2004 (e-shop ČÚZK, produkt 63811). Prohlížení
  je volné, převzetí rastrů pro vlastní web je třeba ověřit. **Pravděpodobně.**

**Doplněno 2026-10-17** pro obce s adresami ve stromu (zadání místopis-adresy). Zdroj: aplikace
Archiv ČÚZK, klik do mapy na bod adresního místa RÚIAN (souřadnice z `chlumecko-cp.csv`); aplikace
při tom dotazuje vrstvu `arcgis4/rest/services/Archiv/klady/MapServer/3` (pole `cio_*`, `om_*`,
`kme_*`, `S0X`). 24 dotazů ručně/po jednom s pauzou 2,5 s. **Doloženo.**

Sloupce: **mapa** = číslo mapy SK (`AEC`); **otisk** = signatura císařského otisku (`cio_SIGN_INV`),
listy jsou `<signatura>_1` … `_n`; **originál** = originální mapa SK (`om_SIGN_NOMEN`) a rok
reambulance; **KME** = katastrální mapa evidenční (roky); **skica** = pole `S0X`, podle tvaru
(kraj BYD = Bydžovský, číslo obce, rok 1841) **pravděpodobně** signatura indikační skici v NA —
ověřit objednávkou.

| k. o. 1841 (název na otisku) | dnešní KÚ | mapa | otisk (rok, listů) | originál, reambulace | KME | skica (`S0X`) | pozn. |
|---|---|---|---|---|---|---|---|
| Chlumec n. Cidl. — *Chlumetz (Chlumec)* | Chlumec nad Cidlinou 651800 | 2525-1 | B2_a_6C_2525-1 (1841, 8) | B2_a_4C_898, 1878 | 1906–1934 | BYD064018410 | město + 3 předměstí |
| Lučice — *Lutschitz (Luczitz)* | Lučice u Chlumce n. C. 688291 | 4287-1 | B2_a_6C_4287-1 (1841, 4) | B2_a_4C_3952, 1877 | 1895–1944 | BYD243018410 | **zahrnuje Kladruby (dnes KÚ Chlumec) i Pamětník (dnes vlastní KÚ)** |
| Převýšov — *Przebeischow (Přebegssow)* | Převýšov 735299 | 6221-1 | B2_a_6C_6221-1 (1841, 4) | B2_a_4C_5836, 1873 | 1895–1939 | BYD322018410 | |
| Olešnice nad Cidlinou — *Wolleschnitz (Wollessnice)* | Olešnice n. C. 710351 | 5445-1 | B2_a_6C_5445-1 (1841, 3) | B2_a_4C_8388, 1877 | — | BYD449018410 | potvrzuje tvar „Volešnice“ |
| Levín nad Cidlinou — *Lewin* | Levín n. C. 710342 | 3900-1 | B2_a_6C_3900-1 (1841, 2) | B2_a_4C_3593, 1875 | — | BYD213018410 | |
| Písek u Chlumce n. C. — *Pisek* | Písek u Chlumce n. C. 720917 | 5780-1 | B2_a_6C_5780-1 (1841, 3) | B2_a_4C_5461, 1877 | 1877–1939 | BYD300018410 | |
| Chudeřice — *Chuderzitz* | Chudeřice 654787 | 2674-1 | B2_a_6C_2674-1 (1841, 1) | B2_a_4C_2724, 1876 | — | BYD077018410 | |
| Strašov — *Straschow (Strassow)* | Strašov 756318 | 7393-1 | B2_a_6C_7393-1 (1841, 6) | B2_a_4C_7288, 1876 | — | BYD385018410 | |
| Vápno u Přelouče — *Wapno* | Vápno u Přelouče 776955 | 8330-1 | B2_a_6C_8330-1 (1841, 2) | B2_a_4C_8038, 1875 | — | BYD419018410 | |
| Újezd u Přelouče — *Augezd* | Újezd u Přelouče 773689 | 8205-1 | B2_a_6C_8205-1 (1841, 3) | B2_a_4C_5254, 1876 | — | BYD007018410 | |
| Komárov — *Komarow* | Komárov u Přelouče 668702 | 3300-1 | B2_a_6C_3300-1 (1841, 3) | B2_a_4C_3023, 1876 | — | BYD177018410 | bod Komárov čp. 1 padá do k. o. Kolesa |
| Kolesa — *Kolles* | Kolesa 668079 | 3279-1 | B2_a_6C_3279-1 (1841, 5) | B2_a_4C_3002, 1876 | — | BYD176018410 | |
| Kundratice u Žiželic — *Kundratitz* | Kundratice 797456, **Tetov 766968, Bílé Vchynice 604143** | 3698-1 | B2_a_6C_3698-1 (1841, 5) | B2_a_4C_3375, 1876 | 1895–1949 | BYD201018410 | Tetov a Bílé Vchynice 1841 bez vlastní k. o. |
| Vlkov nad Lesy — *Wlkow* | Vlkov nad Lesy 603171 | 8703-1 | B2_a_6C_8703-1 (1841, 5) | B2_a_4C_8322, 1873 | — | BYD442018410 | 1841 v Bydžovském kraji |
| Žiželice nad Cidlinou | 797481 | ? | ? | | | | viz [zizelice/mapy.md](../zizelice/mapy.md) |
| Pamětník (dnešní KÚ 717533) | | — | — | | | | 1841 součást k. o. Lučice (viz výše) |

Datace „1826–1843, pro Chlumecko neověřeno“ výše je tím pro tyto obce **upřesněna na 1841**.
„Lučice“ 688282 v RÚIAN je jiná obec (u Chotěboře) — v tabulce je jen 688291.

**Oblasti pro `tools/mapy/stahni.py`:** `tools/mapy/oblasti/chlumecko.geojson` (Chlumec, Lučice,
Pamětník, Olešnice, Levín, Písek, Chudeřice) a `vapensko.geojson` (Strašov, Vápno, Újezd, Komárov,
Kolesa, Tetov, Bílé Vchynice) — hranice k. ú. z RÚIAN 2026-10-17. Dlaždice stažené nejsou (rozhodne
manager). Vlkov nad Lesy (jediná adresa, 7 km severně) do oblastí nezahrnut.

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
