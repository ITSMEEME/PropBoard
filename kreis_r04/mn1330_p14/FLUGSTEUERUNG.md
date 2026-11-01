# P14-Flugsimulator bedienen

[P14-Flugsimulator öffnen](P14_Flugsimulator.html). Im bisherigen [H01/P11-Simulator](../../modell_r04_taumel/simulation/H01_Flugsimulator.html) führt die Modellauswahl oben ebenfalls zu P14. P14 besitzt seine eigene Flugphysik mit den tatsächlichen CAD-Massenvarianten; die P11-Physik wird nicht für das Großmodell skaliert.

## Starten

Im vollständigen Repository oder entpackten P14-Paket `P14_Flugsimulator.html` öffnen. Falls der Browser lokale Skripte sperrt, aus dem Repository- bzw. Paketstamm starten:

```bash
python3 -m http.server 8050 --bind 127.0.0.1
```

Dann `http://127.0.0.1:8050/kreis_r04/mn1330_p14/P14_Flugsimulator.html` aufrufen. Das portable Paket enthält P14; die Navigation zum kleinen P11-Modell benötigt das vollständige Repository.

**Für einen steuerbaren Flug „Trainingsflug · freie Motorleistung“ wählen.** Diese Aktion wählt sichtbar150Nm und40kW elektrische Leistung je Motor als freie Annahmen, mit einem Modellbereich bis2.800/min. Sie sind keine bestätigten MN1330-Leistungswerte. Das Modell läuft vom Boden hoch und steigt auf etwa1,2m. Anschließend kann es mit Tastatur, Standard-Gamepad oder Bildschirmtasten gesteuert werden.

**„Start / T“ verwendet immer den aktuell ausgewählten Motorfall.** Voreingestellt sind die MN1330-Daten mit3,4kW/180s und46,25Nm. In der Standardkonfiguration mit100kg Nutzlast reicht der modellierte Schub damit nicht zum Abheben. Die Software erhöht diese Grenzen nicht automatisch. Der Fall „Prüfmaxima“ verwendet16,27kW und46,25Nm ohne erfundene Haltedauer. Beide Datenfälle behalten den bisherigen Simulationsbereich bis2.400/min; das ist keine Hersteller-Drehzahlfreigabe.

## Tasten und Eingabegeräte

| Eingabe | Wirkung |
|---|---|
| W / S oder Pfeil hoch / runter | vorwärts / rückwärts relativ zur aktuellen Ausrichtung |
| A / D oder Pfeil links / rechts | links / rechts relativ zur aktuellen Ausrichtung |
| Q / E | links / rechts drehen, Soll-Gierrate bis40°/s |
| R / F | steigen / sinken, Sollhöhe mit bis0,8m/s verändern |
| T | Hochlauf und Start; pausierten Start/Flug fortsetzen |
| L | automatische Landung; einen Start am Boden abbrechen |
| X | Motorantrieb aus, physikalischer Rotorauslauf; kein sofortiger Stillstand |
| Leertaste | Pause / Fortsetzen; startet keine kalten Motoren |
| Rücktaste / Backspace | Flugzustand zurücksetzen |
| M | Positions- / Winkelmodus wechseln |
| C | Verfolger / Orbit / Übersicht wechseln |
| Maus ziehen / Mausrad | Kamera drehen / zoomen; Ziehen wechselt vom Verfolger zum Orbit |

Im **Positionsmodus** gibt WASD eine horizontale Geschwindigkeit bis2m/s vor. Nach dem Loslassen bremst der Modellregler und kehrt zur zuletzt gehaltenen Position zurück; das geschieht mit dem tatsächlich berechneten Schub und benötigt Weg und Zeit. Im **Winkelmodus** gibt WASD bis10° Roll/Nick vor. Nach dem Loslassen richtet sich das Modell auf, hält aber keine horizontale Position. In beiden Modi hält der Höhenregler die eingestellte Höhe. L übernimmt die Landung und den anschließenden Motor-Auslauf.

Standard-Gamepad, Mode2: linker Stick Höhe/Gier, rechter Stick Bewegung; A Start, B Landung, Y Modus, Start-Taste Pause. Es wird die Standardbelegung der Browser-Gamepad-API mit12% Totzone verwendet. Geräte ohne Standard-Mapping sowie nicht selbstzentrierende Gasachsen benötigen eine eigene Anpassung; eine Kalibrierung ist hier nicht enthalten. Bei Verbindungsverlust werden die Analogkanäle neutral. Sperrt der Browser die Gamepad-API, funktionieren Tastatur und Touch weiterhin.

