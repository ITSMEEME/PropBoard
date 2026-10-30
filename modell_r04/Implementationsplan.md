# R04-Testmodell – Implementationsplan

Stand 30.10.2026, abgestimmt in zwei Fragerunden. Grundlage: Simulator `kreis_r04/simulation` (BEMT, vereinfacht) und Herstellerdaten EMAX ECO II 2306. Alle Zahlen sind Vorauslegung und müssen durch Messung bestätigt werden.

## Getroffene Entscheidungen

| Thema | Entscheidung |
|---|---|
| Ziel | **erst Prüfstand, später Flug**; die Konstruktion sieht Bauraum für eine spätere Flugsteuerung vor |
| Maßstab | **1:4**: Flügelkreis Ø 375 mm, Flügel 150 × 30 mm, 8 je Ebene, Ebenenabstand 60 mm, offene Mitte |
| Motor | EMAX ECO II 2306 **KV1900** an 6S, ein Motor je Rotor |
| Antrieb | **Ritzel auf der Motorwelle greift direkt in den Zahnkranz am Rotor** (eine Stufe, **14 Z / 91 Z, Modul 1 → 6,5:1**, Phase 1). Der Zahnkranz liegt axial außen am Rotor, die Motoren sitzen oben bzw. unten am Mittelrohr. Ein 1:1-Direktantrieb mit diesem Motor wurde verworfen: 33–69 A bei ~30–36 % Wirkungsgrad |
| FC/ESC | **SpeedyBee F405 V4 + BLS 55A**; ESC mit **Bluejay** geflasht (bidirektionales DShot, Drehzahl je Motor) |
| Empfänger | ELRS (CRSF) |
| Akku Antrieb | Tattu 1550 mAh 6S |
| Zahnkranz | **selbst gedruckt** (PA-CF, 91 Z, Modul 1) |
| Servomodell | **noch offen**; CAD V1 nutzt ein Platzhalter-Hüllmaß der 9-g-Klasse |
| Pitch | **ein Servo je Flügel (16)**, gesteuert über den FC; für **langsame Verstellung**: kollektiv je Ebene und Einzeltrimmung je Flügel. Austauschbare Wurzeladapter bleiben als Rückfallebene und für den ersten Schleudertest |
| Zyklische Steuerung | **nicht mit Servos**: 1/Umlauf entspricht 38–57 Hz, Hobby-Servos schaffen ~5–10 Hz. Wird für die Flugphase separat gelöst |
| Servo-Versorgung | **Akku + Funk auf jedem Rotor** (keine Schleifringe) |
| Drucker | Bauraum 200 × 148 × 150 mm: Flügel liegend (Bahnen längs der Spannweite), Nabenringe einteilig ≤ Ø 140 mm, Rahmen und Schutzring segmentiert bzw. Carbonrohre mit gedruckten Knoten |
| Werkstoff | Rotorteile **PETG-CF / PA-CF** (gehärtete Düse), Rahmen PETG |
| Außenring | **später als Option** |
| Drehmomentmessung | **eine Wägezelle für das Summen-Reaktionsmoment**; Einzelmomente aus Motorstrom × Kt |
| Testort | **draußen** |

## 1. Ziel

Ein verkleinertes Funktionsmodell der R04-Anordnung: zwei übereinanderliegende, gegenläufige Ringrotoren mit je 8 einzeln pitchverstellbaren Flügeln. Es soll zuerst auf einem Prüfstand Schub, Reaktionsmoment, Drehzahl und Leistung über Pitch und Drehzahl messen und damit den Simulator validieren. Später soll es fliegen. Nicht nachgebildet werden Magnetführung, Linearantriebe und die schnelle Pitchdynamik von R04.

## 2. Vorauslegung

**Phase 1 abgeschlossen:** Die maßgeblichen Werte stehen in [auslegung/Auslegung.md](auslegung/Auslegung.md). Ergebnis: Übersetzung 6,5:1, Schweben bei Pitch 14°/16,7° und ≈ 2 200 U/min mit ≈ 7,6 A je Motor, ≈ 129 W und ≈ 13 min; Maximalpunkt bei Schub/Gewicht 2 mit ≈ 3 110 U/min; Servobereich −2…+21°; Modellmasse ≈ 1,10 kg. Die folgende Tabelle ist die **ursprüngliche Grobschätzung mit 10:1** und bleibt nur zur Nachvollziehbarkeit stehen.

