# {{GPT_NAME}} – kompatibilitet

Custom GPT-varianten bevarar kärnflödet och gates men har inte lokala Python-skript inbäddade.

## Paritet
- SCB: hög paritet via Action mot PxWebApi v2.
- Eurostat: hög paritet via Action mot SDMX 3.0, med verifierad series-key.
- Comext: hög paritet via separat Comext Action.
- Brå: reducerad paritet; officiell webb/statistikfil via Webbsökning i stället för generellt API.
- Beräkningar: Dataanalys används i stället för lokala projektskript.

## Begränsningar
Actions ersätter inte METADATA-GATE, DATA-GATE, METHOD-GATE eller PROVENANCE-GATE. Dataset- och dimensionskoder ska verifieras före datauttag.
