# Spezifikation: Env Finder

Stand: 2026-10-06

## Ziel

Eine lokale Webanwendung findet `.env`-Dateien in einem vom Nutzer ausgewählten Verzeichnis einschließlich seiner Unterverzeichnisse. Die Umsetzung erfolgt in Python 3.12 mit Flask und einer virtuellen Umgebung. Ein Docker-Container lässt sich standardmäßig im Hintergrund starten.

## Anforderungen

1. Python 3.12 verwenden; lokale Abhängigkeiten liegen in `.venv`. Auch das Docker-Image nutzt Python 3.12 und eine venv.
2. Flask stellt eine deutschsprachige Browseroberfläche bereit. Waitress betreibt den Server ohne Debug-Modus.
3. Das Standardverzeichnis wird mit `DEFAULT_SEARCH_FOLDER` in der `.env` neben den Python-Dateien konfiguriert. Ausschließlich `.env` enthält den persönlichen Standardpfad; der bestehende Wert bleibt unverändert. `.env.example` enthält das generische Beispiel `DEFAULT_SEARCH_FOLDER=/pfad/zu/projekten`. Auch Dokumentation und frühere Prompt-Einträge enthalten den persönlichen Pfad nicht. Anwendung und Starter verwenden denselben Loader in `settings.py`, unabhängig vom aktuellen Arbeitsverzeichnis. Eine gesetzte Umgebungsvariable `DEFAULT_SEARCH_FOLDER` hat Vorrang vor der Datei. Explizite Pfadargumente bzw. `ENV_FINDER_ROOT` können den konfigurierten Standard überschreiben. Ein fehlender oder leerer Wert ergibt ohne expliziten Suchbereich einen verständlichen Fehler. `.env` wird durch `.gitignore` ausgeschlossen; `.env.example` bleibt versionierbar. Die Konfiguration wird beim Start eingelesen; Änderungen erfordern einen Neustart. Docker erhält den daraus bestimmten Host-Suchbereich weiterhin als schreibgeschützten Mount, während `.env` nicht ins Image kopiert wird.
4. Ein browserbasierter Verzeichnispicker zeigt Unterordner, erlaubt Aufwärtsnavigation und die Auswahl des aktuellen Ordners. Alternativ kann ein Pfad eingegeben werden. Ein nativer Betriebssystemdialog ist nicht erforderlich; der Picker muss im Docker-Betrieb funktionieren.
5. Der Suchbereich entspricht standardmäßig dem Standardverzeichnis. Mit `--root` kann beim Start ein anderer Bereich freigegeben werden. `--directory` wählt einen Startordner innerhalb dieses Bereichs. Der Picker kann den freigegebenen Bereich nicht verlassen.
6. Die Suche ist rekursiv und findet standardmäßig Dateien mit exakt dem Namen `.env`. Die Option „Auch .env.* finden“ schließt Varianten wie `.env.local` und `.env.example` ein. Versteckte Unterverzeichnisse werden ebenfalls durchsucht.
7. Ergebnisse zeigen Name, vollständigen Host-Dateipfad, Dateigröße und Änderungszeit. Dateipfade lassen sich kopieren. Die Inhalte jeder gefundenen Datei werden automatisch direkt unter dem Treffer in einem zunächst geöffneten, einklappbaren Textbereich dargestellt. Bis zu vier Inhaltsanfragen laufen gleichzeitig. `/api/content` darf ausschließlich reguläre `.env`-/`.env.*`-Dateien innerhalb des freigegebenen Bereichs öffnen und lehnt symbolische Links ab. Pro Datei werden bis zu 1 MiB als UTF-8-Text dargestellt; Begrenzungen und ersetzte ungültige Zeichen werden angezeigt. Inhalte werden als Text dargestellt, nicht als HTML ausgeführt, und nicht in Logs oder Projektdokumenten gespeichert.
8. Symbolische Links werden nicht verfolgt. Fehler beim Zugriff werden als Hinweis gemeldet. Suchergebnisse werden nach dem relativen Pfad sortiert.
9. Standardmäßig läuft die Suche ohne Zeitlimit. Das optionale Kontrollkästchen „Suche auf 2 Minuten begrenzen“ begrenzt eine Suche auf 120 Sekunden. Die Trefferzahl ist auf 10.000 begrenzt. Bei jeder Begrenzung wird das Ergebnis ausdrücklich als Teilergebnis gekennzeichnet.
10. Port 5000 ist bevorzugt. Ist er belegt, verwendet die Anwendung automatisch einen freien Port und gibt die tatsächlich erreichbare URL aus. Der lokale Start reserviert den Port vor dem Serverstart. Docker validiert den Port beim Start erneut und der Starter wiederholt bei einer Portkollision bis zu fünfmal.
11. `python3.12 start.py` und `python3.12 start.py --docker -d` bauen das Docker-Image und starten es mit `docker run -d`. Der freigegebene Host-Ordner wird schreibgeschützt nach `/scan` eingebunden. Der Host-Port ist an `127.0.0.1` gebunden. Die Weboberfläche zeigt originale Host-Pfade, auch im Eingabefeld und im Picker; die API übersetzt diese in Containerpfade.
12. `python3.12 start.py --local` erstellt bei Bedarf `.venv`, installiert Abhängigkeiten und startet den Server im Vordergrund. `Ctrl+C` beendet den lokalen Server.
13. Der Docker-Starter prüft die Bereitschaft des Webservers und gibt URL, Containername, Suchbereich und Stoppbefehl aus. Ein nicht erreichbarer Docker-Dienst führt zu einer verständlichen Fehlermeldung.
14. Neue Nutzerprompts zum Projekt werden durch den bearbeitenden Coding-Agenten fortlaufend in `CLAUDE.md` ergänzt. Die dafür verbindlichen Projektanweisungen stehen in `CLAUDE.md` und `AGENTS.md`. Die Anwendung selbst erhält keine Chatprompts und protokolliert keine Browser-Suchanfragen als Prompts.
15. `README.md` ist die einzige README-Datei des Projekts und enthält eine kurze englische App-Beschreibung sowie Voraussetzungen, Installation/Konfiguration, lokale und Docker-Startbefehle, Stoppbefehle und die grundlegende Bedienung. Beispiele verwenden ausschließlich generische Pfade.
16. Das Projekt verwendet die MIT-Lizenz. `LICENSE` enthält den vollständigen Lizenztext mit Copyright 2026 Peter Strössler; `README.md` verweist darauf.
17. `README.md` bindet `env-finder.png` als Demo-Screenshot mit einem relativen Bildpfad ein.

## Abnahme

- `.env` im Startordner und in verschachtelten Unterordnern werden gefunden.
- `.env.*` wird ausschließlich bei aktivierter Option gefunden.
- Die Inhalte gefundener Dateien werden automatisch in der Oberfläche angezeigt und lassen sich einklappen. Leere Dateien, Lesefehler und eine begrenzte Inhaltsanzeige werden verständlich dargestellt.
- Die Inhalts-API weist fremde Dateitypen, symbolische Links und Pfade außerhalb des Suchbereichs zurück; HTML-Zeichen in Dateiinhalten werden als Text angezeigt.
- Ordnernavigation und Pfadeingabe funktionieren innerhalb des Suchbereichs; Pfade außerhalb werden zurückgewiesen.
- Symbolische Links werden übersprungen.
- Ein belegter Port 5000 verhindert den Start nicht.
- Der Container läuft im Hintergrund und `/health` antwortet mit `{"status":"ok"}`.
- Python-3.12-venv, README, `CLAUDE.md` und diese Spezifikation sind vorhanden.
- `.env` und `.env.example` konfigurieren `DEFAULT_SEARCH_FOLDER`; der Python-Code enthält keinen persönlichen Standardpfad, Git ignoriert `.env` und lässt `.env.example` zu.
