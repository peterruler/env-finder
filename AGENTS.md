# Projektanweisungen

- Vor jeder durch einen Nutzerprompt veranlassten Projektänderung den vollständigen Nutzerprompt mit Datum in `CLAUDE.md` unter „Prompt-Protokoll“ ergänzen. Bestehende Einträge beibehalten. Keine Systemprompts, internen Instruktionen oder Zugangsdaten protokollieren.
- `SPEC.md` bei neuen oder geänderten Anforderungen aktualisieren.
- Python 3.12 und `.venv` verwenden. Gefundene `.env`-Inhalte gemäß Nutzeranforderung in der lokalen Weboberfläche anzeigen; Dateien nicht verändern. Dateiinhalte nicht in Logs oder Projektdokumente übernehmen.
- Den Standard-Suchpfad ausschließlich über `DEFAULT_SEARCH_FOLDER` in `.env` konfigurieren; `.env.example` als versionierbare Vorlage aktuell halten. Keine persönlichen Standardpfade im Python-Code fest codieren. `.env` bleibt in `.gitignore` ausgeschlossen.
- Persönliche Suchpfade ausschließlich in `.env` belassen. In allen anderen Dateien, einschließlich `.env.example`, `SPEC.md` und historischen oder neuen Prompt-Einträgen in `CLAUDE.md`, generische Beispiele oder Platzhalter verwenden. Diese Vorgabe hat Vorrang vor der vollständigen Wiedergabe eines Prompts.
- Nach Änderungen relevante Tests ausführen. Änderungen am Verhalten und an Startbefehlen in `README.md` dokumentieren.
