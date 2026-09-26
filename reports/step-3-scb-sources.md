# Steg 3 – verifierade SCB-källfakta

Verifierat 2026-09-26 mot SCB:s officiella dokumentation och Swagger:

- PxWebApi v2 lanserades i Statistikdatabasen oktober 2025.
- API-root för Statistikdatabasen är `https://statistikdatabasen.scb.se/api/v2`.
- Centrala endpoints: `GET /tables`, `GET /tables/{id}`, `GET /tables/{id}/metadata`, `GET|POST /tables/{id}/data`.
- `GET /tables` har serversökning och pagination; wildcard kan användas i söktext på SCB:s v2-server.
- SCB anger högst 150 000 dataceller per uttag och 30 anrop per 10 sekunder per IP-adress.
- Obligatoriska variabler måste ingå i urvalet; därför måste metadata verifieras före datauttag.
- En känd 2026-begränsning i fristående `/codelists/{id}` gäller vissa ID:n med specialtecken; metadata/selection-vägen fungerar för de rapporterade fallen.

Officiella referenser:
- https://www.scb.se/vara-tjanster/oppna-data/pxwebapi/
- https://www.scb.se/vara-tjanster/oppna-data/pxwebapi/pxwebapi-v2/
- https://statistikdatabasen.scb.se/api/v2/index.html
- https://github.com/statisticssweden/PxApiSpecs/blob/master/PxAPI-2.yml
