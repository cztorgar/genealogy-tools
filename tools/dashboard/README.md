# Dashboard workbenche

Lokální stránka s živým přehledem stavu výzkumu nad stromem: rodokmen s barvou stavu u každé osoby,
odznaky (běžící session, čekající patch, nápovědy, todo, doklady), panel osoby s dossierem a vším k ní,
přehled session / patchů / sdílených seznamů / výzkumného logu, mapa „kde kdo žil“ a **fronta kontrol**
s rozhodováním a doložením údajů počtem nezávislých pramenů.

Není to výstup stromu (rodinný web) — je to vizualizace **workbenche**.

## Spuštění

```sh
uv run tools/dashboard/server.py                    # strom berescak, http://127.0.0.1:5056/
uv run tools/dashboard/server.py --tree <strom> --port 5056
uv run tools/dashboard/server.py --tree-dir /cesta/ke/stromu --gramps-url http://localhost:5055
```

Poslouchá jen na `127.0.0.1`. Závislost jen PyYAML (inline metadata pro `uv`). Frontend bez build kroku,
`marked` a `DOMPurify` z cdnjs s pevnou verzí. Odkaz na osobu: `http://127.0.0.1:5056/#<ID>`.

## Zásady

- **Žádná druhá kopie dat.** Server čte živé soubory stromu při každém požadavku (paměťová cache podle
  mtime). Stránka se dotazuje `/api/state` každých 5 s; když se změní verze (mtime souborů nebo stav
  session), překreslí strom i otevřený panel.
- **Jen čtení — s jedinou výjimkou:** rozhodnutí kontroly (viz níže). Jinak do stromu nic nezapisuje,
  necommituje, Gramps nevolá (jen odkaz `<gramps-url>/person/<gramps_id>`).
- `/api/file` vydá jen soubory uvnitř stromu (snímky, přepisy, sidecary jako text).

## Zdroje dat (`T = ../genealogy-trees/<strom>/`)

| Co | Odkud |
|---|---|
| osoby, stav, checklist, doklady, odloženo, log | `T/research/people/*.md` — front-matter `id`/`kekule`, `stav`, `gramps_id`; sekce `## Checklist`, `## Doklady k dohledání`, `## Odloženo`, `## Log hledání` |
| roky (orientačně) | `**narození:**` / `**úmrtí:**` v sekci nápověd, `manual.json` (`birth`) |
| osoby bez dossieru | `T/research/people/manual.json`; chybějící články řetězce ID jako prázdné rámečky |
| nápovědy | `T/research/hints/<ID>-*.md` |
| patche | `T/patches/P-<ID>-<nn>.yml` (`status`, `summary`); čeká = `navrženo` / `schváleno` |
| sdílené seznamy | `T/research/todo-*.md` — záznamy `## …` (se `stav:`) nebo řádky `- YYYY-MM-DD | …`; k osobě podle výskytu ID |
| prameny | sidecary `T/sources/**/*.yml` ve složce osoby nebo s osobou v `persons:`; snímky a přepisy |
| doklady (souhrn) | `T/research/doklady.md` |
| výzkumný log | `T/research/log.md` (posledních 25) |
| příběh | `T/research/pribehy/<ID>.md` (pravidla `docs/metodika/pribehy.md`) — nahoře v panelu osoby, ve stromu 📖 |
| kontext | sekce `## Kontext` dossieru — v panelu zvýrazněně pod příběhem |
| chybí kontext/příběh | front-matter `kontext: chybí` (`tools/research/kontext_flags.py`) — ve stromu šedé ∅📖, filtr „chybí kontext/příběh“, co přesně chybí (Kontext / příběh) dopočítá dashboard |
| závora | sekce `## Závora` dossieru (formát `docs/metodika/workflow-sessions.md`, oddíl Závora) — ve stromu ⛔ (šedé = „prolomeno YYYY-MM-DD“) s tooltipem kde/proč, v panelu červený rámeček, v přehledu seznam s filtrem podle typu. Typ = klíčová slova z „proč“ (nezachovány, nedigitalizováno, nenalezeno, nečitelné, nejistá totožnost, mimo dosah, rozpočet/kontext, nezkoumáno; víc typů najednou možné), šance = nejlepší z uvedených v „co by závoru prolomilo“ |
| původ osoby | front-matter `původ` dossieru — štítek v rohu rámečku: modrý **MH** (myheritage), zelený **★P** (pramen), oranžový **Ú** (ústně); filtr „původ“ v liště |
| kontroly | `T/research/kontroly/<ID>-<nn>.yml`, `G-<nn>.yml` |
| doložení údajů | události z aplikovaných patchů + sidecary citací |
| běžící session | `herdr agent list` — agent se jménem ve tvaru ID (`k0056`, `k0001-s2-p2`) nebo `vetev-*` (session větve) s cwd ve workbenchi/stromu |
| kořen větve | `T/research/vetve.yml` (`vetev-x: <ID kořene>`), jinak první ID v prvním promptu session (Claude transkript `~/.claude/projects/<cwd>/<agent_session>.jsonl`, čte se jen začátek) |

