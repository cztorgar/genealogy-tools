# SOA v Praze — eBadatelna

Portál: <https://ebadatelna.soapraha.cz/> · web archivu: <https://www.soapraha.cz/>
Modul MCP: `ebadatelna_praha` ([`mcp/czech-archives`](../../mcp/czech-archives/README.md)).
Průzkum: 16. 10. 2026. Značení: **[ověřeno]** = vyzkoušeno požadavkem, **[z kódu]** = vyčteno z HTML/JS
stránky, nevyzkoušeno; **[neověřeno]** = domněnka.

Co eBadatelna obsahuje (úvodní stránka): **kompletní digitalizovanou sbírku matrik Středočeského
kraje**, které SOA Praha spravuje (N po 100 letech, O a Z po 75 letech od posledního zápisu), dále
sekci „Archiválie“ (jiné digitalizované archiválie, modul ji nepoužívá). Co v eBadatelně není, SOA
Praha nemá (mladší matriky jsou na matričních úřadech — seznam v sekci Dokumenty).

## Podmínky užití

Hledal jsem na portálu (úvod, Nápověda, Dokumenty, registrační formulář, `robots.txt`) a na webu
archivu (Pro badatele, badatelský řád). **Samostatné podmínky užití eBadatelny ani zákaz strojového
přístupu jsem nenašel.** [ověřeno]

- `robots.txt` neexistuje (302 na úvodní stránku). [ověřeno]
- **Registrační formulář** (souhlas GDPR) výslovně říká: *„Unregistered users are allowed to browse
  all images on eBadatelna without any restriction. They are only not allowed to download ZIP files of
  the whole records/books and write users remarks to digitized records.“* — tj. **neregistrovaný
  uživatel smí prohlížet všechny snímky**; registrace je jen pro **ZIP celé knihy** a uživatelské
  poznámky. [ověřeno, text formuláře v angličtině]
- Prohlížeč má u každého snímku tlačítko **stáhnout (▼)** s originálním JPG — stažení jednotlivého
  snímku je tedy nabízená funkce i bez přihlášení. [ověřeno]
- Úvodní stránka: dotazy a připomínky na `ebadatelna@soapraha.cz`, diskusní fórum na okounu,
  **denní údržba ve 4:44** (~2 min nedostupnost). Omezení: matriky předané dříve (špatný stav) nejsou
  dálkově přístupné před uplynutím lhůty (neplatí pro Z). [ověřeno]
