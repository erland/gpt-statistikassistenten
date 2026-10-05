# {{GPT_NAME}} — OpenAI Plugin {{VERSION}}

Skills-first runtime för verifierbara frågor mot officiell statistik.

## Skills

{{SKILLS}}

## Runtimekrav

- Web/HTTP-åtkomst krävs för att verifiera aktuell metadata och officiell statistik.
- Structured data krävs för säkra uttag och metodkontroller.
- Code execution är rekommenderad för deterministiska planners, beräkningar, export och quality gates men får degraderas när hosten saknar kompatibel exekvering.
- Paketerade Python-scripts är resurser och kräver inte MCP-wrapper enbart för att användas.
- Simulera aldrig ett scriptresultat och markera alltid skillnaden mellan hämtad observation, egen beräkning och analys.
