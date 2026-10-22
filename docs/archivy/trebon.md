# SOA Třeboň — DigiArchiv (digi.ceskearchivy.cz)

Stav k 21. 10. 2026: **modul `digi_trebon` existuje (v0.1)** — hledání, popis svazku a stažení snímku
složeného ze Zoomify dlaždic. Rozhodnutí G-02 (přístup pro soukromý výzkum) platí; modul chodí
s browserovým UA, snímky po jednom, bez přihlášení. Endpointy v sekci „Modul digi_trebon“.

## Obsah

Matriky jižních Čech všech církví (~10 000 svazků), soupisy poddaných, sčítání 1857–1921, kroniky, pozemkové
knihy, mapy; elektronické jmenné rejstříky (přepis indexů, hledání podle jména) u části svazků. Aplikace
DigiArchiv ver. 26.10.15 (© Martin Hankovec), starší PHP + jQuery, prohlížeč snímků Zoomify.

Příklad pokrytí (hledání „Nosetín“): ř. k. f. ú. **Chyšky** — kn. 1 (N O 1673–1713, Z 1689–1713, inv. č. 2149),
kn. 2 (1714–1743, inv. č. 2150) … kn. 16 (O 1882–1925). Obce farnosti: Branišov, Busíny, Chlístov, Chyšky (Malá
Chýška), Číčovice, Dobřemilice, Hrachov, Klokočov, Kvašťov, Květuš, Nosetín, Nová Ves, Podchýšská Lhota, Rážkovy,
Rohozov, Růžená, Střítež, Vilín, Voděrady, Záluží.

## Technika

- je potreba pouzit jinou user User-Agentem hlavicku nez genealogy, delame jen soukromy vyzkum a chceme se tam jednoduse dostat par listu stahnout.
- `robots.txt`: povoluje `/index.php`, `/index_main.php`, `/DA*`; zakazuje `/pages/*`, `/cache/*`, `/oai/*` ad.
  (obsahové endpointy aplikace jsou pod `/pages/` — modul je volá cíleně jako prohlížeč, ne jako crawler).

## Modul digi_trebon

Ověřeno 21. 10. 2026 (browserové UA, cs hlavičky, anonymní session s cookie). Stavová PHP aplikace,
bez API. Čísla snímků od 1.

- **Hledání** (`find_registers`): `POST /pages/search_result.php?id=0&queryid=&doctree=10`, tělo
  `sparam=<PHP-serializovaný dotaz 21 polí>&obsah_sn=0&lang=cs&sst=0&order=&ih=&iw=&histstore=0`.
  Z výsledku se vyberou `id` svazků (`otevridet("mtyp=2&id=<id>…")`). Je to **fulltext nad záznamy**
  (nápověda) — vrací i svazky, kde se obec objeví jen jako bydliště osoby; farnost ověř v popisu.
- **Popis svazku** (`register_info`): `GET /description.php?menu=4&id=<id>&doctree=10&lang=cs` — tabulka
  label→hodnota. Užitečná pole: `Sídlo farního úřadu` (farnost), `Datace NOZ` (druh + roky, např.
  „O 1913-1932“), `Církev`, `Číslo NAD`, `Archivní soubor` (fond), `Pořadové číslo` (signatura),
  `Počet snímků`, `Kniha vedena pro` (obce).
- **Prohlížeč**: permalink `https://digi.ceskearchivy.cz/<id>/<snímek>` → `GET /view.php?menu=3&id=<id>&page=<snímek>&r=0`
  (čistá session stačí, `page` je 1-based; `page=0` = „neexistuje“). Hlavní obrázek je v JS
  `Z.showImage("myContainer","<expirace>/<HMAC>/data1/<imgnum>", …)`.
- **Snímek** (`fetch_page`): Zoomify přes `GET /cgi-bin/isrv8.cgi?<expirace>/<HMAC>/data1/<imgnum>.0.<suffix>`.
  Token je podepsaný, časově omezený a **platí pro celý obrázek**: `.0.desc` = `IMAGE_PROPERTIES`
  (WIDTH, HEIGHT, TILESIZE, NUMTILES), dlaždice `.0.<tier>-<col>-<row>` (512 px, okraje oříznuté).
  Nejvyšší tier = plné rozlišení (např. 8176×6132 = 16×12 dlaždic); modul je složí přes Pillow do JPG.
  Token se nikdy necachuje (bere se čerstvý z view.php), hotový JPG se cachuje.
- **Rychlost**: portálové stránky ≥ 2,5 s, dlaždice jednoho snímku ≥ 0,5 s (sdílený zámek) → plný snímek
  ~100 s. Oficiální export celého JPG (`export.php`) je jen pro přihlášené — nepoužíváme.
