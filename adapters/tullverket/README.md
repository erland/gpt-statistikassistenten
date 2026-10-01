# Tullverket-adapter

Adaptern planerar uttag från Tullverkets publika beslagsstatistik utan konto eller API-nyckel.

Tullverket erbjuder filtrering efter bland annat halvår, varutyp, varuslag, län och plats samt CSV-export av hela materialet eller vald filtrering. Eftersom ett stabilt generellt statistik-API inte är dokumenterat används **inte** ett antaget internt endpoint-kontrakt.

## Metodregler

- Verifiera filtervärden och sidans uppdateringsdatum vid varje uttag.
- Bevara mängdenhet per rad. Kilo, liter och styck får inte summeras som samma mått.
- Tramadol särredovisas i den nuvarande statistiken.
- Uppgifter kan revideras när laboratorieanalys ändrar klassificering eller när beslag hävs.
- Lokala tidsjämförelser är känsliga för enskilda stora beslag.
- Beslag mäter Tullverkets operativa utfall och får inte beskrivas som ett direkt mått på konsumtion, tillgång eller marknadsstorlek.
