# Checklist osoby

Checklist říká, **co by se u osoby mělo dát ověřit**, podle doby a místa, kde žila. Generuje se
automaticky: šablona podle období × citace v Gramps → stav každé položky. Ruční výjimky se píšou do
`research/people/<ID>.md` (např. „sčítání 1869 pro obec nedochováno“).

## Stav položky

`[x]` doloženo primárním pramenem (jistota ≥ 3) · `[~]` jen odvozený / slabý pramen ·
`[-]` hledáno, nenalezeno (s odkazem na log) · `[n]` pramen pro místo/dobu neexistuje · `[ ]` nehledáno

## Šablona podle období

Položka se nabízí, když se období pramene překrývá s životem osoby (detaily pramenů:
[`../prameny/README.md`](../prameny/README.md)).

| Položka | Kdy se nabízí |
|---|---|
| narození / křest — matrika N | vždy (matriky v Čechách souvisle hlavně od pol. 17. st.) |
| sňatek — matrika O | ženatí / vdané |
| úmrtí / pohřeb — matrika Z | zemřelí |
| sňatek rodičů — matrika O | vždy (ověřuje vazbu na rodiče) |
| narození sourozenců | vždy (kontrola rodiny, č. p., kmotrů) |
| soupis poddaných 1651 | žil kolem 1651 |
| berní rula 1654 (Čechy) / lánové rejstříky (Morava) | držitel usedlosti kolem 1654 |
| tereziánský katastr | držitel usedlosti 1748–1757 |
| josefský katastr | držitel usedlosti 1785–1789 |
| stabilní katastr (indikační skica) | držitel usedlosti 1824–1843 |
| pozemková / gruntovní kniha | držitel usedlosti (16.–20. st.) |
| sčítání lidu 1857, 1869, 1880, 1890, 1900, 1910, 1921 | žil v daném roce |
| policejní přihláška Praha | pobyt v Praze 1850–1914 |
| vojenský kmenový list (VÚA) | muž, odvodní věk v 19. st. – 1918 |
| Verlustlisten / kartotéka padlých 1. sv. v. | muž, služba 1914–1918 |
| legionáři (VÚA) | muž, 1914–1920 |
| padlí 2. sv. v. / odboj / holocaust.cz | 1938–1945 |
| domovský list / domovská obec | 1863–1948 |
| školní matriky / katalogy | dítě v 19.–20. st. |
| hrob (BillionGraves, hřbitovní evidence) | zemřelí, hlavně 19.–20. st. |
| parte, noviny (Kramerius) | 19.–20. st. |
| vystěhování (lodní seznamy, Ellis Island) | podezření na emigraci |

U žijících a nedávno zemřelých platí lhůty: N 100 let, O a Z 75 let — mladší záznamy jen na
matričním úřadě (oprávněná osoba / přímý příbuzný).
