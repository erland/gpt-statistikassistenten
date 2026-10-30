# Migrering till modulära Skills (GPT Byggaren 1.6.33)

## Beslut
Tre sammanhållna ansvar med olika aktiveringsvillkor: `statistikkallor` (upptäckt och dataåtkomst), `statistikkvalitet` (metod, beräkning och gates), `statistikpresentation` (slutsvar och export). Gemensamt arbetsflöde och kärnregler i `canonical/core.md`.

## Spårbarhet mot tidigare instruktion
- `assistant/instructions.md` är bevarad oförändrad som ursprungligt beteendekontrakt.
- Identitet och syfte, kärnregler, arbetsflöde och begränsningar → `canonical/core.md`.
- Källval och METADATA-GATE inklusive alla källspecifika regler → `canonical/skills/statistikkallor/behavior.md`.
- DATA-, METHOD-, PROVENANCE- och QUALITY-GATE → `canonical/skills/statistikkvalitet/behavior.md`.
- Svar och export samt historiska Custom GPT-regler → `canonical/skills/statistikpresentation/behavior.md`.

## Resurser och begränsningar
Befintliga Python-verktyg, source registry och schemas behålls intakta. Resursisolering på Skill-nivå är **inte** aktiverad utan detaljerad beroendeinventering; skillresurser måste fortfarande verifieras i byggpaketen. Den historiska Custom GPT-sektionen är endast dokumentation, inte ett sjätte distributionsmål.

## Verifiering som återstår
Kör GPT Byggarens kanoniska lint, build och validate för samtliga fem runtimepaket och jämför genererade skillinstruktioner med ursprungligt beteende. CI PASS är inte funktionell runtimeparitet. Om validatorn rapporterar fel får migrationen inte mergas.
