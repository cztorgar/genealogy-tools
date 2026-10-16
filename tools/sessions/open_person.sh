#!/usr/bin/env bash
# Otevře osobní session pro výzkum osoby v herdr: nový tab ve workspace managera,
# Claude Code pojmenovaný podle osoby, spuštěný skill research-person.
#
# Použití: open_person.sh <ID: 42 | K0042 | K0001-S1 | K0002-C1-C2> [strom]
# Spouští manager (běží v herdr, HERDR_ENV=1).
set -euo pipefail

[ "${HERDR_ENV:-}" = 1 ] || { echo "neběžím v herdr" >&2; exit 1; }
[ $# -ge 1 ] || { sed -n '2,6p' "$0" >&2; exit 2; }

tree=${2:-berescak}
id=$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')
if [[ "$id" =~ ^K?0*([0-9]+)(-.*)?$ ]]; then
  k=$(printf 'K%04d%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}")
else
  echo "neplatné ID: $1" >&2; exit 2
fi
name=$(printf '%s' "$k" | tr '[:upper:]' '[:lower:]')   # herdr agent name: [a-z][a-z0-9_-]*
workbench=$(cd "$(dirname "$0")/../.." && pwd)
people="$workbench/../genealogy-trees/$tree/research/people"

dossier=$(ls "$people/$k"-[a-z]*.md 2>/dev/null | head -1 || true)   # slug začíná malým písmenem, -S1/-C1 velkým
[ -n "$dossier" ] || { echo "dossier $k ve stromu $tree neexistuje" >&2; exit 1; }
# název tabu: ID + celé jméno + rok narození („K0056 František Vrbický *1848“), ať se jmenovci rozliší
label=$(python3 "$workbench/tools/sessions/tab_label.py" "$workbench/../genealogy-trees/$tree" "$k")

if herdr agent get "$name" >/dev/null 2>&1; then
  echo "session $name už běží — přepínám na ni"
  herdr agent focus "$name" >/dev/null
  exit 0
fi

# osoba, o které mluvíme, existuje i v Gramps (jen jméno + pohlaví; fakta až po ověření)
python3 "$workbench/tools/gramps/ensure_persons.py" "$workbench/../genealogy-trees/$tree" "$k" || \
  echo "varování: založení $k v Gramps selhalo" >&2

tab_json=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$workbench" \
  --label "$label" --no-focus)
pane=$(printf '%s' "$tab_json" | python3 -c 'import sys,json;print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')

if ! herdr agent start "$name" --kind claude --pane "$pane" --timeout 60000 -- --name "$name" >/dev/null 2>&1; then
  # typicky dialog důvěry ke složce / povolení MCP — potvrzuje uživatel v tabu
  echo "$name čeká na potvrzení v tabu '$label' — čekám, až bude připravená…"
  herdr agent wait "$name" --until idle --until done --timeout 600000 >/dev/null
fi
herdr agent prompt "$name" "/research-person $k $tree" >/dev/null
echo "otevřeno: $label — agent '$name', pane $pane"
