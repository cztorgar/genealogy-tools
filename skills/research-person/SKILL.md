---
name: research-person
description: Výzkum jedné osoby stromu v samostatné session — projde checklist, hledá v pramenech, přepisuje záznamy, vede log a připraví patch pro managera. Použij, když uživatel napíše "/research-person K0042" nebo "zkoumej K42".
---

# Výzkum osoby

Argument: číslo osoby (`K42`, `K0042`) a volitelně cesta ke stromu (výchozí `strom.adresar`
z `genealogy.toml`, viz `python3 tools/wbconfig.py get strom.adresar`). Jsi **osobní session** — pravidla v
`docs/metodika/workflow-sessions.md` (co smíš zapisovat). Komunikuj česky.

## 1. Načti kontext

1. `AGENTS.md`, `docs/metodika/workflow-sessions.md`, `dukazni-standard.md`, `citace.md`, `prepis.md`.
2. Dossier `research/people/<ID>-<slug>.md` (slug začíná malým písmenem — `K0001-jan-…`, ne `K0001-C1-…`).
3. Kontext (jen čtení): u přímého předka dossiery rodičů (K×2, K×2+1) a dítěte (K÷2); u vedlejší linie
   (`K0001-S1`, `K0002-C1-C2`) dossier kotvy (část ID před posledním `-S<n>`/`-C<n>`) a jejích dalších
   manželů/dětí (`research/people/README.md`, sekce Vedlejší linie).
4. Nápovědy pro tuto osobu: `research/hints/K<nnnn>-*.md`.
5. Pokud chceš porovnat se starým stromem: Gramps strom `myheritage-ref` (čtení).

## 2. Úvodní karta (vždy jako první výstup, ještě před jakoukoli prací)

Vypiš uživateli přehled — **nic nehledej, dokud ho uživatel neviděl**:

```
## K42 · Jan Novák  (otec → matka → otec → matka → otec, generace 6)
Stav: převzato (původ: myheritage) · Gramps (master): nezapsán · MyHeritage: I500150

### Co víme
| Údaj | Hodnota | Jistota | Zdroj |
|---|---|---|---|
| narození | 17. 7. 1841, Lhota č. 10 | 0 | MyHeritage (Smart Match) |
| ...
Rodiče: Josef Novák (K84, stav …), Terezie Svobodová (K85, stav …)
Manželka: Magdaléna Dvořáková (K43) · Děti: … (K21 = naše linie)

### Co máme za soubory
- dossier: research/people/K0042-jan-novak.md
- nápovědy: research/hints/K0042-… (počet, od koho)
- snímky: sources/K0042/ (počet) · přepisy: transcriptions/K0042-* · patche: patches/P-K0042-*
- fotky: media/… (z dossieru, sekce Média)
- odkazy do archivů z poznámek: …

### Checklist
základní: nalezeno x · nenalezeno y · neprohledáno z (vypsat neprohledané) · rozšířený jen souhrnně

### Odloženo (vědomě neřešeno)
- … (ze sekce Odloženo v dossieru — připomenout, ať se to omylem nehledá znovu)

### Slabá místa a rozpory
- …
```

Zdroje pro kartu: dossier, dossiery rodičů a dítěte (jejich `stav:`), `research/hints/K<nnnn>-*`,
výpis souborů v `sources/K<nnnn>/`, `transcriptions/K<nnnn>-*`, `patches/P-K<nnnn>-*`; je-li osoba už
v Gramps master stromu (`gramps_id` v dossieru), načti její doložená fakta a ukaž je s jistotou z citací.

Pak navrhni plán (viz níže) a **počkej na pokyn uživatele**.

## 3. Začni

- Až uživatel odsouhlasí plán: nastav v dossieru `stav: rozpracováno` a pošli managerovi zprávu
  `herdr agent prompt manager "K0042 Jan Novák: začínám"` (bez herdr: napiš to uživateli).
- Pořadí hledání:
  1. odkazy do archivů z poznámek (už někdo něco našel),
  2. **základní checklist** ([fáze I](../../docs/metodika/faze-vyzkumu.md)): křest (N) → rodiče → sňatek (O) →
     úmrtí (Z) → sčítání lidu v jeho životě. Úmrtí známé jen nepřímo („† otec“ v zápisu dítěte, vdovec)
     navrhni patchem jako Death `BEF …` / `BET … AND …`. Sčítání po něm z checklistu zmizí samo.
  3. rozšířený checklist (fáze II) jen na pokyn.
- U osob mladších 100 let (N) / 75 let (O, Z) se zeptej na **rodinné doklady** — online matriky nejsou.

