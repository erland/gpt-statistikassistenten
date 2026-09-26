# Gemensam statistikmodell

## Syfte

Analyslagret ska vara oberoende av om observationen ursprungligen kommer från SCB, Eurostat/Comext eller Brå. Adapterlagret översätter respektive källas metadata och observationsformat till samma modell.

## Lager

1. **Frågemodell** – uttrycker användarens informationsbehov i generiska begrepp.
2. **Adapterlager** – hittar dataset, verifierar metadata och översätter källspecifika dimensioner.
3. **Normaliserad statistikmodell** – dataset, dimensioner, mått och observationer.
4. **Metodlager** – kontrollerar jämförbarhet och utför deterministiska beräkningar.
5. **Svarskontrakt** – skiljer källvärden från beräknade värden och redovisar provenance.

## Kärnobjekt

### Dataset
Generiska egenskaper som titel, publicerande organisation, ämne, frekvens och uppdateringstid. Källspecifika dataset-ID:n hör hemma i `provenance.source.source_identifiers`.

### Dimension
Varje dimension har ett lokalt normaliserat `id`, en `kind` och tillåtna värden. Följande typer är kärnan:

- `time`
- `geography`
- `classification`
- `population`
- `category`
- `measure_variant`
- `other`

### Mått
Mått beskriver vad värdet betyder, inte hur källan råkar namnge kolumnen. Det innehåller statistisk typ och enhet samt vid behov valuta, prisbas, skalfaktor och nämnare.

### Observation
En observation består av dimensionsnycklar, mått, numeriskt värde och status. Saknade, preliminära, skattade eller sekretesskyddade värden representeras uttryckligen och får inte konverteras till noll.

### Metod
Metodfältet beskriver population, definitioner, jämförbarhetsreservationer och brott i tidsserie. Det är underlag för METHOD-GATE.

### Proveniens
Proveniens bevarar ursprung, åtkomstmetod, verifieringsstatus och transformationer. Källspecifika ID:n är tillåtna här eftersom de behövs för reproducerbarhet men de är inte analysdimensioner.

## Normaliseringsregler

- Leverantörens kod får inte användas som semantiskt mått eller analysdimension utan översättning.
- Geografiska etiketter och koder ska särskiljas från geografisk nivå.
- Tid ska bevara källans granularitet; månad får inte reduceras till år före en uttrycklig aggregation.
- Enhet och skalfaktor måste följa varje mått.
- Valutor måste ange valuta och, när källan gör skillnad, relevant prisbas.
- Klassificering ska ange klassifikationssystem när detta påverkar tolkningen, exempelvis CN, SITC eller brottsklassificering.
- Statusmarkeringar ska bevaras genom analysen.
- Beräknade observationer ska dokumenteras som transformationer och får inte presenteras som direkt källdata.

## Kompatibilitet mellan källor

Två serier får kombineras först när följande kan etableras:

1. samma eller metodologiskt förenlig population,
2. samma eller förenlig geografisk nivå,
3. perioder som kan matchas utan dold approximation,
4. förenliga definitioner och klassificeringar,
5. kompatibla enheter eller en explicit enhetskonvertering.

Om kompatibiliteten inte kan verifieras ska assistenten stanna vid jämförelsebeskrivning eller be om ett sakval; den ska inte skapa ett sammanslaget mått.
