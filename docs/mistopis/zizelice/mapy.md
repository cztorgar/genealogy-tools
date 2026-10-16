# Žiželice — historické mapy

Rešerše 2026-10-16. Katalog map pro k. ú. Žiželice a osady fary. U každé mapy je uvedeno, jestli
jsme ji **stáhli jako vrstvu** (`cache/mapy/zizelice/<vrstva>/`, nástroj
[`tools/mapy/`](../../../tools/mapy/README.md)). Jistota: **doloženo** / **pravděpodobně** /
**neověřeno**. K číslům popisným viz [cisla-popisna.md](cisla-popisna.md).

## 0. Území

| Katastrální území | Kód k. ú. | Obec (kód) | Části obce na k. ú. |
|---|---|---|---|
| **Žiželice nad Cidlinou** | 797481 | Žiželice (533947), okr. Kolín | Žiželice |
| Končice | 797448 | Žiželice | Končice, **Zbraň** |
| Hradišťko II | 797430 | Žiželice | Hradišťko II |
| Loukonosy | 797464 | Žiželice | Loukonosy, **Pod Vinicí** |
| Kundratice u Žiželic nad Cidlinou | 797456 | Žiželice | Kundratice |
| Převýšov | 735299 | Převýšov (570681), okr. Hradec Králové | Převýšov |

**Doloženo:** RÚIAN, https://ags.cuzk.gov.cz/arcgis/rest/services/RUIAN/MapServer/7 (dotaz
2026-10-16). Hranice k. ú. jsou uložené v
[`tools/mapy/oblasti/zizelice.geojson`](../../../tools/mapy/oblasti/zizelice.geojson). Obálka
stažených vrstev = hranice k. ú. + 300 m, tj. WGS84 15.3475–15.4522 E, 50.0965–50.1671 N.

**Oprava k README (kap. 5):** úřední název katastrálního území je **„Žiželice nad Cidlinou“**
(RÚIAN), takže přívlastek se úředně používá, jen u k. ú., ne u obce. **Doloženo.**

Mimo obálku zůstaly osady fary, které leží v jiných obcích (Bílé Vchynice, Hlavečník,
Radovesnice II, Rasochy, Rozehnaly, Tetov, Korce). Doplnit je jde přidáním jejich k. ú. do
geojsonu a znovuspuštěním nástroje.

---

## 1. Přehled

| Vrstva | Mapa | Rok | Měřítko / rozlišení | Čp.? Jména? | Služba | Licence | Staženo |
|---|---|---|---|---|---|---|---|
| — | I. vojenské (josefské) mapování | Čechy 1764–1768, rektifikace 1780–1783 | 1 : 28 800 | ne | jen Mapire (komerční) | Arcanum | **ne** |
| — | **Indikační skica** stabilního katastru | ~1840 | 1 : 2 880 | **čp. ano, jména držitelů ano** | NA; v aplikaci Archiv ČÚZK (token) | NA, archiválie | **ne** (viz 2.2) |
| — | **Císařský povinný otisk** stabilního katastru | 1824–1843, pro tuto oblast neověřeno | 1 : 2 880 | parcelní čísla, bez čp. | Archiv ČÚZK, `arcgis4/…/archiv_spojene_cisarske_otisky` (token) | ÚAZK, archiválie | **ne** (viz 2.1) |
| `vm2` | II. vojenské (Františkovo) mapování | 1836–1852 | 1 : 28 800; staženo 1 m/px | ne (sídla, názvy) | CENIA WMTS, S-JTSK | CENIA, bez omezení | **ano** |
| `vm3_25` | III. vojenské mapování, topografické sekce | 1874–1880 | 1 : 25 000; staženo 1,19 m/px (Merc.) | ne | Chartae Antiquae WMS, EPSG:3857 | © VÚGTK & HÚ AV ČR, licence neuvedena | **ano** |
| `vm3_75` | III. vojenské mapování, speciální mapa | 1880–1950 (vydání) | 1 : 75 000; staženo 2 m/px | ne | CENIA WMTS, S-JTSK | CENIA, bez omezení | **ano** |
| `orto1950` | Historická ortofotomapa | **1954** pro celou obálku | ~0,5 m/px | ne | CENIA WMTS, S-JTSK | CC BY 4.0 | **ano** |
| — | Archivní ortofoto ČÚZK | 1998–(roky) | ~0,5 m | ne | ČÚZK WMS | CC BY 4.0 | ne (stačí odkaz) |
| `orto_dnes` | Ortofoto ČR | aktuální | staženo 0,6 m/px (Merc., z18) | ne | ČÚZK ArcGIS `ORTOFOTO_WM` | CC BY 4.0 | **ano** |
| `km` | Katastrální mapa | aktuální | staženo 0,3 m/px (Merc., z19) | parcelní čísla, bez čp. | ČÚZK WMS KN | CC BY 4.0 | **ano** |
| — | RÚIAN adresní místa | 30. 9. 2026 | body | **čp. ano** | otevřená data VDP | CC BY 4.0 | **ano** (CSV) |

