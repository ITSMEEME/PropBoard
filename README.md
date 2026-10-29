# PropBoard

PropBoard ist die Konzeptidee eines elektrischen Hoverboards, das eine Person mit einem Körpergewicht von bis zu 100 kg tragen und kontrolliert bewegen soll. Im Mittelpunkt stehen elektrischer Antrieb, stabile Lageregelung und eine sichere Bedienung.

## Projektidee

Das Board soll durch elektrisch erzeugten Schub abheben und seine Lage mithilfe von Sensoren und einer automatischen Regelung stabilisieren. Anders als bei einem selbstbalancierenden Rollbrett ist hier tatsächliches Schweben über dem Boden gemeint. Ob sich das Ziel technisch und energetisch sinnvoll umsetzen lässt, muss zunächst untersucht werden.

## Technische Schwerpunkte

- **Antrieb und Auftrieb:** Ermittlung des erforderlichen Schubs für Person, Board, Akku und Antrieb sowie Vergleich geeigneter Antriebskonzepte.
- **Energieversorgung:** Bewertung von Leistungsbedarf, Akkumasse, Wärmeentwicklung und erreichbarer Betriebsdauer.
- **Stabilisierung:** Erfassung von Neigung und Bewegung sowie Regelung von Höhe und Lage.
- **Tragstruktur:** Auslegung einer belastbaren Plattform unter Berücksichtigung von Gesamtmasse, Schwerpunkt und dynamischen Lasten.
- **Bedienung:** Verständliche Steuerung mit klarer Zustandsanzeige und definierten Betriebsgrenzen.

## Sicherheit und Entwicklung

Ein personentragendes Fluggerät stellt hohe Anforderungen an die Sicherheit. Dazu gehören geschützte Antriebskomponenten, die Erkennung von Fehlern und ein kontrolliertes Verhalten bei Sensor-, Antriebs- oder Energieausfällen. Ein Abschalten allein ist im Schwebeflug kein ausreichendes Sicherheitskonzept.

Die Entwicklung beginnt mit einer Machbarkeitsstudie, Berechnungen und Simulationen. Anschließend können unbemannte, gesicherte Versuchsaufbauten die Annahmen überprüfen. Versuche mit Personen setzen eine fachkundige Sicherheitsbewertung und die Klärung der geltenden rechtlichen Anforderungen voraus.

## Aktueller Stand

Die [Projektübergabe](docs/Projektuebergabe.md) hält Anforderungen, Rechenannahmen, bisher berichtete Ergebnisse und offene Nachweise fest.

Neu erstellte native [FreeCAD-Konzeptdateien](cad/README.md) bilden die übergebenen Referenzmaße ab. Fehlende Strukturdetails sind als neue Annahmen dokumentiert. Die ursprünglichen CAD-Dateien wurden nicht wiederhergestellt.

Als alternative Konzeptstudie liegen jetzt zwei gegenläufige, nominell magnetgeführte Flügelumläufe mit individueller Pitch-Vorgabe als [FreeCAD-Modell](cad/Gegenlaeufiger_Fluegelumlauf.FCStd) vor. Eine [explorative 2D-CFD](cfd/README.md) untersucht vorgeschriebene Flügelbewegungen bei künstlich niedriger Reynolds-Zahl. Das ist keine realmaßstäbliche Simulation des Boards und liefert keinen Tragfähigkeits- oder Leistungsnachweis.

Eine zusätzliche [Vergleichsvariante](vergleich_horizontal/README.md) ordnet beide Bänder waagerecht in der x-y-Ebene und übereinander entlang z an. Das separate FreeCAD-Modell zeigt 240 mm Ebenenabstand. Der lokale 2D-Strömungsversuch vergleicht gerade Flügelreihen; ein vollständiger 3D-Vergleich der Fahrzeugvarianten steht aus.

Der [ausführliche Vergleichsbericht](bericht/Vergleichsbericht.pdf) stellt 3D-Geometrie, CFD-Voruntersuchungen, analytische Referenzlastfälle und belegte beziehungsweise offene Vor- und Nachteile gegenüber. Eine [interaktive 3D-Ansicht](bericht/Modelle_3D.html) zeigt die Geometrien beider nativen Modelle. Reale Flugfähigkeit ist damit nicht nachgewiesen.

Die [zeitaufgelöste Begegnungsanalyse](begegnung/Begegnungsanalyse.md) betrachtet die direkte Überdeckung der oberen und unteren Flügel im lokalen 2D-Modell. Eine [interaktive Flow-Ansicht](begegnung/results/Flow_Interaktiv.html) zeigt gespeicherte Geschwindigkeits-, Wirbelstärke- und Druckfelder vor, bei und nach der Begegnung. Es handelt sich weiterhin um Re = 40 und keine realmaßstäbliche 3D-CFD.

Der [fertigungsorientierte Konstruktionsvorentwurf](konstruktion/Konstruktionsbericht.pdf) ergänzt Carbonrahmen, Führungs-/Antriebsdetails, Batterie-/Kabelräume und drei Ergonomiekonzepte. **Stehen ist die gewählte Hauptvariante.** Native FreeCAD-Baugruppen, Referenzzeichnungen und ein [interaktiver Detailviewer](konstruktion/Modelle_3D.html) liegen vor. Werkstoff-, Last-, Magnet-, Elektro- und Fertigungsfreigaben fehlen weiterhin.

Verbindliche Ziele sind maximal **2100 × 1700 × 600 mm** Fahrzeugabmessungen einschließlich Rotoren und Schutz, **100 kg Personengewicht zuzüglich Ausrüstung**, mindestens **15 Minuten Flugzeit** und ungefähr **80 km/h** Zielgeschwindigkeit. Gewünscht sind eine selbststabilisierende Winkelregelung entsprechend ANGLE MODE und native, editierbare FreeCAD-Dateien. Die Fahrzeughöhe wird bisher ohne Person verstanden; Missionsprofil und Ausrüstungsmasse sind noch offen.

Der geometrische Referenzentwurf verwendet sechs Rotorpositionen in einem rechteckigen 3×2-Raster. Der bisherige 650-mm-Rotoransatz und der neue X605-Kandidat mit nominell 558,8 mm Propellerdurchmesser müssen getrennt bewertet werden. Der untersuchte Tattu-41000-Pack liefert im bisherigen Modell zu wenig Dauerleistung. Für den X605 fehlen verifizierte Herstellerkennfelder.

Keine Variante ist bislang als sicher, baubar oder personenflugfähig nachgewiesen. CAD-Konzepte und idealisierte Rechnungen ersetzen keinen konstruktiven oder experimentellen Nachweis.
