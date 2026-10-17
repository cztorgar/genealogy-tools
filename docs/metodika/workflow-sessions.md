# Pracovní workflow — manager a osobní session

Strom se staví **od nuly, osoba po osobě**: přímí předci od výchozí osoby dozadu (čísla podle Kekuleho).
Export z MyHeritage je jen zdroj nápověd (Gramps strom `myheritage-ref`), master je Gramps strom
`berescak`, který obsahuje jen doložené osoby.

## Role

| Session | Pojmenování | Co dělá |
|---|---|---|
| **manager** | `manager` | řídí frontu, otevírá práci na osobách, kontroluje a aplikuje patche do Gramps, commituje repo stromu, rozvíjí workbench (nástroje, moduly archivů, metodiku) |
| **osobní session** | `K0042` (číslo osoby) | výzkum jedné osoby: checklist, hledání, přepisy, závěr, patch; spouští se skillem `/research-person K0042` |

Všechny session startují ve složce workbenche (`genealogy/`) — tam se načtou pravidla, skills a MCP.
Strom je v `../genealogy-trees/<strom>/`.

## Kdo smí co zapisovat (aby se session nepraly)

| Soubor | Osobní session K | Manager |
|---|---|---|
| `research/people/K<nnnn>-*.md` (vlastní dossier) | ✅ | ✅ |
| dossier **jiné** osoby | ❌ → zapiš nápovědu do `research/hints/` | ✅ |
| `research/hints/K<cíl>-<datum>-od-K<nnnn>.md` (nový soubor) | ✅ | ✅ |
| `sources/K<nnnn>/…`, `transcriptions/K<nnnn>-*` | ✅ | ✅ |
| `patches/P-K<nnnn>-<nn>.yml` | ✅ vytvořit | ✅ schválit / aplikovat |
| `research/people/README.md` (fronta), `research/doklady.md` | jen přes `build_queue.py` | ✅ (generuje `build_queue.py`) |
| `research/todo-*.md` (sdílené seznamy: `todo-hroby`, `todo-pozemkove-knihy`, `todo-rodina`, `todo-<rod>`, …) | ✅ jen **připsat nový záznam na konec** | ✅ úpravy záznamů, nové seznamy |
| `doklady/` (skeny od uživatele) | ✅ přesunout do `sources/<ID>/` | ✅ |
| Gramps strom `berescak` | ❌ jen čtení | ✅ zápis (z patche) |
| git commit repa stromu | ❌ | ✅ |
| workbench (`genealogy/`) | ❌ — návrhy změn pošli managerovi | ✅ |

## Převzetí jiné osoby

Když uživatel chce v jedné session dotáhnout i jinou osobu (typicky manžela/ku) a ta **nemá vlastní běžící
session**, smí ji osobní session převzít: v dossieru převzaté osoby zapíše do Výzkumu
„převzato session K0056 (YYYY-MM-DD)“, vede její dossier, checklist a patch (`P-K0057-01`) a nastavuje
její stav. Zprávu o patchi pošle managerovi stejně jako za svou osobu. Kdyby se pro převzatou osobu
otevřela vlastní session, nejdřív se domluví přes managera.

## Centrální seznam dokladů

`research/doklady.md` = co musí uživatel sehnat, seskupené podle místa (doma, u rodičů, matriční úřad…).
Generuje se ze sekcí `## Doklady k dohledání` v dossierech — session zapisují jen do svého dossieru,
přehled se skládá automaticky (formát řádku ve skillu `research-person`). Skeny dává uživatel do
`doklady/`, session je zařadí do `sources/<ID>/` a odškrtnou.

## Odloženo (vědomě neřešeno)

Každý dossier má sekci `## Odloženo (vědomě neřešeno)` (před logem): co jsme se **rozhodli teď nedělat**,
aby se na to nezapomnělo a nehledalo se to omylem znovu. Formát:
`- YYYY-MM-DD · **co** — proč / kde (odkaz na todo-seznam) · kdo rozhodl`.
Rozdíl proti checklistu: `[-]` = hledáno a nenalezeno; *odloženo* = vědomě nehledáno.

## Životní cyklus osoby

Front-matter dossieru má dvě pole:

**`původ:`** — odkud osobu známe (nemění se): `myheritage` · `pramen` (narazili jsme na ni v záznamu —
kmotr, svědek, sourozenec) · `ústně` (z vyprávění).

**`stav:`** — kde je výzkum:

