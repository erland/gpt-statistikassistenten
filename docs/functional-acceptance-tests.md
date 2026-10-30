# Funktionella acceptanstester – Statistikassistenten 1.6.1

## Omfattning och evidens
Fyra manuella end-to-end-scenarier genomfördes i en verklig ChatGPT-konversation med installerad `@statistikassistenten` 1.6.1 (2026-10-30). Testutfall återgavs i projektchatten och granskades mot det förväntade beteendet. Test 4 inkluderade en exporterad CSV-fil. Detta dokument är en **återanvändbar testplan och historisk observationsrapport**, inte automatisk bevisning för live-API-paritet eller exakt intern Skill-aktivering.

De tre modulära Skills som omfattas är `statistikkallor`, `statistikkvalitet` och `statistikpresentation`. För alla tester gäller: avvikelse från källa får inte döljas; metodgrindar får inte kringgås; skilj direkta observationer från egna beräkningar.

## Test 1 – Officiell källa, befolkningsserie

**Prompt:**
> Med hjälp av @statistikassistenten: Hur har Sveriges befolkning utvecklats under de senaste tio åren? Använd officiell statistik från SCB, presentera en tabell med årtal och befolkning samt beräkna den procentuella förändringen under perioden. Ange källor och metod.

**Förväntat:**
1. Källval SCB och verifierad statistikprodukt, population och referensdatum.
2. Senaste tio **avslutade** kalenderår och identifierbart årsintervall, inte preliminär senare period.
3. Årstabell med källbelagda heltalsobservationer, total absolut och procentuell förändring samt formel.
4. Definition och metodreservationer, tydligt åtskild observation/beräkning; inga obelagda förklaringar till trend.

**Observerat 2026-10-30:** 2016–2025, 9 995 153 → 10 605 529 invånare, +610 376 (+6,11 %). Godkänt avseende scenario och observerbart beteende. Källänkarnas utseende i kopierad text var inte tillräckligt för att testa klickbarhet.

## Test 2 – Olika arbetslöshetsdefinitioner

**Prompt:**
> Med hjälp av @statistikassistenten: Jämför arbetslösheten i Sverige enligt SCB och Arbetsförmedlingen under 2025. Förklara om uppgifterna är direkt jämförbara och visa eventuella skillnader i definition, population och mätmetod. Om uppgifterna inte är jämförbara ska du inte beräkna en gemensam arbetslöshetssiffra.

**Förväntat:**
1. SCB AKU och Arbetsförmedlingens registerstatistik särskiljs.
2. Respektive åldersgrupp, observationsenhet, definition, period, metod och nämnare redovisas.
3. Ingen summa, medelvärdesbildning eller differens som antyder jämförbara personer/andelar.
4. Slutsatser begränsas till vilka frågor respektive källa kan besvara.

**Observerat:** 8,8 % och cirka 510 000 enligt AKU; 6,9 % och cirka 367 000 inskrivna enligt Arbetsförmedlingen. Ingen gemensam arbetslöshetssiffra beräknades. Godkänt för metodspärren. Kontrollera uppgifternas aktualitet vid omtest.

## Test 3 – Extern källa med obligatoriskt godkännande

**Prompt (del A):**
> Med hjälp av @statistikassistenten: Hur har antalet registrerade elbilar i Norge utvecklats 2020–2025? Använd i första hand officiell norsk statistik och redovisa antalet per år samt procentuell förändring. Om källan inte ingår bland dina integrerade statistikkällor ska du följa ditt ordinarie granskningsförfarande.

**Förväntat före godkännande:**
1. Kontrollerar `integrated_scope` och `catalog_scope` i source registry.
2. SSB är extern Tier B om den inte är integrerad och föreslås som officiell primärkälla.
3. Visar mätdefinition (bestånd av registrerade batterielektriska personbilar, inte nyregistreringar), geografi, period, enhet och metod.
4. **Stoppar före datauttag** och ber om uttryckligt godkännande.

**Prompt (del B, endast efter godkänd plan):**
> Godkänn och fortsätt

