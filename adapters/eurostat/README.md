# Eurostat-adapter

Den generella Eurostat-adaptern använder **SDMX 3.0** och gör inga nätverksanrop själv. Runtime hämtar katalog, struktur och data från Eurostats officiella API; adaptern validerar sedan dataset och filter innan ett datauttag konstrueras.

## Flöde

1. Hämta dataflow-katalogen från `structure/dataflow/*/*/~` och matcha användarens fråga mot namn/beskrivning.
2. Välj aldrig datasetkod enbart från minne.
3. Hämta strukturmetadata för den valda dataflowen och verifiera DSD, dimensioner och codelists.
4. Bygg filter med `c[DIMENSION]=...`; flera värden betyder OR och tidsintervall uttrycks med SDMX-operatorer.
5. Hämta minsta nödvändiga utsnitt och normalisera observationerna till projektets gemensamma statistikmodell.
6. Dataset vars kod börjar med `DS-` ska inte gå genom denna adapter; de hanteras av Comext-adaptern i nästa steg.

## Designval

Komponentfilter används framför positionsberoende series keys eftersom de blir mindre felkänsliga när GPT:n arbetar med flera dataset med olika dimensionsordning. Strukturen måste ändå verifieras före datauttag.
