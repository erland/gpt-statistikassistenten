# Beräkningar och kombinerade mått

## Princip

Beräkningar sker först efter normalisering. Beräkningslagret får inte fylla luckor, anta periodmatchning eller konvertera definitioner implicit. Ett beräknat värde ska alltid kunna härledas till sina källobservationer.

## Stödda operationer i version 1

- **Absolut förändring:** `slutvärde - startvärde`.
- **Procentuell förändring:** `((slutvärde - startvärde) / startvärde) * 100`; basvärdet får inte vara 0.
- **Andel:** `(del / total) * 100`; del och total måste ha samma enhet och matchande period/geografi.
- **Indexering:** `(värde / basvärde) * basindex`; basperiod och basvärde måste finnas och basvärdet får inte vara 0.
- **Per-capita:** `(täljare / population) * skala`, normalt per 100 000; period och geografi måste matcha och nämnaren måste vara positiv.

## Matchningsregler

1. Tid och geografi matchas semantiskt, inte via källspecifika dimensions-ID:n.
2. Två källor med olika explicit frekvens får inte kombineras utan en separat, dokumenterad aggregation/transformation.
3. Saknad match för en period/geografi är ett stoppfel, inte en signal att använda närmaste period.
4. Saknade eller sekretesskyddade värden får inte tolkas som 0.
5. Status propagateras konservativt: ett beräknat värde kan inte få högre säkerhetsstatus än sina ingångsvärden.
6. För andelar måste enheterna vara identiska.
7. Per-capita kräver ett räknemått som täljare och ett verifierat populationsantal som nämnare.

## Proveniens

Ett beräkningsresultat lagrar formel, parametrar och de konkreta ingångsvärden som användes. Presentationen ska märka sådana värden som **beräknade**, aldrig som direkt källdata.

Normativt format finns i `schemas/calculation-result.schema.json`. Deterministisk referensimplementation finns i `scripts/calculation_engine.py`.