**Förväntat efter godkännande:**
1. Hämtar och verifierar SSB-tabell och metadata, redovisar sex årsobservationer och förändringsberäkningar.
2. Märker externa data som verifierade för **det aktuella svaret**, inte permanent integrerade eller kvalitetssäkrade.
3. Dokumenterar eventuella källavvikelser utan att spekulera om deras orsaker.

**Observerat:** Granskningsstopp och godkännande fungerade. SSB tabell 07849 användes för 2020–2025 och svar gavs med beståndstal och förändringar. Notera att skillnad mellan närliggande SSB-totaler inte ska förklaras utan separat källa.

## Test 4 – CSV-export till svensk Excel

**Prompt (som uppföljning i samma testchatt):**
> Med hjälp av @statistikassistenten: Använd de verifierade uppgifterna från SSB för registrerade batterielektriska personbilar i Norge 2020–2025. Skapa en nedladdningsbar CSV-fil med år, antal, årlig förändring i antal, årlig förändring i procent, enhet och källa. Kontrollera att beräkningarna stämmer och att filen kan användas i Excel.

**Förväntat:**
1. En faktiskt nedladdningsbar `.csv`, inte bara en påstådd fil.
2. Sex datarader och kolumner för år, antal, årsändring antal/procent, enhet, källa.
3. Tomma ändringsfält för 2020; fem korrekt beräknade differenser och procenttal.
4. För svensk Excel: UTF-8 med BOM, semikolon och decimaltecken komma, numeriska cellvärden utan tusentalsavgränsare.
5. Läs tillbaka CSV och kontrollera rader, kolumner och beräkningar; källhänvisning bevaras.

**Referensvärden för omtest:**

| År | Antal | Årsförändring | Årsförändring % |
|---|---:|---:|---:|
| 2020 | 340002 | – | – |
| 2021 | 460734 | 120732 | 35,51 |
| 2022 | 599169 | 138435 | 30,05 |
| 2023 | 689169 | 90000 | 15,02 |
| 2024 | 788750 | 99581 | 14,45 |
| 2025 | 945182 | 156432 | 19,83 |

Förändringen 2020–2025: 605 180 och avrundat 177,99 %. Referensvärdena är **historiska testdata**, inte löpande uppdaterade SSB-observationer.

**Observerat:** CSV levererades som bifogad fil och granskades i testkonversationen; återläsning, delimiter, BOM och beräkningskontroll rapporterades godkända. Excel-programmets faktiska importdialog testades inte.

## Godkännandegrind för kommande releaser

- Kör test 1–4 i ordning i en **ny chatt**, med aktuell installerad Plugin-version dokumenterad.
- Spara prompt, utfall och eventuella filer/skärmbilder i testprotokoll. Dokumentera aktuell tabellidentifiering, referensdatum och käll-URL:er.
- Notera PASS/FAIL per kriterium ovan. Avvikelse i metadata, metodstopp, numerik eller filintegritet = FAIL.
- Kör automatiserad CI (lint, tester, distributioner, Plugin/Engine-kontrakt) separat; grönt CI ersätter inte funktionell värdtestning.
- Intern Skill-aktivering får bara anges som *verifierad* om värden ger tillförlitliga aktiveringsloggar. Slutresultat som matchar förväntningarna ger endast **beteendeindikation**.
- Vid omtest med ny statistikperiod: uppdatera indata och förväntade värden först efter verifierad källkontroll. Förlita dig inte på historiska tal som live-fakta.

## Testomgång 2026-10-30

| Test | Utfall | Begränsning |
|---|---|---|
| 1 Befolkningsutveckling | PASS | Klickbara källänkar ej verifierade i originalvyn |
| 2 Arbetslöshetsdefinitioner | PASS | Statisk resultatgranskning; ej Skill-aktiveringslogg |
| 3 Extern Tier B/granskning | PASS | Inga tekniska anropsloggar från värden |
| 4 CSV-export | PASS | Faktisk Excel-programimport ej genomförd |

**Samlat:** Fyra observerade funktionella scenarier godkända. Inga blockerande beteendeavvikelser noterade; full runtimeparitet är inte bevisad.
