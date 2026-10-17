# Autonomní výzkum — pravidla a fronta kontrol

Cíl: session prochází strom **sama**. Uživatel nekontroluje průběžně každé čtení. Dostává jen
**frontu kontrol**, tedy věci, které stroj spolehlivě nerozhodne, a nejdřív ty, které blokují další postup.
Každý údaj nese, **z kolika nezávislých pramenů** je doložený.

Navazuje na [`dukazni-standard.md`](dukazni-standard.md), [`prepis.md`](prepis.md) a
[`workflow-sessions.md`](workflow-sessions.md). Kde se pravidla liší, platí pro autonomní session tento dokument.

---

## 1. Čtení zápisu (pravidla R)

| # | Pravidlo |
|---|---|
| R1 | Každý použitý zápis se čte **dvakrát nezávisle** ze stejného výřezu: Claude a OpenAI (`read-record`, `compare.py`). Claude nesmí nahlížet do čtení OpenAI, dokud nemá vlastní. |
| R2 | **Shoda** v poli → pole se přijme. Jistota se řídí pramenem (kap. 3). |
| R3 | **Neshoda** u klíčového pole (jméno, příjmení, datum, č. p., věk, rodiče, manžel/ka) → **rozhodčí čtení**: OpenAI s vyšším effortem / silnějším modelem (`--model gpt-5.5 --effort medium`) jen na sporné pole, ideálně z užšího výřezu. **Když rozhodčí čtení zjevně čte jiný text** (nesedí ani jasně čitelná slova, jiná jména, jiné č. p. — gpt-5.5 to na kurentu dělá), zopakovat ho s `--model gpt-6.1-sol --effort medium` (případně `high`) a halucinované čtení nepočítat (rozhodl uživatel, kontrola K0451-03). |
| R4 | Rozhodčí čtení se shoduje s jedním z prvních dvou → přijmout tu verzi, jistota **o stupeň níž**. Do `context` patří všechna tři čtení. |
| R5 | Spor se dá rozhodnout **kontextem jiného pramene** (stejné jméno rodiče v jiném zápisu, rejstřík, souvislá řada č. p., věk z jiného zápisu) → session rozhodne, napíše **proč** a jistotu sníží o stupeň. |
| R6 | Ani R4, ani R5 nepomohly → **kontrola `cteni`** do fronty (kap. 5). Do patche jdou všechny varianty s jistotou 1, nebo se pole vynechá, když na něm nic nestojí. |
| R7 | Pole, která nejsou klíčová (kmotři, porodní bába, příčina smrti, svědci), se při neshodě **neeskalují**. Zapíšou se obě čtení s `[?]`. |
| R8 | Shoda dvou modelů není důkaz. U jmen platí R2 jen tehdy, když jméno **nepřišlo z nápovědy** (hint nesmí obsahovat čtené jméno — jen obec, rok, č. p., co hledat). |

## 2. Totožnost (pravidla I) — největší riziko

| # | Pravidlo |
|---|---|
| I1 | Zápis se přiřadí osobě, jen když kromě jména sedí **aspoň dva nezávislé údaje**: č. p., rodiče, manžel/ka, věk ±2 roky (u starších zápisů ±5), povolání, obec, kmotři z rodiny. |
| I2 | Sedí jen jeden údaj → **kandidát**. Do patche jde nanejvýš jako nápověda nebo s jistotou 1 a do fronty jde **kontrola `totoznost`, blokující**. Na kandidátovi se nestaví další generace. |
| I3 | Víc kandidátů (jmenovci ve stejné obci a období) → **vždy kontrola `totoznost`**, s tabulkou kandidátů a toho, co u kterého sedí. |
| I4 | Rodiče osoby se zakládají (`add_person`, `ensure_family`) jen z doloženého zápisu (I1). U kandidátů se rodina nezakládá. |
| I5 | Typická past: otec a syn stejného jména ve stejném domě, vdova po druhém sňatku, macecha. Když to nelze vyloučit, jde o kandidáta (I2). |

## 3. Jistota a doložení (pravidla D)

**Nezávislý pramen** = jiný zápis vzniklý jindy nebo jiným pisatelem: křest, sňatek, úmrtí, sčítání,
doklad z jiné instituce. Dvě fotky téhož zápisu, rejstřík vůči hlavnímu zápisu ani matriční výpis
vůči originálu **nejsou** nezávislé (rejstřík se počítá jako podpůrný, ne jako další pramen).

| Jistota citace | Kdy |
|---|---|
| 4 | primární zápis, čtení ověřil uživatel |
| 3 | primární zápis, R2 shoda, **a** údaj potvrzuje aspoň jeden další nezávislý pramen (D2 ≥ 2) |
| 2 | primární zápis, R2 shoda, jediný pramen; nebo údaj odvozený (věk → rok narození) |
| 1 | R4/R5 (rozhodnuto rozhodčím čtením nebo kontextem), sporné čtení, kandidát totožnosti |
| 0 | nápověda (MyHeritage, cizí strom) |

- **D1** — Každá událost v patchi uvádí v `citations` **všechny** zápisy, které tentýž údaj uvádějí (narození: křest, sňatek s věkem, úmrtí s věkem, sčítání). Neodkládat to „na později“.
- **D2** — Počet nezávislých pramenů údaje = počet různých zápisů v `citations` (dvojice fotek téhož zápisu = jeden). Dashboard ho ukazuje jako ①②③ u každé události. Údaj s ① se má potvrdit, když to jde levně.
- **D3** — Zápisy se v údaji **rozcházejí** (jiný den narození, jiné jméno matky): zapsat obě verze (dvě události nebo `context`) a do fronty dát **kontrolu `rozpor`**. Blokující je jen tehdy, když na údaji stojí totožnost (I).
- **D4** — Autonomní citace nese v `notes` text **„autonomní čtení Claude+OpenAI, neověřeno uživatelem“**. Po potvrzení kontroly se jistota zvedne přes `update_citation`.

