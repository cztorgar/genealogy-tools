# Playbook: závory a žádosti do archivů

**Kdy:** položka checklistu nebo celá linie nejde dál.
**Formát závory:** [`workflow-sessions.md`](../metodika/workflow-sessions.md) (sekce Závora).
**Obtížnost:** [`fronta.md`](../metodika/fronta.md).

## Závora

Sekce `## Závora` v dossieru poslední osoby linie:

```
## Závora
- **kde:** co přesně chybí (křest ~1783, sňatek rodičů…)
- **proč:** matriky nezachovány | nedigitalizováno | nenalezeno v prohledaném rozsahu | nečitelné |
  nejistá totožnost (kontrola …) | mimo dosah (jiný archiv, lhůta)
- **prohledáno bez výsledku:** svazky, roky, snímky
- **co by závoru prolomilo:** konkrétní další pramen + šance (vysoká / malá / prakticky žádná)
- **obtížnost:** nízká | střední | velká — proč
- **datum, kdo:** YYYY-MM-DD, session
```

| obtížnost | volíš, když |
|---|---|
| nízká | pramen je online, známý a dosažitelný za pár snímků. **Pak to není závora, prostě to udělej.** |
| střední | online jen pracně (bez rejstříku, stovky snímků, nejistá fara), nebo je potřeba dopis, matriční úřad, doklad od rodiny |
| velká | matriky se nedochovaly / před začátkem řady; zbývají nepřímé prameny (pozemkové knihy, katastry, soupisy) |

**„Nehledáno“, „rozpočet“ ani „konec dávky“ není důvod závory.** Pramen zůstane v checklistu `[ ]` s poznámkou,
kde hledat. Prolomenou závoru nemaž, připiš `prolomeno YYYY-MM-DD: …`.

## Žádost do archivu / matričního úřadu

1. Ověř, že pramen opravdu není online (`register_info`, `docs/archivy/`), a zapiš to do logu.
2. Koncept: MCP `genealogy` → `draft_archive_request`, nebo ručně. Adresát, co přesně (osoba, obec, roky,
   druh zápisu), proč (vztah žadatele: přímý potomek), kontakt doplní uživatel.
3. Ulož ho do dossieru (sekce `## Koncepty žádostí`) a odkaz připiš do `research/doklady.md` / `todo-rodina.md`.
4. **Neodesílej.** Odesílá uživatel. Do závory napiš „koncept žádosti připraven (datum)“.

## Otázka pro rodinu

Řádek na konec `research/todo-rodina.md`: otázka, ID osob, proč, kdo by mohl vědět. Doklad z domova (rodný,
oddací, úmrtní list) patří do sekce `## Doklady k dohledání` v dossieru.
