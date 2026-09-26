# {{GPT_NAME}} – OpenCode-distribution

Detta paket är en portabel OpenCode-runtime för Statistikassistenten.

## Användning

1. Packa upp ZIP-filen som ett eget OpenCode-workspace.
2. Öppna workspace-roten i OpenCode.
3. OpenCode läser root `AGENTS.md` som projektinstruktion.
4. `knowledge/` innehåller käll- och metodreferenser som kan läsas när de behövs.
5. `.opencode/tools/` innehåller genererade, typade wrappers för Statistikassistentens deterministiska Pythonverktyg.
6. `.opencode/runtime-scripts/` innehåller endast de canonical script som uttryckligen deklarerats som runtimeverktyg.
7. `.opencode/runtime-contract.json` beskriver hur canonical kontrakt realiseras i OpenCode.

## Externa statistikdata

De lokala verktygen planerar, validerar, normaliserar, beräknar och kvalitetssäkrar. De gör inte godtyckliga nätanrop på egen hand. När aktuell statistik behövs ska agenten hämta den från officiell källa och följa `METADATA-GATE`, `DATA-GATE`, `METHOD-GATE` och `PROVENANCE-GATE` i `AGENTS.md`.

- SCB: använd officiell Statistikdatabas/PxWebApi v2.
- Eurostat: använd officiell SDMX-tjänst.
- Comext: använd Eurostats officiella Comext/SDMX-tjänst.
- Brå: använd officiell statistiktjänst eller publicerad statistikfil och verifiera metadata före analys.

## Verktyg

OpenCode-konfigurationen tillåter de genererade, icke-muterande statistikverktygen direkt. Generell `bash` och redigering kräver godkännande. Verktygen omfattar källplanering, SCB/Eurostat/Comext/Brå-planering, beräkningar, presentation/export och quality gate.

## Viktigt

`AGENTS.md` och `.opencode/runtime-contract.json` är genererade projektioner. Canonical källa är projektets ursprungliga GPT-kontrakt, inte filerna i denna runtime-distribution.

## Version

{{VERSION}}
