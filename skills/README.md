# Skills

Opakovatelné postupy pro Claude Code. Složka je nalinkovaná do `.claude/skills/`.

| Skill | Účel | Stav |
|---|---|---|
| `research-person` | výzkum jedné osoby v osobní session (checklist, hledání, přepis, patch) | **v1** |
| `read-record` | trojí čtení zápisu (Claude + OpenAI + PERO) a porovnání po polích | **v1** (nástroje ve výstavbě) |
| `research-plan` | otázka → plán hledání podle checklistu osoby → úkoly | plán |
| `find-record` | najdi svazek a stránku pro osobu/událost přes `czech-archives`, zapiš log | plán |
| `transcribe-record` | snímek → reader (Claude + OpenAI) → přepis 4 vrstvy + JSON → označit neshody | plán |
| `add-fact` | ověřený fakt + citace → patch do `patches/` | plán |
| `import-myheritage` | nový export → lokalizace médií → diff → nápovědy do `hints/` | plán |
| `audit-tree` | nesmysly, duplicity, chybějící citace, nejednotná místa | plán |
