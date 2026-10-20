# Playbook: založení stromu

**Kdy:** uživatel začíná nový rodokmen. **Role:** manager. Lidský popis: [`docs/prirucka.md`](../prirucka.md)
§ 3–4.

## Kroky

1. **Předpoklady:** Gramps Web běží (`infra/gramps-web`, `docker compose up -d`). V `.env` jsou účty
   (`GRAMPSWEB_ADMIN_*`). Založení stromu a uživatele v Gramps Web dělá uživatel. Ty mu jen připravíš příkazy
   (`python3 -m gramps_webapi tree …`, `user add …`) a do přihlašování nezasahuješ.
2. **Šablona:** `uv run tools/init_tree.py ../genealogy-trees/<nazev> --nazev <nazev> --k0001 "<jméno (*rok)>"`.
3. **Konfigurace:** uživatel vyplní `genealogy.toml` (`strom.adresar`, `strom.gramps_strom`, `badatel.jmeno`).
   Ověř: `python3 tools/wbconfig.py get strom.adresar`.
4. **Osoby:**
   - z GEDCOM / MyHeritage: `uv run tools/research/build_queue.py <export.ged> <xref výchozí osoby> <strom>/research/people`
     (+ `--family-of`, `--parents-of` pro vedlejší linie). Údaje exportu jsou nápovědy s jistotou 0.
     Export ulož do `data/exports/`. Do Gramps se importuje jen jako referenční strom, nikdy do masteru.
   - od nuly: `uv run tools/research/add_person.py <strom> K0001 --name … --sex … --puvod ústně --rel "výchozí osoba"`,
     rodiče a prarodiče, které uživatel zná, stejně. Vazby: `uv run tools/gramps/ensure_family.py --father … --mother … --children …`
     (citace ústního sdělení badatele, jistota 3).
5. **Ústní sdělení** (data, která uživatel zná zpaměti) zapiš patchem se sidecarem `type: ústní sdělení`.
   Do `research/todo-rodina.md` dej, co by potvrdily doklady z domova.
6. **Kontrola:** `uv run tools/dashboard/server.py` → strom se zobrazí, fronta (`tools/research/fronta.py`)
   ukáže první osoby.
7. **Git:** první commit repa stromu. Repo má být **soukromé** (žijící osoby).

## Hotovo, když

Strom má TREE.md, K0001 a známé předky jako dossiery i osoby v Gramps, dashboard ho ukazuje a fronta má pořadí.
