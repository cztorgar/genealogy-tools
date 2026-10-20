# Playbook: orchestrace více sessions (volitelné)

Pro pokročilé: víc AI sessions najednou (manager + osoby / větve) v terminálovém multiplexeru
herdr s Claude Code. **Bez toho se dá pracovat v jedné session**, která role střídá.

**Potřebuje:** herdr, `jq`, Claude Code. Pro střídání účtů také vlastní nástroj `claude-account` (přepíná
credentials) a `genealogy.toml` → `[sessions] ucty`, `ucty_bez_chrome`.

| skript | co dělá |
|---|---|
| `tools/sessions/open_person.sh <ID>` | nový tab se session osoby, spuštěný `/research-person` |
| `tools/sessions/park.sh <jméno> \| --idle` | uloží Claude session ID a zavře tab (šetří paměť) |
| `tools/sessions/unpark.sh <jméno> ["zpráva"]` | obnoví session s kontextem (`claude --resume`) |
| `tools/sessions/usage_guard.sh [práh]` | při limitu účtu pošle sessions pauzu |
| `tools/sessions/night_shift.sh` | noční běh: pauza → zaparkovat → přepnout účet → obnovit |
| `tools/sessions/tab_label.py` | název tabu „K0056 Jméno *1848“ |

## Pravidla

- Manager je tab a agent `manager`. Zprávy: `herdr agent prompt manager "K0042: …"` (bez `--wait`).
- Session zavírá a parkuje manager: jen hotové nebo pozastavené, **nikdy pracující**, nikdy manager ani dashboard.
- Na každou osobu nebo větev jedna session. Před otevřením zkontroluj, že na ní nikdo nepracuje.
- **Náklady:** každá session s obrázky v kontextu je drahá. Žádné paralelní podagenty nad snímky. Víc sessions
  najednou spouštěj jen s vědomím limitů účtu (dashboard ukazuje stav sessions).
- Model: na čtení kurentu a rozhodování totožnosti nejsilnější model. Slabší model čte kurent výrazně hůř
  (`docs/nastroje/reader.md`).
