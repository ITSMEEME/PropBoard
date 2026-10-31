# Projektübergabe: Personengetragenes elektrisches Hoverboard

**Aktuell: P11 – Direktantrieb 1:1 mit kugelgelagerten Führungsrollen.**
[Native Konstruktion und technische Grenzen](../modell_r04_taumel/integration_p11/README.md) ·
[Visueller Physik-Prüfstand](../modell_r04_taumel/simulation/Physik_Pruefstand.html) ·
[Flugsimulator](../modell_r04_taumel/simulation/H01_Flugsimulator.html).
P10 und frühere Revisionen bleiben historische Vergleichsstände. Der spätere Ringmotor
ist noch auszuwählen; EMAX bleibt die elektrische Vergleichsreferenz.

Stand: 28.10.2026. Quelle ist die vom Nutzer übermittelte Projektübergabe. Historische Rechen- und Testergebnisse sind übernommene Angaben und wurden in dieser Sitzung nicht erneut validiert. Produktangaben sind ohne unabhängigen Quellenabgleich dokumentiert.

## Anforderungen und offene Entscheidungen

- Frei fliegendes Board im Stil „FPV-Drohne + Skateboard“.
- Bis 100 kg Personengewicht, Ausrüstung zusätzlich; 10 kg Ausrüstung sind lediglich eine bisherige Rechenannahme.
- Maximal 2100 × 1700 × 600 mm einschließlich Rotoren und Schutz; Höhe bisher ohne Person interpretiert.
- Mindestens 15 Minuten Flugzeit; offen ist, ob Schweben oder ein gemischtes Missionsprofil gemeint ist.
- Ungefähr 80 km/h Zielgeschwindigkeit.
- Selbststabilisierende Winkelregelung entsprechend ANGLE MODE.
- Native, editierbare FreeCAD-Dateien.
- Noch offen: Flughöhe, Windbereich, Temperatur, Einsatzland und rechtlicher Rahmen.

Keine Variante ist als sicher, baubar oder personenflugfähig nachgewiesen.

## Geometrischer Referenzentwurf

Alle Maße in mm. Sechs Rotorzentren bilden das kartesische Produkt x = −690, 0, +690 und y = −505, +505. Der Ursprung liegt ungefähr im Fahrzeugzentrum auf der ursprünglich angenommenen Rotorebene.

| Größe | Wert |
| --- | --- |
| Ursprünglicher Rotordurchmesser | 650 |
| Ring-Platzhalter außen / innen / Höhe | 680 / 668 / 70 |
| Berichtete Außenmaße | 2060 × 1690 × 320 |
| Standdeck | 1200 × 300 × 60 |
| Deckunterseite z | 170 |

Die Ringe sind keine ausgelegten Schutzvorrichtungen. Materialien, Querschnitte, Verbindungen und Schutzwirkung sind nicht nachgewiesen. Für eine vollständige Rekonstruktion fehlen insbesondere Rahmen-, Arm- und Fahrwerksdetails.

## Ideales Schwebe-Rechenmodell

```text
rho = 1,225 kg/m³
g = 9,80665 m/s²
FM = 0,60
eta = 0,92
A = n × pi × D² / 4
T = m × g
P_elektrisch = T^(3/2) / (sqrt(2 × rho × A) × FM × eta)
```

Sechs unabhängige 650-mm-Rotorflächen ergeben A = 1,990984 m². Das Modell gilt für Schweben außerhalb des Bodeneffekts. FM und Wirkungsgrade sind Annahmen. Abschattung, Rotorinteraktion, Rahmen, Schutz, Wind und Vorwärtsflug sind nicht validiert. Bei Koaxialrotoren dürfen überlagerte Flächen nicht doppelt als unabhängige Fläche gezählt werden. Reale Kennfelder des gesamten Systems sollen dieses Modell ersetzen.

## Massen und generischer Akkuvergleich

Ohne Akku werden 155 kg angenommen: Person 100 kg, Ausrüstung 10 kg und Nicht-Akku-Systeme 45 kg. Die 45 kg sind kein geschlossener konstruktiver Massennachweis.

