# Custom GPT Actions

Distributionen innehåller sju OpenAPI-underlag i `builder/actions/`:

1. `scb-openapi.yaml` – SCB PxWebApi v2.
2. `eurostat-openapi.yaml` – generell Eurostat SDMX.
3. `comext-openapi.yaml` – Eurostat Comext.
4. `kolada-openapi.yaml` – Kolada API v3 för KPI-metadata och kommunvärden.
5. `socialstyrelsen-openapi.yaml` – metadata/ämnen i Socialstyrelsens Statistikdatabas API.
6. `arbetsformedlingen-openapi.yaml` – publik JobSearch för platsannonser.
7. `riksbank-openapi.yaml` – Riksbankens SWEA för serier, räntor och växelkurser.

Dessa grundanrop kräver ingen personlig API-nyckel eller inloggning. Lägg dem som separata Actions i GPT Builder. Folkhälsodata använder ett hierarkiskt PxWeb API där tabellvägen varierar; använd därför officiell webb/PxWeb-åtkomst när runtime inte kan uttrycka den dynamiska sökvägen säkert som Action. Brå hanteras fortsatt via officiell statistiktjänst eller publicerade filer/webbsidor.

### Säker användning
- Använd Action först efter källval.
- Läs metadata före data.
- Skapa aldrig KPI-, serie-, dimensions- eller tabellkod från minnet när den kan verifieras.
- Begränsa datauttag till frågans faktiska behov och följ respektive källas paginering/tak.
- Arbetsförmedlingens annonser är en efterfrågesignal, inte ett direkt mått på arbetslöshet eller sysselsättning.
- För Kolada ska ursprunglig statistikproducent i metadata bevaras i proveniensen.
- Om API:t returnerar fel eller oväntad struktur, gå tillbaka till metadata i stället för att gissa.