| Stav | Význam | Kdo nastavuje |
|---|---|---|
| `zmínka` | narazili jsme na ni, dossier založen, nic nezkoumáno | kdokoli, kdo ji objeví (přes manažera — založení dossieru) |
| `převzato` | jen údaje z MyHeritage, nic ověřeného | generátor fronty |
| `rozpracováno` | výzkum začal | osobní session po odsouhlasení plánu |
| `pozastaveno` | čeká na doklad / pramen — důvod v dossieru | osobní session |
| `dokončeno` | výzkum hotový, patch připraven pro managera | osobní session |
| `zapsáno` | v Gramps `berescak` s citacemi | manager |

```
zmínka ─┐
        ├──► rozpracováno ⇄ pozastaveno ──► dokončeno ──► zapsáno
převzato┘
```

Fronta (`research/people/README.md`) čte stav z dossierů a ukazuje souhrn.

## Herdr

Všechno běží v herdr (terminálový multiplexer pro agenty), ve workspace
`genealogy`. Manager je tab + agent `manager`.

- **Otevření osobní session** dělá manager: `tools/sessions/open_person.sh 42` → nový tab `K0042 <příjmení>`,
  Claude Code s agentem/jménem `k0042`, spuštěný `/research-person K0042`. Když session už běží, jen se na
  ni přepne.
- **Zpráva managerovi:** `herdr agent prompt manager "K0042: <zpráva>"` (bez `--wait`).
- **Manager → osobní session:** `herdr agent prompt k0042 "<zpráva>"`; stav `herdr agent get k0042`.
- **Session zavírá manager jen na pokyn uživatele.** Ani po zápisu patche (`zapsáno`) ji nezavírat sám —
  u osoby můžou zůstat otevřené body. Před zavřením ověřit, že agent nepracuje. Všechno podstatné je v dossieru; po dodání dokladu se otevře nová session a úvodní karta naváže.

## Komunikace

- Osobní session posílá managerovi zprávu (`herdr agent prompt manager …`), když:
  patch je hotový · narazila na blok (chybí pramen, nečitelný snímek, potřeba nového modulu archivu) ·
  zjistila něco podstatného o jiné osobě (a zapsala to do `research/hints/`).
- Manager odpovídá do téže session nebo rozhodne o další osobě.
- Rozhodnutí, která patří uživateli (sporná identita, přijetí rozporu), se neřeší mezi session —
  vždy se zeptat uživatele.

## Patch (`patches/P-K0042-01.yml`)

```yaml
person: K42                       # číslo osoby, Gramps ID doplní manager při zápisu
status: navrženo                  # navrženo → schváleno → aplikováno
summary: Jan Řezáč, * 17. 7. 1841 Nosetín č. 10, ověřeno v matrice N
changes:
  - op: add_event                 # add_event | update_event | add_citation | remove_citation | update_citation | add_media
    type: Birth                   # Birth | Christening | Marriage | Death | Burial | Residence | Occupation | Census
    date: 17 JUL 1841
    place: Nosetín
    description: "Nosetín č. 10"            # jen o této osobě, krátce
    context: "otec Josef Řezáč, tkadlec; kmotři …"   # kontext záznamu → poznámka k události
    citation: c1
citations:
  c1:
    source_sidecar: sources/K0042/soapraha-nosetin-N-1830-1850-s18.yml
    page: "fol. 12v, snímek 18"
    confidence: 4
    transcription: transcriptions/K0042-krest-1841.md
```

Osoby a rodinné vazby zakládá manager rovnou (`ensure_persons.py`, `ensure_family.py`) — patch nese jen
fakta. Vazbu, kterou zná uživatel, cituje „Ústní sdělení“; vazbu z pramene zakládá `--no-oral` a citaci dodá
patch. Osobu mimo export MyHeritage zakládá `tools/research/add_person.py` (dossier + `manual.json` + Gramps).
Odvozené obrázky (kontrastní kopie apod.) zůstávají jen v `sources/`, do Gramps se nedávají. Operace: `add_event` (osoba, nebo `family: [K6, K7]`), `update_event` (`event: <handle>` +
`description`/`date`/`place`/`type`; u `add_event`/`update_event` lze místo `citation: c1` uvést víc citací
`citations: [c1, c2]`), `add_citation` (`event: <handle>` + `citation`), `remove_citation`
(`event: <handle>` + `citation_gramps_id`; nepoužívaná citace se smaže), `update_citation` (`citation_gramps_id` +
`page`/`confidence`), `add_family_citation` (`family: [otec, matka]` + `citation`/`citations` — doklad vazby
rodiče → dítě nebo manželství), `add_media` (`file`, `citation`). Sidecar ústního sdělení uživatele
(`type: ústní sdělení`, informátor Vojtěch Bereščák) se zapíše pod společný zdroj `S-USTNE-K0001`.
Zdroj v Gramps = původní fotka dokladu z pole `original` sidecaru (`S-IMG_3967`), jinak název souboru —
kopie téhož dokladu u jiné osoby (i přejmenovaná) duplikát nezaloží, pokud má v sidecaru stejné `original`. Stejná citace (zdroj + `page` + jistota) se znovu
použije, nezakládá se duplikát.
Handly událostí jsou v sekci `applied:` dřívějších patchů.

