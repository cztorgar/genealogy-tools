# Zadání: historické mapy Žiželic a lokalizace čísel popisných

Cíl: doplnit místopis Žiželic (`README.md` v této složce) o **historické mapy** a připravit podklad,
abychom mohli na mapě ukázat, **kde kdo žil** (osoba → číslo popisné v daném roce → poloha domu).
Obecný podklad bez osobních dat — jen mapy, místa a čísla popisná.

## 1. Katalog map (`mapy.md`)

Pro katastrální území Žiželice a osady fary (Končice, Hradišťko II, Loukonosy, Kundratice, Zbraň,
Převýšov…) najdi a popiš:

- **Stabilní katastr:** císařský povinný otisk (ČÚZK — archivnimapy.cuzk.gov.cz / ags.cuzk.gov.cz/archiv)
  a **indikační skica** (NA — bývají v nich čísla popisná a jména držitelů); rok mapování (~1840),
  měřítko 1 : 2880, čísla mapových listů / kód k. ú., přímé odkazy.
- **Vojenská mapování:** 1. (josefské), 2. (františkovo, ~1840–1850), 3. (~1877–1880) — mapire.eu,
  oldmaps.geolab.cz (Laboratoř geoinformatiky UJEP), listy a odkazy.
- **Historické ortofoto** (ČÚZK, ~1950) a **současná katastrální mapa / RÚIAN**.
- Další: mapy velkostatku Chlumec, plány obce, staré pohlednice/plány v Krameriovi, pokud najdeš.
- U každé mapy: rok, měřítko, co na ní je (čp.? jména?), licence/podmínky užití, a **zda je použitelná
  jako mapová vrstva** (WMS / WMTS / XYZ dlaždice — URL služby a název vrstvy), nebo jen jako obrázek
  ke stažení (a zda by šla georeferencovat).

## 2. Čísla popisná → poloha (`cisla-popisna.md` + strojově)

- Současné adresní body Žiželic z **RÚIAN** (otevřená data ČÚZK): čp. → souřadnice (WGS84),
  část obce. Ulož strojově do `mcp/czech-archives/gazetteer/zizelice-cp.csv`
  (`cast_obce,cp,lat,lon,zdroj`).
- **Přečíslování:** zjisti, zda a kdy se v Žiželicích a osadách čísla popisná měnila (konskripční číslování
  1770–71, přečíslování v 19. století, změny po sloučení obcí 1964) a jak historické čp. převést na dnešní
  (srovnání indikační skici ~1840 se současnou mapou; sčítací operáty v ARONu mají čp. po letech).
- Popiš postup, jak u konkrétního historického čp. najít polohu (které mapy, v jakém pořadí).

## 3. Návrh mapové vizualizace (krátce)

Navrhni, jak ve workbenchi zobrazit „kde kdo žil“: např. statická stránka v `web/` s Leaflet/MapLibre,
podkladové vrstvy (současná + historické), body čp. z CSV a vrstva osob (ze stromu — osoba, rok, čp.,
pramen). Jen návrh a seznam vrstev s URL, implementace později.

## Pravidla

- Šetrně (rychlostí člověka), žádné hromadné stahování mapových dlaždic.
- U tvrzení jistota **doloženo / pravděpodobně / neověřeno** + zdroj (URL).
- Žádná osobní data ze stromu.
- Výstupy do této složky (`mapy.md`, `cisla-popisna.md`) a `mcp/czech-archives/gazetteer/zizelice-cp.csv`;
  doplň odkaz do `README.md` (sekce Mapy) a `docs/mistopis/README.md`.

Necommituj — až budeš hotový: `herdr agent prompt manager "mistopis-zizelice-mapy: hotovo — <shrnutí>"`.
