# Místa

Místo je klíč k hledání: v Česku se matrika najde přes **obec + rok → farnost → archiv → svazek**.
Proto musí být místa ve stromu jednotná a hierarchická.

## Konvence v Gramps

- **Hierarchie:** obec (případně část obce / osada) → [historicky: panství, okres] → země (Čechy /
  Morava / Slezsko) → stát. Pro hledání v matrikách je nejdůležitější vazba na **farnost**
  (ukládá se jako atribut místa, s obdobím platnosti).
- **Číslo popisné není místo.** `Luková č. 2` → místo `Luková`, č. p. jako atribut/popis události
  (adresa). Jinak vznikají duplicity (`Luková 2`, `Luková č.10`, `Luková No. 2…`).
- **Historické názvy a exonyma** jako alternativní jména místa s obdobím
  (Chlumec nad Cidlinou / Chlumetz an der Zidlina; Bydžov → Nový Bydžov).
- Obec, která zanikla nebo se sloučila, zůstává samostatným místem s poznámkou.
- Souřadnice z RÚIAN / Wikidata, ID Wikidata jako atribut (umožní `place_history`).

## Zdroje pro místopis

- Historický lexikon obcí ČR 1869–2015 (ČSÚ, PDF/XLS) — příslušnost obcí, počty domů a obyvatel.
- Inventáře matrik jednotlivých archivů (PDF) — které matriky pokrývají kterou obec.
- Schematismy diecézí (Kramerius) — příslušnost obcí k farnostem v daném roce.
- Zeměpisný rejstřík SOA Třeboň, česko-německý rejstřík obcí SOA Litoměřice.
- Wikidata / RÚIAN — souřadnice a stabilní ID.

Z toho se postupně skládá **gazetteer** v `mcp/czech-archives/gazetteer/` (obec → farnost → archiv →
svazky), který je jádrem hledání.
