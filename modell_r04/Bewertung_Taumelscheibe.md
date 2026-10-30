# Bewertung: Taumelscheibe statt eines Servos je Flügel

Stand 30.10.2026. Grundlage: CAD-Entwurf V1 (`cad/`), Nachrechnung mit CAD-Masse (`auslegung/Nachrechnung_CAD.json`) und die quasistatische Zyklik-Abschätzung `auslegung/zyklik.js` → `Zyklik_Abschaetzung.json`. Alle Zahlen sind Modellwerte.

**Nachtrag zur neueren Taumelvariante:** Die unten stehenden pauschalen Aussagen „Standard-Mikroservos reichen“ und „unkritisch“ stellen keinen Nachweis dar. Die [unabhängige Prüfung mit H01-Haltern](../modell_r04_taumel/mechanik/README.md) berücksichtigt vollständige Servohebelübersetzung, Fliehkraftreibung, tatsächliche CAD-Trägheit und zusätzliche Masse. Sie bestätigt keine pauschale 9-g-Servoauswahl. Der folgende Text bleibt als früher Konzeptvergleich erhalten.

## Kurzfazit

**Die Taumelscheibe ist für das Testmodell das bessere Hauptsteuerelement.** Sie liefert mechanisch die zyklische Pitchverstellung mit 1/Umlauf (≈ 39 Hz), die für Roll- und Nicksteuerung im Flug nötig ist. Die Servos je Flügel können das prinzipiell nicht (5–10 Hz Stellbandbreite). Zugleich entfallen die drehende Elektronik, die Rotorakkus, die Funkstrecke und die Servobelastung von ≈ 640 g. Verloren geht nur die freie Einzelverstellung je Flügel: Möglich bleiben kollektiv und erste Harmonische. Das Prinzip „individueller Pitch“ von R04 wird damit im Modell nicht mehr abgebildet.

Begünstigt wird das Konzept durch die **feststehende Mittelachse**: Jeder Rotor bekommt seine eigene Taumelscheibe auf der Außenseite des Rohrs. Koaxialhubschrauber brauchen dafür sonst ineinanderliegende Wellen und Gestänge durch den oberen Rotor.

## Vergleich

| Kriterium | Servo je Flügel (CAD V1) | Taumelscheibe je Rotor |
|---|---|---|
| Kollektiver Pitch | ja | ja |
| Zyklischer Pitch 1/Umlauf (≈ 39 Hz) | **nein**: Servos ~5–10 Hz | **ja**, mechanisch |
| Freie Einzelverstellung je Flügel | ja (langsam) | nein; nur Spureinstellung über verstellbare Kugelgelenkstangen |
| Anzahl Servos | 16, drehend | **6, feststehend** (3 je Taumelscheibe) |
| Servobelastung durch Fliehkraft | 470–700 g im Schleudertest, nicht spezifiziert | keine |
| Drehende Elektronik, Akkus, Funk | 2 × ESP32-C3, 4 Zellen, Bridge, Failsafe | entfällt |
| Steuerkette | FC → Bridge → Funk → Rotor-Controller | FC → 6 Servos direkt (PWM) |
| Unwucht durch Elektronik | ≈ 27 g·mm je Rotor | entfällt |
| Masse (Schätzung) | ≈ 1 195 g (CAD V1) | **≈ 1 100 g** (−16 Servos, −Rotorelektronik, kleinere Nabe; +6 Servos, 2 Taumelscheiben mit Lager, 16 Steuerstangen, größerer Zahnkranz) |
| Nähe zum R04-Konzept | individueller Pitch abgebildet | Aerodynamik gleich, Stellprinzip wie beim Hubschrauber |
| Mechanischer Aufwand | Servotaschen, Stifte, Mitnehmer | Taumelscheibe mit Kugelgelenk, Verdrehsicherung, Mitnehmer, 16 Kugelgelenkstangen, Pitchhebel |
| Hauptrisiko | Servos versagen unter Fliehkraft; keine Flugsteuerung | Spiel in der Kette (0,1 mm ≈ 0,5° Pitch), Druckpräzision der Taumelscheibe |

## Steuerwirkung (Abschätzung)

Schwebepunkt mit CAD-Masse: 2 316 U/min, Pitch 14° / 16,7°.

| Größe | Wert |
|---|---|
| Rollmoment je Grad zyklisch, beide Rotoren | **0,13…0,26 Nm/°** (untere Grenze: Abwind passt sich zur Hälfte an; obere: Abwind eingefroren) |
| Bei ±4° zyklisch ausgleichbarer Schwerpunktversatz | **42…84 mm** |
| Schubänderung durch Zyklik | vernachlässigbar (< 0,06 N bei 3°) |
| Steuerfrequenz (1/Umlauf) | 38,6 Hz, mechanisch über die Taumelscheibe |

Die Steuerwirkung reicht für ein Modell dieser Größe deutlich aus. Weil die Flügel starr angebunden sind (gelenkloser Rotor), geht das Moment direkt über Nabe, Lager und Rohr. Bei 4° sind das ≈ 0,5–1 Nm je Rotor, an zwei 6806 im Abstand 29 mm also ≈ ±17–35 N Lagerkraft. Das ist unkritisch. Die Phasenverschiebung zwischen Steuereingabe und Rotorreaktion liegt bei starren Flügeln unter 90°, muss gemessen und im Mischer eingestellt werden. Für die beiden gegenläufigen Rotoren ist sie spiegelbildlich.

