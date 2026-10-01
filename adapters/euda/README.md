# EUDA-adapter

EUDA-adaptern använder öppna data från European Union Drugs Agency utan API-nyckel.

Första implementerade datasetfamiljen är **EUDA/SCORE wastewater analysis**. Metadata och metodregler verifieras på EUDA:s officiella factsheet och observationerna hämtas från de publicerade CSV-filerna.

## Viktiga regler

- Källa ska anges som **EUDA och SCORE**.
- Enheten i huvudtabellen är populationsnormaliserad mängd drogrest per dag, normalt `mg/1000 population/day`.
- Avloppsdata är en konsumtionssignal på samhällsnivå och får **inte** tolkas som antal användare eller prevalens.
- Kokain mäts via metaboliten benzoylecgonine och cannabis via THC-COOH.
- Platsmetadata ska kopplas via `SiteID`.
- Den verifierade 2026-distributionen innehåller studier 2011–2025. Runtime ska kontrollera factsheet före användning och inte anta att framtida distributioner har samma URL eller struktur.
