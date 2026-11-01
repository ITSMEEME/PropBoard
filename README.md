# PropBoard

**Leichtbauentwicklung P14: Außenrahmen entfernt, Flügel nur innen gelagert, Zentrum verstärkt und reale PH54-Servos ausgewählt.**
[Konstruktion und native CAD-Dateien](kreis_r04/mn1330_p14/README.md) ·
[Animierter parametrischer Entwicklungsprüfstand](kreis_r04/mn1330_p14/P14_Entwicklungspruefstand.html) ·
[Ergebnis und Massengrenzen](kreis_r04/mn1330_p14/ERGEBNIS.md) ·
[Offene Freigaben](kreis_r04/mn1330_p14/FREIGABESTATUS.md).
P14 untersucht 4–12 Blätter je Rotor und 1–4 gegenläufige Rotorpaare mit CAD-Masse/-Trägheit.
Es ist noch nicht produktionsreif; das aktive H01-Profil bleibt deshalb erhalten.

**Vorheriger Ergänzungsstand P13 – Anfrageentwurf mit Motoranschlüssen, Pitchlagerung, Taumelscheiben, Aktoren, CFK-Flügeln und Fahrwerk.**
[Ergebnis: 32 offene Überschneidungen](kreis_r04/mn1330_p13/ERGEBNIS.md) ·
[Entwurf und Prüfgrenzen](kreis_r04/mn1330_p13/README.md) ·
[Offene Freigabepunkte](kreis_r04/mn1330_p13/FREIGABESTATUS.md).
P13 ist nicht bestell- oder flugfreigegeben; Masse und Bauraum überschreiten bisherige Ziele.

**Parametrische Vergleichsbasis: P12 – Direktantrieb mit CFK-Rohrrahmen.**
[Parametrisches CAD und Bedienung](kreis_r04/mn1330_p12/README.md) ·
[CFK-Rahmen CBU20171005TG](kreis_r04/mn1330_p12/CFK_RAHMEN.md) ·
[Aktuelle CAD-Ansicht](kreis_r04/mn1330_p12/Ausgabe/Zwischenstand_P12_Perspektive.png).
[Geometrieergänzungen und offene Baugruppen](kreis_r04/mn1330_p12/GEOMETRIESTATUS.md).
P12 ist ein Fertigungsentwurf mit offenen Last-/Klemm- und Pitchmechaniknachweisen.

**Kleines Referenzmodell: P11 – Direktantrieb 1:1 mit kugelgelagerten Führungsrollen.**
[Native Konstruktion und technische Grenzen](modell_r04_taumel/integration_p11/README.md) ·
[Visueller Physik-Prüfstand](modell_r04_taumel/simulation/Physik_Pruefstand.html) ·
[Flugsimulator](modell_r04_taumel/simulation/H01_Flugsimulator.html).
P10 und frühere Revisionen bleiben historische Vergleichsstände. EMAX bleibt die elektrische
Vergleichsreferenz des kleinen Modells. Für die Großausführung wird MN1330 KV40 untersucht;
der Motor hat keinen durchgehenden axialen Kanal.
[MN1330-Integrationskonzept](konstruktion/MN1330/Direktantrieb.md) ·
[Anordnungsskizze](konstruktion/MN1330/Anordnung.svg) ·
[Lokale CFD mit Linux/Docker](lokale_cfd/README.md) ·
[Portables CFD-Paket](lieferung/PropBoard_CFD_Local_Linux.zip).

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

Das [technische Entwicklungsdatenblatt](datenblatt/Technisches_Datenblatt.pdf) fasst bekannte CAD-Daten, Zielanforderungen und offene Leistungswerte zusammen. Nachgewiesene Tragfähigkeit, Akkukapazität und elektrische Aufnahme sind noch nicht bestimmt; 100 kg Personengewicht sind eine Zielanforderung.

