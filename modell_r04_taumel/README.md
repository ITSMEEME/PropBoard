# R04-Taumelmodell 1:4

Eigenständige Variante des R04-Testmodells: Der Pitch wird **je Rotor über eine Taumelscheibe** gestellt (kollektiv + zyklisch), nicht über einen Servo je Flügel. Das Servo-je-Flügel-Modell bleibt unverändert in [`modell_r04/`](../modell_r04/Implementationsplan.md). Die Begründung steht in [`modell_r04/Bewertung_Taumelscheibe.md`](../modell_r04/Bewertung_Taumelscheibe.md).

**Entwurf, keine Freigabe.** Alle Zahlen sind Modellwerte (BEMT mit vereinfachter Polare, Gleichstrom-Motormodell) und müssen am Prüfstand bestätigt werden.

## Gemeinsam mit dem Servo-Modell

Maßstab 1:4 (Flügelkreis Ø 375 mm, 8 Flügel je Ebene, Sehne 30 mm, NACA 0012, Ebenenabstand 60 mm), EMAX ECO II 2306 KV1900, SpeedyBee F405 V4 + BLS 55A (Bluejay), ELRS, Tattu 1550 mAh 6S, Druck auf 200 × 148 × 150 mm, PA-CF/PETG-CF für drehende Teile, Prüfstand draußen mit Schub- und Summenmoment-Wägezelle. Simulator und Antriebsmodell werden gemeinsam genutzt (`kreis_r04/simulation`, `modell_r04/auslegung/antrieb.js`).

## Unterschiede

| | Servo-Modell (`modell_r04`) | Taumelmodell (dieses Verzeichnis) |
|---|---|---|
| Pitchsteuerung | 16 drehende Servos, nur langsam | 2 Taumelscheiben, 6 feststehende Servos; kollektiv + **zyklisch** |
| Rotorelektronik | ESP32, Akkus, Funk je Rotor | keine |
| Flügelprofil ab | r = 62 mm | **r = 48 mm** (näher an R04: 37,5 mm) |
| Nabe | Trommel mit Servotaschen | **Topf** (Innenring, Boden, Außenwand), Pitchhebel innen |
| Zahnkranz / Ritzel | 91 Z / 14 Z, Motor bei r = 52,6 mm | **130 Z / 20 Z**, Motor bei r = 75,1 mm, gleiche Übersetzung 6,5:1 |
| Flugsteuerung | offen | Roll/Nick zyklisch, Gieren über Differenz von Kollektiv bzw. Drehzahl |

## Elektronik und Firmware

- **Ausgänge:** Laut ArduPilot-Dokumentation hat der SpeedyBee F405 V4 bis zu 9 PWM-Ausgänge: M1–M4 am ESC-Stecker, M5–M8 auf Pads, PWM 9 am LED-Pad. Sie sind gruppiert (1-2, 3-4, 5-6, 7-8, 9), und innerhalb einer Gruppe muss das Protokoll gleich sein.
  - Vorschlag: M1/M2 DShot für die Motoren, M5–M8 und PWM 9 für fünf Servos (PWM).
  - Der sechste Servo braucht einen weiteren Ausgang, z. B. M3 oder M4 (Gruppe 3-4 auf PWM umstellen, ESC-Kanäle 3/4 dann unbenutzt). **Am Board prüfen.**
- **Prüfstand:** Für die ersten Messungen genügt die direkte Kanalzuordnung (Kollektiv oben/unten, Zyklik) über Sender bzw. Mischer.
- **Flug:** ArduPilot TradHeli mit `FRAME_CLASS 11` (Heli Dual).
  - Die offizielle Doku nennt die Modi Tandem, quer und ineinandergreifend.
  - Für Koaxialaufbauten wird `H_YAW_SCALER = 0` genannt. Ein eigener Koaxialmodus ist nur aus einem Forumsbeitrag mit angepasstem Code bekannt.
  - **Ob und wie der koaxiale Doppeltaumelscheiben-Aufbau damit läuft, ist am Prüfstand zu verifizieren**; sonst wird ein eigener Mischer nötig.

Quellen: [ArduPilot Dual Helicopter](https://ardupilot.org/copter/docs/dual-helicopter.html), [ArduPilot SpeedyBee F4 V3/V4](https://ardupilot.org/plane/docs/common-speedybeef4-v3.html), [Forum: Co-axial heli](https://discuss.ardupilot.org/t/new-co-axial-heli/60067).

## Inhalt

Die **Cohexial Study, Fertigungsentwurf F01**, liegt unter [`cad/`](cad/README.md): native Baugruppe, skriptparametrische Einzelteile mit TechDraw-Seiten, STEP/STL, Zeichnungssatz und Stücklisten. Führungsnut, Mitnehmerstift und Kappenanordnung wurden gegenüber V1 korrigiert. Fehlende Kaufteilanschlüsse, Passungen und Festigkeitsnachweise sind in den [Fertigungshinweisen](cad/Fertigung/Fertigungshinweise.md) aufgeführt; es liegt keine Fertigungsfreigabe vor.

- [`cad/`](cad/README.md): parametrisches FreeCAD-Modell, STL-Dateien, Prüfbericht
- [`auslegung/`](auslegung/): Nachrechnung der Betriebspunkte und der Steuerwirkung mit CAD-Masse
