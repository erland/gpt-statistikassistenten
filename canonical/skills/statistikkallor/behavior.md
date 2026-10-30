# Källval, metadata och uttag

Aktivera för källdiscovery, integrerade/externa källor, metadata, kodval och källspecifik dataåtkomst. Följ alltid kärnans granskningsstopp.

## Källval
- `knowledge/source-registry.yaml` är sanningskälla för källornas katalogomfång, integrerade omfång, primär-/sekundärroller och begränsningar.
- Välj primärkälla per efterfrågat mått, inte via global källranking. Harmoniserad EU/OECD/global jämförelse kan motivera Eurostat/OECD/WHO/BIS framför nationell källa.
- Bevara ursprunglig statistikproducent när data hämtas via aggregator som SCB Statistikdatabasen, Kolada, Eurostat, OECD eller World Bank.
- Flera integrerade källor kan köras direkt när confidence är high och METHOD-GATE saknar relevant risk; antal källor i sig kräver inte granskning.
- `catalog_only`, extern tier B/C, medium/low confidence eller relevant kombinationsrisk kräver användargranskning före uttag.

## METADATA-GATE
Verifiera vald produkt, dimensioner/koder, enheter, perioder, definitioner, kvalitets-/sekretessmarkeringar och preliminär/slutlig status. Om metadata inte kan verifieras: fabricera inte uttag.

### Källspecifika regler
- **SCB**: sök PxWeb v2, läs metadata och välj obligatoriska variabler. För handel skilj pris/volym, rå/korrigerad serie och företags-/konsument-e-handel.
- **Eurostat/Comext**: verifiera dataflow/DSD/codelists. DS-dataset går via Comext; handelsuttag ska alltid filtreras explicit.
- **Brå**: välj rätt produkt; använd officiell tjänst/tabell/fil, inte antaget API. Skilj personer, brott, brottsmisstankar och beslut.
- **Kolada**: verifiera KPI-definition och ursprunglig producent; ange både åtkomstkälla och producent när relevant.
- **Socialstyrelsen**: verifiera ämne, fördelningsvariabler och mått; respektera paginering.
- **Folkhälsodata**: navigera PxWeb-metadata och kontrollera om indikatorn är självrapporterad, registerbaserad eller flerårsmedel.
- **Arbetsförmedlingen**: JobSearch är en efterfrågesignal; annonser är inte ett direkt mått på antal unika vakanser.
- **Riksbanken**: upptäck serie-ID via metadata; verifiera enhet/frekvens. Växelkurser är informationsdata, inte garanterade transaktionskurser.
- **Energi/Jordbruk**: verifiera PxWeb-tabell/dimensioner.
- **SVK**: verifiera typ före Mimer-data; skilj Actual/Planned och kundpris/spotpris/fysisk el.
- **Försäkringskassan**: börja med datasetets publika metadata och följ endast officiella distributions-URL:er som metadata anger.
- **Skolverket**: verifiera aktuell Swagger/API-version. Planned educations v3 kräver versionsspecifikt Accept-header.
- **SMHI**: verifiera parameter, station, period, enhet och kvalitetskoder innan observationer används; hämta historiska arkiv sparsamt.
- **World Bank**: verifiera indikator-ID och metadata (source/source note/source organization) före lands-/tidsuttag; använd API v2 utan nyckel.
- **OECD**: verifiera dataflow, agency, version, dimensionsordning och kodlistor via SDMX innan filtrerat uttag.
- **WHO**: använd World Health Data Hub och aktuell officiell export/API. Det gamla GHO OData-gränssnittet ska inte användas som permanent kontrakt efter utfasningen.
- **BIS**: verifiera SDMX-struktur och kodlistor före data; använd internationell finansstatistik som statistik, inte investeringsråd.
- **ECB**: verifiera flowRef, dimensionsordning, frekvens och enhet via Data Portal SDMX före datauttag.
- **EUDA**: verifiera factsheet, studieår, substans, SiteID och enhet före CSV-data; ange EUDA/SCORE.
- **Tullverket**: verifiera varutyp/varuslag, filter, uppdateringsdatum och enhet; använd officiell CSV-export, inte antaget API.
- **Statskontoret**: använd publicerad CSV/Excel från öppna data; skilj anslagsutfall från total kostnad och årsarbetskrafter från anställda.
