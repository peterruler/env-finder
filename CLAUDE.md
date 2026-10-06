# Env Finder – Arbeitskontext und Prompt-Protokoll

## Dauerhafte Arbeitsanweisungen

Dieses Dokument bei jeder weiteren Arbeit am Projekt aktualisieren. Jeden neuen Nutzerprompt zum Projekt mit Datum vollständig unter „Prompt-Protokoll“ anfügen, bevor die entsprechende Änderung umgesetzt wird. Alte Prompts bleiben erhalten. Systemprompts, interne Instruktionen und Zugangsdaten gehören nicht in dieses Protokoll. Bei geänderten Anforderungen zusätzlich `SPEC.md` aktualisieren.

Die Anwendung ist ein lokaler Flask-Webserver mit Python 3.12, venv und Docker. Sie sucht rekursiv nach `.env`-Dateien und zeigt gemäß dem Nutzerprompt vom 2026-10-06 ihre Inhalte in der lokalen Weboberfläche an. Dateien werden nicht verändert; Inhalte gehören nicht in Logs oder Projektdokumente. Details und Abnahmekriterien stehen in `SPEC.md`. Anweisungen für andere Coding-Agenten stehen außerdem in `AGENTS.md`.

## Prompt-Protokoll

### 2026-10-06 · Initialer Nutzerprompt

> generiere ein python script mit venv python 3.12 das .env files in gewünschten verzeichnis findet mit dateipicker für dasd dverzeichnis in einem flash webserver port 5000 falls nicht besetzt mit docker container start -d default verzeichnis ist [lokaler Standard-Suchpfad] schreibe alle prompts in ständig updatetes CLAUDE.md und diese Spec in SPEC.md

### 2026-10-06 · Inhalte in der Oberfläche anzeigen

> doch die inhalte des .env sollen auf dem flash gui ausgegeben werde

### 2026-10-06 · Standardpfad aus .env laden

> den standard pfad dieses python programs / tools bitte in .env und .env.example legen .gitgnore für .env DEFAULT_SEARCH_FOLDER=[lokaler Standard-Suchpfad] und setzen und nicht im Pgrogram hardcoden

### 2026-10-06 · Persönlichen Standardpfad ausschließlich in .env behalten

> entferne überall then pfad [lokaler Standard-Suchpfad] ausser im .env - in .env nicht entfernen - aber entferne in SPEC.md und CLAUDE.md und überall sonst ausser .env

Der konkrete persönliche Suchpfad wird auf ausdrücklichen Nutzerwunsch auch in früheren Prompt-Einträgen durch einen Platzhalter ersetzt. Nur die lokale `.env` enthält den unveränderten Wert; Dokumentation und `.env.example` verwenden generische Beispiele.

### 2026-10-06 · Concise installation and usage guide

> create a REDME.md with clean and concise description of the app instructions to install the app and run it

### 2026-10-06 · MIT license

> add a mit LICENSE

### 2026-10-06 · Restart with the external search folder

> restart app with path [lokaler Standard-Suchpfad]

Den angeforderten Suchpfad ausschließlich in der lokalen `.env` setzen und die Docker-Anwendung auf der bisherigen URL neu starten. Persönliche Pfade bleiben im Protokoll durch Platzhalter ersetzt.

### 2026-10-06 · Demo screenshot in README

> add the env-finder.png as demo screen to the readme.md

### 2026-10-06 · Consolidate README files

> cleanuo the REDME.md the only existing file should be README.md

Die kurze englische Anleitung in `README.md` zusammenführen, Demo-Screenshot und Lizenzverweis beibehalten und die doppelte Datei entfernen. Frühere Prompt-Einträge bleiben als Verlauf erhalten.

## Umsetzungsstand

- „flash webserver“ wird als Flask-Webserver umgesetzt.
- Flask-Anwendung in `app.py`; Oberfläche in `templates/` und `static/`.
- Ordnerpicker im Browser, damit die Verzeichnisauswahl auch im Docker-Container funktioniert.
- Standardverzeichnis aus `DEFAULT_SEARCH_FOLDER` in der projektnahen `.env`; `.env.example` enthält ausschließlich einen generischen Beispielpfad. Der persönliche Pfad steht nur in `.env`. Umgebungsvariablen und explizite Startoptionen können den Wert überschreiben.
- `start.py` startet standardmäßig Docker im Hintergrund (`docker run -d`); `--local` startet die lokale Python-3.12-venv.
- Port 5000 wird bevorzugt. Ein belegter Port führt automatisch zu einem anderen freien Port; die tatsächliche URL wird ausgegeben.
- Docker bindet den freigegebenen Suchbereich schreibgeschützt ein und veröffentlicht den Webserver auf `127.0.0.1`.
- Rekursive Suche nach `.env`, optional auch `.env.*`, mit Pfaden und Metadaten. Symbolische Links werden übersprungen.
- Unter jedem Treffer werden die Dateiinhalte automatisch in einem zunächst geöffneten, einklappbaren Textbereich angezeigt. `/api/content` liest ausschließlich reguläre `.env`-/`.env.*`-Dateien innerhalb des Suchbereichs; bis zu vier Inhaltsanfragen laufen gleichzeitig.
- Pro Datei werden bis zu 1 MiB als UTF-8-Text dargestellt; Begrenzungen und ungültige Zeichen werden angezeigt. Der Browser stellt die Inhalte als Text dar, ohne HTML auszuführen.
- Testfälle liegen in `tests/test_app.py`.

