# Matricula Online (ICARUS) — data.matricula-online.eu

Stav k 18. 10. 2026 (session predci-k0005). Modul **`matricula` v0.1 — jen metadata** (svazky farnosti,
počet a jména snímků, citace, odkaz do prohlížeče). **Snímky nestahuje** — viz Technika.

## Obsah

Matriky diecézí a evangelických církví Rakouska, Německa, Polska, Srbska aj. (žádné české fondy). Rakousko:
arcidiecéze Vídeň (`oesterreich/wien`, ~570 farností včetně vídeňských `16-altottakring`, `16-neuottakring`),
St. Pölten (`oesterreich/st-poelten`), Linec (`oberoesterreich`), Salcburk, Štýrský Hradec (`graz-seckau`),
Gurk, Tyroly, Vorarlbersko, Burgenland, evangelické diecéze A. V. a H. V. Knihy bývají uložené na faře
(„Lagerungsort: Pfarre“) — originál = farní úřad, ne diecézní archiv.

Příklad: **Hennersdorf** (u Vídně, okr. Mödling; k farnosti patří i **Leopoldsdorf**): Taufbuch 01-02 až 01-17
(1782–1938), Trauungsbuch 02-02 až 02-08 (1771–1938), Sterbebuch 03-02 až 03-07 (1784–1938), indexy uvnitř
svazků. Taufbuch 01-12 (1912–1921) má 230 snímků; `?pg=30` = snímek `03-Taufe_0026`.

## Podmínky užití (https://www.icar-us.eu/cooperation/online-portals/matricula/nutzungsbedingungen/)

- Data (snímky i metadata) **jen k soukromým nebo vědeckým účelům**, v souladu se zákony o osobním stavu a o
  ochraně údajů dotčeného státu.
- Podmínky se přijímají tlačítkem „Weiter zu Matricula“ na úvodní stránce — tedy uživatel.

## Technika (ověřeno)

- HTML bez API, bez přihlášení. `robots.txt` (`cdn-static.matricula-online.eu/static/robots.txt`):
  pro všechny **`Disallow: /*?pg=`, `/*/suchen`, `/*/landkarte-features`, `/*/accounts`**; GPTBot, ClaudeBot
  a další AI crawlery `Disallow: /`. Modul volá jen povolené stránky: země `/de/<země>/`, diecéze
  `/de/<země>/<diecéze>/` (všechny farnosti na jedné stránce), farnost `/de/…/<farnost>/` (tabulka svazků +
  detaily: Matrikeltyp, rozsah, Inhalt, Lagerungsort), svazek `/de/…/<farnost>/<signatura>/` (JS
  `MatriculaDocView` s poli `labels` a `files`).
- Snímek = `https://img.data.matricula-online.eu/image/<base64 cesty>/`. Mimo prohlížeč na stránce `?pg=`
  vrací **403** (i bez vlastního UA; hlavička `Vary: Origin` → kontrola Origin/Referer). Podvrhnout ji =
  obcházení ochrany → **nedělat.** Ovládat kvůli tomu prohlížeč uživatele (Claude in Chrome) na `?pg=` taky ne
  (robots.txt zakazuje automatům právě tyto stránky).
- Hledání podle jména obce: modul prochází seznam farností `DEFAULT_DIOCESES` (Vídeň, St. Pölten), jinak zadat
  cestu farnosti přímo (`oesterreich/wien/hennersdorf`). Vyhledávání portálu (`/suchen`) se nepoužívá.
- Rate limit 3 s, HTML v cache 7–30 dní.

## Jak s tím pracovat

1. `find_registers(module="matricula", place="Hennersdorf" | "oesterreich/wien/hennersdorf", year_from, year_to, kind)`.
2. `register_info` → počet snímků a jména (`03-Taufe_0026`); `page_url` → odkaz `…/?pg=<snímek>`.
3. Session zapíše odkaz do `## Doklady k dohledání` dossieru (`kde: online Matricula (uživatel)`); uživatel snímek
   otevře, uloží (soukromé studium) do `doklady/` a session ho zpracuje jako doklad.
4. Druhé čtení přes OpenAI = předání třetí straně → jen po rozhodnutí uživatele.

Použije i predci-k0007 (Vídeň-Ottakring: `oesterreich/wien/16-altottakring`, `16-neuottakring`).
