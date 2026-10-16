# SOA Zámrsk / SOA v Hradci Králové — ARchiv ONline (ARON)

Portál: <https://aron.vychodoceskearchivy.cz/> · nápověda: <https://soahradec.gov.cz/napoveda-archivu-online/>
Modul MCP: `aron_zamrsk` ([`mcp/czech-archives`](../../mcp/czech-archives/README.md)).
Průzkum: 16. 10. 2026. Značení: **[ověřeno]** = vyzkoušeno požadavkem, **[z kódu]** = vyčteno z JS
bundlu portálu, nevyzkoušeno; **[neověřeno]** = domněnka.

> Archiv se dnes jmenuje **Státní oblastní archiv v Hradci Králové**; matriky spravuje jeho
> **Archivní oddělení Zámrsk**. Portál i citace generované portálem uvádějí nový název. [ověřeno]

## Co ARON obsahuje

Podle nápovědy archivu ([co v ARchivu ONline najdete](https://soahradec.gov.cz/napoveda-archivu-online/co-v-archivu-online-najdete/)):

- **Matriky N/O/Z** — všechny zveřejnitelné prvopisy matrik z území bývalého Východočeského kraje,
  fond **Sbírka matrik Východočeského kraje (NAD 190)**; strukturovaný popis + PDF pomůcka.
  Digitalizáty u „většiny“. API vrací **14 189** záznamů typu `matrika` (vč. indexů), z toho
  ~12 911 s příznakem `DIGITAL=Ano` [ověřeno počtem, význam filtru DIGITAL neověřen proti UI].
- **Sčítací operáty** — všechny dochované z okresů Královéhradeckého a Pardubického kraje
  (fondy *Okresní úřad …* ve SOkA), po obcích a číslech popisných.
- další: kroniky, „další evidence obyvatel“ (soupisy, urbáře), školní evidence, evidence nemovitostí
  (záložky na úvodní stránce = `favoriteQuery`), zeměpisný rejstřík k matrikám a sčítání.
- Neobsahuje objednávky ani jmenný index osob.

## Podmínky užití

Hledal jsem na portálu (patička, konfigurace, `robots.txt`) i na webu archivu (nápověda, vyhledávání
„podmínky“). **Žádné samostatné podmínky užití ARONu ani zákaz strojového přístupu jsem nenašel.**

- `robots.txt` neexistuje (SPA vrací `index.html`). [ověřeno]
- V `configuration.js` je zakomentovaný `daoFooter` se šablonou „Smluvní podmínky“ (odkaz na
  google.com) — tedy nepoužitá šablona, žádné podmínky zveřejněné nejsou. `disableDownloads` je
  vypnuté. [ověřeno]
- Nápověda archivu stahování výslovně nabízí: *„Lze prohlížet a stahovat jednotlivé snímky i celé
  sady digitalizátů (např. všechny stránky jedné matriky).“* a návod „Chci si stáhnout jednotlivý
  snímek nebo celou matriku“. Archiv doporučuje poznamenat si **citaci** (tlačítko „Vytvořit citaci“)
  a **identifikátor sady snímků**, který je vložen do každého snímku i do názvu souboru. Upozorňuje,
  že odkazy nejsou věčné. [ověřeno]
- Problémy s digitálními matrikami: `webmaster@ahapa.cz`; žádosti o informace z matrik: Archivní
  oddělení Zámrsk.
- **Smlouva o úschově s Biskupstvím královéhradeckým** (6. 5. 2025,
  [informace pro badatele PDF](http://soahradec.gov.cz/wp-content/uploads/2025/06/Smlouva-o-uschove_Biskupstvi-Hradec-Kralove_informace-pro-badatele_20250627.pdf)):
  týká se fondů **ve vlastnictví církve** (biskupství, kapitul, farností) — souhlas biskupství je třeba
  mj. k *reprodukcím pro komerční účely* a k *matričním přílohám* (snubní protokoly, ohlášky,
  biřmovanci) a k materiálu mladšímu 100 let. **Sbírky matrik (státní fond NAD 190) se podle textu
  netýká**; pro osobní rodinný výzkum z ARONu z ní nic neplyne. [ověřeno čtením, výklad můj]
- Obecně platí zákon č. 499/2004 Sb. (lhůty: N 100 let, O a Z 75 let — mladší svazky nejsou online).

**Závěr:** strojový přístup výslovně zakázán není a stahování snímků i celých sad je oficiálně
nabízené. Modul se drží pravidel workbenche: ~1 požadavek / 2,5 s, žádné paralelní dotazy,
User-Agent `genealogy-workbench/0.1 (osobní rodinný výzkum)`, cache, jen na vyžádání.

## Architektura

- `index.html` načítá React 16 + Material-UI z unpkg, `/configuration.js` a jeden bundle
  `/main.<hash>.js` (~3,7 MB). Backend: Spring (chybové odpovědi `org.springframework…`), za ním
  Elasticsearch (fulltext). [ověřeno]
- Základ API: `https://aron.vychodoceskearchivy.cz/api/aron`. Bez přihlášení, bez tokenu, JSON.
- Snímky: originální JPG přes `/api/aron/referencedfiles/{fileId}`; dlaždice DZI pro OpenSeadragon
  na `https://imgx.vychodoceskearchivy.cz/tiles/…/image.dzi`; ZIP celé sady na
  `https://storage.vychodoceskearchivy.cz/matriky/…zip`. [ověřeno]
- Žádné IIIF. Žádný anti-bot (Cloudflare apod.) jsem nepotkal; rate limit neznám. [ověřeno / neznámo]

## API — endpointy

Všechny cesty relativně k `/api/aron`.

| Metoda | Cesta | Účel | Stav |
|---|---|---|---|
| POST | `/apu/listview?listType=ARCH_DESC` | hledání (filtry, stránkování) | [ověřeno] |
| GET | `/apu/{id}` | plný detail záznamu vč. rodičů, `parts`, `digitalObjects` | [ověřeno] |
| GET | `/apu/{id}/view` | jen `id, name, description` (rychlé jméno entity / fondu) | [ověřeno] |
| GET | `/script/citation/{id}` | oficiální citace archivu (tlačítko „Vytvořit citaci“) | [ověřeno] |
| GET | `/referencedfiles/{fileId}` | stažení souboru (snímek JPG, náhled) | [ověřeno] |
| GET | `/favoriteQuery` | YAML záložek úvodní stránky (vyžaduje `Accept: */*`, s `application/json` vrací 400) | [ověřeno] |
| GET | `/apu/{id}/tree` | strom archivního souboru | [z kódu] |
| GET | `/apu/{id}/entity`, `/apu/{id}/related/{…}` | rejstříková hesla / související | [z kódu] |
| GET | `/file/{id}` | soubor uložený v DB (u matrik 404 — ty jsou „referenced“) | [ověřeno 404] |
| GET | `/digitalObjectFile/{id}/metadata/csv` | metadata snímku jako CSV | [z kódu] |
| GET | `/tile/{id}/image.dzi` | DZI, pokud dlaždice nejsou externí | [z kódu] |
| POST | `/apu/listsimple`, `/apu/list?listType=…` | agregace pro filtry UI | [z kódu] |

### Hledání: `POST /apu/listview?listType=ARCH_DESC`

Tělo:

```json
{
  "filters": [
    {"field": "type", "operation": "EQ", "value": "ARCH_DESC"},
    {"field": "UNIT~TYPE", "operation": "EQ", "value": "matrika"},
    {"field": "RECORD~TYPE", "operation": "EQ", "value": "záznamy narozených"},
    {"operation": "FTX", "value": "Chlumec nad Cidlinou"},
    {"field": "UNIT~DATE", "operation": "RANGE",
     "gte": "1840-01-01T00:00:00.000Z", "lte": "1860-12-31T23:59:59.999Z"}
  ],
  "offset": 0,
  "size": 50
}
```

Odpověď (zkráceno):

```json
{
  "items": [{
    "id": "d55af1cf-2d6c-4600-94eb-fcb6c89db2cb",
    "name": "Státní oblastní archiv v Hradci Králové: Sbírka matrik Východočeského kraje, sign.: 55-8 (poř.č. 3849), 1855-1859",
    "description": "římskokatolická matrika NAROZENÝCH, Chlumec nad Cidlinou - město, …, Olešnice",
    "order": 5619
  }],
  "count": 6,
  "searchAfter": "[\"…\"]",
  "aggregations": null
}
```

- Operace filtrů (z kódu): `EQ, AND, OR, NOT, FTX` (fulltext), `FTXF` (fulltext v poli),
  `CONTAINS, RANGE, GTE, LTE, NOT_NULL, AKF`. Vnořování přes `{"operation":"OR","filters":[…]}`. [z kódu; EQ/FTX/RANGE/OR ověřeno]
- `type`: `ARCH_DESC` (archiválie), `ENTITY` (rejstříková hesla), `FUND`, `FINDING_AID`, `ORIGINATOR`, `INSTITUTION`.
- `UNIT~TYPE`: `matrika`, `sčítací operát`, `kronika`, `dílčí evidence obyvatel`,
  `evidence školní docházky`, `evidence nemovitostí` (z `favoriteQuery`). [ověřeno]
- `RECORD~TYPE`: `záznamy narozených` / `záznamy oddaných` / `záznamy zemřelých`. [ověřeno]
- `UNIT~DATE` RANGE vrací svazky, jejichž datace se **překrývá** s intervalem (pro 1840–1860 přišly
  i 1837–1846 a 1860–1865). [ověřeno]
- `REG~GEO~REF` = UUID hesla zeměpisného rejstříku (filtr přesně podle obce). [ověřeno]
- FTX hledá v popisu **i v názvech navázaných rejstříkových hesel**: dotaz „Žiželice“ najde i svazek
  Chlumce, který má v rejstříku „Loukonosy (Žiželice, Kolín, Česko)“. Bez zástupných znaků,
  bez rozlišení velikosti písmen a délky samohlásek. Výsledky řazené abecedně (ne podle relevance).
- Stránkování: `offset` + `size` (UI má limit 9 999 výsledků; vrací i `searchAfter`). [ověřeno offset]

### Detail: `GET /apu/{id}`

Klíčová pole (zkráceno, záznam `d55af1cf-…`):

```text
type: ARCH_DESC, name, description
parent → parent → …   (strom sbírky: „Chlumec nad Cidlinou“ → „fary CH“ → „Římskokatolická církev“ → „Sbírka matrik…“)
parts[].items[]  (type = hodnota):
  UNIT~TYPE        = matrika
  OTHERID~SIG      = 55-8 (poř.č. 3849)     ← signatura (pořadové číslo v pomůcce)
  OTHERID~SIG~ORIG = VIII.                  ← původní označení svazku (např. „matrika IV“)
  STORAGE          = 3345                   ← ukládací jednotka
  UNIT~DATE        = {"from":"1855-01-01T00:00:00","to":"1859-12-31T23:59:59","format":"Y-Y"}
  UNIT~CONTENT     = fol. 259-260 narození mimo farnost (Loukonosy, Převýšov, Hradišťko) 1842-1858
  SIZE             = 25,5x38,5 cm, 261 fol.
  RECORD~TYPE      = záznamy narozených
  EXISTING~COPY    = číslo mikrofilmu: 2586,2587
  URL              = "Stáhnout všechny snímky", href = https://storage.vychodoceskearchivy.cz/matriky/4/CZ_215000010_00190_4QWJDYGB_sign-55-8.zip
  DIGITAL          = Ano
  REG~GEO~REF      = <UUID obcí>            ← zeměpisný rejstřík
  ORIGINATOR~REF   = <UUID>  (u rodiče)      → /apu/{uuid}/view = „Děkanský úřad Chlumec nad Cidlinou …“
  FUND~REF         = 802115df-…              → „Sbírka matrik Východočeského kraje“
digitalObjects[0]: id (= id záznamu), files[]:
  PUBLISHED  ×270  name=CZ_215000010_00190_4QWJDYGB_00001_sign-55-8.JPG, size≈2,3 MB, referencedFile=/mnt/images/…
  THUMBNAIL  ×270
  TILE       ×270  referencedFile=https://imgx.vychodoceskearchivy.cz/tiles/ec/38/<uuid>/image.dzi
```

Číslo snímku = `order` souboru typu `PUBLISHED` (1…N) = číslo v názvu souboru (`_00005_`).
[ověřeno pro 1 svazek s jedním DAO; svazky s více DAO neověřeny]

### Oficiální citace: `GET /script/citation/{id}`

```json
{"citation": "Státní oblastní archiv v Hradci Králové; Sbírka matrik Východočeského kraje (NAD 190); sign. 55-8 (poř.č. 3849); sign. pův. VIII.; ukl. j. 3345; římskokatolická matrika NAROZENÝCH, Chlumec nad Cidlinou - město, …"}
```

## Jak najít matriku podle obce / farnosti a roku

1. **Rychle (modul):** `find_registers(place, year_from, year_to, kind)` = hledání výše (FTX + typ +
   datace). Výsledky, kde obec není v popisu svazku, jsou na konci — obvykle shoda přes místní část.
2. **Přesně:** najít heslo obce (`type=ENTITY`, FTX název) → UUID → filtr `REG~GEO~REF` (OR přes obec
   a její části). Heslo má tvar „Žiželice (Kolín, Česko)“ (obec) a „Loukonosy (Žiželice, Kolín, Česko)“ (část).
3. **Podle farnosti:** rodič svazku ve stromu sbírky (`parent.description`, např. „Chlumec nad
   Cidlinou“) a původce (`ORIGINATOR~REF`). Historické názvy přes zeměpisný rejstřík.
4. PDF pomůcka ke sbírce matrik obsahuje rejstřík matričních míst a odkazy na ZIP — [neověřeno, nestahováno].

## Snímek a ZIP

- **Jeden snímek:** `GET /api/aron/referencedfiles/{fileId}` → `image/jpeg`, `Content-Disposition`
  s původním názvem, `Cache-Control: public, max-age=604800`. Ukázka: 4078×3248 px, ~2 MB. [ověřeno]
- **Odkaz do prohlížeče na snímek:** `https://aron.vychodoceskearchivy.cz/apu/{id}/dao/{daoId}/file/{fileId}`
  (trasa SPA; `daoId` = id záznamu u matrik). [z kódu, v prohlížeči neověřeno]
- **Celá sada (ZIP):** href položky `URL` v detailu. Ukázka `sign. 55-8`: **565 MB**, 270 snímků,
  `Last-Modified: 2023-03-10` — **nestahováno**, jen HEAD. Modul ZIP nikdy nestahuje
  (`register_zip_info` = jen HEAD; limit 50 MB na jeden soubor v HTTP klientu). [ověřeno]
- DZI dlaždice (`TileSize=254, Overlap=1`) modul nepoužívá — originál JPG je k dispozici přímo.

## Identifikátory pro citaci

| Prvek | Odkud | Příklad |
|---|---|---|
| archiv | `name` před dvojtečkou / citace | Státní oblastní archiv v Hradci Králové |
| fond + NAD | `name`, `/script/citation` | Sbírka matrik Východočeského kraje (NAD 190) |
| farnost / úřad | `parent.description`, `ORIGINATOR~REF` | Chlumec nad Cidlinou; Děkanský úřad Chlumec nad Cidlinou |
| signatura (poř. č.) | `OTHERID~SIG` | 55-8 (poř.č. 3849) |
| původní signatura | `OTHERID~SIG~ORIG` | VIII. |
| ukládací jednotka | `STORAGE` | 3345 |
| sada snímků | 4. pole názvu souboru | 4QWJDYGB (v `CZ_215000010_00190_4QWJDYGB_00005_sign-55-8.JPG`) |
| snímek | `order` souboru PUBLISHED | 5 |
| trvalý identifikátor záznamu | UUID v `/apu/{id}` | d55af1cf-2d6c-4600-94eb-fcb6c89db2cb |

`215000010` v názvu souboru je zřejmě kód archivu, `00190` číslo NAD. [neověřeno]
Folio/stranu modul neurčí — je jen na snímku; doplní člověk.

## Omezení a poznámky

- API je nedokumentované a může se změnit (bundle `main.c085bdb24439f0b78cec.js`, index z 18. 2. 2025).
- `permalink` je u matrik `null`; trvalý je UUID záznamu. Archiv sám upozorňuje, že odkazy nejsou věčné
  → vždy ukládat i signaturu a identifikátor sady.
- Fulltext vrací i volné shody (místní části, poznámky o narozených mimo farnost) — výsledek je nutné
  číst, ne slepě brát.
- Územní příslušnost: **ARON má matriky dnešního Královéhradeckého a Pardubického kraje (bývalý
  Východočeský kraj)**. Obce, které dnes leží jinde, tu mají jen civilní/evangelické matriky
  širších obvodů nebo sčítání (viz Žiželice níže).

## Případ Žiželice (okr. Kolín) — co ARON má

Dotazy 16. 10. 2026 (FTX „Žiželice“ a filtr `REG~GEO~REF` na hesla obce a části). [ověřeno]

- **Římskokatolické matriky farnosti Žiželice v ARONu nejsou.** Žádný řkt svazek s Žiželicemi jako
  matričním místem; obec leží dnes ve Středočeském kraji, matriky farnosti Žiželice proto
  pravděpodobně spravuje **SOA Praha (eBadatelna)** [neověřeno — ověřit v eBadatelně].
- Řkt **Chlumec nad Cidlinou N 1855–1859** (`d55af1cf-…`, sign. 55-8) má fol. 259–260 „narození mimo
  farnost (Loukonosy, Převýšov, Hradišťko) 1842–1858“ — Loukonosy a Hradišťko II jsou dnes části Žiželic.
- **Civilní matriky** okresního úřadu (soudní okres Chlumec n. C., Žiželice uvedeny): O 7.1871–12.1921
  (sign. 7661), Z 11.1872–1932 (sign. 8139), indexy O 1871–1949 (8717) a Z 1872–1949 (8718), dále
  roční svazky 1931–1942 a čsl./ev. matriky 20. stol.
- **Sčítací operáty Žiželice** (SOkA Hradec Králové, fond Okresní úřad Nový Bydžov), po čp.:
  1869 (inv. č. 1075, čp. 1–305, `6e5d102e-1c91-4c93-9d87-5fa5084de490`), 1880 (inv. č. 1158,
  `9e1841a5-…`), 1890 (inv. č. 1246, `4f1b11b9-…`), 1900 (inv. č. 1338, `09c952c2-…`), 1910
  (inv. č. 1435, `017df0a5-…`), 1921 (poř. č. 815 a 816, `34478435-…`, `dac3a1ba-…`); plus místní části
  (Zbraň, Končice, Kundratice, Loukonosy, Hradišťko II). **Všechny uvedené ročníky pokrývají čp. 53** —
  vhodné pro rodinu Vrbických. Sčítání 1869 je digitalizované: 862 snímků, sada `AP77LOV2`, ZIP
  `https://storage.vychodoceskearchivy.cz/scitani/A/CZ_225101010_01019_AP77LOV2_zizelice-1869.zip`
  (velikost neověřena, nestahováno).
