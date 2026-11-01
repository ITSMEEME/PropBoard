# P13 – mechanischer Gesamtentwurf für Beschaffung und Dienstleisteranfragen

**Aktueller Prüfstand: [Ergebnis und offene Mechanik](ERGEBNIS.md).**
32 statische Überschneidungen bleiben offen; Gewicht und Bauraumziele sind verfehlt.

Stand01.11.2026. P13 baut auf dem gesicherten P12-Quellstand in `basis_p12/`
auf; P12 und das kleine P11-Modell werden nicht überschrieben. Änderungen an der
P13-Basiskopie sind in `basis_p12/MODIFIKATIONEN.json` dokumentiert.

Die vom Nutzer gelieferte MN1330-Zeichnung ist als Grundlage der Motoranschlüsse
übernommen. Die Konstruktion wird nicht mehr vom fehlenden Herstellerdownload
abhängig gemacht. Nicht bemaßte Gewindetiefen sind ausdrücklich Montageannahmen.

## Konstruktionsumfang

- Motoraufnahme mit4×M6/PCD50, Rotornabe mit12×M5/PCD40, Senkungen für ISO4762.
- Innenring mit8 radialen Pitchlagerpatronen je Ebene;7201B-Paare in DB-Anordnung,
 12mm-Pitchwellen, KM1/MB1, demontierbare formschlüssige Hebel und Wurzeleinsätze.
- Fliehkraftanschlag am Wurzeleinsatz durch Endscheibe/M5-Endschraube;
 äußere8mm-Zapfen mit608-Loslager und Sicherungsringen.
- Durchgehende V-Laufkontur auf tragendem Außenring; Außenlagerträger und
 20×17-Speichen sowie zusätzliche V-Fachwerke aus30×26-CFK-Rohren mit M8-Gelenkköpfen.
- Taumelscheiben mit GE60ES-Gelenklager,61820-Rotationslager, axialen Deckeln,
 Lagermuttern, Hubanschlägen und Scheren für stationäre/rotierende Phasenhaltung.
- Je drei12mm-Hub-Spindelaktor-Baugruppen mit12×4-Kugelgewindetrieb,
7001B-Festlagerpaar, Linearführung und gemeinsam schwenkbarem Servo-/HTD3M-Träger.
 GE20ES-Füße und Verdrehsicherungsstifte vermeiden eine starre Überbestimmung.
- Zwei CFK-Flügelschalen, Wurzel-/Spitzenverstärkungen, zwei Holmstege und
 galvanisch isolierte metallische Wurzel-/Spitzeneinsätze je Flügel.
- Standdeck auf RHS-Trägern und vier Stützen mit Druckhülsen; vier Landebeine
 und zwei Kufen als qualifiziert zu fertigende Aluminium-Schweißbaugruppen.
- Ergänzte Verschraubungen, Zentrierbuchsen, Zuganker und Sicherungsbleche.

## Dateien und Nutzung

`Ausgabe/P13_Mechanik.FCStd` enthält einzeln benannte native FreeCAD-Körper mit
Material, Normfamilie, Herkunft, Fertigungsmerkmalen und offenen Freigabepunkten.
Der Gesamt-STEP wurde wegen einer fehlgeschlagenen Rückleseprüfung zurückgestellt
(4782 statt4780 Körper). Er ist nicht im Lieferpaket. Native Baugruppe und
Einzel-STEP-Dateien sind die bereitgestellten CAD-Formate; Details in
`Ausgabe/Gesamt_STEP_Pruefung.json`. Alle395 Einzel-STEPs sind als gültige
Einzelkörper rücklesbar; bei zwei Außenring-Varianten ist der Volumenvergleich
noch offen, siehe `Ausgabe/Einzel_STEP_Pruefung.json`.

