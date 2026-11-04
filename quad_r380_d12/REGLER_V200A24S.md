# V200A 24S – übernommene Zeichnungs- und Leitungsdaten

Der Nutzer hat die zuvor bereitgestellte Zeichnung dem **V200A 24S** zugeordnet. Die Außenmaße passen zur bisherigen Einbaureferenz. Diese Zuordnung ist damit im Projekt geklärt; eine unabhängige Prüfung am Originaldatenblatt beziehungsweise OEM-STEP ist nicht erfolgt.

[Erfasste Originalangaben](Quellen/Regler/V200A24S_Nutzerdaten.txt) · [normalisierte Daten](Quellen/Regler/V200A24S.json) · [Einbau-/Leitungsbewertung](Ausgabe/V200A24S_Integration.json)

| Merkmal | Übernommener Wert |
| --- | --- |
| Modell | V200A 24S |
| Gehäuse, Länge × Breite × Höhe | 146 × 74 × 39,5 mm |
| Masse einschließlich Leitungen | 748 g je Regler; vier Einheiten 2,992 kg |
| Betrieb | 12–24S, maximal 105 V |
| Dauerausgangsstrom | 100 A |
| Kurzzeitige Stromangabe | 200 A für **unter** 10 s; genaue Stromdefinition/Prüfbedingungen fehlen |
| Versorgungskabel | Rot/schwarz, Silikon, 10 AWG, je 1.200 mm; isolierter Außendurchmesser nicht angegeben |
| Ausgangskabel | Orange, Silikon, 10 AWG, 250 mm; drei Phasen aus Motor-/Zeichnungskontext; Außendurchmesser nicht angegeben |
| Signalkabel | Geschirmt, schwarz, Ø4,2 mm, fünfadrig, 500 mm, Angabe JP-3P×2 |
| Als „Encoder“ bezeichnete Leitung | Geschirmt, fünfadrig, 24 AWG, 460 mm, „M6 Flugzeugkopf“ |
| Kommunikation | PWM/CAN |
| BEC | Keines |
| Gasbereich | 1040–1940; Einheit in der übermittelten Tabelle nicht enthalten, vermutlich µs |
| Aktualisierungsfrequenz | 50–500 Hz |
| Standby | Höchstens 50 mA bei 100 V, entsprechend höchstens 5 W bei 100 V |
| Ansprechgeschwindigkeit | Übermittelter Eintrag endet ohne Wert |

Das vorhandene Lochraster 126 × 66 mm mit vier M3 und gezeichneten 4 mm Gewindetiefe stammt aus der früheren Zeichnung. Drehmoment, Gewindetoleranzen und Einbaurichtung sind weiterhin zu bestätigen. Die Farben werden nicht in eine erfundene Pinbelegung umgesetzt. Die Bezeichnung M6 belegt keine sechs Pins. Ob „Encoder“ tatsächlich einen Motorpositionssensor oder einen Programmier-/Zubehöranschluss bezeichnet, muss das Handbuch klären.

## Was dadurch im Projekt geschlossen ist

Modellname, Zuordnung zur Maßzeichnung, nominelle Außenmaße, Katalogmasse einschließlich Leitungen sowie die genannten Kabeldaten und Betriebsgrenzen sind erfasst. Der Viewer zeigt Modell und separate Katalogmasse. Die Hochkantplanung bleibt ein 146 × 39,5 × 74 mm großer Zeichnungsbauraum; tatsächliche Gehäusedetails und Ports sind weiterhin nicht als OEM-Oberflächen modelliert.

Die native CAD-Geometrie bleibt unverändert. Die Leiter-/Signalgeometrien aus D10 sind noch Planungsgeometrien, insbesondere 35 mm²/Ø12-mm-DC-Leitungen und ein Ø4,0-mm-Signalersatz. Das Eintragen eines echten Kabelwertes bedeutet nicht, dass diese alten Geometrien bereits durch den konfektionierten OEM-Kabelsatz ersetzt wurden. Der Datenabgleich protokolliert identische Viewer-Meshes/Instanzen vor und nach dem Katalogeintrag.

## Konkrete Folgen für die Innenverkabelung

Die neue Ø4,2-mm-Signalleitung wurde rechnerisch auf dem vorhandenen Planungsweg untersucht, ohne die CAD-Geometrie zu verändern:

- **V2/V3:** Im Ø17-mm-Rohr verbleiben mit dem vorhandenen Liner nominal 16,2 mm lichte Weite. Die alte Ø12-mm-Plusleitung sitzt bei −2 mm und der Signalersatz bei +6 mm. Mit dem echten Signaldurchmesser beträgt der Achsabstand 8 mm, die Radiensumme aber 8,1 mm: **0,1 mm nominelle Überschneidung**. Das Signalkabel berührt zudem den Liner nominal. Eine kleine Achsverschiebung allein kann höchstens Tangentialkontakt ohne Toleranzreserve herstellen. Dies betrifft 20 der 50 Variantenstellungen.
- **V1/V4/V5:** Der neue Signaldurchmesser bleibt auf der jeweiligen nominellen Signalachse ohne diese Überschneidung. Das ist keine Freigabe des ganzen Kabelbaums: Encoder-Außendurchmesser, echte DC-Kabel, Stecker, Austritte, Mindestbiegeradien, Toleranzen und Befestigungen fehlen.
- **10 AWG** entspricht nominell etwa **5,26 mm² Kupfer**, nicht 35 mm². Der isolierte Außendurchmesser folgt daraus nicht. Ob die OEM-Leitung gemeinsam mit der Signalleitung genügend Platz hat, muss mit dem echten Kabel-OD geprüft werden. Für V2/V3 wären beim vereinfachten Zweikreispacken und je 0,5 mm Abstand zu Liner und Nachbarkabel höchstens **10,5 mm DC-Kabel-OD** möglich; dies berücksichtigt noch keinen dritten Kabelsatz oder Steckverbinder.
- Die OEM-Signalleitung ist 500 mm lang. In 25 der 50 vorhandenen Planungsstellungen ist bereits das alte gerade Signalstück länger. Im 42-Zoll-Stand sind es etwa 672–673 mm, vor zusätzlichen Anschlussbögen und der Rückführung zum seitlichen Regler. Die neue Kabelführung benötigt deshalb eine dokumentierte Verlängerung oder geänderte Elektronik-/Reglerposition. Die Herstellergrenzen für PWM/CAN-Verlängerungen und Schirmführung fehlen.

