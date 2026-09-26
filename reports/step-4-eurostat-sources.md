# Steg 4 – verifierade Eurostat-källor

Verifierat 2026-09-26 mot Eurostats officiella användarguide.

- SDMX 3.0 kan lista publika dataflows, hämta strukturmetadata och hämta hela eller filtrerade dataset.
- Dataquery använder `/data/{context}/{agencyID}/{resourceID}/{version}/{key}` och stöder komponentfilter via `c[DIMENSION]=...`.
- Flera komponentvärden separeras med komma (OR). Tidsintervall kan uttryckas med operatorer som `ge:` och `le:` sammanfogade med `+`.
- Strukturella metadata omfattar bl.a. dataflows, DSD:er och codelists.
- Comext/Prodcom har separata API-endpoints för `DS-`-prefixerade dataset och behandlas separat i nästa steg.

Källor:
- https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx3.0
- https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/sdmx3-0/data-query
- https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/sdmx3-0/structure-queries
- https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction
