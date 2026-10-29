# Vergleichsbericht PropBoard

Start: **Vergleichsbericht.pdf** oder **Vergleichsbericht.html**. Die HTML-Berichtsdatei enthält ihre Abbildungen eingebettet. **Modelle_3D.html** enthält beide aus FreeCAD abgeleiteten Geometrien und funktioniert mit WebGL ohne Internetverbindung. Native FCStd- und STEP-Dateien liegen im Gesamtpaket in ihren ursprünglichen Unterordnern. ZIP zuerst entpacken, damit relative Dateiverweise funktionieren.

Der Bericht wertet vorhandene CFD-Voruntersuchungen aus und ergänzt analytische Referenzlastfälle. Eine realmaßstäbliche 3D-CFD und reale Hardwaremessungen wurden nicht durchgeführt. Ergebnisse, Rechnungen, Hypothesen und offene Nachweise sind getrennt gekennzeichnet.

PDF und HTML erzeugen, im Repository-Verzeichnis:

```sh
python bericht/lastfaelle.py
/usr/bin/python3 bericht/modelle_exportieren.py
python bericht/viewer_erstellen.py
pandoc bericht/Vergleichsbericht.md --from markdown --to html5 --standalone --embed-resources --toc --resource-path=bericht:. -o bericht/Vergleichsbericht.html
XDG_CACHE_HOME=/tmp/propboard-cache pandoc bericht/Vergleichsbericht.md --pdf-engine=xelatex --toc --resource-path=bericht:. -V mainfont='DejaVu Sans' -V monofont='DejaVu Sans Mono' -V geometry:margin=20mm -V fontsize=10pt -V colorlinks=true -o bericht/Vergleichsbericht.pdf
```

Die vorhandene 3D_Ansicht.png ist ein Screenshot der Browserprüfung. `browser_pruefen.py` überprüft WebGL, interaktives Drehen und eingebettete Berichtsbilder über einen temporären, nur an 127.0.0.1 gebundenen Testserver. Browser-Systemaufrufe benötigen in dieser Cloud-Umgebung eine Ausführung außerhalb der Befehls-Sandbox; die Prüfung wurde dort erfolgreich ausgeführt. Es wird kein externer Dienst verwendet und kein Server für den Nutzer veröffentlicht.

Die PDF wurde auf Lesbarkeit ausgewählter Tabellen-/Textseiten und extrahierbare Schlüsselwerte geprüft. Die ZIP-Integrität und Dateiprüfsummen werden beim Packen geprüft. Diese Darstellungsprüfungen sind keine Validierung der Aerodynamik oder des Fluggeräts.
