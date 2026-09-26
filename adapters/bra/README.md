# Brå-adapter

Brå-adaptern hanterar i första versionen **statistik över anmälda brott**. Den bygger medvetet inte på ett påhittat generellt API-kontrakt. Runtime ska i stället använda Brå:s officiella statistiktjänst eller publicerade filer och skapa en verifierad metadata-snapshot som adaptern kan validera.

## Officiella ingångar

- Statistiktjänst: `https://statistik.bra.se/solwebb/action/start`
- Hjälp/metod: `https://statistik.bra.se/solwebb/action/hjalp?kod=h_hjalp_anv`

## Flöde

1. Identifiera att frågan gäller **anmälda brott**. Andra statistikprodukter får inte mappas hit av bekvämlighet.
2. Hämta aktuell metadata från Brå:s officiella tjänst eller publicerade tabell/fil: brottstyp eller brottskod, geografi, period, enhet och preliminär/slutlig status.
3. Normalisera metadata till en snapshot enligt `schemas/bra-adapter.schema.json`.
4. Validera användarens urval mot snapshoten. Gissa aldrig brottskod, områdeskod eller tillgänglig period.
5. Begränsa uttaget till högst 10 000 dataceller, vilket motsvarar Brå-tjänstens publicerade gräns.
6. Respektera sekretessrelaterade begränsningar för korta perioder och små geografier; detaljerade brott/koder kan saknas där.
7. Hämta resultatet från den officiella tjänsten eller en publicerad fil och normalisera därefter till den gemensamma statistikmodellen.

## Viktiga tolkningsregler

- Anmälda brott är brott som registrerats hos polis, tull, åklagare eller Ekobrottsmyndigheten; det är inte samma sak som faktisk total brottslighet eller självrapporterad utsatthet.
- Statistik kan vara preliminär eller slutlig. Status ska redovisas när den är relevant.
- Brå:s databas uppdateras kontinuerligt; ett nytt uttag kan därför avvika något från tidigare publicerade värden.
- Geografin har förändrats över tid. Län används i äldre serier medan polisregioner används från 2015 för motsvarande regional redovisning; sådana serier ska inte sammanfogas naivt.
- Kommunstatistik finns från 1996, medan landnivå finns från 1975 enligt Brå:s nuvarande tjänstinformation.

## Fallbackstrategi

Om runtime inte kan göra ett maskinellt uttag ska assistenten inte simulera ett API-anrop. Den får i stället använda en officiell publicerad Excel-/tabellfil, eller redovisa att ett verifierat uttag inte kan göras i aktuell runtime. Proveniens ska alltid peka tillbaka till Brå.
