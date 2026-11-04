# Quad R380: umschaltbare Anschlüsse V1–V4

**Neue Nutzerunterlagen ausgewertet:** [MN1330-Prüfzeitbezug, CFK-Angaben und Reglerzeichnung](DATENNACHTRAG.md). Der Motor-Temperaturbezug bei 80 % Gas ist jetzt dokumentiert; keine Änderung der CAD-Geometrie oder Produktionsfreigabe.

[Lieferpaket mit Quellen und Prüfungen](Quad_Parametrisch_V1_V4_Paket.zip) · [Interaktive CAD-Ansicht](Projekt.html) · [FreeCAD-Datei](Ausgabe/Quad_Parametrisch_V1_V4.FCStd) · [Geometrie und Umschalter](Ausgabe/Varianten_Pruefung.json) · [Freiraumprüfung](Ausgabe/Freiraum_Pruefung.json) · [Browserprüfung](Ausgabe/Viewer_Pruefung.json)

Die Datei enthält den gemeinsamen Carbonrahmen, zwei verstellbare Fußplatten, vier MN1330-KV40-Zeichnungsreferenzen und vier eigene Dreiblattpropeller R380 sowie vier alternative Sätze von Auslegern. Rohre, Rahmenanschlüsse, integrierte Aluminium-Motorträger, Klemmkappen, Isolierlagen, Endpolster und Klemmverschraubungen wechseln gemeinsam. V3 ist beim Öffnen aktiv.

## Bedienung

In FreeCAD im Modellbaum **Variantensteuerung** auswählen, im Reiter **Daten** die Eigenschaft **Variante** auf V1, V2, V3 oder V4 setzen. Die Sichtbarkeit der zugehörigen AppLinks ist über Ausdrücke gekoppelt. Das Dokument enthält alle vier vorberechneten Geometriesätze. Im Browser wechselt „CAD-Konfiguration“ dieselben aus dem CAD exportierten Geometrien; die Browserauswahl speichert die native Datei nicht.

| Variante | Rohre je Motor | CFK Außen-/Innendurchmesser | Anordnung | Erfasste Teilmasse |
|---|---:|---|---|---:|
| V1 | 1 | 35/32 mm | einzelnes Rohr | 26,462 kg |
| V2 | 2 | 20/17 mm | vertikales V | 27,134 kg |
| V3 | 2 | 20/17 mm | horizontales V | 27,108 kg |
| V4 | 3 | 20/17 mm | Dreieck | 28,266 kg |

V2–V4 übernehmen das Rohrmaß CBU20171005TG aus dem bisherigen Aufbau. V1 benötigt ein zusätzliches, bislang nicht herstellerseitig belegtes Rohr Ø35/32 mm. Die geringste modellierte Masse von V1 belegt keine ausreichende Steifigkeit oder Tragfähigkeit. Akku, Regler, vollständiger Kabelbaum, Schutzstruktur, Fahrwerk und Motor-Nabenschrauben sind in diesen Massen nicht enthalten. Ein globales Gewichtsoptimum wurde nicht nachgewiesen.

## Mechanischer Aufbau

Die vier Motorknoten sind je Variante identische, gedrehte Kopien. Jeder Motorträger wird aus einer Hälfte und ihrer exakten Spiegelung aufgebaut: integrierte Rohrklemmen, Verbindungsrippen und vier Befestigungsaugen auf dem angenommenen 50-mm-Lochkreis. Eine zusätzliche separate Motor-Montageplatte entfällt. Auch die Rohr-/Rippenanordnung der Rahmenknoten ist symmetrisch; die übernommenen Rechtsgewinde im Kernknoten sind keine spiegelbaren Linksgewinde.

Die Rohrklemmung besitzt 35 mm Eingriffslänge, geteilte Kappen, Isolierlagen und 0,3-mm-Endpolster. Je Rohr und Ende sind zwei M4×30-Schrauben mit Muttern und beidseitigen Scheiben modelliert. Insgesamt sind es 16/32/32/48 Schrauben-Mutter-Paare. Die Schrauben und Muttern besitzen tatsächliche Schraubengeometrien aus dem dokumentierten FastenersWB-Stand.