| Betriebspunkt | Rotordrehzahl | Schub | P aero | Motor | P elektr. | Flugzeit* |
|---|---|---|---|---|---|---|
| Schweben (Masse ≈ 1,1 kg) | ≈ 2 600 U/min | ≈ 1,2 kg | ≈ 105 W | ≈ 26 000 U/min, ≈ 5 A | ≈ 175 W | ≈ 9 min |
| 30 m/s bei r = 0,6 R | 2 550 U/min | 1,16 kg | 103 W | ≈ 4,8 A | ≈ 170 W | ≈ 10 min |
| 40 m/s bei r = 0,6 R | 3 400 U/min | 2,07 kg | 241 W | ≈ 9,6 A | ≈ 345 W | ≈ 5 min |

Pitch oben 12°, unten auf Drehmomentgleichgewicht (≈ 14,6°). \* 80 % Akkunutzung, grobe Motorverluste, optimistisch. Re im Modell ≈ 60–80 · 10³ statt ≈ 3 · 10⁵ bei R04: Die Messwerte sind konservativ und nicht 1:1 hochrechenbar.

**Massenbudget (Schätzung):** Antriebsakku 250 g, 2 Motoren 64 g, Stack 25 g, Empfänger 2 g, 2 Rotoren mit Flügeln und Nabenring ~200 g, Zahnräder, Lager und Mittelrohr ~80 g, Rahmen ~200 g, Kabel ~30 g, **Rotorelektronik 2 × ~100 g** (8 Servos, Akku, Funkmodul). Summe ≈ **1,05–1,15 kg**.

## 3. Mechanik

- **Antrieb:** Motor neben der Achse, Stahlritzel Modul 1, 14 Z (auf M5-Wellenadapter) im Außenzahnkranz (91 Z, Kopfkreis Ø 93 mm, Achsabstand 52,5 mm). Das ergibt 6,5:1. Der Zahnkranz sitzt axial außerhalb der Flügelebene und ist über Speichen mit dem Nabenring verbunden. Die Umfangsgeschwindigkeit der Verzahnung erreicht bis zu 18 m/s: Zahnkranz aus PA-CF oder als POM-Normzahnrad (90 Z), gefettet. Oberer und unterer Motor laufen gegensinnig, die Drehrichtung wird über die ESC-Konfiguration festgelegt.
- **Lagerung:** feststehendes Aluminium-Mittelrohr Ø 30 mm, je Rotor ein Dünnringlager 6806 (30 × 42 × 7). Ein Distanzstück legt den Ebenenabstand fest; ein zweites Distanzstück erlaubt die Variation des Abstands.
- **Flügel:** einzeln gedruckt, mit Pitchachse bei 50 % Sehne (wie R04). Die Wurzel sitzt auf einer Stahlstiftachse in zwei Lagerstellen am Nabenring. Der Servoarm greift über ein kurzes Gestänge an einem Wurzelhebel an. Die **Fliehkraft (≈ 110 N je Flügel bei 3 400 U/min)** nimmt der Nabenring über einen Axialanschlag bzw. ein Axiallager an der Wurzel auf, **nicht der Servo**.
- **Servos:** so nah wie möglich an der Achse (r ≈ 30–45 mm). Dort wirken 180–580 g; Hobby-Servos sind dafür nicht spezifiziert. Deshalb gibt es vor dem Einbau einen **Schleudertest einzelner Servos** (Phase 3a). Anforderungen: digital, Metallgetriebe, HV (bis 8,4 V, damit direkt an 2S ohne BEC), ≥ 1,5 kg·cm, ≤ 9 g. Geschätzter Bedarf: Propellermoment ≈ 0,15 kg·cm, aerodynamisches Moment um die 50-%-Achse ≈ 0,1 kg·cm.
- **Rotorelektronik:** je Rotor ein ESP32-C3-Modul, ein 2S-LiPo (~300–450 mAh, als **zwei Einzelzellen gegenüberliegend** zur Massensymmetrie), Schalter und Ladebuchse. Alles sitzt auf dem Nabenring in gedruckten Taschen. Der Rotor wird mit vollständig bestückter Elektronik gewuchtet.
- **Rahmen:** gedrucktes Mittelteil mit Motorhaltern, Akkuträger und Stack-Halter (30,5 × 30,5 mm); Füße bzw. Prüfstandsadapter. Für die Flugphase kommt ein segmentierter Schutzring dazu.

