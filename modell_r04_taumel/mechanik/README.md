# Mechanikprüfung Koaxialrotor / zwei Taumelscheiben

Stand 30.10.2026. Bezug: F01-Rotor, neue FC/ESC-/Akkuhalter H01. **Rechnerische Prüfung mit ausdrücklich bedingten Lastannahmen; keine mechanische oder betriebliche Freigabe.**

## Ergebnis

**Das Taumelscheibenprinzip ist kinematisch plausibel; der aktuelle Aufbau ist mechanisch unvollständig. Ein 9-g-Mikroservo ist nicht pauschal ausreichend.** Fehlende echte Servoarme, Kugelanschlüsse, axiale Sicherungen und die reibende Fliehkraftabstützung verhindern eine belastbare Hardwarefreigabe. Die frühere Aussage „Standard-Mikroservos reichen“ wird durch diese Prüfung nicht bestätigt.

## Nachweise und Prüfumfang

- Unabhängige Vorwärts-/Rückwärtskinematik: 6552 Zustände, 52416 Blatt-Gestängeschlüsse, beide Drehrichtungen, Kollektiv −2…21°, Zyklik bis 4°, Zyklikrichtung in 30°-Schritten, Rotorwinkel in 10°-Schritten.
- Größter numerischer Restfehler im mathematisch geschlossenen 15-mm-Gestänge: 3.55e-15 mm. Dies ist keine Aussage über reales Gelenkspiel.
- Größte Abweichung vom vorgegebenen Sinus: 0.268°. Acht feste Stangen lassen bei endlichen Winkeln keinen beliebigen idealen Sinus mit nur drei Taumelscheiben-Freiheitsgraden zu.
- Zwölf Vergleichsfälle mit dem bestehenden FreeCAD-Posesolver stimmen bis etwa 10⁻¹² in den Posekomponenten überein. Das prüft die Rechengeometrie; es validiert keine Material- oder Reibannahmen. Die F01-Kollisionsgeometrie verwendet den vorgegebenen Pitch. Für eine mechanische Freigabe muss sie mit den tatsächlich geschlossenen Vorwärtswinkeln und realen Gelenken erneut untersucht werden.
- Die virtuelle Arbeit nutzt die vollständige 8-Blatt-/3-Servo-Jacobimatrix. Nicht einfach die Kraft eines Blattes durch drei teilen.
- Lastauswertung an 7 Kollektivwerten, 12 Zyklikrichtungen plus Nullzyklik, beiden Rotorseiten und vier Rotorazimuten je 45°-Periode. Kein kontinuierlicher Extremwert- oder Resonanznachweis.

## Funktionsprüfung und tatsächlich offene Mechanik

1. **Koaxiale Drehrichtung:** Die untere lokale Rotorachse wird im CAD nach −z gespiegelt; gleiche lokale Drehung ergibt entgegengesetzte Weltdrehung. Bei der Zyklik sind die stationären Servoazimute oben 60/180/300°, unten im Fahrzeug 120/0/240°. Den Mischer nicht unverändert kopieren; Vorzeichen und dynamische Phasenlage am Prüfstand identifizieren.
2. **Servoanlenkung:** F01 zeichnet veränderlich lange Stangen zu festen Punkten bei z60. Ein realer Servoarm und ein festes Servogestänge fehlen. Die neue Rechnung schlägt 8-mm-Horn, tangentiale Abtriebsachse, radial-vertikale Hornebene und r58,3/z60 als Geometrie vor. Das ist ein berechneter Vorschlag, kein verifiziertes Produktlochbild.
3. **Stellweg:** Etwa -26.0…+8.6° relativ zum Schwebezustand, also rund 35°. Ein typischer ±60°-Servo wäre vom Weg her ausreichend; tatsächliche elektronische Endpunkte und Kollisionsräume müssen mit dem gewählten Produkt geprüft werden.
4. **Drehzahl und Bandbreite:** Für gleichbleibende Zyklik bleibt die stationäre Taumelscheibe geneigt. Die Servos müssen nicht pro Rotorumdrehung hin und her laufen. Rotierende Pitchglieder tun dies; deren Beschleunigung, Reibung, Spiel und Ermüdung bleiben relevant. 0,12 s/60° ist ein Entwurfsziel für den Servo, kein gemessener Regelbandbreitennachweis.
5. **Pitchwurzel:** Die gedruckte Nut und zwei D2-Stifte nehmen die Fliehkraft gleitend auf. Deren Reibmoment μ·Fz·4,8 mm kann die Servoauslegung dominieren. Eine definierte Radiallagerung und eine separate, gering reibende axiale Fliehkraftabstützung sind die bevorzugte nächste Revision. Ein nominell stärkerer Servo ersetzt diesen Nachweis nicht.
6. **Sicherungen/Lastpfade:** Die F01-Pitchhebel besitzen keinen fertigen Kugelbolzenanschluss und keine ausgearbeitete axiale Sicherung. Stationäre Taumelarme besitzen keine ausdefinierten Bolzensitze. Der geschlitzte Motor-/Servoträger hat noch keine Klemmschraube und die Lagerringe keine nachgewiesene axiale Sicherung. Die geschlossene Kugelpaarung benötigt eine plausible Montagefolge oder konstruktive Teilung. Die neuen Endadapter sichern die Halter, schließen diese offenen Rotoranschlüsse aber nicht.
7. **Spiel:** Der effektive vertikale Pitchhebel ist 9·cos(θ) − 5,5·sin(θ), bei 25° nur etwa 5,83 mm. 0,1 mm wirksames Spiel kann dort rund 0,98° Pitchfehler bedeuten. Die alte konstante 9-/12-mm-Hebelabschätzung genügt nicht. Reale Kugelgelenke, Wurzel und Servogetriebe auf Gesamtspiel prüfen.

