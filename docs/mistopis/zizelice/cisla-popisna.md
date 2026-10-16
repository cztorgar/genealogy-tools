# Žiželice — čísla popisná a jejich poloha

Rešerše 2026-10-16. Obecný podklad bez osobních dat. Jistota: **doloženo** / **pravděpodobně** /
**neověřeno**, jako v [README](README.md). Mapové podklady: [mapy.md](mapy.md).

Strojově: [`mcp/czech-archives/gazetteer/zizelice-cp.csv`](../../../mcp/czech-archives/gazetteer/zizelice-cp.csv)
(`cast_obce,cp,lat,lon,zdroj`).

---

## 1. Dnešní stav (RÚIAN)

Zdroj: otevřená data RÚIAN, adresní místa obce ve formátu CSV, stav k **30. 9. 2026**. ČÚZK je
poskytuje pod licencí CC BY 4.0.

- Žiželice (obec 533947): https://vdp.cuzk.gov.cz/vymenny_format/csv/20260930_OB_533947_ADR.csv.zip
- Převýšov (obec 570681, dnes okres Hradec Králové, patřil k faře Žiželice): https://vdp.cuzk.gov.cz/vymenny_format/csv/20260930_OB_570681_ADR.csv.zip

Souřadnice adresního místa jsou v S-JTSK (EPSG:5514). Do WGS84 je převedl pyproj 3.7 (PROJ,
výchozí transformace S-JTSK → WGS84), přesnost je zhruba 1 m. Bod adresního místa obvykle leží u
vchodu nebo uvnitř budovy, nebývá to těžiště domu. Do CSV jsem vzal jen **č. p.** Vynechal jsem
9 evidenčních čísel (rekreační stavby: Loukonosy ev. 9, 57, 84; Zbraň ev. 6, 8; Žiželice ev. 121,
201, 419; Kundratice ev. 24). U 4 čísel popisných je víc adresních míst (orientační čísla), v CSV
zůstalo jen první.

| Část obce | K. ú. (kód) | Počet č. p. | Rozsah | Volná čísla v řadě (dnes nepřidělená) |
|---|---|---|---|---|
| Žiželice | Žiželice nad Cidlinou (797481) | 410 | 1–432 | 37, 42, 79, 80, 121, 140, 144, 156, 158, 201, 210, 291, 292, 327, 329, 357, 412, 414, 419, 425, 430, 431 |
| Končice | Končice (797448) | 99 | 1–101 | 53, 96 |
| Zbraň | **Končice** (797448) | 24 | 1–27 | 6, 8, 9 |
| Hradišťko II | Hradišťko II (797430) | 80 | 1–82 | 30, 32 |
| Loukonosy | Loukonosy (797464) | 85 | 1–89 | 8, 9, 57, 84 |
| Pod Vinicí | **Loukonosy** (797464) | 41 | 450–510 | (řada začíná až od 450) |
| Kundratice | Kundratice u Žiželic nad Cidlinou (797456) | 25 | 1–30 | 13, 15, 16, 18, 24 |
| Převýšov | Převýšov (735299) | 143 | 1–145 | 28, 59 |

Celá tabulka je **doložená** (RÚIAN). Přiřazení ke k. ú. jsem spočítal průnikem bodů s hranicemi
k. ú. z RÚIAN a sedí beze zbytku. Zbraň nemá vlastní katastr, leží v k. ú. Končice, a proto ji
v mapách stabilního katastru hledej na listech Končic. **Doloženo.**

Každá část obce má **vlastní číselnou řadu** od 1. Sloučením obcí v roce 1964 (Hradišťko II,
Loukonosy) se tedy čísla do jedné řady obce nesjednotila. **Doloženo** pro dnešní stav. Že se
v roce 1964 nepřečíslovávalo vůbec, je jen **pravděpodobné**, přímý doklad jsem nenašel.

Řada Pod Vinicí začíná od 450, dřív v ní žádná čísla nejsou. Je to novodobá část obce a
v matrikách 1798–1949 se nevyskytuje (viz README). **Pravděpodobně.**

---

## 2. Přečíslování: co se ví