Die Bildschirmtasten unterstützen gleichzeitige Finger und Pointer Capture. Loslassen, Pointer-Abbruch und verlorene Pointer-Capture geben die Steuerung frei. Im mobilen Layout bleibt die Flugansicht beim Scrollen sichtbar. Fokusverlust oder ein ausgeblendeter Browser-Tab pausiert die Rechnung und löscht gehaltene Tasten. Anschließend ausdrücklich fortsetzen. Eingabefelder und Auswahlfelder behalten ihre normale Tastaturbedienung; dort lösen WASD, T usw. keine Flugbefehle aus.

## Parametrisierung und Anzeige

Blattzahl4/6/8/10/12, Rotorpaare1–4, Nutzlast0–150kg und Nutzlast-Schwerpunkt0–1,3m sind veränderbar. Jede Änderung setzt den Flugzustand zurück. CAD-Geometrie, Masse, Schwerpunkt und Trägheit werden aus den vorhandenen Varianten übernommen; Schwebedrehzahl, Drehmomenttrimm und Steuerwirkung werden für den neuen Fall berechnet. Außerhalb der verfügbaren Modell-/Leistungsgrenzen wird kein erfolgreicher Start vorgegeben.

Bei mehreren Paaren fehlt der Verbindungsrahmen einschließlich Masse und Steifigkeit. Das wird angezeigt. Die Konfiguration lässt sich inklusive Motorannahmen, Steuerungsmodus und CAD-Quellhash als JSON speichern. `production_ready` bleibt falsch.

Die Fluganzeige zeigt Höhe, Geschwindigkeit, Kurswinkel, Modellzeit, Roll/Nick, Rotor-Drehzahlen, Leistung und Gesamtmasse. Kurs0° zeigt entlang der Modell-X-Achse,90° entlang+Y. Bodenraster1m, Startkreis und Karten-Flugspur dienen der Orientierung; Markierungen haben kein Kollisionsmodell. Die Verfolgerkamera folgt Position und Ausrichtung. Die Rotoranzeige läuft um Faktor0,035 langsamer, während der Flugzustand mit der tatsächlichen Modellzeit integriert wird.

## Modell und Nachweise

Der Pilot ist ein idealisierter Positions-/Winkelregler. Er verändert ausschließlich Drehzahlziel, Kollektiv und zyklischen Pitch. Schub, Motormoment, Leistung, Schwerkraft, CAD-Trägheit, Wellendrehimpuls und Gegenmomente kommen weiterhin aus `P14Physics.Flight`; es gibt keine zusätzliche Auftriebskraft, keinen Positionssprung und kein sofortiges Abheben. Die zyklische Taumelneigung bleibt auf0,5° begrenzt, Kollektiv auf±3,5mm. Die aus dem Modell bestimmte Steuerwirkung berücksichtigt die konfigurierte Blattzahl und Anzahl Rotorpaare.

Die Integration verwendet höchstens1/120s pro Teilschritt. Die konservative180-s-Grenze bleibt aktiv und kann durch Pause/Fortsetzen nicht umgangen werden. Die Höhengrenze des Trainingsreglers beträgt80m. Über65° Neigung oder bei hartem Bodenkontakt wird der Versuch beendet. Der Bodenkontakt ist weiterhin eine idealisierte Höhenbegrenzung, kein ausgelegtes Fahrwerks-/Blattkontaktmodell. Ein beendeter Versuch benötigt Zurücksetzen.

Es ist keine echte Firmware oder Betaflight-SITL. Reale Servo-Stellzeiten, geschlossener ESC-Regelkreis, Vorwärtsflug, Strömungsabriss außerhalb der vereinfachten Polare, Motorthermik, elastische Flügel und Hinderniskollisionen sind nicht validiert. Trainingsleistung ist keine Hardwarefreigabe. Die [mechanischen Freigabepunkte](FREIGABESTATUS.md) bleiben offen.

Reproduzieren:

```bash
node kreis_r04/mn1330_p14/pruefen_flugsteuerung.cjs
node kreis_r04/mn1330_p14/pruefen_flugsimulator.cjs
node kreis_r04/mn1330_p14/pruefen_simulation.js
node kreis_r04/mn1330_p14/pruefen_browser.cjs
```

Die Browserprüfungen benötigen einen lokalen HTTP-Server und Playwright/Chromium. [Regler-Prüfbericht](Ausgabe/Flugsteuerung_Pruefung.json) und [Flugsimulator-Browserprüfung](Ausgabe/Flugsimulator_Browser_Pruefung.json) enthalten Prüfumfang, CAD-Quellhash und die jeweiligen Software-Quellhashes. Die gemeinsame App-Funktion `P14_SIM.advance(dt)` ermöglicht deterministische Wiederholungen mit denselben Eingaben und demselben120-Hz-Integrationspfad wie die laufende Anzeige.
