# Projektspecifik Statistikassistenten Engine (steg 3)

## Bedömning

Statistikassistenten har 29 deklarerade körbara statistikverktyg (källadaptrar, beräkningar, kvalitetskontroll och export). Därför är `engine.enabled: true` berättigat. Engine är **skild** från GPT Byggarens distributionsmotor 1.6.33.

## Paketering

`gpt-project.yaml` deklarerar uttryckliga skriptresurser, källregister, verkligt körbart självtest och PyYAML-beroende. Script-resurserna är inte automatiskt tillgängliga som Plugin-verktyg; hosten måste erbjuda Python-exekvering och filåtkomst. API-anrop, nätverk och runtime-hoststöd är inte verifierade.

## Säkerhet och verifiering

Verifiera `engine-package.json` och varje filhash innan körning. Kör endast det deklarerade självtestet i en kompatibel Python-miljö. Engine-självtest täcker import och deterministisk procentförändring; projektets unittest/pytest täcker vidare domänlogik. Inga live-API-tester eller värdtester har körts.

## Fortsättning

Kör GitHub Actions, kontrollera release-tag och Engine-ZIP från samma tagg. Kör därefter funktionella värdtester i Plugin och andra runtimes.
