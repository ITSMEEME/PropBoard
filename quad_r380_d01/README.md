# Quad R380 D01 – mechanischer Detailstand

Detailliertes verschraubtes Tragwerk mit Deck: **351 Instanzen, 23 Teiletypen, 12 native PartDesign-Typen, 21,538 kg modellierte Masse**. Eigenbauteile besitzen Skizzen, Bohrungen, modellierte Gewinde, Taschen und bearbeitete Kanten; Normteile besitzen reale Gewindegeometrie. Motoren und weitere OEM-Komponenten sind noch nicht integriert. Der Gesamt-Quad ist nicht produktions- oder flugfreigegeben.

- [Gesamtes Detailpaket mit Prüfsummen](QuadR380_D01_Detailpaket.zip)
- [Interaktive CAD-Ansicht](Mechanik.html) · [Ansichtsbild](Tragwerk_Ansicht.png)
- [Detailbericht](Detailbericht.pdf) · [A3-Bauteilprüfblätter](Bauteilpruefblaetter.pdf)
- [Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D01_Mechanik.FCStd) · [STEP-Baugruppe](Ausgabe/QuadR380_D01_Mechanik.step)
- [Editierbare Einzelteile, STEP und Prüfblätter](Ausgabe/Einzelteile/)
- [Stückliste](Ausgabe/Stueckliste.csv) · [Schraubstellen](Ausgabe/Schraubstellen.csv)
- [Prüfstatus](Ausgabe/Pruefung.json) · [Geometrische Kollisionsprüfung](Ausgabe/Kollisionen.json) · [Montageprüfung](Ausgabe/Montage_Pruefung.json)
- [Gezielter Datenbeschaffungsauftrag und benötigte Domains](BESCHAFFUNGSAUFTRAG.md)

## Nachweise und Grenzen

94 nominale Gewindepaarungen geprüft; keine Überschneidung >0,1 mm³ unter 826 über Bounding-Box vorselektierten Paaren. Wiederverwendete Nachweise prüfen Geometrie-Hashes und relative Lage. Gerade Werkzeugzugänge und vier Kassetten-Einschubwege sind für definierte Montagestufen geprüft. Das umfasst keine Werkzeughandhabung, Toleranzsimulation, Vorspannungs-, Kontakt- oder Ermüdungsfreigabe.

Linearer Ausleger-Vorcheck bei 200 kg und Lastfaktor 2: nominal 56,7 MPa und 2,30 mm Enddurchbiegung. Materialkennwerte, Lastverteilung und Einspannung sind Annahmen. Eingepasste Druckstücke sind erforderlich; max. Flächenspalt 0,03 mm muss durch tatsächliche Paarung/Messung sichergestellt werden. Schraubenmomente sind lediglich Rechenbereiche und nicht zur Montage freigegeben.

Motoren, Rotoren, OEM-Adapter, Regler, Batterie/BMS, Kontaktoren, Sicherungen, Kabelbaum, Schutz und Landegestell bleiben offen. Bauteilprüfblätter sind aus tatsächlichen CAD-Kanten abgeleitet; sie ersetzen keine vollständigen tolerierten Fertigungszeichnungen.

## Montagefolge

1. Profile und Druckstücke paaren/messen, Druckstücke einschieben und mit M5 sichern; erst danach Wurzelplatten klemmen.
2. Endträger montieren. IF90 besitzt noch keine bestätigte OEM-Kompatibilität.
3. Mutternkassetten samt vier Muttern und Deckel außerhalb der Deckrohre vormontieren; von den jeweiligen offenen Rohrenden einschieben.
4. Stützenfüße und Stützenköpfe verschrauben; Kassetten vor Deckhülsen und deren Schrauben einsetzen.
5. Druckhülsen und Deck montieren. Vor Wiederholung müssen Reibwerte, Anzugstrategie und Sicherungsverfahren qualifiziert sein.

## Reproduktion

FreeCAD 0.20.x mit PartDesign/TechDraw; System-Python, ReportLab, pypdf, Chromium und Node/Playwright. `rahmen_erstellen.py` erstellt die Ausgangsgeometrie aus `parameter.json` und den mitgelieferten Normteil-BReps. `mechanik_pruefen.py` stellt Gewindephasen ein und prüft die Körperpaare; der vollständige Lauf kann lange dauern. `montage_pruefen.py`, `tragwerk_rechnen.py`, `ableiten.py`, `viewer_pruefen.cjs` und `bericht_erstellen.py` erzeugen die weiteren Ergebnisse. `layout_korrigieren.py` dokumentiert die iterative Korrektur, ist beim Neuaufbau nicht erforderlich. `lastfaelle.cjs` benötigt zusätzlich `../kreis_r04/simulation/r04_physik.js` aus diesem Repository.

Normgeometrie: FreeCAD Fasteners Workbench, SHA `fddd07af422b7d3a69098b32333711c5eeae184c`, Lizenz und Maßtabellen unter `Quellen/Normteile`. Geometrien stellen Nennmaße dar, keine Lieferzertifikate. Für Neugenerierung der Normteilbibliothek benötigt `normteile_erstellen.py` diesen Quellstand unter `/tmp/quad-r380-fasteners`.
