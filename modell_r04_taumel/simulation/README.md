# H01 – CAD-basierter geregelter Freiflug

## Neu in P10: 3D-Ansicht, Strömung, Bodenstart, Steuerung

- **Darstellung (WebGL):** Die Ansicht zeigt die native [P10-Baugruppe](../integration_p10/README.md) mit 774 Bauteilen: Servohalter, Planetenstufe, Kabelbaum und Landegestell. Quelle ist `p10_mesh.js`, exportiert aus FreeCAD.
  - Alle Gelenkrahmen werden in jedem Bild aus dem Physikzustand berechnet (`kinematik_p10.js`). Bewegt werden Servohebel, Servo- und Blattgestänge, beide Taumelscheiben, die 16 Blattwinkel, die Rotoren und die Planeten.
  - Der Abgleich gegen FreeCAD-Referenzrahmen ergibt Abweichungen unter 1e‑13 mm (`pruefen.js`).
  - **Zeitlupe** bis 0,015× macht die zyklische Blattverstellung sichtbar. Bei Echtzeit wird die Rotorscheibe halbtransparent dargestellt.
  - Kameras: Verfolgen, Orbit, Seite, Oben, Taumelscheibe oben/unten, Landegestell. Naben/Hohlräder, Servogehäuse und Kabel lassen sich ausblenden.
- **Strömung (`stroemung.js`):** Partikelbahnen und ein Geschwindigkeitsschnitt aus der Aktuatorscheiben-Näherung.
  - Grundlage sind die induzierte Geschwindigkeit je Rotor aus der Simulation, die Einschnürung auf R/√2 per Kontinuität und der Drall aus dem Rotormoment.
  - Dazu kommen Wind und Fahrzeugbewegung. Am Boden wird die Strömung in eine radiale Abströmung umgelenkt.
  - Das ist reine Visualisierung, keine CFD, und hat keine Rückwirkung auf die Physik.
- **Steuerung (`flugsteuerung.js`):** Ablauf Bodenstart → Hochlauf (3 s Drehzahlrampe) → Abheben auf 1 m → Flug → Landung mit Aufsetzerkennung → Auslauf.
  - Zwei Modi:
    - **Positionsmodus:** Knüppel verschieben den Haltepunkt mit 1 m/s und 0,8 m/s Steigrate.
    - **ANGLE-Modus:** Knüppel geben Roll-/Nickwinkel bis 25°, Gierrate 90°/s und Steigrate 1,5 m/s vor.
  - Eingabe über Tastatur (W/S Nick, A/D Roll, Q/E Gier, R/F Steigen, T Start, L Landen, M Modus, Leertaste Pause), Gamepad (Mode 2, A Start, B Landen, Y Modus) oder virtuelle Knüppel mit Maus/Touch.
  - Wind mit Richtung und Böigkeit einstellbar.
  - Positionsmodus bei Rechtshändigkeit: Vorwärts ist +x in Gierrichtung, links ist +y. Damit kehrt sich gegenüber der alten WASD-Belegung A/D um.
- **Physik-Optionen (Standard aus, die 19 H01-Fälle bleiben bitgleich):**
  - `massModel:'P10'` entfernt die ersetzten H01-Teile und fügt alle P10-Teile mit Masse, Schwerpunkt und Tensor aus der nativen Baugruppe hinzu (`p10_massen.json`). Das 45-g-Kabelbudget wird durch die modellierten Leitungen ersetzt.
  - `drive:'P10_HOHLRAD'`: Der Motor dreht gleichsinnig; Drehimpuls und reflektierte Trägheit enthalten die Stützplaneten.
  - `ground:true`: Feder-Dämpfer-Bodenkontakt mit Reibung an den vier Schellenringen sowie Kufen- und Endpunkten (tragen bei Neigung mit), Bodeneffekt nach Cheeseman-Bennett (empirisch), Grenze für harte Landung 3 m/s.
  - `mode:'angle'|'idle'` im Sollwert für Handsteuerung und Bodenbetrieb.
