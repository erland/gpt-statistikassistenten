# CI och releaseautomation

## CI

Workflow: `.github/workflows/ci.yml`

Körs vid push, pull request och manuell dispatch. Kedjan:

1. installerar Python-beroenden,
2. kör projektlint,
3. validerar modellrobusthet,
4. kör regressionstester,
5. kör final project hygiene före build,
6. bygger `project`, `chat`, `custom-gpt` och `opencode` med version `0.0.0-ci`,
7. validerar distributionerna,
8. verifierar att Custom GPT-paketet innehåller alla tre OpenAPI Actions.

## GitHub Release

Workflow: `.github/workflows/release.yml`

Triggas av en publicerad GitHub Release. Versionsnumret härleds enbart från `github.event.release.tag_name`. Giltiga exempel är `v1.0.0` och `v1.0.0-rc1`.

Releasekedjan kör samma gates som CI och bygger sedan samtliga aktiva distributioner med versionsnumret från taggen. Slutligen laddas följande upp till releasen:

- projekt-ZIP,
- ChatGPT Chat-ZIP,
- ChatGPT Custom-ZIP,
- OpenCode-ZIP,
- `SHA256SUMS.txt`,
- `DELIVERY-MANIFEST.json`.

## Reproducerbarhet

GPT Byggaren 1.5.0:s nödvändiga bygg- och valideringsverktyg är vendorerade under `tools/gpt_builder/`. Projektet behöver därför inte hämta en separat GPT Byggaren-repository i CI. ZIP-byggaren använder stabil filordning och fast ZIP-timestamp.

Custom GPT:s Action-scheman är canonical under `runtime-assets/custom-gpt/actions/` och kopieras av byggverktyget till `builder/actions/`.
