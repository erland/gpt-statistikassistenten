# Comext-adapter

Comext-adaptern hanterar Eurostats `DS-`-prefixerade dataset för detaljerad internationell varuhandel. Dessa dataset ligger på en separat officiell API-bas: `https://ec.europa.eu/eurostat/api/comext/dissemination`.

## Flöde

1. Lista eller sök dataflows på Comext-endpointen.
2. Hämta strukturmetadata för valt `DS-`-dataset.
3. Mappa verkliga dimensions-ID:n till de semantiska rollerna `reporter`, `partner`, `flow`, `product`, `time` och `indicator` samt vid behov `frequency`.
4. Verifiera alla val mot datasetets codelists/constraints.
5. Bygg alltid ett filtrerat datauttag. Ett komplett Comext-dataset får aldrig efterfrågas.
6. Normalisera värde/kvantitet och övriga dimensioner till projektets gemensamma statistikmodell före analys.

## Semantiska handelsroller

- **reporter** – rapporterande land eller område.
- **partner** – handelspartner.
- **flow** – import eller export enligt datasetets kodlista.
- **product** – varukod enligt den klassificering datasetet använder, exempelvis CN/HS/SITC/BEC.
- **time** – år eller månad.
- **indicator** – exempelvis handelsvärde eller kvantitet.
- **frequency** – års- eller månadsfrekvens när dimensionen finns.

Koder får inte antas från minnet. Exempelvis kan `1`/`2` förekomma som flödeskoder i vissa dataset, men betydelsen ska alltid verifieras i metadata innan användning.

## Storleksregel

Comext-dataset kan vara mycket stora. Adaptern kräver därför explicit urval för rapportör, partner, flöde, produkt, period och indikator. Om användaren frågar brett ska uttaget delas upp eller aggregeringsnivån höjas i stället för att ett fullständigt dataset hämtas.
