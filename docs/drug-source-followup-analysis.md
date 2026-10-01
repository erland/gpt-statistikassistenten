# Lämplighetsanalys: fortsatt narkotikarelaterat källstöd

## Syfte

Den här analysen görs efter implementationen av EUDA/SCORE och Tullverket och **innan** någon utökning av Brå eller Rättsmedicinalverket (RMV).

## Brå

### Nyttan

Brå har flera relevanta officiella statistikprodukter utöver den nu implementerade statistiken över anmälda brott. För narkotika är särskilt följande användbart:

- personer lagförda för narkotikabrott,
- lagföringsbeslut efter typ av gärning,
- unika narkotikapreparat i lagföringsbeslut,
- tidsserier efter preparat,
- misstänkta personer,
- handlagda brott och brottsmisstankar.

Detta tillför andra perspektiv än anmälda brott och kan exempelvis skilja mellan bruk/innehav och andra gärningar samt ge preparatdimension.

### Teknisk bedömning

Brå publicerar interaktiva tabeller och XLS/XLSX-filer men Statistikassistenten bör fortsatt **inte anta ett generellt publikt API**. Produkterna har olika dimensioner, täckning och historik.

### Rekommendation

**Lämplig för fortsatt implementation**, men stegvis:

1. Utöka först Brå-adaptern med produkten *Personer lagförda för narkotikabrott*.
2. Prioritera typ av gärning och narkotikapreparat eftersom de tillför mest ny information jämfört med befintlig adapter.
3. Använd samma verifierade tjänst-/filstrategi som nuvarande Brå-adapter.
4. Inför produktspecifik metadata-snapshot i stället för ett generiskt Brå-kontrakt.
5. Lägg misstänkta/handlagda produkter i senare steg om konkreta frågor motiverar dem.

Brå är Sveriges officiella kriminalstatistikkälla och är därför primär när måttet faktiskt gäller rättsväsendets statistik.

Officiella ingångar:
- https://bra.se/statistik/statistik-om-rattsvasendet/personer-lagforda-for-brott/personer-lagforda-for-narkotikabrott
- https://bra.se/statistik/statistik-om-rattsvasendet/misstankta-personer
- https://bra.se/statistik/statistik-om-rattsvasendet/handlagda-brottsmisstankar

## Rättsmedicinalverket (RMV)

### Nyttan

RMV:s öppna tabeller innehåller värdefull information som kan saknas i vanliga officiella statistiktabeller, särskilt:

- substanser som bedömts bidra till förgiftningsdödsfall,
- rättstoxikologiska fynd i dödsfallsutredningar,
- konkreta läkemedel och droger i rättsmedicinska ärenden.

Detta kan komplettera Socialstyrelsens officiella dödsorsaksstatistik med en toxikologisk substansbild.

### Begränsningar

RMV anger uttryckligen att myndigheten **inte är en statistikmyndighet** och att uppgifterna kommer från ärendehanteringssystemet. Officiell statistik om avlidna och dödsorsaker tillhandahålls av Socialstyrelsen.

Tabellerna är huvudsakligen HTML-baserade, uppdateras årsvis eller halvårsvis och vissa tabeller redovisar exempelvis de vanligaste substanserna snarare än ett stabilt komplett dataset. Bedömningen av bidragande substans kan dessutom variera mellan sammanställningar beroende på underlagen.

Officiell ingång:
- https://www.rmv.se/om-oss/forskning/statistik/

### Rekommendation

**Inte en full primär runtime-adapter i nästa steg.**

Lämpligare är att:

1. behålla Socialstyrelsen som primär källa för dödsorsaksstatistik,
2. använda RMV som uttryckligt kompletterande toxikologiskt underlag när frågan kräver substansdetalj,
3. dokumentera RMV i käll-/metodreferensen som en sekundär officiell myndighetskälla men inte Sveriges officiella statistik,
4. överväga en begränsad HTML-/tabelladapter först om återkommande konkreta användningsfall visar behov,
5. aldrig blanda RMV:s ärendedata med Socialstyrelsens dödsorsaksstatistik utan tydligt METHOD-GATE.

## Rekommenderad fortsättning

Efter att EUDA/Tullverket-PR:n är validerad:

1. **Brå – lagförda för narkotikabrott och preparat** som separat, avgränsat nästa steg.
2. **RMV – dokumenterad kompletterande källa**, men avvakta full adapter tills ett konkret användningsfall motiverar den.

Det håller projektets princip om primära, verifierbara och stabila källor intakt samtidigt som relevant narkotikastatistik kan byggas ut stegvis.