## Bedingte Servolast mit neuer Haltermasse

CAD-Trägheit statt pauschalem Rechteck: Blattmasse 8,920 g bei angenommener homogener effektiver Dichte, Schwerpunkt r109,464 mm. Tatsächliche Druckinfill-Verteilung muss gewogen/gemessen werden. Verwendet werden Fliehkraft-Twistmoment, Pitch-Beschleunigung aus geschlossener Kinematik, BEMT-Mittelschub mit 25-%-Sehnenhebel und Gleitreibung. Beträge werden ohne hilfreiche Vorzeichenkompensation addiert. Der Luftkraftansatz ist kein validierter Worst-Case-Grenzwert; insbesondere zyklische Luftlasten und echte Profilmomentenkennfelder fehlen.

| Servomasse je Stück | Gesamtmasse H01 | Schweben, Modell | Schub/Gewicht 2, Modell |
|---|---:|---:|---:|
| 9 g | 1.218 kg | 2325 U/min | 3286 U/min |
| 20 g | 1.284 kg | 2387 U/min | 3374 U/min |
| 60 g | 1.524 kg | 2600 U/min | 3675 U/min |

**Erforderliches Moment je Servo bei Modell-Schub/Gewicht 2, bereits mit Faktor 2:**

| effektiver Reibwert μ | 9-g-Servos | 20-g-Servos | 60-g-Servos |
|---|---:|---:|---:|
| 0.00 | 3.90 kg·cm | 4.11 kg·cm | 4.88 kg·cm |
| 0.03 | 5.74 kg·cm | 6.05 kg·cm | 7.18 kg·cm |
| 0.10 | 10.02 kg·cm | 10.56 kg·cm | 12.53 kg·cm |
| 0.20 | 16.13 kg·cm | 17.01 kg·cm | 20.18 kg·cm |

μ ist hier eine Sensitivitätsannahme, kein gemessener Werkstoffwert. Ein äquivalenter kleiner Wert für eine überarbeitete Wälzlagerung ist erst durch Messung zu bestätigen. Hersteller-Stallmoment ist kein Dauerbetriebsmoment. Faktor 2 und Stallreserve ersetzen keine Strom-/Temperaturmessung.

Reale Servo-Befestigungen, BEC und Schutzteile sind noch nicht vollständig im genannten Massenbudget enthalten. Die Rechnung ist daher eine bedingte Vorauslegung. Mit großen Servos steigt die Masse erheblich. Die 60-g-Variante erreicht rechnerisch etwa 3675 U/min für Schub/Gewicht 2; der 120-%-Screeningfall läge bei etwa 4410 U/min. Das überschreitet den früheren Rechen-/Prüfbereich. Diese Zahl ist **kein Auftrag für einen Schleuderversuch** und keine Drehzahlfreigabe.

