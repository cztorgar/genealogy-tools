# Chlumecko — čísla popisná a jejich poloha

Rešerše 2026-10-17. Obecný podklad bez osobních dat. Jistota: **doloženo** / **pravděpodobně** /
**neověřeno**, jako v [README](README.md). Vzor a obecný postup: [Žiželice](../zizelice/cisla-popisna.md).
Mapové podklady: [mapy.md](mapy.md).

Strojově: [`mcp/czech-archives/gazetteer/chlumecko-cp.csv`](../../../mcp/czech-archives/gazetteer/chlumecko-cp.csv)
(`cast_obce,cp,lat,lon,zdroj`). Převýšov je už v `zizelice-cp.csv` (fara Žiželice), sem se neduplikuje.

---

## 1. Dnešní stav (RÚIAN)

Zdroj: otevřená data RÚIAN, adresní místa obcí ve formátu CSV, stav k **30. 9. 2026**, licence
CC BY 4.0 (ČÚZK). Soubory `https://vdp.cuzk.gov.cz/vymenny_format/csv/20260930_OB_<kód obce>_ADR.csv.zip`:

| Obec | kód obce | části obce převzaté do CSV |
|---|---|---|
| Chlumec nad Cidlinou | 570109 | Chlumec nad Cidlinou I–IV, Kladruby, Lučice, Pamětník |
| Strašov | 575763 | Strašov |
| Vápno | 575933 | Vápno |
| Kladruby nad Labem | 575178 | Komárov, Kolesa, Bílé Vchynice (**ne** část Kladruby nad Labem — jmenovec Kladrub u Chlumce) |
| Běrunice | 537021 | Vlkov nad Lesy |
| Písek | 570575 | Písek |
| Tetov | 575810 | Tetov |
| Chudeřice | 570125 | Chudeřice |
| Olešnice | 570524 | Olešnice, Levín |
| Újezd u Přelouče | 575909 | Újezd u Přelouče |

Převod S-JTSK (EPSG:5514) → WGS84 jako u Žiželic (pyproj 3.7, výchozí transformace, přesnost ~1 m);
bod adresního místa leží u vchodu nebo v budově. Do CSV jen **č. p.**; evidenční čísla vynechána.
Žádné č. p. neměla víc adresních míst. Chudeřice č. p. 80 je v RÚIAN **bez souřadnic**, v CSV chybí.
Přiřazení ke k. ú. spočítáno průnikem bodů s hranicemi k. ú. z RÚIAN (vrstva 7) a sedí beze zbytku.
**Doloženo.**

| Část obce (= `cast_obce` v CSV) | K. ú. (kód) | č. p. | Rozsah | Ev. č. (vynechána) |
|---|---|---|---|---|
| Chlumec nad Cidlinou I (město) | Chlumec nad Cidlinou (651800) | 195 | 1–207 | — |
| Chlumec nad Cidlinou II (Hradecké předměstí) | Chlumec nad Cidlinou (651800) | 81 | 1–85 | 1 |
| Chlumec nad Cidlinou III (Kolínské předměstí) | Chlumec nad Cidlinou (651800) | 385 | 1–402 | 42 |
| Chlumec nad Cidlinou IV (Pražské předměstí) | Chlumec nad Cidlinou (651800) | 891 | 1–923 | 60 |
| Kladruby | **Chlumec nad Cidlinou** (651800) | 95 | 3–91, pak novostavby 108–154 | 1 |
| Lučice | Lučice u Chlumce nad Cidlinou (688291) | 88 | 1–93 | 1 |
| Pamětník | Pamětník (717533) | 71 | 1–72 | 3 |
| Strašov | Strašov (756318) | 132 | 1–133, 155, 161, 171 | — |
| Vápno | Vápno u Přelouče (776955) | 60 | 1–67 | — |
| Komárov | Komárov u Přelouče (668702) | 35 | 1–39 | — |
| Kolesa | Kolesa (668079) | 50 | 1–50 | 2 |
| Bílé Vchynice | Bílé Vchynice (604143) | 70 | 1–73 | 11 |
| Vlkov nad Lesy | Vlkov nad Lesy (603171) | 60 | 1–62 | 1 |
| Písek | Písek u Chlumce nad Cidlinou (720917) | 135 | 1–140 | 2 |
| Tetov | Tetov (766968) | 98 | 1–101 | 10 |
| Chudeřice | Chudeřice (654787) | 100 | 1–101 | — |
| Olešnice | Olešnice nad Cidlinou (710351) | 123 | 1–130 | 14 |
| Levín | Levín nad Cidlinou (710342) | 38 | 1–38 | — |
| Újezd u Přelouče | Újezd u Přelouče (773689) | 99 | 1–104 | — |

