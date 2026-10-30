# Status

## Lägesbild

Den aktuella utvecklingsomgången är avslutad och projektet är i maintenance-läge.

## Genomfört

- Source registry för samtliga integrerade källor.
- Semantisk fråge- och källplanering.
- Adaptivt direct/review-arbetsflöde.
- Källroller per informationsbehov: primary, supporting, alternative och excluded.
- Deterministiska guardrails för källkombinationer och integrationsstatus.
- Extern fallback med tier B/C/D-bedömning.
- Provenance och disclosure för externa källor.
- Quality gates som blockerar otillräckligt verifierade externa källor.
- Befintliga källadaptrar, distributioner, CI och releaseautomation kvarstår validerade.
- OpenAI Plugin är tillagd som skills-first peer distribution med `equivalent_runtime_dependent` parity; web/structured data är kärnkrav och code execution är rekommenderad med degrade-fallback.

## Validering

Senaste fulla validering för funktionerna i utvecklingsomgången passerade med 147 regressionstester, projektlint utan fel/varningar, modellrobusthet PASS, final hygiene PASS och distributionsvalidering PASS.

## Maintenance-princip

Nya förändringar ska i första hand drivas av faktisk användning. Särskilt relevanta signaler är:

- återkommande frågor där en källa bara är `catalog_only`,
- återkommande extern fallback mot samma officiella källa,
- källkombinationer som ofta kräver användargranskning,
- upptäckta metod-/proveniensproblem,
- nya tydliga användningsfall som motiverar ytterligare adapter eller källstöd.

Det finns inget planerat obligatoriskt nästa utvecklingssteg.

## Migration mot GPT Byggaren 1.6.33 (2026-10-30)

- Projektets källfiler och statistikbeteende har bevarats i en säker migrationskopia.
- Kanonisk motor 1.6.33: integritet/självtest PASS; installation PASS.
- Distributioner: Chat, Plugin, Claude Projects, Claude Skills och OpenCode byggda; distributionsvalidering PASS.
- Projektets `unittest`-svit: 99 tester PASS i denna körning (tidigare uppgift om 147 regressionstester avser en annan körning).
- Migreringen omfattar inte funktionell kontroll i verkliga runtimevärdar, live-API-anrop eller CI/release.
- Projektspecifika Python-skript har bevarats. Eventuell separat statistik-Engine till Plugin kräver resursinventering och ett faktiskt självtest före aktivering.
- Gamla byggverktyg har inte raderats innan CI- och beteendeparitet fastställts.

Se `docs/migration-1.6.33.md` för öppna frågor och verifieringsomfattning.

## CI/release-migrering (2026-10-30)

- Workflowkällor uppdaterade för versionslåst motor 1.6.33 och sex artefakter (projekt + fem distributioner).
- Historisk Custom GPT-projektion behålls som källreferens men byggs inte.
- GitHub Actions behöver fortfarande köras på GitHub innan merge/release rekommenderas.
- Nästa steg: kontrollera Plugin-statistikmotorns exekverings- och resursbehov och funktionstesta runtime-miljöerna.

### Migreringssteg 3

Separat Statistikassistenten Engine definierad och paketeringsbar; se `docs/engine-assessment.md`. Runtimeparitet och GitHub Actions-körning återstår att verifiera.

### Migreringssteg 4 – Plugin/Engine-överlämning
Offlineintegritet, resursparitet mellan Plugin och Engine och uppackat självtest verifieras nu av `scripts/verify_plugin_engine_handoff.py`. CI/release kör denna kontroll efter distributionsbygget. Se `docs/plugin-engine-handoff.md`. Exekvering i faktisk Plugin-värdmiljö och live-API är fortfarande **ej verifierade**. Nästa steg: GitHub Actions/release i repositoryt och funktionella hosttester.