**Typy událostí (pozor na českou lokalizaci Gramps):** křest dítěte = **`Christening`** („Křest“, GEDCOM CHR),
**ne `Baptism`** (česky „Baptistické křtiny“ — aplikátor ho odmítne); `Adult Christening` = „Křtiny dospělých“.
Ostatní: `Birth` (Narození), `Marriage` (Sňatek), `Divorce` (Rozvod), `Death` (Úmrtí), `Burial` (Pohřeb),
`Residence` (Bydliště), `Occupation` (Povolání), `Census` (Sčítání lidu), `Religion` (Náboženství). Hodnoty s dvojtečkou v YAML
dávej do uvozovek.

**Patch se vede průběžně a je informačně bohatý** (pravidla od uživatele):
- patch upravuj **pokaždé, když uživatel něco potvrdí** — ne až na konci výzkumu (status zůstává `navrženo`,
  nepotvrzené části označ komentářem; `schváleno` až uživatel řekne ok k zápisu);
- zapisuj **všechno potvrzené**, i nestrukturované údaje — kmotři, svědci, oddávající/křtitel, porodní bába,
  č. p., stav a povolání, příbuzní uvedení v zápisu, poznámky matrikáře → do `description` události
  (případně do další události: `Occupation`, `Residence`, `Religion`).
- **Popis vs. kontext:** `description` = jen to, co záznam říká **o této osobě**, stručně (vidí se v seznamu
  událostí: „obuvník, Žiželice č. 300“). Vše ostatní ze záznamu — domácnost, rodiče, děti, kmotři, svědci,
  oddávající, poznámky — patří do pole **`context`** (aplikátor z něj udělá poznámku k události).
  Údaj převzatý ze záznamu příbuzného označ v popisu krátce v hranatých závorkách:
  „rolník, Žiželice č. 300 [z oddacího listu syna Josefa]“.
- **Náboženství** = událost `Religion` (datum a místo záznamu, popis „římskokatolické“); přestup = další
  `Religion` s popisem („přestup do Církve československé“).

Manager patch zkontroluje, aplikuje do Gramps, doplní `gramps_id` do dossieru, nastaví `stav: zapsáno`
a commitne.

## Autonomní režim (na pokyn uživatele)

Pravidla čtení, totožnosti, jistoty a **fronty kontrol** jsou v [`autonomie.md`](autonomie.md). Autonomní
session uživateli nic ke kontrole do tabu neposílá. Co stroj nerozhodne, jde do `research/kontroly/` a
uživatel to vyřizuje v dashboardu. Souhrnný patch má `status: schváleno` (hromadný souhlas) a manager ho
aplikuje bez další kontroly. Poprvé: K0448–K0451, 2026-10-16.

## Session větve

Autonomní session nemusí být na jednu osobu: **session větve** zpracuje jednu rodovou linii **do hloubky**
(otec → jeho otec …, u každé generace i manželku a vlastní sourozence z týchž matrik), protože generace
jedné linie sdílejí farnost, svazky, rejstříky a čísla popisná. Do šířky (jiná příjmení, jiné farnosti)
se větví nestaví — na to je další session. Pravidla čtení a jistoty: [`autonomie.md`](autonomie.md).

- Píše do souborů osob své větve (dossiery, `sources/<ID>/`, `patches/P-<ID>-nn.yml`, `research/kontroly/`),
  o založení osob a rodin větve (`ensure_persons.py`, `ensure_family.py --no-oral`, `add_person.py` — struktura
  bez faktů) žádá managera, klidně dávkově (session to auto-mode zamítá). Fakta jen patchem přes managera.
- **Patch po každé osobě** (ne až na konci větve) → manager aplikuje průběžně.
- Konec: hranice pramenů, jiný archiv bez přístupu, rozpočet, nebo **plný kontext** — pak zapíše do dossieru
  poslední osoby `## Předání` (co dál, kde) a ohlásí managerovi, ten otevře navazující session.
