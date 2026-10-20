# Příručka — jak s workbenchem pracovat

Pro člověka, který chce stavět vlastní rodokmen s pomocí AI agenta (Claude Code, Codex, Cursor…). Pravidla pro
samotného agenta jsou v [`AGENTS.md`](../AGENTS.md) a jeho postupy v [`playbooky/`](playbooky/README.md).

## 1. Co to je

Sada nástrojů a postupů pro **doložený** rodokmen z českých pramenů: matriky, sčítání lidu, pozemkové knihy,
noviny. Princip:

- **Strom se staví od nuly, osoba po osobě.** Do stromu jde jen to, co má pramen. Cizí stromy
  (MyHeritage, Geni…) slouží jen jako nápovědy.
- **AI dělá rešerši, ty rozhoduješ.** Agent hledá v archivech, čte zápisy, navrhuje změny. Spornou totožnost,
  nejisté čtení nebo odeslání dopisu rozhodne člověk.
- **Všechno je dohledatelné.** Každý fakt má citaci, jistotu a odkaz na snímek. Každé hledání, i neúspěšné,
  je v logu.

## 2. Jak je to poskládané

```
 genealogy-tools/  (tohle repo, sdílené)          genealogy-trees/<strom>/  (tvoje repo, soukromé)
 ├─ AGENTS.md, CLAUDE.md  pravidla pro AI          ├─ TREE.md            o čem strom je
 ├─ docs/metodika/        jak se dokazuje          ├─ research/people/   dossier na každou osobu
 ├─ docs/archivy, prameny kde co hledat            ├─ research/log.md    log všech hledání
 ├─ docs/playbooky/       postupy pro AI           ├─ sources/<ID>/      snímky + citace (.yml)
 ├─ skills/               postupy (Claude skills)  ├─ transcriptions/    přepisy zápisů
 ├─ mcp/czech-archives    přístup k portálům       ├─ patches/           navržené změny stromu
 ├─ tools/                skripty, dashboard       ├─ research/kontroly/ otázky na tebe
 ├─ templates/strom/      šablona nového stromu    └─ data/gramps/       snímky stavu Gramps
 └─ infra/gramps-web/     Gramps Web (Docker)

                 Gramps Web (localhost:5055) = MASTER stromu, jen doložené osoby
                 Dashboard  (localhost:5056) = přehled: strom, fronta, kontroly, mapa
```

Tok jedné změny: **hledání** (agent, archivy) → **přepis** (snímek → text) → **dossier + log** →
**patch** (`status: navrženo`) → **aplikace** do Gramps (manager) → osoba se v dashboardu přebarví.

## 3. Instalace

