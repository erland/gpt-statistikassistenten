# Status

## Lägesbild

Tidigare källutbyggnader är genomförda och PR #5 är mergad. Pågående steg 20 generaliserar Tullverket från narkotikabeslag till hela den publika beslagsstatistiken för restriktionsvaror.

## Pågående justering

- Tullverket-adaptern har inte längre Narkotika som implicit standardvarutyp.
- Källplaneraren routar tydliga frågor om alkohol-, tobaks-, läkemedels-/dopnings-, vapen- och sprängämnesbeslag till Tullverket.
- Aktuell varutyp/varuslag ska fortfarande verifieras i källan före uttag.
- Officiell CSV-export används fortsatt; inget odokumenterat internt API införs.
- Metodregeln gäller alla beslagstyper: beslag är operativa utfall och inte direkta mått på bakomliggande konsumtion, prevalens, tillgång eller marknadsstorlek.

## Nästa rekommenderade steg

Kör full CI/distributionsvalidering. Efter grön PR kan arbetet fortsätta med den tidigare analyserade Brå-utökningen.
