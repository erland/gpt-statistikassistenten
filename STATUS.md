# Status

## Lägesbild

De ursprungliga utvecklingsstegen och tidigare källutbyggnader är genomförda. Pågående steg 19 lägger till två nyckelfria narkotikarelaterade källor: EUDA/SCORE och Tullverkets beslagsstatistik.

## Pågående utbyggnad

- EUDA/SCORE wastewater analysis: verifierad 2026-distribution med CSV för observationer och SiteID-baserad platsmetadata.
- Tullverket: officiell beslagsstatistik med CSV-export, utan antagande om odokumenterat internt API.
- Källplaneraren skiljer avloppsmätningar från tullbeslag och kan kombinera båda först efter METHOD-GATE.
- ChatGPT Custom får EUDA Action; Tullverket använder officiell webb/CSV-fallback.
- OpenCode får deterministiska wrappers för båda adaptrarna.

## Metodprinciper

Avloppsmätningar, beslag, brottsstatistik och vårdutfall mäter olika fenomen. Avloppsdata får inte beskrivas som antal användare/prevalens och beslag får inte beskrivas som konsumtion eller marknadsstorlek.

## Nästa rekommenderade steg

Kör full CI/distributionsvalidering. Därefter görs en separat lämplighetsanalys av möjlig utökning av Brå och RMV innan någon sådan implementation påbörjas.
