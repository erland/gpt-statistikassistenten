# Utvecklingsworkflow

Den explicita state machine som deklareras i `gpt-project.yaml` styr **utveckling och underhåll av GPT-projektet**, inte användarens enskilda statistikfrågor. Statistikassistentens runtime fortsätter att använda det kortare gated-flödet i canonical instruktionen.

Ett utvecklingssteg får bara markeras klart efter deterministisk validering. Vid fel går arbetet tillbaka till implementation/validation innan status eller paket uppdateras. `project-status.yaml` är auktoritativ projektstatus.
