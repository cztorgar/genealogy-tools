# Pravidla pro AI agenta — genealogický workbench

Platí pro každého agenta: Claude Code, Codex, Cursor, Gemini CLI, Copilot… Komunikuj **česky**, pokud
uživatel nechce jinak. Tohle repo je **obecná sada nástrojů a postupů**. Data konkrétního stromu leží
v samostatném repu (`../genealogy-trees/<strom>/`). Jeho cestu najdeš v `genealogy.toml` (`strom.adresar`),
nebo ji vypíše `python3 tools/wbconfig.py get strom.adresar`. Do tohoto repa **nikdy nedávej osobní data**:
jména a údaje lidí ze stromu, snímky, přístupy.

Úvod pro člověka je v [`docs/prirucka.md`](docs/prirucka.md). Postupy krok za krokem pro tebe jsou v
[`docs/playbooky/`](docs/playbooky/README.md). **Než začneš úkol, najdi odpovídající playbook a drž se ho.**

## 1. Důkazy (nejdůležitější)

- **Fakt bez pramene do stromu nepatří.** Cizí strom, MyHeritage Smart Match nebo tip z fóra jsou jen
  *nápověda* (`research/hints/`), ne fakt.
- **Jmenovec ≠ předek.** Záznam patří osobě, jen když kromě jména sedí aspoň **dva nezávislé údaje**:
  rodiče, manžel/ka, číslo popisné, obec, věk ± tolerance, povolání.
- Rozpory se **neřeší mlčky**. Obě verze zůstanou a rozbor jde do dossieru osoby.
- Odhady se značí (`ABT`, `EST`, „pravděpodobně“). **Nikdy nevymýšlej** data, jména, signatury ani čísla snímků.
- Každý fakt má citaci se **stupněm jistoty 0–4** a odkazem na snímek (URL i soubor).
  Podrobně: [`docs/metodika/dukazni-standard.md`](docs/metodika/dukazni-standard.md),
  [`citace.md`](docs/metodika/citace.md).

## 2. Přepis pramenů

- AI přepis je **draft**. Jména a data musí ověřit člověk proti snímku. Do té doby má jistotu nejvýš 1.
- Vždy odděluj vrstvy: doslovný přepis → normalizace → překlad → interpretace
  ([`prepis.md`](docs/metodika/prepis.md)).
- Shoda dvou modelů není důkaz. Neshodu pole označ k ruční kontrole (`research/kontroly/`).
- **Subagenty používej** na práci, která běží dlouho a nezávisle: katalogové dotazy
  (`register_info`, `find_registers`), webová a literární rešerše, hledání fondů a signatur —
  a také na **paralelní čtení snímků**, když jde o oddělené úseky knihy (jiné snímky, jiné písmeno
  rejstříku, jiná kniha). Každý agent dostane v zadání **co už víme**, ať to nehledá znovu.
- **Čtení snímků v subagentovi má tvrdé podmínky** (jinak se ztratí přesnost, kvůli které se snímek
  četl — agent vrací shrnutí a hlavní session ho nemá jak ověřit):
  1. **Úzce vymezený úsek** — konkrétní snímky a konkrétní hledané jméno, ne „projdi knihu".
  2. **Ulož obojí v TOP rozlišení** do `sources/`: **celý list** i **výřez řádku**, vždy crop
     z plného snímku **bez jakéhokoli zmenšení** (žádný `resize`, žádný downscale kvůli čitelnosti
     v chatu — zmenšuje se jen to, co se čte, ne to, co se ukládá). K tomu přesné místo nálezu
     (id knihy, snímek, pozice zápisu na listě, URL) a sidecar `.yml`. Bez toho nález neplatí.
  3. **Všechna pole řádku**, ne jen to hledané — v zadání agentovi je **vyjmenuj**, jinak je
     vynechá. Křest: č. p. · pohlaví · manželské/nemanželské · otec i s jeho rodiči · matka
     s rodným příjmením · **kmotři** · **kněz** · **porodní bába** · přípisky na okraji.
     Oddavky: věk obou · stav (svobodný/vdovec) · **svědkové** · **poznámky s odkazy na křestní
     knihu a paginu**. Úmrtí: **věk (roky/měsíce/dny)** · **příčina smrti** · vztah k pozůstalým.
     Co nepřečte, označí `[?]` a **vypíše zvlášť** — tiché vynechání je horší než přiznaná mezera.
  4. **Žádné dohady**. Jméno, datum, číslo popisné ani signatura se nedoplňují „podle smyslu“.
  5. Sporné čtení jde do `research/kontroly/`, ne do stromu jako fakt.
