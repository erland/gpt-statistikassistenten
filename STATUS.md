# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Pågående steg 21 breddar Brå från enbart anmälda brott till flera officiella produkter i rättskedjan.

## Pågående Brå-utbyggnad

- Anmälda brott.
- Handlagda brott.
- Misstänkta personer.
- Handlagda brottsmisstankar.
- Personer lagförda för brott.
- Narkotikabrott/preparat hanteras som dimensioner i generella Brå-produkter när de publiceras, inte som en separat specialintegration.
- Ingen generell Brå-API-endpoint antas; officiell tjänst, tabell eller publicerad fil verifieras per produkt.
- OpenCode-adaptern stöder produktupptäckt, produktmetadata och validerade urvalsplaner.

## Metodprincip

Personer, brott, brottsmisstankar och lagföringsbeslut är olika observationsenheter. Statistikassistenten ska välja rätt produkt före datauttag och får inte blanda dem utan METHOD-GATE.

## Nästa rekommenderade steg

Kör full CI/distributionsvalidering och merge:a först efter grön kontroll.