- **Neue Testfälle:**
  - `P10_Bodenstart_Schweben_Landung` (Positionsmodus mit Manövern)
  - `P10_ANGLE_Handsteuerung` (Lagewinkel, Steigen, Gieren)
  - `P10_Boee_3ms_Schweben`

  Die beiden Bodenfälle gelten als erfolgreich, wenn das Fahrzeug aufrecht gelandet und abgeschaltet ist.
- **Masse im P10-Modell:** 1,934 kg mit 69-g-Servos, Schwebedrehzahl ≈ 2950 U/min (H01-Savöx-Fall: 1,578 kg ohne Halter/BEC). Siehe [P10-Massen](../integration_p10/README.md#masse).

Bekannte Abweichung zwischen Darstellung und Physik:

- Die Darstellung verwendet die P09-Blattanlenkung (r = 33 mm), die Physik weiter das H01-Kinematikmodell (r = 32 mm). Die gezeigten Blattwinkel weichen dadurch um Bruchteile eines Grads ab.
- Die Servoachsen der Physik bleiben die H01-Vorschlagsgeometrie.

[Simulator öffnen](H01_Flugsimulator.html). Die Seite läuft offline im vollständigen Checkout oder im beigefügten ZIP. Darstellung, Browser und Node-Testserie verwenden **dieselbe** Physik und dieselben Regler. Im bisherigen [Auftriebssimulator](../../kreis_r04/simulation/R04_Simulator.html) gibt es einen direkten Link hierher.

**Numerisch verifiziertes, reduziertes Modell; keine empirische Validierung oder Flugfreigabe.** Die tatsächlichen Servo-Typen, Halterungen, Reibung, Polaren, Regelphase und BEC sind offen. Die bestehenden mechanischen Freigabepunkte aus [der Mechanikprüfung](../mechanik/README.md) bleiben bestehen. Die Simulation ersetzt insbesondere keinen Festigkeits- oder Rotor-Prüfstandstest. Die PID-Werte sind Simulationsparameter und dürfen nicht ungeprüft auf eine Flugsteuerung übertragen werden.

## Welches echte Modell verwendet wird

`cad_import.py` liest `halterungen/Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd`. Die Quelldatei wird mit SHA256 identifiziert. Alle massentragenden CAD-Körper gehen mit ihren globalen Volumen-Schwerpunkten und vollen Trägheitstensoren ein; Zusammensetzung und Parallelachsenverschiebung stehen einzeln in `modell_h01.json`. `cad_mesh.js` enthält die tatsächlichen, gröber triangulierten CAD-Oberflächen. Es handelt sich um keine generische Quadrokopter-Grafik.

Aus dem aktuellen CAD:

- Masse einschließlich bisherigem Budget: **1,217676 kg**, mit sechs 9-g-Platzhaltern.
- Schwerpunkt im CAD-Rahmen: **(0, −0,125, −34,387) mm**.
- Trägheitsmatrix um den Schwerpunkt in kg·m²:

```
[ 0.00960702849   0.00000042839  -0.00039518030 ]
[ 0.00000042839   0.01025837161   0.00000591918 ]
[-0.00039518030   0.00000591918   0.00362057266 ]
```

Der Standardflugfall verwendet **20 g je Servo und damit 1,283676 kg**. Die sechs zusätzlichen Massen werden an den tatsächlichen CAD-Platzhalterpositionen addiert; Schwerpunkt und Tensor werden neu berechnet. Das behauptet keine geometrische Passung größerer Servos.

Batterie: 78 × 37 × 52 mm, 254 g, 6S/1550 mAh aus deiner Angabe. FC/ESC-Massenaufteilung 10/16 g innerhalb des bisherigen 26-g-Budgets ist angenommen. Empfänger, Kabel, fehlende Schraubenköpfe und Gurte werden mit expliziten Massen, Positionen und räumlichen Abmessungen angesetzt. Effektive Druck-Füllgrade sind homogen angenommen. Tatsächliche Halter für größere Servos und BEC-Masse fehlen weiterhin.

## Neue Savöx-Daten und M01-Geometrie

Die zusätzlichen Fälle `Savox_7_4V_Manoever`, `Savox_6_0V_Boee`, `Savox_7_4V_Reibung_0_20` und `Savox_7_4V_XFOIL_N4` verwenden deine Zeichnung/Spezifikation des SB-2271SG(+): 69 g, 6,0–7,4 V, 15/20 kg·cm und 0,08/0,06 s/60°. Masse **1,577676 kg**, ohne neue Halter/BEC. Der Standard der Browserauswahl ist jetzt der Savöx-7,4-V-Manöverfall; die alten generischen 9-/20-/60-g-Vergleiche bleiben erhalten.

`servo_profiles.json` ersetzt für diese Fälle die sechs Massenverteilungen durch die tatsächlichen nominalen M01-Hüllen. Alle anderen H01-Massen bleiben erhalten. Die Grafik ersetzt die alten Servo-Platzhalter durch diese Hüllen. Interne Dichteverteilung, Laschendicke und Savöx-Bohrungs-/Spline-Maße sind teilweise angenommen. Der Legacy-Parameter `servoStallNm` dient hier nur als **angenommene Momentgrenze anhand der angegebenen „Dynamic Torque“**, nicht als verifiziertes Stall- oder Dauermoment. Stellzeit-Lastbedingungen, Totzeit, Lastkennlinie, Strom und PWM-Daten fehlen. [Daten und Lastscreen](../messdaten/README.md).

Der optionale XFOIL-Fall nutzt berechnete Polaren des echten CAD-Profils. Rund 20 % seiner tatsächlichen Blattelementauswertungen benötigen das weiterhin unvalidierte bisherige Ersatzmodell. Dieser Anteil steht im Log und Browser. Die stationären BEMT-Vergleiche haben andere Abdeckung, siehe [Aerodynamik](../aerodynamik/README.md). CM wird aufbewahrt, aber noch nicht vollständig im zyklischen Servo-Luftlastmodell berücksichtigt.

Die vollständige Bewegungsdarstellung einschließlich Hörnern und Lager-/Motorteilen liegt in der [nativen M01-FreeCAD-Baugruppe](../bewegung/README.md). Die Browseransicht animiert weiterhin keine einzelnen Servo-/Blatt-Pitchbewegungen. KST 760 µs bleibt eine reine CAD-Vergleichsoption ohne Flugfreigabe oder hinterlegte Lastdaten.

## Physik

Koordinaten: rechtshändiger Körperrahmen, +z nach oben; Weltrahmen +z nach oben. Lage als normierte Quaternion. Position/Geschwindigkeit beziehen sich auf den Schwerpunkt. Es gibt keine künstliche Schwebekraft, keine an den Sollwert festgesetzte Lage und keine automatische Positionsrücksetzung.

| System | Modell | Wichtige Grenzen |
|---|---|---|
| Starrkörper | `m dv/dt = R F − m g`; vollständiger Tensor, `J dω/dt = M − ω × H`; Rotor-Drehimpuls und dessen Änderung | starre Struktur; keine Schwingungen, Unwucht oder Resonanz |
| Rotoren | 8 Blätter je Ebene, Außenradius 187,5 mm, Profilbeginn 48 mm, Sehne 30 mm, Ebenenabstand 60 mm aus CAD; 10 radiale und 16 azimutale Integrationspunkte | azimutal gemittelte Kräfte; keine aufgelösten Blattpassagen |
| Aerodynamik | vorhandene Reynolds-/Abriss-abhängige Profilpolare; Blattelement-Auftrieb und Widerstand, Kräfte und Hebelarme um den CAD-Schwerpunkt; Körpergeschwindigkeit, Wind und Körperdrehrate in lokaler Anströmung | Polare nicht gemessen, uniforme induzierte Geschwindigkeit je Rotor statt radial aufgelöstem BEMT; keine CFD |
| Induzierter Zustrom | instationäre erste Ordnung, 80 ms Annahme; Impulsbilanz `T = 2 ρ A vi (vi + Vext)` im normalen Arbeitsbereich | Wirbelring, tiefer Sinkflug, Rückströmung und Autorotation nicht validiert |
| Koaxialkopplung | oberer Nachlauf beschleunigt und kontrahiert, radial geglätteter Rand; unterer Rotor sieht gegenläufigen Drall aus Drehimpulsbilanz | keine untere Rückwirkung auf oberen Rotor, keine diskreten Wirbel; Zeitkonstante und Randbreite angenommen |
| Rumpf | quadratischer Luftwiderstand, effektive Fläche 0,025 m² angenommen | kein CAD-CFD-Widerstand; keine aerodynamischen Strukturmomente |
| Motoren | zwei ECO-II-2306-KV1900-Ersatzmodelle, Gegen-EMK und 62 mΩ, 46-A-Modellgrenze, ESC-Tastgrad 0…0,95, 6,5:1, Getriebewirkungsgrad 0,92 | quasistationäre Ströme, keine Kommutierung/Induktivität, Temperatur und ESC-Firmware; Motorträgheit 1,2e−6 kg·m² angenommen |
| Akku | 6S-LiPo-OCV-Kurve, 35 mΩ Gesamtinnenwiderstand, Ladezustandsintegration | Widerstand/Kurve angenommen; keine thermische Simulation oder validierte C-Rate |
| Servos | 6 interne Positions-PID-Modelle, 12 ms Totzeit, begrenzte Beschleunigung und Geschwindigkeit; lineare Drehmoment-/Geschwindigkeitsreserve | kein Datenblatt eines ausgewählten Servos; keine reale Servofirmware; ideal gehaltenes blockiertes Servo, kein Rücktreiben |
| Servolast | virtuelle Arbeit mit neutralem CAD-Gestänge-Jacobi-Modell; Fliehkraft-Torsion, Gleitreibung der Flügelnut, angenommener aerodynamischer Hebelarm | lokale Lastabschätzung, keine exakte Last außerhalb Neutralstellung; dynamische Blatt-Pitch-Trägheit, Losbrechen, Vorspannung und strukturelle Biegung fehlen |
| Sensoren | Gyro-Rauschen mit reproduzierbarem Seed, Filter; gefilterte vertikale Beschleunigung | perfekte Positions-/Lageschätzung, ideale Rotor-Drehzahlmessung; kein EKF, GPS, Barometer, Drift oder Funkverlust |

Der gesamte Motor/Getriebe/Rotor-Aufbau speichert Drehimpuls. Das Motordrehmoment wird nicht gleichzeitig als unabhängiges zweites aerodynamisches Giermoment hinzugefügt: Das Modell berücksichtigt den aerodynamischen Widerstand und die Änderung des gespeicherten Drehimpulses. Die Motorwelle dreht wegen der Außenverzahnung gegenläufig zur zugehörigen Rotorwelle.

## Taumelscheibe und Regelung

Die Simulation berechnet aus den sechs tatsächlichen Servo-Winkeln die beiden Taumelscheibenlagen durch Lösen der drei festen Servo-Gestängelängen. Daraus folgt jeder Blattwinkel mit der tatsächlichen 15-mm-Blattanlenkung. Der lokale untere Rahmen wird mit `diag(−1,1,−1)` auf den Körperrahmen abgebildet. Die Steuerwirkung wird aus Kräften/Momenten der nominellen Geometrie differenziert und als 4×6-Mischer für Gesamtschub, Roll-, Nick- und Giermoment verwendet. Die sechs Servos fahren während stationärer Zyklik keine erzwungene Rotorfrequenz.

Der Servo-Aufbau ist der **Vorschlag aus der Mechanikprüfung**, kein bereits konstruiertes Kaufservo: tangentiale Achse, 8-mm-Horn, Achsradius 58,3 mm, lokale Höhe 60 mm, Anschlussradius 50,3 mm. `kinematik_referenz.json` enthält unabhängige Python-Referenzlösungen für den JS-Abgleich.

Regelkaskade: Positions-PID → Sollbeschleunigung → Solllage/Höhen-Beschleunigungsregler → Lagefehler → Drehraten-PIDs → Moment/Schub-Allokation → Servo-PIDs. Zwei eigene Drehzahl-PIDs regeln die Motor-Tastgrade. Die nominelle Getriebe-/Rotorlast liefert eine Vorsteuerung; der Regler bekommt keine tatsächlichen momentanen aerodynamischen Lasten als perfekte Vorsteuerung. Der Beschleunigungsregler kompensiert langsame Schubmodellfehler.

| Schleife | Kp | Ki | Kd | Begrenzung |
|---|---:|---:|---:|---|
| Position, je Achse | 1,8 | 0,45 | 2,6 | ±3 m/s² Ausgang |
| Vertikale Beschleunigung, innere Korrektur | 0,6 | 2,0 | 0 | ±5 m/s² |
| Lage | 4 | 0 | 0 | Drehratensoll ±1,5 rad/s |
| Drehrate Roll/Nick | 0,10 | 0,035 | 0,002 | ±0,18 Nm |
| Drehrate Gier | 0,045 | 0,015 | 0,001 | ±0,08 Nm |
| Motor-Drehzahl, je Motor | 0,0016 | 0,003 | 0,00003 | ±0,25 Tastgradkorrektur |
| Servo-Position, je Servo | 35 | 3 | 0,10 | ±8,73 rad/s; zusätzlich lastabhängig |

Einheiten der Verstärkungen ergeben sich aus den jeweiligen SI-Ein-/Ausgängen. D-Anteile verwenden gefilterte Messwertableitung. PID-Integratoren begrenzen Sättigung; bei Verlust der Allokationsreserve wird zurückgeführt. Die Servo-Kommandos werden auf den nominalen Kollektivbereich −2…21° und Zyklik bis 4° projiziert. Tatsächliche bewegte Zustände werden zusätzlich überwacht. Dies ist **keine erneute dynamische CAD-Kollisions- oder Festigkeitsfreigabe**.

Standard-Servoannahmen: Stallmoment **0,6865 Nm (~7 kg·cm)**, unbelastete Geschwindigkeit **8,73 rad/s (~0,12 s/60°)**, Masse **20 g**, Reibwert **0,03**. Stallmoment ist kein zulässiges Dauermoment. Diese Zahlen sind eine Anforderungshypothese, keine zugesicherten Daten von KST oder Savöx. Die Variante mit 60-g-Servos setzt 1,471 Nm an.

Nominelle Drehzahl und Mischer werden vor dem Test aus **nomineller** Polare, Masse und Phase kalibriert. Anschließend wirken abweichende Polare/Phase auf die Pflanze; sie werden nicht zur nachträglichen idealen Mischeranpassung verwendet. Anfang: 1 m Flughöhe, Rotoren bereits hochgelaufen. Start vom Boden und Landen werden nicht geprüft.

## Tests und Bewertung

`Ergebnisse/Testbericht.json` und `Flugbericht.pdf` enthalten die aktuelle 22-Fall-Serie (19 H01-Fälle, 3 P10-Fälle). Die Testreihe umfasst Schweben, Anfangsstörung, Translation/Steigen/Gieren, 3-m/s-Böe mit Momentstoß, 10-%-Drehzahlsprung, Servomasse/Reibung, falsche Phase, blockiertes Servo, Motorausfall, 25 % aerodynamische Abweichung und niedrigen Ladezustand.

„STABIL_IM_MODELL“ verlangt: kein Abbruch, keine Überschreitung der Entwurfs-Kinematikgrenzen, Endpositionsfehler <15 cm und RMS-Positionsfehler der letzten 5 s <15 cm. Das ist ein definiertes Testkriterium, keine Flugtauglichkeitsnorm. Abbruch bei Schwerpunkt unter 18 cm oder Roll/Nick über etwa 74,5°. Fehlerereignis und Kinematiküberschreitungen werden separat aufgezeichnet. Tests dauern 16…28 s; kein Akku-Leerflug und keine Langzeiterwärmung.

Zusätzlich: 12 reproduzierbare kombinierte Annahmen mit abweichender Servomasse, Stallmoment, Reibung, Phase, Totzeit, Geschwindigkeit, Polare und Ladezustand. **Keine empirischen Verteilungen, keine Ausfallwahrscheinlichkeit, keine Zertifizierung.** `Physikpruefung.json` prüft Schwerkraft, Drehimpuls, PID-Sättigung, Stellgrenzen, unabhängige Kinematik und numerische Konvergenz.

Die Flugansicht zeigt seit P10 die native P10-Baugruppe; Blatt-Pitch, Taumelscheiben, Servohebel, Gestänge und Planeten werden aus dem Physikzustand animiert (siehe oben). Anzeige maximal Echtzeit, bei langsamen Geräten langsamer; fester Physikschritt bleibt gleich. Der 3-m/s-Windfall verwendet die zusätzliche Annahme einer effektiven Rumpfwiderstandsfläche.

## Reproduzieren

Aus dem Repository-Stamm, Node ohne zusätzliche Pakete:

```sh
node modell_r04_taumel/simulation/testflug.js
node modell_r04_taumel/simulation/pruefen.js
node modell_r04_taumel/simulation/robustheit.js
```

Optionaler Browser-Integrationstest mit installiertem Playwright und Chromium (keine Laufzeitabhängigkeit des Simulators):

```sh
node modell_r04_taumel/simulation/browser_pruefen.cjs
```

Er prüft WebGL-Initialisierung mit den P10-Bauteilen, Bodenstart bis Schwebeflug, Tastatur- und Zeigerknüppel, ANGLE-Modus, Landung bis Motor aus, Strömungspartikel, Testfall-Wiedergabe, JSON-Download mit CAD-Prüfsummen, mobile Breite und JavaScript-Fehler. WebGL läuft im Test über SwiftShader. Der Test startet einen temporären Loopback-Server und beendet ihn wieder. Falls nötig den Chromium-Pfad über `H01_CHROMIUM` angeben. `Ergebnisse/Browser_Desktop.png` zeigt den geprüften Stand.

CAD und Python-Referenzen nur nach Geometrieänderungen neu importieren:

```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/simulation/cad_import.py
.cfd-tools/venv/bin/python modell_r04_taumel/simulation/kinematik_export.py
```

Offizielle FreeCAD-Version 1.0.2 verwenden; die vorinstallierte 1.0.0 verursachte zuvor Geometrie-Abstürze. Die Referenzexporte benötigen numpy; PDF/Plots matplotlib/reportlab in der bestehenden Tools-venv.

```sh
MPLCONFIGDIR=/workspace/.propboard/cache/matplotlib .cfd-tools/venv/bin/python modell_r04_taumel/simulation/bericht_erstellen.py
python modell_r04_taumel/simulation/paket.py
```

Bei Browsern mit blockiertem `file://`: Repository lokal per HTTP bereitstellen, z. B. `python -m http.server 8000 --bind 127.0.0.1`, dann `/modell_r04_taumel/simulation/H01_Flugsimulator.html` öffnen.

Für belastbare Aussagen fehlen Messungen von Gesamtmasse/Schwerpunkt/Trägheit, stationären Schub-/Drehmomentkennfeldern, Rotordynamik, Reibung über Last/Drehzahl, Servoantwort unter Last, realer Steuerphase, Elektronik-/BEC-Grenzen sowie mechanische Verriegelung und Festigkeit. Die Simulation liefert eine testbare Regelhypothese und zeigt Fehlerfälle, nicht den Beweis, dass der gedruckte Aufbau sicher fliegt.

## Steuerung im Browser

Siehe Abschnitt „Neu in P10“. Tasten wirken nicht in Eingabefeldern. Pause, Fensterwechsel und Ausblenden des Tabs löschen gehaltene Tasten. „Test starten“ spielt einen Fall der Testserie mit dessen eigenen Sollwerten ab; „Start“ beginnt den interaktiven P10-Freiflug vom Boden.
