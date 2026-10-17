#!/usr/bin/env bash
# Zaparkuje herdr session: uloží její Claude session ID (pro `claude --resume`) a zavře tab — uvolní paměť.
# Obnova: unpark.sh <jméno>. Stav: ~/.cache/genealogy-workbench/parked.tsv (jméno, session id, label tabu, cwd, čas).
#
# Použití: park.sh <jméno> [...]          zaparkuje jmenované (jen když nepracují — status idle/done)
#          park.sh --idle                 zaparkuje všechny nečinné session workbenche kromě managera a dashboardu
#          park.sh --force <jméno>        i když pracuje (nedoporučeno)
set -uo pipefail
state="$HOME/.cache/genealogy-workbench/parked.tsv"; mkdir -p "$(dirname "$state")"; touch "$state"
force=0; [ "${1:-}" = "--force" ] && { force=1; shift; }
if [ "${1:-}" = "--idle" ]; then
  mapfile -t names < <(herdr agent list 2>/dev/null | jq -r '.result.agents[] | select((.cwd // "") | test("genealogy"))
    | select(.name != null and .name != "manager" and .name != "dashboard") | select(.agent_status != "working") | .name')
else
  names=("$@")
fi
[ ${#names[@]} -gt 0 ] || { echo "nic k zaparkování"; exit 0; }
for n in "${names[@]}"; do
  info=$(herdr agent get "$n" 2>/dev/null) || { echo "✗ $n: neběží"; continue; }
  read -r status sid tab cwd < <(printf '%s' "$info" | jq -r '.result.agent | [.agent_status, (.agent_session.value // ""), .tab_id, .cwd] | @tsv')
  if [ "$status" = "working" ] && [ $force -eq 0 ]; then echo "↷ $n pracuje — nechávám"; continue; fi
  [ -n "$sid" ] || { echo "✗ $n: chybí session id — nezavírám"; continue; }
  label=$(herdr tab list 2>/dev/null | jq -r --arg t "$tab" '.result.tabs[]? | select(.tab_id == $t) | .label' 2>/dev/null)
  grep -v "^$n	" "$state" > "$state.tmp" 2>/dev/null; mv "$state.tmp" "$state"
  printf '%s\t%s\t%s\t%s\t%s\n' "$n" "$sid" "${label:-$n}" "$cwd" "$(date +%F\ %H:%M)" >> "$state"
  herdr tab close "$tab" >/dev/null && echo "⏸ $n zaparkována (resume $sid)"
done
