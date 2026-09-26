# Status

## Lägesbild

De ursprungliga 15 utvecklingsstegen är genomförda. Därefter har källstödet utökats med fem nya nyckelfria/offentliga källor: Kolada, Socialstyrelsen, Folkhälsodata, Arbetsförmedlingen JobSearch och Riksbanken SWEA. Ändringen är validerad som release-kandidat och ligger avsedd för PR-granskning.

## Validering

- 64 regressionstester passerar.
- Projektlint: 0 fel, 0 varningar.
- Modellrobusthet: godkänd.
- Final hygiene före build: godkänd utan findings.
- Distribution validation: PASS för projekt, ChatGPT Chat, ChatGPT Custom och OpenCode.
- Custom GPT Actions verifieras för SCB, Eurostat, Comext, Kolada, Socialstyrelsen, Arbetsförmedlingen och Riksbanken.
- Folkhälsodata använder verifierad PxWeb/webb-fallback i Custom GPT när dynamisk tabellväg inte kan uttryckas säkert som Action.

## Nya källor

- Kolada API v3 – kommun- och regionnyckeltal samt metadata om ursprunglig statistikproducent.
- Socialstyrelsens Statistikdatabas API – vård, socialtjänst, läkemedel, dödsorsaker m.m.
- Folkhälsodata/PxWeb – folkhälsoindikatorer, vaccinationer, smittsamma sjukdomar och levnadsvanor.
- Arbetsförmedlingen JobSearch – platsannonser och annonserad efterfrågan på yrken/kompetenser.
- Sveriges Riksbank SWEA – räntor, växelkurser och relaterade serier.

## Nästa rekommenderade steg

Granska och merge:a PR:n. Skapa därefter en ny release candidate, lämpligen `v1.1.0-rc1`, och verifiera GitHub Actions före stabil `v1.1.0`.
