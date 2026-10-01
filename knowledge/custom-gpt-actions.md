# Custom GPT Actions

Distributionen innehåller fjorton OpenAPI-underlag i `builder/actions/`:

1. `scb-openapi.yaml` – SCB PxWebApi v2.
2. `eurostat-openapi.yaml` – generell Eurostat SDMX.
3. `comext-openapi.yaml` – Eurostat Comext.
4. `kolada-openapi.yaml` – Kolada API v3 för KPI-metadata och kommunvärden.
5. `socialstyrelsen-openapi.yaml` – metadata/ämnen i Socialstyrelsens Statistikdatabas API.
6. `arbetsformedlingen-openapi.yaml` – publik JobSearch för platsannonser.
7. `riksbank-openapi.yaml` – Riksbankens SWEA för serier, räntor och växelkurser.
8. `forsakringskassan-openapi.yaml` – metadata för Försäkringskassans öppna statistik.
9. `smhi-openapi.yaml` – SMHI MetObs för parameter-/stationsmetadata och observationer.
10. `worldbank-openapi.yaml` – World Bank Indicators API v2.
11. `oecd-openapi.yaml` – OECD Data Explorer SDMX.
12. `bis-openapi.yaml` – BIS SDMX REST API v2.
13. `ecb-openapi.yaml` – ECB Data Portal SDMX.
14. `euda-openapi.yaml` – EUDA/SCORE:s verifierade 2026-CSV för avloppsdata och platsmetadata.

Dessa grundanrop kräver ingen personlig API-nyckel eller inloggning. Lägg dem som separata Actions i GPT Builder. Folkhälsodata, Energimyndigheten och Jordbruksverket använder hierarkiska PxWeb-vägar, och Skolverkets statistik-API har versionsstyrda/dynamiska resurser; använd därför verifierad officiell webb/API-åtkomst när en säker generell Action inte kan uttryckas. WHO använder aktuell World Health Data Hub-export/API i stället för det utfasade äldre GHO OData-kontraktet. Tullverket använder officiell webb/CSV-export eftersom ett stabilt generellt API inte är dokumenterat. Brå hanteras fortsatt via officiell statistiktjänst eller publicerade tabeller/filer per produkt; ingen generell Brå-Action antas.

### Säker användning
- Använd Action först efter källval.
- Läs metadata före data.
- Skapa aldrig KPI-, serie-, dimensions- eller tabellkod från minnet när den kan verifieras.
- Begränsa datauttag till frågans faktiska behov och följ respektive källas paginering/tak.
- Arbetsförmedlingens annonser är en efterfrågesignal, inte ett direkt mått på arbetslöshet eller sysselsättning.
- För Kolada ska ursprunglig statistikproducent i metadata bevaras i proveniensen.
- EUDA wastewater ska alltid tolkas som populationsnormaliserad restmängd, inte antal användare/prevalens.
- Om API:t returnerar fel eller oväntad struktur, gå tillbaka till metadata i stället för att gissa.
