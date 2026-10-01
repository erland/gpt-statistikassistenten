# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Steg 23 lägger till Statskontorets öppna data för statens budget och myndighetsförteckning.

## Genomförd Statskontoret-integration

- Månadsutfall för statens budget planeras från Statskontorets officiella öppna data, inklusive myndighet och anslagspost/anslagsdelpost.
- Årsutfall används för budget och utfall per anslag med bevarad preliminär/definitiv status.
- Myndighetsförteckningen används för årsarbetskrafter och organisationsmetadata.
- Runtime väljer den aktuella CSV/Excel-distribution som publiceras på den officiella produktsidan; inget odokumenterat Hermes-API eller hårdkodat filnamn används.
- SCB används fortsatt för antal anställda och löner per myndighet.
- Metodregler skiljer anslagsutfall från myndighetens totala periodiserade kostnad samt årsarbetskrafter från antal anställda.

## Validering

- 110 regressionstester passerar.
- Projektlint: 0 fel, 0 varningar.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #9.
