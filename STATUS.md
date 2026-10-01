# Status

## Lägesbild

Steg 25A–25C är genomförda. Pågående steg 25D gör extern fallback körbar när ingen integrerad källa täcker ett informationsbehov.

## Implementerat i 25D

- Nytt schema `schemas/external-source-assessment.schema.json`.
- Ny `scripts/external_source_validator.py` med:
  - sökordning för externa källor,
  - tier B/C/D-validering,
  - krav på definition, population, geografi, period, enhet och status/revision,
  - krav på HTTPS och evidens,
  - obligatorisk disclosure.
- Tier B kräver officiell primärkälla eller officiell internationell organisation.
- Tier C tillåts för trovärdig forskning/sekundär källa när officiell källa inte räcker.
- Tier D blockeras.
- Canonical instruktion kräver användargranskning innan extern sökning/exekvering.
- Extern sökning ska leta efter dataset/källa, inte efter ett färdigformulerat svar.
- Provenance har frivill quality_assurance-struktur för source tier, integrationsstatus och verifieringsstatus.
- Quality gate blockerar externa resultat som saknar verifiering eller disclosure.
- External source validator är registrerad som tool och OpenCode-wrapper.

## Nästa rekommenderade steg

Kör full CI. Efter grön validering kan steg 25D markeras klart och PR:n granskas för merge.
