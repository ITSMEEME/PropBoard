# Cohexial Study – R04-Taumelmodell 1:4, Fertigungsentwurf F01

Stand: 30.10.2026. Grundlage: `modell_r04_taumel/cad/parameter.json` und `erstellen.py`.

**Dokumentierter Fertigungsentwurf, keine Fertigungsfreigabe.** Das vorhandene V1-Modell enthält noch unvollständige Befestigungen und Kaufteilplatzhalter. Die Dateien erfassen den tatsächlich modellierten Stand; fehlende Anschlüsse sind nicht durch willkürlich gewählte Bohrungen oder Gewinde ersetzt. Kein Belastungs-, Lebensdauer- oder Flugnachweis.

## Dateien und Verwendung

- `../R04_Taumelmodell_1zu4.FCStd`: native Gesamtbaugruppe in Schwebestellung; gruppierte BRep-Körper, Bauteilkennungen und Massenansätze.
- `Einzelteile/*.FCStd`: 13 Eigenfertigungs-/Zuschnittpositionen, jeweils geometrisches Python-Feature, bearbeitbare Parametertabelle und native TechDraw-Seite mit drei Ansichten und assoziativen Hüllmaßen.
- `STEP/*.step`: je Position ein Festkörper; Kontrollimport mit Volumenvergleich im Geometrieprotokoll.
- `STL/*.stl`: zwölf Druckteilvarianten; Millimeter. STL enthält keine Einheit. Herkunft ist der jeweilige lokale Einzelteilkörper; keine Slicer- oder Stützstrukturdaten.
- `Zeichnungen/*.svg`, `Fertigungszeichnungen_F01.pdf`: drei orthogonale Ansichten aus FreeCAD/OpenCASCADE-HLR, Hüllmaße und Nennmaßtabellen. Der 3D-Datensatz definiert die komplexen Konturen. Die Tabellen ersetzen keine noch fehlende Passungs- und Toleranzauslegung.
- `Fertigungsstueckliste.csv`: Mengen, Werkstoffe, Verfahren und offene Punkte. `../Stueckliste.csv` umfasst zusätzlich modellierte Kaufteile; keine vollständige Bestellliste für die noch fehlenden Befestigungen.
- `Druckorientierung.csv`: begründete Orientierungs- und Nacharbeitsvorschläge; kein validierter Slicerauftrag. Insbesondere die Halteplatte benötigt wegen der knappen Bettbreite eine gesonderte Lageprüfung.
- `Profil_NACA0012.csv`: Nennprofil einschließlich der angehobenen Hinterkante; die CAD-Kontur verwendet eine polygonale Abtastung.
- `Parameterstand.json`, `Geometriepruefung.json`: Eingabestand und Exportprüfungen.
- `Pruefbericht_V1_vor_Korrektur.json`: gesicherter fehlgeschlagener Vorlauf als Vergleich zum korrigierten F01-Stand.
- `Validierung.json`: Wiederöffnungs-, Parameteränderungs- und Dateiprüfungen, sofern erfolgreich erzeugt.

## Bearbeiten in FreeCAD

FreeCAD **1.0.2** verwenden. Die vorinstallierte 1.0.0-Python-Bibliothek stürzte hier bei `Part.makeCompound` ab. Die offizielle 1.0.2-AppImage wurde gegen die veröffentlichte SHA-256-Prüfsumme geprüft.

