# Custom GPT Actions

Distributionen innehåller tre OpenAPI-underlag i `builder/actions/`:

1. `scb-openapi.yaml` – sök tabeller, läs metadata och hämta data från SCB PxWebApi v2.
2. `eurostat-openapi.yaml` – läs Eurostat-katalog/dataflow och hämta filtrerad SDMX-data via en verifierad series-key.
3. `comext-openapi.yaml` – läs Comext-dataflow och hämta filtrerad handelsdata via verifierad series-key.

Ingen av dessa kräver API-nyckel i grundversionen. Lägg dem som separata Actions i GPT Builder. Brå hanteras genom webbsökning och officiella filer/webbsidor, inte en påhittad Action.

### Säker användning
- Använd Action först efter källval.
- Läs metadata före data.
- Skapa aldrig kod eller series-key från minnet när den kan verifieras.
- Begränsa datauttag till frågans faktiska behov.
- Om API:t returnerar ett fel eller oväntad struktur, gå tillbaka till metadata i stället för att gissa.