Die Tabelle `Nennmasse` dokumentiert den eingefrorenen Stand. Sie ist **keine
automatische Parametrikkopplung**. Für Änderungen `parameter.json` und gegebenenfalls
die Konstruktionsmodule bearbeiten und `/usr/bin/python3 erstellen.py` bzw.
`P13_erstellen.FCMacro` ausführen. P12 bleibt das separat verfügbare parametrisierte
Vergleichsmodell. P13 ist ein neuer Schnittstellenentwurf mit festen Architekturmaßen;
einzelne neue Maßparameter sind noch nicht für freie Variantenbildung verifiziert.

`STEP_Sonderteile/` enthält anfragbare Eigenkonstruktionen;`STEP_Nennkonturen/`
enthält Montage-/Normmaßreferenzen. Normkonturen sind keine Hersteller-CADs und
keine Bestellung von selbst zu fertigenden Schrauben oder Lagerinnenteilen.
`RFQ_Sonderteile.csv` und `Stueckliste.csv` beschreiben Fertigung und CAD-Mengen.
`RFQ_Fertigungsvarianten.csv` zählt die tatsächlichen STEP-Fertigungsvarianten
einschließlich gespiegelter Teile. `Beschaffungsfamilien.csv` führt geteilte Lager-/Gelenkkopfkonturen zu ganzen
Kaufbaugruppen zusammen; sie ist noch keine freigegebene Bestellliste.
Zeichnungen unter`Zeichnungen_RFQ/` sind Anfragezeichnungen. Vollständige
Fertigungszeichnungen mit freigegebenem Bezugssystem und Toleranzketten sind damit
nicht ersetzt.

[Normteile und Prüfgrundlagen](NORMTEILE.md) · [Motoranschluss](MOTORANSCHLUSS.md) ·
[CFK-Dienstleisteranfrage](RFQ_CFK.md) · [Metall-/Baugruppenanfrage](RFQ_METALL.md) ·
[Montagefolge](MONTAGE.md) · [Verbleibende Freigabepunkte](FREIGABESTATUS.md).

## Verifikation und Grenzen

Aktuelle Ergebnisse stehen in`Ausgabe/Pruefung.json`,`Kollisionen.json`,
`Kinematik_Pruefung.json`und`Lastscreen.json`. Nur abgeschlossene Prüfungen dürfen
als bestanden gelesen werden. Die Starrkörper-Kinematik prüft den Gelenkschluss
im ausdrücklich begrenzten Stellraum. Sie ist keine dynamische Simulation und keine
vollständige BRep-Bewegungskollisionsprüfung aller Baugruppen.

Wesentliche Bauraumänderungen gegenüber P12: Rotor-Ebenenabstand360 statt240mm;
Flügelspitze R710 stattR750 bei unveränderter V-Laufspitze R770. Die Referenzflügel
haben lokale Wurzel-/Spitzenverstärkungen und eine3mm-Hinterkante. Frühere CFD-,
Massenträgheits-, Flugzeit- und Reglerergebnisse gelten dafür nicht automatisch.

Die ursprünglichen maximalen Fahrzeugmaße und das150kg-Auslegungsszenario werden
mit der tatsächlichen neuen Geometrie verglichen. Der konstruktive Entwurf ist
keine Aussage, dass diese Ziele erfüllt sind. Lieferteilfreigaben, CFK-Laminat,
Fügetechnik, Passungen, Vorspannungen und Festigkeits-/Ermüdungsnachweise stehen
weiterhin aus. Das Paket ist für technische Prüfung und Angebote, nicht zum
ungeprüften Fertigungsauftrag oder Personenbetrieb bestimmt.

## Reproduzieren

```bash
/usr/bin/python3 erstellen.py
/usr/bin/python3 pruefen.py
/usr/bin/python3 kinematik.py
/usr/bin/python3 gesamt_step.py
/usr/bin/python3 anfrage_erstellen.py
/usr/bin/python3 beschaffung.py
/usr/bin/python3 visualisieren.py
/usr/bin/python3 paket_erstellen.py
```

FreeCAD1.0/OCC7.8-Pythonmodule, TechDraw und die vorhandene Python-Standardbibliothek
werden verwendet. Die Baugruppen und Zeichnungsansichten stammen aus den BRep-Körpern.