---

## 2. Stabilní katastr

### 2.1 Císařský povinný otisk (ÚAZK, ČÚZK)

- **Co to je:** barevná kopie originální mapy stabilního katastru. Měřítko 1 : 2 880, pro Čechy
  vznikaly 1824–1843. Na rozdíl od originálních map v nich **nejsou dokreslené pozdější změny**.
  Mapa obsahuje parcely s parcelními čísly (stavební a pozemkové), budovy, kultury a pomístní
  názvy. **Doloženo** (popis vrstvy v aplikaci Archiv ČÚZK, `https://ags.cuzk.gov.cz/archiv/`).
- **Rok mapování a čísla listů pro Žiželice, Končice, Hradišťko, Loukonosy, Kundratice a Převýšov
  (Neudorf): neověřeno.** Aplikace Archiv je zjistí kliknutím na místo a výběrem „Císařské
  povinné otisky“. Z příkazové řádky nejdou, protože služba vyžaduje token (viz níže).
- **Služba:** `https://ags.cuzk.gov.cz/arcgis4/rest/services/Archiv/archiv_spojene_cisarske_otisky/MapServer`
  je georeferencovaná mozaika („spojené“ listy). Vedle ní existují nespojené jednotlivé listy
  (`archiv_nespojene_stable/ImageServer`) a originální mapy SK (`archiv_spojene_originalni_mapy`).
  Všechny vracejí *499 Token Required*. Token vydává aplikace anonymně přes
  `arcgis2/…/GenerateToken`, je ale určený pro prohlížečku. **Doloženo** (JS aplikace a odpověď
  serveru 2026-10-16).
