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

## Nästa rekommenderade steg

Validera 25B. Efter merge bör steg 25C implementera en planner som producerar v2-planer och beslutar mellan direktläge och användargranskning.
