# Brå-adapter

Brå-adaptern använder officiell statistik från Brottsförebyggande rådet utan att anta att Brå har ett enda stabilt generellt statistik-API.

## Stödda produktfamiljer

- anmälda brott
- handlagda brott
- misstänkta personer
- handlagda brottsmisstankar
- personer lagförda för brott

Runtime ska först välja produkt och därefter hämta/normalisera metadata från Brås officiella statistiktjänst, webbtabelldata eller publicerade filer. Den deterministiska adaptern validerar produkt, dimensioner, urval och proveniens men fabricerar aldrig tabell- eller dimensionskoder.

Narkotikabrott hanteras inom samma generella produkter som andra brottstyper. Om Brå publicerar preparat eller gärningstyp som dimension inom lagföringsstatistiken får den användas där, men den är inte ett separat special-API.

## Metodregler

- Anmälda brott är registrerade anmälningar, inte all faktisk brottslighet.
- Handlagda brott och brottsmisstankar beskriver avslutade steg i rättskedjan.
- Misstänkta personer är personer; en person kan förekomma i flera brottskategorier.
- Brottsmisstankar är inte personer och får inte summeras som sådana.
- Lagföringsbeslut, lagförda personer, huvudbrott och påföljd är olika redovisningsmått.
- Kontrollera alltid produktens kvalitetsdeklaration och definitions-/metodbrott före tidsjämförelser.
