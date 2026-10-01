# Källkapacitetsanalys – steg 25A

## Syfte

Statistikassistenten har nu tillräckligt många källor för att källval inte längre bör baseras främst på nyckelord, statiska vikter och parvisa konfliktregler. Detta steg kartlägger vad varje officiell källa faktiskt innehåller och skiljer det från vad den nuvarande integrationen kan hämta säkert.

Den maskinläsbara modellen finns i `knowledge/source-registry.yaml`. Detta steg ändrar inte runtime-beteendet.

## Centrala slutsatser

### 1. Källans katalog och vår integration är två olika saker

Flera källor är betydligt bredare än den adapter som finns idag.

| Källa | Officiell katalog i stort | Nuvarande integration |
|---|---|---|
| SCB | Mycket bred svensk samhällsstatistik över drygt 20 ämnesområden | Generisk PxWeb v2, med särskilda routingregler för bl.a. handel, statlig personal och elpris |
| Eurostat | Ekonomi, befolkning, sociala frågor, företag, jordbruk, transport, miljö, energi, digitalisering m.m. | Generisk SDMX |
| Comext | Detaljerad varuhandel, partner, produkt, kvantitet/värde, företagskarakteristika | Detaljerad varuhandel |
| Brå | Nio officiella kriminalstatistikprodukter plus trygghets-/surveyprodukter och annan rättsstatistik | Fem kriminalstatistikprodukter |
| Kolada | Kommun-/regionnyckeltal inom många verksamheter, resurser, volymer och resultat | KPI-metadata och värden |
| Socialstyrelsen | Hälsa, vård, personal, dödsorsaker och socialtjänst | Generisk statistikdatabas |
| Folkhälsodata | Hälsoutfall och bestämningsfaktorer inom flera temaområden | Generisk PxWeb |
| Arbetsförmedlingen | Aktuella och historiska platsannonser samt relaterad öppen data | JobSearch |
| Riksbanken | Räntor, växelkurser, SWESTR, betalningar och statistikansvar för delar av finansmarknad/betalningsbalans | SWEA räntor och växelkurser |
| Energimyndigheten | Tillförsel, användning, energibalanser, priser, infrastruktur och prognoser | Generisk PxWeb |
| Försäkringskassan | Hela socialförsäkringsområdet samt tandvårdsstöd, analyser och prognoser | Metadata/distributionsvalidering |
| Jordbruksverket | Jordbruk, trädgård, vattenbruk och långa tidsserier | Generisk PxWeb |
| Skolverket | Skolenheter, elever, personal, resultat, kostnader och flera skolformer | Främst planned educations/utvalda API-vägar |
| SMHI | Meteorologi, hydrologi, oceanografi, klimat, modell-/radardata | MetObs meteorologi |
| World Bank | Nära 16 000 indikatorserier från över 45 databaser | Indicators API v2 |
| OECD | Organisationens hela statistiklager inom ekonomi, samhälle, miljö m.m. | Data Explorer SDMX |
| WHO | Global hälsa från mortalitet och sjukdomsbörda till riskfaktorer, vårdsystem och UHC | Aktuell Data Hub/export-fallback |
| BIS | Bank, kredit, skulder, likviditet, derivat, fastighetspriser, KPI, växelkurser, policy rates, betalningar | SDMX |
| ECB | Euroområdets penning-, bank-, marknads-, betalnings- och valutastatistik | Data Portal SDMX |
| EUDA | Prevalens, högriskanvändning, dödsfall, behandling, beslag, pris/renhet, brott, wastewater m.m. | SCORE wastewater |
| Tullverket | Beslag av flera typer av restriktionsvaror | Beslagsstatistik via CSV |
| Statskontoret | Budgetutfall, tidsserier, realekonomisk fördelning, myndighetsförteckning | Månads-/årsutfall och myndighetsförteckning |
| Svenska kraftnät | Operativ fysisk produktion/förbrukning efter typ och område | Mimer produktion/förbrukning |

Konsekvensen är att planner-logiken framöver måste kunna säga både:

1. **Källan har data inom området**, och
2. **vår nuvarande integration stöder just det uttaget**.

Om punkt 1 är sann men punkt 2 falsk bör källan kunna användas som en officiell extern fallback utan att låtsas vara fullt integrerad.

### 2. "Primär källa" måste definieras per mått

Ingen källa är generellt mest central. Primärkälla bestäms av det efterfrågade måttet och dess önskade harmonisering/granularitet.

Exempel:

- svensk befolkning → SCB,
- svensk registrerad brottslighet → Brå,
- svensk socialförsäkring → Försäkringskassan,
- statens budgetutfall → Statskontoret,
- timvis fysisk elförbrukning per elområde → Svenska kraftnät,
- detaljerad EU-varuhandel → Comext,
- harmoniserad EU-arbetsmarknadsjämförelse → Eurostat,
- OECD-specifik jämförelse → OECD,
- global hälsa → WHO,
- internationell bankstatistik → BIS.

