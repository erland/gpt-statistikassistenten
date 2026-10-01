# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Steg 22 förbättrar användningen av den befintliga generella SCB-adaptern för svensk handel, e-handel och hushållskonsumtion.

## Genomförd SCB-förbättring

- Detaljhandel, dagligvaru-/sällanköpsvaruhandel, försäljningsvolym, partihandel, e-handel och hushållens konsumtion routas tydligare till SCB.
- Import/export, partnerland och varukod routas fortsatt till Comext.
- Frågor som kombinerar inhemsk handel och utrikeshandel kan planera SCB + Comext.
- Ingen ny SCB-handelsadapter eller hårdkodade tabell-ID:n införs.
- Metodregler skiljer omsättning från volym, löpande från fasta priser, råa från kalender-/säsongskorrigerade serier samt företags- från konsument-e-handel.
- Tabellspecifika symboler och dokumenterade metodförändringar verifieras via metadata/dokumentation före tolkning.
- Routingkonflikter har samtidigt korrigerats så att ordet `från` inte feltolkas som brottstypen rån och så att detaljerad varuhandel med exempelvis Kina inte felaktigt drar in World Bank.

## Validering

- 99 regressionstester passerar.
- Projektlint: 0 fel, 0 varningar.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #8.
