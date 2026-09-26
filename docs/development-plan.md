# Statistikassistenten – utvecklingsplan

## Målbild

Statistikassistenten ska låta användaren ställa frågor på naturlig svenska mot officiell statistik och få ett verifierbart svar med tabell, analys, källor och metodnoteringar. Första versionen ska stödja:

- SCB Statistikdatabasen via PxWebApi v2.
- Eurostat och Eurostat Comext för EU- och handelsstatistik.
- Brå:s publicerade statistik via en separat adapter/fallback eftersom ett generellt publikt statistik-API inte kan förutsättas.
- Kombination av källor när det är metodologiskt rimligt, exempelvis brott per 100 000 invånare.
- Export av resultat i Markdown och CSV när data lämpar sig för det.

Grundversionen ska inte kräva att användaren skaffar API-nycklar eller konton.

## Viktiga beteenderegler

1. Assistenten får inte gissa tabell, variabel, geografikod, varukod eller brottskod när metadata kan verifieras.
2. Den ska skilja på källa, observation, beräkning och egen analys.
3. Varje statistiksvar ska ange källa, statistikprodukt/tabell, tidsperiod, geografisk nivå och relevanta definitioner/reservationer.
4. Kombinerade mått ska endast räknas när nämnare och täljare är metodologiskt kompatibla.
5. Vid osäker matchning mellan användarens fråga och tillgänglig statistik ska alternativa tolkningar redovisas i stället för att en kod väljs godtyckligt.
6. Senaste tillgängliga period ska verifieras i källans metadata och aldrig antas utifrån dagens datum.
7. Assistenten ska föredra officiella primärkällor framför sekundära sammanställningar.

## Rekommenderad arkitektur

Flödet ska vara plattformsneutralt:

`fråga → intent/tolkning → källval → metadataupptäckt → verifierat datauttag → normalisering → beräkning/analys → validering → presentation + källor`

Källspecifika adapters döljer skillnader mellan SCB, Eurostat/Comext och Brå. Canonical instruktion beskriver när varje adapter får användas och vilka valideringsgates som gäller.

### Modellrobusthet

Nivå: **guided**.

Motivering: varje fråga kräver flera beroende steg, men normalt inget långlivat persistent state mellan sessioner. Canonical instruktion ska därför innehålla en kort operativ kärna med tydliga gates för metadata, datauttag, beräkning och källredovisning.

## Runtime-bedömning

| Runtime | Bedömning | Default | Kommentar |
|---|---|---:|---|
| ChatGPT Chat | Equivalent | Ja | Web, dataanalys och filhantering räcker för kärnflödet. |
| ChatGPT Custom | Equivalent | Ja | Lämplig för Actions mot nyckelfria API:er och styrd statistikdialog. |
| Claude Projects | Reduced | Nej | Instruktion/knowledge kan porteras men extern verktygsparitet kan inte förutsättas. |
| OpenCode | Equivalent | Ja | Kan använda samma kontrakt och deterministiska adapters/scripts. |
| OpenAI Plugin | Reduced | Nej | Skills passar, men extern HTTP/dataanalys bör inte antas ha full parity i Plugin v1. |

Aktiverade distributionsmål i första versionen: **ChatGPT Chat, ChatGPT Custom och OpenCode**.

## Utvecklingssteg

### Steg 1 – Canonical projektgrund

**Mål:** skapa första projekt-ZIP:en med canonical projektmodell, README, kontrakt och strukturerad status.

**Leverans:**
- `gpt-project.yaml`
- `project-status.yaml`
- `PROJECT.md`
- `STATUS.md`
- `README.md`
- `docs/development-plan.md`
- canonical instruktion med kärnkontrakt och operativt flöde

**Klart när:** projektet kan lintas mot GPT Byggarens grundkrav och nästa steg kan härledas från status.

### Steg 2 – Gemensam statistikmodell och svarskontrakt

**Mål:** definiera källneutral modell för fråga, dimensioner, observationer, metadata, beräkningar och provenance.

**Klart när:** schemas kan representera SCB-, Eurostat- och Brå-data utan källspecifika fält i analyslagret.

### Steg 3 – SCB-adapter

**Mål:** stödja upptäckt av tabeller, metadata och datauttag via PxWebApi v2.

**Klart när:** tester kan lösa representativa frågor om exempelvis befolkning och arbetsmarknad utan hårdkodad tabellgissning.

