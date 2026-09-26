# SCB-adapter

SCB-adaptern översätter en källneutral statistikfråga till verifierade anrop mot SCB Statistikdatabasens PxWebApi v2.

## Bas-URL

`https://statistikdatabasen.scb.se/api/v2`

## Flöde

1. Sök tabeller med `GET /tables?lang=sv&query=<term>&pageSize=<n>`.
2. Rangordna kandidater semantiskt, men välj inte tabell enbart på titelträff.
3. Hämta metadata för kandidat med `GET /tables/{id}/metadata?lang=sv`.
4. Matcha användarens semantiska dimensioner mot metadata och kontrollera obligatoriska variabler.
5. Bygg en explicit selection-plan.
6. Hämta minsta nödvändiga data via `GET` för små enkla frågor eller `POST /tables/{id}/data` för komplexa frågor.
7. Normalisera svaret till `schemas/statistical-result.schema.json` innan analys.

## Regler

- Tabell-ID får endast komma från `/tables` eller en användarverifierad källa, aldrig från gissning.
- Variabelkoder och värdekoder får endast komma från verifierad metadata.
- `latest` löses mot metadata, inte mot kalenderdatum.
- Obligatoriska variabler får inte utelämnas.
- Om en kodelista behövs ska den följa metadata. Specialtecken i fristående `/codelists/{id}` kan vara problematiska; föredra metadata-/selection-vägen när sådan kodelista redan refereras av tabellen.
- Uttag ska hållas under SCB:s publicerade cellgräns. Frågor som riskerar att bli stora ska begränsas eller delas deterministiskt.

## Adapterkontrakt

Se `schemas/scb-adapter.schema.json` för discovery-, metadata- och data-planer.
