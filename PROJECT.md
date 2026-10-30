# Projekt: Statistikassistenten

## Syfte

Statistikassistenten ska göra officiell statistik tillgänglig genom naturliga frågor på svenska, utan att offra verifierbarhet eller metodologisk tydlighet.

## Version 1

Kärnan började med SCB, Eurostat/Comext och Brå men omfattar nu även svenska sektorskällor och internationella källor som World Bank, OECD, WHO, BIS och ECB. Grundflödet ska fortsatt inte kräva användarkonto eller personlig API-nyckel.

## Arkitekturprincip

`fråga → tolkning → källval → metadata → data → normalisering → beräkning → metodkontroll → svar + provenance`

Källspecifika adapters ska kapsla in API- och formatdetaljer. Analyslagret ska arbeta mot en gemensam statistikmodell som införs i steg 2.

## Modellrobusthet

Projektet använder nivån **guided**. Kritiska gates ligger direkt i canonical instruktion så att korrekt kärnbeteende inte beror på att modellen hittar extra knowledgefiler.

## Migration mot GPT Byggaren 1.6.33 (2026-10-30)

- Projektets källfiler och statistikbeteende har bevarats i en säker migrationskopia.
- Kanonisk motor 1.6.33: integritet/självtest PASS; installation PASS.
- Distributioner: Chat, Plugin, Claude Projects, Claude Skills och OpenCode byggda; distributionsvalidering PASS.
- Projektets `unittest`-svit: 99 tester PASS i denna körning (tidigare uppgift om 147 regressionstester avser en annan körning).
- Migreringen omfattar inte funktionell kontroll i verkliga runtimevärdar, live-API-anrop eller CI/release.
- Projektspecifika Python-skript har bevarats. Eventuell separat statistik-Engine till Plugin kräver resursinventering och ett faktiskt självtest före aktivering.
- Gamla byggverktyg har inte raderats innan CI- och beteendeparitet fastställts.

Se `docs/migration-1.6.33.md` för öppna frågor och verifieringsomfattning.

Plugin/Engine-överlämningen och dess verifieringsgränser: `docs/plugin-engine-handoff.md`.
