# Zadání: místopis — přesné určení adres (čísla popisná) na Chlumecku a Vápensku

Cíl: aby každá adresa, která se ve stromu vyskytuje (obec + č. p.), šla **přesně umístit** — dnes i historicky —
a ukázat na mapě v dashboardu („kde kdo žil“). Navazuje na `docs/mistopis/zizelice/cisla-popisna.md` (vzor) a
`docs/mistopis/chlumecko/obce.md`.

## Co dnes chybí (rozbor patchů stromu 2026-10-17, obecně bez osob)

Obec je v místopisu, ale **čísla popisná nejsou v gazetteeru** (`mcp/czech-archives/gazetteer/*-cp.csv` má jen fara Žiželice + Převýšov):

| Obec | č. p. ve stromu | Poznámka |
|---|---|---|
| **Chlumec nad Cidlinou** (město) | 6, 40, 66 (+ „66/III“) | městské čtvrti I–IV s vlastní řadou č. p. — vyřešit číslování po čtvrtích; „Chlumec 40“ v patchích je patrně Kladruby 40 (část města) |
| **Kladruby** (č. o. Chlumce) | 40 | |
| **Lučice** (č. o. Chlumce) | 6 | obec 1850–1985; historické vazby na Převýšov, Olešnici, Levín, Loukonosy |
| **Převýšov** | (v CSV 143 č. p. z RÚIAN) | **prohloubit historii**: přečíslování, osady, stav v 19. stol. — dnes jen dnešní body |
| **Strašov** | 27, 39, 40 | fara Vápno; stará vs. dnešní čísla |
| Vápno | 6, 18, 27, 39, 40 | |
| Komárov | 8, 18 | |
| Vlkov nad Lesy (č. o. Běrunic) | 4 | |
| Písek (u Chlumce) | 15 | |
| Tetov | 5 | fara Žiželice |
| Chudeřice | 33 | |
| Olešnice / Volešnice | 14 | ověřit, že jde o tutéž obec (zápis „Volešnice“) |

Obec **není v místopisu vůbec**: **Újezd u Přelouče** (zápis „Oujezd č. 27“ — sjednotit s řádkem „Újezd (u Přelouče)“ v
obce.md, ať se páruje) a **Hradec Králové** (dva sňatky 1921 — zjistit, ve které farnosti/úřadu se 1921 oddávalo,
když snoubenci byli z Chlumecka: vojenská duchovní správa? civilní sňatek u okresní politické správy po 1919?).

Priorita uživatele: **Chlumec, Převýšov, Lučice, Strašov**; pak ostatní z tabulky.

## Co udělat

1. **Dnešní stav (RÚIAN):** pro každou obec/část obce stáhnout adresní místa (CSV obce z vdp.cuzk.gov.cz, jako u Žiželic),
   převést S-JTSK → WGS84, zapsat do `mcp/czech-archives/gazetteer/<oblast>-cp.csv` (`cast_obce,cp,lat,lon,zdroj`;
   názvy `cast_obce` přesně jako v obce.md / v patchích — Chlumec po čtvrtích např. „Chlumec nad Cidlinou I“).
2. **Historie číslování:** kdy a jak se přečíslovávalo (konskripce 1770/71, 1805, přečíslování ve 20. stol., čtvrti
   Chlumce), jak číslo z matriky 19. stol. převést na dnešní. Zdroje: stabilní katastr (indikační skici, ~1840),
   císařské otisky, sčítací operáty 1869–1921 (ARON, mají č. p. a jména), pozemkové knihy, obecní kroniky, Profous,
   literatura. Výsledek do `docs/mistopis/chlumecko/cisla-popisna.md` (po obcích; tabulka staré č. p. → dnešní, kde to jde;
   jistota doloženo/pravděpodobně/neověřeno).
3. **Mapy:** doplnit `docs/mistopis/chlumecko/mapy.md` a `tools/mapy/vrstvy.yml` o stabilní katastr / císařské otisky pro
   tyto katastry (ČÚZK archiv, Archivní mapy), aby šly v dashboardu podložit.
4. **obce.md:** doplnit chybějící obce (Újezd — sjednotit název; Hradec Králové jen jako místo sňatků, s vysvětlením),
   u Lučic, Strašova, Převýšova prohloubit dějiny osady (příslušnost, fara, panství, změny názvů).

## Pravidla

- Obecný místopis, **žádná osobní data** do workbenche (ani jména ze stromu; č. p. bez osob jsou v pořádku).
- Portály šetrně (≈ 2,5 s, cache, žádné hromadné stahování snímků). RÚIAN CSV je otevřená data.
- Nic nevymýšlet; zdroj u každého údaje.
- Necommituj. Hotovo: `herdr agent prompt manager "mistopis-adresy: hotovo — <shrnutí>"`.
