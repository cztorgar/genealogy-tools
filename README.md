# genealogy-tools

Sada nástrojů, postupů a pravidel pro **doložený rodokmen z českých pramenů** s pomocí AI agenta
(Claude Code, Codex, Cursor, Gemini CLI…). AI hledá v archivech, čte zápisy a navrhuje změny. Člověk rozhoduje.
Každý fakt má pramen, jistotu a odkaz na snímek.

Repo **neobsahuje osobní data**. Každý strom žije ve vlastním soukromém repu (`../genealogy-trees/<strom>/`),
které se zakládá ze šablony.

## Začni tady

| kdo | čti |
|---|---|
| **člověk** | [`docs/prirucka.md`](docs/prirucka.md): instalace, založení stromu, denní práce, dashboard |
| **AI agent** | [`AGENTS.md`](AGENTS.md) (závazná pravidla) a [`docs/playbooky/`](docs/playbooky/README.md) (postupy) |
| Claude Code | navíc [`CLAUDE.md`](CLAUDE.md), skills v [`skills/`](skills/), MCP v [`.mcp.json`](.mcp.json) |

```sh
cp genealogy.example.toml genealogy.toml                         # cesta ke stromu, jméno badatele
(cd infra/gramps-web && cp .env.example .env && docker compose up -d)   # Gramps Web: http://localhost:5055
uv run tools/init_tree.py ../genealogy-trees/novak --nazev novak --k0001 "Jan Novák (*1980)"
uv run tools/dashboard/server.py                                 # dashboard: http://localhost:5056
```

## Co tu je

| složka | obsah |
|---|---|
| [`docs/metodika/`](docs/metodika/) | důkazní standard, citace a jistota, přepis, jména, místa, checklist osoby, fronta, workflow, autonomie |
| [`docs/playbooky/`](docs/playbooky/) | postupy pro AI: výzkum osoby, čtení zápisu, manager, větev, kontroly, portály, závory |
| [`docs/prameny/`](docs/prameny/) | katalog typů pramenů: co existuje, pro jaké období, co lze ověřit |
| [`docs/archivy/`](docs/archivy/) | jeden soubor na archiv / portál: co má, jak hledat, omezení |
| [`docs/mistopis/`](docs/mistopis/) | místopis: obce → farnosti → archivy (ukázkový region Chlumecko a Žiželicko) |
| [`docs/nastroje/`](docs/nastroje/) | poznámky k nástrojům čtení (reader, PERO, HTR) |
| [`skills/`](skills/) | Claude skills = podrobné playbooky (`research-person`, `read-record`) |
| [`mcp/czech-archives/`](mcp/czech-archives/) | MCP server pro české archivy (ARON Zámrsk, eBadatelna Praha, Kramerius, Matricula) |
| [`tools/`](tools/) | skripty: Gramps (patche, osoby, rodiny, export), výzkum (fronta, checklist, syncy), dashboard, reader, GEDCOM, mapy |
| [`templates/strom/`](templates/strom/) | šablona nového stromu (`tools/init_tree.py`) |
| [`infra/gramps-web/`](infra/gramps-web/) | Gramps Web v Dockeru (master stromu) |
| [`evals/htr/`](evals/htr/) | testovací sada čtení rukopisu (veřejné archiválie, referenční přepisy) |

Architektura a tok dat: [`docs/architektura.md`](docs/architektura.md).

## Lokální nastavení (necommituje se)

- `genealogy.toml`: strom, jméno badatele, volitelně účty pro orchestraci (vzor `genealogy.example.toml`).
- `infra/gramps-web/.env`: přístupy do Gramps Web.
- `CLAUDE.local.md`: osobní pokyny pro Claude Code.
- Klíč OpenAI pro druhé čtení (volitelné): `OPENAI_API_KEY`.
