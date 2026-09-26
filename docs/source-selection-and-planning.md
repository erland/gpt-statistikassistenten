# Källval och frågeplanering

Steg 7 inför ett källneutralt planeringslager mellan användarfrågan och de källspecifika adaptrarna.

## Principer

1. Källval görs före METADATA-GATE men är inte en ersättning för metadata-verifiering.
2. Tydliga brottsfrågor går till Brå; tydlig detaljerad varuhandel går till Comext.
3. Generell svensk samhällsstatistik går normalt till SCB.
4. Jämförelser mellan EU-länder eller uttryckligt Eurostat-behov går till generell Eurostat-adapter, utom detaljerad varuhandel som hör till Comext.
5. Flera källor får väljas när frågan kräver kombination, exempelvis Brå + SCB för brott per 100 000 invånare.
6. En kombinationsplan är endast en plan. Resultat får inte kombineras förrän METHOD-GATE har verifierat definitioner, geografi, perioder och enheter.
7. Vid verklig tvetydighet ska frågan markeras `needs_clarification` i stället för att en källa gissas.

## Konfliktregel Eurostat kontra Comext

Comext är den specialiserade källan för detaljerad varuhandel. Om en fråga samtidigt innehåller EU-signaler och handelsdimensioner som import/export, partnerland eller varukod ska Comext prioriteras framför den generella Eurostat-adaptern. Generell Eurostat behålls bara när frågan dessutom kräver en annan EU-statistik.

## Planformat

Planen följer `schemas/source-query-plan.schema.json` och innehåller:

- status (`ready`, `needs_clarification`, `blocked`),
- en eller flera källor,
- ordnade källsteg,
- beslutsskäl och confidence,
- explicita tvetydigheter eller konfliktlösningar,
- beroenden när flera källor ska kombineras.

`scripts/source_planner.py` är en deterministisk referensimplementation och får användas som guardrail. Semantisk modellförståelse kan ge bättre tolkning, men får inte kringgå metadata- eller metodgates.
