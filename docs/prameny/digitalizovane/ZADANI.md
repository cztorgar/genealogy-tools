# Zadání: index digitalizovaných pramenů po oblastech (kroniky, noviny …)

Cíl: pro každou oblast výzkumu (`docs/mistopis/oblasti.yml`) a v ní **každou obec** zjistit, jaké **nematriční prameny**
jsou digitalizované a dostupné online, a zapsat je do indexu. Zatím **jen indexovat prameny** (co existuje, kde, za jaké
období, v jaké podobě) — **texty nestahovat ani nečíst**. Ke každému prameni rozlišit, jestli je jen **nafocený**
(skeny), nebo i **převedený na text** (OCR / přepis / edice).

## Co hledat (podle obce, příp. farnosti, školy, spolku, panství)

- **kroniky:** obecní/městské, školní, farní (liber memorabilium), spolkové (hasiči, Sokol), pamětní knihy, kroniky rodů
- **noviny a periodika:** regionální týdeníky a věstníky (okresní, krajské), obecní zpravodaje, celostátní deníky jen tam,
  kde mají regionální rubriku; výskyt v Krameriu (fulltext!)
- **úřední knihy obce:** obecní protokoly, domovské matriky, seznamy obyvatel, knihy cizinců
- **školní:** třídní výkazy, katalogy (pokud online)
- **další:** sčítací operáty (máme zčásti v ARONu — jen zapsat odkaz na fond), pozemkové/gruntovní knihy, urbáře,
  císařské otisky a indikační skici (mapy už v `docs/mistopis/*/mapy.md` — jen odkázat), vojenské (VÚA), pohlednice/fotografie
  (jen fondy, ne jednotlivé snímky)

## Kde hledat

ARON východočeských archivů (SOA Zámrsk + SOkA), eBadatelna SOA Praha (SOkA Kolín, Nymburk, Beroun, Příbram …),
Kramerius: Národní digitální knihovna (ndk.cz), digitalniknihovna.cz (CDK), Kramerius SVK Hradec Králové, KK Pardubice,
SVK Kladno, KVK; Porta fontium; krajské a obecní weby (zpravodaje), Manuscriptorium; Digitální badatelna NA. Šetrně (≈ 2,5 s,
cache), žádné hromadné stahování.

## Výstup (jen workbench, žádné osobní údaje)

1. `docs/prameny/digitalizovane/<oblast>.csv` — jeden řádek = jeden pramen (svazek / periodikum / fond):
   `obec,oblast,typ,nazev,obdobi,instituce,fond_signatura,portal,url,forma,text_url,jazyk,poznamka,overeno`
   - `typ`: kronika-obecni | kronika-skolni | kronika-farni | kronika-spolkova | pametni-kniha | noviny | zpravodaj |
     uredni-kniha | skolni | scitani | pozemkova-kniha | mapa | jine
   - `forma`: **sken** (jen obrázky) | **sken+ocr** (obrázky a strojový text, hledatelný) | **text** (přepis / edice / digitálně
     vzniklý text) | **katalog** (jen záznam, bez digitalizátu) — rozhoduje, co je skutečně **online**
   - `text_url`: kde je text (fulltext, ALTO, PDF s textovou vrstvou), jinak prázdné
   - `overeno`: `ano` (otevřeno a viděno) | `katalog` (jen v katalogu) | `ne` (nepřímý údaj)
2. `docs/prameny/digitalizovane/<oblast>.md` — krátký přehled: co oblast má / nemá, nejcennější prameny, mezery,
   doporučení (kde je text = rychlé fulltextové hledání příjmení).
3. Nic nevymýšlet; URL a období jen z portálu. Nenalezeno taky zapsat (řádek `forma: katalog` / poznámka „online nenalezeno“).

Necommituj. Hotovo: `herdr agent prompt manager "prameny-<oblasti>: hotovo — <shrnutí>"`.
