# Playbook: výzkum osoby

**Kdy:** uživatel řekne „zkoumej K0042“, nebo je osoba na řadě ve frontě (`research/fronta.md`).
**Podrobná verze:** [`skills/research-person/SKILL.md`](../../skills/research-person/SKILL.md). Tenhle playbook
je její zkrácená kostra pro libovolného agenta.

## Vstup

- ID osoby (`K0042`, `K0001-S1-P2`). Strom z `genealogy.toml` (`python3 tools/wbconfig.py get strom.adresar`).
- Přečti: `AGENTS.md`, `docs/metodika/workflow-sessions.md`, `dukazni-standard.md`, `citace.md`, `prepis.md`,
  `checklist-osoby.md`.

## Kroky

1. **Kontext.** Dossier `research/people/<ID>-*.md`, dossiery rodičů a dětí (jen čtení), nápovědy
   `research/hints/<ID>-*`, otevřené kontroly `research/kontroly/<ID>-*.yml` (rozhodnuté zapracuj jako první),
   log hledání osoby (`grep <ID> research/log.md`), už aplikované patche `patches/P-<ID>-*.yml`.
2. **Úvodní karta.** Co víme (údaj, hodnota, jistota, zdroj), rodiče, manžel/ka, děti, soubory a otevřené
   položky checklistu. Navrhni plán: které prameny, v jakém pořadí, proč. **Počkej na souhlas.**
3. **Stav** v dossieru → `rozpracováno`.
4. **Hledání** podle checklistu, od nejjistějších pramenů (matriky N/O/Z, sčítání). Místo → farnost →
   archiv → svazek: `docs/mistopis/`, MCP `czech-archives` (`find_registers`, `register_info`), postup
   v [`portaly.md`](portaly.md). **Každé hledání hned do `research/log.md`**, i bez výsledku.
5. **Snímek** ulož do `sources/<ID>/` se sidecarem `.yml` (citace, URL snímku i svazku). **Přepis** podle
   [`cteni-zapisu.md`](cteni-zapisu.md) do `transcriptions/<ID>-*.md`.
6. **Přiřazení.** Záznam patří osobě, jen když kromě jména sedí ≥ 2 nezávislé údaje. Jinak kontrola typu
   `totoznost` ([`kontroly.md`](kontroly.md)).
7. **Patch** `patches/P-<ID>-<nn>.yml` (`status: navrženo`) doplňuj průběžně po každém potvrzeném faktu.
   Formát a typy událostí najdeš ve `workflow-sessions.md` (pozor: křest = `Christening`, ne `Baptism`).
8. **Nové osoby** (rodiče z pramene, sourozenci, druhý manžel): ID podle schématu (`-P1/-P2/-S<n>/-C<n>`).
   Založení (`add_person.py`, `ensure_family.py --no-oral`) dělá manager. Napiš mu přesné příkazy.
9. **Checklist** v dossieru: u každé položky `[x]` (doloženo) nebo `[-]` + důvod. Známý, ale neprohledaný pramen
   zůstává `[ ]` s poznámkou, kde hledat.
10. **Závora**, když linie nejde dál: [`zavory-a-zadosti.md`](zavory-a-zadosti.md).
11. **Konec.** Sekce `## Kontext` v dossieru, stav `dokončeno` (nebo `pozastaveno` + důvod, když čeká
    blokující kontrola či doklad). Zpráva managerovi a uživateli: co je v patchi, kolik kontrol, co nenalezeno.

## Výstup

Dossier (checklist, log, kontext, případně závora), `sources/<ID>/`, `transcriptions/`, patch `navrženo`,
případně kontroly, nápovědy pro jiné osoby (`research/hints/<cíl>-<datum>-od-<ID>.md`), řádek do
`research/todo-rodina.md`.

## Nesmíš

Zapisovat do Gramps, commitovat, měnit workbench, psát do cizích dossierů, upravovat aplikovaný patch,
číst snímky paralelními podagenty, stahovat celé svazky.

## Hotovo, když

Každá položka základního checklistu je `[x]`, nebo `[-]` s platným důvodem. Rodiče jsou založení, nebo je
napsaná závora s obtížností. Patch čeká na managera a stav dossieru odpovídá skutečnosti.
