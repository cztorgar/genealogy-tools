# Playbooky pro AI agenta

Postupy krok za krokem pro libovolného agenta (Claude Code, Codex, Cursor, Gemini CLI…). Obecná pravidla jsou
v [`AGENTS.md`](../../AGENTS.md) a platí vždy. Playbook říká, **co dělat a v jakém pořadí**. Metodika
(`docs/metodika/`) vysvětluje **proč** a drží přesné formáty.

Každý playbook má stejnou kostru: **Kdy** · **Vstup** · **Kroky** · **Výstup** · **Nesmíš** · **Hotovo, když**.

| playbook | kdy | role |
|---|---|---|
| [`zalozeni-stromu.md`](zalozeni-stromu.md) | nový strom: šablona, výchozí osoby, import nápověd | manager |
| [`vyzkum-osoby.md`](vyzkum-osoby.md) | prozkoumat jednu osobu do zelené | výzkum osoby |
| [`cteni-zapisu.md`](cteni-zapisu.md) | přečíst snímek zápisu a zapsat přepis | kdokoli |
| [`vetev.md`](vetev.md) | autonomně projít jednu rodovou linii do hloubky | větev |
| [`manager.md`](manager.md) | dávka: aplikace patchů, syncy, fronta, commit | manager |
| [`kontroly.md`](kontroly.md) | založit otázku na uživatele a zapracovat jeho rozhodnutí | kdokoli / manager |
| [`portaly.md`](portaly.md) | najít svazek a snímek v archivu; portály s ochranou proti robotům | kdokoli |
| [`zavory-a-zadosti.md`](zavory-a-zadosti.md) | sepsat závoru, odhadnout obtížnost, připravit dopis do archivu | výzkum osoby |
| [`zafixovani-stavu.md`](zafixovani-stavu.md) | export Gramps, commit, tag | manager |
| [`orchestrace.md`](orchestrace.md) | volitelně: víc sessions najednou (herdr), parkování, limity účtů | manager |

Skills v `skills/*/SKILL.md` jsou podrobné verze dvou playbooků: `research-person` (výzkum osoby) a `read-record`
(čtení zápisu). Claude Code je spouští jako `/research-person K0042`. Jiný agent si `SKILL.md` přečte jako
návod. Místo `herdr agent prompt manager …` pak napiš zprávu uživateli.

## Společné zásady

- **Začni přehledem a počkej na „ok“**, pokud uživatel výslovně neřekl „autonomně“.
- **Jedna session = jedna osoba nebo jedna větev.** Neber práci, na které už běží jiná session (dashboard →
  Strom, odznak session).
- **Zapisuj průběžně**: log hledání po každém hledání, patch po každém potvrzeném faktu. Session může kdykoli
  skončit a další musí navázat jen ze souborů.
- **Při odchodu od osoby srovnej její `stav:`** v dossieru (rozpracováno → dokončeno / pozastaveno).
- **Když nevíš, zeptej se, nebo založ kontrolu.** Nehádej.
