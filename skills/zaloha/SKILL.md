---
name: zaloha
description: Záloha výzkumu — texty stromu (hinty, patche, sidecary, dossiery, kontroly) commit + push do jeho git remote, snímky a PDF (soubory, které git ignoruje) přírůstkově přes rclone na OneDrive. Použij, když uživatel napíše „zálohuj“, „udělej zálohu“, „pushni výzkum“, „/zaloha“, nebo na konci dávky práce, když o to požádá.
---

# Záloha výzkumu

Strom: `python3 tools/wbconfig.py get strom.adresar` (dál `<strom>`). Komunikuj česky, výsledek krátce.
Dvě části, obě vždy:

| Co | Kam | Jak |
|---|---|---|
| texty stromu (vše, co git sleduje) | git remote stromu (`git -C <strom> remote -v`) | commit + push |
| snímky, PDF, fotky (vše, co git ignoruje) | `zaloha.cil` z `genealogy.toml` (rclone) | `tools/zaloha/snimky.sh` |

## 1. Texty stromu — commit a push

```sh
git -C <strom> status --short
```

- Nic ke commitu → jen `git -C <strom> push` (kdyby lokální commity ještě nebyly venku).
- Jsou změny → **podívej se, co to je** (`git -C <strom> status --short`, u neznámých souborů `git diff --stat`)
  a commitni je **jedním commitem** se zprávou podle obsahu (např. „Soukupovi: křty 1831–1841, sňatek 1829; listiny Spole“).
  Pravidla commit zprávy z uživatelova CLAUDE.md platí (krátce, co a proč, bez narace).
- Před commitem zkontroluj, že se nepřidává nic, co do gitu nepatří: hesla, `.env`, token cache, `.idea/`,
  velké binárky (ty má vylučovat `.gitignore` stromu — když se objeví v `git status`, zastav se a zeptej se).
- Pak `git -C <strom> push`. Remote musí být **soukromý** repozitář (strom obsahuje žijící osoby a snímky archivů,
  které se nesmí šířit). Když remote chybí nebo push selže, napiš to a nic nezkoušej obcházet.

Workbench (`genealogy-tools`) tímto skillem **necommituj** — commituje ho uživatel (nebo na jeho výslovný pokyn).
Jen na konci zmiň, jestli tam jsou necommitnuté změny (`git status --short`, bez `.idea/`).

## 2. Snímky a PDF — rclone na OneDrive

```sh
tools/zaloha/snimky.sh            # přenese jen nové a změněné soubory, na cíli nic nemaže
tools/zaloha/snimky.sh --dry-run  # jen ukáže, co by se přeneslo
```

- Spouštěj z kořene workbenche. Při větším objemu (stovky MB) spusť na pozadí a počkej na dokončení.
- Po doběhnutí ověř počet a velikost na cíli: `rclone size "$(python3 tools/wbconfig.py get zaloha.cil)"`
  a porovnej s počtem souborů, který skript vypsal na začátku.
- `ERROR` v logu → vypiš konkrétní soubory, neopakuj naslepo.
- Chybí `zaloha.cil` → zeptej se uživatele na cíl a zapiš ho do `genealogy.toml` (sekce `[zaloha]`, vzor v `genealogy.example.toml`).

## 3. Odpověď

Dvě až tři věty: commit (hash, co obsahoval) a push kam; kolik souborů a MiB přeneslo rclone a kolik je na cíli celkem;
případné chyby nebo necommitnuté změny ve workbenchi.
