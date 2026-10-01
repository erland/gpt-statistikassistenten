# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Pågående steg 22 förbättrar användningen av den befintliga generella SCB-adaptern för svensk handel, e-handel och hushållskonsumtion.

## Pågående SCB-förbättring

- Detaljhandel, dagligvaru-/sällanköpsvaruhandel, försäljningsvolym, partihandel, e-handel och hushållens konsumtion routas tydligare till SCB.
- Import/export, partnerland och varukod routas fortsatt till Comext.
- Frågor som kombinerar inhemsk handel och utrikeshandel kan planera SCB + Comext.
- Ingen ny SCB-handelsadapter eller hårdkodade tabell-ID:n införs.
- Metodregler skiljer omsättning från volym, löpande från fasta priser, råa från kalender-/säsongskorrigerade serier samt företags- från konsument-e-handel.
- Tabellspecifika symboler och dokumenterade metodförändringar ska verifieras via metadata/dokumentation före tolkning.

## Nästa rekommenderade steg

Kör full CI och merge:a först efter grön distributionsvalidering.