Die vorhandenen bestandenen D10/D12-Geometrieprüfungen gelten für ihre gespeicherten Planungsgeometrien. Sie werden ausdrücklich nicht als Nachweis der Passung des neuen OEM-Kabelsatzes ausgegeben. Die neue Bewertung steht separat in V200A24S_Integration.json.

## Elektrische Grenzen und Masse

**100 A Dauer-Ausgangsstrom ist die maßgebliche angegebene Dauergrenze.** Der Modellname und die 200-A-Angabe erlauben keine 200 A Dauerbetrieb. Ausgangsstrom, Phasen-RMS-/Spitzenstrom und Batteriegleichstrom sind ohne Herstellerdefinition nicht gleichzusetzen. Der MN1330-/Propeller-Arbeitspunkt ist daher mit dieser Angabe noch nicht positiv nachgewiesen.

24S mit 4,2 V je Zelle ergibt 100,8 V Ladeschluss. Zum angegebenen absoluten Maximalwert 105 V verbleiben rechnerisch nur 4,2 V; zulässige Spannungsspitzen, DC-Verlängerung, Leitungsinduktivität und vorgeschriebene Stützkondensatoren sind noch offen. Daraus folgt keine Freigabe für mehr als 24S.

Als ausdrücklich angenommener Rechenpunkt: Zwei 1,2-m-10-AWG-Kupferleitungen ergeben bei 20 °C etwa 7,865 mΩ. **Falls** 100 A Batteriegleichstrom fließen, wären es etwa 0,786 V Spannungsabfall und 78,6 W Verlust in diesem Paar. Das ist keine Behauptung, dass die Ausgangsstromangabe 100 A DC-Eingangsstrom bedeutet. Litzenaufbau, Temperatur, Isolierung, Kontaktverluste und Wärmeabfuhr im Carbonrohr fehlen für die thermische Auslegung.

Ohne BEC muss die Avionik separat passend versorgt werden. Vier Regler ergeben bei 100 V bis zu 20 W aus der angegebenen Standby-Obergrenze. Diese Werte ersetzen keine Messung am gewählten Betriebspunkt.

Vier Katalogeinheiten wiegen zusammen **2,992 kg einschließlich ihrer Leitungen**. Diese Masse wird getrennt von der bisherigen CAD-Teilmasse geführt: Beim Ersetzen alter Planungsleitungen durch OEM-Leitungen können sonst Leitungsanteile doppelt gezählt werden. Die Strukturstudie bleibt bei ihrer bisherigen **160-kg-Gesamtmassenannahme**; diese wird nicht automatisch um weitere 2,992 kg erhöht, da sie bereits eine Annahme für das komplette Fahrzeug ist. Ein gewogener und vollständig zugeordneter Massen-/Schwerpunktbericht fehlt weiterhin.

## Was für den fertigen mechanischen Kabelbaum noch fehlt

1. Originalgehäuse-CAD oder bemaßte Details mit Kühllamellen, Befestigungsseite und erlaubter Einbaulage.
2. Koordinaten und Richtungen der Kabelausgänge, Steckerhüllen, Zugentlastungen sowie Mindestbiegeradien.
3. Isolierter Außendurchmesser der 10-AWG-Leitungen und des Encoder-/Zubehörkabels.
4. Pinbelegung, Signalpegel, CAN-Abschluss-/Adressierungsangaben, Schirmanbindung und Funktion der Encoder-Leitung.
5. Dauerstrom-Prüfbedingungen und Stromdefinition, Kühlvorgaben, zulässige Verlängerungen und notwendige DC-Kondensatoren.
6. Vollständige Ansprechgeschwindigkeitsangabe und Befestigungsdrehmomente.

Die neuen Reglerdaten ändern die ermittelten strukturellen Nachweisdefizite nicht in eine positive Freigabe. Die Untersuchung zu Armrohren, Klemmung, Klebung und Landestoß bleibt maßgeblich: [Festigkeitsbericht](Ausgabe/Festigkeit/BERICHT.md).

## Reproduktion

`Quellen/Regler/V200A24S_Nutzerdaten.txt` hält den Transkriptstand fest; `V200A24S.json` die normalisierten Werte und offene Felder. `reglerdaten.py` aktualisiert die aktuelle Montage-Metadatei und annotiert einen bereits zum nativen CAD passenden Viewer. Es baut keine neuen Kabelkörper. Nach einem echten CAD-Neuaufbau zuerst Geometrie/Viewer passend erzeugen und dann diesen Datenabgleich erneut ausführen. `bauen.py` und `viewer_export.py` berücksichtigen die Modellzuordnung künftig ebenfalls.
