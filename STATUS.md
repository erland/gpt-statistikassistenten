# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Steg 24 förbättrar elprisdata via SCB och lägger till Svenska kraftnäts Mimer API för fysisk elproduktion och elförbrukning.

## Genomförd eldataförbättring

- SCB används för elhandelspris, elnätspris, elavtal och publicerade kund-/totalpriser.
- Svenska kraftnät används för fysisk produktion/förbrukning efter verifierad typ, period och elområde/nätområde.
- Energimyndigheten används fortsatt för bredare energi-/elanvändning och energibalanser.
- Routingkonflikten mellan SVK och Energimyndigheten hanteras så att detaljerad elområdes-/tidsdata går till SVK medan bred kraftslags-/energistatistik går till Energimyndigheten.
- Kundpris, spotpris och fysisk förbrukning behandlas som olika mått.
- Nord Pool spotpris ingår ännu inte.
- Mimer-adaptern verifierar produkt-/förbrukningstyp före data och skiljer Actual från Planned.

## Validering

- Regressionstester passerar.
- Projektlint: PASS.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #10.