## Strom z ID

`K%04d` = Kekule (otec `2n`, matka `2n+1`); přípony `-S<n>` manžel/ka, `-C<n>` dítě, `-P1`/`-P2` rodiče.
Přímí předci tvoří pedigree (generace = sloupce, K0001 vlevo). Manželé a děti visí čárkovaně pod kotvou
ve stejném sloupci (∞ / d.); mají-li vlastní rodiče, dostanou pás pod rodokmenem kotvy a jejich
pedigree pokračuje doprava. Větve jdou sbalit (±, pamatuje si prohlížeč).

Volba **prázdní rodiče** ukáže u každého přímého předka s dossierem prázdné rámečky rodičů — kam se dá jít.
Odznak **⚑N** = otevřené kontroly osoby (červeně, je-li některá blokující). Filtr **údaje jen s 1 pramenem**
nechá osoby, které mají aspoň jednu událost doloženou jediným zápisem (u nich `①×N`).
Filtry: **jen rozpracované** (rozpracováno / pozastaveno / běží session), **čeká na mě**
(patch `navrženo` nebo session ve stavu idle/done).
Volba **jen předci** (pamatuje si prohlížeč) nechá jen přímou linii: Kekule `K…` a od kotvy vedlejší linie
(`K0001-S2`) řetězce `-P1`/`-P2`. Kotva `-S<n>` zůstane, jen když z ní předci vedou. Sourozenci (`-C`), další manželé
(`-S`) a jejich potomci se skryjí; počty stavů v liště, hledání a seznam závor berou totéž. Fronta kontrol ne.

## Mapa (záložka Mapa)

„Kde kdo žil“: výběr oblasti, podklad, posuvník roku (▶ přehrát, šipky ←/→, Shift = po 10 letech).
U čísel popisných, kde v daném roce bydlel někdo ze stromu, se objeví tečka. Klik na ni ukáže, kdo tu
byl v daném roce, a celou historii domu (rok → posuvník, jméno → panel osoby). Z panelu osoby vede
sekce **Bydliště** s odkazem „na mapě“.

| Co | Odkud |
|---|---|
| bydliště | události `add_event` v `T/patches/*.yml` s č. p. v `description`, typy narození, úmrtí, bydliště, sčítání, povolání („bytem…“). Sňatek a křest se neberou (č. p. nevěsty, kmotry, porodní báby). Rok z `date`, `FROM a TO b` = rozmezí |
| poloha domu | `mcp/czech-archives/gazetteer/*-cp.csv` — **dnešní** RÚIAN; historicky mohl dům stát jinde |
| část obce u adresy | čtvrť z římské číslice za lomítkem (`66/III` → Chlumec nad Cidlinou III, čp. 66); část jmenovaná před č. p. („…, část Kladruby č. p. 40“ → Kladruby); obec se čtvrtěmi bez uvedené čtvrti se nehádá — „čtvrť neurčena“, jen střed obce |
| poloha obce | tabulky `docs/mistopis/*/obce.md` (sloupec „lat, lon“) — obec bez dat o domech = čtvereček na středu obce |
| oblasti | `cache/mapy/<oblast>/` (obálka z `tilejson.json`) a `docs/mistopis/<oblast>/` (obálka obcí); název z nadpisu README |
| podklady | `cache/mapy/<oblast>/<vrstva>/xyz/` (stahuje `tools/mapy/stahni.py`), názvy a citace z `tools/mapy/vrstvy.yml`; přes `/tiles/…`. Pod nimi OpenStreetMap (online) |

- **doloženo** (plná tečka) = záznam z toho roku nebo rozmezí FROM–TO; **odvozeno** (čárkovaný kroužek)
  = mezi dvěma doklady téhož domu, nebo nejvýš 10 let po posledním dokladu (nikdy po úmrtí, před narozením).
  Volba „jen doložené“ odvozené skryje.
