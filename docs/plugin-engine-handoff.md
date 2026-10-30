# Plugin ↔ Statistikassistenten Engine – offlinekontrakt (steg 4)

## Resultat

Plugin ZIP innehåller `skills/statistikassistenten/scripts/` och källregistret som Skill-resurser. Den separat levererade Engine ZIP innehåller samma statistikskript, ett fristående självtest samt `engine-package.json` med SHA-256 per resurs och Pythonberoendet `PyYAML>=6.0`. Ingen automatisk Engine-installation eller exekveringsrätt i OpenAI Plugin kan härledas enbart av att dessa filer finns.

## Kontroller

Kör `python scripts/verify_plugin_engine_handoff.py --plugin dist/statistikassistenten-plugin-<version>.zip --engine dist/statistikassistenten-engine-<version>.zip` efter bygg. Testet kontrollerar identitet, säker filstruktur, fullständig resursinventering, SHA-256, byte-identitet för resurser som delas mellan Skill och Engine samt riktigt självtest från extraherad Engine i isolerad temporär katalog. Negativt regressionstest kräver att manipulerad resurs avvisas. Kontroll ingår i CI och release innan uppladdning.

## Exekveringsgräns och fallback

- **När hosten erbjuder Python och filåtkomst:** verifiera Engine ZIP från exakt motsvarande release/version, granska beroendena, kör självtest och därefter enbart uttryckligen begärda skript. Motorn ska inte installera eller köra okänt innehåll automatiskt.
- **När Python saknas:** använd officiell webb/API och strukturerade observationer om dessa finns och uppfyller metadata-, metod-, data- och provenienskraven. Skriptresultat får inte imiteras. Beräkningar eller exporter som inte kan verifieras ska markeras otillgängliga; inga fabricerade värden.
- **När webb/API eller strukturerade data saknas:** markera datainsamling/verifiering blockerad snarare än att hävda funktionell paritet.
- **När självtest eller kontrollsummor misslyckas:** exekvera inte Engine. Återhämta verifierad artefakt; degradera bara i de delar där ett annat tillförlitligt arbetsflöde faktiskt finns.

## Testgräns

Kontrollen bevisar lokal Python-körning och artefaktparitet, **inte** faktisk host-installation i OpenAI Plugin, webb-API-behörighet, installerade beroenden hos hosten, tillgänglighet för bilagor eller körning i andra runtimes. Dessa kräver separata värdtester.