Die Armwurzel liegt radial bei 210 mm, der übernommene Rahmenanschluss bei 145 mm. Die oberen Endpunkte der Ø20-mm-Rohre liegen relativ zum Motorbezug bei −22 mm; das verhindert tangentiale Nullstärken im Motorknoten. Die nominale Klemmbohrung beträgt Rohrdurchmesser +0,6 mm. Im unteren Klemmenkörper ist zusätzlich 0,01 mm radialer CAD-Freiraum berücksichtigt. Das sind Modellannahmen, keine freigegebenen Fertigungstoleranzen.

## Nachweise und Grenzen

Der native Umschalter wurde in allen vier Stellungen geprüft: 4/8/8/12 aktive Armrohre und jeweils vier passende Motor- und Rahmenknoten. Alle neuen Geometrieprototypen wurden als gültige Einzelvolumenkörper geprüft. Die lokale Überschneidungsprüfung der Anschlusskörper ist bestanden. Die nominale M4-Schrauben-Mutter-Paarung erreicht bei 34° Phasenlage 0,07048 mm³ rechnerische Restüberschneidung bei einer Prüfschwelle von 0,1 mm³; das ist kein Gewindetoleranznachweis.

`Freiraum_Pruefung.json` dokumentiert zusätzlich sämtliche neuen Teile einschließlich Verschraubungen an allen vier Auslegern gegen einander und gegen die gemeinsamen Rahmenbauteile in der Grundstellung. Die Z-Abstandsprüfung der neuen Teile berücksichtigt alle Rotorwinkel und die reine Längsverschiebung der Fußsysteme. Die Prüfschwelle ist 0,1 mm³; elastische Verformung, Vorspannung, Fertigungstoleranzen und Werkzeugzugang sind nicht abgedeckt.

**Die übernommenen D06-Kollisionen zwischen Propellerumlauf und Fußschienen-Endknoten beziehungsweise Strebenanschlüssen bleiben offen.** Die Ansicht markiert diese Teile rot. Es gibt daher keine Freigängigkeit des Gesamtfahrzeugs. Auch Festigkeit, CFK-Laminat, Klemmpressung, Dauerfestigkeit, Motor-OEM-Geometrie und Antriebsleistung sind nicht freigegeben. Der Stand ist ein detaillierter CAD-Entwurf, keine Produktions- oder Flugfreigabe.

## Reproduktion

Die Bedienung benötigt nur die native Datei; alle verwendeten Formen sind eingebettet. Maßänderungen erfolgen in den Python-/JSON-Parametern und erfordern einen Neuaufbau. Es gibt noch keine durchgängige GUI-Maßsteuerung mit Feature-Historie für jedes Einzelteil.

Das Lieferpaket bewahrt die benötigten relativen Projektpfade. Voraussetzungen: FreeCAD-Python einschließlich Part, PartDesign, Import und MeshPart (hier FreeCAD 1.0.0 unter `/usr/lib/freecad-python3/lib`). Aus dem Paketstamm in dieser Reihenfolge ausführen:

```sh
/usr/bin/python3 quad_r380_varianten/aufbau.py
/usr/bin/python3 quad_r380_varianten/fertigstellen.py
/usr/bin/python3 quad_r380_varianten/pruefen.py
/usr/bin/python3 quad_r380_varianten/viewer_export.py
```

`aufbau.py` liest die D06-Basis, die beiden benötigten D07-Kerngeometrien, `quad_r380_d07/parameter.json`, den Geometriehelfer und `motoranschluss_varianten/Varianten.json`. `fertigstellen.py` ergänzt die mitgelieferten Normteil-BREPs und prüft den Umschalter. Die Normteil-Neuerzeugung über `normteile.py` ist optional und benötigt den in `Quellen/Normteile/Quellenmanifest.json` dokumentierten FastenersWB-Commit; die fertigen Formen und Lizenz sind beigefügt. `viewer_export.py` übernimmt die D06-Oberflächen für unveränderte Bauteile und erzeugt die neuen Oberflächen direkt aus dem aktuellen CAD.

`lieferung.py` erstellt nach erfolgreicher Freiraumprüfung die Stücklisten je Variante, prüft ihre Massensummen und bündelt CAD, Quellen, Abhängigkeiten und Berichte mit SHA-256-Prüfsummen in einem ZIP-Paket.

Die Browserprüfung `viewer_pruefen.cjs` benötigt Playwright und Chromium. Sie prüft alle vier Varianten, unterschiedliche Canvas-Bilder, die Instanzzahlen und eine mobile Ansicht. Screenshots V1–V4 sind enthalten.
