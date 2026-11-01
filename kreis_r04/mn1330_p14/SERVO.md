# Servowahl: PH54-200-S500-R

Ausgewählt ist **ROBOTIS DYNAMIXEL PH54-200-S500-R**, dreimal pro Rotor, sechsmal pro Rotorpaar. Der Nutzer hat die Auswahl eines passenden neuen Servotyps ausdrücklich erlaubt. Die vorhandenen Savöx werden nicht als ungeprüfter Ersatz übernommen.

| Herstellerangabe | Wert |
|---|---:|
| Nennversorgung | 24 V |
| Masse | 855 g |
| Abmessungen W × H × D | 54 × 126 × 54 mm |
| Continuous Torque | 44,7 Nm |
| Continuous Speed | 29/min = 174°/s |
| Continuous Current | 9,3 A |
| Leerlaufdrehzahl | 33,1/min |
| Radiallast, 10 mm vom Horn | 370 N |
| Axiallast | 130 N |
| Spiel | < 0,1° |
| Kommunikation | RS485, DYNAMIXEL Protocol 2.0 |

Das OEM-Datenblatt weist ausdrücklich darauf hin: **„These specifications are calculated based on the specifications of the core motor. Please consult ROBOTIS for the long term use or special use“**. Die 44,7 Nm sind somit eine veröffentlichte Berechnungsangabe, keine zugesicherte Dauertragfähigkeit in unserem Gehäuse, bei unserer Kühlung und bei zyklischer Belastung. Die Anwendung muss mit ROBOTIS und am Prüfstand abgesichert werden. Der Simulator bildet keine bestätigte Servo-Thermik oder Belastungsbandbreite ab.

Der zunächst untersuchte XH540-W150-R wurde verworfen: Seine 7,1 Nm waren ein **Stillstandsmoment**, kein Dauermoment. Der Lastscreen überschreitet diesen Wert bei hoher Drehzahl. Er bleibt nur als verworfene Quellenreferenz im Quellenverzeichnis.

Die neue Wahl liefert deutlich mehr Moment ohne ein zusätzliches Untersetzungsgetriebe. Die 15-mm-Umlenkwelle mit 28-mm-Hebel und Alu-Passfeder ist extern gelagert. Der aktuelle Lastscreen unter `Ausgabe/Lastscreen.json` berechnet den Momentbedarf erneut mit der geänderten Hebelübersetzung und CAD-Masse. Darin stecken ein angenommener aerodynamischer Momentenbeiwert und vereinfachte Lastverteilung; Reibung, Spiel, Stoß, elastische Lastspitzen und Wärme sind nicht nachgewiesen.

Die stationären Servos müssen eine fest eingestellte zyklische Neigung nicht einmal pro Rotorumlauf durchfahren. Die umlaufenden Pitchglieder führen diese Bewegung aus. Deren dynamische Kräfte wirken trotzdem auf Taumelscheibe und Servoanlenkung. Ein dynamischer Belastungs- und Steifigkeitsnachweis bleibt erforderlich.

Sechs Servos können bei der genannten Stromangabe zusammen etwa 55,8 A aus dem 24-V-Zweig aufnehmen. Ein geeigneter Wandler, Leitungen, Steckverbinder, Absicherung und Kühlkonzept sind nicht in der bisherigen 2-kg-Elektronikannahme nachgewiesen. Die angezeigte elektrische Motorleistung `Wellenleistung / angenommener Motorwirkungsgrad` enthält diese Servolasten nicht.

## Quellen und CAD-Grenze

- [OEM eManual](https://emanual.robotis.com/docs/en/dxl/p/ph54-200-s500-r/), lokal: [ph54-200-s500-r.md](Quellen/ph54-200-s500-r.md)
- [OEM Datentabelle](https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/_data/dxl_p_info.yml), lokal: [dxl_p_info.yml](Quellen/dxl_p_info.yml)
- [Tabellenbedeutung und Fußnote](Quellen/specifications_p.md)
- [OEM Leistungsdiagramm](Quellen/ph54_performance.jpg)
- [Allgemeine PH54-Flanschreferenz](Quellen/h54p_drawing.png)
- [Original-STEP-Download](https://www.robotis.com/service/download.php?no=1258)

Die Original-STEP-Anfrage wurde mit HTTP 403 durch die Netzwerkumgebung gesperrt. Das eingebaute Gehäuse verwendet Hersteller-Nennmaße und einen nominalen vorderen Flansch. Es ist **kein behauptetes Original-STEP**. Befestigungsbohrungen, tatsächliches Horn, Flanschabstände, Kabel-/Steckerraum und Wärmeübergang sind deshalb noch offen. Die Kupplung ist auf der eigenen Wellenseite formschlüssig modelliert, auf der OEM-Seite eine Anschlussreserve. Für die Beschaffung ist vor Fertigung die gültige Maßzeichnung der konkreten Lieferausführung erforderlich.
