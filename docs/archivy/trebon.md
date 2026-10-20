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

## Podmínky užití (doslova, https://digi.ceskearchivy.cz/Uvod)

> Všechny digitalizované materiály jsou chráněny platným autorským zákonem! Veškerá práva na zveřejnění a
> rozmnožení reprodukcí náleží jednotlivým vlastníkům archiválií, jejichž souhlas je nutný k případnému dalšímu
> využití snímků.
> Snímky jsou poskytnuty pouze za účelem on-line prohlížení v DigiArchivu SOA v Třeboni, jejich kopírování,
> distribuování, prodávání, využití v jiných projektech a na jiných stránkách je zakázáno.

Registrovaní uživatelé mohou snímky tisknout / exportovat („Registrovaní uživatelé mohou snadno tisknout snímky
a zdarma využívat další funkce“). Kontakt: digi@ceskearchivy.cz.

## Technika (ověřeno)

- **Blok klienta:** požadavek s User-Agentem obsahujícím „genealogy“ dostane **403** na celý web včetně
  `robots.txt`; `curl/…`, `Python-urllib/…`, `workbench/0.1` i prohlížeč dostanou 200. Jde o cílený blok
  nástrojů pro genealogii → změnit UA by bylo obcházení ochrany. **Nedělat.**
- `robots.txt`: povoluje `/index.php`, `/index_main.php`, `/DA*`; zakazuje mj. `/Assets/`, `/cache/`, `/pages/`, `/oai/`.
- URL pohledu: `https://digi.ceskearchivy.cz/<id svazku>/<snímek>/<x>/<y>/<zoom %>/<rotace>` (x, y = střed pohledu
  v pixelech originálu) → přesměruje na `DA?menu=3&id=…&page=<snímek−1>&x=…&y=…&z=…&r=…`. URL se dá uložit jako
  odkaz na konkrétní místo zápisu.
- Snímky: Zoomify přes `cgi-bin/isrv8.cgi?<expirace>/<HMAC>/data1/<číslo>.0.<úroveň-x-y>`; `.desc` vrací
  `IMAGE_PROPERTIES` (např. 4487 × 3233 px, dlaždice 561). Dlaždice jsou **podepsané a časově omezené**.
- Hledání: záložka HLEDÁNÍ (fulltext, přístupové body = obce s historickými názvy), výsledky v iframe.

## Proč žádný modul

1. Portál cíleně blokuje náš (poctivě identifikovaný) klient.
2. Podmínky užití zakazují kopírování snímků — a modul by snímky ukládal do cache a `sources/` a posílal OpenAI.
3. Ovládat kvůli tomu prohlížeč uživatele (Claude in Chrome) je také obcházení — **manager 18. 10. 2026: na
   DigiArchiv Třeboň Claude in Chrome nepoužívat, dokud uživatel nerozhodne G-02.**

Co by to změnilo: souhlas archivu s kopiemi pro soukromý výzkum, nebo registrace uživatele a export snímků
(uživatel je dá do `doklady/`, session je zpracuje jako ostatní doklady).

## Co session stihla před zastavením

Jediný zápis přečtený on-line (jedno čtení Claude, bez kopie snímku): O Chyšky kn. 16 (1882–1925), snímek 82,
zápis č. 13 (sňatek 1897). Formát URL pohledu:
https://digi.ceskearchivy.cz/4265/82/1450/1550/100/0 (jistota ≤ 1, „čteno on-line přes prohlížeč“).
