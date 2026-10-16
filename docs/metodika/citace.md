# Citace pramenů

Citace musí umožnit **kdokoli najít stejný záznam znovu**. Každý stažený snímek má v `sources/`
sidecar `.yml` se strukturovanou citací; text citace se z ní generuje.

## Matrika (vzor)

```yaml
type: matrika
archive: SOA Zámrsk               # archiv
fond: Sbírka matrik Východočeského kraje
parish: Chlumec nad Cidlinou      # farnost / matriční úřad
confession: řkt                   # řkt, ev. a. v., ev. h. v., izr. …
book: N                           # N / O / Z / I (index) / kombinovaná
years: 1850–1860
volume: "inv. č. 1234, sign. 41-7654"   # tak, jak uvádí portál
folio: "fol. 12v"                 # nebo strana
image: 18                         # číslo snímku v prohlížeči
url: https://aron.vychodoceskearchivy.cz/…
accessed: 2026-10-20
entry: "Luková č. 2, 3. 5. 1853, křest Jan"   # identifikace zápisu na stránce
```

Text: *SOA Zámrsk, Sbírka matrik Východočeského kraje, ř. k. f. ú. Chlumec nad Cidlinou, N 1850–1860,
inv. č. 1234, fol. 12v, snímek 18, zápis Luková č. 2 (3. 5. 1853). Online: <url>, cit. 20. 10. 2026.*

## Další typy

| Typ | Povinné prvky |
|---|---|
| sčítání lidu | archiv (SOkA), rok, obec, č. p., číslo archu / snímek |
| policejní přihláška Praha | NA, fond Policejní ředitelství Praha – konskripce, karton, folio, jméno hlavy rodiny |
| pozemková / gruntovní kniha | archiv, fond (velkostatek / soud), sign., folio, usedlost |
| katastr | NA / ČÚZK, katastr (tereziánský, josefský, stabilní), obec, číslo listu / parcely |
| kartotéka padlých / VÚA | VÚA, kartotéka, jméno, datum narození, odkaz |
| tisk (Kramerius) | titul, ročník, číslo, strana, digitální knihovna, UUID |
| cizí strom (nápověda) | služba, název stromu, autor, datum, URL — jistota 0 |
| ústní sdělení uživatele | „Ústní sdělení — Vojtěch Bereščák“, datum, kontext (session) — **jistota 3** |
| ústní sdělení třetí osoby / tradice | kdo, kdy, komu, v jaké souvislosti — jistota 1 (přímý svědek nedávné události 2) |

Citace v Gramps: Zdroj = matrika (svazek), Citace = konkrétní zápis (folio, snímek, jistota).
