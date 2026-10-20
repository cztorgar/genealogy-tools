# Architektura

## Části

```
                         ┌────────────────────── Claude Code session ──────────────────────┐
                         │  CLAUDE.md + skills/ (postupy)  +  docs/ (metodika, prameny)      │
                         └───────┬───────────────┬────────────────┬───────────────┬─────────┘
                                 │ MCP           │ MCP            │ MCP           │ soubory
                    ┌────────────▼───┐  ┌────────▼────────┐  ┌────▼─────────┐  ┌──▼──────────────────┐
                    │ gramps-mcp     │  │ czech-archives  │  │ reader       │  │ genealogy-trees/X/  │
                    │ (read → patch) │  │ core + moduly   │  │ Claude+OpenAI│  │ research/ sources/  │
                    └───────┬────────┘  └────────┬────────┘  │ (+PERO)      │  │ transcriptions/     │
                            │ REST               │ HTTP      └──────────────┘  │ patches/            │
                    ┌───────▼────────┐   ARON, eBadatelna, Třeboň,             └──────────┬──────────┘
                    │ Gramps Web     │   Porta fontium, Acta Publica,                     │
                    │ (Docker)       │   Kramerius, NA konskripce, VÚA…                   │
                    │ MASTER stromu  │──── noční export Gramps XML ──► data/gramps/ (git) ─┘
                    └───────▲────────┘
                            │ import (normalizace, diff)
                    MyHeritage GEDCOM export  ──►  hints/ (nápovědy k ověření)

  + igormel81/genealogy-mcp  (kalendáře, svátky, varianty jmen, check_match, kinship)
  + web/  (plán: vizualizace rozpracovaného stavu — checklisty, otevřené otázky, pokrytí prameny)
```

## Tok dat

1. **Import** — export z MyHeritage → `tools/myheritage` (lokalizace médií, normalizace míst) → Gramps.
   Opakovaný export → diff proti minulému → nové věci jdou do `hints/`, ne rovnou do stromu.
2. **Otázka** — `research/questions/Q-xxx.md` (co chci zjistit, o kom, proč).
3. **Hledání** — skill `find-record` → `czech-archives` najde matriku (místopis: obec + rok → farnost →
   archiv → svazek) → stáhne snímek do `sources/` se sidecar citací. Zápis do `research/log.md`.
4. **Přepis** — `reader` (Claude + OpenAI) → `transcriptions/<id>.md` + `.json`, neshody označené.
5. **Kontrola** — uživatel ověří pole proti snímku.
6. **Patch** — `patches/P-xxx.yml` (osoba, fakt, citace, jistota) → schválení → zápis do Gramps.
7. **Checklist** — generovaný z Gramps citací × šablona podle období
   ([`metodika/checklist-osoby.md`](metodika/checklist-osoby.md)).

## Stabilní identifikátory

Každá osoba má mapování `Gramps ID (I0001)` ↔ `Gramps handle` ↔ `MyHeritage _UID` ↔ `MyHeritage RIN`.
Uchovává se v Gramps jako atributy osoby (`_UID` se importuje) → umožňuje opakované importy a diffy.

## Hosting

- Teď: Gramps Web lokálně v Dockeru (`infra/gramps-web`, port 5055, jen localhost).
- Později: vlastní server za VPN (zálohy např. restic), případně přístup pro rodinu.
