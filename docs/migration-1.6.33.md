# Migration till GPT Byggaren 1.6.33

Datum: 2026-10-30. Källa: bifogat gpt-statistikassistenten-main.zip, originalet orört.

## Genomfört

1. Inventering och säker kopieringsmigrering med originalverktyget `migrate_legacy_copy.py`.
2. Kontroll av originalmotorn 1.6.33 med kanoniskt självtest: PASS.
3. Genomgång av projektschemat: äldre profil hade bara tre aktiva moderna runtime-mål och saknade båda Claude-projektionerna.
4. Kompletterade runtimekontrakt för Claude Projects och Claude Skills enligt motorversion 1.6.33. Historisk Custom GPT har inaktiverats som distributionsmål men dess projektspecifika resurser har bevarats.
5. Kanonisk installation, bygge och distributionsvalidering: PASS, fem runtimepaket och projektpaket.
6. Projektets `unittest`-svit: 99 tester PASS.

## Ej verifierat / blockerar release

- Funktionella värdtester i ChatGPT Chat, OpenAI Plugin, Claude Projects/Skills och OpenCode. Paketbyggnad motsvarar inte full runtimeparitet.
- Statistikfrågor mot externa live-API:er och hostverktyg.
- Projektets CI/releaseworkflow kan innehålla kvarvarande anrop till äldre vendorerade verktyg. Granska och kör CI före merge/release.
- Statistikskriptens behov av en separat Plugin-Engine, resurser och faktiskt självtest. Ingen statistik-Engine har automatiskt aktiverats.
- Full projektspecifik modellutvärdering och eventuella andra testkommandon än `unittest`.

## Nästa steg

Granska och uppdatera CI/releaseworkflow mot 1.6.33, fastställ runtime/Engine-resurser för statistikskripten och genomför värdtester innan release. Bevara äldre bygghjälpmedel tills funktionell ersättning verifierats.

## Nästa steg genomfört: CI/release-anpassning

- `.github/workflows/ci.yml` och `release.yml` använder nu den kanoniska motorn 1.6.33 via versionslåst GitHub Release-arkiv och SHA-256-kontroll.
- CI och release bygger projektarkivet samt fem aktiva runtime-distributioner (Chat, Plugin, Claude Projects, Claude Skills, OpenCode); historiska `custom-gpt` är inte längre ett buildmål.
- Statistikspecifika Plugin-resurser kontrolleras i byggd ZIP. GitHub-hostad Actions-körning är ännu inte genomförd.
- Beroende: den publicerade v1.6.33-motorfilens SHA-256 måste överensstämma med bifogat arkiv. Om releasefilen skiljer sig avbryts CI säkert.
- Riktiga runtime-/live-API-tester kvarstår; paketvalidering visar inte funktionell paritet.

## Steg 3: Projektspecifik Engine

En separat statistik-Engine har aktiverats med explicita skript, källregister och körbart offline-självtest. Se `docs/engine-assessment.md`. Extern körning i Plugin-host kvarstår som ej verifierad.
