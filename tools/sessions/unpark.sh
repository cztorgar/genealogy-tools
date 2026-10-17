#!/usr/bin/env bash
# Obnoví zaparkovanou session s celým kontextem (`claude --resume <id>`) v novém herdr tabu a pošle jí zprávu.
# Použití: unpark.sh <jméno> ["zpráva"]      |  unpark.sh --list
set -uo pipefail
state="$HOME/.cache/genealogy-workbench/parked.tsv"
[ "${1:-}" = "--list" ] && { column -t -s$'\t' "$state" 2>/dev/null || echo "nic zaparkováno"; exit 0; }
n=${1:?jméno}; msg=${2:-"manager: session obnovena (resume). Pokračuj tam, kde jsi skončil(a); pravidla beze změny."}
line=$(grep "^$n	" "$state" | tail -1) || { echo "✗ $n není zaparkovaná"; exit 1; }
IFS=$'\t' read -r _ sid label cwd _ <<<"$line"
herdr agent get "$n" >/dev/null 2>&1 && { echo "$n už běží"; exit 0; }
tab=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$cwd" --label "$label" --no-focus)
pane=$(printf '%s' "$tab" | jq -r '.result.root_pane.pane_id')
herdr agent start "$n" --kind claude --pane "$pane" --timeout 60000 -- --resume "$sid" --name "$n" >/dev/null 2>&1 \
  || herdr agent wait "$n" --until idle --timeout 600000 >/dev/null
herdr agent prompt "$n" "$msg" >/dev/null && echo "▶ $n obnovena ($sid)"
grep -v "^$n	" "$state" > "$state.tmp"; mv "$state.tmp" "$state"