## 4. Postup autonomní session

1. Intro karta jako obvykle (bez čekání na uživatele), pak checklist podle období.
2. Pro každý pramen: najít → výřez → R1–R7 → přiřazení podle I1–I5 → zápis do přepisu, sidecaru a logu.
3. Narazí-li na **blokující kontrolu**: zapíše ji, **tu větev dál nestaví** a pokračuje v jiných bodech checklistu.
4. Na konci jeden souhrnný patch (`status: schváleno`, hromadný souhlas uživatele s autonomním režimem)
   s tím, co je jisté (jistota ≥ 2). Sporné věci jsou ve frontě, ne v patchi jako fakta.
5. Stav dossieru `dokončeno`. Jsou-li otevřené **blokující** kontroly, stav je `pozastaveno` a důvod se zapíše
   do `## Odloženo`.
6. Zpráva managerovi: co je zapsáno, kolik kontrol (z toho blokujících), co nenalezeno.

**Kdy se session zastaví úplně:** hranice pramenů (např. Žiželice před 10/1798), žijící osoby (jen ústní
sdělení uživatele), anti-bot ochrana portálu, rozpočet čtení vyčerpán (viz kap. 7).

## 5. Fronta kontrol

Jedna kontrola = jeden soubor **`research/kontroly/<ID>-<nn>.yml`** ve stromu (osoba), obecné věci
`research/kontroly/G-<nn>.yml`. Soubor zakládá session (každá jen své, číslování navazuje). Dashboard je ukazuje
jako frontu a uživatel v něm rozhoduje. Rozhodnutí se zapíše do téhož souboru.

```yaml
id: K0448-01
osoba: K0448                       # nebo null u obecné (G-)
typ: cteni                         # cteni | totoznost | rozpor | nastroj | jine
blokuje: true                      # true = na tom stojí další postup (I2/I3, D3 s dopadem na totožnost)
priorita: 2                        # 1 vysoká … 3 nízká (blokující mají vždy 1)
otazka: "Jméno otce ženicha v O 1808 fol. 9v: František, Jan, nebo Tomáš?"
kontext: >-
  Proč na tom záleží a co už víme (2–5 vět). Které další kroky čekají.
varianty:                          # možnosti k volbě; uživatel může napsat i vlastní
  - {volba: "František", opora: "Claude; N 1813 č. 49 otec František kolář", ctení: claude}
  - {volba: "Jan",       opora: "rozhodčí čtení gpt-5.5", ctení: openai-medium}
  - {volba: "Tomáš",     opora: "OpenAI low", ctení: openai}
doporuceni: "František — sedí č. 49 a povolání (I1), ale písmo je nečitelné"
snimek: sources/K0224/10060_0011.jpg
vyrez: sources/K0224/10060_0011.jpg.crop-1.jpg     # co se má uživatel podívat
url: https://ebadatelna.soapraha.cz/d/10060/11
souvisi: [patches/P-K0448-01.yml, research/hints/K0448-…md]
vzniklo: {kdo: k0448, kdy: 2026-10-17}
stav: otevřeno                     # otevřeno → rozhodnuto → zapracováno | zamítnuto
rozhodnuti: null                   # vyplní dashboard: {volba, poznamka, kdo: uzivatel, kdy}
zapracovano: null                  # vyplní ten, kdo rozhodnutí promítl: {patch: P-…, kdy}
```

- **Řazení ve frontě:** blokující → priorita → nejstarší.
- **Aplikovaný patch se nemění.** Úprava souboru `status: aplikováno` do Gramps nic nezapíše. Zapracování
  rozhodnutí = **nový patch** (`P-<ID>-<další nn>`; `update_citation` podle Gramps ID citace z `applied:`).
- **Rozhodnuto → zapracovat:** manager (nebo běžící session té osoby) vytvoří patch (`update_citation` zvedne
  jistotu, `update_event` opraví údaj, případně založí rodinu) a vyplní `zapracovano`.
- **Typ `vzorek`** (audit): namátkou ~1 z 10 přijatých klíčových polí (R2) dá session do fronty jako
  nízkou prioritu, ne blokující. Z výsledků se měří skutečná chybovost autonomního čtení a podle ní se
  pravidla zpřísní nebo uvolní.
- **Typ `nastroj`:** chyby nástrojů a metodiky (rozbitý YAML, špatná citace, nekonzistentní data ve stromu),
  které session nemůže opravit sama. Jdou managerovi i do fronty, ať o nich uživatel ví.

## 6. Co vidí uživatel (dashboard)

- **Fronta kontrol**: počet otevřených a blokujících, seznam podle řazení, u položky výřez snímku, varianty
  vedle sebe, doporučení, odkaz na snímek v portálu. Volba varianty nebo vlastní text → zápis rozhodnutí.
- **U osoby ve stromu**: odznak počtu otevřených kontrol (červený = blokující).
- **U události**: počet nezávislých pramenů ①②③ a jistota. Události s jedním pramenem lze filtrovat.

## 7. Brzdy a náklady

- Archivy: platí `docs/archivy/` (≈ 2,5 s mezi požadavky, cache, žádné hromadné stahování svazků).
- OpenAI: běžné čtení `gpt-6.1-sol` low ≈ 0,05 USD/výřez, rozhodčí `gpt-5.5` medium ≈ 0,25 USD. Session
  hlásí útratu v závěrečné zprávě. Strop na osobu ~3 USD; pak se zastaví a ozve se.
- Jedna osoba = jedna session; souběžně nanejvýš ~4 autonomní session (koordinace přes managera).
