---
name: precti-zapis
description: Uživatel pošle odkaz na snímek matriky (digi.ceskearchivy.cz/<id>/<snímek>/…) a řekne, který zápis („druhý odspodu", „první řádek", „3. zápis") — stáhni list v plném rozlišení, udělej přesný výřez řádku, přečti VŠECHNA pole, urči, kdo to je vůči stromu (předek, příbuzný, jmenovec), a správně ulož (sources/, hint, log, todo, kontroly). Použij vždy, když uživatel vloží odkaz na zápis se slovy „přepiš", „přečti", „co tam je", „ulož", nebo napíše „/precti-zapis <url> <který zápis>".
---

# Přečti a zařaď zápis z odkazu

Argumenty: **odkaz** na snímek, **který zápis** na listě (pořadí shora/zdola), volitelně **nápověda** uživatele
(„sedláci Novákovi ze Lhoty, nějací příbuzní"). Komunikuj česky. Strom: `python3 tools/wbconfig.py get strom.adresar`
(dál `<strom>`). Jde vždy o **příbuzného nebo jmenovce, který se bude hodit** — i jmenovec se ukládá, jen jinam.

Tohle je krátká úloha na jeden tah: **udělej ji celou v tomtéž tahu**, neslibuj „jdu to ověřit". Žádné subagenty (výjimka jen na pokyn uživatele — sekce 4a).

## 1. Stáhni list (jen ten jeden)

Nejdřív zkontroluj, jestli list už ve stromu není (`<strom>/sources/**/<id>_<snímek:04d>.jpg`,
případně seznam `<strom>/sources/_metodika/stazene-snimky.txt`). Pokud ano, použij ho.

```
uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py fetch "<odkaz>" \
    --dest <scratchpad>/zapis --preview <scratchpad>/zapis/pv.jpg
```

- Stáhne **plné rozlišení** přes cache modulu `digi_trebon` (rate limit, hlavičky jako prohlížeč) + sidecar `.yml`
  s citací. Archiválie, kterou modul nepozná (sčítání, fascikl), se složí přímo — `sidecar_rucne: true` → sidecar napiš sám.
- **Odkaz nese i střed výhledu uživatele**: `…/<id>/<snímek>/<x>/<y>/<zoom>/<rot>` — x, y jsou pixely plného snímku.
  Náhled `pv.jpg` má **mřížku v souřadnicích plného snímku** (červená x, modrá y) a **zelený křížek** v místě,
  kam se uživatel díval. Pořadí zápisu, které uživatel řekl, má přednost; když křížek leží v jiném řádku, řekni to.
- Jiný portál než DigiArchiv: použij MCP `czech-archives` (`fetch_page` / `fetch_archivalie_page`) pro daný modul;
  když modul není, požádej uživatele o snímek.
- **Porta fontium (SOA Plzeň)** modul nemá, ale jde stáhnout jeden snímek ručně: z HTML stránky prohlížeče vezmi `ImagePath`
  (`register/…/<kniha>_<nnnn>-n.jp2`), velikost zjisti `fcgi-bin/iipsrv.fcgi?FIF=<path>&obj=IIP,1.0&obj=Max-size`, obraz
  `…?FIF=<path>&WID=<plná šířka>&QLT=95&CVT=jpeg`. Server neposílá mezicertifikát — stáhni ho z AIA certifikátu
  (`http://crt.harica.gr/HARICA-GEANT-TLS-R1.cer`) a předej curl `--cacert` (systémový bundle + mezicertifikát); ověřování nevypínej.
  Jen jeden snímek, s Refererem a běžným User-Agentem. Sidecar napiš ručně (archiv SOA v Plzni, kniha, snímek, pagina). **Nestahuj sousední listy** — výjimka: rok na listě nikde není
  (ani v záhlaví sloupce, ani u prvního zápisu) → stáhni předchozí list a řekni proč.

## 2. Najdi řádek a sloupce

Z náhledu odečti hranice řádku (y0–y1) a stránek (dvoustrana: levá + pravá). Pak:

1. **Záhlaví sloupců** — výřez hlavičky v plném rozlišení. Pořadí rubrik (katolické/nekatolické, mužské/ženské,
   manželské/nemanželské, mrtvě narozené; u Z stav/náboženství/pohlaví/věk) **se mezi knihami liší** — mapuj
   čárky podle hlavičky, ne zpaměti.
2. **Rok** (záhlaví sloupce, první zápis listu), **pagina** (číslo vpravo nahoře), u knih členěných po vsích
   **název vsi v záhlaví vpravo nahoře**.
3. Řádek čti po **segmentech v plném rozlišení** (cca 600–1000 px široké, výška celého řádku):
   ```
   uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py read <list.jpg> x0 y0 x1 y1 <scratchpad>/zapis/seg-a.jpg
   ```
   Nejistá slova zvětši `--scale 2`–`3`; **tužku a vybledlý inkoust** `--contrast`. Tyto kopie jsou jen ke čtení.
4. **Opakovací značky** („do.", „Idem", „ut supra", „ — ") rozřeš podle zápisu výš na listě a uveď, odkud hodnota je.
5. **Křížky †** u rodičů a manželů, **vpisky nad řádkem** (stříška), **přípisky na okraji** (pozdější sňatek,
   úmrtí, vydaný list) a **ověření listu dole** („testor") — vždy přečíst a zapsat.

## 3. Všechna pole — nic nevynechat

Rutinní hodnota se zapisuje taky (podle ní se pozná výjimka). Co nepřečteš: `[?]`, varianty `[a/b?]`,
a **vypiš zvlášť** — tiché vynechání je horší než přiznaná mezera. Nic nedoplňuj „podle smyslu".

- **Křest (N):** rok · den narození · den křtu · ves + **č. p.** + panství · jméno dítěte · náboženství ·
  **pohlaví** · **manželské/nemanželské** · mrtvě narozené · otec (jméno, stav/povolání, bydliště, **jeho rodiče**
  s povoláním a bydlištěm) · matka (jméno, **rodné příjmení**, její rodiče) · **kmotři** (jméno, stav, bydliště,
  ✚✚✚ = negramotný, „podepsal") · **kněz** · **porodní bába** (jméno, bydliště, zkoušená/nezkoušená) ·
  přípisky na okraji
- **Oddavky (O):** datum · ves + č. p. ženicha i nevěsty · **oddávající** · ženich a nevěsta (povolání, rodiče
  s povoláním a bydlištěm, náboženství, **věk**, **stav**: svobodný/vdovec, zletilost) · **svědci** ·
  poznámky (ohlášky, protokol, povolení, **odkazy na křestní knihu s paginou**)
- **Úmrtí (Z):** datum úmrtí i pohřbu · ves + č. p. · jméno · **vztah** (čí manžel/ka, vdova po kom, dítě koho) ·
  stav · náboženství · pohlaví · **věk (roky/měsíce/dny)** · **příčina smrti** · ohledací list s číslem ·
  místo pohřbu · kdo pohřbil · kdo zaopatřil a kdy · přípisky (úmrtní list vydán …)
- **Sčítání:** každá osoba archu (i čeleď, podnájemníci) · vztah k přednostovi · stav · **datum narození** ·
  **rodiště** · domovská příslušnost · náboženství · povolání a postavení · gramotnost · přítomnost

## 4. Kdo to je — porovnej se stromem

Prohledej strom (`grep -rn -i`) na příjmení i jeho varianty, **číslo domu**, jména rodičů a manželů:
`<strom>/research/STAV-*.md`, `research/people/`, `research/hints/`, `research/todo-*.md`, `research/log.md`.

| Výsledek | Kam to patří |
|---|---|
| **přímý předek** (sedí ≥ 2 nezávislé údaje kromě jména: rodiče, manžel/ka, č. p., obec, věk, povolání) | `sources/K<nnnn>/`, hint `research/hints/K<nnnn>-<datum>-<událost>.md` |
| **sourozenec / dítě předka** | `sources/K<kotva>/`, hint `K<kotva>-<datum>-<popis>.md`, zápis do `todo-<rod>.md` |
| **příbuzný rodu bez K-čísla** | `sources/rod-<rod>/`, hint `rod-<rod>-<datum>-<popis>.md`, `todo-<rod>.md` |
| **jmenovec** (jen jméno, nebo údaje nesedí) | totéž jako příbuzný rodu, v hintu výslovně **„jmenovec — NENÍ …, protože …"** |
| **sporná totožnost** | navíc `research/kontroly/<ID>-<nn>.yml` — rozhoduje uživatel |

- **Pravidlo jmenovce** platí vždy: jméno samo nestačí. Ve vsi bývá víc stejnojmenných rodin — rozlišuj
  **podle č. p. a manželky**.
- Když zápis **mění nebo vyvrací** dřívější údaj (jiný rok narození z věku, křížek u žijícího, jiné č. p.,
  opravené čtení jména) — **nic nepřepisuj potichu**: do původního hintu **připiš** `> **OPRAVA <datum>:** …`
  a do nového hintu uveď obě verze. Novou oporu pro otevřenou kontrolu připiš do jejího `.yml` jako `nove_doklady:`.
- Vypadne-li ze zápisu **další osoba stromu** (babička, nový předek, sourozenec), napiš to — a ověř ji jedním
  dalším zápisem, který už je ve stromu (staženém listu), než ji prohlásíš za tutéž.

### 4a. Sporné čtení — nejdřív uživatel, agent jen na pokyn
Když čtení **klíčového pole** (jméno, rodné příjmení, ves, č. p., datum, povolání rozhodující o totožnosti — např. Sedl/Podl)
zůstane nejisté i po zvětšení a porovnání tvaru písmen s jiným místem listu:
1. **Zeptej se uživatele** — kurent čte rychle a levně. Pošli cestu k malému výřezu (jen to slovo, plné rozlišení) a 1–3 varianty čtení.
   Sporné pole zapiš s `[?]`/`[a/b?]` a pokračuj; nečekej na odpověď s ostatní prací.
2. **Subagenta** (druhé nezávislé čtení) spusť **jen na výslovný pokyn uživatele**, a to:
   - `effort: "high"` (ne max), jeden agent, jedna nejasnost;
   - dej mu **jen malý výřez** (to slovo) + nejvýš jeden malý vzorek téhož písmene odjinud z listu — **nikdy celý list**;
   - nedávej mu své čtení; ať vrátí doslovné čtení písmeno po písmenu, varianty a jistotu, bez dalšího průzkumu.
3. Shoda → do přepisu s poznámkou, kdo ověřil; neshoda → obě varianty do hintu a kontrola `research/kontroly/` (typ `cteni`).
   Shoda dvou čtení pořád není důkaz — jistota zůstává draft (AGENTS.md).

### Sousední zápisy na listě
Projdi zběžně i ostatní řádky listu. Je-li tam **stejné příjmení, stejný dům nebo rodina, kterou strom zná**,
přečti ji celou taky a ulož stejně (uživatel to chce — „ulož si i toho potenciálního bratra").

## 5. Ulož (plné rozlišení, nic nezmenšovat)

1. **Celý list** do cílové složky (`sources/K<nnnn>/` nebo `sources/rod-<rod>/`) jako `<id>_<snímek:04d>.jpg`.
2. **Výřez celého řádku přes obě strany**:
   ```
   uv run --project mcp/czech-archives python skills/precti-zapis/zapis.py crop <list.jpg> x0 y0 x1 y1 \
       <strom>/sources/<složka>/<id>_<snímek:04d>_radek-<událost>-<jméno>-<rok>.jpg
   ```
   Detaily sporných míst stejně (`…_detail-<co>.jpg`), **bez zmenšení**.
3. **Sidecar** `<id>_<snímek:04d>.yml`: doplň `entry` (pořadí zápisu na listě, datum, jméno, č. p., rodiče),
   `page` (pagina), `crops:` (seznam výřezů s popisem); do `text` pořadí zápisu a jméno. Existující sidecar
   nepřepisuj, jen doplň.
4. Seznam stažených snímků (`sources/_metodika/stazene-snimky.txt`), pokud ho strom vede.

## 6. Zapiš

- **Hint** (šablona níže) — doslovný přepis všech polí, nejistá čtení, totožnost, co z toho plyne, pro managera.
  **Odkazy piš jako relativní markdown** (`[`soubor`](../../sources/…)`, `[hint](jiny-hint.md)`, `[todo](../todo-<rod>.md)`), ne holé cesty
  v backtickách — uživatel čte MD v editoru a klikne. Nový hint přidej do rozcestníku v `research/STAV-*.md` (sekce Rozcestník).
- **`research/log.md`** — připiš na konec: datum, kniha/snímek/pořadí, výsledek, odkaz na hint.
- **`research/todo-<rod>.md`** — u příbuzných a jmenovců (formát z hlavičky souboru, jen `cat >>`).
- **Kontroly** — sporná totožnost nebo čtení klíčového pole → nová kontrola, nebo `nove_doklady:` do existující.
- **Nepiš** do dossierů osob (`research/people/`), do Gramps ani patchů — to je session osoby / manager.

```markdown
# <K-číslo nebo rod> <Jméno> — <UDÁLOST> (<datum>, <ves> č. <č. p.>)

Od: <session> · datum: <dnes> · jistota: <typ pramene>, identita **<jistá/silná/pravděpodobná/jmenovec>**.
Odkaz dal uživatel.

## Pramen (PŘESNÉ MÍSTO NÁLEZU)
<archiv>, <farnost>, **<N/O/Z> <roky> (id <id>), snímek <n> (pag. <p>), <k>. zápis na listě**.
Celý list [`<id>_<sn>.jpg`](../../sources/<složka>/<id>_<sn>.jpg) · řádek [`…_radek-….jpg`](../../sources/<složka>/…) · detaily … · sidecar [`….yml`](../../sources/<složka>/….yml). Online: <url>

## Doslovný přepis — všechna pole
| Sloupec | Zápis |
|---|---|

### Nejisté čtení
## Totožnost (body shody / proč jmenovec)
## Co z toho plyne
(nové osoby, posunutá data, okna pro hledání: **kniha + id + přibližné snímky**, kde je hledat)
## Pro managera
```

## 7. Odpověď uživateli

Krátce, bez ceremonie:
1. Jedna věta: **kdo to je** vůči stromu (např. „první dítě K0016", „jmenovec, jiný dům").
2. **Tabulka všech polí** (doslovně, zkratky rozepsané jen v závorce).
3. **Co z toho plyne** — body; u úmrtí a rozporů **konkrétní tip, kde hledat dál** (kniha, id, snímky, odkaz) —
   uživatel čte novější knihy rychleji než ty, dej mu cíl.
4. Kam se co uložilo (jedna věta s cestami).

Nejistá čtení označ i v odpovědi. Nic, co nebylo přečteno, nevydávej za přečtené.
