# Zadání: místopisná rešerše Chlumecka

Cíl: podrobný místopis **Chlumecka** (Chlumec nad Cidlinou a okolí) pro matriční výzkum — obecný podklad
bez osobních dat, stejně jako [`../zizelice/README.md`](../zizelice/README.md) (vzor struktury a míry
podrobnosti).

## Rozsah

- **Území:** historický **soudní okres Chlumec nad Cidlinou** (po 1850; politický okres Nový Bydžov) —
  všechny obce a osady. Doplň i navazující obce, které se v pramenech stromu objevují: Luková, Lučice,
  Mlékosrby, Nové Město, Kladruby, Komárov, Újezd, Lhotka, Uhlířská Lhota, Kratonohy, Nepolisy,
  Kosičky, Kosice, Písek, Pamětník, Lovčice, Olešnice, Kněžičky, Žehuň, Ohaře, Převýšov, Vlkov
  (ověř, které do Chlumecka skutečně patří; ostatní uveď v samostatné sekci „okolí“).
- **Pro každou obec/osadu:** dnešní příslušnost (obec, okres, kraj), historické a německé názvy,
  **ř. k. farnost a její změny v čase** (zřízení far/lokálií, přefaření), evangelický sbor, čsl. obec,
  panství (Chlumec – Kinští aj.), správní vývoj 1850–1960.
- **Uložení matrik:** pro každou farnost seznam svazků N/O/Z/indexů s roky, archiv (SOA Zámrsk / ARON
  vs. SOA Praha / eBadatelna — Chlumecko leží na hranici), signatury a ID svazků, počet snímků,
  dochování (požáry, ztráty, duplikáty/druhopisy).
- **Další prameny na místě:** sčítací operáty (ARON má sčítání po obcích), pozemkové knihy, katastry,
  kroniky, soupis poddaných 1651 / berní rula 1654 pro panství Chlumec, archiv velkostatku Chlumec.
- **Otevřené otázky** a co ověřit.

## Nástroje a pravidla

- MCP `czech-archives` (modul `aron_zamrsk`) — hledání svazků v ARONu podle obce a roku.
  eBadatelna SOA Praha zatím modul nemá: prohledávej ji šetrně (ručně, pár dotazů) nebo požádej
  uživatele o výpis katalogu.
- Šetrnost: rychlostí člověka, žádné hromadné stahování (`CLAUDE.md`, `docs/archivy/README.md`).
- Jistota u každého tvrzení: **doloženo** (katalog archivu / citovaný pramen) · **pravděpodobně** ·
  **neověřeno** — a zdroj (URL).
- Žádná osobní data ze stromu (jména předků) — jen místa.

## Výstupy (do `docs/mistopis/chlumecko/`)

- `README.md` — shrnutí pro badatele + tabulka obcí → farnost → archiv; odkazy na podsoubory.
- `farnosti/<farnost>.md` — podrobně po farnostech (svazky, ID, dochování, osady).
- `obce.md` — tabulka všech obcí a osad (dnes / historické názvy / fara / panství / správní vývoj).
- `ostatni-prameny.md` — sčítání, pozemkové knihy, panství, kroniky.
- strojově: `mcp/czech-archives/gazetteer/chlumecko.yml` (farnost → obce → svazky s ID), formát jako
  `gazetteer/zizelice.yml`.
- aktualizuj řádek Chlumecka v `docs/mistopis/README.md`.

Necommituj — až budeš hotový, napiš managerovi: `herdr agent prompt manager "mistopis-chlumecko: hotovo — <shrnutí>"`.
Když potřebuješ rozhodnutí nebo výpis z eBadatelny, zeptej se uživatele.
