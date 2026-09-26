# Käll- och metodreferens

## Källval
- **SCB**: svensk officiell statistik och Statistikdatabasen.
- **Eurostat**: harmoniserad EU-statistik.
- **Comext**: detaljerad internationell varuhandel, särskilt reporter × partner × produkt × flöde × tid.
- **Brå**: svensk kriminalstatistik.

## SCB PxWebApi v2
Bas-URL: `https://statistikdatabasen.scb.se/api/v2`.
Arbetsordning: sök `/tables` → verifiera `/tables/{id}/metadata` → hämta `/tables/{id}/data` med explicit selektion. Komplexa urval bör göras med POST. Max 150 000 dataceller per uttag. Verifiera obligatoriska variabler och värdekoder i metadata.

## Eurostat SDMX 3.0
Bas-URL: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0`.
Dataset kan upptäckas via Eurostats katalog eller dataflows. Hämta dataflow/DSD/codelists före tolkning av koder. Datafrågor kan använda series-key eller komponentfilter. Dataset med `DS-`-prefix hör till Comext.

## Eurostat Comext
Bas-URL: `https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/3.0`.
Verifiera alltid faktisk struktur. Semantiska roller måste kunna mappas till datasetets dimensioner: rapportör, partner, flöde, produkt, tid och indikator. Hämta aldrig ett helt stort Comext-dataset när frågan kan filtreras.

## Brå
Brå saknar i version 1 ett antaget generellt publikt API i assistenten. Använd officiell statistiktjänst eller publicerade tabeller/filer och verifiera produkt, brottstyp, geografi, period, enhet och preliminär/slutlig status. Anmälda brott är inte samma sak som faktisk brottslighet.

## Kombinerade mått
- Per capita: samma geografi och period i täljare och nämnare.
- Procentuell förändring: `(nytt-gammalt)/gammalt*100`; basvärde får inte vara 0.
- Index: vald bas måste vara verifierad och icke-noll.
- Andel: del och total måste ha kompatibla enheter och definitioner.
- Saknade/sekretesskyddade värden får aldrig ersättas med 0.
- Preliminär status ska följa med härledda resultat.

## Proveniens
Ange organisation, dataset/tabell/statistikprodukt, geografi, tid, mått/enhet, metodreservationer och om siffran är direkt hämtad eller beräknad.

## Kolada API v3
Bas-URL: `https://api.kolada.se/v3`. Använd metadata för nyckeltalet före data. Kommunuttag följer mönstret `/data/municipality/{kommunkod}/kpi/{nyckeltal}`. Kolada kräver källangivelse och metadata kan ange en annan ursprunglig statistikproducent; bevara båda nivåerna i proveniensen.

## Socialstyrelsens Statistikdatabas
Bas-URL: `https://sdb.socialstyrelsen.se/api/v1`. Lista ämnen och fördelningsvariabler innan `/resultat` hämtas. Resultat pagineras vid större uttag; standardtaket i dokumentationen är 5 000 poster per sida. Ange Socialstyrelsen och statistikdatabasen som källa.

## Folkhälsodata
Folkhälsomyndighetens Folkhälsodata använder PxWeb API v1. Metadata måste verifiera tabell, dimensioner, geografi, år, mått och särskilda metodegenskaper som självrapportering eller flerårsmedelvärden.

## Arbetsförmedlingen JobSearch
Publikt JobSearch-API för platsannonser. Använd endast som indikator på annonserad efterfrågan efter yrken/kompetenser/geografi. Antal annonser får inte tolkas som arbetslöshet, sysselsättning eller antal unika lediga tjänster utan uttryckligt stöd.

## Sveriges Riksbank SWEA
Bas-URL: `https://api.riksbank.se/swea/v1`. Använd `/Series` eller `/Groups` för att verifiera serie-ID och metadata, därefter `/Observations/...`. Källan ska anges. Växelkurser är indikativa och avsedda för information, inte som garanterade transaktionskurser.