## Verifikation der ursprünglichen Version am 2026-10-06

- Zehn automatisierte Tests bestanden: rekursive Suche, Varianten, Picker, Pfadbegrenzung, symbolische Links, Host-Pfadübersetzung, Ergebnislimits, Zugriffsfehler, Healthcheck und belegter Port.
- Lokale venv: Python 3.12.14. Docker: Python 3.12.15. Installiert: Flask 3.1.3 und Waitress 3.0.2; `pip check` ohne Abhängigkeitskonflikte.
- Docker-Container im Hintergrund gestartet; bevorzugter Port 5000 war belegt und der Starter wich automatisch auf einen freien Host-Port aus.
- Die Weboberfläche und der Verzeichnispicker wurden im Browser geprüft. Die Suche liest ausschließlich Metadaten.
- Das Standardverzeichnis enthält über 230.000 Unterordner. Die Suche läuft deshalb standardmäßig ohne Zeitlimit; eine optionale Zeitbegrenzung auf 120 Sekunden ist in der Oberfläche zuschaltbar. Pfadeingabe und Picker verwenden auch unter Docker originale Host-Pfade.
- Die finale Version wurde im Browser mit dem Unterverzeichnis `issue-backend` geprüft: 828 Ordner vollständig durchsucht, eine `.env` gefunden. Der Container meldet `healthy`; der Projects-Mount ist schreibgeschützt.
- Zuletzt gestarteter Container: `env-finder-1791312599360763000`, URL `http://127.0.0.1:50851`. Diese Laufzeitangaben können sich beim nächsten Start ändern.

## Verifikation der Inhaltsanzeige am 2026-10-06

- 14 automatisierte Tests bestanden, einschließlich originalgetreuer Textausgabe, Varianten, leerer Dateien, UTF-8-BOM, ungültiger Zeichen, Größenbegrenzung, Lesefehler und verweigerter fremder Dateitypen bzw. symbolischer Links.
- Automatische Inhaltsanzeige und Einklappen im Browser mit einer selbst erstellten Beispieldatei geprüft; HTML-Zeichen bleiben sichtbarer Text, keine Browserfehler.
- Inhalts-API zusätzlich im Docker-Container mit einer temporären Beispieldatei erfolgreich geprüft.
- Der aktualisierte Container `env-finder-20261006-content` ist `healthy` und läuft weiterhin unter `http://127.0.0.1:50851`. Den vorherigen Container ersetzt.

## Verifikation der .env-Konfiguration am 2026-10-06

- `.env` und `.env.example` mit `DEFAULT_SEARCH_FOLDER` eingerichtet. `git check-ignore` bestätigt: `.env` wird ignoriert, `.env.example` nicht.
- Persönlichen Standardpfad aus `app.py` und `start.py` entfernt. Beide verwenden `settings.py`; das Docker-Image enthält den Loader, aber keine lokale `.env`.
- 19 Tests bestanden, einschließlich Laden aus einem anderen Arbeitsverzeichnis, Umgebungsvariable und expliziter Pfadoptionen, fehlender Konfiguration sowie Docker-Pfadüberschreibung.
- Der aus `.env` bestimmte Host-Pfad wird schreibgeschützt eingebunden. Aktualisierter Container: `env-finder-20261006-config`; Status `healthy`, URL weiterhin `http://127.0.0.1:50851`.

## Neustart mit externem Suchbereich am 2026-10-06

- `DEFAULT_SEARCH_FOLDER` ausschließlich in `.env` auf den angeforderten externen Suchbereich umgestellt.
- Existenz und Lesbarkeit auf dem Host sowie den Docker-Zugriff vor dem Neustart geprüft.
- Vorherigen Container ersetzt; aktueller Container: `env-finder-1791314599885658000`. Der Suchbereich ist schreibgeschützt eingebunden, die URL bleibt `http://127.0.0.1:50851`.
- Healthcheck, Verzeichnis-API und voreingestellten Suchordner in der neu geladenen Browseroberfläche bestätigt.