Det bör därför inte finnas en global källranking. Registret ska i stället matcha frågans delmått mot källans `primary_for`, geografi, granularitet och metodprofil.

### 3. Aggregatorer kräver producentproveniens

SCB Statistikdatabasen, Kolada, Eurostat, OECD och World Bank kan innehålla data vars ursprungliga producent är en annan organisation.

Planner och PROVENANCE-GATE bör därför skilja på:

- **åtkomstkälla** – var Statistikassistenten hämtade datat,
- **statistikproducent** – vem som producerade/ansvarar för måttet.

När samma mått finns hos både en aggregator och den ursprungliga producenten bör den ursprungliga producenten normalt prioriteras om den har jämförbar tillgänglighet och den efterfrågade harmoniseringen inte kräver aggregatorn.

### 4. Bred harmonisering kan vara viktigare än nationell förstakälla

Det finns ett viktigt undantag från "ursprunglig producent först": användaren kan efterfråga harmoniserbarhet.

Exempel:

- Sverige jämfört med EU-länder → Eurostat kan vara bättre än separata nationella källor.
- Sverige jämfört med OECD → OECD.
- Global hälsa → WHO.
- Internationell kredit och skuldtjänst → BIS.

Planner behöver därför identifiera om frågans syfte är ett nationellt mått eller en harmoniserad jämförelse.

## Föreslagen frågemodell inför steg 25B

Källval bör börja med en semantisk uppdelning av frågan:

- `measure`: vilket mått behövs?
- `concept`: vilken företeelse beskriver måttet?
- `population`: vilken population/observationsenhet?
- `geography`: vilken geografisk nivå?
- `period` och `frequency`: tid och önskad upplösning?
- `breakdowns`: kön, ålder, produkt, brottstyp, sektor etc.
- `comparison_mode`: nationellt, trend, kommunjämförelse, EU/OECD/global harmonisering?
- `derived_measure`: krävs nämnare, join eller beräkning?

Först därefter bör source registry användas för att klassificera källor.

## Föreslagna källroller

Varje informationsbehov bör kunna få:

- **primary** – förstahandskällan för måttet,
- **supporting** – behövs för ett annat mått, en nämnare, join-dimension eller kontext,
- **alternative** – kan svara men är mindre lämplig för den efterfrågade granulariteten/harmoniseringen,
- **excluded** – verkar relevant men mäter något annat eller bryter mot metodkraven.

En källa bör inte läggas till en plan enbart för att den innehåller ord som liknar frågan.

## Föreslagen planeringslogik

### Direktläge

Direkt datauttag kan göras när:

- ett enda informationsbehov finns,
- en tydlig tier-A-källa har integrerad kapacitet,
- confidence är hög,
- ingen metodkänslig kombination krävs.

### Granskningsläge

Käll- och metodplan bör visas före datauttag när:

- flera källor behövs,
- data måste joinas,
- en nämnare kommer från annan källa,
- tidsfrekvenser måste aggregeras,
- observationstyper riskerar att blandas,
- flera primärkällor är plausibla,
- harmoniserad internationell statistik konkurrerar med nationell förstakälla,
- extern, ännu ej kvalitetssäkrad källa behövs.

Planen bör visa vad varje källa ska bidra med, varför den valts, alternativ som valts bort och riskerna i kombinationen.

## Extern fallback när integrerade källor saknar data

Det är önskvärt att Statistikassistenten kan söka vidare. Fallbacken bör däremot vara dataset-orienterad, inte "sök efter ett svar".

### Källnivåer

**Tier A – integrerad och kvalitetssäkrad**

Normal användning. Källspecifik adapter/guardrails finns.

**Tier B – officiell primärkälla som inte är integrerad**

Tillåten efter verifiering av dataset, metadata och åtkomstmetod. Exempel kan vara en annan svensk myndighets officiella statistik eller en ny produkt inom en redan känd organisations katalog.

**Tier C – trovärdig sekundär-/forskningskälla**

Används endast när A/B inte täcker behovet och med tydligare reservation.

**Tier D – oklar eller icke verifierbar källa**

Får inte bära ett statistiskt resultat.

### Fallbackflöde

1. Identifiera exakt vilket delmått tier-A-källorna inte täcker.
2. Kontrollera först om en redan känd organisation har måttet utanför vår integrerade adapter.
3. Sök därefter efter officiell statistikproducent, öppna data eller dokumenterat API.
4. Verifiera producent, dataset, definition, population, geografi, period, enhet och status.
5. Föredra API/CSV/Excel eller annan officiell maskinläsbar distribution.
6. Undvik odokumenterade interna endpoints och generell webbskrapning.
7. Kör samma METADATA-, METHOD- och PROVENANCE-GATE som vanligt.
8. Märk källan som extern och ännu inte kvalitetssäkrad i Statistikassistentens registry.

### Obligatorisk transparens i svaret

När en extern källa används ska användaren kunna se:

- att ingen integrerad kvalitetssäkrad källa täckte måttet,
- vilken extern organisation/dataset som användes,
- varför källan bedömdes lämplig,
- vilka metadata som verifierades,
- att den tillfälliga verifieringen inte innebär att källan nu är permanent kvalitetssäkrad.

