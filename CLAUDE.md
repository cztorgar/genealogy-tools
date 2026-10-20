@AGENTS.md

# Doplněk pro Claude Code

- **Skills** (`skills/`, nalinkované do `.claude/skills/`): `/research-person K0042` (výzkum osoby),
  `read-record` (čtení zápisu). Skill je zároveň playbook, takže ostatní AI čtou stejný `SKILL.md`.
- **MCP** (`.mcp.json`): `czech-archives` (portály českých archivů, cache, šetrné tempo) a `genealogy`
  (kalendáře, svátky, varianty jmen, `check_match`, příbuznost, koncepty žádostí do archivů).
- **Claude in Chrome**: jen pro portály, které blokují roboty (§ 4 v AGENTS.md). Prohlížeč v jednu chvíli
  ovládá jen jedna session a jen tehdy, když je uživatel u počítače.
- **Subagenti**: smí hledat v souborech a dokumentaci. **Nikdy nesmí číst snímky** (viz § 2).
- Volitelná orchestrace více sessions (herdr, parkování, noční směna): [`docs/playbooky/orchestrace.md`](docs/playbooky/orchestrace.md).
- Osobní nastavení konkrétního uživatele patří do `CLAUDE.local.md` (je v .gitignore), ne sem.
