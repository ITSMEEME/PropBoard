# P08 – mechanische Verbindung SB-2270SG+ ↔ Taumelscheibe

P08 konstruiert die sechs Servoverbindungen als **detaillierte mechanische Anschlussentwürfe**. Der Antrieb ist der ausgewählte Kaufservo Savöx SB-2270SG+, kein Schrittmotor. Die bisherigen schwebenden Kugeln und einfachen Verbindungszylinder dieser sechs Kanäle werden ersetzt. **Der Stand ist weiterhin nicht fertigungsfreigegeben.**

## Durchgängiger Lastpfad

Servoabtrieb → geschlitzter Klemmhebel → M2-Kugelbolzen → unter Haltekappe eingeschlossener Kugelsitz → Rechts-/Linksgewindestange mit zwei Kontermuttern → zweiter Kugelsitz → M2-Kugelbolzen in radialem Aufnahmeboss des stationären Taumelrings.

Je Kanal sind 15 einzelne Bauteile modelliert: Hebel, zwei Kugelbolzen, zwei Pfannenkörper, zwei einschraubbare Haltekappen, Verstellstange, zwei Stangen-Kontermuttern, Mutter am Hebel-Kugelbolzen, M2×12-Klemmschraube, Klemmmutter und zwei Scheiben. Insgesamt 90 neue Bauteilobjekte. Zwei stationäre Taumelringe erhalten echte Bohrungen und Aufnahmebosse; zwei Motorplatten größere Gestängedurchlässe.

## Abtrieb und Hebel

Die vollständige Servo-STEP aus P07 ist weiterhin ungültig. Ihr **lokaler Abtriebsbereich** lässt sich jedoch gültig ausschneiden. Ein geschlossener Außenkonturschnitt mit 100 Kanten bei Quell-Y=14 mm liefert die tatsächlich vorhandene 25-zähnige Kontur. Diese wird für die neue Hebelbohrung radial um 1 % erweitert (bei Radius 3 mm: 0,03 mm). Das ist ein ausdrücklich vorgeschlagenes Prototyp-Passspiel, keine bestätigte Normpassung. Die komplette STEP wird dadurch nicht repariert.

Der Hebel hat 8 mm Kugellochradius, eine 4 mm breite Klemmnabe und eine modellierte M2×12-Klemmschraube mit Mutter/Scheiben. Zur Aufnahme des tatsächlichen Hubvolumens werden die Servo-Körper tangential um −5,5 mm verschoben. Die Abtriebsachsen und Kugelmitten behalten ihre radialen/höhenbezogenen Kinematikbezüge; die späteren Servohalter müssen zu dieser neuen tangentialen Lage passen. Ein abschließender Kollisionsnachweis gegen das ungültige Servo-Gesamtmodell ist damit nicht erbracht.

## Montierbares Gelenk und einstellbare Stange

Die Kugel Ø4,8 wird durch die Gewindeöffnung in den Pfannenkörper eingeführt; erst danach wird die Haltekappe M6×0,5 eingeschraubt. Es wird keine unmögliche Montage einer geschlossenen Kugel durch eine kleinere fertige Öffnung vorausgesetzt. Der Kugelsitz R2,43 hat nominal 0,03 mm Radialspiel. Die Halsöffnung ist konisch freigestellt.

Die Stange hat unten M2-Rechtsgewinde, oben M2-Linksgewinde und einen mittleren Schlüsselansatz SW3. Beide Enden lassen sich gemeinsam verstellen; Kontermuttern sichern die eingestellte Länge. Neutraler Gewindeeingriff 3 mm, vorgeschlagene Verstellung ±0,3 mm je Ende (±0,6 mm Kugelmittenlänge), 0,5 mm nominelle Bodenreserve. Der neutrale Kugelmittenabstand bleibt 22,57143 mm oben und 22,27435 mm unten. Aus den vorhandenen Kinematikdaten werden die individuellen Längen übernommen.

Die Taumelringarme besitzen je drei Ø6-Aufnahmebosse mit radialen M2-Gewindeangaben. Die Plattendurchlässe sind Ø14 statt Ø10. **Restquerschnitte, Schraubenkräfte und Werkstoff-/Verfahrenswechsel müssen noch nachgewiesen werden.**

## Dateien

- `Ausgabe/P08_Baugruppe_Servoverbindung_ENTWURF.FCStd`: kompletter statischer Integrationsstand.
- `Ausgabe/P08_Isolierte_Anschlussbewegung.FCStd`: sechs Verbindungen, stationäre Taumelringe und Servo-Körper als isolierte Bewegungsbaugruppe.
- `P08_Bewegung_oeffnen.FCMacro`: isolierte Baugruppe öffnen, sechs Servowinkel einstellen oder Demo starten. Rotorblätter und die übrige Rotorbaugruppe werden in diesem separaten Modell nicht mitbewegt. Die einstellbaren ±15° sind ein isolierter Gestänge-Prüfbereich, kein nachgewiesener Gesamtrotor-Stellbereich; einzelne Kombinationen können die Blattkinematik überschreiten.
- `Ausgabe/P08_Anschluss_Einzelteile_ENTWURF.FCStd` und einzelne STEP: getrennte Körper für die konstruierten Teile, mit Gewinde-/Anschlussangaben.
- `Anschlussdaten.json`: Maße und ausdrücklich noch nicht freigegebene Werkstoff-/Prozessvorschläge.
- `Ausgabe/Aufbaupruefung_P08.json`, `Bewegungspruefung_P08.json`, `Abtriebsprofil.json`: tatsächliche Erzeugungs-, Bewegungs- und lokale Profilprüfungen.

## Grenzen

Die neuen Teile besitzen reale Sitz-, Freistellungs-, Schrauben- und Montagegeometrien. Gewindeflanken sind normgerecht nominal dargestellt; die schriftlichen M2×0,4-RH/LH- und M6×0,5-RH-Angaben gelten, nicht eine glatte Bohrung als Ersatz für ein Gewinde. Fertigungszeichnungen mit endgültigen Bezügen/Toleranzen, Passlehren, Werkstoffen/Oberflächen, Anzugsmomenten und Belastungs-/Verschleißnachweisen fehlen noch. Neue Reibwerte werden nicht aus dem CAD erfunden. Die bisherige Flugphysik wird durch diese Geometrieänderung nicht automatisch neu validiert.

Die vollständigen Servo-Montagehalter und frühere P06-Probleme an anderen Rotorbauteilen bleiben offen. P08 ist konkrete Anschlusskonstruktion, **kein Nachweis, dass die Gesamtmaschine bereits fertigungsbereit ist**.

## Reproduzieren

Vollständiger Checkout einschließlich P07/P06 und FreeCAD 1.0.2:

```sh
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p08/profil_erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p08/erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p08/pruefen.py
```

Die Bewegungsfunktion und nativen Dateien wurden ohne GUI geprüft. Der zusätzliche GUI-Lauf konnte hier wegen fehlendem gültigem OpenGL-Kontext im Offscreen-Betrieb nicht abgeschlossen werden; die Dialogbedienung ist deshalb nicht als getestet ausgewiesen.
