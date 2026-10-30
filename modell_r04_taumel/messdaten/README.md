# Belegte Servodaten, Lastrechnung und noch ausstehende Messwerte

`Servodaten_Nutzer.json` trennt Werte aus den von dir gelieferten Bildern/der Spezifikationstabelle von fehlenden Angaben. Die unabhängige Herstellerabfrage blieb durch die Cloud-Domainfreigabe gesperrt. Es werden keine nicht eingesehenen Herstellerdaten behauptet.

Savöx SB-2271SG(+) gemäß Zeichnung: **69 g, 6,0–7,4 V, 15/20 kg·cm und 0,08/0,06 s pro 60° bei 6,0/7,4 V, Brushless, Stahlgetriebe, 25T**, Gehäuse 40,3×20,2×38,7 mm. Der Typ unterscheidet sich vom früheren Kandidaten SB-2270SG. Der Plus-Suffix und die Zuordnung der Tabelle sollten am tatsächlichen Artikel bestätigt werden. **8,4 V sind durch diese Angabe nicht gedeckt.** Die Lastbedingungen der Geschwindigkeitsangabe sind nicht genannt; „Dynamic Torque“ wird weder als verifiziertes Stallmoment noch als Dauerlast behandelt.

KST X15-755X: Abmessungen aus deiner Zeichnung; **760 µs auf dem Gehäuse**. Drehmoment, Geschwindigkeit, Gewicht, Spannung und Frame-/Stellbereich fehlen. Er ist nur als geometrische Vergleichsoption verfügbar, nicht für die Flugfälle ausgewählt.

## Berechnete Anforderungen

Mit sechs 69-g-Servos steigt das bisherige Budget auf **1,577676 kg**. Zusätzliche Halter und BEC fehlen. `Servolasten_Savox.json` berechnet 728 Gestängezustände mit dem vollständigen Acht-Blatt-/Drei-Servo-Jacobi-Modell je Rotor, CAD-Blattträgheit, Fliehkraft-Torsion, zyklischer Pitch-Trägheit, Viertelsehnen-Hebelarm des mittleren Auftriebs und angenommener Gleitreibung der Haltenut. Keine günstige Vorzeichenkompensation wird vorausgesetzt.

Im bisherigen vereinfachten TW2-Aeromodell ergibt sich je Servo **einschließlich Faktor 2**:

| angenommener effektiver Reibwert | benötigtes Moment |
|---:|---:|
| 0 | 5,06 kg·cm |
| 0,03 | 7,43 kg·cm |
| 0,10 | 12,97 kg·cm |
| 0,20 | 20,89 kg·cm |

20 kg·cm bei 7,4 V liegen bei µ=0,2 bereits knapp unter dieser Modellanforderung. Bei µ=0,1 ist der Quotient angegebener Wert/Anforderung etwa 1,54. Diese Quotienten sind Lastscreenings, **keine bestätigte Dauerlastreserve**. In diesem Modell liegt die Reibungsgrenze zur 20-kg·cm-Angabe bei ungefähr µ=0,19; das ist kein ermittelter Materialreibwert. Preload, Losbrechen, Lagerreibung, vollständige zyklische Luftlasten/CM, Resonanz, Dauerlast und Temperatur fehlen. Ergebnisse mit CAD-XFOIL-Betriebspunkten sind separat ausgewiesen, einschließlich Ersatzmodellanteilen.

Die Flugsimulation verwendet die angegebenen Werte lediglich als hypothetische Moment-/Geschwindigkeitsgrenzen mit angenommener Lastkennlinie und Totzeit. Die interne PID-Parametrierung eines Kaufservos lässt sich aus diesen Daten nicht bestimmen. Das neue Massenträgheitsprofil nutzt die tatsächlichen nominalen CAD-Hüllen, nimmt aber homogene interne Massenverteilung an.

## Was noch unbekannt ist

