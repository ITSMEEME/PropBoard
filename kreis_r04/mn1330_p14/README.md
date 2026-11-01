# P14 – MN1330 mit freitragenden Flügeln

P14 setzt den gewünschten Leichtbau als neue Entwicklungsrevision um. P13 bleibt als Vergleich erhalten. Außenrahmen, Spitzenlager, äußere Streben und die Riemen-/Spindelaktoren entfallen. Die zwei Motoren sitzen weiterhin im Zentrum; die Flügel sind ausschließlich an ihren Wurzeln befestigt.

**Dieser Stand ist animierbar und parametrisch untersuchbar, aber noch nicht produktionsreif.** Die Gestänge besitzen ausgeführte Gelenkaugen, Lager, Gabeln, Bolzen und Sicherungen. Servo-OEM-Anschluss und Belastungs-/Ermüdungsnachweise bleiben offen. [Ergebnisse](ERGEBNIS.md), [Montagefolge und Prüfumfang](MONTAGE.md) und [Freigabestatus](FREIGABESTATUS.md) trennen geprüfte Eigenschaften von offenen Punkten.

![P14 CAD](Ansichten/P14_Gesamt.png)

## Öffnen

- [P14-Flugsimulator mit WASD, Gamepad und Touch](P14_Flugsimulator.html), [Bedienung und Modellgrenzen](FLUGSTEUERUNG.md)
- [Technischer CAD- und Leistungsprüfstand](P14_Entwicklungspruefstand.html)
- [Native FreeCAD-Baugruppe](Ausgabe/P14_MN1330_Leichtbau.FCStd)
- [Gesamt-STEP](Ausgabe/P14_MN1330_Leichtbau.step)
- [Einzelteile und Kaufteilreferenzen](Ausgabe/Teile.json), [Stückliste](Ausgabe/Stueckliste.csv)
- [Wurzelbefestigung](Ansichten/P14_Wurzel.png), [Servoeinheit](Ansichten/P14_Servo.png), [Gelenk-Explosionsansicht](Ansichten/P14_Gelenk_Explodiert.png)
- [Montagefolge](MONTAGE.md), [44 Gelenke mit RH-/LH-Varianten](Ausgabe/Gelenk_Register.csv)
- [Konstruktionsprinzip](KONSTRUKTION.md), [Servowahl mit Herstellerquellen](SERVO.md)
- [MN1330-Daten, Prüflinie und 180-s-Zeitbezug](MOTOR_DATEN.md)

Der HTML-Prüfstand lädt ausschließlich lokale Dateien und benötigt WebGL. Er kann direkt geöffnet werden. Falls ein Browser lokale Skripte sperrt, aus dem Repository-Stamm starten:

```bash
python3 -m http.server 8050 --bind 127.0.0.1
```

Dann `http://127.0.0.1:8050/kreis_r04/mn1330_p14/P14_Entwicklungspruefstand.html` öffnen. Ziehen dreht die Kamera, das Mausrad zoomt. „Zentrum / Servos“, „Blattwurzel“ und das Ausblenden von CFK/Unterrotor erleichtern die Prüfung. Die Rotorrotation wird für die Darstellung um Faktor 0,035 verlangsamt; die Flugrechnung verwendet die tatsächliche Modellzeit.

In FreeCAD die Baugruppe öffnen und [P14_Animation.FCMacro](P14_Animation.FCMacro) aus diesem Verzeichnis ausführen. Der Dialog bewegt Rotoren, Blattpitch, Taumelscheiben, Servohebel und Gestänge aus denselben geschlossenen Gelenkbedingungen wie der Browser. Beim Schließen wird die Neutralstellung wiederhergestellt. Das Makro ist ein separater Animator; der Generator liefert native `Part::Feature`-Ergebniskörper, keine vollständige PartDesign-Historie.

## Parametrisierung

Der Browser bietet **4, 6, 8, 10 oder 12 Blätter pro Rotor** und **1 bis 4 gegenläufige Rotorpaare**. Ein Rotorpaar besteht aus zwei MN1330, zwei Rotorebenen und sechs Servos. Blattzahl und Anzahl kompletter Hubrotoren sind getrennte Parameter.

Für jede Blattzahl wurden die CAD-Geometrie, Masse, Schwerpunktlage und Trägheit neu berechnet. Die größere Wurzelteilung bei 10/12 Blättern ist geometrisch berücksichtigt. Der Browser zeigt die entsprechenden CAD-Netze, keine durch Skalierung verzerrten Flügel. Mehrere Rotorpaare werden ohne Scheibenüberlappung angeordnet; **ihr Verbindungsrahmen fehlt**. Solche Fälle sind reine Anordnungs-/Flugrechenstudien mit ausdrücklich unvollständiger Strukturmasse und überschreiten teilweise das Fahrzeug-Zielmaß.

Nutzlast und deren Schwerpunkt sind veränderbar. Die voreingestellten 100 kg bei 0,90 m Höhe sind ein Punktmassenszenario für eine stehende Person, kein ausgelegtes Personendeck. Akku 12 kg und Elektronik 2 kg sind Annahmen. Eine Parameter-/Laständerung setzt den Flugzustand zurück.

Weitere Maße stehen in [parameter.json](parameter.json). Die konstruktive Untersuchungsdomäne ist: Radius 650–800 mm, Profiltiefe 115–145 mm, äußeres Dickenverhältnis 0,10–0,16 und Ebenenabstand 360–440 mm. Diese Bereiche bedeuten keine Festigkeitsfreigabe. Geänderte Abmessungen benötigen einen erneuten CAD-Aufbau und neue Massendaten; der Browser verwirft unpassende alte Massendaten.