| Období | Co se dělo | Platí pro Žiželice? | Jistota a zdroj |
|---|---|---|---|
| 1770–1771 | První číslování domů při konskripci (patent z 10. 3. 1770). Čísla se zapisují do matrik zhruba od té doby | ano, obecně | **doloženo** obecně: [cs.wiki Číslo popisné](https://cs.wikipedia.org/wiki/Číslo_popisné); [Familia Austria (PDF)](https://blog.familia-austria.at/images/inhalte/datensammlung/oeffentlich/Tschechien_Identifizierung_eines_Hauses_anhand_der_Konskriptionsnummer.pdf). Pro Žiželice to nemůžu ověřit, protože matriky před 1798 se nedochovaly |
| 1804/1805–1815 | „První vlna přečíslování“, hlavně ve městech. Na vesnicích jen výjimečně | **nevím.** Žiželice byly městečko, takže to vyloučit nejde | **pravděpodobně** (sekundární texty bez pramene: cs.wiki; [Rod Nebeských a Čackých](https://www.rod-nebeskych-a-cackych.cz/l/oznacovani-domu/); [fórum genealogie.taby.cz](https://genealogie.taby.cz/viewtopic.php?f=16&t=23669)) |
| po 1805 | Vesnice většinou drží čísla z 1770–71, nová čísla se přidávají na konec řady. Čísla zbořených domů se později často přidělují novostavbám | pravděpodobně ano | **pravděpodobně** (cs.wiki). Pozor: číslo zbořeného domu může dnes stát jinde |
| 1869 | Sčítání: Žiželice čp. **1–305** (sčítací operát, SOkA Hradec Králové, fond OÚ Nový Bydžov, inv. č. 1075) | ano | **doloženo**: [docs/archivy/aron-zamrsk.md](../../archivy/aron-zamrsk.md), sekce „Případ Žiželice“ |
| 1964 | Sloučení Hradišťka II a Loukonos se Žiželicemi (14. 6. 1964) | každá část si nechala vlastní řadu (viz výše) | **pravděpodobně** |
| dnes | Žiželice 1–432 (410 přidělených čísel) | | **doloženo** (RÚIAN) |

Konkrétní zmínku o přečíslování v Žiželicích nebo v osadách jsem **nenašel** (web obce,
vyhledávání). Pramenem by mohla být pamětní kniha obce (SOkA Kolín) nebo vyhlášky okresního úřadu
Nový Bydžov (SOkA Hradec Králové).

**Pozor na zdroj Familia Austria:** píše, že od roku 1860 se přešlo na „orientační čísla
(č. ev.)“. To plete dvě věci, orientační číslo (č. o.) a evidenční číslo (č. ev.). Na vesnicích se
orientační čísla zaváděla až s ulicemi a v Žiželicích dnes skoro nejsou.

### Jak přečíslování v Žiželicích otestovat

Test jde udělat bez cizího pramene, jen z matrik, které už máme:

1. **Kolem roku 1805.** Svazek N I (Žiželice 01, 1798–1816) pokrývá dobu před vlnou i po ní. Vyber
   několik domácností, které se v letech 1798–1804 i 1806–1816 opakují (stejný otec, stejné
   povolání). Pokud se jim kolem roku 1805 **hromadně** změní číslo domu, šlo o přečíslování. Pokud
   se změní jen jednotlivě, jde o stěhování.
2. **Kolem roku 1869.** Porovnej čísla v matrikách 1860–1880 se sčítacím operátem 1869 (po čp.,
   ARON). Když v operátu sedí čp. s matrikou, řada se tehdy neměnila.
3. **Kolem roku 1964.** Porovnej sčítání 1921 a matriky 1930–1949 s dnešním RÚIAN. Rozsahy řad
   (Hradišťko II 1–82, Loukonosy 1–89) by měly navazovat.

Výsledek patří do `research/` stromu, ne sem, protože pracuje s osobami. Sem stačí přenést závěr
(„v roce X přečíslováno / nepřečíslováno“) s odkazem na doklad.

---

## 3. Postup: historické čp. → poloha domu

Pořadí map podle toho, jak blízko mají k historickému čp. a jak přesně jsou umístěné:

1. **Zjisti, které číslování v daném roce platí** (kap. 2). Do roku 1805 počítej s možností
   jiné řady.
2. **Indikační skica stabilního katastru (~1840–1843).** Mapa 1 : 2 880, na které jsou
   u stavebních parcel **čísla popisná** a ve sloupcích **jména držitelů**. Uložení: Národní
   archiv, fond Stabilní katastr – indikační skici (Čechy), viz [mapy.md](mapy.md#2-stabilní-katastr).
   Tady se historické čp. najde přímo.
3. **Císařský povinný otisk (téhož roku, stejný list).** Na otisku čp. nejsou, je ale barevný a
   ČÚZK ho má **georeferencovaný** v mozaice. Dům ze skici se na něj přenese podle tvaru parcel.
   Tím se dostane do souřadnic.
4. **Překryv s dnešní katastrální mapou a ortofotem** (vrstvy `km`, `orto_dnes` a `orto1950`
   z [mapy.md](mapy.md)). Většina návesních parcel má tvar zachovaný dodnes. V roce 1954 je
   zástavba ještě skoro stejná jako v 19. století.
5. **Kontrola dnešním RÚIAN.** Najdi stejné čp. ve stejné části obce
   (`zizelice-cp.csv`). Když bod leží na téže parcele jako dům ze skici, je to „tentýž dům“
   (**pravděpodobně**, protože budova mohla být přestavěná). Když leží jinde, číslo bylo
   předěleno, nebo došlo k přečíslování.
6. **Mosty mezi lety.** Sčítací operáty 1869, 1880, 1890, 1900, 1910 a 1921 (ARON, po čp.) a
   pozemkový katastr a evidence nemovitostí 20. století (ÚAZK, mapy 1 : 2 880 s čp.) ukážou,
   kdy číslo na parcele zaniklo nebo kdy přibylo.

Výsledek u osoby zapisuj jako trojici **čp. + rok + pramen**. Polohu (parcelu, souřadnici) ber
jako odvozený údaj se stupněm jistoty, ne jako fakt z pramene.

---

## Otevřené otázky

1. Přečíslování kolem roku 1805 v Žiželicích: provést test v N I (kap. 2).
2. Historický lexikon obcí ČSÚ (počty domů 1869–2011 po částech obcí) jsem nestahoval. Tabulky po
   okresech nejsou na stránce produktu přímo vidět,
   https://csu.gov.cz/produkty/historicky-lexikon-obci-1869-az-2015 . Počty domů by ukázaly, jestli
   řady rostly souvisle.
3. Kdy vznikla část Pod Vinicí a proč má řadu od 450: dotaz na OÚ Žiželice.
