# A/B – P14-Vierblatt und klassische Rahmen

[Entwicklungsbericht PDF](Entwicklungsbericht.pdf) · [HTML-Bericht](Entwicklungsbericht.html) · [Interaktive CAD-Ansicht](Modelle.html) · [Gesamtpaket](Entwicklung_AB.zip)

Neue, isolierte Entwürfe mit Rahmen, Rotoren, Schutzringen, Gittern, Deck,
Batteriebauräumen und Kufen. Die ursprüngliche P14-Konstruktion und die erste
Antriebsstudie bleiben erhalten.

| Weitergeführte Variante | Native FreeCAD-Datei | Rahmen-STEP |
| --- | --- | --- |
| P14, 4 Blätter, Radius 750 mm | [P14 R750](Ausgabe/P14_R750/P14_R750.FCStd) | [STEP](Ausgabe/P14_R750/P14_R750_Rahmen.step) |
| P14, 4 Blätter, Radius 800 mm | [P14 R800](Ausgabe/P14_R800/P14_R800.FCStd) | [STEP](Ausgabe/P14_R800/P14_R800_Rahmen.step) |
| Quadrokopter, 3 Blätter, Radius 380 mm | [Quad R380](Ausgabe/QUAD_R380/QUAD_R380.FCStd) | [STEP](Ausgabe/QUAD_R380/QUAD_R380_Rahmen.step) |
| Hexakopter, 4 Blätter, Radius 265 mm | [Hexa R265 B4](Ausgabe/HEXA_R265_B4/HEXA_R265_B4.FCStd) | [STEP](Ausgabe/HEXA_R265_B4/HEXA_R265_B4_Rahmen.step) |

Die nativen P14-Dateien enthalten den vollständigen übernommenen Kern und die
neuen Rahmenanteile. Die P14-Rahmen-STEPs enthalten ausschließlich neue Komponenten.
Die klassischen STEP-Dateien enthalten die vollständigen modellierten Entwürfe.
Die nativen Dateien bestehen aus einzeln benannten `Part::Feature`-Körpern mit
Material-/Massen-/Nachweisangaben; sie besitzen keine vollständige PartDesign-Historie.
Parameteränderungen erfolgen reproduzierbar über JSON und Generator.

Die Vergleichsfälle [Quad R400](Ausgabe/QUAD_R400/QUAD_R400.FCStd),
[Hexa R275](Ausgabe/HEXA_R275/HEXA_R275.FCStd) und
[Hexa R265 mit 3 Blättern](Ausgabe/HEXA_R265/HEXA_R265.FCStd)
dokumentieren die Gründe für kleinere Radien beziehungsweise mehr Blätter.

## Nachweisgrenzen

Die Massen der neuen Struktur- und Schutzteile stammen aus CAD-Volumen und
angenommenen Dichten. Klassische Motoren, Blattschalen, Akku und Elektronik besitzen
ausgewiesene Massenannahmen. Rohrknoten, CFK-Klemmen, OEM-Anschlüsse, vollständige
Verbindungsmittel und Laminat-/Ermüdungsnachweise sind offen. Die erfasste Masse ist
keine abschließend gewogene Fahrzeugmasse.

Rotorfreiraum: stationärer Hüllraum mit Pitchreserve, 15 mm angenommener
Verformung und 3 mm Toleranz. Das beweist keine vollständige aeroelastische
Bewegungsfreiheit. Schutzgitter sind kein bestätigtes Containment. Die Aerorechnung
enthält noch keine zusätzlichen Strömungsverluste von Gitter, Deck und Akkus.

Für keine Variante liegen vollständige Motor-/ESC-/Rotor-/Batterie-Dauernachweise
vor. Das 15-Minuten-Ziel wird mit der angenommenen 12-kg-Batterie verfehlt.
Die Motor-Ausfallrechnung ist ein idealisierter statischer Kraft-/Momentenscreen,
keine Flugreglerprüfung. Fertigungs- und Flugfreigaben fehlen.

## Reproduktion

Im Repository-Stamm, mit FreeCAD für System-Python:

```bash
/usr/bin/python3 entwicklung_ab/cad_erstellen.py
node entwicklung_ab/rechnen.cjs
/usr/bin/python3 entwicklung_ab/geometrie_pruefen.py
/usr/bin/python3 entwicklung_ab/mesh_exportieren.py
MPLCONFIGDIR=/tmp/propboard-ab-mpl python entwicklung_ab/auswerten.py
node entwicklung_ab/viewer_pruefen.cjs
python entwicklung_ab/paket.py
```

Der CAD-Aufbau benötigt einige Minuten. `--case QUAD_R380` erzeugt eine einzelne
Variante. `--reuse-core` ist ausschließlich für unveränderte P14-Kerngeometrie
gedacht und prüft den vorherigen nativen Datei-Hash; es ist kein Ersatz für einen
Neuaufbau nach Änderungen an P14-Parametern.

Weitere Abhängigkeiten: Node.js, Python mit NumPy/SciPy/Matplotlib/ReportLab/Pillow,
DejaVu Sans, für den Viewercheck Playwright mit Chromium. Der Viewer selbst braucht
keine externe Netzwerkverbindung. Falls der Browser lokale Dateizugriffe sperrt,
im Repository-Stamm `python -m http.server 8050 --bind 127.0.0.1` starten und
`http://127.0.0.1:8050/entwicklung_ab/Modelle.html` öffnen. Der automatisierte
Viewercheck startet seinen eigenen temporären lokalen Server. Der Viewer zeigt
tatsächliche CAD-Netze; feine Schutzgitter sind für die Übersicht ausgeblendet.

Wichtige Ausgaben: `Leistungsbedarf.csv`, `Lastpunkte.csv`,
`Komponenten_Nachweismatrix.csv`, `Motor_Massenschluss.csv`,
`Rahmen_Lastscreen.csv`, `Hochlauf_Screen.csv`, `Motor_Ausfall_Screen.csv`,
`Geometrie_Pruefung.json` sowie pro CAD-Variante `Stueckliste.csv`,
`Massendaten.json` und `Pruefung.json`. Die `Manifest_SHA256.json` dokumentiert
Artefakte und verwendete Projektquellen.