## Servosuche – konkrete Kandidaten, Datenblattprüfung offen

- **KST X15-755X:** Kandidat für eine leichte Revision mit gering reibender Pitchlagerung. Zielklasse mindestens etwa 7 kg·cm bei tatsächlich gewählter Versorgung. Drehmoment, Masse, Geschwindigkeit, Lochbild, Horn, Signalformat und Strom dieses Produkts sind hier noch nicht aus dem Herstellerdatenblatt verifiziert.
- **Savöx SB-2270SG:** Kandidat für eine stärkere konventionelle Servo-/Halterrevision. Für den angenommenen Reibwert 0,1 bei schweren Servos wäre mindestens die 15-kg·cm-Klasse anzustreben; bei 0,2 eher 25 kg·cm. Auch dieser Kandidat ist ausdrücklich noch nicht mit aktuellen Herstellerdaten oder dem Bauraum abgeglichen. **Keiner ist als Drop-in-Ersatz oder zum Kauf freigegeben.**
- Beide Anbieterzugriffe wurden versucht und vom Umgebungsproxy mit HTTP 403 abgewiesen. Die nötigen Domainergänzungen wurden im Konfigurationsentwurf gespeichert, sind im laufenden Netz noch nicht aktiv. Für eine belastbare Produktauswahl Herstellerzugriff ermöglichen oder Datenblätter bereitstellen. Keine Spezifikationen oder Preise wurden als recherchiert ausgegeben.
- Kandidatenlinks: [KST-Suche](https://kstservos.com/search?q=X15-755X), [Savöx-Suche](https://www.savoxusa.com/search?q=SB-2270SG). Das sind Rechercheziele, keine hier eingesehenen Datenquellen.

## Elektrik und nächste messbare Schritte

Sechs Servos brauchen eine eigene geregelte Versorgung passend zum gewählten Servo. Einen üblichen 6-/7,4-/8,4-V-Servo niemals direkt an den 6S-Akku (bis 25,2 V) anschließen. BEC-Spitzenstrom aus sechs tatsächlichen Servo-Stallströmen und Lastmessungen dimensionieren; Dauerstrom/Temperatur nachweisen. FC-Signalpegel, Neutralpuls und zugelassene Rahmenfrequenz im Datenblatt prüfen; einen 760-µs-Heckservo nicht ungeprüft als Taumelscheibenservo verwenden.
Vor verbindlicher Auswahl: axiale Pitchlagerung schließen, Reibmoment unter radialer Ersatzlast messen, Gesamtspiel messen, echten Servoarm/Servoanschluss einzeichnen. Danach Herstellerdaten gegen Moment, Stellweg, Spannung, Strom und Gehäuse einschließlich Befestigungsflanschen prüfen. Abschließend statische Belastung und niedrige Stellgeschwindigkeiten mit vollständiger Lager-/Schraubensicherung prüfen. Geometrie-, Material-, Temperatur- und Regelungsfreigaben bleiben getrennte Nachweise.

## Dateien und Reproduktion

- `Mechanikpruefung.json`, `Kinematik_Sweep.csv`, `CAD_Abgleich.json`: numerische Ergebnisse und Vergleich.
- `Fluegel_Traegheit.json`: aus dem vorhandenen FreeCAD-Blattkörper extrahiert; Füllannahme enthalten.
- `Betriebspunkte_H01.json`: BEMT-/Antriebsmodell mit H01-Masse und Servo-Massensensitivität.
- `Servoauswahl_OFFEN.json`: Anforderungen, unbestätigte Kandidaten und konkret blockierter Datenzugriff.
- `Servomoment_Reibung.png`, `Pitchvergleich.png`, `Mechanikbericht.pdf`: lesbare Darstellung.
```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/mechanik/traegheit_erstellen.py
node modell_r04_taumel/mechanik/betriebspunkte.js
OPENBLAS_NUM_THREADS=2 .cfd-tools/venv/bin/python modell_r04_taumel/mechanik/pruefen.py
MPLCONFIGDIR=/workspace/.propboard/cache/matplotlib .cfd-tools/venv/bin/python modell_r04_taumel/mechanik/bericht_erstellen.py
```
