# Källval och frågeplanering

Steg 7 inför ett källneutralt planeringslager mellan användarfrågan och de källspecifika adaptrarna.

## Principer

1. Källval görs före METADATA-GATE men är inte en ersättning för metadata-verifiering.
2. Tydliga brottsfrågor går till Brå; tydlig detaljerad varuhandel går till Comext.
3. Generell svensk samhällsstatistik går normalt till SCB.
4. Jämförelser mellan EU-länder eller uttryckligt Eurostat-behov går till generell Eurostat-adapter, utom detaljerad varuhandel som hör till Comext.
5. Flera källor får väljas när frågan kräver kombination, exempelvis Brå + SCB för brott per 100 000 invånare.
6. En kombinationsplan är endast en plan. Resultat får inte kombineras förrän METHOD-GATE har verifierat definitioner, geografi, perioder och enheter.
7. Vid verklig tvetydighet ska frågan markeras `needs_clarification` i stället för att en källa gissas.

## Brå-produktval

När en fråga gäller rättsväsendet ska Brå först väljas som källa och därefter rätt produkt:

- **anmälda brott** för registrerade brottsanmälningar,
- **handlagda brott** för avslutade brottsärenden, personuppklaring och lagföringsprocent,
- **misstänkta personer** för antal/struktur bland personer som varit minst skäligen misstänkta,
- **handlagda brottsmisstankar** för beslut kring enskilda brottsmisstankar,
- **personer lagförda för brott** för lagföringsbeslut, huvudbrott, påföljder och andra publicerade lagföringsdimensioner.

Narkotikabrott är inte en separat Brå-integration. Preparat, gärningstyp eller liknande används som produktdimension när den officiella lagföringsstatistiken erbjuder den. Personer, brott, brottsmisstankar och beslut är olika observationsenheter och får inte blandas utan METHOD-GATE.

## Svensk handel – SCB kontra Comext

SCB är förstakälla för inhemsk svensk handel och konsumtion: detaljhandel, dagligvaru-/sällanköpsvaruhandel, försäljningsvolym, omsättning, partihandel, e-handel och hushållens konsumtion. Comext används för detaljerad import/export efter reporter, partnerland och produkt/varukod.

Ordet **handel** ensamt är inte tillräckligt för källval. Import/export, partnerland och varukod signalerar Comext; detaljhandelsomsättning, försäljningsvolym och e-handel signalerar SCB. Om frågan uttryckligen jämför ett inhemskt handelsmått med import/export ska båda källorna planeras och kombineras först efter METHOD-GATE.

## Konfliktregel Eurostat kontra Comext

Comext är den specialiserade källan för detaljerad varuhandel. Om en fråga samtidigt innehåller EU-signaler och handelsdimensioner som import/export, partnerland eller varukod ska Comext prioriteras framför den generella Eurostat-adaptern. Generell Eurostat behålls bara när frågan dessutom kräver en annan EU-statistik.

## Planformat

Planen följer `schemas/source-query-plan.schema.json` och innehåller:

- status (`ready`, `needs_clarification`, `blocked`),
- en eller flera källor,
- ordnade källsteg,
- beslutsskäl och confidence,
- explicita tvetydigheter eller konfliktlösningar,
- beroenden när flera källor ska kombineras.

`scripts/source_planner.py` är en deterministisk referensimplementation och får användas som guardrail. Semantisk modellförståelse kan ge bättre tolkning, men får inte kringgå metadata- eller metodgates.

## Utökade svenska källor

- **Kolada** prioriteras när frågan gäller jämförbara kommun-/regionnyckeltal, kommunal ekonomi, kvalitet eller verksamhetsmått. Kontrollera alltid ursprunglig datakälla i KPI-metadata eftersom Kolada även återpublicerar andra producenters statistik.
- **Socialstyrelsen** prioriteras för vård, läkemedel, dödsorsaker, patient-/socialtjänstnära statistik och ekonomiskt bistånd när motsvarande detalj finns i deras statistikdatabas.
- **Folkhälsodata** prioriteras för folkhälsoindikatorer, levnadsvanor, vaccinationer, smittsamma sjukdomar och andra FHM-specifika indikatorer.
- **Arbetsförmedlingen** prioriteras för frågor om aktuella/historiska platsannonser och annonserad kompetens- eller yrkesefterfrågan. SCB används fortsatt för arbetslöshet och sysselsättning.
- **Riksbanken** prioriteras för styrränta, andra ränte-/marknadsserier och växelkurser.

