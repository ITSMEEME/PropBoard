# MN1330 KV40 – bereitgestellte Daten und Zeitbezug

Die vom Nutzer hochgeladene [XLS-Datei](<Quellen/basicParameter_MN1330 KV40.xls>) und die zusätzlich übermittelte [NS52×20-Prüftabelle](Quellen/MN1330_NS52x20_Nutzertabelle.csv) sind als Originaldaten erhalten. Die XLS ist ein HTML-Export für Excel. Der Import liest ausschließlich Tabellenwerte; Dokumentinhalte werden nicht als Arbeitsanweisungen ausgeführt. Ein ursprünglicher Herstellerlink wurde nicht mitgeliefert.

## Übernommene Angaben

| Angabe | Quelle / Wert |
|---|---|
| Motor | MN1330 KV40 |
| Masse inklusive Anschlussdraht | 2.750 g je Motor, XLS |
| Versorgung | 24S laut XLS; Prüftabelle 91,90–92,07 V |
| Abmessungen | XLS Ø150 × 65 mm; frühere Anschlusszeichnung Ø150 × 66 mm |
| Maximalstrom | 177 A laut XLS; höchster Tabellenwert 177,03 A |
| Leistung mit Zeitangabe | **3.400 W für 180 s**, Leistungsseite nicht ausdrücklich bezeichnet |
| Höchster elektrischer Tabellenwert | 16.270 W bei 2.744/min, Haltedauer unbekannt |
| Höchstes tabelliertes Drehmoment | 46,25 Nm bei 2.744/min |
| Daraus berechnete Wellenleistung | rund 13,29 kW am höchsten Tabellenpunkt |
| Prüfflugschraube | NS52×20 |
| Temperaturhinweis | 117 °C Motor / 25 °C Umgebung; keine eindeutige Einzelpunkt-/Zeitzuordnung |
| Empfohlener Regler | M200A24S laut XLS |

Der Nutzer hat ausdrücklich den Zusatz **„180 s“** hervorgehoben. Die 3,4-kW-Angabe wird deshalb als zeitgebundene Angabe und **nicht als Dauerleistung** geführt. Die höheren Tabellenwerte haben keinen angegebenen Zeitbezug. Unterschiedliche Belastungsdauern können die unterschiedlichen Leistungen erklären; ein zwingender Datenwiderspruch ist daraus nicht ableitbar. **16,27 kW werden insbesondere nicht als für 180 s zulässig ausgegeben.** Eine bestätigte Dauerleistung bleibt offen.

Die alten pauschalen 2,0 kg pro Motor sind durch die dokumentierten 2,75 kg ersetzt. Damit steigt die erfasste CAD-Masse eines Rotorpaars um 1,50 kg. Die größere 66-mm-Bauraumreferenz aus der Anschlusszeichnung bleibt bis zur Klärung der tatsächlichen Montagebezüge erhalten. Sie ist keine Behauptung, dass die 65-mm-Angabe falsch sei.

## Aussagegrenzen der Prüftabelle

Alle 19 Punkte wurden mit ihren Einheiten übernommen. `U × I` stimmt innerhalb der Tabellenrundung mit der elektrischen Leistung überein. Aus `P_Welle = Q × 2πn/60` folgt für diese Prüflinie ein rechnerischer Motorwirkungsgrad von etwa 0,82. Dieser Wirkungsgrad ist im P14-Rechenfall eine **Annahme aus einer anderen Propellerlast**, keine bestätigte Effizienz bei unserem Sonderrotor.

Die Spalte g/W ist Schub pro elektrischer Leistung; sie ist kein thermodynamischer Motorwirkungsgrad. Die NS52×20-Zugkräfte werden nicht als Schub unseres mehrblättrigen CFK-Rotors verwendet. Dessen Schub und Lastmoment werden weiterhin aus seiner eigenen Geometrie berechnet.

Die Kurve `Q(n)` entstand bei verändertem Gas und festem NS52×20-Propeller. Sie ist eine **Propellerlastlinie**, keine vollständige Motor-Drehmomentgrenze über der Drehzahl. Ein Prüfpunkt bei 2.093/min mit etwa 25 Nm bedeutet weder, dass der Motor dort maximal 25 Nm kann, noch, dass er die für P14 benötigten etwa 98 Nm liefern darf. Die maximal dokumentierten 46,25 Nm und 16,27 kW begrenzen lediglich den großzügigen Vergleichsrahmen. Eine echte Strom-/Spannungs-/Temperatur-/Drehzahlgrenzkennlinie wird daraus nicht erfunden.

117 °C ist ein beobachteter Temperaturhinweis, kein freigegebener Grenzwert. Die Material-Temperaturklassen für Wicklung/Magnete aus der XLS ergeben ebenfalls keine zugesicherte Dauerbetriebstemperatur des kompletten Motors.

## Drei explizite Rechenfälle

1. **XLS / 180 s, voreingestellt:** 3.400 W pro Motor werden vorsichtig als elektrische Decke interpretiert; die Leistungsseite ist im Export nicht eindeutig. Die Momentdecke liegt höchstens beim maximal dokumentierten Prüfmoment. Nach 180 s endet die numerische Flugrechnung mit einem Hinweis auf fehlende Dauerdaten. Das definiert kein reales Motor-Abschaltkonzept und behauptet keine thermisch nachgewiesene 180-s-Belastbarkeit unter beliebigen Bedingungen.
2. **Prüfmaxima, Haltedauer unbekannt:** 16.270 W elektrisch und 46,25 Nm je Motor bilden eine obere rechteckige Rechenbegrenzung. Das ist keine zugesicherte Kennlinie und insbesondere keine 180-s- oder Dauerfreigabe. Ein thermisches Zeitmodell fehlt.
3. **Freie Annahmen:** Moment und elektrische Leistung sind explizit veränderbar. Diese Ergebnisse sind nicht als durch die vorliegenden Daten gedeckter Hardwarebetrieb ausgewiesen.

Die Drehzahlregelung ist idealisiert und nutzt die berechnete aerodynamische Last als Vorsteuerung. Strom-/ESC-Reglerdynamik, tatsächliche Effizienz, Motorverlustwärme und Kühlung fehlen. Moment- und Leistungsgrenzen greifen beim Hochlauf; die Simulation erhöht die verfügbare Leistung nicht automatisch für einen Schwebeflug. Bei zurückgenommenem Drehzahlziel laufen die Wellen unter aerodynamischem Widerstand aus; eine unbestätigte Rekuperation wird nicht vorausgesetzt.

Der theoretische P14-Schwebebedarf für die Standardgeometrie liegt mit 100 kg Nutzlast weiterhin bei ungefähr **43 kW Wellenleistung und 98 Nm je Motor**. Das liegt über dem Bereich der bereitgestellten Prüfpunkte. Schon die gesamte maximale dokumentierte elektrische Aufnahme beider Motoren von 32,54 kW ist kleiner als dieser berechnete Wellenbedarf. Das ist ein klarer Machbarkeitskonflikt für diese Konfiguration innerhalb der vorliegenden Betriebsdaten; es ist keine vollständige Vermessung aller denkbaren Motorbetriebspunkte.

[Maschinenlesbare Original-/Rechenwerte](Motor_Daten.json) · [Importprogramm](import_motor_daten.py) · [aktuelles Simulationsergebnis](Ausgabe/Simulation_Pruefung.json)
