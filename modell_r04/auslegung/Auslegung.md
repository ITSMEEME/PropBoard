# R04-Testmodell – Auslegung Phase 1

Stand 30.10.2026. Erzeugt mit `node auslegung.js` (Werte aus `Auslegung.json`). **Modellwerte, nicht validiert.** Aerodynamik: BEMT des Simulators mit vereinfachter Polare. Antrieb: Gleichstrom-Ersatzmodell (`antrieb.js`). Die Werte sind durch die Prüfstandsmessung (Phase 5) zu bestätigen.

## Festgelegte Auslegung

| Größe | Wert |
|---|---|
| Maßstab | 1:4: Flügelkreis Ø 375 mm, Flügel r = 37,5…187,5 mm, Sehne 30 mm, NACA 0012, 8 je Ebene, Ebenenabstand 60 mm |
| Übersetzung | **Ritzel 14 Z / Zahnkranz 91 Z, Modul 1 → 6,5:1**; Kopfkreis Ø 93 mm, Achsabstand 52,5 mm. Alternative mit Normzahnrad 90 Z (6,43:1, Kunststoff-Kaufteil möglich): Leistung praktisch gleich |
| Zahnkranzlage | axial außen am Rotor (oberer Rotor oben, unterer unten), da er in der Flügelebene mit den Flügelwurzeln kollidieren würde; Motoren auf Halteplatten oben und unten am Mittelrohr |
| Schwebepunkt | Pitch oben **14°**, unten **16,7°** (Drehmomentgleichgewicht), **≈ 2 200 U/min** Rotor bzw. ≈ 14 300 U/min Motor |
| Pitchbereich der Servos | **−2° … +21°** (Abrissbeginn laut Modell bei ≈ 19° kollektiv oben) |
| Maximalpunkt | Schub/Gewicht 2: **≈ 3 110 U/min**, 2,2 kg Schub |
| Schleudertest | **3 740 U/min** (120 % des Maximalpunkts) |

## Massenbudget (≈ 1 097 g)

| Position | g | Quelle |
|---|---:|---|
| Antriebsakku Tattu 1550 mAh 6S | 255 | Annahme, **wiegen** |
| 16 Flügel (PETG-CF, Füllgrad 0,65) | 173 | Geometrie (10,8 g je Flügel) |
| 16 Servos HV-Mikro | 112 | Annahme 7 g |
| Motorhalteplatten, Akkuträger, Stackhalter | 120 | Schätzung |
| 2 Nabenringe mit Lagerung und Gestänge | 100 | Schätzung |
| 2 Motoren ECO II 2306 inkl. Kabel | 64 | Datenblatt + Kabel |
| 2 Zahnkränze inkl. Speichen | 52 | Schätzung |
| Rotorelektronik 2 × (ESP32-C3, 2 × 1S 400 mAh, Schalter) | 50 | Annahme |
| Kabel, Stecker, Schrauben | 50 | Schätzung |
| Mittelrohr Al Ø 30 × 1, 160 mm | 39 | Geometrie |
| 2 Lager 6806-2RS | 38 | Katalogwert ca. |
| FC + ESC, Empfänger, Pitch-Bridge, 2 Ritzel | 44 | Annahmen |

Rotierende Masse je Rotor ≈ 244 g.

## Betriebspunkte

| | Schweben | Maximalpunkt (Schub/Gewicht 2) |
|---|---|---|
| Rotordrehzahl | 2 203 U/min | 3 114 U/min |
| Schub | 1,10 kg | 2,20 kg |
| Aerodynamische Leistung | 89 W | – |
| Motorstrom je Motor | 7,6 A | 14,1 A |
| Motorverlust je Motor | 12 W | 27 W |
| Tastgrad | 35 % (bei 60 % Ladung) | 54 % (am Flugende, 20 % Restladung) |
| Elektrische Leistung | ≈ 129 W | ≈ 344 W |
| Schwebedauer | **≈ 13 min** (80 % Akkunutzung, optimistisch) | – |
| Gütegrad | 0,78 | – |

## Wahl von Pitch und Übersetzung