### Steg 4 – Eurostat-adapter

**Mål:** stödja vanliga Eurostat-dataset via officiella API:er.

**Klart när:** assistenten kan hitta dataset, läsa dimensioner och göra begränsade datauttag med verifierad metadata.

### Steg 5 – Eurostat Comext-adapter

**Mål:** stödja handelsfrågor med rapportör, partner, produktklassificering, flöde, period, värde och kvantitet.

**Klart när:** frågor om svensk import/export kan översättas till verifierade Comext-dimensioner utan att hela stora dataset hämtas.

### Steg 6 – Brå-adapter och fallbackstrategi

**Mål:** stödja utvalda Brå-statistikprodukter med explicit provenance och metodnotering.

**Första omfattning:** statistik över anmälda brott.

**Klart när:** assistenten kan hitta och analysera publicerad Brå-statistik utan att låtsas att ett generellt API finns.

### Steg 7 – Källval och frågeplanerare

**Mål:** välja rätt källa eller kombination av källor från användarens fråga.

**Klart när:** evals täcker enkla frågor, tvetydiga frågor, källkonflikter och kombinationsfall.

### Steg 8 – Beräkningar och kombinerade mått

**Mål:** stödja förändring, andel, indexering, per-capita-mått och jämförelser över tid/geografi.

**Klart när:** deterministiska tester verifierar enheter, periodmatchning och nämnare/täljare.

### Steg 9 – Presentation och export

**Mål:** standardisera kort svar, tabell, trendanalys, metodnotering och källhänvisning samt Markdown/CSV-export.

**Klart när:** samma analys kan presenteras konsekvent oavsett datakälla.

### Steg 10 – Säkerhets- och kvalitetsgates

**Mål:** minska hallucinerade koder, felaktiga jämförelser och feltolkad statistik.

**Klart när:** negativa tester verifierar att assistenten stoppar eller markerar osäkra uttag i stället för att fabricera data.

### Steg 11 – ChatGPT Chat-distribution

**Mål:** paketera en portabel Chat ZIP som kan användas som GPT-kontext i en konversation.

**Klart när:** distributionsvalidering och representativa end-to-end-evals passerar.

### Steg 12 – ChatGPT Custom-distribution

**Mål:** skapa Custom GPT-instruktion, knowledge och Actions/OpenAPI-definitioner där plattformen medger det.

**Klart när:** Actions är begränsade till de API:er som behövs och inga användarhemligheter krävs för grundflödet.

### Steg 13 – OpenCode-distribution

**Mål:** skapa OpenCode-runtime med samma canonical kontrakt och körbara adapterverktyg.

**Klart när:** kärnscenarier ger samma sakresultat och provenance som övriga aktiverade runtimes.

### Steg 14 – Runtime parity, project hygiene och release readiness

**Mål:** kontrollera att aktiverade runtimes har dokumenterade skillnader men samma kärnbeteende.

**Klart när:** lint, tester, distribution validation, paritybedömning, final hygiene och release-readiness passerar utan blockerare.

### Steg 15 – Releaseautomation

**Mål:** lägga till GitHub Actions CI och release-byggning som standard.

**Klart när:** release-taggen styr versionen och en release kan bygga samtliga aktiverade distributionsartefakter deterministiskt.

## Avgränsningar för version 1

- Ingen UN Comtrade-integration i första versionen; kan läggas till senare som optional adapter.
- Ingen generell skrapning av godtyckliga webbplatser.
- Ingen persistent användarprofil eller långtidslagring av tidigare statistikfrågor.
- Ingen automatisk kausal tolkning av korrelationer.
- Ingen bildgenerering; diagram skapas endast som datavisualisering när runtime stödjer det.

## Kandidater för senare versioner

- UN Comtrade.
- Kolada.
- Riksbanken.
- Arbetsförmedlingen.
- Socialstyrelsen och Folkhälsomyndigheten.
- Energimyndigheten och Naturvårdsverket.
- Trafikanalys.
- Sparade analysrecept och återkommande rapporter.

## Nästa rekommenderade steg

Alla 15 planerade utvecklingssteg är genomförda. Skapa en första GitHub Release Candidate, exempelvis `v1.0.0-rc1`, verifiera GitHub Actions-körningen och gå därefter vidare till stabil `v1.0.0` om RC:n är grön.