### Sdílené seznamy `research/todo-*.md`

- `todo-hroby.md` — hroby k návštěvě (data na desce, další jména, číslo hrobu)
- `todo-pozemkove-knihy.md` — nemovitosti / pozemkové knihy (převody, výměnky); celý seznam nízká priorita
- `todo-rodina.md` — otázky na příbuzné (vzpomínky, doklady doma, parte); odpověď = ústní sdělení, do stromu přes patch
- `todo-<rod>.md` (např. `todo-vrbicti.md`) — vedlejší větve rodu, které strom eviduje (pokyn v `TREE.md`): každý nalezený člen mimo zkoumanou linii

Zápis podle šablony v hlavičce souboru — **jen připsáním na konec** (`cat >> …`). Změny existujícího
záznamu nebo nový typ seznamu → napiš managerovi.

### Doklady k dohledání

Každý doklad, který musí uživatel sehnat, zapiš do sekce `## Doklady k dohledání` **svého** dossieru:

```
- [ ] oddací list 2018 — Jan Novák × Marie Svobodová | potvrdí: datum a místo sňatku, rodiče snoubenců | kde: doma
```

- Název dokladu piš **jednotně** (`rodný list — <jméno>`, `oddací list <rok> — <on> × <ona>`,
  `úmrtní list — <jméno>`, `rozvodový rozsudek <rok> — …`) — stejný doklad u dvou osob se pak v přehledu sloučí.
- `kde`: `doma` · `u rodičů` · `u prarodičů` · `matriční úřad <obec>` · `soud <obec>` · `archiv <název>` · `neurčeno`.
- Když doklad dorazí (sken v `../genealogy-trees/<strom>/doklady/`), přesuň ho do `sources/<ID>/`,
  udělej sidecar citaci a změň řádek na `[x]` s cestou k souboru. Nesehnatelné = `[-]` + důvod.
- Po změně spusť regeneraci přehledů (deterministická, smí kdokoli):
  `python3 tools/research/build_queue.py ../genealogy-trees/<strom>/data/exports/myheritage/2026-10-16.ged @I500003@ ../genealogy-trees/<strom>/research/people`
  → aktualizuje `research/doklady.md` a frontu.

## 4. Hledání

- Najdi správný svazek: obec + rok → farnost → archiv (`docs/archivy/`, místopis `docs/metodika/mista.md`).
  Jakmile existuje MCP `czech-archives`, použij `find_registers` / `fetch_page`.
  Do té doby: dej uživateli přesný odkaz na svazek a požádej o snímek / screenshot stránky
  (nebo ji otevři přes Claude in Chrome, pokud to uživatel chce).
- Snímek ulož do `sources/K<nnnn>/` + sidecar `.yml` s citací (vzor v `citace.md`).
- **Tisk (noviny, adresáře, věstníky, vlastivědy) — MCP `kramerius_*`:** až po matrikách, u předků dospělých
  v letech ~1880–1950 (parte, adresáře, spolky, úřední oznámení). Postup: `kramerius_plan(tree_dir, ID)` vygeneruje
  tvary příjmení, obce a časové okno → dotazy spouštěj **po jednom** přes `kramerius_search` (obec nikdy samotnou;
  u šumových obcí proximity 5) → zajímavou stránku přečti `kramerius_page_text` a jméno ověř proti snímku.
  Nález je **nápověda (jistota 0)**: nejdřív totožnost (pravidlo jmenovce, dva nezávislé údaje), pak teprve patch.
  Nápovědy ulož do `research/hints/` (citace + URL stránky z výsledku), každý dotaz včetně „nenalezeno“ do `research/log.md`.
  Žijící a po ~1932 narození: plán vrátí prázdné okno — nehledej.
- **Každé hledání zapiš** do „Log hledání“ v dossieru — i „nenalezeno“ (svazek, roky, snímky).

## 5. Přepis

- Snímek přečti skillem `read-record` (trojí čtení Claude + OpenAI + PERO a porovnání po polích).
- Výsledek do `transcriptions/K<nnnn>-<udalost>-<rok>.md` (4 vrstvy) + `.json` (pole s `raw`, `value`,
  `confidence`).
- Jména a data **ukaž uživateli proti snímku** a nech potvrdit — přepis je draft.

## 6. Vyhodnocení

- Pravidlo jmenovce: kromě jména aspoň dva nezávislé údaje. Rozpory s nápovědami z MyHeritage
  zapiš do „Výzkum“ v dossieru a nech rozhodnout uživatele.
- Odškrtej checklist: `[x]` nalezeno (zapsané v Gramps se doplní samo), `[-]` nenalezeno **s důvodem za pomlčkou**
  (co prohledáno) nebo závorou. Neměň klíč ani štítek (`docs/metodika/checklist-osoby.md`).
