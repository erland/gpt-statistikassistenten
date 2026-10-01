# Status

## Lägesbild

Tidigare källutbyggnader och steg 25A är genomförda. Pågående steg 25B definierar nästa generations fråge- och källplanmodell utan att ändra runtime-beteendet.

## Pågående planmodell v2

- Frågor modelleras som ett eller flera informationsbehov.
- Varje informationsbehov beskriver mått, begrepp, population, geografi, period/frekvens, nedbrytningar och jämförelseläge.
- Källor får rollerna primary, supporting, alternative eller excluded per informationsbehov.
- Source tier och integrationsstatus följer source registry.
- Kombination beskriver join-dimensioner, transformationer och metodrisker.
- Direktläge och granskningsläge är explicit modellerade.
- Extern fallback har eget planobjekt och kräver disclosure.
- Befintlig source planner och v1-schema lämnas orörda i steg 25B.

## Artefakter

- `schemas/source-query-plan-v2.schema.json`
- `docs/source-query-plan-v2-design.md`
- `docs/source-query-plan-v2-examples.md`
- `tests/test_source_query_plan_v2.py`

## Validering

- Source Query Plan v2-schema och exempel valideras av regressionstester.
- Befintlig v1-planner och dess tester är oförändrade.
- Projektlint: PASS.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #12. Därefter bör steg 25C implementera planner v2 och det adaptiva arbetsflödet.
