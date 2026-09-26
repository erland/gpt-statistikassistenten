# Statistikassistenten

Statistikassistenten är ett GPT-projekt för verifierbara frågor mot officiell svensk och europeisk statistik.

## Första datakällor

- SCB Statistikdatabasen / PxWeb
- Eurostat
- Eurostat Comext
- Brå, initialt statistik över anmälda brott

## Viktig princip

Assistenten verifierar metadata före datauttag och skiljer alltid på hämtade observationer, egna beräkningar och analys.

## Projektstruktur

- `gpt-project.yaml` – canonical projektkonfiguration och kontrakt
- `project-status.yaml` – auktoritativ projektstatus
- `assistant/instructions.md` – canonical beteende
- `docs/development-plan.md` – utvecklingsplan
- `PROJECT.md` – målbild och arkitektur
- `STATUS.md` – läsbar status
- `schemas/` – kontraktsscheman

## Distributioner

Aktiva mål är ChatGPT Chat, ChatGPT Custom och OpenCode. Alla tre byggs från samma canonical kontrakt via den vendorerade GPT Byggaren 1.5.0-toolchainen.
## Implementerade kärnfunktioner

- SCB PxWebApi v2: tabellsökning, metadata-gate och verifierad uttagsplan.
- Eurostat SDMX 3.0: dataflow-katalog, strukturmetadata och verifierade komponentfilter.
- Eurostat Comext: verifierad handelsplan för rapportör, partner, flöde, produkt, period och indikator.
- Brå: verifierad adapter/fallback för statistik över anmälda brott.
- Källval/frågeplanering för enkla och kombinerade statistikfrågor.
- Deterministiska beräkningar för förändring, andel, index och per-capita.
- Säkerhets- och kvalitetsgates som blockerar ofullständig provenance, felaktiga maskerade värden, otillräckligt verifierade beräkningar och obelagda kausala slutsatser.


## CI och release

- `.github/workflows/ci.yml` kör lint, robusthetskontroll, 58 regressionstester, final hygiene, bygger projekt + Chat + Custom GPT + OpenCode och validerar distributionerna.
- `.github/workflows/release.yml` triggas när en GitHub Release publiceras. Taggar som `v1.0.0` eller `v1.0.0-rc1` styr versionsnumret i artefakterna.
- Release-workflow bifogar alla ZIP-filer, `SHA256SUMS.txt` och `DELIVERY-MANIFEST.json` till releasen.
- Custom GPT:s tre OpenAPI Actions ligger canonical i `runtime-assets/custom-gpt/actions/` och följer därför med deterministiskt i varje releasebygge.
- Build-toolchainen från GPT Byggaren 1.5.0 är vendorerad under `tools/gpt_builder/` så CI inte är beroende av en separat lokal GPT Byggaren-installation.