Vergleichsannahmen: 180 Wh/kg auf Packebene und 80 % eingeplante Nennenergie. Die verbleibenden 20 % sind keine festgelegte sichere Notreserve.

| Akku | Gesamtmasse | Modell-Schwebeleistung | Energiebezogene Schwebedauer |
| --- | --- | --- | --- |
| 30 kg | 185 kg | 63,38 kW | 4,09 min |
| 40 kg | 195 kg | 68,59 kW | 5,04 min |

Für 15 Minuten Schweben bei 195 kg und unverändertem 40-kg-Akku ergeben sich rund 21,4 kWh Nennenergie bzw. 536 Wh/kg bei gleichzeitig ungefähr 69 kW Dauerleistung. Ein geeigneter Pack ist nicht nachgewiesen.

Die mathematische Akku-Massenoptimierung bei unverändertem übrigen Modell ergibt 310 kg Akku, 465 kg Gesamtmasse und etwa 10,6 Minuten Schweben. Dies liegt außerhalb des Entwurfs und ist keine allgemeine physikalische Flugzeitgrenze.

## Tattu 41000 mAh 6S

Nutzerquelle: https://www.genstattu.com/4-45v-ultra-high-voltage/

Übermittelte Produktdaten: 41 Ah, 23,7 V nominal, 26,7 V vollgeladen (4,45 V/Zelle), 60 A maximaler Dauerstrom, 100 A Peak mit ungeklärter Textangabe „≤3S“, Masse 3790 g ±20 g, 230 × 104 × 70 mm, QS8, G-Tech-7P, Entladekabel 8# / 150 mm. Beworben werden 280 Wh/kg.

Aus den Nennwerten folgen 971,7 Wh, 256,4 Wh/kg und 1,422 kW nominale Dauerleistung pro Pack. Die beworbenen 280 Wh/kg sind daraus nicht reproduzierbar; ein gemessenes Energieintegral fehlt.

Acht CAD-Gehäuse: x = −440, −190, +190, +440; jeweils y = −57 und +57; Unterseite z = 70. Gesamtanordnung 1110 × 218 × 70 mm. Berichtet sind mindestens 10 mm Gehäuseabstand und keine Berührung mit anderen Ergebniskörpern. Stecker, Kabelbögen, Halter, Kühlung, Isolation und Ausdehnung fehlen.

| Acht Packs | Wert |
| --- | --- |
| Masse | 30,32 kg |
| Nennenergie | 7,7736 kWh |
| Dauerleistung nominal / bei Volladung | 11,376 / 12,816 kW |
| Modell-Gesamtmasse | 185,32 kg |
| Modell-Schwebebedarf | 63,549 kW |

Die nominale Dauerleistung deckt nur rund 18 % des Modellbedarfs. Mehr identische Packs erreichen selbst beim mathematischen Optimum innerhalb desselben festen Modells nominal nur etwa 46 %. Dieser Pack versorgt den Entwurf nicht ausreichend. Solange die Dauerleistung fehlt, darf eine Energie-/Leistungsrechnung nicht als erreichbare Flugzeit ausgegeben werden.

## T-Motor X-605: ungeprüfter Kandidat

Produktlink: https://shop.tmotor.com/products/x-605-coaxial-integrated-propulsion-system

Aus einer früher bereitgestellten Zeichnung wurden Ø72 mm Motorkörper, 112,3 mm Körperhöhe, 121 mm Gesamthöhe und 124,8 mm Ausdehnung einschließlich seitlicher Aufnahme abgelesen. Weitere Angaben: Ø30, Ø32, Ø18, Ø12 und 4-M3. Bezugslagen, Aufnahme, Bohrbild und Propellerebenen sind nicht vollständig bestimmt.

Das berichtete Bauraummodell enthält einen Zylinder Ø72 × 112,3 mm und eine separate überlappende Referenzhülle 124,8 × 72 × 121 mm. Die Motorachsenlage enthält eine dokumentierte Modellannahme; es ist keine vollständige Produktgeometrie.

