# Review — kontrolní session nad stromem a workbenchem

*Živý dokument: manager ho doplňuje průběžně o věci, které se při práci ukázaly jako riziko. Review session
spouští **uživatel ručně** (žádný automat), typicky na konci většího bloku práce. Poslední doplnění: 2026-10-17.*

## Smysl

Autonomní větve, manager i nástroje dělají chyby a rozhodnutí, které nikdo zpětně neviděl celé. Review projde
**všechna data a rozhodnutí** (strom i workbench), ověří je proti pramenům a pravidlům a vrátí **seznam nálezů** —
nic sama neopravuje ve stromu bez patche a nic neschvaluje.

## Vstupy

- Strom `../genealogy-trees/<strom>/`: `research/people/` (dossiery, Kontext, Závora, Předání), `patches/` (changes + applied),
  `research/kontroly/`, `sources/` (sidecary, přepisy, `.compare.md`), `research/pribehy/`, `research/hints/`, `research/log.md`,
  `research/todo-*.md`, `research/korespondence.md`, `research/mista.md`, **`research/rozhodnuti-managera.md`** (deník zásahů),
  git log stromu.
- Gramps Web (API přes `tools/gramps/gw.py`, jen čtení).
- Workbench: `docs/metodika/*`, `tools/*`, `skills/*`, git log workbenche (změny nástrojů → kterých dat se týkají).

## Jak postupovat

1. **Rozsah:** od posledního review (datum v `research/review/`) nebo celý strom. Rozdělit po větvích (`research/vetve.yml`).
2. Pro každou oblast níže projít data, **otevřít pramen (výřez/snímek) tam, kde jde o klíčový údaj**, a zapsat nález.
3. Výstup: `research/review/YYYY-MM-DD.md` — nálezy seřazené podle závažnosti (**chyba ve stromu** › **nepodložené**
   › **nekonzistence** › **kosmetika**), u každého: osoba/patch/citace, co je špatně, důkaz, návrh opravy (patch / kontrola /
   úprava nástroje). Opravy dělá až manager po schválení uživatelem.
4. Statistika na konec: kolik osob, patchů, citací podle jistoty, kontrol, závor; kolik nálezů v které kategorii.

## Kontrolní seznam

### A. Totožnost a vazby (nejvyšší riziko)
- Každá vazba rodič → dítě a manželství: má citaci? Splňuje **I1** (≥ 2 nezávislé údaje kromě jména)? Zvlášť vazby, které
  rozhodl **manager podle I0** bez uživatele (deník rozhodnutí) a **zhroucení předků** (stejný pár ve dvou liniích).
- Past **I5**: otec × syn stejného jména ve stejném domě, vdova × druhá manželka, macecha. (Viz dva Jakubové Kučerové,
  Jan Kubelka st. × jeho otec, Václav × Jan Kubelka 1826.)
- **Jmenovci obcí**: Komárov u Přelouče × Komárov u Nechanic, Písek, Lhotka… — místo musí sedět s farností a okresem.
- Rodiny s jedním rodičem (`F-…-X`) — není druhý rodič mezitím doložen? Nevznikla duplicitní rodina?
- Osoba nesmí mít dvě rodičovské rodiny ani rodiče ze dvou generací (chyba managera 2026-10-17: Magdalena Kubelková
  dočasně připojena k matce Jana st. místo k jeho ženě).
- Pohlaví podle pozice v ID (P1 = muž, P2 = žena, sudé/liché Kekule) — MyHeritage se pletl (Voderka).

### B. Čtení a jistota
- Citace s jistotou ≥ 3 musí mít buď ověření uživatelem, nebo shodu dvou čtení + další pramen (kap. 3 autonomie).
- **Shody `compare.py` před opravou `d9f5c97` (2026-10-17)** — porovnání dřív hlásilo shodu i při rozdílných číslech
  a příjmeních. Všechna R2 přijetí z autonomních běhů před touto opravou přepočítat.
- Rozhodčí `gpt-5.5` občas halucinuje celý jiný text — čtení, která rozhodl jen on, ověřit.
- Hinty pro OpenAI nesměly obsahovat čtené jméno (R8) — zkontrolovat starší `.openai.json` (pole `hint`).
- „Jen Claude“ čtení z doby bez kreditu (G-reader-backlog) — všechna dočtena? Jistota odpovídá?

### C. Události a data
- Duplicitní události téhož typu u osoby (dvě narození — odhad z věku + přesné datum; Šanda E0243).
- Odhady (`ABT`/`EST`/`BET`) mají popis, z čeho plynou; věk při úmrtí bývá nadsazený (Jan Jukl 78 → 1740–1750).
- Datum v Gramps odpovídá patchi (formát, modifikátory); pořadí událostí chronologické (`sort_events.py`).
- Rozpory mezi prameny jsou zapsané (obě verze), ne mlčky vyřešené.
- Křest × narození: typ `Christening`, nikdy `Baptism` (lokalizační past).

### D. Prameny a citace
- Jeden Gramps Source na doklad; žádné prázdné / rozbité názvy zdrojů (chyba applieru 2026-10-16); ID zdrojů bez mezer.
- Rozdělené zdroje téhož dokladu (sčítací arch 1921 Kladruby 40 = 3 zdroje — backlog).
- Citace sdílené víc osobami (např. Z 1742 C0328 Dorota + Jakub) — text `page` sedí pro obě.
- Sidecar má URL snímku i svazku (pravidlo uživatele), signaturu, snímek; `original` u fotek.
- Kopie z rodinných materiálů (rodokmen Ornstů 2020) = nápověda, dokud není ověřeno v originále.

