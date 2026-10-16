# Dashboard workbenche

Lokální stránka s živým přehledem stavu výzkumu nad stromem: rodokmen s barvou stavu u každé osoby,
odznaky (běžící session, čekající patch, nápovědy, todo, doklady), panel osoby s dossierem a vším k ní,
přehled session / patchů / sdílených seznamů / výzkumného logu.

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
- **Jen čtení.** Do stromu nic nezapisuje, necommituje, Gramps nevolá (jen odkaz
  `<gramps-url>/person/<gramps_id>`).
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
| běžící session | `herdr agent list` — agent se jménem ve tvaru ID (`k0056`, `k0001-s2-p2`) s cwd ve workbenchi/stromu |

## Strom z ID

`K%04d` = Kekule (otec `2n`, matka `2n+1`); přípony `-S<n>` manžel/ka, `-C<n>` dítě, `-P1`/`-P2` rodiče.
Přímí předci tvoří pedigree (generace = sloupce, K0001 vlevo). Manželé a děti visí čárkovaně pod kotvou
ve stejném sloupci (∞ / d.); mají-li vlastní rodiče, dostanou pás pod rodokmenem kotvy a jejich
pedigree pokračuje doprava. Větve jdou sbalit (±, pamatuje si prohlížeč).

Volba **prázdní rodiče** ukáže u každého přímého předka s dossierem prázdné rámečky rodičů — kam se dá jít.
Filtry: **jen rozpracované** (rozpracováno / pozastaveno / běží session), **čeká na mě**
(patch `navrženo` nebo session ve stavu idle/done).

## Mapa (záložka Mapa)

„Kde kdo žil“: výběr oblasti, podklad, posuvník roku (▶ přehrát, šipky ←/→, Shift = po 10 letech).
U čísel popisných, kde v daném roce bydlel někdo ze stromu, se objeví tečka. Klik na ni ukáže, kdo tu
byl v daném roce, a celou historii domu (rok → posuvník, jméno → panel osoby). Z panelu osoby vede
sekce **Bydliště** s odkazem „na mapě“.

| Co | Odkud |
|---|---|
| bydliště | události `add_event` v `T/patches/*.yml` s č. p. v `description`, typy narození, úmrtí, bydliště, sčítání, povolání („bytem…“). Sňatek a křest se neberou (č. p. nevěsty, kmotry, porodní báby). Rok z `date`, `FROM a TO b` = rozmezí |
| poloha domu | `mcp/czech-archives/gazetteer/*-cp.csv` — **dnešní** RÚIAN; historicky mohl dům stát jinde |
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
