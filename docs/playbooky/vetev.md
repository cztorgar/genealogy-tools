# Playbook: větev (autonomní linie)

**Kdy:** uživatel výslovně řekne „autonomně“ a zadá kořen linie (např. „otcovská linie od K0008“).
**Pravidla:** [`docs/metodika/autonomie.md`](../metodika/autonomie.md) (čtení R, totožnost I, jistota D,
brzdy). Sekce „Session větve“ ve [`workflow-sessions.md`](../metodika/workflow-sessions.md).

## Princip

Jedna rodová linie **do hloubky**: otec → jeho otec… U každé generace i manželka a sourozenci z týchž matrik.
Generace jedné linie sdílejí farnost, svazky, rejstříky a čísla domů, takže práce je levná. Do šířky (jiné
příjmení, jiná farnost) se nestaví. Na to je další větev.

## Kroky

1. Úvodní karta kořene **bez čekání** na uživatele. Pak postup jako ve [`vyzkum-osoby.md`](vyzkum-osoby.md)
   pro každou osobu linie.
2. **Patch po každé osobě** (ne až na konci). V autonomním režimu `status: schváleno` (hromadný souhlas)
   a jen fakta s jistotou ≥ 2. Sporné věci jdou do kontrol, ne do patche.
3. Nové osoby linie (rodiče z pramene) si vyžádej od managera dávkovým REQ skriptem
   (`patches/REQ-<větev>-<n>.sh`, viz [`manager.md`](manager.md)).
4. **Blokující kontrola** (totožnost, klíčové čtení): zapiš ji a **tu větev dál nestav**. Pokračuj jinými body.
5. U každé osoby při odchodu srovnej stav: `dokončeno`, nebo `pozastaveno` + důvod.
6. **Konec** (hranice pramenů, jiný archiv bez přístupu, rozpočet, plný kontext): závora v dossieru poslední
   osoby ([`zavory-a-zadosti.md`](zavory-a-zadosti.md)) a sekce `## Předání` (co dál, kde). Ohlas to managerovi.

## Nesmíš

Rozhodovat totožnost sám bez I1 (≥ 2 nezávislé údaje); číst snímky podagenty; pokračovat přes blokující
kontrolu; jít do šířky; obcházet ochrany portálů. Na portálech s CAPTCHA se zastav a předej řízení uživateli.

## Hotovo, když

Linie končí rodiči ve stromu, nebo závorou s obtížností. Všechny patche jsou předané a stavy osob odpovídají.
