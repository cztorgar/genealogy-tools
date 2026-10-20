# Kontext a příběhy osob

Strukturovaná data (události, citace, jistota) zachytí *co*, ale ztrácí *jak a proč*: cholera ve vsi,
přípisek faráře, kmotři z „lepší“ rodiny, stěhování mezi čísly popisnými, děti umírající v jednom roce,
„Israelitka“ u matky, podpis na sčítacím archu. Proto ve dvou krocích:

## 1. Kontext — sbírat průběžně, surově, hned

Každá session zapisuje do dossieru osoby sekci **`## Kontext`** — volné poznámky, jakmile na něco narazí,
**ne až na konci** (po zavření session je to pryč). Jeden bod = jedno pozorování + odkaz na pramen:

```
- 1855 · v Z Žiželice 14 za VIII–IX/1855 neobvykle mnoho úmrtí, příčina „cholera“ (sn. 120–126) — v č. 49 umírá … [Z 14 sn. 123]
- kmotr u všech dětí: Jan Pospíšil, rychtář z č. 12 → rodina měla vazbu na obecní elitu [N 01 sn. 44, 57, 60]
- farář připsal k zápisu „Israelitka“ — konvertitka? jinde nedoloženo [Z 11 sn. 24]
- podpis vlastní rukou v sčítacím archu 1921 (umí psát) [sčítání Kladruby 1921 č. 40]
```

Co tam patří: okolnosti zápisů (příčiny smrti, epidemie, nemanželské děti, legitimace, dispens, přípisky,
opravy), sociální síť (kmotři, svědci, porodní báby, sousedé), bydlení a stěhování (č. p., výměnky),
povolání a jejich změny, gramotnost (podpis / křížek), vojna, válka, náboženství, zajímavosti o obci
z místopisu (`docs/mistopis/`), věci, které se nevešly do patche. Odhady a domněnky značit („asi“, „?“).

## 2. Příběh — krátký článek z ověřených údajů

Soubor **`research/pribehy/<ID>.md`** ve stromu. Píše ho session osoby (nebo větve) **při dokončení osoby**,
z dossieru, sekce Kontext, přepisů a patchů. Znovu se přepíše, když přibydou podstatná fakta.

Pravidla:
- **Žádná fikce.** Žádné vymyšlené myšlenky, pocity, rozhovory, počasí, vzhled. Každé tvrzení má oporu
  v pramenu (odkaz v hranatých závorkách na konci věty nebo odstavce, jako v Kontextu).
- **Nejistota zůstává vidět:** „patrně“, „podle věku při úmrtí asi kolem roku 1750“, „jméno je v zápisu nečitelné“.
  Rozpory se nezamlčí.
- **Dobový a místní kontext** je dovolený, jen když je doložený (místopis, pamětní kniha, matrika — např.
  počet úmrtí na choleru v daném roce) a je zřejmé, že jde o kontext, ne o fakt o osobě.
- Rozsah 150–400 slov, souvislý text v češtině, chronologicky. Nadpis: jméno, roky, obec.
- Na konci **„Z čeho vycházím“** (seznam pramenů) a **„Co nevíme“** (otevřené otázky, odložené věci).
- Jistota 0 (MyHeritage) do příběhu nepatří, nanejvýš do „Co nevíme“ jako nápověda.
- Žijící osoby: příběh jen interně (nepublikovat), stejně jako ostatní data.

Šablona:

```markdown
# Josef Novák (1815–1887), barvíř v Žiželicích

<text>

**Z čeho vycházím:** N Žiželice 01 sn. 57 (křest 1815) · O Žiželice 09 … · Z … · sčítání 1869, 1880
**Co nevíme:** …
```

## Kde se to ukazuje

Dashboard v panelu osoby (záložka Příběh) a sekce Kontext z dossieru.