- **Podklad podle roku** vybere vrstvu s rozsahem let nejbližším roku na posuvníku (rozsah z názvu vrstvy
  ve `vrstvy.yml`, „aktuální“ = letos). Katastrální mapa jde přes podklad zvlášť.
- Do mapy jde jen to, co je v patchích (navržené i aplikované; neaplikované má v historii domu stav).
  Nálezy jen v dossierech nebo přepisech se na mapě neobjeví, dokud nejsou v patchi.

## Fronta kontrol (záložka Kontroly)

Formát a pravidla: [`docs/metodika/autonomie.md`](../../docs/metodika/autonomie.md), kap. 5. Počet otevřených
(a za tečkou blokujících) je na záložce v horní liště. Řazení: blokující → priorita → nejstarší (`vzniklo.kdy`);
filtr podle stavu (výchozí otevřené), osoby a typu. U položky otázka, kontext, výřez snímku (klik = zvětšit,
odkaz na celý snímek a portál), varianty vedle sebe s oporou (★ = doporučení session), doporučení, související soubory.

**Rozhodnutí** — volba varianty nebo vlastní znění + poznámka → *Zapsat rozhodnutí*. Je to **jediný zápis
dashboardu**:

- jen do `T/research/kontroly/*.yml`, jen klíče `stav: rozhodnuto` a
  `rozhodnuti: {volba, poznamka, kdo: uzivatel, kdy}`; textová úprava řádků, zbytek souboru (komentáře,
  pořadí) zůstane. Výsledek se ověří parserem (jiná pole se nesmí změnit), soubor se nahradí atomicky;
  změnil-li se mezitím na disku, zápis se odmítne.
- měnit jde jen stav `otevřeno` / `rozhodnuto` (tlačítko *změnit*); po `zapracováno` / `zamítnuto` ne.
- `POST /api/kontrola/<id>` přijme jen spojení z 127.0.0.1, JSON, hlavičku `X-Dashboard-Token` (token se vkládá
  do stránky a mění se při každém startu serveru → po restartu obnov stránku) a `Origin`/`Host` tohoto serveru.
- Běží-li session té osoby (herdr), dostane `kontrola <id>: rozhodnuto — <volba>`. Jinak rozhodnutí
  vyzvedne manager. Zapracování (`zapracovano`) dělá patchem session nebo manager, ne dashboard.

## Doložení údajů (panel osoby)

Tabulka událostí osoby z **aplikovaných** patchů: `add_event` (handle z `applied.items`), k nim citace z
`add_citation` a `update_event … citation` (i z patchů jiných osob), rodinné události u obou manželů.
Sloupec **pramenů** ①②③ = počet **různých zápisů** v citacích (pravidlo D2): jeden sidecar = jeden zápis,
sidecar s `pair` a jeho dvojče = jeden, rejstřík (typ/forma „rejstřík“, „index“) se nepočítá (`+R1`),
citace odkazem na Gramps (`C0013`) = jeden zápis. **jist.** = nejvyšší jistota citace. Najetí na počet ukáže
zápisy. Neaplikované patche se nepočítají (`remove_citation` se neprojevuje; duplicitní citace téhož zápisu
se sloučí).

## Session větví

Agent `vetev-*` (viz `docs/metodika/workflow-sessions.md`, Session větve) se ukáže v přehledu běžících session
s názvem, kořenem větve (a odkud se vzal) a osobou, na které teď pracuje. Ve stromu má tečku s kroužkem.

- **Kořen větve:** `T/research/vetve.yml` má přednost (zapisuje manager při otevření větve, např.
  `vetev-x: K0001-S2-P2-P2` nebo `vetev-x: {koren: …}`). Bez něj se vezme první ID osoby v prvním promptu
  session — zadání větve začíná „Začni <ID> …“. Neznámý kořen = větev je jen v přehledu.
- **Osoba patří větvi**, když je pod jejím kořenem ve struktuře ID (Kekule n → n//2, jinak bez poslední přípony);
  víc větví nad sebou → vyhraje **nejbližší** kořen (vetev-boudys pod vetev-kubelka). Vlastní session `k<ID>`
  má vždy přednost.
- **Odznak** dostane osoba větve se stavem `rozpracováno`. Nemá-li větev žádnou (session je mezi osobami),
  dostane bledou tečku osoba větve s naposledy změněným dossierem („naposledy“ v přehledu).
- Rozhodnutí kontroly osoby, která patří větvi, se pošle session větve.
