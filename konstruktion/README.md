# Konstruktionsvorentwurf – Hauptvariante Stehen

Start: `00_PropBoard_Detail_Stehen.FCStd`, `Konstruktionsbericht.pdf` oder `Modelle_3D.html`.

Alle Dateien sind **Vorentwürfe ohne Fertigungs-/Flugfreigabe**. Die Hüllmaße beziehen sich auf die modellierte Stellung; insbesondere verbleiben in der Hauptbaugruppe nominell nur 2 mm Gesamtbreitenreserve. Schutz, Toleranzen, Verformung und vollständige Verbindungsteile sind damit nicht geschlossen.

Enthalten sind sieben räumliche FCStd-/STEP-Dateien und die native TechDraw-Datei `05_Referenzzeichnungen.FCStd`. `Referenzblaetter.pdf` zeigt vier A3-Blätter mit realen Teileprojektionen und nominalen Referenzmaßen. Diese Unterlagen sind keine freigegebenen Werkstattzeichnungen. Kritische Beispiele: 1,8 mm Restwand im Schlittenkörper und zu überarbeitende Randabstände der Akku-Rückhaltebügel.

Die Carbonrohre enthalten keine ausgelegte Lagenfolge. Die Führung enthält kein validiertes Magnet-/Motorsystem. Akku und Kabel sind Bauraumannahmen ohne Spannungs-, Strom-, Kapazitäts- oder Isolationsfreigabe. Sitz- und Liegedateien sind Ergonomiekontexte mit vereinfachter Fahrzeugausstattung. Personen sind Haltungsreferenzen, keine validierten anthropometrischen Modelle.

## Dateien bearbeiten

Native Grundkörper, Schnitte, Bohrungen und Platzierungen lassen sich in FreeCAD bearbeiten. Generierte Flügel-/Bahnflächen werden vollständig über die Skripte regeneriert. Die Tabellen in den Dateien dokumentieren Eingaben; sie sind keine vollständig verknüpfte parametrische Steuerung. Geänderte Maße benötigen erneute Anschluss-, Abstand- und Hüllmaßprüfungen.

Die Erzeugung überschreibt die von den Skripten erzeugten Dateien. Eigene Änderungen vor einer Regeneration separat speichern. Es werden keine Quell-CAD-Links zu externen Dokumenten benötigt. Die TechDraw-Vorlagen sind im FCStd-Archiv eingebettet; die SVG-Dateien liegen zusätzlich bei.

## Stücklisten

`Stueckliste_Instanzen.csv` enthält Betrachtungsdateien getrennt – niemals alle Dateien zu einem Fahrzeug aufsummieren. `Stueckliste_Hauptbaugruppe_Familien.csv` ist nur eine Gruppierung der Hauptbaugruppe nach Familien, keine bestellfertige Teileliste. `CFK_Zuschnitt_Referenz.csv` enthält nominale Zuschnitte ohne freigegebene Materialien, Toleranzen oder Zuschläge.

## Reproduktion

Im Repository-Verzeichnis mit dem FreeCAD-Python-Modul dieser Umgebung:

```sh
/usr/bin/python3 konstruktion/erstellen.py
/usr/bin/python3 konstruktion/detailauszug.py
/usr/bin/python3 konstruktion/zeichnungen_erstellen.py
/usr/bin/python3 konstruktion/geometrie_pruefen.py
python konstruktion/stuecklisten.py
/usr/bin/python3 konstruktion/modelle_exportieren.py
python konstruktion/viewer_erstellen.py
```

Der Viewer-Erzeuger nutzt die ebenfalls beigelegte getestete Renderer-Vorlage aus `bericht/viewer_erstellen.py`; die native Geometrie benötigt `cad/umlauf_kinematik.py`. Die hier verwendeten Bibliothekspfade gelten für FreeCAD 1.0 und `/usr/bin/python3` (Python 3.13). Viewer-/PDF-Helfer verwenden die andere verfügbare Python-Installation mit Playwright/PyPDF.

`browser_pruefen.py` prüft sieben WebGL-Ansichten, Drehen und Personenumschaltung. Es erzeugt außerdem die echten CAD-Screenshots für den Bericht. Die Browser-Systemaufrufe erfordern in dieser Cloud-Umgebung die Ausführung außerhalb der Befehls-Sandbox. Die Prüfung läuft ausschließlich lokal über einen temporären Loopback-Server. `zeichnungen_pdf.py` gibt die SVG-Referenzblätter als A3-PDF aus.

Der Konstruktionsbericht wird mit Pandoc/XeLaTeX aus `Konstruktionsbericht.md` erzeugt. Die `Ansicht_*.png` sind tatsächliche Ansichten triangulierter CAD-Geometrien. Eine neue CFD der Detailkonstruktion wurde nicht durchgeführt.