## 4. Elektronik und Steuerkette für die Servos

```
Sender ─ELRS─► Empfänger ─CRSF─► FC (F405 V4) ─DShot─► ESC ─► Motor oben/unten
                                   │
                                   └─UART (MSP bzw. MAVLink)─► Pitch-Bridge (ESP32, feststehend)
                                                                  │ ESP-NOW (Funk)
                                         ┌────────────────────────┴────────────────────────┐
                                  Rotor oben: ESP32-C3 ─► 8 Servos         Rotor unten: ESP32-C3 ─► 8 Servos
                                  (2S-Akku, Telemetrie zurück: Spannung, Link)
```

- Der **FC ist die Quelle der Pitchwerte**. Auf dem Prüfstand (Betaflight) liest die Bridge per MSP die Kanäle bzw. Servowerte (kollektiv oben, kollektiv unten, Trimmung). In der Flugphase (ArduPilot) liest sie per MAVLink die Servoausgänge.
- Die **Rotor-Controller** setzen Kommandos in 8 Servo-PWM-Signale um und begrenzen die Pitchwinkel auf einen erlaubten Bereich, z. B. −2…20°.
- **Failsafe:** Bei Funkverlust über 200 ms oder Unterspannung des Rotorakkus fahren die Servos auf einen sicheren Pitch, und der FC drosselt die Motoren. Ein Arm-Schalter am Sender gibt Motoren und Servos frei.
- **Antrieb:** BLS 55A mit Bluejay, DShot600 bidirektional, Motordrehzahl im Blackbox-Log, Strom und Spannung über den ESC-Sensor.

## 5. Prüfstand und Messung (draußen)

- **Aufbau:** Gestell aus 2020-Profil; das Modell sitzt auf einer Schubwaage mit Wägezelle 5 kg und HX711, quer dazu ein Drehmomenthebel mit Wägezelle 1 kg für das Summen-Reaktionsmoment. Die Erfassung läuft über ein ESP32 mit Zeitstempel, die Synchronisation mit dem FC-Log über einen Gasimpuls.
- **Draußen:** Die Rotorebene liegt mindestens 1,5 m über dem Boden, weil Bodeneffekt die Messung verfälscht. Gemessen wird nur bei Windstille (< 2 m/s, Windmessung mitprotokolliert) und Trockenheit. Leer-Messungen vor und nach jeder Reihe dienen der Nullpunktkontrolle.
- **Messmatrix:** Drehzahl 1 000…3 400 U/min × Pitch kollektiv 4…18° in 2°-Schritten (Servos) × Betrieb nur oben / nur unten / beide × zwei Ebenenabstände. Ergebnis: Nachlaufverlust des unteren Rotors, Pitch für Drehmomentgleichgewicht, Leistung über Schub.
- **Auswertung:** Python-Skript mit Vergleich zum Simulator, anschließend Kalibrierung der Polaren- und Nachlaufparameter.

## 6. Phasen

| Phase | Inhalt | Ergebnis |
|---|---|---|
| 1 ✓ | Simulator um Modellmaßstab, Motor-/Getriebe-/Akkumodell und Rotormasse erweitern; Auslegung finalisieren | [Auslegung.md](auslegung/Auslegung.md): 14/91, Pitch 14°/16,7°, −2…21°, ≈ 1,10 kg |
| 2 (V1 ✓) | Parametrisches FreeCAD-Modell (Skript wie im Projekt): Nabenring mit Zahnkranz, Flügel mit Wurzelachse, Servo- und Akkutaschen, Ritzel, Mittelrohr, Rahmen, Prüfstandsadapter; STL ≤ 200 × 148 × 150 mm | [cad/README.md](cad/README.md): Entwurf V1 kollisionsfrei, alle Teile passen aufs Bett, Masse ≈ 1 195 g; V2 nach Servoauswahl |
| 3a | Schleudertest: einzelne Servos und Flügel auf einer Testnabe bis 120 % Nenndrehzahl | Bauteilfreigabe |
| 3b | Druck, Montage, Wuchten, Schleudertest je Rotor | freigegebene Rotoren |
| 4 | Firmware: Bluejay, Betaflight-Konfiguration, Pitch-Bridge und Rotor-Controller (ESP32, Arduino/PlatformIO), Failsafe-Tests | betriebsbereites System |
| 5 | Prüfstandsmessungen draußen nach Matrix | Messdaten + Simulatorabgleich |
| 6 (optional) | Konzept für die Flugsteuerung (Roll/Nick), Umstieg auf ArduPilot, gefesselter Schwebeflug | Flugversuch |