### E. Soubory patchů a stav
- Každý `aplikováno` patch má platný YAML a `applied:` odpovídá `changes:` (bug applieru `add_note` zkracoval soubory —
  P-K0014-07, P-…-P1-P1-P1-P1-P1-01).
- Aplikovaný patch se nemá upravovat; zapracování = nový patch. Hledat aplikované patche měněné po aplikaci (git log).
- Navazující patche s `citation_gramps_id` doplněným ručně — správná citace?
- Patche se `status: schváleno`, které nastavila session sama (nemá) — kdo schválil?
- Stav dossierů (`zapsáno` jen po `dokončeno`), příznak `kontext: chybí`.

### E2. Patche schválené managerem
- Od 2026-10-17 patche schvaluje manager sám po dávkách — review je **jediná věcná kontrola**: projít všechny patche aplikované od té doby
  (git log stromu, commity „Dávka … aplikována“) se stejnou důkladností jako schválení.

### F. Ruční zásahy do Gramps (mimo patche)
- Projít `research/rozhodnuti-managera.md`: přejmenování (NN → příjmení), alternativní jména, smazané rodiny/události/citace,
  přesuny dossierů (Voderka), ručně změněné pohlaví. Každý zásah má mít důvod a pramen.

### G. Příběhy, Kontext, Závory
- Příběh bez fikce; každé tvrzení s oporou; odvozené věci označené („patrně“); jistota 0 jen v „Co nevíme“.
- Žijící osoby jen interně.
- Závora: typ odpovídá (nedigitalizováno × nenalezeno × prohledáno jen rejstříkem); „co by ji prolomilo“ konkrétní.

### G2. Příběhy proti datům (kontrola napříč soubory)
- **Úplnost:** příběh osoby zmiňuje všechny doložené manžele a děti z Gramps (rodiny osoby) — chybějící dítě/manžel = nález
  (případ 2026-10-17: K0120 Josef Doležal — v příběhu chyběli synové Jan a Václav).
- **Zastaralé „Co nevíme“:** otázka, kterou mezitím rozhodla kontrola (`research/kontroly/*` stav zapracováno) nebo nový patch,
  v příběhu nesmí zůstat jako otevřená (K0121: „Anna, nebo Magdalena?“ po rozhodnutí K0121-01).
- **Role osob:** jména zmíněná v příběhu v jiné roli (porodní bába, kmotr, svědek) nesmí jít splést s rodiči — u stejného
  příjmení/jména výslovně uvést roli (K0060: porodní bába Magdalena × matka Dorota).
- **Shoda s dossierem:** jména a data v příběhu = hodnoty v Gramps (po přejmenování NN → příjmení, opravách dat).
- Review session běží na **Opusu** (Sonnet čte data hůř — `docs/nastroje/reader.md`); pro tuhle kapitolu nejdřív vygenerovat
  seznam rodin/dětí z Gramps a kontrol podle osoby, pak číst příběhy.

### H. Workbench
- Metodika ↔ skilly ↔ nástroje si neodporují (autonomie R/I/D, pribehy, workflow, review).
- Změny nástrojů v git logu: které ovlivnily už zapsaná data a jsou ošetřené (seznam „známé chyby a jejich dopad“ níže).
- Žádná osobní data ve workbenchi (docs, příklady, gazetteer jen obecně).

## Známé chyby a jejich dopad (doplňuje manager)

| Datum | Chyba | Dopad | Ošetřeno |
|---|---|---|---|
| 2026-10-16 | applier: prázdné názvy zdrojů u fotek matrik | S-IMG_3961–3963 | opraveno ručně |
| 2026-10-16 | `find_registers` vždy `digitized: false` | místopis Chlumecka tvrdil „bez skenů“ | opraveno |
| 2026-10-17 | applier `add_note` přepisoval soubor patche | 2 patche bez `changes` | obnoveno |
| 2026-10-17 | `compare.py` falešné shody (čísla, příjmení, podmnožina tokenů) | R2 přijetí před `d9f5c97` | přepočteno jen u Midlochů/Boudyšů — **zbytek ověřit** |
| 2026-10-17 | manager: Magdalena Kubelková připojena k rodině s matkou Jana st. | 1 rodina + citace | smazáno, opraveno (-03) |
| 2026-10-17 | MyHeritage: Jiří Voderka na pozici matky, pohlaví F | dossier, Gramps | přesunuto, opraveno |
| 2026-10-17 | applier: ID zdroje s mezerou (rodokmen Ornstů) | 9 patchů spadlo | opraveno, aplikováno |
| 2026-10-17 | duplicitní narození Jiřího Šandy (E0243) | 1 událost | smazáno |
| 2026-10-17 | gpt-5.5 rozhodčí halucinuje na kurentu | čtení rozhodnutá jen jím | ověřit |
| 2026-10-18 | souběh: session upravila patch během aplikace (P-K0116-01 `c6`) | text patche ≠ `applied` | ověřeno v Gramps; review: porovnat `changes` × Gramps u patchů měněných v commitu aplikace |
