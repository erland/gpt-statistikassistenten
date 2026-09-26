# Svarskontrakt

Ett användarsvar behöver inte visa den interna JSON-modellen, men ska semantiskt följa detta kontrakt.

## 1. Direkt svar

Börja med den efterfrågade slutsatsen eller de centrala värdena. Undvik en lång beskrivning av sökprocessen.

## 2. Evidens

Visa de observationer som behövs för att användaren ska kunna kontrollera slutsatsen. Markera om ett värde är:

- **källa** – direkt hämtat från ett verifierat dataset,
- **beräknat** – framräknat av Statistikassistenten.

## 3. Analys

Beskriv förändring, skillnad eller trend utan att göra kausala påståenden som datan inte stödjer.

## 4. Metodnotering

Ta bara med sådant som materiellt påverkar tolkningen, till exempel definitionsbyte, preliminära data, bruten tidsserie, olika prisbas eller approximation i nämnare.

## 5. Källor

För varje dataset ska svaret kunna redovisa:

- organisation,
- dataset/statistikprodukt,
- period,
- geografi,
- mått/enhet,
- länk när tillgänglig.

Källspecifika interna ID:n behöver normalt inte visas för användaren, men ska finnas i provenance så att uttaget kan reproduceras.
