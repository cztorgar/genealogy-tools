# Genealogický workbench

Obecná sada nástrojů, postupů a pravidel pro genealogický výzkum v českém prostředí s pomocí AI
(Claude Code + MCP). Workbench **neobsahuje osobní data** — stromy žijí v samostatných repozitářích
v `../genealogy-trees/<strom>/`.

## Co tu je

| Složka | Obsah |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | závazná pravidla pro agenta (důkazy, citace, zápis do stromu) |
| [`docs/architektura.md`](docs/architektura.md) | jak spolu části souvisí, tok dat |
| [`docs/metodika/`](docs/metodika/) | jak stavět strom: důkazní standard, citace, místa, jména, data, přepis, checklist osoby |
| [`docs/prameny/`](docs/prameny/) | katalog typů pramenů — co existuje, pro jaké období, co z toho lze ověřit |
| [`docs/archivy/`](docs/archivy/) | jeden soubor na archiv/portál: co má, jak hledat, technika, omezení |
| [`docs/slovnik/`](docs/slovnik/) | latina a němčina v matrikách, zkratky, stavy, povolání |
| [`skills/`](skills/) | Claude skills — opakovatelné postupy (plán výzkumu, hledání, přepis, zápis faktu, import) |
| [`mcp/czech-archives/`](mcp/czech-archives/) | modulární MCP server pro české archivy (1 modul = 1 portál) |
| [`tools/`](tools/) | skripty: GEDCOM (statistiky, normalizace, diff), MyHeritage (export, média), Gramps (zálohy) |
| [`infra/`](infra/) | Gramps Web v Dockeru |
| [`evals/`](evals/) | testovací stránky matrik s ručním přepisem — měření kvality čtení |
| [`web/`](web/) | (plán) stránka pro vizualizaci rozpracovaných výsledků |
| [`docs/navrh-2026-10-16.md`](docs/navrh-2026-10-16.md) | výchozí průzkum a návrh |

## Strom (repo `genealogy-trees/<strom>/`)

```
TREE.md            rozsah, hlavní linie, stav
data/gramps/       noční export Gramps XML (verzovaný master)
data/exports/      importované exporty (MyHeritage…)
media/             fotky a dokumenty (mimo git, zálohováno zvlášť)
sources/           stažené snímky pramenů + sidecar .yml s citací
transcriptions/    přepisy záznamů (.md) + extrahovaná data (.json)
research/          log.md, questions/, hints/, people/
patches/           navržené změny stromu → schválené → aplikované
```

## Rychlý start

```sh
cd infra/gramps-web && cp .env.example .env && docker compose up -d   # http://localhost:5055
```

Postup práce a rozdělení dat mezi Gramps a workbench: [`docs/metodika/gramps-vs-workbench.md`](docs/metodika/gramps-vs-workbench.md).
