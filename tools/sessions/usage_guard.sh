#!/usr/bin/env bash
# Hlídač limitů Claude účtu: když 5h nebo 7denní využití dosáhne prahu (výchozí 85 %), pozastaví všechny
# výzkumné session workbenche (herdr agenti s cwd v genealogy, kromě managera a dashboardu) a skončí.
# Využití čte z cache stavového řádku (~/.claude/cache/usage-<účet>.json, obnovuje ji statusline).
#
# Použití: usage_guard.sh [práh=85] [interval_s=60] [účet=aktivní] [regex agentů=vše] [přepnout_na_účet]
#   S 5. parametrem po pauze přepne aktivní účet (claude-account <účet>) — nové session pak poběží na něm.
#   Víc účtů: jeden hlídač na účet, s regexem agentů, kteří na něm běží (session drží účet, se kterým startovala).
set -uo pipefail
limit=${1:-85}; interval=${2:-60}; acct=${3:-}; only=${4:-.}; switch_to=${5:-}
[ -n "$acct" ] || acct=$(claude-account list 2>/dev/null | awk '/aktivní/{print $1; exit}')
cache="$HOME/.claude/cache/usage-${acct:-default}.json"

while :; do
  read -r five week < <(jq -r '[(.five_hour.utilization // 0), (.seven_day.utilization // 0)] | @tsv' "$cache" 2>/dev/null || echo "0 0")
  if awk -v f="$five" -v w="$week" -v l="$limit" 'BEGIN{exit !(f>=l || w>=l)}'; then
    msg="manager — PAUZA (limit účtu ${acct}: 5h ${five} %, 7d ${week} %, práh ${limit} %): dokonči rozdělaný krok (ulož přepis/sidecar, log hledání, rozpracovaný patch jako navrženo), pak ZASTAV a čekej na pokyn. Nic nového nespouštěj."
    herdr agent list 2>/dev/null | jq -r '.result.agents[] | select((.cwd // "") | test("genealogy")) | select(.name != "manager" and .name != "dashboard") | select(.agent_status == "working") | .name' | grep -E "$only" |
      while read -r a; do herdr agent prompt "$a" "$msg" >/dev/null && echo "pauza → $a"; done
    # po potvrzení pauzy (session přestanou pracovat) je zaparkuj — uvolní paměť; obnova unpark.sh
    for i in $(seq 1 20); do sleep 30; busy=$(herdr agent list 2>/dev/null | jq -r '.result.agents[] | select((.cwd // "") | test("genealogy")) | select(.name != "manager" and .name != "dashboard") | select(.agent_status == "working") | .name' | grep -cE "$only"); [ "$busy" = 0 ] && break; done
    "$(dirname "$0")/park.sh" --idle
    [ -n "$switch_to" ] && claude-account "$switch_to" >/dev/null 2>&1 && echo "přepnuto na účet $switch_to"
    echo "PAUZA provedena (${acct}): 5h ${five} %, 7d ${week} % (práh ${limit} %), cache $(date -r "$cache" +%H:%M)"
    exit 0
  fi
  sleep "$interval"
done