- **Pitch:** Mehr Pitch bei weniger Drehzahl senkt die Schwebeleistung (`Schwebepunkt_ueber_Pitch.csv`: 10° → 173 W, 14° → 142 W, 18° → 130 W bei vorläufig 10:1). Ab etwa 18–19° erreicht der effektive Anstellwinkel aber den Abrisswinkel der Polare. Gewählt ist 14° mit ≥ 2° Abstand. **Der Abrisswinkel bei Re ≈ 5 · 10⁴ ist im Modell sehr unsicher**, daher ist das die wichtigste Größe der ersten Messreihe.
- **Übersetzung:** Das Leistungsoptimum ist flach (`Uebersetzung_Varianten.csv`: 5,7:1 → 128 W, 6,5:1 → 129 W, 10:1 → 143 W, 12,8:1 → 157 W). Weil Regler-Teillastverluste nicht modelliert sind, wurden zusätzlich Tastgrad im Schweben ≥ 35 % und Ritzel ≥ 12 Z gefordert. Daraus ergeben sich 14/91. Die frühere Annahme 10:1 im Plan war zu hoch.
- **Prüfmatrix** (`Pruefmatrix.csv`, 1 000…3 100 U/min × 4…18° Pitch): Alle 48 Punkte sind elektrisch fahrbar, auch am Flugende. Der stärkste Punkt (3 100 U/min, 18°) erreicht 3,1 kg Schub bei 556 W und 22 A je Motor. Punkte über ≈ 15 A je Motor nur kurz fahren (≤ 10 s), dabei die Motortemperatur beobachten.

## Lasten im Schleudertest (3 740 U/min)

| Größe | Wert | Bewertung |
|---|---:|---|
| Fliehkraft je Flügel (10,8 g, Schwerpunkt r = 112,5 mm) | **186 N** | Aufnahme über Wurzelstift und Axialanschlag am Nabenring, nicht über den Servo |
| Mittlere Zugspannung im Flügelquerschnitt | 3,9 MPa | klein gegenüber PETG-CF/PA-CF in Bahnrichtung; kritisch sind Wurzelauge, Stift und Kriechen |
| Servobeschleunigung bei r = 30 / 45 mm | **470 / 700 g** (Schweben: ≈ 160 / 245 g) | Hobby-Servos dafür nicht spezifiziert → Schleudertest Phase 3a |
| Radialkraft eines 7-g-Servos bei r = 45 mm | 48 N | formschlüssige Servotasche erforderlich |
| Propellermoment je Flügel (verdreht Richtung 0°) | 29 N·mm (0,3 kg·cm) | Servo ≥ 1,5 kg·cm ausreichend |
| Blattspitzengeschwindigkeit | 73 m/s | – |
| Kinetische Energie je Rotor | **≈ 111 J** | entspricht 1 kg bei 15 m/s → Schutzwand Pflicht |
| Zahnkraft am Zahnkranz | 12 N | – |
| Zahnfußspannung Ritzel (Lewis, b = 6 mm) | 7 MPa | unkritisch |
| Umfangsgeschwindigkeit Verzahnung | **18 m/s** | hoch für gedruckte Zahnräder: Stahlritzel, Zahnkranz aus PA-CF oder POM-Kaufteil, fetten, Temperatur beobachten |

## Annahmen und Unsicherheiten

- BEMT mit vereinfachter Polare; Abriss und Profilwiderstand bei Re ≈ 5–8 · 10⁴ unsicher (laminare Ablöseblasen nicht modelliert).
- Unterer Rotor im Nachlauf des oberen, Rückwirkung nach oben fehlt; Einfluss von Zahnkränzen und Motoren im Zu- und Abstrom fehlt.
- Motor: Leerlaufstrom proportional zu n^0,5 angenommen, Getriebe 0,92, ESC 0,95, maximaler Tastgrad 0,95.
- Akku: typische LiPo-Kennlinie, Innenwiderstand 5 mΩ je Zelle angenommen, Masse 255 g angenommen.
- Massen teilweise geschätzt; nach Phase 2 aus dem CAD und nach dem Bau durch Wiegen ersetzen.

## Dateien

| Datei | Inhalt |
|---|---|
| `antrieb.js` | Motor-, Getriebe-, ESC- und Akkumodell (auch im Simulator genutzt) |
| `auslegung.js` | Auslegungsrechnung |
| `Auslegung.json` | alle Ergebnisse maschinenlesbar |
| `Schwebepunkt_ueber_Pitch.csv`, `Uebersetzung_Varianten.csv`, `Pitchbereich.csv`, `Pruefmatrix.csv` | Variantenrechnungen |

Im Simulator (`kreis_r04/simulation/R04_Simulator.html#testmodell` oder Knopf „Testmodell 1:4 laden“) lassen sich Übersetzung, Ladezustand, Pitch und Drehzahl interaktiv variieren; Motorstrom, Tastgrad, Leistung und Laufzeit werden live angezeigt.