Ein **realer Reibwert** und eine **experimentell validierte Aerodynamik** sind bislang nicht vorhanden. Es wurden keine Hardwaremessungen durchgeführt. Die leeren CSV-Vorlagen werden vom Auswerter ausdrücklich zurückgewiesen; es werden keine Ersatzmesswerte erfunden. Stromaufnahme, PWM-Frequenz/Pulsbereich, 3,3-V-Eingangsverträglichkeit, Stallstrom, zulässige Dauerlast, tatsächliche Stellzeit unter Last und echte Servoachsen-/Horn-/Befestigungstoleranzen bleiben offen. Aus 25T allein folgt kein fertiges Verzahnungsprofil.

## Reibung messen und auswerten

`Reibung_Vorlage.csv`: Das reale Blattwurzel-/Nut-/Stiftpaar am ruhenden Prüfstand mit axialer Vorlast belasten. Vorlasten z. B. über den berechneten Fliehkraftbereich bis zum relevanten Betriebspunkt staffeln und positive/negative Pitchbewegung bei mehreren Geschwindigkeiten aufnehmen. Die normale Kontaktgeometrie muss der montierten Wurzel entsprechen; der gefittete µ-Wert ist **effektiv für dieses Gelenk**, kein universeller PA-CF-Kennwert.

Erfasst werden Vorlast, Pitchgeschwindigkeit, Antriebsmoment sowie separat bekannte Trägheits- und Luftmomentanteile. Losbrechmessungen mit `breakaway=1` werden von der Gleitreibung getrennt. Modell:

`T_friction = mu_eff × F_axial × 0,0048 m + T_preload + b × abs(pitch_speed)`.

Mindestens neun Gleitwerte bei unabhängig veränderten Vorlasten **und** Geschwindigkeiten werden benötigt. Der Auswerter prüft Identifizierbarkeit, Vorzeichen und nichtnegative Parameter. Langsame Handmessungen allein qualifizieren die bei Zyklik umlaufend auftretenden schnellen Pitchbewegungen/Temperaturen nicht.

## Servodynamik messen

`Servo_Vorlage.csv`: Kommandowinkel, unabhängig gemessenen Ausgangswinkel, Spannung direkt am Servo, Lastmoment und Strom mit Zeitstempel aufzeichnen. Kleine, ungesättigte Schritte bei mehreren Lasten und bei 6,0/7,4 V trennen. Ein effektives Modell erster Ordnung mit Totzeit wird angepasst; Messauflösung begrenzt die zeitliche Genauigkeit. Es liefert **keine internen Servo-PID-Werte**, keinen Stallstrom aus normalen Stellbewegungen und keine Dauerlastfreigabe. Größere gesättigte Schritte separat auf Stellgeschwindigkeit, Spiel, Spannungseinbruch und Erwärmung prüfen.

## Aerodynamik messen

`Aero_Vorlage.csv`: Drehzahl/Pitch beider Ebenen, Gesamtschub und **Summe der beiden einzeln gemessenen positiven Rotordrehmomente** aufnehmen; das ausgeglichene Netto-Giermoment nahe Null ist dafür ungeeignet. Kraftmess-Nullpunkt und Unsicherheit erfassen. Vergleichswerte müssen aus demselben Modell/Betriebspunkt stammen. Die Auswertung liefert lokale Schub-/Drehmomentkorrekturen, keine eindeutige vollständige Profilpolare aus nur einer Gesamtlastmessung. Drehmomentverluste von Lagern/Getriebe müssen getrennt behandelt werden. Nur innerhalb des gemessenen Kennfelds interpolieren.

```sh
.cfd-tools/venv/bin/python modell_r04_taumel/messdaten/identifizieren.py friction echte_reibung.csv --out reibung_identifiziert.json
.cfd-tools/venv/bin/python modell_r04_taumel/messdaten/identifizieren.py servo echte_servomessung.csv --out servo_identifiziert.json
.cfd-tools/venv/bin/python modell_r04_taumel/messdaten/identifizieren.py aero echte_pruefstandswerte.csv --out aero_identifiziert.json
```

`pruefen.py` kontrolliert die Auswerter mit **synthetischen Daten ausschließlich im Arbeitsspeicher**. `Identifikation_Pruefung.json` enthält Testresultate, keine echten Messdaten. Gefittete Werte werden nicht automatisch als freigegebene Flugparameter installiert.
