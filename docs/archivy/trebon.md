# SOA Třeboň — DigiArchiv (digi.ceskearchivy.cz)

Stav k 18. 10. 2026 (session predci-k0005). **Modul `digi_trebon` nevznikl a zatím nevznikne** — viz níže.
Rozhodnutí o dalším postupu (vlastní modul vs. jen ruční čtení přes prohlížeč) je na uživateli.

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
  
- `robots.txt`: povoluje `/index.php`, `/index_main.php`, `/DA*`; zakazuje mj. `/Assets/`, `/cache/`, `/pages/`, `/oai/`.
- URL pohledu: `https://digi.ceskearchivy.cz/<id svazku>/<snímek>/<x>/<y>/<zoom %>/<rotace>` (x, y = střed pohledu
  v pixelech originálu) → přesměruje na `DA?menu=3&id=…&page=<snímek−1>&x=…&y=…&z=…&r=…`. URL se dá uložit jako
  odkaz na konkrétní místo zápisu.
- Snímky: Zoomify přes `cgi-bin/isrv8.cgi?<expirace>/<HMAC>/data1/<číslo>.0.<úroveň-x-y>`; `.desc` vrací
  `IMAGE_PROPERTIES` (např. 4487 × 3233 px, dlaždice 561). Dlaždice jsou **podepsané a časově omezené**.
- Hledání: záložka HLEDÁNÍ (fulltext, přístupové body = obce s historickými názvy), výsledky v iframe.