## Stellkräfte und Präzision

| Größe | Wert |
|---|---|
| Propellermoment je Flügel (zieht Richtung 0°) | 8,2 N·mm im Schweben |
| Luftkraftmoment (Auftrieb bei 25 % vor der 50-%-Achse, Nase hoch) | 5,5 N·mm |
| Netto | ≈ 2,7 N·mm; Stangenkraft < 1 N bei 12 mm Pitchhebel |
| Stangenweg für −2…21° (Hebel 12 mm) | 4,7 mm |
| Pitchfehler je 0,1 mm Spiel (Hebel 12 mm) | **0,48°** |

Die Kräfte sind klein; Standard-Mikroservos reichen. Maßgeblich ist das **Spiel**: Nötig sind Kugelgelenke aus dem Hubschraubermodellbau (M2), ein spielarmes Kugelgelenk in der Taumelscheibe und Pitchhebel, die so lang sind, wie es der Bauraum erlaubt.

## Auswirkungen auf die Konstruktion (V2)

Die Steuerstangen laufen um. In V1 kreuzen sie die Zone von Ritzel und Motor (r ≈ 38–67 mm über dem Zahnkranz). Daraus folgt eine neue Anordnung:

1. **Nabe kleiner und flacher**: keine Servotaschen, nur Bohrungen für die Wurzelzapfen und Schlitze für die Pitchhebel. Das Profil kann dadurch näher an die Achse rücken (z. B. ab r ≈ 48 mm statt 62 mm), was R04 besser entspricht.
2. **Zahnkranz größer und außen**: 130 Z, Modul 1, Kopfkreis Ø 132 mm (passt aufs Bett). Er liegt wenige Millimeter über den Flügelwurzeln, Mindestabstand zum Flügel bei 25° Gesamtpitch ≥ 3 mm.
3. **Ritzel 20 Z, Motor bei r = 75 mm** über den Flügeln. Übersetzung 130/20 = 6,5:1, also unverändert. Motor und Ritzel liegen damit außerhalb des Umlaufbereichs der Steuerstangen.
4. **Taumelscheibe** auf einer Gleithülse am Rohr über dem Zahnkranz bzw. beim unteren Rotor darunter:
   - feststehender Ring mit Verdrehsicherung, drehender Ring mit 8 Armen, Lager z. B. 6808;
   - Kugelgelenkstangen durch Löcher im mitdrehenden Zahnkranz zu den Pitchhebeln;
   - drei Servos je Taumelscheibe auf der Halteplatte (120°-Anordnung).
5. **Flugsteuerung**: Mischung aus Kollektiv, Zyklik und Phasenwinkel je Rotor; Gieren über Differenzkollektiv bzw. Differenzdrehzahl.
   - Betaflight und INAV unterstützen keine Taumelscheiben.
   - ArduPilot hat einen Modus für Hubschrauber mit zwei Rotoren und Taumelscheiben (TradHeli Dual). Ob er die koaxiale Anordnung abdeckt, muss geprüft werden.
   - Der F405 V4 muss **8 Ausgänge** liefern (2 ESC + 6 Servos); auch das ist zu prüfen.
6. **Prüfstand:** Die Wägezelle für das Reaktionsmoment kann um eine Rollmomentmessung ergänzt werden. Damit lässt sich die Zyklikwirkung direkt messen.

## Varianten

| Variante | Beschreibung | Einschätzung |
|---|---|---|
| **A: Taumelscheibe je Rotor** | kollektiv + zyklisch, 6 feststehende Servos | **empfohlen** für Prüfstand und Flug |
| B: Servo je Flügel (V1) | nur langsamer Kollektiv- und Einzelpitch | nur sinnvoll, wenn das R04-Einzelpitchprinzip selbst getestet werden soll; für den Flug fehlt ein Steuerkonzept |
| C: Taumelscheibe + Einzeltrimmung | wie A, Stangenlänge je Flügel verstellbar (manuelle Spureinstellung) | Bestandteil von A |
| D: Feste Wurzeladapter + Ruderklappen im Abwind | kein Pitch im Betrieb, Steuerung über Klappen | einfacher, aber Pitchkennfeld nur durch Umbau messbar |

## Offene Punkte

1. Entscheidung A oder B (bzw. D).
2. Firmware: Eignung von ArduPilot TradHeli für eine koaxiale Doppel-Taumelscheibe prüfen, sonst eigener Mischer.
3. Ausgänge des SpeedyBee F405 V4 (mindestens 8) prüfen.
4. Taumelscheibe: Druckteil mit Kauflager und Kugelgelenk; spielarm genug? Gegebenenfalls Kugel und Pfanne aus Metall zukaufen.
5. Servoauswahl (6 Stück, feststehend; Anforderungen jetzt einfach: Mikroservo mit geringem Spiel und hoher Stellgeschwindigkeit).
