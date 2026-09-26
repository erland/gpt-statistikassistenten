# {{GPT_NAME}} – Custom GPT-distribution

Detta paket innehåller Builder-underlaget för **{{GPT_NAME}}**.

## Installera

1. Öppna GPT Builder och skapa en ny GPT.
2. Klistra in `builder/instructions.md` som instruktion.
3. Lägg in `builder/conversation-starters.md`.
4. Följ `builder/capabilities.md` och aktivera Webbsökning samt Dataanalys.
5. Ladda upp filerna i `builder/knowledge-package/` som Knowledge.
6. Lägg in OpenAPI-filerna i `builder/actions/` som tre separata Actions med autentisering **None**.
7. `builder/runtime-contract.json` dokumenterar canonical runtime-kontraktet.
8. Läs `COMPATIBILITY.md` för reducerad funktionalitet och Brå-fallback.

## Actions

- SCB PxWebApi v2
- Eurostat SDMX 3.0
- Eurostat Comext SDMX 3.0

Brå hanteras i version 1 via officiell webb/statistikfil och Webbsökning, eftersom distributionen inte antar något generellt publikt Brå-API.

## Version

{{VERSION}}
