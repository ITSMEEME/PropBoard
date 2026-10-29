# Vergleich: zwei horizontale Flügelbänder übereinander

Vom Nutzer bestätigt: zwei gegenläufige Umlaufbahnen in der **x-y-Ebene**, gestapelt entlang **z**. Die Flügelspannweiten liegen radial, die Pitchachsen ebenfalls radial. Die Profilnasen folgen der jeweiligen Geschwindigkeit mit 12° Anstellung nach oben. Dadurch ist die gedachte Auftriebsrichtung auf beiden Bändern +z.

## Neue Annahmen

Zwei Ebenen z = −120 / +120 mm, acht Flügel pro Ebene, NACA 0012, Sehne 120 mm, Spannweite 600 mm. Gerade Ovalabschnitte 500 mm, mittlerer Umlenkradius 450 mm. Die anderen Ovalmaße gegenüber dem vertikalen Entwurf sind notwendig, um auch die radialen Flügel innerhalb der Fahrzeughülle unterzubringen. Deck 1200 × 300 × 40 mm, Unterseite z = 250 mm. Parameterdatei: `parameter.json`.

`Horizontal_Z_gegenlaeufig.FCStd` ist ein eigenständiges natives FreeCAD-Konzept mit editierbaren Extrusionen und Platzierungen. Die Tabelle dokumentiert die Parameter; für eine vollständige Neuberechnung JSON ändern und Skript ausführen. Führungshüllen und Schlitten sind Bauraumplatzhalter, keine Magnetlagerauslegung. Strukturelle Verbindungen, Pitchantriebe, Linearmotoren, Energieversorgung und Fangführung fehlen. Die STEP-Datei ist ein zusätzlicher Geometrieexport.

## Tatsächlicher Strömungsversuch

Der frühere 2D-Solver kann den Auftrieb eines horizontalen Umlaufs nicht durch bloßes Vertauschen der Achsen abbilden: Auftrieb wirkt aus seiner Bahnebene heraus. Deshalb wird hier ein **lokaler x-z-Schnitt gerader Bahnabschnitte** berechnet. Darin bewegen sich die beiden Profile gegeneinander und können ihre Strömungsfelder gegenseitig beeinflussen.

Versuche: Einzelreihe als Referenz, Gegenlauf mit 240 mm Abstand, Gegenlauf mit 360 mm Abstand, feineres Gitter für 240 mm. Alle bei Re = 40, 12° Pitch und gleicher Gittergeschwindigkeit 0,04. Die x-Ränder sind periodisch; die Periode entspricht näherungsweise dem mittleren Flügelabstand auf der Bahn. Dadurch werden unendlich lange gerade Flügelreihen angenähert. Dies ist keine Simulation der endlichen geraden Abschnitte und ihrer Ein-/Ausläufe. Außen in z gibt es Dämpfungszonen zur Ruhegleichverteilung.

Die Geometrieskalierung verwendet Meter, aber Re = 40 entspricht künstlich hoher Viskosität. Bei 10 m/s und 120 mm Sehne hätte reale Luft ungefähr Re = 80.000. Die Vorschubreferenz 10 m/s ist kein ausgewählter realer Betriebspunkt. Weder eine reale Traglast noch ein Energiebedarf darf aus den Testwerten abgeleitet werden. Magnet- und Strukturkräfte werden nicht simuliert.

Gebietsgröße, Fernfeldbehandlung und Zeitschritt wurden nicht unabhängig variiert. Insbesondere kann die Dämpfungszone den langfristigen Abstrom und die Kraftwerte beeinflussen. Die Läufe starten aus ruhender Strömung ohne Anfahrrampe; veränderliche Blockmittelwerte müssen als Einschwing- oder andere Zeiteffekte offengehalten werden.

**Ein vollständiger CFD-Vergleich „vertikale Bahnen neben­einander gegen horizontale Bahnen übereinander“ wurde nicht durchgeführt.** Dafür braucht es 3D-Strömung mit Kurvenfahrt, endlicher Spannweite, beiden Umläufen und relevanten Störkörpern. Der Bericht des lokalen Versuchs nennt Gitter- und Zeiteinflüsse, ohne eine Entwurfsvalidierung zu behaupten.

## Reproduzieren

Im Repository-Verzeichnis; CFD-Abhängigkeiten wie in `../cfd/README.md`:

```sh
/usr/bin/python3 vergleich_horizontal/cad_erstellen.py
python vergleich_horizontal/bewegung_pruefen.py
NUMBA_NUM_THREADS=1 python vergleich_horizontal/strip_cfd.py --name single_c16 --single
NUMBA_NUM_THREADS=1 python vergleich_horizontal/strip_cfd.py --name stack_240_c16
NUMBA_NUM_THREADS=1 python vergleich_horizontal/strip_cfd.py --name stack_360_c16 --gap .36
NUMBA_NUM_THREADS=1 python vergleich_horizontal/strip_cfd.py --name stack_240_c24 --cells 24
python vergleich_horizontal/auswerten.py
```

Die separate 360-mm-Variante ist nur ein Strömungsparametervergleich; das CAD zeigt den 240-mm-Stapel. Ergebnisse in `results/`, CAD-Prüfung in `CAD_Pruefung.json`. Die Form- und Schnittprüfung des CAD gilt für die gespeicherte Momentaufnahme. Sie ersetzt keine kontinuierliche Kollisionsprüfung, keine Lager-/Magnetauslegung und keinen Festigkeitsnachweis.

Die Führungsplatzhalter haben rechteckigen Querschnitt 16 × 16 mm. `bewegung_pruefen.py` prüft zusätzlich konservative Flügelgrundrisse in 360 Phasen pro Ebene mit einem Trennachsentest. Diese Stichprobe ist keine kontinuierliche Prüfung aller Bauteile und Lager. Die Vorschau ist aus denselben Parametern gezeichnet, kein FreeCAD-Screenshot.
