# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Pågående steg 24 förbättrar elprisdata via SCB och lägger till Svenska kraftnäts Mimer API för fysisk elproduktion och elförbrukning.

## Pågående eldataförbättring

- SCB används för elhandelspris, elnätspris, elavtal och publicerade kund-/totalpriser.
- Svenska kraftnät används för fysisk produktion/förbrukning efter verifierad typ, period och elområde/nätområde.
- Energimyndigheten används fortsatt för bredare energi-/elanvändning och energibalanser.
- Kundpris, spotpris och fysisk förbrukning behandlas som olika mått.
- Nord Pool spotpris ingår ännu inte.
- Mimer-adaptern verifierar produkt-/förbrukningstyp före data och skiljer Actual från Planned.

## Nästa rekommenderade steg

Kör full CI och merge:a först efter grön distributionsvalidering.
