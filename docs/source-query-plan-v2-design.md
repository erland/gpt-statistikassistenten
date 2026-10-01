# Source Query Plan v2 – design

## Mål

Version 2 flyttar fokus från "vilka källor verkar relevanta?" till "vilka informationsbehov krävs för att besvara frågan, och vilken roll ska varje källa ha för respektive behov?".

Detta steg definierar kontraktet men ändrar inte `scripts/source_planner.py` eller GPT:ns runtime-beteende.

## Informationsbehov först

Varje fråga bryts ned i ett eller flera informationsbehov med:

- mått,
- begrepp,
- population/observationsenhet,
- geografi,
- period och frekvens,
- önskade nedbrytningar,
- jämförelseläge,
- om måttet är direkt eller härlett.

Härledda mått ska dessutom ange formel och vilka informationsbehov de beror på.

## Källroller

En källa kopplas alltid till ett specifikt informationsbehov och får en av fyra roller:

- `primary` – förstahandskälla för just detta mått,
- `supporting` – levererar nämnare, join-dimension, kontext eller annat separat delmått,
- `alternative` – kan användas men är mindre lämplig,
- `excluded` – semantiskt närliggande men metodmässigt olämplig.

Källrollen kompletteras med:

- tier A–D från source registry,
- integrationsstatus: `integrated`, `catalog_only` eller `external`,
- skäl,
- begränsningar.

## Direktläge kontra granskningsläge

### Direktläge

`planning_mode: direct` är lämpligt när:

- frågan har ett eller flera okomplicerade informationsbehov,
- varje behov har en tydlig integrerad tier-A primärkälla,
- ingen metodkänslig join eller transformation krävs,
- ingen extern källa behövs,
- confidence är hög,
- risklistan är tom eller trivial.

### Granskningsläge

`review_before_execution` används när minst ett av följande gäller:

- flera källor måste joinas,
- olika observationsenheter kan blandas,
- olika tidsfrekvenser måste transformeras,
- flera rimliga primärkällor finns och valet påverkar tolkningen,
- ett härlett mått kräver data från flera källor,
- en källa är bara `catalog_only`,
- extern tier-B/C-källa behövs,
- confidence är medium/low,
- metodriskerna är relevanta för hur användaren tolkar resultatet.

Användargranskning ska inte krävas bara för att två källor förekommer. Om exempelvis en källa levererar en enkel befolkningsnämnare och definitionerna är stabila kan framtida runtime tillåta direktläge efter deterministisk validering. Detta beslut hör till steg 25C.

## Status

- `ready` – planen är körbar utan ytterligare mänskligt beslut.
- `needs_clarification` – frågan saknar nödvändig information, exempelvis geografi eller måttdefinition.
- `needs_user_review` – planen är tekniskt möjlig men källkombination/metod bör bekräftas.
- `blocked` – ingen säker plan kan skapas.

Status och planeringsläge är relaterade men inte identiska. En plan kan exempelvis vara `ready` och ändå beskrivas i granskningsläge i framtida UI-flöden, men v2-designen använder normalt `needs_user_review` tillsammans med `review_before_execution`.

## Kombination och METHOD-GATE

`combination` beskriver:

- om flera informationsbehov faktiskt måste kombineras,
- join-dimensioner,
- transformationer/aggregationer,
- metodrisker.

Planen får beskriva en tänkt join, men kombinationen får inte exekveras innan METHOD-GATE verifierat kompatibilitet för population, geografi, period/frekvens, definition och enhet.

## Extern fallback

Extern fallback är ett eget planeringsobjekt och aktiveras när:

1. source registry saknar en tier-A-källa för måttet, eller
2. en känd källa har relevant `catalog_scope` men inte en säker `integrated_scope` för det efterfrågade uttaget.

Planen ska då formulera ett `search_target` som beskriver vilket dataset som söks. Runtime ska inte söka efter ett färdigformulerat svar.

Extern källa innebär normalt:

- `tier: B` för officiell primärkälla/open data,
- `integration_status: external`,
- `planning_mode: review_before_execution`,
- obligatorisk disclosure i det slutliga svaret.

## Förhållande till source registry

Source Query Plan v2 ska använda `knowledge/source-registry.yaml` som den strukturerade sanningskällan för:

- officiell katalogkapacitet,
- nuvarande integrationskapacitet,
- primära/sekundära användningsområden,
- producentroll,
- geografi och frekvens,
- kända begränsningar.

Planen får inte påstå `integration_status: integrated` för ett uttag som endast stöds av `catalog_scope`.

## Förhållande till dagens planner

Dagens `source_planner.py` och v1-schema lämnas orörda i steg 25B.

Steg 25C bör införa en ny semantisk planner eller ett adapterlager som kan producera v2-planer. Den deterministiska v1-plannern kan då användas som guardrail/regressionkontroll under övergången i stället för att direkt tas bort.

## Acceptanskriterier inför 25C

Innan runtime ändras ska följande vara stabilt:

1. Schemat kan representera enkel-, fler- och extern-källsfrågor.
2. Källroller är kopplade till informationsbehov, inte bara hela frågan.
3. Katalogkapacitet och integrerad kapacitet hålls isär.
4. Extern fallback kräver tydlig disclosure.
5. Review-reglerna är dokumenterade.
6. Exempel finns för direktläge, multi-source review och extern fallback.
7. Befintlig v1-planner och dess tester fortsätter fungera oförändrat.