1. Paketstruktur erhalten und `../Fertigung_oeffnen.FCMacro` in FreeCAD ausführen. Damit wird `fertigung_features.py` importierbar. Python-Makros nur aus dieser geprüften Projektquelle ausführen.
2. Gewünschtes Einzelteil öffnen. Im Blatt **Parameter** stehen Parameterpfad und Wert. Zahlen in mm bzw. Grad; Texte und Listen als JSON bearbeiten. Die Baugruppe folgt nicht automatisch den separat bearbeiteten Einzelteilen.
3. Dokument neu berechnen. Das Feature **Bauteil** baut den Festkörper aus den Tabellenwerten neu auf. Die drei primären TechDraw-Ansichten und Hüllmaße folgen dem Bauteil. Zusätzliche Schnittkonturen sind Momentaufnahmen und müssen nach Änderungen neu erzeugt werden. Die textuellen Nennmaßtabellen bezeichnen fest den F01-Stand; sie ändern sich nicht automatisch. Bei Zahnkranzdeckeln ist die separate vereinfachte Zeichnungsgeometrie ebenfalls eine F01-Momentaufnahme und muss nach einer Parameteränderung neu erzeugt werden.
4. Nach Änderungen STEP/STL und PDF neu erzeugen und Kollisionen erneut prüfen. Die im Paket mitgelieferten SVG/PDF/STEP/STL sind Momentaufnahmen des F01-Stands.

Dies ist ein skriptparametrischer Aufbau, kein Sketcher-/PartDesign-Featurebaum mit einzeln editierbaren Taschen. Die Geometrie bleibt auch ohne das Python-Modul sichtbar; für parametrische Neuberechnung wird es benötigt. Für eine gemeinsame neue Revision die geänderten Werte auch in `../parameter.json` übernehmen und den gesamten Erzeugungslauf wiederholen. Nicht nur einzelne Exportdateien ersetzen.

Das Einzelteilkoordinatensystem wird auf die Minimalwerte X/Y/Z verschoben. Die in den Tabellen genannten Radien und z-Positionen beziehen sich, soweit angegeben, auf den ursprünglichen Rotorrahmen. Montagepositionen sind in der Baugruppe gespeichert.

## Vor Fertigung verbindlich zu schließen

| Schnittstelle | Aktueller CAD-Stand | Noch erforderlich |
|---|---|---|
| Sechs Servos | 9-g-Hüllkörper ohne gewähltes Produkt | Herstellerzeichnung, Horngeometrie, Befestigungslöcher, Schrauben, Steckerraum und realer Stellweg |
| Pitchhebel | Vierkantaufnahme, aber kein Kugelbolzenanschluss | Kugelbolzenprodukt, Aufnahme, Verschraubung und axiale Hebelsicherung |
| Taumelscheiben-Innenring | Arme ohne Befestigung für radiale Kugelbolzen/Führungsstift | Bohrungen, Gewinde bzw. Einsätze, Randabstände und Sicherung |
| Mitnehmerstift | D3 mit 3 mm Einbindung in D3.1-Bohrung bei r31.5 | Axiale Sicherung, Befestigungsart und tragfähige Einbindelänge nachweisen |
| Klemmring und Halteplatte | Ring bzw. geschlitzter Kragen ohne Klemmschraube | Schraubanschluss und axiale Sicherung beider Rotoren |
| Kappen | Am Rohrende angeordnet; Einsteckhülse D27.8 in Rohrbohrung D28 | Axiale Sicherung, durchgehender Lastpfad und Toleranzen |
| Kugel-Gleitlager | Geschlossene Gleitkugel und geschlossener Innenring | Nachvollziehbare Montagefolge, ggf. konstruktive Teilung, Oberflächen und Schmierung |
| Lager 6806/6809 | Nennmaße und vereinfachte Hüllkörper | Lagerhersteller, Passungen, Sitztoleranzen und axiale Sicherungen |
| Flügelzapfen / Querstifte | D10/D10.4 und Nut mit zwei D2-Stiften | Festigkeit von Zapfen/Nut/Stiftsitz, Verschleiß, Montage- und Sicherungsverfahren |
| Steuer-/Servostangen | Geometrische Verbindungen mit Kugelmitten | Reale Gelenke, Gewindelängen, Einstellbarkeit, Gelenkwinkel und Kollisionshüllen |
| Motor / Ritzel | Hüllkörper und geometrische Verzahnung | Produktzeichnung, Wellenbefestigung, axiale Ritzelsicherung und Zahneingriff unter Last |
| Mittelrohr | D30 x 1, Länge 192, Legierung offen | Material, Geradheit, Sitz- und Endtoleranzen, Lastnachweis |
| Elektro-/Prüfstandsaufbau | Akku/Elektronik überwiegend Massenansatz | Mechanische Befestigungen, Leitungsführung und Prüfstandsadapter |

