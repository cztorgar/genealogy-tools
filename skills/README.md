# Skills

Opakovatelné postupy pro Claude Code (složka je nalinkovaná do `.claude/skills/`). Jiní agenti čtou `SKILL.md` jako playbook, přehled je v [`../docs/playbooky/`](../docs/playbooky/README.md).

| Skill | Účel | Stav |
|---|---|---|
| `research-person` | výzkum jedné osoby v osobní session (checklist, hledání, přepis, patch) | **v1** |
| `read-record` | trojí čtení zápisu (Claude + OpenAI + PERO) a porovnání po polích | **v1** (nástroje ve výstavbě) |
| `precti-zapis` | odkaz na snímek + který zápis → list v plném rozlišení, výřez řádku, všechna pole, zařazení do stromu (předek / příbuzný / jmenovec) | **v1** |
| `research-plan` | otázka → plán hledání podle checklistu osoby → úkoly | plán |
| `find-record` | najdi svazek a stránku pro osobu/událost přes `czech-archives`, zapiš log | plán |
| `transcribe-record` | snímek → reader (Claude + OpenAI) → přepis 4 vrstvy + JSON → označit neshody | plán |
| `add-fact` | ověřený fakt + citace → patch do `patches/` | plán |
| `import-myheritage` | nový export → lokalizace médií → diff → nápovědy do `hints/` | plán |
| `audit-tree` | nesmysly, duplicity, chybějící citace, nejednotná místa | plán |
