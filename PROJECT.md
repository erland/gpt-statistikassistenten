# Projekt: Statistikassistenten

## Syfte

Statistikassistenten ska göra officiell statistik tillgänglig genom naturliga frågor på svenska, utan att offra verifierbarhet eller metodologisk tydlighet.

## Version 1

Version 1 fokuserar på SCB, Eurostat/Comext och Brå. Grundflödet ska inte kräva användarkonto eller personlig API-nyckel.

## Arkitekturprincip

`fråga → tolkning → källval → metadata → data → normalisering → beräkning → metodkontroll → svar + provenance`

Källspecifika adapters ska kapsla in API- och formatdetaljer. Analyslagret ska arbeta mot en gemensam statistikmodell som införs i steg 2.

## Modellrobusthet

Projektet använder nivån **guided**. Kritiska gates ligger direkt i canonical instruktion så att korrekt kärnbeteende inte beror på att modellen hittar extra knowledgefiler.
