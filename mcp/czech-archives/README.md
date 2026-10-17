# czech-archives — modulární MCP pro české archivy

Jeden MCP server, jeden modul na archiv/portál. Moduly se dopisují podle toho, který archiv zrovna
potřebujeme. Stav: **v0.2 — hotové moduly `aron_zamrsk`** (SOA Zámrsk / Hradec Králové, viz
[`docs/archivy/aron-zamrsk.md`](../../docs/archivy/aron-zamrsk.md)) **a `ebadatelna_praha`** (SOA Praha,
eBadatelna, viz [`docs/archivy/ebadatelna-praha.md`](../../docs/archivy/ebadatelna-praha.md));
ostatní moduly jsou zatím návrh.

## Spuštění

```bash
cd mcp/czech-archives
uv run czech-archives                                   # MCP server (stdio)
uv run python examples/zizelice_demo.py /tmp/demo-out   # kouřový test: hledání + 1 snímek
```

Registrace do `.mcp.json` workbenche (návrh):

```json
"czech-archives": {
  "command": "uv",
  "args": ["run", "--directory", "mcp/czech-archives", "czech-archives"]
}
```

Struktura: `czech_archives/core/` (modely, HTTP klient s rate limitem a cache, citace + sidecar),
`czech_archives/modules/` (jeden soubor na archiv, registr v `__init__.py`), `czech_archives/server.py`.

- **Rate limit** 2,5 s mezi požadavky na jeden archiv, hlídaný zámkem v souboru → platí i pro
  souběžné session. Žádné paralelní dotazy. User-Agent `genealogy-workbench/0.1 (osobní rodinný výzkum)`.
- **Cache** `~/.cache/genealogy-workbench/czech-archives/<modul>/` (přepsatelné `CZECH_ARCHIVES_CACHE`):
  hledání 1 den, detail svazku 7 dní, citace/jména 30 dní, snímky natrvalo.
- **Pojistka:** jeden stahovaný soubor max. 50 MB — ZIP celé matriky se nestáhne nikdy
  (`register_zip_info` dělá jen HEAD).
- `fetch_page` zapíše vedle snímku sidecar `<snímek>.yml` (existující nepřepisuje); `entry`,
  `persons`, `confidence` a folio doplní člověk po přečtení zápisu.
- Funguje s `mcp` 1.x (`FastMCP`) i 2.x (`MCPServer`).

Zatím neimplementováno: `sync_catalog` / SQLite katalog, `search_names`, `fetch_register`
(stažení celé sady — záměrně jen info o ZIPu). Gazetteer YAML zatím používá jen `ebadatelna_praha`
jako offline zálohu hledání.

### Modul `ebadatelna_praha` (SOA Praha)

Nástroje jsou stejné, jen s `module="ebadatelna_praha"`; `register_id` = **matrikaId** (číslo
z `…/MatrikaPage/matrikaId/<ID>` nebo z krátkého odkazu `…/d/<ID>/<snímek>`), `image` = číslo
snímku v prohlížeči (= číslo v krátkém odkazu).

- bez přihlášení (anonymní Wicket session, cookie jen v paměti), HTML parsing, žádné API;
- `find_registers` = živé hledání eBadatelny „v lokalitách“ (podřetězec, i historické názvy obcí),
  při výpadku portálu záloha z `gazetteer/*.yml`; v Pythonu `in_titles=True` hledá v názvech knih;
- `fetch_page` = HTML prohlížeče `/d/<ID>/<snímek>` → odkaz „stáhnout“ → originální JPG
  (2 požadavky, tj. ~5 s); sidecar `.yml` s odkazem `https://ebadatelna.soapraha.cz/d/<ID>/<snímek>`;
- `register_zip_info` jen vrátí poznámku — ZIP celé knihy je pro registrované, modul ho nepoužívá;
- jen v Pythonu (zatím ne jako MCP tool): `register_details(ID)` (okres, typ knihy, rozsahy N/O/Z
  a indexů, lokality s variantami) a `image_map(ID)` — oddíly svazku podle obcí s čísly snímků
  z „Obecného popisu“ (např. Loukonosy fol. 173–184 = snímky 165–176).

## Nástroje (MCP tools)

| Tool | Co dělá |
|---|---|
| `list_modules()` | dostupné moduly a co umí (matriky / sčítání / index jmen / tisk) |
| `find_registers(place, year_from, year_to, kind?, confession?)` | přes gazetteer najde farnost a archiv a vrátí svazky (z cache katalogu modulu) |
| `register_info(module, register_id)` | metadata svazku: farnost, typ, roky, obce, signatura, počet snímků, URL |
| `fetch_page(module, register_id, image)` | stáhne snímek do cache (`sources/` stromu), vrátí cestu + sidecar citaci |
| `fetch_register(module, register_id)` | celý svazek, jen kde to portál oficiálně nabízí (ARON ZIP) — *zatím jen `register_zip_info` (URL + velikost, HEAD)* |
| `search_names(module, query)` | jen moduly s jmenným indexem (NA přihlášky, VÚA, Třeboň indexy, holocaust.cz) |
| `cite(module, register_id, image, entry?)` | citace podle [`docs/metodika/citace.md`](../../docs/metodika/citace.md) |

## Rozhraní modulu (Python)

```python
class ArchiveModule(Protocol):
    id: str                      # "aron_zamrsk"
    archive: str                 # "SOA Zámrsk"
    capabilities: set[str]       # {"registers", "fetch_page", "fetch_register", "search_names"}

    def sync_catalog(self) -> Iterable[Register]: ...      # katalog svazků → lokální SQLite
    def register_info(self, register_id: str) -> Register: ...
    def page_url(self, register_id: str, image: int) -> str: ...
    def fetch_page(self, register_id: str, image: int, dest: Path) -> Path: ...
    def citation(self, register: Register, image: int) -> Citation: ...
```

`core/` dodává: HTTP klienta s **rate limitem** a User-Agentem, diskovou cache, SQLite katalog svazků,
generátor citací a sidecar `.yml`.

## Gazetteer

`gazetteer/` = data obec → farnost (s obdobím) → archiv → svazky. Plní se z katalogů modulů
(svazky nesou seznam obcí) a z inventářů / schematismů. Jádro `find_registers`.

## Pořadí modulů

1. `aron_zamrsk` — hlavní archiv stromu `berescak` (Chlumecko, Bydžovsko, Hradecko) — hotovo
2. `ebadatelna_praha` — střední Čechy (Žiželice, Týnec n. L., Žehuň, Ohaře) — hotovo
3. `kramerius` — schematismy (farnosti), noviny
4. ostatní podle potřeby

## Backlog

- `aron_zamrsk.find_house(register_id, cp)` — u sčítacích operátů najít snímky domácnosti podle čísla
  popisného (názvy souborů snímků v ARONu obsahují čp., např. `…-cp-300.jpg`; tip z výzkumu K0014).
- MCP tool pro `ebadatelna_praha.register_details` / `image_map` (navigace k oddílu obce ve svazku)
  — vyžaduje úpravu `server.py`.
- `ebadatelna_praha`: fond pro citaci (portál ho neuvádí; ověřit v ARON SOA Praha).
- **Nový modul SOA Třeboň** (digi.ceskearchivy.cz / Digitální badatelna SOA Třeboň) — potřeba pro Mirovice
  (Petrovi/Voborníkovi, větev Brejchovi 2026-10-17); jižní a jihozápadní Čechy.
- SQLite katalog svazků (`sync_catalog`), gazetteer → `find_registers` podle obce bez znalosti archivu.