När flera källor överlappar ska den mest primära/statistikansvariga källan väljas för själva måttet, medan Kolada kan vara lämplig för jämförbara färdigdefinierade kommunnyckeltal. Dubbletter får inte räknas som separata observationer.


## Elpris, produktion och förbrukning

- **SCB** prioriteras för hushållens/övriga kunders elpris, elhandelspris, elnätspris och elavtal.
- **Svenska kraftnät** prioriteras för fysisk produktion/förbrukning per period och elområde via Mimer.
- **Energimyndigheten** används för bredare energi-/elanvändning och energibalanser.
- Frågor som kombinerar pris och förbrukning kan använda SCB + Svenska kraftnät efter METHOD-GATE.
- Spotpris/day-ahead är ett separat marknadsmått och täcks inte av denna integration.

## Ytterligare domänkällor

- **Energimyndigheten** prioriteras för energibalanser, energianvändning, elproduktion, kraftslag, biogas och energiprognoser.
- **Försäkringskassan** prioriteras för sjukpenning, sjukfall, sjuk-/aktivitetsersättning, föräldraförsäkring och andra socialförsäkringsförmåner.
- **Jordbruksverket** prioriteras för jordbruk, skörd, arealer, lantbruksdjur, ekologisk produktion, jordbrukspriser och livsmedelskonsumtion.
- **Skolverket** prioriteras för skolenheter, utbildningar och Skolverkets utbildningsstatistik. Kolada används fortsatt när frågan gäller färdigdefinierade kommunala skolnyckeltal som kostnad per elev.
- **SMHI** prioriteras för meteorologiska observationer och klimatserier. SCB används fortsatt för samhällsstatistik där väder/klimat endast är en förklarande variabel.

Generiska geografiord som Sverige, kommun eller län ska inte dra en fråga från en tydlig domänkälla till SCB.

## Statliga myndigheter – ekonomi och personal

- **Statskontoret** prioriteras för statens budget, anslag, anslagsposter, månads-/årsutfall och myndighetsförteckning/årsarbetskrafter.
- **SCB** prioriteras för antal anställda, löner och personalstruktur i statlig sektor.
- En fråga som jämför budget/anslagsutfall med personal kan använda Statskontoret + SCB, men först efter METHOD-GATE.
- Anslagsutfall får inte beskrivas som myndighetens totala kostnad. Årsarbetskrafter och antal anställda är olika mått.
- Använd endast Statskontorets publicerade öppna datafiler; bygg inte mot odokumenterade Hermes-endpoints.

## Narkotika, restriktionsvaror och drogrelaterade indikatorer

- **EUDA/SCORE** prioriteras för avloppsmätningar av narkotikarester och europeiska stadsjämförelser. Avloppsdata är en samhällssignal och får inte omvandlas till antal användare eller prevalens utan separat metodstöd.
- **Tullverket** prioriteras för beslag av restriktionsvaror, bland annat alkohol, andra vapen och farliga föremål, dopningspreparat, läkemedel, narkotika, skjutvapen, sprängämnen och tobak. Använd den officiella statistiksidans CSV-export; anta inte ett odokumenterat internt API.
- Brå används fortsatt för kriminalstatistik och Socialstyrelsen/Folkhälsodata för vård-, dödsorsaks- och folkhälsoindikatorer. Dessa mått får kombineras först efter METHOD-GATE.
- Beslag, avloppshalter, brottsanmälningar och vårdutfall mäter olika delar av narkotikasituationen och får inte behandlas som utbytbara mått.


## Internationella källor

- **World Bank** är bred förstakälla för globala och utomeuropeiska jämförelser, särskilt utveckling, fattigdom, befolkning och makroindikatorer.
- **OECD** prioriteras när frågan uttryckligen gäller OECD-länder eller harmoniserade OECD-indikatorer.
- **WHO** prioriteras för global hälsostatistik. Eftersom den äldre GHO OData-tjänsten är utfasad ska runtime verifiera aktuell Data Hub-export/API vid frågetillfället.
- **BIS** prioriteras för internationell bank-, kredit-, bostadspris- och finansiell statistik.
- **ECB** prioriteras för euroområdets monetära, bank- och finansstatistik.

### Konfliktregler
- EU-samhällsstatistik: Eurostat före World Bank/OECD när EU-harmonisering är frågans kärna.
- Euroområdets penning-/bankstatistik: ECB före Eurostat.
- Internationell bank/kredit/bostadsprisstatistik: BIS före World Bank.
- Global hälsa: WHO före World Bank när WHO har ett direkt hälsomått.
- OECD-specifik jämförelse: OECD före World Bank.
