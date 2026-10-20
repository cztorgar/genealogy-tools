# Playbook: hledání v archivech

**Kdy:** potřebuješ najít svazek a snímek pro osobu nebo událost.
**Detaily portálů:** [`docs/archivy/`](../archivy/). **Typy pramenů:** [`docs/prameny/`](../prameny/).

## Kroky

1. **Místo v té době:** obec → farnost (v daném roce, fary se měnily) → archiv. Pomůžou `docs/mistopis/`, MCP
   `genealogy` (`place_history`, `where_are_records`) a gazetteer v `mcp/czech-archives/gazetteer/`.
2. **Svazek:** MCP `czech-archives` → `find_registers(module, place, year_from, year_to, kind)` →
   `register_info` (rozsah, počet snímků, rejstříky). Signatury a čísla snímků **nikdy nevymýšlej**. Ber je
   z výsledku nástroje.
3. **Rejstřík napřed:** existuje-li index (abecední rejstřík svazku), najdi stránku v něm a pak jdi přímo na
   snímek. Bez rejstříku procházej po ročnících a zapisuj, co jsi prošel.
4. **Snímek** stáhni po jednom (`fetch_archivalie_page` / modul portálu) do cache a zkopíruj do `sources/<ID>/`
   se sidecarem `.yml`: archiv, fond, signatura, folio / strana, snímek, **URL snímku i svazku**, datum citace.
5. **Log:** `research/log.md`: co, kde, roky, snímky, hledané jméno a varianty, výsledek. U „nenalezeno“
   i proč na tom záleží a co zkusit příště.

## Portály s ochranou proti robotům

Třeboň, Matricula, Plzeň, Opava, Litoměřice a podobné: **jen prohlížeč ovládaný agentem, tempem člověka,
po jednotlivých snímcích**. Ulož přesnou URL pohledu.

- Žádné podvrhy hlaviček ani User-Agenta. Neobcházej detekci a neřeš CAPTCHA. **CAPTCHA nebo přihlášení:
  zastav se a předej řízení uživateli.**
- Stažení souboru jen se souhlasem uživatele. Sepiš seznam snímků a uživatel potvrdí.
- Snímky Třeboně a Matriculy neposílej do dalších AI služeb. Jistota ≤ 1, dokud je neověří uživatel.
- Prohlížeč ovládá v jednu chvíli jen jedna session.

## Nesmíš

Stahovat celé svazky, mirrorovat, překračovat limity (MZA Brno blokuje IP), měnit tempo modulů `czech-archives`.
