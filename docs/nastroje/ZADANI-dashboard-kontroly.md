# Zadání: dashboard — fronta kontrol a doložení údajů

Navazuje na `ZADANI-dashboard.md`. Pravidla: `docs/metodika/autonomie.md` (kap. 3, 5, 6).

1. **Fronta kontrol** (nová záložka, a počet v horní liště): čte `T/research/kontroly/*.yml` živě.
   Řazení blokující → priorita → nejstarší; filtr podle osoby, typu, stavu. Položka: otázka, kontext,
   varianty vedle sebe s oporou, doporučení, **výřez snímku** (+ odkaz na celý snímek a URL portálu),
   související soubory.
2. **Rozhodnutí z dashboardu:** volba varianty nebo vlastní text + poznámka → zápis do **téhož souboru**:
   `stav: rozhodnuto`, `rozhodnuti: {volba, poznamka, kdo: uzivatel, kdy}`. Je to **jediný zápis**, který
   dashboard smí dělat. Jen do `research/kontroly/*.yml`, jen tato pole, zbytek souboru zachovat (ruamel nebo
   textová úprava, ne přepsání přes yaml.dump). Po zápisu, pokud běží session té osoby (herdr), jí pošli
   `herdr agent prompt <id> "kontrola <id>: rozhodnuto — <volba>"`. Jinak to vyzvedne manager.
   Zápis jen z 127.0.0.1, s ochranou proti CSRF (token v stránce).
3. **Odznak u osoby ve stromu:** počet otevřených kontrol, červeně blokující.
4. **Doložení údajů:** u každé události osoby (z `add_event` v aplikovaných patchích a `add_citation`) počet
   **nezávislých** pramenů ①②③ = počet různých zápisů v citacích (sidecar + `pair` = jeden zápis; rejstřík
   se nepočítá) a nejvyšší jistota. V panelu osoby tabulka událostí s tímto počtem. Filtr ve stromu
   „údaje jen s 1 pramenem“.
5. README doplnit. Necommituj, ohlas managerovi.
