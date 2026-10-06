# Env Finder

Findet `.env`-Dateien rekursiv über eine deutsche Flask-Weboberfläche mit Ordnerpicker und zeigt ihre Inhalte direkt unter den Treffern an. Das Standardverzeichnis wird ausschließlich in der lokalen `.env` konfiguriert.

## Standardverzeichnis konfigurieren

Anwendung und Starter lesen `DEFAULT_SEARCH_FOLDER` aus der `.env` im Projektverzeichnis:

```dotenv
DEFAULT_SEARCH_FOLDER=/pfad/zu/projekten
```

Das Beispiel oben ist ein Platzhalter. `.env` ist bereits mit dem lokalen Pfad eingerichtet und wird von Git ignoriert. `.env.example` enthält eine versionierbare Vorlage mit einem generischen Beispiel. Nach einem frischen Checkout zuerst `cp .env.example .env` ausführen und den Beispielpfad durch ein existierendes Verzeichnis ersetzen. Bei Änderungen an `.env` die Anwendung neu starten; im Docker-Betrieb den bisherigen Container stoppen und mit `python3.12 start.py --docker -d` neu erstellen.

Eine gesetzte Umgebungsvariable `DEFAULT_SEARCH_FOLDER` überschreibt den Wert aus der Datei; `--root` überschreibt beide. Anführungszeichen und Kommentare sind in der Konfiguration möglich. Relative Konfigurationspfade beziehen sich auf das Projektverzeichnis. Ohne konfigurierte Vorgabe ist ein explizites `--root` erforderlich. Der persönliche Standardpfad ist nicht im Python-Code enthalten. Docker erhält den konfigurierten Ordner als Mount; die lokale `.env` wird nicht ins Image kopiert.

## Docker starten

Voraussetzungen: Docker Desktop läuft; `python3.12` ist installiert.

```sh
python3.12 start.py --docker -d
```

Der Starter baut `env-finder:local`, startet den Container im Hintergrund und gibt die URL aus. Standard ist **http://127.0.0.1:5000**. Ist Port 5000 belegt, wird ein anderer freier Port verwendet. `python3.12 start.py` führt denselben Docker-Start aus.

Ein anderer Suchbereich mit einem vorausgewählten Unterordner:

```sh
python3.12 start.py --docker -d \
  --root /pfad/zu \
  --directory /pfad/zu/projekten
```

Der Picker kann innerhalb von `--root` navigieren. Docker erhält diesen Ordner als schreibgeschützten Bind-Mount. Der Host muss diesen Bereich für Docker freigegeben haben. Eingabefeld, Picker und Suchergebnisse verwenden die Originalpfade des Hosts. Ein anderer Host-Ordner erfordert einen Neustart mit entsprechendem `--root`.

Die Ausgabe enthält den individuellen Containernamen. Jeder Starteraufruf erzeugt einen neuen Container:

```sh
docker ps --filter ancestor=env-finder:local
docker logs CONTAINERNAME
docker stop CONTAINERNAME
docker rm CONTAINERNAME
```

Nach einem Docker-Neustart laufen nicht ausdrücklich gestoppte Container automatisch weiter (`unless-stopped`).

## Lokal mit Python 3.12 und venv

```sh
python3.12 start.py --local
```

Erstellt `.venv`, installiert Flask und Waitress und startet den Server. Mit `Ctrl+C` beenden. `--root`, `--directory` und `--port` funktionieren auch lokal. Die tatsächliche URL wird beim Start angezeigt.

Manuelle Einrichtung:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

`app.py` verwendet bei Bedarf die Umgebungsvariablen `ENV_FINDER_ROOT` und `ENV_FINDER_DEFAULT` für Suchbereich und Startverzeichnis; `ENV_FINDER_HOST_ROOT` steuert die angezeigte Host-Pfadwurzel im Container.

## Verwendung

1. Angezeigte URL im Browser öffnen.
2. „Ordner auswählen“ anklicken, einen Ordner öffnen und „Diesen Ordner verwenden“ wählen. Alternativ einen absoluten Serverpfad oder einen Pfad relativ zum freigegebenen Suchbereich eingeben.
3. Bei Bedarf „Auch .env.* finden“ aktivieren.
4. „Dateien finden“ anklicken. Unter jedem Treffer werden die Dateiinhalte automatisch angezeigt; mit „Dateiinhalt“ lässt sich der Textbereich einklappen. Bei Bedarf die gefundenen Pfade kopieren.

Dateien werden ausschließlich gelesen. Die Inhaltsanzeige ist auf 1 MiB pro Datei begrenzt; bei größeren Dateien erscheint ein Hinweis. UTF-8-BOM wird entfernt, ungültige UTF-8-Zeichen werden mit Hinweis ersetzt. Inhalte werden als reiner Text dargestellt. Leere Dateien und Lesefehler werden beim jeweiligen Treffer angezeigt. Das Nachladen läuft mit höchstens vier gleichzeitigen Inhaltsanfragen.

Alle Unterverzeichnisse werden durchsucht, einschließlich versteckter Ordner. Symbolische Links werden übersprungen. Die Suche läuft standardmäßig ohne Zeitlimit; bei großen Verzeichnissen kann sie mehrere Minuten dauern. Optional lässt sie sich mit „Suche auf 2 Minuten begrenzen“ auf 120 Sekunden begrenzen. Nicht lesbare Dateien/Ordner sowie eine Begrenzung auf 120 Sekunden bzw. 10.000 Treffer werden angezeigt. Eine begrenzte Suche liefert ein gekennzeichnetes Teilergebnis.

## Tests und Projektdokumente

```sh
.venv/bin/python -m unittest discover -s tests -v
```

`SPEC.md` enthält Anforderungen und Abnahmekriterien. `CLAUDE.md` enthält das fortlaufende Nutzerprompt-Protokoll. `AGENTS.md` und `CLAUDE.md` weisen Coding-Agenten an, neue Projektprompts und geänderte Anforderungen bei jeder weiteren Bearbeitung einzutragen.

Technische Referenzen: [Flask-Installation](https://flask.palletsprojects.com/en/stable/installation/), [Docker-Container starten](https://docs.docker.com/reference/cli/docker/container/run/), [Docker Bind-Mounts](https://docs.docker.com/engine/storage/bind-mounts/).

## Lizenz

Das Projekt steht unter der [MIT-Lizenz](LICENSE).
