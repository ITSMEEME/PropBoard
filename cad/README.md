# FreeCAD-Konzeptdateien

**Aktuell: P11 – Direktantrieb 1:1 mit kugelgelagerten Führungsrollen.**
[Native Konstruktion und technische Grenzen](../modell_r04_taumel/integration_p11/README.md) ·
[Visueller Physik-Prüfstand](../modell_r04_taumel/simulation/Physik_Pruefstand.html) ·
[Flugsimulator](../modell_r04_taumel/simulation/H01_Flugsimulator.html).
P10 und frühere Revisionen bleiben historische Vergleichsstände. Der spätere Ringmotor
ist noch auszuwählen; EMAX bleibt die elektrische Vergleichsreferenz.

## Neues Umlaufkonzept

`Gegenlaeufiger_Fluegelumlauf.FCStd` und die STEP-Datei bilden zwei gegenläufige Ovalmodule mit je acht NACA-0012-Flügeln, Pitchachsen, Schlitten-Platzhaltern, Führungshüllen und einem Deck ab. Sie ersetzen den Rotorentwurf nicht automatisch.

Die neue Momentaufnahme misst ungefähr **1707 × 1664 × 493 mm**. Alle Maße, Profilwahl, Flügelzahl und Pitch-Verlauf sind neue, unbestätigte Konzeptannahmen. Führungen sind lediglich geometrische Platzhalter; Magnetlager, Linearmotoren, Fangführung, Pitchantriebe, Verbindungen, Akku und Verkabelung sind nicht ausgelegt. Schlittenblöcke überlagern die Führung absichtlich als Bauraumreferenz; ein funktionsfähiges Lager ist damit nicht modelliert. Deck und Module haben keinen konstruktiven Verbindungsnachweis.

Parameter stehen in `umlauf_parameter.json`, im FreeCAD-Dokument sind sie zusätzlich als Tabelle dokumentiert. Diese Tabelle ist bei diesem neuen Modell keine vollständig verknüpfte Steuerung: Geometrieänderungen werden durch Bearbeiten der JSON-Datei und erneute Skriptausführung erzeugt. Native Part-Grundkörper, Flügelextrusionen und Platzierungen bleiben in FreeCAD editierbar. Die Profilkonturen und Führungshüllen sind generierte Part-Geometrien. Individuelle Pitchachsen sind geometrisch dargestellt; es gibt keine funktionsfähige Stellmechanik oder Animation im FCStd-Dokument.

```sh
/usr/bin/python3 cad/umlauf_erstellen.py
python cad/umlauf_pruefen.py
```

Erzeugung, Speichern, Wiederöffnen und Formgültigkeit wurden geprüft. Eine zusätzliche Abtastung von 360 Umlaufphasen pro Richtung prüft konservative Flügelhüllen auf gegenseitigen Abstand und Deckfreiheit. Dies ist keine vollständige kontinuierliche Kollisions-, Lager- oder Strukturprüfung. Berichte: `Umlauf_Pruefbericht.json` und `Umlauf_Bewegungspruefung.json`.

Die [CFD-Voruntersuchung](../cfd/README.md) ist ein getrenntes, vereinfachtes 2D-Modell bei Re = 40. Sie simuliert keine Magnetführung und keinen Personenflug. Die [Konzeptansicht](Umlauf_Konzept.png) ist eine schematische Darstellung aus denselben Geometrieparametern, kein FreeCAD-Screenshot.

## Frühere Rotor-Konzepte

- `Hexacopter_650_Konzept.FCStd`: sechs 650-mm-Rotorreferenzen, Ringe, Deck und neu angenommene Strukturplatzhalter.
- `Hexacopter_Tattu41000_8Packs.FCStd`: zusätzlich acht maßhaltige Tattu-Gehäuse an den übergebenen Positionen.
- `Tmotor_X605_Bauraum.FCStd`: vereinfachter Motorzylinder und bewusst überlappende Referenzhülle. Kein bestätigtes Produktmodell und kein integrierter Antriebsentwurf.

Die Dateien enthalten editierbare Part-Grundkörper, boolesche Ring-Differenzen und in den Boarddateien eine Parametertabelle mit Expressions. Rotorwirkflächen sind ausgeblendet; sie lassen sich im Modellbaum einblenden. Maße in mm.

Erzeugung im Repository-Verzeichnis:

```sh
/usr/bin/python3 cad/erstellen.py
```

Hier wurde FreeCAD 1.0 über seine Python-Schnittstelle verwendet. Der separate Starter `freecadcmd --version` stürzt in dieser Umgebung ab. Der Bibliothekspfad im Skript gilt für diese Linux-Installation.

## Neue Annahmen und Grenzen

Die Originaldateien fehlen. Rahmen, Motorplatzhalter, Deckstützen und Landefüße wurden neu als einfache Visualisierungsgeometrie angenommen. Sie rekonstruieren keine unbekannten Originaldetails. Die Fahrzeughülle beträgt 2060 × 1690 × 320 mm; die Höhe entsteht aus der angenommenen Fahrwerksunterkante z = −90 und der Deckoberkante z = 230.

Querträger folgen den Rasterparametern, Längsträger, Deckstützen und Fahrwerk sind jedoch nicht vollständig rasterabhängig. Geänderte Geometrien müssen erneut auf Abstände und Außenmaße geprüft werden. Es gibt keinen Nachweis einer zusammenhängenden tragfähigen Struktur, von Schutzwirkung oder ausreichender Rotorfreiheit im Betrieb. Motorplatzhalter sind keine realen Antriebe. Stecker, Verkabelung, Kühlung, Halter und Akkuausdehnung fehlen.

Der X605 wird nicht automatisch in das Board eingebaut. Seine Achsenlage innerhalb der Hülle ist eine ausdrücklich benannte Annahme. Die überlappende Hülle dient nur als Referenz.

## Ausgeführte Prüfungen

`Pruefbericht.json` dokumentiert die aktuelle Erzeugung: alle drei Dokumente gespeichert und erneut geöffnet, vorhandene Formen auf geometrische Gültigkeit geprüft, Board-Außenmaße geprüft, Rotordurchmesser geändert und zurückgesetzt. In der Tattu-Variante wurden mindestens 10 mm zwischen Packgehäusen und positive Abstände zu anderen modellierten Ergebnisobjekten geprüft.

Diese Prüfungen sind geometrisch. Keine Flug-, Struktur-, Schutz- oder Leistungsvalidierung. Keine Fertigungszeichnungen.
