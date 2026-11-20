#!/usr/bin/env bash
# Záloha velkých souborů stromu (snímky, PDF, fotky) — přesně těch, které git ignoruje — přes rclone.
# Inkrementálně: rclone copy přenese jen nové a změněné soubory (velikost + čas), na cíli nikdy nic nemaže.
# Cíl: `zaloha.cil` v genealogy.toml (rclone remote, např. "onedrive:rodokmen/zaloha/hesoun").
#
#   tools/zaloha/snimky.sh            # záloha
#   tools/zaloha/snimky.sh --dry-run  # jen ukáže, co by se přeneslo
set -euo pipefail
cd "$(dirname "$0")/../.."
strom=$(python3 tools/wbconfig.py get strom.adresar)
cil=$(python3 tools/wbconfig.py get zaloha.cil)
[ -n "$cil" ] || { echo "chybí zaloha.cil v genealogy.toml (např. \"onedrive:rodokmen/zaloha/<strom>\")" >&2; exit 1; }
seznam=$(mktemp); trap 'rm -f "$seznam"' EXIT
# soubory mimo git (snímky, PDF…), bez nastavení editorů
git -C "$strom" -c core.quotePath=false ls-files --others --ignored --exclude-standard \
  | grep -v -E '^(\.idea|\.obsidian)/' > "$seznam" || true
echo "strom: $strom → $cil ($(wc -l < "$seznam") souborů mimo git)"
rclone copy "$strom" "$cil" --files-from-raw "$seznam" --transfers 4 --stats 30s --stats-one-line -v "$@" 2>&1 \
  | grep -E "Transferred|Copied \(new\)|Copied \(replaced|ERROR|NOTICE" || true
echo "hotovo $(date '+%Y-%m-%d %H:%M')"
