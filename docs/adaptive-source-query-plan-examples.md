# Exempel på Source Query Plan v2

Dessa exempel är designartefakter för steg 25B. De beskriver önskat planformat men styr ännu inte runtime.

## 1. Enkel fråga – direktläge

**Fråga:** Hur många invånare hade Sundsvalls kommun 2025?

```yaml
question: Hur många invånare hade Sundsvalls kommun 2025?
status: ready
planning_mode: direct
information_needs:
  - id: population
    measure: folkmängd
    concept: befolkning
    population: folkbokförda invånare
    geography: Sundsvalls kommun
    period: "2025"
    frequency: annual
    breakdowns: []
    comparison_mode: single_value
    derived: false
source_roles:
  - need_id: population
    source_id: scb
    role: primary
    tier: A
    integration_status: integrated
    reason: SCB är primär svensk källa för kommunal befolkningsstatistik.
    limitations:
      - Kontrollera tabellens referenstidpunkt och preliminär/slutlig status.
combination:
  required: false
  join_dimensions: []
  transformations: []
  risks: []
decision:
  confidence: high
  review_reasons: []
  clarifications: []
```

## 2. Flera källor – användargranskning före exekvering

**Fråga:** Jämför budgetutfall och antal anställda per myndighet 2025.

```yaml
question: Jämför budgetutfall och antal anställda per myndighet 2025.
status: needs_user_review
planning_mode: review_before_execution
information_needs:
  - id: budget-outturn
    measure: budgetutfall
    concept: statliga anslag
    population: statliga myndigheter
    geography: Sverige
    period: "2025"
    frequency: annual
    breakdowns:
      - myndighet
    comparison_mode: cross_section
    derived: false
  - id: employees
    measure: antal anställda
    concept: statlig sysselsättning
    population: anställda vid statliga myndigheter
    geography: Sverige
    period: "2025"
    frequency: annual
    breakdowns:
      - myndighet
    comparison_mode: cross_section
    derived: false
source_roles:
  - need_id: budget-outturn
    source_id: statskontoret
    role: primary
    tier: A
    integration_status: integrated
    reason: Statskontoret är primär källa för statens budgetutfall per myndighet.
    limitations:
      - Anslagsutfall är inte samma sak som myndighetens totala periodiserade kostnad.
  - need_id: employees
    source_id: scb
    role: primary
    tier: A
    integration_status: integrated
    reason: SCB publicerar antal anställda och löner per statlig myndighet.
    limitations:
      - Antal anställda är inte samma sak som årsarbetskrafter.
  - need_id: employees
    source_id: statskontoret
    role: excluded
    tier: A
    integration_status: integrated
    reason: Myndighetsförteckningens årsarbetskrafter mäter inte samma sak som antal anställda.
    limitations:
      - Annan observationsdefinition.
combination:
  required: true
  join_dimensions:
    - myndighet
    - år
  transformations: []
  risks:
    - Myndighetsnamn och organisationsstruktur kan skilja mellan källorna.
    - Populationerna måste verifieras före join.
decision:
  confidence: medium
  review_reasons:
    - Två primärkällor måste kombineras.
    - Join mellan myndighetsdimensioner krävs.
  clarifications: []
user_review_prompt: >
  Jag föreslår Statskontoret för budgetutfall och SCB för antal anställda.
  De behöver matchas på myndighet och år, och årsarbetskrafter ska inte
  blandas ihop med antal anställda. Vill du att jag går vidare med detta upplägg?
```

## 3. Extern officiell fallback

**Fråga:** Hur många laddbara personbilar finns registrerade per kommun om ingen integrerad källa täcker måttet?

```yaml
question: Hur många laddbara personbilar finns registrerade per kommun?
status: needs_user_review
planning_mode: review_before_execution
information_needs:
  - id: chargeable-cars
    measure: antal registrerade laddbara personbilar
    concept: fordonsbestånd
    population: registrerade personbilar
    geography: svensk kommun
    period: senaste tillgängliga
    frequency: annual
    breakdowns:
      - kommun
      - drivmedelstyp
    comparison_mode: cross_section
    derived: false
source_roles:
  - need_id: chargeable-cars
    source_id: external-official-source
    role: primary
    tier: B
    integration_status: external
    reason: Ingen integrerad tier-A-källa har verifierad täckning för detta exakta mått.
    limitations:
      - Källan måste identifieras och verifieras innan data hämtas.
combination:
  required: false
  join_dimensions: []
  transformations: []
  risks:
    - Definitionen av laddbar bil måste verifieras.
external_fallback:
  required: true
  reason: Ingen integrerad källa täcker det exakta måttet med efterfrågad kommunnivå.
  search_target: Officiell svensk fordonsstatistik med kommun, drivmedelstyp och period.
  disclosure_required: true
decision:
  confidence: medium
  review_reasons:
    - Extern officiell källa krävs.
  clarifications: []
user_review_prompt: >
  Ingen integrerad och kvalitetssäkrad källa täcker detta exakta mått.
  Jag föreslår därför att jag söker efter en officiell svensk fordonsdatakälla,
  verifierar definition, period, geografi och enhet och tydligt märker källan
  som ännu inte kvalitetssäkrad av Statistikassistenten. Vill du att jag går vidare?
```

## Planeringsregler som exemplen illustrerar

- Direktläge ska vara möjligt för en enda tydlig informationsbehov/källa-kombination med hög confidence.
- Fler källor innebär inte automatiskt granskning, men join, olika definitioner, olika frekvenser eller metodrisker gör det.
- En `excluded` källa dokumenterar varför en semantiskt närliggande källa inte används.
- Extern fallback ska beskriva vilken typ av dataset som söks innan webbsökningen startar.
- `source_roles` ska knytas till specifika informationsbehov, inte bara till hela frågan.