- Co se s uživatelem **vědomě rozhodnete neřešit**, zapiš do `## Odloženo (vědomě neřešeno)`:
  `- YYYY-MM-DD · **co** — proč / kde · kdo rozhodl` (odkaz na `todo-*` seznam, pokud tam je).
- Co jsi zjistil o **jiných osobách** (rodiče ze záznamu o křtu, sourozenci, č. p.), zapiš jako nový
  soubor `research/hints/K<cíl>-<YYYY-MM-DD>-od-K<nnnn>.md` s odkazem na přepis. Do cizích dossierů nepiš.

## 7. Patch a předání

- **Patch veď průběžně:** založ ho hned při prvním potvrzeném údaji a doplňuj ho **pokaždé, když uživatel
  něco potvrdí** (status `navrženo`, nepotvrzené části okomentuj). `schváleno` až na výslovné ok k zápisu.
- **Informačně bohatý, ale oddělený:** všechno potvrzené ze zápisu patří do patche. `description` = jen o této
  osobě, krátce (č. p., stav, povolání); kmotři, svědci, oddávající, porodní bába, domácnost, rodiče a další
  příbuzní ze zápisu → pole `context` (poznámka k události). Údaj ze záznamu příbuzného označ
  „[z oddacího listu syna Josefa]“. Náboženství = událost `Religion`.

- Typy událostí podle `workflow-sessions.md` (sekce Patch): křest = **`Christening`**, nikdy `Baptism`
  (v české lokalizaci Gramps „Baptistické křtiny“). Text s dvojtečkou v YAML dej do uvozovek.
- Až uživatel údaje proti snímku potvrdí, nastav v patchi `status: schváleno` (bez toho ho manager nezapíše).
- Až jsou základní fakta doložená (aspoň N, u ženatých O, u zemřelých Z — nebo co jde), vytvoř
  `patches/P-K<nnnn>-<nn>.yml` podle formátu ve `workflow-sessions.md`.
- Nastav `stav: dokončeno` a pošli managerovi zprávu (`herdr agent prompt manager "K0042: patch patches/P-K0042-01.yml — <shrnutí>"`).
- Když se zasekneš (chybí pramen, potřeba modulu archivu), nastav `stav: pozastaveno`, popiš proč
  v dossieru a dej vědět managerovi.

Jinou osobu (např. manželku) smíš převzít, jen když chce uživatel a ta osoba nemá vlastní session —
pravidla v `workflow-sessions.md`, sekce Převzetí jiné osoby.

Do Gramps (master) nezapisuj, necommituj a neměň workbench — to dělá manager.

## Autonomní režim

Když manager (na pokyn uživatele) řekne „autonomně“: řiď se `docs/metodika/autonomie.md`. Uživateli do tabu
nic ke kontrole neposílej, intro kartu jen vypiš a pokračuj. Sporné čtení, totožnost a rozpory zapiš jako
kontroly `research/kontroly/<ID>-<nn>.yml` (formát tamtéž). Na blokující kontrole nestav další generaci.
V patchi uváděj u každé události **všechny** zápisy, které údaj potvrzují (počet nezávislých pramenů).

## Kontext a příběh

Průběžně zapisuj do dossieru sekci `## Kontext` (surové poznámky s odkazem na pramen: epidemie, přípisky,
kmotři, stěhování, gramotnost, zajímavosti o obci) — hned, ne až na konci. Při dokončení osoby napiš
`research/pribehy/<ID>.md` — krátký článek bez fikce, každé tvrzení s oporou. Pravidla a šablona:
`docs/metodika/pribehy.md`.

## Závora

Když se linie nebo osoba zastaví (nic dál nejde, nebo končíš session), zapiš do dossieru poslední osoby sekci
`## Závora` — kde to končí, proč (typ závory), co bylo prohledáno bez výsledku, co by ji prolomilo a s jakou šancí.
Formát: `docs/metodika/workflow-sessions.md`, oddíl Závora.

## Log hledání — negativní výsledky

U každého „nenalezeno“ (dossier `## Log hledání` i `research/log.md`) uveď kromě rozsahu i **hledané jméno a varianty**,
**proč na absenci záleží** (co z ní plyne — např. „rodina se přistěhovala“, „křest bude jinde“) a **co zkusit příště**.
Přepis: jednotné značky nejistoty z `docs/metodika/prepis.md` (`[?]`, `[a/b?]`, `{^vpisek^}`, `[přeškrtnuto: …]`, `[okraj: …]`).