- **Licence:** archiválie ÚAZK nespadají pod otevřená data ČÚZK (CC BY 4.0 se na ně
  nevztahuje). Zveřejnění reprodukce je bezplatné a bez souhlasu, ÚAZK jen žádá citaci archivu
  a signatury, např. „B2/a/6 Císařský povinný otisk“. Skeny plného rozlišení se **prodávají
  po 25 Kč za sken** (e-shop Geoportálu ČÚZK). **Doloženo:**
  [Ceník ÚAZK](https://www.cuzk.gov.cz/Urady/Zememericky-urad/Dalsi-informace/UAZK/Cenik-UAZK.aspx),
  [Podmínky poskytování dat ČÚZK](https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx).
- **Jako vrstva:** technicky ano (MapServer s tokenem). Nestaženo, rozhodne uživatel (viz
  Otevřené otázky). Skeny z e-shopu jsou nespojené listy a musely by se georeferencovat (po
  rozích listů v systému Gusterberg nebo po identických bodech s KM).

### 2.2 Indikační skica (Národní archiv)

- **Co to je:** pracovní kopie mapy stabilního katastru. Má **čísla popisná u stavebních parcel**
  a jména držitelů (často i s čp.) a slouží k identifikaci vlastníků. Čechy ~1824–1843.
  **Pravděpodobně** (zadání, OHM wiki; konkrétní skici Žiželic jsem neviděl).
- **Uložení:** Národní archiv, sbírka indikačních skic stabilního katastru pro Čechy. Prohlížet
  jde v aplikaci Archiv ČÚZK pod nadpisem „Indikační skici“ (služba
  `archiv_nespojene_skici/ImageServer`, token). Objednávka skenu vede na NA:
  `https://digi.nacr.cz/formis/formular.php?sign=<signatura>`. **Doloženo** (JS aplikace),
  [OHM wiki: Indication Sketches](https://wiki.openstreetmap.org/wiki/OpenHistoricalMap/Projects/Indication_Sketches),
  [NA – digitální badatelna](https://www.nacr.cz/en/for-public/research-room/digital-research-room-archival-records-on-line).
- **Pro lokalizaci čp. je to klíčový pramen** (postup v [cisla-popisna.md](cisla-popisna.md#3-postup-historické-čp--poloha)).
  Signatury skic pro naše k. ú.: **neověřeno**.
- **Jako vrstva:** nespojené listy, jen obrázek. Georeferencování po identických bodech
  s císařským otiskem nebo s KM.

### 2.3 Další operáty v aplikaci Archiv ČÚZK

Podle seznamu vrstev v aplikaci (**doloženo**, JS): originální mapy SK 1 : 2 880 (s červeně
dokreslenými změnami do konce 19. století), mapa kultur ~1 : 36 000 (1837–1844, s hranicemi
dominií), výkazy ploch SK, mapy pozemkového katastru (`archiv_spojene_pk`), SMO-5
(`archiv_spojene_smo5`), Müllerova mapa Čech (1720), evidence nemovitostí 1964–1988. Pro
přečíslování čp. ve 20. století jsou užitečné **mapy pozemkového katastru a evidence nemovitostí**.
Pokrytí našich k. ú. jsem neověřoval.

---

## 3. Vojenská mapování

### 3.1 I. vojenské (josefské) mapování
- Čechy 1764–1768, 1 : 28 800. Bez souřadnicového základu, jde georeferencovat jen přibližně.
  **Pravděpodobně** (obecně známé).
- Online je na **Mapire** (Arcanum): https://mapire.eu/ . Dlaždice jsou komerční služba
  Arcanum (stránka s WMTS a ceníkem https://www.arcanum.hu/hu/mapire/wmts/ vrací 403).
  **Nestaženo**, kvůli licenci.
- Portál oldmaps.geolab.cz (UJEP), dřív s 1. až 3. mapováním, dnes přesměrovává na rozcestník
  www.geolab.cz a staré služby neodpovídají (404). **Doloženo** (2026-10-16).

### 3.2 II. vojenské (Františkovo) mapování — vrstva `vm2`
- Čechy 1836–1852, 1 : 28 800. Žiželice jsou zachycené v podobě blízké stabilnímu katastru.
- **Služba:** CENIA WMTS
  `https://gis.cenia.cz/mapcache/II_vojenske_mapovani/wmts?SERVICE=WMTS&REQUEST=GetCapabilities`.
  Vrstva `II_vojenske_mapovani`, TileMatrixSet `jtsk:epsg:5514` (512 px, počátek
  −925000/−920000, úrovně 0–12 = 1024…0,25 m/px). WMS je jen v EPSG:5514. Starší endpoint
  `geoportal.gov.cz/ArcGIS/services/CENIA/cenia_rt_II_vojenske_mapovani` vrací 404.
  **Doloženo.**
- **Licence:** metadata CENIA uvádějí *noLimitations / noConditionsApply*.
  [Záznam micka](https://micka.cenia.cz/en/record/full/4e678953-ba1c-49a2-a61e-3b96c0a80137).
  Originál je ve Vídni (Kriegsarchiv), práva na skeny **neověřeno**.
- **Staženo:** úroveň 10 (1 m/px), pro tohle měřítko mírně přezoomováno.

### 3.3 III. vojenské mapování
- **Topografické sekce 1 : 25 000 — vrstva `vm3_25`.** Čechy mapovány 1874–1880. Služba je WMS
  Chartae Antiquae (VÚGTK & HÚ AV ČR), `https://www.chartae-antiquae.cz/WMS/Military3/`,
  vrstva `Military3`, CRS včetně **EPSG:3857** a 5514. V obraze je vodoznak „VÚGTK v.v.i.“.
  Licenci stránka neuvádí, jen „© VÚGTK, v.v.i. & HÚ AV ČR, v.v.i.“, projekt NAKI.
  **Doloženo:** https://chartae-antiquae.cz/cs/maps/3military25 . Použití: osobní výzkum.
  Před publikováním se zeptat.
- **Speciální mapa 1 : 75 000 — vrstva `vm3_75`.** CENIA WMTS
  `https://gis.cenia.cz/mapcache/III_vojenske_mapovani/wmts?…`, ortorektifikovaná, stejná
  mřížka jako `vm2`. **Doloženo**,
  [micka](https://micka.cenia.cz/en/record/full/53df7ed6-c66c-4d25-8212-6966c0a80137).
- ČÚZK má sekce 1 : 25 000 i jako archiválii (dataset CZ-CUZK-TOPO75-R, vydání 1872–1953). Ty
  jsou za token nebo k zakoupení.

---

## 4. Letecké snímky a dnešní mapy

- **Historická ortofotomapa — vrstva `orto1950`.** CENIA WMTS
  `https://gis.cenia.cz/mapcache/ortofotomapa_historicka/wmts?SERVICE=WMTS&REQUEST=GetCapabilities`,
  vrstva `orto`, stejná mřížka S-JTSK. Rok snímku pro celou obálku je **1954**
  (`https://gis.cenia.cz/geoserver/ortofotomapa_historicka_roky/wms`, GetFeatureInfo
  `rok=1954` v Žiželicích i v Převýšově). Licence CC BY 4.0 (CENIA, GEODIS BRNO, MO ČR).
  **Doloženo.** Zástavba v roce 1954 je ještě skoro shodná s 19. stoletím, takže je to dobrý
  most mezi stabilním katastrem a dneškem.
- **Archivní ortofoto ČÚZK** (roky od 1998):
  `https://geoportal.cuzk.gov.cz/WMS_ORTOFOTO_ARCHIV/WMService.aspx`, vrstvy po letech.
  Nestaženo, pro genealogii má malý význam.
- **Ortofoto ČR — vrstva `orto_dnes`.** `https://ags.cuzk.gov.cz/arcgis1/rest/services/ORTOFOTO_WM/MapServer`
  (cache EPSG:3857, export). CC BY 4.0. **Doloženo.**
- **Katastrální mapa — vrstva `km`.** WMS KN `https://services.cuzk.gov.cz/wms/local-km-wms.asp`,
  vrstva `KN`, EPSG:3857 i 5514, MaxWidth 4096, *Fees none*. CC BY 4.0. **Doloženo.**
- **RÚIAN** (adresní místa, hranice k. ú.): viz [cisla-popisna.md](cisla-popisna.md).

## 5. Ostatní

- **Mapy velkostatku Chlumec nad Cidlinou** (Kinští): fond Velkostatek Chlumec n. C., SOA Zámrsk.
  Jestli obsahuje mapy a plány Žiželic: **neověřeno**.
- **Kramerius** (plány obce, pohlednice): **nehledáno**.
- Mapire má i katastrální mapy Čech z 19. století (stabilní katastr), komerčně. **Neověřeno**
  pro tuto oblast.

---

## 6. Stažené vrstvy (tools/mapy)

Všechno je v `cache/mapy/zizelice/` (mimo git, `cache/` je v `.gitignore`). Znovu se to dá
vytvořit příkazem:

```sh
.venv/bin/python tools/mapy/stahni.py zizelice            # všechny vrstvy z tools/mapy/vrstvy.yml
.venv/bin/python tools/mapy/stahni.py zizelice km --bez-stahovani   # jen přegenerovat z cache
```

Každá vrstva obsahuje:

- `src/` — surové odpovědi služby (dlaždice WMTS nebo metadlaždice WMS) v původní mřížce.
- `<vrstva>.tif` — **mozaika GeoTIFF v nativním CRS** (S-JTSK nebo Web Mercator) s přesnou
  geotransformací odvozenou z mřížky služby, RGBA, s overviews. Je to master pro QGIS.
- `xyz/{z}/{x}/{y}.webp|png` — **společná mřížka** EPSG:3857, 256 px. Všechny vrstvy se
  skládají přesně na sebe a ve webové mapě stačí `L.tileLayer('…/xyz/{z}/{x}/{y}.webp')`.
- `manifest.json` — zdroj (URL, vrstva, CRS, rozlišení, TileMatrix ověřená proti
  GetCapabilities), licence, citace, datum, obálka, geotransformace, sha256 mozaiky, počty.
- `tilejson.json` — TileJSON 3.0 pro MapLibre.

Přesnost skládání: vrstvy ze S-JTSK se převádějí do 3857 přes PROJ (výchozí transformace
S-JTSK → WGS84, ~1 m). Historické mapy samy mají chybu georeferencování v řádu metrů (SK)
až desítek metrů (vojenská mapování), a ta je o řád větší.

Staženo 2026-10-16, celkem 2,5 GB:

| Vrstva | Požadavků | Mozaika (nativní CRS) | GeoTIFF | XYZ zoom | Dlaždic | XYZ |
|---|---|---|---|---|---|---|
| `vm2` | 306 | 8704×9216 px, S-JTSK, 1 m | 107 MB | 12–17 | 2 189 | 36 MB |
| `vm3_25` | 36 | 12288×12288 px, 3857, 1,19 m | 217 MB | 12–17 | 2 189 | 19 MB |
| `vm3_75` | 90 | 4608×5120 px, S-JTSK, 2 m | 56 MB | 11–16 | 591 | 7 MB |
| `orto1950` | 1 190 | 17408×17920 px, S-JTSK, 0,5 m | 425 MB | 12–18 | 8 426 | 110 MB |
| `orto_dnes` | 121 | 22528×22528 px, 3857, 0,6 m | 1,2 GB | 12–18 | 8 426 | 93 MB |
| `km` | 420 | 40960×43008 px, 3857, 0,3 m | 43 MB | 14–17 hotovo, **z18–19 chybí** | 7 100 | 57 MB |

Generování XYZ pro `km` zastavil systém kvůli nedostatku paměti během z18. Data jsou celá
v cache, takže stačí `stahni.py zizelice km --bez-stahovani`. To dopočítá z18–19 a manifest,
nic se nestahuje.

**Kontrola skládání** (z17, náměstí Žiželic, KM + body RÚIAN přes ortofoto dnes, ortofoto
1954, II. a III. vojenské mapování): KM a body čp. lícují s oběma ortofoty na pixel. Uliční
síť ve vm2 a vm3_25 sedí s odchylkou v řádu metrů. **Doloženo** (vizuální kontrola).

---

## 7. Návrh vizualizace „kde kdo žil“

Statická stránka `web/mapa/` (Leaflet 1.9 nebo MapLibre GL), bez serveru, čte jen soubory:

1. **Podkladové vrstvy** (přepínač a průhlednost, „swipe“ pro porovnání):
   - lokálně `cache/mapy/zizelice/<vrstva>/xyz/{z}/{x}/{y}.webp`: `vm2`, `vm3_25`, `vm3_75`,
     `orto1950`, `orto_dnes`, `km` (PNG s průhledností, jako překryv);
   - online záloha: OSM `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, CENIA WMTS, ČÚZK WMS.
     Leaflet umí WMS v 3857 jen u ČÚZK (`L.tileLayer.wms`); CENIA je jen v 5514 (Proj4Leaflet),
     proto jsou její vrstvy předpočítané lokálně.
2. **Body čp.** z `mcp/czech-archives/gazetteer/zizelice-cp.csv` (popisek „Žiželice čp. 53“),
   filtr podle části obce.
3. **Vrstva osob** ze stromu: export `osoba, rok_od, rok_do, cast_obce, cp, pramen, jistota`
   z Gramps (událost *Residence* s místem „Žiželice čp. N“) nebo z `research/` stromu. Spojení
   na body přes (`cast_obce`, `cp`). Časová osa (posuvník roku) ukazuje, kdo v roce X bydlel
   v kterém čp. Barva podle linie, průhlednost podle jistoty. Data osob zůstávají ve stromu,
   stránka je načte z lokálního souboru, nic se nepublikuje.
4. **Historická poloha ≠ dnešní bod:** kde se čp. ověří proti indikační skice, uloží se
   vlastní poloha (`docs/mistopis/zizelice/cp-historicke.csv`: `cast_obce, cp, platnost_od,
   platnost_do, lat, lon, doklad, jistota`). Ta má přednost před RÚIAN.

Implementace později.

---

## Otevřené otázky

1. **Císařské otisky a indikační skici** (jediné mapy s parcelami a čp.): stahovat je přes
   anonymní token aplikace Archiv ČÚZK (georeferencovaná mozaika, ale neoficiální cesta), nebo
   koupit skeny listů (25 Kč za sken ÚAZK, skici přes NA) a georeferencovat je ručně? Napřed
   v aplikaci Archiv zjistit počet listů a signatury pro 6 k. ú.
2. Rok mapování stabilního katastru pro naše k. ú. (1839–1842?): **neověřeno**, je to v aplikaci
   Archiv u listů.
3. I. vojenské mapování: jen Mapire (komerčně). Stačí ho prohlížet online?