## 7. Sicherheit

Zwei gedruckte Rotoren mit je 8 Flügeln plus Servos und Akkus bei bis zu 3 400 U/min speichern viel Energie. Bei einem Bruch fliegen Teile mit bis zu ~70 m/s weg.
- Betrieb nur mit Schutzwand (Polycarbonat ≥ 4 mm) zwischen Rotorebene und Personen.
- Mindestabstand 10 m, niemand in der Verlängerung der Rotorebene.
- Arm-Schalter und Failsafe vor jeder Messreihe testen.
- Schrittweise hochfahren.
- Rotor-LiPos sind mechanisch gesichert und gegen Fliehkraft gekapselt.
- Akkus nur in der LiPo-Tasche laden.
- Draußen auf privatem Gelände testen. Für den späteren Freiflug gelten die Regeln für unbemannte Fluggeräte (EU-Kategorie „Offen“, Modell > 250 g: Registrierung als Betreiber und Kompetenznachweis).

## 8. Offene Punkte (für die Phasen 1–2)

1. Konkretes Servomodell auswählen (Kriterien in Abschnitt 3) und 2–3 Kandidaten im Schleudertest vergleichen.
2. Rotorakku: Kapazität nach Servostrom festlegen (Messung im Betrieb). Prüfen, ob 2 × 1S gegenüberliegend als 2S gebraucht wird oder 1S + Step-up genügt.
3. Flugsteuerung für Roll und Nick (Phase 6): Ruderklappen im Abwind, schnelle Pitchaktuatoren oder eine Kombination aus Drehzahl- und Kollektivdifferenz.
4. ~~Zahnkranz~~ → selbst gedruckt (PA-CF, 91 Z).

## 9. Einkaufsliste (ohne die vorhandenen Komponenten)

| Bereich | Teil | Menge | Zweck |
|---|---|---|---|
| Messtechnik | ESP32-DevKit | 1 | Datenerfassung Prüfstand |
| | Wägezelle 5 kg + HX711 | 1 | Schub |
| | Wägezelle 1 kg + HX711 | 1 | Summen-Reaktionsmoment |
| | Laser-/Optik-Drehzahlmesser + Reflexmarke | 1 | Kontrolle der ESC-Drehzahl |
| | Feinwaage 0,01 g, Hand-Anemometer | je 1 | Wuchten, Windkontrolle draußen |
| Rotorelektronik | ESP32-C3-Mini-Modul | 3 (+1) | 2 × Rotor, 1 × Pitch-Bridge |
| | HV-Digital-Mikroservo, Metallgetriebe (Kandidaten) | 16 + 4 Test | Pitch je Flügel |
| | LiPo-Zellen 1S 300–450 mAh, Schalter, JST-Stecker | 4 (+2) | Rotorversorgung (2S je Rotor) |
| | 2S-Ladegerät mit Balancer | 1 | Rotorakkus |
| Mechanik | Dünnringlager 6806-2RS | 2 (+2) | Rotorlagerung |
| | Aluminiumrohr Ø 30 mm, Wand ≥ 1,5 mm | ~200 mm | Mittelachse |
| | Stahlritzel Modul 1, 14 Z, Bohrung 5 mm (M5-Welle) | 2 (+1) | Antrieb 6,5:1 |
| | optional POM-Stirnrad Modul 1, 90 Z, Breite ≥ 6 mm | 2 | Zahnkranz als Kaufteil statt Druck |
| | Stahlstifte Ø 3 mm, Mini-Axiallager bzw. Anlaufscheiben | 16 + Reserve | Flügelwurzel, Fliehkraftaufnahme |
| | Carbonrohre Ø 8–10 mm, Gewindeeinsätze M2/M3, Schrauben | 1 Satz | Rahmen, Nabe |
| | Alu-Profil 2020 + Winkel, Polycarbonat ≥ 4 mm ~1 m² | – | Prüfstand, Schutzwand |
| Elektrik | XT60, Silikonkabel 14/16 AWG, 6S-Ladegerät (falls fehlt), LiPo-Taschen | – | Antrieb |
| Druck | gehärtete Düse 0,4 mm; PA-CF / PETG-CF, PETG | je ~0,5–1 kg | Rotoren, Rahmen |