## Geometriekorrekturen gegenüber V1

- Mitnehmerstift von r30.5 auf r31.5 versetzt, um Kontakt mit dem Taumelscheibenlager zu vermeiden. D3.1-Aufnahme und 3 mm Einbindung ergänzt; Stiftlänge jetzt 19.5 mm. Sicherungsart ist noch offen.
- Die stationäre Führungsnut von 3.4 auf 4.0 mm verbreitert und die untere 1-mm-Bodenbrücke entfernt, die den Führungsstift bei minimalem Kollektiv schnitt. Die Führung ist jetzt nach unten offen. Die Mitnehmerschlitze im Drehring bleiben 3.4 mm.
- Kappen am Ende des 192-mm-Mittelrohrs angesetzt, statt im Halteplattenkragen. Die Einsteckhülse ist D27.8/D24 x 8; im D28-Innenrohr verbleibt ein nominelles radiales Spiel von 0.1 mm. Dies ist eine Entwurfsannahme und keine freigegebene Passung.

Die Vorrevision zeigte bis zu etwa 1.38 mm³ Führungsstift-/Halteplattenüberdeckung sowie etwa 2344.18 mm³ Kappen-/Halteplattenüberdeckung je Kappe. Der aktuelle Stand wird vollständig neu geprüft; Befestigungs- und Festigkeitsfragen werden durch diese Kollisionskorrekturen nicht gelöst.

## Nennmaße, Werkstoff und Druck

Es wurde **keine Allgemeintoleranz** und keine H7/g6-Passung angenommen. Vorhandene Spiele (z. B. D30.3 auf D30, D42-Sitze oder D58.1-Bohrung) sind Entwurfsnennmaße, keine freigegebenen Passungen. D2.5-Modellbohrungen sind keine ausgearbeiteten Gewinde. Gewindeeinsätze, Schraubenlängen, Unterlegscheiben und Sicherungen fehlen teilweise.

PA-CF für drehende Teile und PETG für stationäre Halter sind übernommene Entwurfsannahmen. Sorte, Faseranteil, Feuchtezustand, Druckrichtung, Schichtdicke, Perimeter, Füllung und Temperung sind nicht freigegeben. Die ursprünglichen effektiven Füllgrade dienen ausschließlich der Massenschätzung. Vor Strukturversuchen Probekörper und Passungsproben herstellen. Die STL-Lage ist ein gemeinsames geometrisches Bezugssystem, keine optimierte Druckorientierung. Das Hüllmaß passt gegebenenfalls aufs Druckbett, bescheinigt aber weder Supportfreiheit noch Druckbarkeit oder Festigkeit.

Die 130-Zähne-Deckel sind oben und unten verschieden. Pitchhebel sind durch Wenden identische Teile. Die Zahnkontur ist eine polygonal angenäherte Evolvente; Zahnqualität und realer Druck-/Fräsprozess müssen festgelegt werden. Flügel gleicher Masse fertigen und den kompletten Rotor auswuchten; CAD-Masse ist kein Wuchtprotokoll.

## Prüfumfang und Montage

Die STEP-Prüfung verlangt weniger als 0,01 % relative Volumenabweichung und weniger als 0,01 mm Abweichung in den sechs Hüllgrenzen. Bei der Nabe zeigten native und rückimportierte getrimmte Flächen geringfügig andere OCCT-Integrationswerte; zwei unabhängige Netze mit 0,005 mm Deflektion bestätigten eine kleine Differenz. Die tatsächlichen Abweichungen stehen je Teil im Protokoll. Diese numerischen Exportgrenzen sind keine Bauteiltoleranzen.

Die zusätzliche Baugruppenprüfung untersucht ausdrücklich auch Kappe gegen Halteplatte, da dies im ursprünglichen Algorithmus nicht enthalten war. Erkannte Kollisionen bleiben als fehlgeschlagene Baugruppenprüfung sichtbar; der Prüflauf schreibt sein Protokoll und endet dann mit Status 1.

