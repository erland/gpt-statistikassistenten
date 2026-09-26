# Presentation och export

Detta lager omvandlar verifierade statistikresultat till användarvänliga svar och filer utan att ändra datans semantik.

## Presentationsprofiler

- `brief`: direkt svar + centrala nyckeltal + källor.
- `table`: direkt svar + kompakt tabell + källor.
- `trend`: direkt svar + tabell + försiktig trendanalys + metodnoter + källor.
- `full`: samtliga delar ovan, inklusive tydlig uppdelning mellan källdata och beräknade värden.

## Obligatoriska regler

1. Presentation får endast bygga på verifierade normaliserade observationer eller deterministiska beräkningsresultat.
2. Saknade eller konfidentiella värden får aldrig exporteras som 0.
3. Preliminära, uppskattade och brutna serier ska bära status in i tabell, CSV och metodnotering.
4. Beräknade värden ska märkas som `calculated`; direkt källdata som `source`.
5. Trendtext får beskriva riktning, förändring och jämförelse men inte tillskriva orsaker utan separat evidens.
6. CSV ska vara maskinläsbar UTF-8 med en rad per observation och kolumner för dimensioner, värde, enhet, status och ursprung.
7. Markdown-export ska innehålla rubrik, direkt svar, tabell/nyckeltal, analys, metodnoter och källor när respektive del finns.
8. Källor ska dedupliceras men inte slås ihop om dataset eller statistikprodukt skiljer sig.

## Standardiserad trendanalys

Trendanalys ska vara deterministiskt underbyggd:

- 2 punkter: beskriv endast förändring mellan start och slut.
- 3+ punkter: beskriv total riktning och, om relevant, om serien har tydliga mellanliggande upp- eller nedgångar.
- Kalla inte en serie stabil om variationen inte faktiskt är liten i relation till nivån.
- Rangordning får endast uttryckas när observationerna är jämförbara enligt METHOD-GATE.

## Exportkontrakt

`presentation-result.schema.json` är det maskinläsbara resultatkontraktet. Renderaren i `scripts/presentation_export.py` producerar samma innehåll till Markdown och CSV.