Die [Montagerevision Horizontal Z R02](horizontal_z_r02/README.md) ergänzt segmentierte Schienen, Pfostenklemmen, Deck-Hardpoints, Akkugehäuse und detaillierte Schraubverbindungen. Die [native Gesamtbaugruppe](horizontal_z_r02/00_Horizontal_Z_R02_Montage.FCStd) enthält 3.185 Ergebniskörper mit 1.270 Schrauben; Detail- und Explosionsansichten sowie Stücklisten liegen bei. Geprüft wurden Formgültigkeit, Registervollständigkeit und ausgewählte Verbindungen. Produktabhängige Anschlüsse und Lastnachweise bleiben offen; dies ist keine Fertigungsfreigabe.

Der [rechnerische Tragfähigkeits-Nachweisversuch](tragfaehigkeit/Nachweisversuch.pdf) untersucht CAD-Massenszenarien, Auftriebs-/Umlenkanforderungen, Antriebs- und Strukturbedingungen sowie die Akku-Massenrückkopplung. **Ein positiver Nachweis für 100 kg Person plus Ausrüstung wurde nicht erbracht.** Die Zahlen sind ausdrücklich bedingte Rechenfälle und keine freigegebenen Betriebswerte.

Die Kreisbahn-Revisionen [Kreis R03](kreis_r03/README.md) und [Kreis R04](kreis_r04/README.md) ersetzen die Umlaufbahn durch einen Kreis mit r = 450 mm: 2 × 8 gegenläufige Flügel, Führungen bei r = 130 / 770 mm. R04 vergleicht Varianten mit und ohne Außenring. **Beide Verzeichnisse sind eine Rekonstruktion:** Der ursprüngliche Arbeitsstand lag in einer nicht mehr erreichbaren Cloud-Umgebung und wurde nie übertragen; siehe [Übernahme- und Rekonstruktionsprotokoll](docs/R03_R04_Rekonstruktion.md). Neu erzeugt wurden der Geometrievergleich (−26,1 % überstrichene Fläche je Ebene), native FreeCAD-Modelle (R03/R04 mit Außenring je 1 744 Körper, ohne Außenring 948), Massenszenarien (erfasste Modellmasse 63,2 bzw. 26,7 kg, keine Fahrzeugmasse), ein Balkenmodell der Pitchwelle und Gmsh-Sektornetze. **Die 3D-CFD-Studie ist unvollständig: Es gibt kein akzeptiertes CFD-Ergebnis.**

Der historische Stand des 1:4-Taumelmodells [P10](modell_r04_taumel/integration_p10/README.md) umfasst:

- Servohalter mit Lastpfad
- eine Planetenstufe (Hohlrad + 3 Planeten)
- einen modellierten Kabelbaum
- ein Kufenlandegestell

Der [Flugsimulator](modell_r04_taumel/simulation/H01_Flugsimulator.html) zeigt standardmäßig P11 und bietet ältere Fälle als Archiv in 3D, animiert aus der Physik, mit Strömungsdarstellung sowie Bodenstart und Landung. Das ist weiterhin ein Konstruktionsentwurf ohne Freigabe.

Verbindliche Ziele sind maximal **2100 × 1700 × 600 mm** Fahrzeugabmessungen einschließlich Rotoren und Schutz, **100 kg Personengewicht zuzüglich Ausrüstung**, mindestens **15 Minuten Flugzeit** und ungefähr **80 km/h** Zielgeschwindigkeit. Gewünscht sind eine selbststabilisierende Winkelregelung entsprechend ANGLE MODE und native, editierbare FreeCAD-Dateien. Die Fahrzeughöhe wird bisher ohne Person verstanden; Missionsprofil und Ausrüstungsmasse sind noch offen.

Der geometrische Referenzentwurf verwendet sechs Rotorpositionen in einem rechteckigen 3×2-Raster. Der bisherige 650-mm-Rotoransatz und der neue X605-Kandidat mit nominell 558,8 mm Propellerdurchmesser müssen getrennt bewertet werden. Der untersuchte Tattu-41000-Pack liefert im bisherigen Modell zu wenig Dauerleistung. Für den X605 fehlen verifizierte Herstellerkennfelder.

Keine Variante ist bislang als sicher, baubar oder personenflugfähig nachgewiesen. CAD-Konzepte und idealisierte Rechnungen ersetzen keinen konstruktiven oder experimentellen Nachweis.
