# Statistikassistenten

Statistikassistenten är ett GPT-projekt för verifierbara frågor mot officiell svensk, europeisk och global statistik.

## Första datakällor

- SCB Statistikdatabasen / PxWeb
- Eurostat
- Eurostat Comext
- Brå: anmälda/handlagda brott, misstänkta personer, handlagda brottsmisstankar och lagförda
- Kolada API v3
- Socialstyrelsens Statistikdatabas
- Folkhälsomyndighetens Folkhälsodata
- Arbetsförmedlingen JobSearch
- Sveriges Riksbank SWEA
- Energimyndighetens statistikdatabas
- Försäkringskassans öppna statistik
- Jordbruksverkets statistikdatabas
- Skolverkets öppna API:er
- SMHI Open Data MetObs
- World Bank Indicators
- OECD Data Explorer
- WHO World Health Data Hub
- BIS Data Portal
- ECB Data Portal
- EUDA/SCORE wastewater analysis
- Tullverkets beslagsstatistik
- Statskontorets öppna data: budgetutfall och myndighetsförteckning
- Svenska kraftnät Mimer: fysisk elproduktion och elförbrukning

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
- `knowledge/source-registry.yaml` – maskinläsbar katalog över källornas verkliga och integrerade kapacitet
- `schemas/source-query-plan-v2.schema.json` – nästa generations planmodell för informationsbehov, källroller och extern fallback
- `scripts/source_planner_v2.py` – deterministisk validator/finalizer för source registry och adaptivt direct/review-läge

## Distributioner

Aktiva mål är ChatGPT Chat, ChatGPT Custom och OpenCode. Alla tre byggs från samma canonical kontrakt via den vendorerade GPT Byggaren 1.5.0-toolchainen.
## Implementerade kärnfunktioner

- SCB PxWebApi v2: tabellsökning, metadata-gate och verifierad uttagsplan, inklusive svensk handel, e-handel och hushållskonsumtion.
- Eurostat SDMX 3.0: dataflow-katalog, strukturmetadata och verifierade komponentfilter.
- Eurostat Comext: verifierad handelsplan för rapportör, partner, flöde, produkt, period och indikator.
- Brå: produktbaserad adapter/fallback för anmälda/handlagda brott, misstänkta personer, handlagda brottsmisstankar och personer lagförda för brott.
- Kolada: kommun-/regionnyckeltal med metadata och källproveniens.
- Socialstyrelsen: ämnes-/dimensionsstyrda uttag från Statistikdatabasen.
- Folkhälsodata: PxWeb-baserade folkhälsoindikatorer.
- Arbetsförmedlingen: platsannonsbaserad efterfrågan via JobSearch.
- Riksbanken: räntor och växelkurser via SWEA.
- Energimyndigheten: energistatistik via PxWeb.
- Försäkringskassan: socialförsäkringsstatistik via metadata och öppna distributioner.
- Jordbruksverket: jordbruks- och livsmedelsstatistik via PxWeb.
- Skolverket: skolenheter, utbildningar och utbildningsstatistik via öppna API:er.
- SMHI: meteorologiska observationer via MetObs.
- World Bank: globala utvecklings- och makroindikatorer.
- OECD: harmoniserad statistik för OECD-länder.
- WHO: global hälsostatistik via World Health Data Hub.
- BIS: internationell bank-, kredit-, bostadspris- och finansstatistik.
- ECB: euroområdets monetära och finansiella statistik.
- EUDA/SCORE: öppna avloppsmätningar av narkotikarester per europeisk mätort.
- Tullverket: narkotika- och andra beslagsdata via officiell statistik och CSV-export.
- Statskontoret: månads-/årsutfall för statens budget samt myndighetsförteckning via officiella öppna CSV/Excel-distributioner.
- Svenska kraftnät: fysisk elproduktion och elförbrukning via Mimer API; SCB används för kundpris/elavtal.
- Källval/frågeplanering för enkla och kombinerade statistikfrågor.
- Deterministiska beräkningar för förändring, andel, index och per-capita.
- Säkerhets- och kvalitetsgates som blockerar ofullständig provenance, felaktiga maskerade värden, otillräckligt verifierade beräkningar och obelagda kausala slutsatser.


## CI och release

- `.github/workflows/ci.yml` kör lint, robusthetskontroll, regressionstester, final hygiene, bygger projekt + Chat + Custom GPT + OpenCode och validerar distributionerna.
- `.github/workflows/release.yml` triggas när en GitHub Release publiceras. Taggar som `v1.0.0` eller `v1.0.0-rc1` styr versionsnumret i artefakterna.
- Release-workflow bifogar alla ZIP-filer, `SHA256SUMS.txt` och `DELIVERY-MANIFEST.json` till releasen.
- Custom GPT:s OpenAPI Actions ligger canonical i `runtime-assets/custom-gpt/actions/` och följer därför med deterministiskt i varje releasebygge.
- Build-toolchainen från GPT Byggaren 1.5.0 är vendorerad under `tools/gpt_builder/` så CI inte är beroende av en separat lokal GPT Byggaren-installation.