Potřebuješ: Linux nebo macOS, `git`, [`uv`](https://docs.astral.sh/uv/) (Python ≥ 3.11 si stáhne sám),
Docker a AI agenta s podporou MCP (Claude Code doporučen, viz § 9).

```sh
git clone git@gitlab.com:geneaology/genealogy-tools.git genealogy
cp genealogy/genealogy.example.toml genealogy/genealogy.toml        # vyplníš v § 4

# Gramps Web
cd genealogy/infra/gramps-web && cp .env.example .env               # vyplň GRAMPS_MEDIA_DIR
docker compose up -d                                                # http://localhost:5055
docker compose exec grampsweb python3 -m gramps_webapi tree --help  # založení stromu
docker compose exec grampsweb python3 -m gramps_webapi user add --help
```

V Gramps Web založ strom a uživatele s rolí vlastníka (`--role 5`). Jméno a heslo zapiš do `.env`
(`GRAMPSWEB_ADMIN_USER/PASSWORD`). Pod tímhle účtem zapisují nástroje. Chceš-li mít importovaný strom
z MyHeritage jako referenci, založ druhý strom a účet (`GRAMPSWEB_REF_*`).

MCP servery se načtou z `.mcp.json`, když agenta spustíš ve složce workbenche. Pro jiné agenty než Claude
Code přenes stejnou konfiguraci do jejich nastavení MCP.

## 4. Založení stromu

```sh
cd genealogy
uv run tools/init_tree.py ../genealogy-trees/novak --nazev novak --k0001 "Jan Novák (*1980)"
```

Pak v `genealogy.toml` nastav `strom.adresar`, `strom.gramps_strom` a `badatel.jmeno`. Jméno badatele se
použije jako informátor u ústních sdělení („Ústní sdělení — Jan Novák“, jistota 3).

**Osoby a jejich ID.** Přímí předci mají čísla podle Kekuleho: K0001 = ty, K0002 otec, K0003 matka, K0004 otcův
otec… Vedlejší linie mají přípony: `-S1` manžel/ka, `-C1` dítě, `-P1`/`-P2` otec/matka (např. `K0001-S1-P1` =
tchán). ID se nikdy nemění.

- **Máš export z MyHeritage nebo jiný GEDCOM:**
  `uv run tools/research/build_queue.py export.ged @I1@ ../genealogy-trees/novak/research/people`
  založí dossiery přímých předků. Údaje z exportu jsou v nich jen jako nápovědy (jistota 0).
  Volby `--family-of` a `--parents-of` přidají vedlejší linie.
- **Začínáš od nuly:**
  `uv run tools/research/add_person.py ../genealogy-trees/novak K0001 --name "Jan Novák" --sex M --puvod ústně --rel "výchozí osoba"`
  a stejně tak rodiče, které znáš. Vazby založí `tools/gramps/ensure_family.py` s citací ústního sdělení.

Repo stromu si dej na vlastní **soukromý** GitLab/GitHub. Jsou v něm údaje o žijících lidech.

## 5. Denní práce

### 5.1 Fronta a cíl (fáze I)

Cíl: **každá osoba zelená**. Znamená to, že její základní checklist je uzavřený:

| položka | kdy |
|---|---|
| narození / křest | vždy |
| rodiče | vždy, jako osoby ve stromu, nebo závora |
| sňatek | ženatí a vdané |
| úmrtí / pohřeb | zemřelí |
| sčítání lidu 1857–1921 | ta, při kterých osoba žila |

Každá položka je **nalezena** (pramen v Gramps), nebo **nenalezena s důvodem**. Pořadí práce určuje
**fronta** (dashboard → záložka Fronta): nejdřív šedí (nezkoumaní), pak rozpracovaní. Uvnitř obou skupin jdou
přímí předci před vedlejšími liniemi, bližší generace dřív. Každá prozkoumaná osoba skončí buď s rodiči ve stromu,
nebo se **závorou**. Podrobně: [`metodika/fronta.md`](metodika/fronta.md),
[`metodika/checklist-osoby.md`](metodika/checklist-osoby.md).

### 5.2 Výzkum osoby

Řekni agentovi, kterou osobu má zkoumat. V Claude Code: `/research-person K0042`. Jinde: „zkoumej K0042 podle
`docs/playbooky/vyzkum-osoby.md`“. Agent:

1. vypíše **úvodní kartu** (co víme, odkud, co chybí) a navrhne plán. **Počká na tvoje „ok“.**
2. hledá v archivech, každé hledání zapíše do logu, snímky uloží do `sources/<ID>/` s citací,
3. zápisy přepíše a všechno potvrzené dá do **patche**,
4. kde nejde dál, napíše **závoru** (proč, co prohledal, co by pomohlo, obtížnost).

Tvoje práce: odsouhlasit plán, ověřit jména a data proti snímku, rozhodnout sporné body.

### 5.3 Kontroly: co rozhoduješ ty

Co agent sám nerozhodne (nejisté čtení, dva kandidáti na otce, rozpor), dá do `research/kontroly/`. V dashboardu
jsou v záložce **Kontroly** s variantami a doporučením. Vybereš variantu, případně připíšeš poznámku, a agent
rozhodnutí zapracuje. *Blokující* kontrola drží osobu, dokud ji nerozhodneš.

### 5.4 Manager: aplikace změn

Patche zapisuje do Gramps role **manager**. Může to být tvoje hlavní AI session, nebo ty sám. Jedna dávka:

```sh
uv run tools/gramps/apply_patch.py <strom> patches/P-K0042-01.yml --approve   # po kontrole obsahu
uv run tools/research/stav_sync.py && uv run tools/research/checklist_sync.py <strom>
uv run tools/research/kontext_flags.py && uv run tools/research/fronta.py
```

Pak commit repa stromu. Postup pro agenta: [`playbooky/manager.md`](playbooky/manager.md).

### 5.5 Závory a jejich obtížnost

| obtížnost | znamená |
|---|---|
| nízká | pramen je online, jen se ještě nehledalo |
| střední | online pracně (bez rejstříku, stovky snímků), nebo je potřeba dopis do archivu či doklad od rodiny |
| velká | matriky se nedochovaly; zbývají nepřímé prameny (pozemkové knihy, katastry) |

Závory s nízkou obtížností jsou nejlevnější další práce. U střední připraví agent **koncept dopisu** do archivu
nebo otázku pro rodinu (`research/todo-rodina.md`). Posíláš ji ty.

### 5.6 Doklady z domova

Rodné, oddací a úmrtní listy, parte, fotky: sken dej do `doklady/` ve stromu. Agent ho zařadí k osobě a odškrtne
v `research/doklady.md`. Ten seznam ti říká, co je dobré u příbuzných sehnat.

### 5.7 Zafixování stavu

Před velkou změnou nebo jednou týdně: export Gramps (`uv run tools/gramps/export_snapshot.py <strom>`),
commit a tag `stav-YYYY-MM-DD` v repu stromu. Gramps Web je master. Bez exportu není jeho obsah v gitu.

## 6. Dashboard

`uv run tools/dashboard/server.py` (strom bere z `genealogy.toml`) → http://localhost:5056

- **Strom** — rodokmen obarvený podle stavu. Kliknutím na osobu otevřeš panel: přehled, život, prameny, práce.
- **Fronta** — pořadí práce, otevřené položky, obtížnost závor.
- **Kontroly** — tvoje rozhodnutí.
- **Mapa** — kde rodina žila, s historickými mapami.

| barva | stav |
|---|---|
| šedá | zmínka / převzato: nikdo ještě nezkoumal |
| žlutá | rozpracováno: agent na osobě právě pracuje |
| fialová | pozastaveno: čeká na doklad, kontrolu nebo přístup |
| modrá | dokončeno: patch čeká na aplikaci |
| světle zelená | zapsáno v Gramps, checklist ještě neúplný |
| zelená | uzavřeno: fáze I hotová |

## 7. Co hlídat

- **Jistota.** Čtení jedním modelem má jistotu nejvýš 1. Zvýší ji až tvé ověření proti snímku. Neověřená jména
  v knize nebo na webu jsou nejčastější zdroj chyb v rodokmenech.
- **Portály.** Agent nesmí obcházet ochrany archivů. CAPTCHA a přihlášení řešíš ty. Stahování celých svazků je
  zakázané.
- **Náklady.** Čtení snímků je drahé (obrázky v kontextu). Nespouštěj paralelní agenty nad snímky. Jedna
  session na jednu osobu nebo větev je dost. Hlídej limity účtu.
- **Soukromí.** Data stromu do LLM posíláš na vlastní odpovědnost a se souhlasem rodiny. Při sdílení
  a publikování vynech žijící osoby.

## 8. Kde co najdeš

| hledám | soubor |
|---|---|
| jak dokazovat, citovat, číst | [`metodika/`](metodika/) (začni `dukazni-standard.md`, `citace.md`, `prepis.md`) |
| jaké prameny existují | [`prameny/`](prameny/) |
| jak funguje konkrétní archiv | [`archivy/`](archivy/) |
| farnosti a obce (ukázkový region Chlumecko) | [`mistopis/`](mistopis/) |
| formát dossieru, patche, závory, role | [`metodika/workflow-sessions.md`](metodika/workflow-sessions.md) |
| autonomní práce bez dohledu | [`metodika/autonomie.md`](metodika/autonomie.md) |
| nástroje | `tools/*/README.md`, [`nastroje/`](nastroje/) |

## 9. Který agent

Postupy jsou psané obecně (Markdown). Nejlépe vyzkoušené jsou s **Claude Code**: skills, MCP, Claude in Chrome
pro portály s ochranou proti robotům. Jiný agent (Codex, Cursor, Gemini CLI…) si přečte `AGENTS.md` a playbooky.
Potřebuje jen podporu MCP (`czech-archives`) a přístup k souborům a shellu. Bez prohlížeče ovládaného agentem
nepřečte portály s ochranou proti robotům (Třeboň, Matricula). Ty pak čteš sám.
