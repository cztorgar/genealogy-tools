#!/usr/bin/env bash
# Hlídač limitů Claude účtu: když 5h nebo 7denní využití dosáhne prahu (výchozí 85 %), pozastaví všechny
# výzkumné session workbenche (herdr agenti s cwd v genealogy, kromě managera a dashboardu) a skončí.
# Využití čte z cache stavového řádku (~/.claude/cache/usage-<účet>.json, obnovuje ji statusline).
#
# Použití: usage_guard.sh [práh=85] [interval_s=60] [účet=aktivní] [regex agentů=vše]
#   Víc účtů: jeden hlídač na účet, s regexem agentů, kteří na něm běží (session drží účet, se kterým startovala).
set -uo pipefail
limit=${1:-85}; interval=${2:-60}; acct=${3:-}; only=${4:-.}
[ -n "$acct" ] || acct=$(claude-account list 2>/dev/null | awk '/aktivní/{print $1; exit}')
cache="$HOME/.claude/cache/usage-${acct:-osobni}.json"

while :; do
  read -r five week < <(jq -r '[(.five_hour.utilization // 0), (.seven_day.utilization // 0)] | @tsv' "$cache" 2>/dev/null || echo "0 0")
  if awk -v f="$five" -v w="$week" -v l="$limit" 'BEGIN{exit !(f>=l || w>=l)}'; then
    msg="manager — PAUZA (limit účtu ${acct}: 5h ${five} %, 7d ${week} %, práh ${limit} %): dokonči rozdělaný krok (ulož přepis/sidecar, log hledání, rozpracovaný patch jako navrženo), pak ZASTAV a čekej na pokyn. Nic nového nespouštěj."
    herdr agent list 2>/dev/null | jq -r '.result.agents[] | select((.cwd // "") | test("genealogy")) | select(.name != "manager" and .name != "dashboard") | .name' | grep -E "$only" |
      while read -r a; do herdr agent prompt "$a" "$msg" >/dev/null && echo "pauza → $a"; done
    echo "PAUZA provedena (${acct}): 5h ${five} %, 7d ${week} % (práh ${limit} %), cache $(date -r "$cache" +%H:%M)"
    exit 0
  fi
  sleep "$interval"
done
