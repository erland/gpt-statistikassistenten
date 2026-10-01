# Käll- och metodreferens

## Källval
- **SCB**: svensk officiell statistik och Statistikdatabasen.
- **Eurostat**: harmoniserad EU-statistik.
- **Comext**: detaljerad internationell varuhandel, särskilt reporter × partner × produkt × flöde × tid.
- **Brå**: svensk kriminalstatistik.
- **World Bank**: bred global utvecklings- och makrostatistik.
- **OECD**: harmoniserade jämförelser mellan OECD-länder.
- **WHO**: global hälsostatistik.
- **BIS**: internationell bank-, kredit-, bostadspris- och finansstatistik.
- **ECB**: euroområdets monetära och finansiella statistik.
- **EUDA/SCORE**: narkotikarelaterade europeiska data; första stödda familjen är avloppsmätningar.
- **Tullverket**: svensk beslagsstatistik för restriktionsvaror via officiell sida och CSV-export.

## SCB PxWebApi v2
Bas-URL: `https://statistikdatabasen.scb.se/api/v2`.
Arbetsordning: sök `/tables` → verifiera `/tables/{id}/metadata` → hämta `/tables/{id}/data` med explicit selektion. Komplexa urval bör göras med POST. Max 150 000 dataceller per uttag. Verifiera obligatoriska variabler och värdekoder i metadata.

## Eurostat SDMX 3.0
Bas-URL: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0`.
Dataset kan upptäckas via Eurostats katalog eller dataflows. Hämta dataflow/DSD/codelists före tolkning av koder. Datafrågor kan använda series-key eller komponentfilter. Dataset med `DS-`-prefix hör till Comext.

## Eurostat Comext
Bas-URL: `https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/3.0`.
Verifiera alltid faktisk struktur. Semantiska roller måste kunna mappas till datasetets dimensioner: rapportör, partner, flöde, produkt, tid och indikator. Hämta aldrig ett helt stort Comext-dataset när frågan kan filtreras.

## Brå
Brå saknar i version 1 ett antaget generellt publikt API i assistenten. Använd officiell statistiktjänst eller publicerade tabeller/filer och verifiera produkt, brottstyp, geografi, period, enhet och preliminär/slutlig status. Anmälda brott är inte samma sak som faktisk brottslighet.

## Kombinerade mått
- Per capita: samma geografi och period i täljare och nämnare.
- Procentuell förändring: `(nytt-gammalt)/gammalt*100`; basvärde får inte vara 0.
- Index: vald bas måste vara verifierad och icke-noll.
- Andel: del och total måste ha kompatibla enheter och definitioner.
- Saknade/sekretesskyddade värden får aldrig ersättas med 0.
- Preliminär status ska följa med härledda resultat.

## Proveniens
Ange organisation, dataset/tabell/statistikprodukt, geografi, tid, mått/enhet, metodreservationer och om siffran är direkt hämtad eller beräknad.

## Kolada API v3
Bas-URL: `https://api.kolada.se/v3`. Använd metadata för nyckeltalet före data. Kommunuttag följer mönstret `/data/municipality/{kommunkod}/kpi/{nyckeltal}`. Kolada kräver källangivelse och metadata kan ange en annan ursprunglig statistikproducent; bevara båda nivåerna i proveniensen.

## Socialstyrelsens Statistikdatabas
Bas-URL: `https://sdb.socialstyrelsen.se/api/v1`. Lista ämnen och fördelningsvariabler innan `/resultat` hämtas. Resultat pagineras vid större uttag; standardtaket i dokumentationen är 5 000 poster per sida. Ange Socialstyrelsen och statistikdatabasen som källa.

## Folkhälsodata
Folkhälsomyndighetens Folkhälsodata använder PxWeb API v1. Metadata måste verifiera tabell, dimensioner, geografi, år, mått och särskilda metodegenskaper som självrapportering eller flerårsmedelvärden.

## Arbetsförmedlingen JobSearch
Publikt JobSearch-API för platsannonser. Använd endast som indikator på annonserad efterfrågan efter yrken/kompetenser/geografi. Antal annonser får inte tolkas som arbetslöshet, sysselsättning eller antal unika lediga tjänster utan uttryckligt stöd.

## Sveriges Riksbank SWEA
Bas-URL: `https://api.riksbank.se/swea/v1`. Använd `/Series` eller `/Groups` för att verifiera serie-ID och metadata, därefter `/Observations/...`. Källan ska anges. Växelkurser är indikativa och avsedda för information, inte som garanterade transaktionskurser.


