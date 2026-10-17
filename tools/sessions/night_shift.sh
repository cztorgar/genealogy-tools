#!/usr/bin/env bash
# Noční směna: drží výzkumné session v běhu na dvou účtech Claude.
# Když aktivní účet dosáhne prahu (5h okno), session pozastaví, zaparkuje, přepne aktivní účet na druhý (pokud má
# rezervu) a session obnoví s kontextem (unpark → claude --resume) — poběží na novém účtu. Když jsou oba účty
# vyčerpané, čeká na reset (resets_at z cache), pak přepne a obnoví. Manager ani dashboard se neparkují.
#
# Použití: night_shift.sh [práh=90] [interval_s=60] [regex session='^(predci-|vetev-|prameny-|kramerius|htr)']
set -uo pipefail
limit=${1:-90}; interval=${2:-60}; only=${3:-'^(predci-|vetev-|prameny-|kramerius|htr)'}
dir=$(cd "$(dirname "$0")" && pwd)
log="$HOME/.cache/genealogy-workbench/night_shift.log"; mkdir -p "$(dirname "$log")"
say() { echo "$(date +%F\ %H:%M) $*" | tee -a "$log"; }

util() {   # využití 5h okna účtu; po resets_at bere 0
  local f="$HOME/.cache/claude-cache-missing"; f="$HOME/.claude/cache/usage-$1.json"
  jq -r --argjson now "$(date +%s)" '
    (.five_hour.resets_at // null) as $r
    | if $r != null and (($r | sub("\\.[0-9]+";"") | sub("\\+00:00$";"Z") | fromdateiso8601) < $now) then 0
      else (.five_hour.utilization // 0) end' "$f" 2>/dev/null || echo 0
}
active() { claude-account list 2>/dev/null | awk '/aktivní/{print $1; exit}'; }
other() { [ "$1" = osobni ] && echo pracovni || echo osobni; }
running() { herdr agent list 2>/dev/null | jq -r '.result.agents[] | select((.cwd // "") | test("genealogy"))
            | select(.name != null and .name != "manager" and .name != "dashboard") | .name' | grep -E "$only"; }

parked_round=()
pause_and_park() {
  local msg="manager — PAUZA (limit účtu $1 ${2} %): dokonči rozdělaný krok, ulož (přepisy, sidecary, log, patch jako navrženo, Předání), pak ZASTAV. Budeš obnoven(a) s kontextem na druhém účtu."
  mapfile -t parked_round < <(running)
  [ ${#parked_round[@]} -gt 0 ] || return 0
  for a in "${parked_round[@]}"; do herdr agent prompt "$a" "$msg" >/dev/null; done
  for i in $(seq 1 30); do sleep 30
    busy=$(herdr agent list 2>/dev/null | jq -r '.result.agents[] | select(.agent_status == "working") | .name' | grep -cE "$only"); [ "$busy" = 0 ] && break; done
  "$dir/park.sh" "${parked_round[@]}" | tee -a "$log"
}
resume_round() {
  for a in "${parked_round[@]}"; do
    "$dir/unpark.sh" "$a" "manager: pauza končí (přepnuto na účet $(active)) — pokračuj podle svého Předání / fronty." | tee -a "$log"
  done
  parked_round=()
}

say "start: práh $limit %, session '$only', aktivní $(active)"
waiting=0
while :; do
  cur=$(active); u=$(util "$cur"); alt=$(other "$cur"); ua=$(util "$alt")
  if [ $waiting = 0 ] && awk -v u="$u" -v l="$limit" 'BEGIN{exit !(u>=l)}'; then
    say "účet $cur na $u % → pauza a parkování"
    pause_and_park "$cur" "$u"; waiting=1
  fi
  if [ $waiting = 1 ]; then
    if awk -v u="$ua" -v l="$limit" 'BEGIN{exit !(u<l)}'; then
      claude-account "$alt" >/dev/null 2>&1 && say "přepnuto na $alt ($ua %) → obnovuji ${#parked_round[@]} session"
      resume_round; waiting=0
    elif awk -v u="$(util "$cur")" -v l="$limit" 'BEGIN{exit !(u<l)}'; then
      say "účet $cur se obnovil → obnovuji ${#parked_round[@]} session"; resume_round; waiting=0
    fi
  fi
  sleep "$interval"
done