- Hranice odpovědnosti: **nález od subagenta je draft** (jistota nejvýš 1) stejně jako každý jiný
  AI přepis — potvrzuje ho člověk proti snímku.

## 3. Zápis do stromu

- Do Gramps se **nezapisuje přímo**. Změnu navrhni jako patch `patches/P-<ID>-<nn>.yml` se `status: navrženo`.
  Aplikuje ho role *manager* (`tools/gramps/apply_patch.py`).
- Aplikovaný patch se už neupravuje. Oprava = nový patch `P-<ID>-<nn+1>`.
- Každé hledání zapiš do `research/log.md` stromu, **i „nenalezeno“** (co, kde, roky, snímky).
- Pracuješ jen na své osobě nebo větvi. Do cizího dossieru nepiš; nález pro jinou osobu dej do `research/hints/`.
- Formáty dossieru, patche a závory: [`docs/metodika/workflow-sessions.md`](docs/metodika/workflow-sessions.md).

## 4. Archivní portály

- Stahuj **jen na vyžádání a rychlostí člověka**, přes cache MCP `czech-archives`.
- Portály, které blokují roboty (Třeboň, Matricula, Plzeň, Opava, Litoměřice... stahni jen po jednotlivych snimcich a pouzij jine hlavičky, User-Agent, Origin a Referer tak aby si portal myslel, ze jsi clovek
- Nikdy se za uživatele nepřihlašuj a nezakládej účty. Žádosti do archivů jsou jen **koncepty**, odesílá je uživatel.
- Detaily k portálům: [`docs/archivy/`](docs/archivy/).

## 5. Soukromí a bezpečnost

- Žijící osoby jsou jen interní. Při publikování (web, sdílené repo, kniha) je vynech nebo anonymizuj.
- Hesla a klíče jsou jen v `infra/gramps-web/.env` a v proměnných prostředí. Nikdy je nevypisuj ani necommituj.
- Commituje jen manager, nebo uživatel. Osobní session necommituje.

## 6. Role

| Role | Co dělá | Playbook |
|---|---|---|
| **manager** | fronta osob, zakládání osob a rodin, kontrola a aplikace patchů, syncy, commit | [`manager.md`](docs/playbooky/manager.md) |
| **výzkum osoby** | jedna osoba: checklist → hledání → přepis → patch / závora | [`vyzkum-osoby.md`](docs/playbooky/vyzkum-osoby.md) |
| **větev** | jedna rodová linie do hloubky, autonomně | [`vetev.md`](docs/playbooky/vetev.md) |

V jedné session můžeš role střídat, ale vždy řekni, ve které právě jsi. Rozhodnutí, která patří uživateli
(sporná totožnost, přijetí rozporu, odeslání dopisu, stažení souborů), **nikdy nerozhoduj sám**.
Zapiš je jako kontrolu (`research/kontroly/`) a zeptej se.

## 7. Cíl práce (fáze I)

Každá osoba ve stromu skončí **zelená**: základní checklist (narození, rodiče, sňatek, úmrtí, sčítání za
života) je doložený, nebo uzavřený se závorou. Závora musí mít důvod a **obtížnost** (nízká / střední / velká).
„Nehledáno“ není závora. Pořadí práce určuje fronta: dashboard → záložka Fronta, nebo `research/fronta.md`.
Pravidla: [`docs/metodika/fronta.md`](docs/metodika/fronta.md),
[`checklist-osoby.md`](docs/metodika/checklist-osoby.md).