```bash
# System-Python mit FreeCAD/Part/Import/MeshPart, hier /usr/bin/python3:
/usr/bin/python3 kreis_r04/mn1330_p14/erstellen.py
/usr/bin/python3 kreis_r04/mn1330_p14/massenvarianten.py
```

Eine im Browser gespeicherte Konfiguration lässt sich mit `--config /pfad/konfiguration.json` an beide Programme übergeben. Ohne `--output` wird `Ausgabe` neu erzeugt; eigene Varianten vorher in ein anderes Verzeichnis sichern. Für eine isolierte CAD-Variante unterstützt der Generator `--output /pfad/variante`. Die mitgelieferte HTML-Seite liest stets ihr benachbartes `Ausgabe`-Verzeichnis.

## Flugrechnung und bestehender Simulator

Die große Ausführung besitzt einen **interaktiven P14-Flugsimulator** mit WASD, QE zum Drehen, RF für die Höhe, Start/Landung/Pause und Positions-/Winkelmodus. Standard-Gamepad und Mehrfinger-Touch sind ebenfalls verfügbar. Der bisherige H01/P11-Simulator verlinkt P14 in seiner Modellauswahl. Der technische Entwicklungsprüfstand bleibt für direkte Pitch-/Leistungsstudien erhalten. Fertigungs- und Flugfreigaben fehlen weiterhin.

Für einen steuerbaren Flug ausdrücklich **„Trainingsflug · freie Motorleistung“** wählen:150Nm und40kW elektrisch je Motor sind dort freie Annahmen. „Start / T“ verwendet den aktuell gewählten Motorfall; mit den voreingestellten MN1330-Daten bleibt die Standardkonfiguration am Boden. Der neue Modellregler verändert ausschließlich Drehzahl- und Pitchbefehle; die bisherige Physik berechnet Auftrieb, Leistung und Bewegung. Die Kameranachführung zeigt die tatsächliche Flugposition. [Alle Tasten und Prüfbedingungen](FLUGSTEUERUNG.md).

Die Rechnung verbindet CAD-Masse/-Trägheit, Nutzlastschwerpunkt, unabhängigen Wellenhochlauf beider Motoren, statische BEMT mit oberem Nachlauf, linearisierte zyklische Momente und einen starren Körper mit Gegenmomenten/Kreiseleffekt. Ein idealisierter Bodenprüfstand hält das Modell bis zum Abheben aufrecht. Motor-Moment und elektrische Leistung begrenzen den Hochlauf; eine idealisierte Drehzahlregelung ist kein bestätigtes ESC-Modell.

Die bereitgestellten MN1330-Daten liefern 2,75 kg Motormasse, 24S und eine NS52×20-Prüflinie bei etwa 92 V. **3,4 kW gelten laut XLS für 180 s; die Prüftabelle bis 16,27 kW hat keine angegebene Haltedauer.** Das sind keine Dauerleistungsangaben. Der voreingestellte konservative 180-s-Rechenfall, ein Vergleich mit den Prüfmaxima und freie Annahmen sind im Prüfstand getrennt wählbar. Im zeitgebundenen Fall endet die Flugrechnung nach 180 s, ohne damit ein reales Abschaltkonzept vorzugeben. [Interpretation und Grenzen](MOTOR_DATEN.md).

„Drehmoment trimmen“ stellt das untere Kollektiv für den gewählten stationären Fall ein. „Schwebepunkt rechnen“ gibt den theoretischen Drehzahl-/Leistungsbedarf aus und vergleicht ihn mit den bereitgestellten Prüfdaten; es übernimmt ihn nicht als nachgewiesenen Motorbetriebspunkt. NS52×20-Schubwerte werden nicht auf die CFK-Flügel übertragen. Vorwärtsflug, elastische Flügel, Lager-/Gelenkspiel, Servokühlung/-bandbreite, Bodeneffekt, Motorthermik und ein ausgelegter Flugregler fehlen.

## Prüfungen reproduzieren

```bash
/usr/bin/python3 kreis_r04/mn1330_p14/pruefen_cad.py step
/usr/bin/python3 kreis_r04/mn1330_p14/pruefen_cad.py collision
/usr/bin/python3 kreis_r04/mn1330_p14/pruefen_mechanik.py --native
/usr/bin/python3 kreis_r04/mn1330_p14/montage_nachweis.py
/usr/bin/python3 kreis_r04/mn1330_p14/lastscreen.py
node kreis_r04/mn1330_p14/pruefen_simulation.js
node kreis_r04/mn1330_p14/pruefen_flugsteuerung.cjs
node kreis_r04/mn1330_p14/pruefen_flugsimulator.cjs
```

Alle Volumenüberschneidungen über 0,1 mm³ werden mitgezählt, ohne pauschale Kontakt-Ausnahmen. Der dynamische CAD-Test prüft ausgewählte kritische Paare in fünf Stellungen; er ist kein vollständiger Hüllvolumen-Nachweis. Der Montageprüfer kontrolliert kontinuierliche Bolzen-Auszugshüllen, benannte Lager-/Baugruppen-Einbauwege und 30-mm-Sechskantbits. Prüfumfang und Restpunkte stehen in [MONTAGE.md](MONTAGE.md). Der Lastscreen berechnet Beanspruchungen ohne erfundene zulässige CFK-/Alu-Dauerlasten.