Die geometrische Prüfung kontrolliert Festkörpergültigkeit, Einzelkörper, Hüllmaße, STEP-Rückimport, STL-Geschlossenheit und Wiederöffnen der FreeCAD-Dateien. Das Baugruppenskript untersucht ausgewählte Kollektiv-/Zyklik-/Rotorwinkelzustände. Kontaktpaare und gleichartige Teile werden im bestehenden Kollisionsalgorithmus teilweise ausgefiltert; ein leerer Kollisionsbericht ist keine vollständige Montierbarkeits- oder Bewegungsraumprüfung. Auch die Länge der montierten Stangen wird gegen ein idealisiertes Kinematikmodell geprüft.

Geplante Montagegruppen: Mittelrohr/Abstützung; Lagerringe und Naben; Flügel mit Pitchhebeln und Querstiften; gesonderte obere/untere Deckel; Gleitkugel/Innenring/6809/Drehring; verstellbare Stangen; Motor/Ritzel; Servos und axiale Sicherungen. **Diese Reihenfolge ist vorläufig**, insbesondere kann die geschlossene Kugelpaarung eine konstruktive Teilung erfordern. Es liegt keine geprüfte vollständige Montageanleitung vor.

## Reproduzieren

Aus dem Repository-Verzeichnis mit der geprüften, entpackten FreeCAD-1.0.2-Version:

```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/cad/erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/cad/fertigung_erstellen.py
.cfd-tools/venv/bin/python modell_r04_taumel/cad/fertigung_pdf.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/cad/fertigung_pruefen.py
```

PDF-Export benötigt svglib 1.5.1, reportlab 4.4.9 und DejaVu Sans (`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`). Alle Ausgaben dieses Workflows liegen unter `modell_r04_taumel/cad`. Nach Parameteränderungen ist der gesamte Ausgabe- und Prüfablauf zu wiederholen. Keine Ergebnisdatei mit bestandenen Prüfungen gleichsetzen, solange der aktuelle Lauf nicht abgeschlossen ist.

Das vollständige Paket lässt sich nach erfolgreicher Validierung mit `.cfd-tools/venv/bin/python modell_r04_taumel/cad/fertigung_paket.py` erzeugen. `SHA256SUMS_Gesamt` im ZIP prüft auch die mitgelieferten Quellskripte und Baugruppendateien.

## Abgeschlossener Prüflauf F01

- 13 native Einzelteilmodelle wieder geöffnet; je ein gültiger Festkörper, drei assoziative Hüllmaße und drei bzw. vier TechDraw-Ansichten geprüft.
- Parameteränderung der Flügelsehne 30 → 31 → 30 mm einschließlich nachgeführter Bemaßungsbezüge erfolgreich; unabhängige Kopien der zwischengespeicherten Geometrie geprüft.
- 13 STEP-Rückimporte bestanden. Größte relative Volumenabweichung etwa 0,00174 %, größte Abweichung einer Hüllgrenze etwa 0,00998 mm.
- 12 geschlossene STL-Dateien mit positivem Volumen geprüft; 13-seitiger A4-Zeichnungssatz erzeugt und repräsentative Blätter visuell kontrolliert.
- Gesamtbaugruppe: 164 gültige Körper. Alle 12 ausgewählten Bewegungsfälle für beide Rotoren bestanden; keine gemeldeten Überdeckungen zwischen den Ebenen.
- Zusätzliche Führungsstiftprüfung: 24 Kombinationen, jeweils 0 mm³ Überdeckung mit der tatsächlich gespeicherten Halteplatte. Kappe gegen Halteplatte und Rohr ebenfalls ohne Überdeckung.

Diese Ergebnisse gelten für den gespeicherten F01-Stand und den beschriebenen Prüfumfang. Sie ersetzen die oben aufgeführten offenen Schnittstellen-, Montage-, Werkstoff- und Festigkeitsnachweise nicht. Insbesondere bleibt **keine Fertigungsfreigabe** erteilt.
