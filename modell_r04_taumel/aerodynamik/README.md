# Aerodynamik des tatsächlichen CAD-Profils

Dies sind **berechnete Kennwerte, keine Messungen und keine vollständige Koaxial-CFD**. `profil_export.py` schneidet den echten FreeCAD-Flügel bei r=110 mm und exportiert 121 BRep-Profilpunkte. Das über die Spannweite unveränderte Profil hat 30 mm Sehne und **0,6 mm / 2 % Sehnenlänge Hinterkantendicke**. Es wird nicht stillschweigend durch ein scharfes NACA 0012 ersetzt.

`Ausgabe/Polaren.json` und `Polaren.csv` enthalten XFOIL-6.99-Ergebnisse für Re = 20.000, 40.000, 60.000, 80.000, 100.000, 140.000 und 180.000; Ncrit 4 und 9, Mach 0,08, α = −6…16°. 317 von 322 angefragten Punkten sind konvergiert. Fehlende Punkte bleiben als Lücken gekennzeichnet. Ncrit-Werte sind Sensitivitätsannahmen, keine gemessene Druckrauheit/Turbulenz. Gedruckte Oberfläche, Ablösung, dynamischer Stall und Nachlauf müssen noch experimentell überprüft werden.

`CL`, `CD`, `CM` sowie Umschlagpositionen werden aufbewahrt. Symmetrie bei α=0 des NACA-Referenzprofils und ein Panelvergleich 160/240 Punkte werden geprüft; diese numerischen Checks sind keine empirische Validierung. XFOIL druckt CL/CD nur mit begrenzter Dezimalzahl aus, daher bedeutet eine identische gerundete Zahl keine exakte Konvergenz.

Der vorkompilierte Debian-XFOIL brach auch am Standard-NACA-Profil mit SIGFPE ab. Deshalb wurde der Originalquellcode als Double-Precision-Release ohne die im Makefile aktivierten Debug-Initialisierungs-/FPE-Trap-Flags kompiliert und am Referenzprofil geprüft. Quelle: [Debian XFOIL 6.99](https://deb.debian.org/debian/pool/main/x/xfoil/xfoil_6.99.dfsg+1.orig.tar.gz), Autoren Mark Drela/Harold Youngren. Quellarchiv-, Solver- und Profil-SHA256 stehen in `Polaren.json`. Der ausführbare Solver und Compiler liegen nur unter dem ignorierten `.cfd-tools/`; nicht im Reviewpaket.

Build: GNU Fortran 14.2, `-O2 -fdefault-real-8 -std=legacy -fallow-argument-mismatch`, Plotlib ebenfalls Double Precision, originale X11-Plotlib. Rohlogs/Polardateien liegen neben den Tabellen. Die Bibliotheken wurden ausschließlich im Workspace entpackt; keine Systeminstallation wurde verändert.

## Rotorvergleich für sechs Savöx-Servos

`betriebspunkte.js` verwendet dieselbe Blattelement-/Impulstheorie wie die historische Rechnung, wahlweise mit vereinfachter Polare oder dem CAD-XFOIL-Satz. Bei jedem Punkt wird der untere Pitch zum Drehmomentausgleich und die Drehzahl zum Zielschub gesucht. Masse 1,577676 kg, oberer Pitch 14°, Geometrie aus H01. `Ausgabe/Betriebspunkte_Savox.json` enthält genaue Werte, Ströme, Winkel- und Re-Bereiche.

| Polare | Schweben [U/min] | modellierte Busleistung | Schub/Gewicht 2 [U/min] |
|---|---:|---:|---:|
| bisher vereinfacht | 2646 | 215 W | 3739 |
| CAD-XFOIL Ncrit 4 | 2569 | 221 W | 3710 |
| CAD-XFOIL Ncrit 9 | 2558 | 225 W | 3618 |

Die konvergierten finalen BEMT-Abschnitte im Schwebepunkt sind vollständig durch die jeweilige XFOIL-Tabelle abgedeckt. Im Ncrit-4-Punkt mit Schub/Gewicht 2 stammen **23,75 % der finalen Abschnitte aus dem bisherigen Ersatzmodell**, weil Tabellenwerte fehlen/außerhalb des Bereichs liegen. Interne numerische Suchschritte können ebenfalls Ersatzwerte benötigen. Das Ergebnis ist dort ausdrücklich eine Hybridrechnung. Ncrit 9 hat an diesem stationären Punkt keine finalen Ersatzabschnitte.

Der optionale Flugfall `Savox_7_4V_XFOIL_N4` verwendet denselben Datensatz mit uniformem dynamischem Zustrom statt radialem stationärem BEMT. Dort benötigen etwa 20 % der tatsächlichen Blattelementauswertungen das Ersatzmodell. Diese Abdeckung wird im Fluglog und Browser angezeigt. `polar_lookup.js` extrapoliert nicht stillschweigend und füllt keine fehlenden Punkte mit Null. Der Flugregler und die Servolastabschätzung verwenden bisher kein vollständiges CM-basiertes zyklisches Blattmomentmodell.

Die Leistungs-/Stromwerte stammen aus dem bisherigen unvalidierten Motor-/Akku-Ersatzmodell. Die BEMT-Busleistung enthält die bisherigen pauschalen Nebenverbraucher, keine gemessene Servo-/BEC-Leistung. Kein 3D-CFD-Nachweis, keine validierte Wirbelringphysik, keine Messung einer sicheren maximalen Drehzahl oder Flugdauer.

```sh
FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib" .cfd-tools/freecad/usr/bin/python modell_r04_taumel/aerodynamik/profil_export.py
.cfd-tools/venv/bin/python modell_r04_taumel/aerodynamik/polaren_erstellen.py
node modell_r04_taumel/aerodynamik/betriebspunkte.js
```

Alternativen XFOIL-Pfad über `XFOIL_BIN` angeben. Tatsächlichen Schub/Drehmoment anschließend über die Vorlagen und Auswertung unter `../messdaten/` identifizieren.