- **Badatelský řád SOA Praha** ([PDF, 2012](https://www.soapraha.cz/files/badatelsky_rad_2012.pdf))
  se týká studia v badatelně; pro využití platí čl. 3 odst. 5: při využití ve vědeckých pracích nebo
  zveřejnění uvádět **název archivu, archivní soubor a bližší označení archiválie (citaci)**; čl. 5
  reprodukce (placené) podle sazebníku. O dálkovém přístupu nic. [ověřeno čtením]
- Obecně zákon č. 499/2004 Sb. (lhůty N 100 let, O a Z 75 let).

**Závěr:** strojový přístup zakázán není, neregistrovaným je prohlížení všech snímků výslovně
povoleno a stažení jednotlivého snímku je funkcí prohlížeče. **ZIP celé knihy je jen pro
registrované — modul ho nepoužívá a nepřihlašuje se.** Modul se drží pravidel workbenche:
~1 požadavek / 2,5 s (sdílený zámek z `core`), žádné paralelní dotazy, User-Agent
`genealogy-workbench/0.1 (osobní rodinný výzkum)`, cache, jen na vyžádání. Pro rozsáhlejší
využití (nad rámec jednotlivých snímků) by bylo slušné napsat na `ebadatelna@soapraha.cz`.

## Je potřeba přihlášení?

**Ne** — popis, hledání, prohlížeč i originální JPG fungují anonymně. [ověřeno pro Žiželice 04,
19, 25] Portál zakládá anonymní session (cookie `JSESSIONID`) sám; modul ji drží v paměti
(nová po 10 min) a nic dalšího nepotřebuje.

Kdyby někdy bylo přihlášení třeba (ZIP celé knihy, uživatelské poznámky, případně budoucí změna):
přihlášení je Wicket AJAX popup (e-mail + heslo) a výsledkem je jen session cookie `JSESSIONID`.
Návrh bez zadávání hesel do agenta: uživatel se přihlásí v prohlížeči a modulu předá **hodnotu
cookie `JSESSIONID`** (proměnná prostředí, např. `EBADATELNA_JSESSIONID`, nikdy do repa); modul by
ji vložil do cookie jaru `_Session`. Session vyprší po nečinnosti, takže jde jen o krátkodobý
„přenos“ přihlášení. **Neimplementováno** — zatím není potřeba.

## Architektura

- **Apache Wicket** (server-side, stavové stránky), Apache/AlmaLinux, jQuery. **Žádné JSON API**,
  žádné IIIF, žádné dlaždice — HTML stránky + Wicket AJAX (`<ajax-response>` XML). [ověřeno]
- Jazyk podle `Accept-Language` (cs/en/de); modul posílá `cs`. Bez hlavičky přichází angličtina.
- Stavovost: URL obsahují číslo verze stránky (`?3-1.0-searchForm-searchButton`) a po prvním
  požadavku nové session i `;jsessionid=…`. Modul `jsessionid` z HTML odstraňuje (cookie stačí).
- Anti-bot ani rate limit jsem nepotkal. [ověřeno / neznámo]

## Stránky a endpointy

| Metoda | Cesta | Účel | Stav |
|---|---|---|---|
| GET | `/pages/MatrikaPage/matrikaId/{ID}` | popis knihy (bookmarkovatelné) | [ověřeno] |
| GET | `/d/{ID}/{snímek}` | krátký odkaz prohlížeče = `DataMatrikaPage/idx/{snímek}/matrikaId/{ID}` | [ověřeno] |
| GET | `/pages/DataMatrikaPage/matrikaId/{ID}` | prohlížeč od snímku 1 | [z kódu] |
| GET | `/pages/PreviewDataMatrikaPage/matrikaId/{ID}` | náhledy | [z kódu] |
| GET | `/pages/PuvodcePage/matrikaId/{ID}` | původce (okres, typ, lokality) | [ověřeno] |
| GET | `/pages/UserNoteMatrikaPage/matrikaId/{ID}` | poznámky uživatelů | [z kódu] |
| GET | `/pages/SearchMatrikaPage` | formulář hledání matrik; v HTML i **úplné seznamy pro našeptávač** | [ověřeno] |
| POST (AJAX) | `/pages/SearchMatrikaPage?{v}-1.0-searchForm-searchButton` | hledání | [ověřeno] |
| GET (AJAX) | `…?{v}-1.0-tableContainer-pagination-results-nextPageUrl` | další stránka výsledků | [ověřeno] |
| GET | `/wicket/resource/org.apache.wicket.Application/{soubor}.jpg` | **originál snímku** (tlačítko ▼) | [ověřeno] |
| GET | `/d/{ID}/{snímek}?{v}--scanImage` | obrázek v prohlížeči (stavový) | [ověřeno] |
| GET | `/pages/DocumentsPage`, `/pages/HelpPage`, `/pages/IndexPage` | dokumenty (PDF), nápověda (převod starých URL), úvod | [ověřeno] |

Menu je Wicket AJAX (`IndexPage?0-1.0-mainNavigation-menuContainer-navigationView-N-menuItemLink`),
odpověď je `<redirect>` na stránku: 1 = `SearchMatrikaPage`, 4 = `DocumentsPage`, 6 = `HelpPage`.

### Popis knihy (`MatrikaPage`)

HTML tabulky `tableMatrikaBasicInfoRow` (label v `tableMatrikaBasicInfoHeader1`, hodnoty
v `tableMatrikaBasicInfoHeader2`), popisy `tableMatrikaDescription`, lokality `obecCastLabel`.
Zkrácená ukázka (Žiželice 04, matrikaId 10056):

```text
<h1>Žiželice 04</h1>
Původní název      IV.
Okres              Kolín
Původce            Žiželice (Římskokatolická církev)
Narození / index   1842 - 1848 | 1842 - 1848      ← [matrika, index]
Oddaní / index     ---         | ---
Zemřelí / index    ---         | ---
Stav úplnosti      úplný
Typ knihy          kniha obsahuje matriku i rejstřík
Počet listů 0, Počet stran 0, Počet snímků 298
Místo uložení      Státní oblastní archiv v Praze
Obecný popis matriky:
  Žiželice 1/1842-12/1848, fol. 1-83 [4-86]
  Loukonosy 1/1842-12/1848, fol. 173-184 [165-176]
  …
  index N 286-309 [273-297]
  prázdná fol.: 84-87, 102-104, …
Detail původce     Matriky před rokem 1798 se nedochovaly.
Lokality           Loukonosy / Loukonos · Převýšov / Neudorf / Přivýšov, Přebýšov, … · Žiželice / Žiželitz
```

**Čísla v hranatých závorkách = čísla snímků.** Ověřeno: snímek 5 svazku 10056 = fol. 2
(„Žiželice 1842“), popis „fol. 1-83 [4-86]“. [ověřeno na 1 snímku] Modul z toho dělá
`image_map` (obec, období, folia → snímky) — rychlá navigace k oddílu obce. Ne každý svazek má
tento formát (Žiželice 25 má jen „Rozvržení folií“ bez čísel snímků).

### Hledání (`SearchMatrikaPage`)

1. `GET /pages/SearchMatrikaPage` → HTML s formulářem (`<form class="searchForm" id="id44">`) a
   AJAX URL tlačítka; obsahuje i JS pole `availableTags1` (**9 972 lokalit** ve tvaru
   „Loukonosy - obec Žiželice - okres Kolín“, vč. historických variant) a `availableTags2`
   (**12 282 názvů knih** „Žiželice 01“…). [ověřeno]
2. AJAX POST (hlavičky `Wicket-Ajax: true`, `Wicket-Ajax-BaseURL: pages/SearchMatrikaPage?{v}`):

```text
id44_hf_0=
searchType=1                              (1 = podle klíčového slova, 2 = podle typu původce)
keywordBox:searchTokenIn=radio0           (radio0 = v lokalitách, radio1 = v názvech knih)
keywordBox:searchToken=Žiželice
dateYearFrom=1840&dateYearTo=1850         (prázdné = 1000–2100)
searchButton=1
```

Odpověď `<ajax-response>` s HTML tabulkou (zkráceno):

```html
<span>nalezeno 7 knih</span>
<tr name="dataLink" href="/pages/DataMatrikaPage/idx/1/matrikaId/10056" …>
  <td><a class="matrikaLink" href="/pages/MatrikaPage/matrikaId/10056">Žiželice&nbsp;04</a></td>
  <td><span>Římskokatolická&nbsp;církev</span></td> <td><span>Kolín</span></td>
  <td class="hidden"><span>15</span></td>          ← počet lokalit
  <td><span>Bílé Vchynice, Freudenthal, …, Žiželice</span></td>
  <td><span>1842&nbsp;-&nbsp;1848</span></td> <td>---</td> <td>---</td>   ← N, O, Z
  <td><span>1842&nbsp;-&nbsp;1848</span></td> <td>---</td> <td>---</td>   ← index N, O, Z
  <td><span>298</span></td>                         ← snímky
</tr>
```

- Lokalita se hledá **podřetězcem** i bez přesného tvaru z našeptávače: „Žiželice“ → 38 knih
  (ř. k. Žiželice + ev. Krakovany a další, které mají Žiželice mezi obcemi). [ověřeno]
- Rozsah let vrací knihy, jejichž datace se **překrývá** (1840–1850 → i Krakovany-ev 03 1830–1858). [ověřeno]
- „V názvech knih“: „Žiželice“ → 30 knih Žiželice 01–30. [ověřeno]
- Stránkování 50 na stránku (volba 5–100); další stránka přes AJAX `nextPageUrl`. [ověřeno, 60 výsledků „Kolín“]

## Jak najít svazek

1. **Podle obce / lokality:** `find_registers(place, year_from, year_to, kind)` → živé hledání
   „v lokalitách“ (modul), filtr druhu N/O/Z/I a překryvu let. Funguje i pro místní části
   a historické názvy (Loukonosy, Žiželitz).
2. **Podle farnosti / názvu knihy:** totéž s `in_titles=True` (v Pythonu), nebo PDF
   „Původci (farnosti) a názvy matrik SOA Praha“ v Dokumentech (farnost → název knihy → okres).
3. **Podle matrikaId:** známé ID (z gazetteeru, z odkazu `…/d/<ID>/<snímek>` od uživatele) →
   `register_info(ID)`.
4. **Offline:** při nedostupnosti portálu se použije `mcp/czech-archives/gazetteer/*.yml`
   s `module: ebadatelna_praha` (Žiželice: [`zizelice.yml`](../../mcp/czech-archives/gazetteer/zizelice.yml)).

## Snímek v plném rozlišení

- Web je stavový: obrázek v prohlížeči `./{snímek}?{v}--scanImage` se neřídí číslem v URL, ale
  stavem session. Proto (princip převzatý z README [lioilsources/genealogy-matriky](https://github.com/lioilsources/genealogy-matriky),
  repo bez licence → kód nepřebírán) **vždy nejdřív načíst HTML `/d/{ID}/{snímek}`** a z něj vzít odkaz.
- V patičce prohlížeče je velikost („1.82 MB“) a **odkaz ▼**:
  `../../wicket/resource/org.apache.wicket.Application/Zizelice_04__005.jpg` →
  `image/jpeg`, `Content-Disposition: attachment; filename="Zizelice_04__005.jpg"`. Po vykreslení
  stránky funguje **i bez cookie** (bezstavový). [ověřeno]
- Originál ukázky: **3300 × 2502 px, 1 908 317 B, šedotón**, EXIF datum 2009-03-20. Obrázek
  `scanImage` je **bajtově shodný** s odkazem ▼ (SHA-256 `cd0975ee…`) — žádné zmenšení. [ověřeno]
- Modul: 1 požadavek na HTML prohlížeče (+ kontrola, že vybraný snímek v `pageDropdown` = žádaný)
  a 1 na JPG; odkaz se cachuje 30 dní, JPG natrvalo. Když by odkaz ▼ chyběl, záloha přes
  `scanImage` ve stejné session. Kontrola magic bytes (JPEG/PNG), jinak nic neuloží.
- Název souboru (`Zizelice_04__005.jpg`) odvozuje portál z názvu knihy bez diakritiky — **neskládat
  ručně**, brát z HTML (odlišné knihy se mohou po odstranění diakritiky shodovat). [neověřeno]
- ZIP celé knihy: jen pro přihlášené, modul nepoužívá.

## Identifikátory pro citaci

| Prvek | Odkud | Příklad |
|---|---|---|
| archiv | „Místo uložení“ | Státní oblastní archiv v Praze |
| fond | portál neuvádí | — *(„Sbírka matrik“ obecně [neověřeno], ověřit v ARON SOA Praha `aron.soapraha.cz`)* |
| původce / farnost | „Původce“ | Žiželice (Římskokatolická církev) |
| název knihy (= farnost + pořadové číslo) | `<h1>` | Žiželice 04 |
| původní označení | „Původní název“ | IV. |
| trvalé ID | URL | matrikaId 10056 |
| snímek | číslo v prohlížeči / `/d/{ID}/{snímek}` | 5 |
| odkaz na snímek | krátký odkaz | `https://ebadatelna.soapraha.cz/d/10056/5` |
| folio | „Obecný popis“ (+ na snímku) | fol. 2 (doplní člověk) |

Text citace z modulu: *Státní oblastní archiv v Praze, ř. k. f. ú. Žiželice, I+N 1842–1848, kniha
Žiželice 04 (pův. IV.), matrikaId 10056, snímek 5. Online: https://ebadatelna.soapraha.cz/d/10056/5,
cit. 16. 10. 2026.*

## Omezení a poznámky

- Parsování HTML — při změně šablony portálu se rozbije; Wicket čísla verzí stránek se neukládají,
  modul je bere vždy z čerstvého HTML.
- Hledání = 2 požadavky (formulář + POST) + 1 na každou další stránku výsledků; cache 1 den.
  Popis knihy 7 dní, odkaz na snímek 30 dní.
- Druh `kinds`: `I` = kniha má index; svazek jen s indexem (Žiželice 22: IN 1866–1880) dostane
  `["I", "N"]`. Přesné rozsahy matriky a indexů jsou v `years_text` („N 1842–1848; IN 1842–1848“).
- Fond portál nevypisuje; citace ho zatím neobsahuje.
- Sekce „Archiválie“ (jiné prameny než matriky) modul nepokrývá.

## Ověřeno 16. 10. 2026

- `register_info` 10056 (Žiželice 04, N+IN 1842–1848, 298 snímků, pův. IV.), 10071 (Žiželice 19,
  O+IO 1871–1888, 266 snímků), 10077 (Žiželice 25, Z+IZ 1906–1930, 366 snímků, 299 listů). [ověřeno]
- `find_registers("Žiželice", 1840, 1860, "N")` → 10055–10058 + Krakovany-ev 03/04;
  `("Loukonosy", 1870, 1890, "O")` → Žiželice 10/19/20 + Krakovany-ev 06. [ověřeno]
- `fetch_page("10056", 5, …)` → JPG 3300×2502 + sidecar `.yml`. Při průzkumu i testu stažen
  **jen tento jeden snímek** (3× ručně pro porovnání metod, 1× modulem). [ověřeno]
