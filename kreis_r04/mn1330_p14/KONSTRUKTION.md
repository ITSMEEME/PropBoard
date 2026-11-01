# Konstruktion und Lastpfade

## Zentrum und Antrieb

Zwei MN1330 liegen Rücken an Rücken an einem gemeinsamen Aluminium-Zentralblock. Die Statoranschlüsse zeigen zur Mitte, die Rotorflansche nach außen. Damit bleiben die Motoren zentriert, obwohl der gegebene Motor keinen durchgehenden Kanal hat. Die obere und untere Rotoreinheit besitzen jeweils eine eigene Hauptwelle und Lagerung. Gleiche, entgegengesetzte Drehzahl allein garantiert keinen Drehmomentausgleich; dazu muss auch das aerodynamische Moment beider Ebenen passen.

Vier gemeinsame M6-Zuganker verbinden die beiden Statorplatten und Hauptlagerjoche. Die Druckhülsen sitzen im Zentrum. Der Motor überträgt das Antriebsmoment über den gezeichneten 12×M5-Anschluss auf eine 60/50,4-mm-Hohlwelle. Zwei separate 7212B-Lager pro Rotor leiten den Rotorschub in das feste Zentrum; die internen Motorlager werden nicht als alleinige Schublager angesetzt.

Die Nutzerzeichnung ist Grundlage für Ø150 × 66 mm, Rotorlochkreis Ø40 mit 12×M5 und Statorlochkreis Ø50 mit 4×M6. Die später bereitgestellte XLS nennt Ø150 × 65 mm sowie 2,75 kg inklusive Draht. Die Masse ist übernommen; der größere 66-mm-Bauraum bleibt bis zur Bestätigung der Montagebezüge erhalten. Gewindetiefen sind nicht sicher ableitbar: 4 mm Rotor- und 6 mm Statoreingriff bleiben Annahmen. Der gezeichnete Motor ist ein Anschluss-/Bauraummodell, kein vollständiges OEM-Innenleben. 65/66-mm-Bezug und ein möglicher Abstandsausgleich müssen vor Fertigung geklärt werden.

## Innenbefestigung der Flügel

Ein monolithischer CNC-Wurzelstern aus 7075-T6 vereint die radialen Lageraufnahmen, die zentrale Nabe und die Phasenmitnehmer. Eine geschlossene Lastplatte unter der Pitch-Ebene führt Kräfte um die Öffnungen der Pitchhebel herum. Ihre Größe folgt den inneren Lagersitzen; sie ist kein Rahmen an den Flügelspitzen. Durchführungen für die Pitchgestänge sind freigestellt.

Je Flügel liegen zwei7205B-Lager35mm auseinander. Eine25/14-mm-Alu-Pitchwelle mit integralem12-mm-Wurzelflansch undØ32-Mandrel nimmt Biegung und Fliehkraft auf. Ein innerer D-Sitz überträgt Pitchmoment zum Hebel. Der äußere CFK-Flansch wird durch die Integralplatte und eine Außenplatte mit vier von außen erreichbarenM6×25 aufØ64 mechanisch gefasst. Separate innere Klemmplatte, loser Wurzeleinsatz und verdeckte M8-Endschraube entfallen.

Die Flügel beginnen bei `root_r_mm + 82 mm` und reichen standardmäßig bis r = 710 mm. Lagerkreis und CFK-Länge stehen je Blattzahl in `Ausgabe/Abgeleitet.json` bzw. `Massenvarianten.json`. Der metallische Wurzelbereich liegt innen; es gibt weder Spitzenlager noch einen Außenring. Das CFK-Modell enthält eine geschlossene Schale, einen Kastenspar, eine verdickte Wurzel und den gefassten Flansch. Das konkrete Laminat und die Fertigung sind mit einem CFK-Dienstleister auszulegen, siehe [CFK-RFQ](CFK_RFQ.md).

Die zunehmende Blattzahl verschiebt den Lagerkreis nach außen. Die Ableitung berücksichtigt 38-mm-Gehäusehüllen einschließlich Deckelschrauben, 5 mm Konstruktionsabstand und die Phasenarme. Daraus folgen echte Änderungen an Sparlänge, Gestängen, Wurzelstern, Masse und Trägheit.

## Gegenlauf und Blatt-Handigkeit

Die untere Motoreinheit wird starr um 180° um Y gedreht. Beide lokalen Rotorphasen laufen negativ; dadurch sind die globalen Drehrichtungen entgegengesetzt. Die obere CFK-Klemmung ist gegenüber ihrem Pitchhebel um −24° indexiert. Die obere Integralwelle A13U besitzt einen entsprechend um−24° indexierten Schraubenkreis. So steht in der Neutralstellung bei beiden Ebenen die Vorderkante über der Hinterkante.

