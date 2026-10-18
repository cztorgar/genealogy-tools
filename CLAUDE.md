# Pravidla pro agenta — genealogický workbench

Komunikace česky. Tohle repo je **obecný workbench**; data konkrétních stromů jsou v
`../genealogy-trees/<strom>/` (každý strom vlastní git). Do tohoto repa nikdy nedávej osobní data.

Aktivní strom: `berescak` (`../genealogy-trees/berescak/`). Gramps Web: http://localhost:5055,
strom `berescak` (master, staví se od nuly) a `myheritage-ref` (import z MyHeritage, jen nápovědy).
Přístupy v `infra/gramps-web/.env`.

## Role session

- Session **`manager`** řídí frontu, aplikuje patche do Gramps, commituje a rozvíjí workbench.
- **Osobní session** (`K0042`) zkoumá jednu osobu přes skill `research-person` a smí zapisovat jen
  do svých souborů. Přesná pravidla: [`docs/metodika/workflow-sessions.md`](docs/metodika/workflow-sessions.md).

## Důkazy

- **Fakt bez pramene do stromu nepatří.** Cizí strom, Smart Match, tip z fóra = *nápověda*
  (`research/hints/`), ne fakt.
- **Jmenovec ≠ předek.** Záznam se k osobě přiřadí, jen když kromě jména sedí aspoň **dva nezávislé
  údaje** (rodiče, manžel/ka, číslo popisné, obec, věk ± tolerance, povolání).
- Rozpory se **neřeší mlčky**: obě verze zůstanou, rozbor do `research/people/<ID>.md`.
- Odhady značit (`ABT`, `EST`, „pravděpodobně“). Nikdy nevymýšlet data, jména ani signatury.
- Metodika: [`docs/metodika/`](docs/metodika/).

## Přepis pramenů

- AI přepis je **draft**. Pole se jménem a datem musí člověk ověřit proti snímku.
- Reader běží s více backendy (Claude + OpenAI, příp. PERO). Neshoda pole = označit k ruční kontrole.
  Shoda dvou modelů není důkaz — oba umí jméno „normalizovat“ stejně.
- Vždy oddělovat: doslovný přepis → normalizace → překlad → interpretace
  ([`docs/metodika/prepis.md`](docs/metodika/prepis.md)).

## Zápis do stromu (Gramps)

- Agent do Gramps **nezapisuje přímo**. Změnu navrhne jako patch do `patches/` stromu, uživatel ji schválí.
- Každý zapsaný fakt má citaci se stupněm jistoty (0–4) a odkazem na snímek v `sources/`.
- Co patří do Gramps a co zůstává ve workbenchi: [`docs/metodika/gramps-vs-workbench.md`](docs/metodika/gramps-vs-workbench.md).

## Výzkumný log

- Každé hledání zapsat do `research/log.md` stromu — **včetně „nenalezeno“** (co, kde, jaký rozsah
  let/stran), aby se stejné místo neprohledávalo dvakrát.

## Archivní portály

- Stahovat **jen na vyžádání a rychlostí člověka**, přes cache. Žádné hromadné mirrorování.
- MZA Brno blokuje IP při překročení limitů; Opava, Litoměřice, Plzeň mají anti-bot ochranu.
- **Portály, které blokují roboty** (Třeboň, Matricula, Plzeň, Opava, Litoměřice…): přístup **jen přes Claude in Chrome**
  jako člověk — jednotlivé konkrétní snímky, tempo člověka, žádné procházení svazků. **Nikdy** podvrh hlaviček/UA,
  Origin/Referer, obcházení detekce robotů ani řešení CAPTCHA. Objeví-li se CAPTCHA/kontrola „jste člověk“ → předat
  řízení uživateli a čekat. Chrome řídí v jednu chvíli **jen jedna session** a jen když je uživatel k dispozici.
- Z prohlížeče **číst z obrazovky** a uložit přesnou URL pohledu (snímek, výřez). **Stažení souboru** jen se souhlasem
  uživatele (session sepíše seznam snímků ke stažení, uživatel potvrdí).
- Snímky z portálů, jejichž podmínky zakazují předání třetím stranám (Třeboň, Matricula), **neposílat do OpenAI** —
  čte jen Claude → jistota ≤ 1 (R5 ≤ 2), dokud snímek neověří uživatel.
- Detaily k portálům: [`docs/archivy/`](docs/archivy/).

## Soukromí

- Všechna data stromu (včetně žijících osob) smí do LLM — uživatel pracuje na vlastní rodině se souhlasem.
- Soukromí řešit jen u **publikování** (rodinný web, sdílené repo): žijící osoby neveřejně.
