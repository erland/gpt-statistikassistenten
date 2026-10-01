# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Pågående steg 25A analyserar hur Statistikassistenten ska skala till många källor utan att källvalet blir ett växande nät av nyckelord och parvisa specialregler.

## Pågående källinventering

- Samtliga 23 integrerade källor finns i ett maskinläsbart source registry.
- Registret skiljer uttryckligen mellan källans officiella katalog och vad nuvarande adapter kan hämta säkert.
- Källorna klassificeras efter producentroll, geografi, frekvens, primär-/sekundär användning och begränsningar.
- Aggregatorer ska bevara ursprunglig statistikproducent i proveniensen.
- Primärkälla definieras per efterfrågat mått, inte som en global källranking.
- Extern fallback definieras för fall där ingen integrerad källa täcker ett nödvändigt mått.
- Externa officiella källor får användas efter metadata-/metodkontroll men ska tydligt märkas som ännu inte kvalitetssäkrade av Statistikassistenten.
- Ingen runtime- eller planner-logik ändras i steg 25A.

## Artefakter

- `docs/source-capability-analysis.md`
- `knowledge/source-registry.yaml`
- `schemas/source-registry.schema.json`
- `tests/test_source_registry.py`

## Nästa rekommenderade steg

Validera 25A. Efter merge bör steg 25B definiera en ny fråge-/källplanmodell baserad på informationsbehov och källroller innan runtime-beteendet ändras.
