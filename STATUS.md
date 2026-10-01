# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Steg 21 breddar Brå från enbart anmälda brott till flera officiella produkter i rättskedjan.

## Genomförd Brå-utbyggnad

- Anmälda brott.
- Handlagda brott.
- Misstänkta personer.
- Handlagda brottsmisstankar.
- Personer lagförda för brott.
- Narkotikabrott/preparat hanteras som dimensioner i generella Brå-produkter när de publiceras, inte som separat specialintegration.
- Ingen generell Brå-API-endpoint antas; officiell tjänst, tabell eller publicerad fil verifieras per produkt.
- OpenCode-adaptern stöder produktupptäckt, produktmetadata och validerade urvalsplaner.
- Befintlig adapter för anmälda brott är bakåtkompatibel.

## Metodprincip

Personer, brott, brottsmisstankar och lagföringsbeslut är olika observationsenheter. Statistikassistenten väljer rätt produkt före datauttag och blandar dem inte utan METHOD-GATE.

## Validering

- 92 regressionstester passerar.
- Projektlint: 0 fel, 0 varningar.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #7.