Die hier nicht vorliegende Datei `TMOTOR_X605_Codex.md` bezeichnet sich als Offline-Snapshot vom 28.10.2026. Genannt werden MN605-S KV170 mit Alpha 60A HV / 12S, MN605-S KV320 mit Alpha 60A LV / 6S, P22×6.6, Rohrkompatibilität 25 / 30 mm und 525 USD. Abruf, Lieferumfang, Preis und Verfügbarkeit sind nicht unabhängig bestätigt.

22 Zoll entsprechen 558,8 mm. Sechs unabhängige Positionen ergeben damit nur 1,47148 m² Rotorfläche, rund 26 % weniger als beim 650-mm-Ansatz. Die Aussage „zwei Motoren pro Modul, zwölf bei sechs Modulen“ ist unbestätigt.

Es fehlen numerische Herstellerkennfelder sowie Systemgewicht, Dauerschub, zeitbegrenzter Maximalschub, Spannung/Strom/Leistung am selben Betriebspunkt, thermische Bedingungen, Propellerzuordnung und Anzahl Motoren/ESCs pro Verkaufseinheit.

## Flugcontroller und Regelung

Pixhawk 6X mit ArduPilot Copter ist ein Kandidat, keine endgültige Auswahl oder Freigabe für Personenbetrieb. Stabilize entspricht grundsätzlich einer Winkelregelung: neutrale Roll-/Pitch-Eingaben richten die Lage aus, liefern allein jedoch keine Höhen- oder Positionshaltung.

Beweglicher Personenschwerpunkt, Vibrationen, Sättigung und Fehlerfälle sind gesondert zu untersuchen. Das rechteckige 3×2-Raster ist kein reguläres Hexagon; Mixer, Drehrichtungen, Gierautorität und Stellreserven müssen zur tatsächlichen Geometrie passen. Abschalten im Flug ist kein universell sicherer Notfallmodus. FPV ersetzt keine Zustandsüberwachung.

## Serieller Benzin-Hybrid: feste Rechenstudie

Masse ohne Kraftstoff: Person 100 kg; Ausrüstung 10 kg; Rahmen/Deck/Schutz/Fahrwerk 25 kg; sechs Hubmotoren mit Propellern 12 kg; Steller 4 kg; Leistungsverteilung 3 kg; Avionik 2 kg; Verbrenner/Generator/Kühlung/Abgas 55 kg; Pufferakku 10 kg; Tank/Kraftstoffsystem 3 kg. Summe 224 kg.

Annahmen: Generatorwirkungsgrad 0,92, Verbrenner-Bremswirkungsgrad 0,28, Benzinheizwert 12 kWh/kg, 15 Minuten Schweben bei konstantem Startgewicht, 20 % des geladenen Kraftstoffs nicht verplant.

| Ergebnis | Wert |
| --- | --- |
| Kraftstoff / Startmasse | 9,0605 / 233,0605 kg |
| Elektrische Schwebeleistung | 89,6247 kW |
| Generator-Wellenleistung | 97,4182 kW |
| Kraftstoffleistungszufuhr | 347,9221 kW |
| Verluste vor Hubantrieben | 258,2974 kW |
| Verbrauch in 15 Minuten | 7,2484 kg |

Die Verluste verteilen sich auf Abgas, Kühlung und weitere Anteile; sie sind keine alleinige Kühlerleistung. Ein reales 55-kg-Komplettaggregat ist nicht nachgewiesen. Reserveleistung, thermische Integration, Einbau, Zielgeschwindigkeit und Budget sind offen. Kein baureifer Vorschlag.

## Historische Prüfungen und CAD-Grenzen

Laut Übergabe bestanden: algebraische Referenz-/Skalierungstests, Außenmaßprüfung, idealisierte Rotor-/Ringabstände, Deck-/Rotorbereichstrennung, Speichern und Wiederöffnen der FreeCAD-Dateien, Änderung und Rücksetzung des Rotordurchmessers, STEP-/STL-Export sowie Tattu-Gehäuseabstände.

Eine berichtete Kontaktprüfung ohne Rotorwirkflächen ergab 25 Körper und 11 getrennte Kontaktkomponenten. Sechs Ringe und vier Landefüße haben keine Rahmenanbindung. Körperkontakt beweist keine tragfähige Verbindung; Akku-Platzhalter sind keine tragende Struktur.

