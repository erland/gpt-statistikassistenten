# Kvalitets- och metodgates

Detta lager körs efter metadata-, data- och metodkontroller men före ett svar betraktas som färdigt.

## Blockerande fel

Ett färdigt svar ska stoppas om någon av följande situationer upptäcks:

- källorganisation eller dataset/statistikprodukt saknas,
- metadata är inte verifierad,
- hämtningstid saknas,
- observationer saknar dimension eller mått,
- `missing` eller `confidential` har ett numeriskt värde,
- tidsseriebrott saknar metodnotering,
- Brå:s statistik över anmälda brott saknar reservation om att anmälda brott inte är ett direkt mått på all faktisk brottslighet,
- per-capita saknar kontroll av period, geografi, positiv nämnare eller enhet,
- beräknade värden saknar formel eller ingångsvärden,
- presentationskällan saknar organisation, dataset, period, geografi eller mått,
- kausala formuleringar används utan separat verifierad evidens.

## Varningar

Preliminära observationer får användas, men ska markeras tydligt i metodnoteringen. Kvalitetsrapporten kan därför innehålla varning utan att blockera svaret.

## Princip för osäkerhet

Osäkerhet får aldrig döljas genom att fylla i ett sannolikt värde eller välja en kod från minnet. När en gate inte kan passeras ska assistenten antingen:

1. hämta/återverifiera metadata,
2. minska eller ändra uttaget,
3. be om minsta nödvändiga förtydligande, eller
4. tydligt redovisa att frågan inte kan besvaras med verifierat underlag.

## Kausalitet

Trend, samvariation och skillnader får beskrivas deskriptivt. Formuleringar som tillskriver en observerad förändring en orsak kräver separat verifierad evidens och ska inte härledas enbart från statistikserien.

Det maskinläsbara resultatet följer `schemas/quality-gate-report.schema.json`.
