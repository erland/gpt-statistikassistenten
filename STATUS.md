# Status

## Lägesbild

Steg 25A och 25B är genomförda. Pågående steg 25C implementerar Source Query Plan v2 som faktisk planeringsguardrail på samma PR.

## Implementerat i 25C

- Ny `scripts/source_planner_v2.py`.
- GPT:n gör semantisk nedbrytning av frågan; deterministisk kod validerar planen mot source registry.
- Verktyget exponerar `registry_summary`, `source_capability` och `finalize_plan`.
- `finalize_plan` avgör `direct`, `needs_user_review`, `needs_clarification` eller `blocked`.
- Kända registry-källor får inte felaktigt märkas som externa eller få annan tier.
- Oregistrerade källor får inte hävda tier A.
- Extern primary/supporting-källa kräver explicit external fallback och disclosure.
- Catalog-only, tier B/C, medium/low confidence och relevanta metodrisker leder till användargranskning.
- Flera integrerade källor eller en enkel deterministisk beräkning kräver inte automatiskt granskning om confidence är high och inga relevanta metodrisker finns.
- Canonical instruktion använder source registry som sanningskälla i stället för en duplicerad lång källista.
- V1-plannern behålls som kompatibilitets-/guardrail under övergången.
- OpenCode och tool contract har source-planner-v2 registrerad.

## Tester

Nya runtime-tester täcker bland annat direktläge, metodrisk, säker flerkällskombination, catalog-only, extern fallback, confidence, clarification och felaktig extern tier A.

## Nästa rekommenderade steg

Kör full CI. Efter grön validering kan 25C markeras klar på PR #12. Extern webbsökning/exekvering av fallback hålls separat från denna plannerimplementation.