Nicht durchgeführt: Hardware-, Schubprüfstands- oder Akku-Lasttests, Struktur-/Ermüdungsnachweise, CFD/Windkanal, dynamische Simulation mit Person, Hardware-in-the-loop sowie unbemannte oder bemannte Flugversuche. Die historischen Prüfungen sind keine Flug- oder Sicherheitsvalidierung.

Native CAD-Struktur laut Übergabe: benannte Part-Grundkörper, boolesche Ringe, Spreadsheet-Parameter mit Expressions, getrennte Gruppen für Rahmen, Antriebe, Ringe, Akku und Fahrwerk. Rasterparameter verschieben Rotorzentren, aktualisieren aber Arme nicht vollständig; Rasteränderungen benötigen Änderungen am Erzeugungsskript. Konzeptmodelle, keine Fertigungszeichnungen.

## Dateien der bisherigen Umgebung

Die folgenden Pfade sind historische Verweise, keine verfügbaren Repository-Dateien:

```text
/workspace/hoverboard/Klaerungsstand.md
/workspace/hoverboard/Lastenheft_210x170x60.md
/workspace/hoverboard/Hybrid_Festgelegte_Rechenstudie.md
/workspace/hoverboard/freecad/Hexacopter_650_Konzept.FCStd
/workspace/hoverboard/freecad/Hexacopter_erstellen.py
/workspace/hoverboard/freecad/Verbindungen_pruefen.py
/workspace/hoverboard/tattu41000/Hexacopter_Tattu41000_8Packs.FCStd
/workspace/hoverboard/tattu41000/Tattu_einbauen.py
/workspace/hoverboard/tattu41000/Tattu_Pruefbericht.json
/workspace/hoverboard/tmotor_x605/Tmotor_X605_Bauraum.FCStd
/workspace/hoverboard/tmotor_x605/X605_Bauraum_erstellen.py
/workspace/hoverboard/tmotor_x605/Quellenabgleich.md
/workspace/Hoverboard_Projektbackup.zip
```

Das historische Backup enthielt laut Übergabe 45 Dateien, bestand eine ZIP-Integritätsprüfung, konnte jedoch nicht heruntergeladen werden und entstand vor den letzten X605-Ergänzungen.

## Abgleich mit dieser Sitzung

`/workspace/hoverboard` und das Backup fehlen hier. FreeCADs Kommandozeilenprogramm ist unter `/usr/bin/freecadcmd` vorhanden. Die genannten CAD- und Referenzdateien wurden nicht übernommen oder nachgeprüft.

Der Aufruf `freecadcmd --version` ist in dieser Sitzung mit einem Segmentation Fault abgestürzt. Die bloße Installation belegt daher keine einsatzfähige CAD-Umgebung; vor einer Rekonstruktion muss der Startfehler untersucht werden.

Anders als in der früheren Umgebung existiert hier ein Commit im Checkout `/workspace/PropBoard`: `56ae21eeeaab80e0c1a20340b2c8547c4bb578d5`. Beim Onboarding stimmte dieser mit dem remote abgefragten `main` überein. Git-Lesezugriff funktionierte über den vorhandenen Proxy nach Ausführung außerhalb der Befehls-Netzwerksandbox. Das belegt weder aktuellen Herstellerzugriff noch Push-Rechte. Die README wurde lokal ergänzt; kein Push wurde ausgeführt.

## Nächste Arbeitsschritte

1. Originaldateien übernehmen, soweit sie wieder verfügbar werden. Eine Rekonstruktion muss fehlende Geometrien ausdrücklich als neue Annahmen kennzeichnen.
2. Originale X605-Schub-/Leistungstabellen und vollständige Varianten-/Lieferumfangsdaten beschaffen und prüfen.
3. Zuerst ausreichenden Dauerschub anhand realer Daten prüfen.
4. Danach Antriebsmasse, Gesamtmasse, Leistung und Akku gemeinsam neu berechnen.
5. Erst bei geschlossenem Leistungs- und Massenbudget konstruktive Details ergänzen.

Fehlende Herstellerwerte, Bauteileigenschaften oder Testergebnisse dürfen nicht erfunden werden. Das Gesamtziel bleibt unbewiesen.
