# Tullverket-adapter

Adaptern planerar uttag från Tullverkets publika beslagsstatistik utan konto eller API-nyckel. Den är generell för de restriktionsvaror som publiceras i tjänsten och är inte begränsad till narkotika.

Tullverket erbjuder filtrering efter bland annat halvår, varutyp, varuslag, län och plats samt CSV-export av hela materialet eller vald filtrering. Aktuella varutyper ska verifieras i källan vid varje uttag; 2026 omfattar tjänsten bland annat alkohol, andra vapen och farliga föremål, dopningspreparat, läkemedel, narkotika, skjutvapen, sprängämnen och tobak. Eftersom ett stabilt generellt statistik-API inte är dokumenterat används **inte** ett antaget internt endpoint-kontrakt.

## Metodregler

- Verifiera filtervärden och sidans uppdateringsdatum vid varje uttag.
- Bevara mängdenhet per rad. Kilo, liter och styck får inte summeras som samma mått.
- Tramadol särredovisas i den nuvarande statistiken.
- Uppgifter kan revideras när laboratorieanalys ändrar klassificering eller när beslag hävs.
- Lokala tidsjämförelser är känsliga för enskilda stora beslag.
- Beslag mäter Tullverkets operativa utfall och får inte beskrivas som ett direkt mått på bakomliggande konsumtion, prevalens, tillgång eller marknadsstorlek.