## Energimyndigheten
Statistikdatabasen är PxWeb-baserad och nås via `https://pxexternal.energimyndigheten.se/api/v1/sv/Energimyndighetens_statistikdatabas`. Verifiera tabell, dimensioner och enhet innan POST-uttag. Energimyndigheten kräver källangivelse för publicerad statistik; bearbetade resultat ska beskrivas som bearbetad statistik från myndigheten.

## Försäkringskassan
Öppen officiell statistik publiceras som maskinläsbara distributioner med metadata under `https://www.forsakringskassan.se/api/sprstatistikrapportera/public/v1`. Börja med `/{dataset-id}/meta/json` och följ endast officiella distributionslänkar som metadata anger. Skilj ersättningsmottagare, belopp, nettodagar och sjukfall enligt datasetets definition.

## Jordbruksverket
Statistikdatabasen är PxWeb-baserad. Verifiera tabell, variabler, geografi, period och sekretessmarkeringar före analys. Databasen omfattar bland annat arealer, skörd, djur, ekologisk produktion, jordbruksekonomi, priser och livsmedelskonsumtion.

## Skolverket
Använd öppna REST-API:er för skolenheter, utbildningar och statistik. Planned educations version 3 använder headern `Accept: application/vnd.skolverket.plannededucations.api.v3.hal+json`. Kontrollera aktuell Swagger eftersom versioner kan ändras och skilj registerdata från statistiska mått.

## SMHI Open Data MetObs
Bas för meteorologiska observationer: `https://opendata-download-metobs.smhi.se/api/version/latest`. Verifiera parameter-ID, station-ID, period, enhet och kvalitetsinformation innan data används. Historiska corrected-archive-uttag kan vara stora och ska hämtas sparsamt.


## World Bank Indicators API v2
Bas-URL: `https://api.worldbank.org/v2`. API:t kräver ingen nyckel. Identifiera indikator via `/indicator` eller `/indicator/{id}` och bevara källa, source note och source organization. Hämta sedan uttryckliga landkoder och perioder. För globala jämförelser ska definition och täckning verifieras före analys.

## OECD Data Explorer
Bas-URL: `https://sdmx.oecd.org/public/rest`. Använd SDMX-dataflow och strukturmetadata före data. OECD:s API är avgiftsfritt men har rate limiting; gör därför filtrerade uttag och återanvänd metadata när möjligt.

## WHO World Health Data Hub
Primär ingång: `https://data.who.int`. WHO:s äldre GHO OData-gränssnitt är deprecated/utfasat och ska inte vara canonical endpoint. Identifiera indikator i aktuella WHO-källor och använd aktuell officiell export/API. Bevara osäkerhetsintervall och modellerad/rapporterad status när de finns.

## BIS Data Portal
BIS publicerar statistik och metadata via SDMX REST API v2. Verifiera struktur, agency, resource och key innan datauttag. Relevanta områden är bland annat kredit, internationell bankstatistik, bostadspriser och effektiva växelkurser.

## ECB Data Portal
Bas-URL: `https://data-api.ecb.europa.eu/service`. ECB använder SDMX 2.1 med metadata discovery och data retrieval. Verifiera dataflow/flowRef, key, frekvens och enhet. ECB används för euroområdets monetära och finansiella statistik; Eurostat används fortsatt för bredare samhällsstatistik.


## EUDA/SCORE wastewater analysis
Metadata/factsheet: `https://www.euda.europa.eu/publications/pods/waste-water-analysis_en`. EUDA publicerar återanvändbara CSV-filer och platsmetadata. Den verifierade 2026-distributionen täcker studier 2011–2025. Huvudenheten är populationsnormaliserad restmängd, `mg/1000 population/day`. Kokain mäts via benzoylecgonine och cannabis via THC-COOH. Värdena beskriver drogrestbelastning i avloppsvatten och får inte beskrivas som antal användare eller prevalens. Ange EUDA och SCORE som källa och koppla platsinformation via SiteID.

## Tullverkets beslagsstatistik
Officiell ingång: `https://www.tullverket.se/sv/omoss/beslagsstatistik.4.226de36015804b8cf353949.html`. Statistiken filtreras bland annat efter halvår, varutyp, varuslag, län och plats och kan exporteras till CSV. Verifiera alltid aktuella varutyper i källan; tjänsten omfattar bland annat alkohol, vapen/farliga föremål, dopningspreparat, läkemedel, narkotika, skjutvapen, sprängämnen och tobak. Ett stabilt generellt API är inte dokumenterat, så använd den officiella exportfunktionen i stället för antagna interna endpoints. Bevara enhet per rad (kilo/liter/styck), uppdateringsdatum och eventuella revideringar. Beslag är ett operativt utfall och inte ett direkt mått på konsumtion eller marknadsstorlek.
