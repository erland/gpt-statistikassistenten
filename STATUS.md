# Status

## Lägesbild

Tidigare källutbyggnader är genomförda. Steg 20 generaliserar Tullverket från narkotikabeslag till hela den publika beslagsstatistiken för restriktionsvaror.

## Genomförd justering

- Tullverket-adaptern har inte längre Narkotika som implicit standardvarutyp.
- Källplaneraren routar tydliga frågor om alkohol-, tobaks-, läkemedels-/dopnings-, vapen- och sprängämnesbeslag till Tullverket.
- Aktuell varutyp/varuslag verifieras fortsatt i källan före uttag.
- Officiell CSV-export används fortsatt; inget odokumenterat internt API införs.
- Metodregeln gäller alla beslagstyper: beslag är operativa utfall och inte direkta mått på bakomliggande konsumtion, prevalens, tillgång eller marknadsstorlek.

## Validering

- 82 regressionstester passerar.
- Projektlint: 0 fel, 0 varningar.
- Modellrobusthet: PASS.
- Final hygiene: PASS.
- Distribution validation: PASS.

## Nästa rekommenderade steg

Granska och merge:a PR #6. Därefter kan arbetet fortsätta med den tidigare analyserade, avgränsade Brå-utökningen för lagförda narkotikabrott och preparat.