En lämplig standardformulering är:

> Ingen av Statistikassistentens integrerade och kvalitetssäkrade källor täckte detta mått. Jag använder därför [organisation/dataset], som är en officiell men ännu inte integrerad källa. Definition, period, geografi och enhet har verifierats för detta uttag.

## Viktiga luckor som inventeringen visar

Inventeringen visar flera ställen där källans officiella katalog är bredare än vår integration. Det betyder inte automatiskt att fler adaptrar ska byggas, men planner ska känna till dem.

Högst potentiell nytta:

1. **Brå** – kriminalvård, återfall, dödligt våld och surveybaserade trygghetsmått ligger utanför nuvarande adapter.
2. **EUDA** – nuvarande adapter använder bara wastewater trots bred europeisk drogstatistik.
3. **Skolverket** – full statistik om elever, personal, resultat och kostnader är bredare än current API-integration.
4. **SMHI** – hydrologi och oceanografi ligger utanför MetObs.
5. **Riksbanken** – bredare statistikansvar finns, men delar publiceras via SCB och bör inte felaktigt routas till SWEA.
6. **Statskontoret** – realekonomisk budgetfördelning finns men är inte integrerad.
7. **World Bank/WHO/OECD/BIS/ECB** – katalogerna är breda; specialistkällor ska prioriteras semantiskt för sina områden.

Dessa luckor bör betraktas som registry-information först. En ny adapter bör byggas först när verkliga användningsfall motiverar det.

## Källöverlapp som steg 25B måste hantera

Minst följande överlapp bör modelleras som generella prioriteringsprinciper i stället för växande parvisa specialregler:

- SCB ↔ domänmyndigheter för svensk officiell statistik,
- SCB ↔ Kolada för rå statistik kontra färdigdefinierade kommunnyckeltal,
- SCB ↔ Statskontoret för statlig personal kontra budget/årsarbetskrafter,
- SCB ↔ Energimyndigheten ↔ SVK för elpris, energibalans och operativ fysisk el,
- Eurostat ↔ nationella källor för harmonisering kontra nationell detalj,
- Eurostat ↔ Comext för generell EU-statistik kontra detaljerad varuhandel,
- World Bank ↔ WHO/OECD/BIS/Eurostat för bred global aggregator kontra specialistkälla,
- Riksbanken ↔ ECB/BIS för svensk kontra euroområdes-/internationell finansdata,
- Brå ↔ EUDA/Tullverket/Socialstyrelsen för olika narkotikarelaterade observationstyper.

## Underlag och verifiering

Inventeringen bygger på respektive organisations officiella katalog, API-dokumentation eller statistiköversikt. Exempel på centrala ingångar:

- SCB: https://www.scb.se/hitta-statistik/
- Eurostat: https://ec.europa.eu/eurostat/data/statistical-themes
- Comext: https://ec.europa.eu/eurostat/web/international-trade-in-goods
- Brå: https://bra.se/
- Kolada: https://kolada.se/om-oss/api/
- Socialstyrelsen: https://www.socialstyrelsen.se/statistik-och-data/statistik/statistikdatabasen/
- Folkhälsodata: https://www.folkhalsomyndigheten.se/statistik-och-data/om-vara-data/statistikdatabaser/folkhalsodata-hitta-och-hamta-statistik/
- Arbetsförmedlingen: https://data.arbetsformedlingen.se/dataset/job-ads/
- Riksbanken: https://www.riksbank.se/en-gb/statistics/
- Energimyndigheten: https://www.energimyndigheten.se/statistik/officiell-energistatistik/
- Försäkringskassan: https://www.forsakringskassan.se/statistik-och-analys
- Jordbruksverket: https://jordbruksverket.se/om-jordbruksverket/jordbruksverkets-officiella-statistik
- Skolverket: https://www.skolverket.se/skolutveckling/statistik
- SMHI: https://www.smhi.se/data/hitta-data-for-en-plats
- World Bank: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- OECD: https://www.oecd.org/en/data/datasets/oecd-DE.html
- WHO: https://data.who.int/about/datadot/
- BIS: https://www.bis.org/statistics
- ECB: https://www.ecb.europa.eu/stats/
- EUDA: https://www.euda.europa.eu/data/stats2026_sq
- Tullverket: https://www.tullverket.se/sv/omoss/beslagsstatistik.4.226de36015804b8cf353949.html
- Statskontoret: https://www.statskontoret.se/analys-och-statistik/oppna-data/
- Svenska kraftnät Mimer: https://mimer.svk.se/swagger/ui/index

## Rekommenderat nästa steg

Efter granskning och merge av 25A bör steg 25B definiera ett nytt schema för fråge- och källplanen. Runtime-logik ska fortfarande inte ändras förrän schemat och regressionsfrågorna är överenskomna.

Det viktigaste i 25B är att gå från `sources: [...]` till en plan byggd kring **informationsbehov och källroller**.
