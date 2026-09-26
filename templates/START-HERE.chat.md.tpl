# {{GPT_NAME}} – Chat ZIP

Detta är den portabla ChatGPT Chat-distributionen för **{{GPT_NAME}}**.

## Användning

Bifoga ZIP-filen i en ChatGPT-konversation och be ChatGPT använda den som GPT-kontext. Assistentens canonical instruktion finns i `assistant/instructions.md`.

## Runtimeinnehåll

- `assistant/instructions.md` – kärnbeteende och statistikgates.
- `assistant/runtime-contract.json` – kompilerad capability-, artifact-, state- och tool-snapshot.
- `schemas/` – kontrakt för statistik, adaptrar, beräkningar, presentation och kvalitet.
- `scripts/` – deterministiska runtimeverktyg för källval, adapters, beräkningar, export och quality gate.

Utvecklingsplan, tester och projektstatus ingår inte i Chat-runtime.

## Version

{{VERSION}}