Celkem 2 806 č. p. Volná čísla v řadách jsou ve skriptu výstupu, pro výzkum nejsou podstatná: číslo,
které dnes chybí, mohlo v 19. stol. existovat (zbořený dům).

**Chlumec má čtyři samostatné řady č. p.** (I–IV) a další vlastní řady mají Kladruby, Lučice a
Pamětník. Samotné „Chlumec č. 40“ je tedy **nejednoznačné** — čtyři různé domy ve městě (a další
v Kladrubech, Lučicích, Pamětníku). U adresy z Chlumce je vždy třeba zjistit čtvrť (v pramenech
„město“, „Hradecké / Kolínské / Pražské předměstí“, později římská číslice: „66/III“, „33/II“,
„42-I“). **Doloženo** (RÚIAN; sčítání níže).

---

## 2. Historie číslování: co se ví

### 2.1 Obecně

Konskripce 1770/71, vlna přečíslování ~1805 (hlavně města), přidávání nových čísel na konec řady
a předělování čísel zbořených domů: viz [Žiželice, kap. 2](../zizelice/cisla-popisna.md#2-přečíslování-co-se-ví).
Pro Chlumecko nic konkrétního navíc jsem nenašel (web, cs.wiki, vyhledávání — **nenalezeno**).

### 2.2 Sčítací operáty 1869–1921 (rozsahy č. p.)

Zdroj: SOkA Hradec Králové, fond **Okresní úřad Nový Bydžov**, popisy jednotek v ARONu
(`find_registers`, druh S), stav 2026-10-17. Rozsahy jsou tak, jak je uvádí popis; „bez X“ =
číslo v řadě vynechané. Odkaz na jednotku: `https://aron.vychodoceskearchivy.cz/apu/<id>`.
**Doloženo** (katalog ARON).

| Část | 1869 | 1880 | 1890 | 1900 | 1910 | 1921 | dnes |
|---|---|---|---|---|---|---|---|
| Chlumec, 1. čtvrť – město | 1–99 (bez 24, 32, 38, 65, 75, 92) | 1–102 | 1–104 | 1–104 | 1–110 | 1–111 | 1–207 |
| Chlumec, 2. čtvrť – Hradecké předm. | 1–58 (bez 23) | 1–59 | 1–59 | 1–61 | 1–64 | 1–65 („čp. 36 viz 62, 62 viz 36“) | 1–85 |
| Chlumec, 3. čtvrť – Kolínské předm. | 1–73 | 1–73 | 1–74 | 1–75 | 1–150 | 1–172 | 1–402 |
| Chlumec, 4. čtvrť – Pražské předm. | 9–128 (bez 1–8, 12, 13, 40, 68, 102) | 1–144 | 1–148 | 1–158 | 1–235 (bez 67, 228) | 1–270 (bez 261) | 1–923 |
| Kladruby | 1–21 | 1–23 | 1–23 | 1–31 | 1–40 | 1–42 (bez 26) | 3–154 |
| Lučice | 1–40 | 1–43 | 1–46 (bez 27) | 1–50 | 1–59 | 1–67 (bez 47, 58, 59) | 1–93 |
| Pamětník | 1–35 | 1–37 | 1–38 | 1–43 | 1–49 (bez 9, 20) | 1–50 (bez 9, 20, 39) | 1–72 |
| Strašov | 1–51 | 1–64 | 1–66 | 1–70 | 1–79 | 1–80 (bez 6) | 1–133 (+3) |
| Vápno | 1–37 | nenalezeno | 1–40 | 1–44 | 1–48 | 1–50 (bez 39) | 1–67 |
| Komárov | 1–27 | 1–27 | 1–28 | 1–28 | 1–29 | 1–31 | 1–39 |
| Písek | 1–47 | nenalezeno | 1–65 | 1–67 (bez 33, 36) | 1–75 | 1–77 (bez 31) | 1–140 |
| Olešnice | nenalezeno (asi pod Lučicemi) | nenalezeno | 1–37 | nenalezeno | 1–52 | 1–57 („15 viz 13, 55 viz 32“) | 1–130 |
| Levín | nenalezeno | 1–17 | — | — | — | 1–18 | 1–38 |
| Újezd (u Přelouče) | nenalezeno | nenalezeno | 1–45 | 1–47 | nenalezeno | 1–56 (bez 6) | 1–104 |
| Chudeřice | 1–14 | 1–25 | 1–25 | 1–25 | 1–31 | 1–31 | 1–101 |
| Tetov | 1–40 | 1–46 | 1–47 | 1–52 | 1–65 | 1–69 (bez 64) | 1–101 |
| Převýšov | 1–55 | 1–65 | 1–67 | 1–67 (bez 34, 56) | 1–76 | 1–84 (bez 35, 56; „68 viz 31“) | 1–145 |

Chlumec 1869–1921: jednotky inv. 1007–1010 (1869), 1088–1091 (1880), 1171–1174 (1890), 1260–1263
(1900), 1353–1356 (1910), 1450–1452 a poř. 689–690 (1921). Lučice/Kladruby/Pamětník: poř. 61/62/66
(1869), 203/204/207 (1880), 330/331/334 (1890), 463/464/465 (1900), 597/598/599 (1910), 728/729/730
(1921). Strašov: inv. 1062, 1144, 1231, 1324, 1419, 1518. Ostatní id viz katalog ARON nebo
`gazetteer/chlumecko.yml` (oddíl `census`).

**Pozor, jmenovci v katalogu:** „Komárov“ 1921 v SOkA Pardubice (čp. 1–60) a v okrese Dvůr Králové
není náš Komárov; „Olešnice“ v okresech Rychnov, Náchod, Trutnov také ne; „Újezd“ je v ARONu
desetkrát. Náš Komárov a Újezd jsou jen ve fondu OÚ Nový Bydžov.

Vlkov nad Lesy patřil k okresu Poděbrady (viz [obce.md](obce.md)), jeho sčítání by bylo v SOkA
Nymburk (SOA Praha) — **nehledáno**.

### 2.3 Co z toho plyne

| Zjištění | Jistota |
|---|---|
| **Chlumec měl čtyři čtvrti s vlastní řadou č. p. už v roce 1869.** Dnešní I–IV jim odpovídají (město, Hradecké, Kolínské, Pražské předměstí). | **doloženo** (popisy operátů 1869–1921 + RÚIAN) |
| Kdy čtvrťové řady vznikly (1770, kolem 1805, nebo až v 19. stol.): **nevím.** Test viz 2.4. | **neověřeno** |
| Pražské předměstí 1869 začíná až čp. 9 a 1880 už má 1–144: buď v operátu 1869 chybí list (domy 1–8), nebo se mezi 1869 a 1880 číslovalo nově. | **neověřeno** — otevřít operát inv. 1010 a 1091 |
| Ve vesnicích (Lučice, Kladruby, Pamětník, Strašov, Vápno, Komárov, Písek, Tetov, Chudeřice, Převýšov) řady 1869–1921 jen **rostou na konci** a drobně se vyprazdňují. Nic nenaznačuje hromadné přečíslování mezi 1869 a dneškem. | **pravděpodobně** (rozsahy navazují; že tentýž dům má totéž číslo, z rozsahů dokázat nejde) |
| Kladruby: dnes chybí čp. 1 a 2, které 1869–1921 existovaly (zaniklé domy). Řada 108–154 jsou novostavby po 1921. | doloženo (rozsahy) / pravděpodobně (výklad) |
| Čísla, která v roce X ještě nebyla (např. Strašov > 51 před 1869, Lučice > 40), u záznamu z té doby znamenají chybu čtení nebo jinou obec. | **pravděpodobně** — dobrý test na jmenovce |
| Sčítání 1921 zná u několika obcí dvojice „čp. A viz čp. B“ (Chlumec II 36/62, Pražské předm. 60/58, 107/83, Olešnice 15/13, 55/32, Převýšov 68/31) — sloučené nebo zaměněné domy. | **doloženo** (katalog); význam neověřen |

### 2.4 Jak přečíslování otestovat (bez osob ve workbenchi)

Postup jako u Žiželic: najít několik domácností, které se v matrice opakují před a po předpokládaném
zlomu, a sledovat, zda se jim číslo mění **hromadně**. Konkrétně:

1. **Chlumec ~1805:** N Chlumec 55-3 (1801–1814) — mění se kolem 1805 čísla domů na předměstích?
   Píše farář čtvrť („Pražské předm. č.“), nebo jen „Chlumec č.“?
2. **Chlumec 1869/1880, Pražské předměstí:** operáty inv. 1010 a 1091 — sedí čp. 9–30 na tytéž
   domácnosti?
3. **Vesnice:** stačí porovnat operát 1869 s matrikou 1860–1870 v jedné obci (Strašov, Lučice).

Výsledek patří do `research/` stromu; sem jen závěr s odkazem.

---

## 3. Mapy stabilního katastru pro tyto obce (1841)

Všechny katastrální obce těchto obcí mají **císařský povinný otisk z roku 1841** (Bydžovský kraj).
Údaje z aplikace Archiv ČÚZK (`https://ags.cuzk.gov.cz/archiv/`, klik do mapy → „Císařské povinné
otisky“; vrstva `Archiv/klady/MapServer/3`), dotazy 2026-10-17. Tabulka s listy: [mapy.md, oddíl 1](mapy.md#1-stabilní-katastr--císařské-povinné-otisky-12880).
**Doloženo.**

Pro adresy je důležité, že **katastrální obec 1841 ≠ dnešní k. ú.**:

| Dnešní část / bod | k. o. 1841 (mapa) | Dnes k. ú. |
|---|---|---|
| Kladruby (čp. 3 i čp. 40) | **Lučice** (4287) | Chlumec nad Cidlinou |
| Pamětník (čp. 1 i čp. 30) | **Lučice** (4287) | Pamětník |
| Chlumec I–IV | Chlumec (2525) | Chlumec nad Cidlinou |
| Tetov, Bílé Vchynice | **Kundratice** (3698) | Tetov, Bílé Vchynice |
| Komárov čp. 8 | Komárov (3300) | Komárov u Přelouče |
| Komárov čp. 1 | **Kolesa** (3279) | Komárov u Přelouče |

Indikační skici (s čp. a jmény držitelů) hledej tedy pro Kladruby a Pamětník pod **Lučicemi**, pro
Tetov pod **Kundraticemi**. **Doloženo** (polohy bodů); že skica Lučic zachycuje i domy Kladrub a
Pamětníku, je **pravděpodobné** (stejný list otisku) — ověřit na skice.

---

## 4. Postup: historické čp. → poloha domu

Stejný jako u [Žiželic, kap. 3](../zizelice/cisla-popisna.md#3-postup-historické-čp--poloha-domu),
s doplňky pro Chlumecko:

1. **Chlumec:** nejdřív určit čtvrť. Bez ní nelze dům umístit. V CSV je `cast_obce` „Chlumec nad
   Cidlinou I“ … „IV“.
2. **Kladruby, Pamětník, Tetov:** indikační skicu a otisk brát z k. o. Lučice, resp. Kundratice
   (kap. 3).
3. **Kontrola rozsahem** ze sčítání (kap. 2.2): číslo vyšší než nejvyšší čp. v nejbližším sčítání
   před událostí je podezřelé.
4. **Dnešní bod** z `chlumecko-cp.csv` je jen „stejné číslo dnes“. Pro 19. stol. je to **pravděpodobně**
   tentýž dům u vesnic s navazující řadou, ve městě s výhradou (přestavby, předělená čísla).

---

## 5. Poznámky k adresám ve stromu (obecně, bez osob)

| Zápis v patchích | Výklad | Jistota |
|---|---|---|
| „Chlumec nad Cidlinou, část Kladruby č. p. 40“ | Kladruby čp. 40 (Kladruby jsou částí Chlumce od 1955). V CSV `Kladruby,40`. | doloženo (správní vývoj, RÚIAN) |
| „Chlumec n. C. č. 66-III“, „č. p. 66/III“ | Chlumec nad Cidlinou III (Kolínské předm.) čp. 66 | doloženo (systém čtvrtí) |
| „Chlumec n. C. č. p. 66/II“ | **rozpor s 66/III** — buď chyba zápisu, nebo jiný dům (II čp. 66 dnes existuje). Neřešit mlčky, ověřit na snímku. | neověřeno |
| „Volešnice č. 14“ | Olešnice (u Chlumce, k. ú. Olešnice nad Cidlinou) čp. 14. Císařský otisk 1841 uvádí k. o. „Wolleschnitz (Wollessnice)“; kontext Lučice / fara Chlumec. | **doloženo** (název k. o. 1841) |
| „Oujezd č. 27“ | Újezd u Přelouče čp. 27 (fara Vápno). V CSV `Újezd u Přelouče,27`. | pravděpodobně (fara Vápno; jmenovců Újezd je mnoho) |
| „Tetov (Tetava) č. 5“ | Tetov čp. 5; 1841 v k. o. Kundratice | doloženo |

**Pro dashboard (manager):** adresa „Chlumec nad Cidlinou č. p. 66/III“ musí jít na
`cast_obce` „Chlumec nad Cidlinou III“. Dnešní `foldPlace` v `tools/dashboard/static/map.js`
navíc odřezává koncové „ II“ (kvůli Hradišťku II), takže „Chlumec nad Cidlinou II“ splyne s obcí
„Chlumec nad Cidlinou“ a adresa bez čtvrti by se tiše umístila do Hradeckého předměstí. Návrh:
čtvrť brát z římské číslice za čp. a bez ní umístit jen na střed obce.

---

## Otevřené otázky

1. Kdy vznikly čtvrťové řady Chlumce (test 2.4/1).
2. Pražské předměstí 1869 bez čp. 1–8: chybějící list, nebo přečíslování 1869–1880 (test 2.4/2).
3. Vápno a Písek 1880, Újezd 1869/1880/1910, Olešnice 1869/1880/1900: operáty nenalezeny vyhledáním
   podle jména — možná pod jinou obcí (Olešnice pod Lučicemi do 1886, Újezd se Štítem).
4. Sčítání Vlkova (okres Poděbrady, SOkA Nymburk) nehledáno.
5. Historický lexikon obcí ČSÚ (počty domů po částech) nestažen — stejně jako u Žiželic.
