# Horizontal Z – Montage R02

Zwei horizontale Umlaufbahnen, 240 mm Ebenenabstand, Hauptvariante Stehen. Detaillierter Montagevorentwurf mit 3.185 Ergebniskörpern, davon 1.270 Schrauben. Keine Fertigungs- oder Personenflugfreigabe.

- [Hauptbaugruppe in FreeCAD](00_Horizontal_Z_R02_Montage.FCStd)
- [Rahmenknoten im Detail](01a_Rahmenknoten_Detail.FCStd) und [Explosionsansicht](01b_Rahmenknoten_Explodiert.FCStd)
- [Schlitten und Flügel](02_Schlitten_R02_Detail.FCStd)
- [Batterie und Kabeltrassen](03_Batterie_R02_Detail.FCStd)
- [TechDraw-Blätter](04_Referenzzeichnungen_R02.FCStd)
- [Offline-3D-Ansichten](Modelle_3D.html)
- [Montagebericht](Montagebericht.pdf) und [Referenzblätter](Referenzblaetter.pdf)
- [Schraubenliste](Schraubenliste.csv), [Instanzliste](Stueckliste.csv), [Verbindungsregister](Verbindungen.json)
- [Prüfumfang und Befunde](Pruefzusatz.md), [maschinenlesbare Montageprüfung](Montagepruefung.json)

Schraubenköpfe, Innensechskantreferenzen, Scheiben, Muttern, Bohrungen und Senkungen sind modelliert. Gewinde sind vereinfachte Nennhüllen. Kaufteil-Normformen, Werkstoffe, Festigkeitsklassen, Passungen und Drehmomente sind nicht freigegeben. Die elektrischen Komponenten und Pitch-/Lager-/Flügelanschlüsse sind teilweise weiter Referenzgeometrie. Das gilt auch für Fußpuffer und für noch fehlende konkrete Kabelschellen und Stecker.

Die Hüllprüfung gilt nur für die gespeicherte Stellung. Es wurde keine neue CFD-, Last- oder Bewegungsvalidierung durchgeführt. Die vorherigen Tragfähigkeitsrechnungen sind nicht auf R02 übertragen.

## Erzeugung

FreeCAD 1.0 Python-API unter `/usr/lib/freecad/lib`, getestet mit `/usr/bin/python3`:

```sh
/usr/bin/python3 horizontal_z_r02/erstellen.py
/usr/bin/python3 horizontal_z_r02/nachbearbeiten.py
/usr/bin/python3 horizontal_z_r02/zeichnungen_erstellen.py
python horizontal_z_r02/viewer_erstellen.py
```

Die Skripte erwarten die unveränderten Hilfsquellen `konstruktion/erstellen.py`, `cad/umlauf_kinematik.py` und `bericht/viewer_erstellen.py` im selben Projektbaum. Diese Quellen liegen im Archiv mit erhaltenen relativen Pfaden. Die Detailauszüge sind unabhängig gespeicherte Kopien und müssen nach Modelländerungen neu erzeugt werden. Die Hauptdatei enthält native Bearbeitungsobjekte; wiederholte Flügelinstanzen enthalten Geometriekopien.

`parameter.json` dokumentiert den erzeugten Stand. Einige konkrete Anschlussmaße sind im Erzeugungsskript festgelegt. Die Datei ist daher kein vollständiger parametrischer Konfigurator.
