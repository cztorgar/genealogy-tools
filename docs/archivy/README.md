# Archivy a portály

Výchozí přehled: [genealogie.cz – digitalizace](https://www.genealogie.cz/aktivity/digitalizace/)
(částečně zastaralý — SOA Praha už nepoužívá Acta Publica, Litoměřice mají nový portál).
Stav k 16. 10. 2026; **[ověřit]** = nepotvrzeno.

Obecně: **žádný portál nemá veřejné API ani IIIF**, matriky jsou snímky bez jmenného indexu.
Lhůty zveřejnění: N 100 let, O a Z 75 let.

| Archiv / portál | Obsah | Technika | Modul | Detail |
|---|---|---|---|---|
| **SOA Zámrsk – ARON** (dnes SOA v Hradci Králové) [aron.vychodoceskearchivy.cz](https://aron.vychodoceskearchivy.cz/) | ~14 200 svazků matrik (většina digitalizovaná), sčítací operáty KHK+PK, inventář PDF | React SPA nad JSON `/api/aron` (nedokumentováno, bez přihlášení, ověřeno); originální JPG po snímcích, **celé matriky jako ZIP s JPG** (stovky MB); podmínky užití nezveřejněny, stahování oficiálně nabízeno | `aron_zamrsk` (hotový, v0.1) | [aron-zamrsk.md](aron-zamrsk.md) |
| **SOA Praha – eBadatelna** [ebadatelna.soapraha.cz](https://ebadatelna.soapraha.cz/) | ~12 300 knih matrik Středočeského kraje (N/O/Z + indexy), hledání podle lokality (~10 000 názvů vč. historických) i názvu knihy | Apache Wicket, HTML bez API, anonymní session (ověřeno); originální JPG po snímcích přes odkaz „stáhnout“ bez přihlášení; ZIP celé knihy jen pro registrované; podmínky užití nezveřejněny, neregistrovaným výslovně povoleno prohlížet všechny snímky | `ebadatelna_praha` (hotový, v0.2) | [ebadatelna-praha.md](ebadatelna-praha.md) |
| **SOA Třeboň – DigiArchiv** [digi.ceskearchivy.cz](https://digi.ceskearchivy.cz/) | ~10 000 svazků všech církví, soupisy poddaných, sčítání 1857–1921, kroniky; **přepis indexů s hledáním podle jména** | starší JS aplikace | — (nevznikne: blok UA „genealogy“, podmínky zakazují kopírování; G-02) | [trebon.md](trebon.md) |
| **SOA Plzeň – Porta fontium** [portafontium.eu](https://www.portafontium.eu/) | matriky západní Čechy + Bavorsko, kroniky, sčítání | DZI dlaždice (IIPImage); anti-bot (403) | `portafontium` | |
| **SOA Litoměřice** [digi.soalitomerice.cz](https://digi.soalitomerice.cz/digitalnibadatelna/) | ~12 000 svazků do 1910, sčítání, rejstřík obcí CZ/DE | nový portál, bot challenge | `litomerice` | |
| **MZA Brno – Acta Publica** [mza.cz/actapublica](https://www.mza.cz/actapublica/) | ~10 000 svazků, Morava | přihlášení, DZI; **blokuje IP při překročení limitů** | `actapublica_mza` | |
| **ZA Opava** [digi.archives.cz](https://digi.archives.cz/da) | ~8 000 svazků, sev. Morava a Slezsko | DZI, Radware Bot Manager | `opava` | |
| **Archiv hl. m. Prahy** [ahmp.cz](https://www.ahmp.cz/) | ~2 500 matrik pražských farností | [ověřit] | `ahmp` | |
| **Národní archiv** [nacr.cz](https://www.nacr.cz/) | policejní přihlášky 1850–1914 (**jmenný vyhledávač**), židovské matriky, katastry | [ověřit] | `nacr` | |
| **VÚA** [vuapraha.cz](https://www.vuapraha.cz/) | vojenské matriky, kartotéka padlých, legionáři | jmenné vyhledávání | `vua` | |
| **Kramerius** [digitalniknihovna.cz](https://www.digitalniknihovna.cz/) | noviny, schematismy, adresáře, Verlustlisten | **veřejné REST API v7** | `kramerius` | |
| **ČÚZK archivní mapy** [ags.cuzk.gov.cz/archiv](https://ags.cuzk.gov.cz/archiv/) | stabilní katastr | [ověřit WMS] | `cuzk_mapy` | |
| **holocaust.cz** [databáze obětí](https://www.holocaust.cz/databaze-obeti/) | oběti šoa | jmenné vyhledávání | `holocaust_cz` | |
| **FamilySearch** | obrázky části SOA (Litoměřice, Opava, Třeboň, Zámrsk), malé indexy; Slovensko | API jen se schválením; jen Chrome, přihlašuje uživatel | — | [slovensko.md](slovensko.md) |
| **Matricula** [data.matricula-online.eu](https://data.matricula-online.eu/) | DE, AT, PL — příhraničí (Pasov, St. Pölten), Vídeň a Dolní Rakousy; **české fondy nemá** | HTML; snímky jen v prohlížeči (403 mimo `?pg=`, robots.txt zakazuje `?pg=`) | `matricula` (v0.1, jen metadata) | [matricula.md](matricula.md) |
| **Archiv UK, Monasterium, Manuscriptorium, Archiv města Ostravy** | specializované | | — | |

## Pravidla stahování

- Na vyžádání, **rychlostí člověka** (sekundy mezi požadavky), přes lokální cache — nikdy hromadný mirror.
- Před implementací modulu přečíst **podmínky užití** portálu a zapsat je do detailu archivu.
- Kde portál nabízí oficiální stažení (ZIP v ARONu), použít to místo procházení dlaždic.