Bei einem lokalen Hebelwinkel θ gilt im vereinfachten Aeromodell oben `Pitch = 24° − θ`, unten `Pitch = θ`. Deshalb wird das obere Kollektiv umgekehrt angesteuert. Die Animation bildet diesen mechanischen Zusammenhang ab. Reale Motordrehrichtung, elektrische Kommutierung und Servo-Vorzeichen müssen am unbemannten Prüfstand bestätigt werden.

## Pitchbetätigung

Drei ROBOTIS PH54-200-S500-R je Rotor verschieben/neigen den stationären Taumelträger. Eine sphärische Gleitaufnahme und ein dünnes 61832-Rotationslager trennen die stehende von der rotierenden Seite. Die Taumelscheibe nutzt keine drei Spindeln, Riemen oder zusätzliche Statorschere.

Eine geführte untere Gabelanlenkung und zwei sphärische Beine bestimmen die stationäre Phase. Die geringe Phasenänderung bei Neigung wird mitgelöst. Zwei gegenüberliegende einfache Gleitstifte halten die rotierende Phase und verteilen die Last symmetrisch. Die Stifte laufen in radialen Langlöchern; sie sollen keine zusätzliche axiale Führung erzwingen.

Jeder 28-mm-Servohebel sitzt auf einer mit zwei 6002-Lagern abgestützten 15-mm-Aluwelle. Eine 5×5×8-mm-Alu-Passfeder verbindet den Hebel mit der Welle; nur die Kupplungsreserve nutzt einen D-Sitz. Die runden Lagerzapfen bleiben erhalten. Schulter, Distanzring und zwei M15×1-Sondermuttern bilden den axialen Aufbau. Die Lager tragen die Gestängequerkraft. Der Anschluss an das tatsächliche OEM-Horn bleibt offen.

Die 22 Gestänge pro Rotorpaar bestehen aus getrennten M6-RH/LH-Gelenkaugen, SW10-Einstellhülse und Kontermuttern. 44 Gabelgelenke enthalten GE8E-Nenngeometrien (8×16×8, Außenringbreite5), Schulter-/DIN472-Sicherung, Distanzhülsen und Alu-Kopfbolzen mit Scheibe/Splint. Je Kopf führt ein DIN1494-Buchsengelenk die stationäre Phase. Die 42 übrigen Gelenke sind sphärisch. Lagerprofile und Tragzahlen sind vor Bestellung zu qualifizieren. Die Animation transportiert auch die Orientierung der Augen und Ringe.

Der Hauptflansch ist abnehmbar; sechs M6 von oben greifen12mm direkt in Aluminium. Die äußeren Blattlagersitze sind nach außen offen und mit abnehmbaren Deckeln versehen. Kugelpfanne und PTFE-Liner sind geteilt, das 61832 besitzt einen abnehmbaren Deckel. Montagefolge und geprüfte Wege: [MONTAGE.md](MONTAGE.md).

## Werkstoffe und Normteile

| Baugruppe | Auswahl / Status |
|---|---|
| CNC-Nabe, Wellen, Klemmungen, Schraubenkonturen | Aluminium 7075-T6, Festigkeits-/Ermüdungsnachweise offen |
| Druckhülsen | Aluminium 6082-T6 |
| Hauptlager | 7212B, 60 × 110 × 22 mm, Paarvorspannung/Lieferausführung offen |
| Pitchlager | 7205B, 25 × 52 × 15 mm, Lieferausführung offen |
| Taumellager | 61832, 160 × 200 × 20 mm, Lieferdaten offen |
| Externe Servolager | 6002, 15 × 32 × 9 mm, Lieferdaten offen |
| Sphärische Gestängelager | GE8E, 8 × 16 × 8 mm, Außenringbreite5; Lieferprofil/Tragzahlen offen |
| Geführtes Gestängebein | DIN1494-8×10×8 und PTFE-Anlaufscheiben |
| Verbindungsmittel | ISO4762-/ISO4032-Konturfamilien und Sondermuttern; keine übernommene Stahl-Festigkeitsklasse |
| Gleitfolien/-pfanne | PTFE-Vorentwurf, Verschleiß/Kriechen/Reibung offen |
| CFK | Geometrie für Dienstleister, kein freigegebenes Laminat |

Strukturelle metallische Verbindungsteile werden als Aluminium modelliert. Lager, OEM-Innenteile und Norm-Federsicherungen behalten ihren erforderlichen Werkstoff. Insbesondere DIN472-Ringe und ISO1234-Splinte sind Stahl-Sicherungsteile. Gewinde sind Kernkonturen ohne vollständige Flanken; Innensechskante sind ausgeführt. Passungen, Anzüge, Alu-Festigkeit und Vorspannung bleiben zu qualifizieren.

Eine galvanische Trennung zwischen CFK und Aluminium gehört in die fertige Wurzelverbindung. Die Glas-/Isolierlage, Klebschicht und die daraus folgenden Passungen sind noch nicht freigegeben.
