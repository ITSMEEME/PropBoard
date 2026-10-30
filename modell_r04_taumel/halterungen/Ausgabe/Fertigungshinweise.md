# Halterungen H01 – Montage- und Fertigungshinweise

Stand 30.10.2026. Maße in mm. Geprüft wurde der gespeicherte Geometrieentwurf mit Referenzhüllen. Keine Fertigungs- oder Betriebsfreigabe.

## Aufbau

**Oben:** H01-Endadapter statt der bisherigen oberen Kappe. Vier H02-Abstandshalter mit 12 mm stellen die angenommene ESC-PCB-Unterseite auf z112. Vier H03-Abstandshalter mit 14,4 mm zwischen den Leiterplatten stellen die FC-PCB-Unterseite auf z128. Das M3-Lochbild ist 30,5 × 30,5. Der USB-Zugang liegt auf +x; das Kabel-/Lötfeld des ESC ist auf −y freigehalten. Die maximale Hüllreservation umfasst jede Verteilung der angegebenen Bauteilhöhe auf beide PCB-Seiten: 5,6 mm Mindestfreiraum zum Endadapter und 4,7 mm zwischen den Komponentenreservierungen.

**Unten:** H01-Endadapter, H04-Anschlussplatte, vier Aluminium-Distanzrohre H06 mit **62 mm**, H05-Akkuwanne. Die Wanne liegt bei z−169…−166; das 2-mm-Bodenpolster bei z−166…−164. Der nominelle Akku reicht von z−164 bis z−112; bis zur Anschlussplatte bleiben **8 mm**. Die Distanzrohre sitzen auf der Wannenoberseite und berühren die Unterseite der Anschlussplatte – keine frei schwebenden Pfosten.

Der Innenraum ist 82 × 41 gegenüber 78 × 37 Akkuaußenmaß. 1-mm-Seiten-/Endpolster können eingelegt werden; dann verbleiben nominell 2 mm gesamtes Längs-/Breitenspiel. Keine Verschraubung oder harte Klemmung gegen die Zellflächen. Zwei 20-mm-Gurte durch die vier 22 × 3-mm-Schlitze führen. Beide kurzen Wannenenden besitzen Kabelausschnitte; XT60- und JST-XHR-Handhabungsräume sind reserviert. Die Steckverbinderhüllen sind keine aus Herstellerdaten rekonstruierte Geometrie.

## Kraftschlüssige und formschlüssige Befestigung

Die bisher lediglich gesteckten F01-Kappen reichen für die neue Last nicht aus. H01 sieht deshalb je Rohrende einen **durchgehenden M2-Querbolzen** durch beide Rohrwände und die Einsteckhülse vor. Das Rohr benötigt dazu **D2,2-Bohrungen bei 3 und 189 mm**, ab derselben Stirn gemessen. Die Achsen sind parallel und liegen entlang x. Beide Wände gemeinsam in einer Bohrlehre bearbeiten, entgraten und die fluchtende Hülse zuordnen. Gewinde, Muttern und Köpfe dürfen die Gleitbewegungen am Rohr nicht berühren.

Die Bohrung lässt nur **1,9 mm Material zwischen Bohrungsrand und Rohrstirn**. Lokale Lochleibung/Ausreißen und die gedruckte Hülse sind zu prüfen; die geometrische Sicherung ist kein Festigkeitsnachweis. Das Rohr ist ein neues Nacharbeitsbauteil H07. Nicht das ungebohrte F01-Rohr als formschlüssig gesichert betrachten.

Die neue H01-Kappe besitzt das FC-/ESC-M3-Lochbild. Die bisherigen zwei M5-Prüfstandsbohrungen der F01-Kappe sind nicht übernommen; ein bestehender Prüfstandsadapter muss für diesen Montagestand angepasst werden. Der F01-Stand bleibt separat erhalten.

## Hardware, ergänzend zur CSV

| Position | Anzahl | Entwurfsangabe |
|---|---:|---|
| M2-Querbolzen | 2 | M2 × 35 mit Scheiben und gesicherter Mutter; tatsächliche Kopf-/Mutternkontur prüfen |
| Stack-Zugschrauben | 4 | M3 × 40 als Längenansatz; mit realen Gummidämpfern, Scheiben und Muttern abgleichen |
| H04 an unterem Endadapter | 4 | M3 × 12 mit Scheiben/gesicherter Mutter; Bauteilzugang bei demontiertem Akkurahmen |
| Akku-Zugschrauben | 4 | M3 × 80; Köpfe/Muttern nicht gegen Zellen, durch Metall-Distanzrohre führen |
| Aluminium-Distanzrohre | 4 | H06: D6/D3,4 × 62, plan/entgratet; Legierung offen |
| Gurte | 2 | 20 mm breit, etwa 300 mm Ausgangslänge, Schließbereich mit realem Pack prüfen |
| Bodenpolster | 1 | 80 × 39 × 2, weich, elektrisch isolierend, nicht abrasiv |
| optionale Seiten-/Endpolster | nach Bedarf | 1 mm, Kabel-/Balancerzugang nicht einklemmen |

Die Nennlängen wurden mit Schraubenschäften dargestellt. Vollständige Köpfe, Muttern, Scheiben, Gewinde und PCB-Gummidämpfer sind nicht geometrisch nachgebildet. Endgültige Schraubenlängen und Gewindeeingriffe müssen mit den realen Teilen geprüft werden. Die Abbildung nennt keine PCB-Loch-/Dämpferdurchmesser; die Komponentenreservierung spart an den Befestigungspunkten D8 aus, **das sind keine behaupteten D8-PCB-Bohrungen**.

## Druck und Nacharbeit

PETG oder vergleichbarer elektrisch isolierender Werkstoff ohne leitfähige Füllung ist die Entwurfsannahme. Für Träger unmittelbar an Elektronik kein unisoliertes CF-Material verwenden. Temperatur-, Kriech- und Festigkeitswerte müssen zur gewählten Sorte passen. Offene Distanzhalter sorgen für Luftzugang; ESC-Temperatur unter Last messen.

H01 im STL mit Plattenaußenseite auf dem Bett, Hülse nach oben. Kleine Querbohrung gegebenenfalls nachbohren. H02/H03 stehend mit Achse z; H04 und H05 flach mit Boden auf dem Bett. Alle fünf Druckteilvarianten haben positiven z-Bezug und passen geometrisch in 200 × 148 × 150. H06/H07 sind Aluminium-Zuschnitt-/Bohrteile und werden nicht als Druck-STL freigegeben.

Keine Pauschalwerte für Füllung, Perimeter oder Anzugsmoment festgelegt. Der 65-%-Füllansatz in der Massenschätzung ist kein geprüfter Slicerauftrag.

## Prüfungen und Grenzen

Sieben Einzelteilmodelle wurden als gültige Festkörper erzeugt und aus STEP zurückgelesen. Fünf Druck-STL werden auf Geschlossenheit und positives Volumen geprüft. Native Dateien, drei TechDraw-Ansichten und drei assoziative Hüllmaße werden wieder geöffnet. Die Änderung des Adapters von 70 auf 72 und zurück prüft Neuberechnung und Maßbezüge.

Die Gesamtbaugruppe prüft die gespeicherte F01-Schwebestellung gegen neue Halter und die freizuhaltenden Bereiche. Die zusätzlichen Halter liegen axial außerhalb der rotierenden Geometrie; ein vollständiger erneuter F01-Bewegungsraumlauf wurde dafür nicht ausgeführt. Die hypothetischen Servoarme aus der Mechanikrechnung sind nicht als produktverifizierte Servos eingebaut. Die ursprünglichen offenen Pitchlager-, Servo- und Gestängeanschlüsse sind dadurch nicht behoben.

Der Akku-Lastansatz ist 274 g × 5 g = etwa **13,44 N**. Das ist ein vorläufiger Screening-Lastfall, kein validiertes Stoß-/Fluglastkollektiv. Gurte, Halter, Rohrendbohrung und Hülsen unter mindestens diesem festgelegten Lastfall mit geeignetem Zuschlag prüfen; eine Freigabe erfordert konkrete Werkstoffe und Messungen. Nicht aus der Gurtbreite auf die Verschlussfestigkeit schließen.

Die neue nominale Massenschätzung beträgt etwa **1,218 kg bei den weiterhin angenommenen sechs 9-g-Servos**. 20-g-Servos ergeben etwa 1,284 kg, 60-g-Servos etwa 1,524 kg. PCB-Masse, Verkabelung, Schraubenköpfe, Muttern, Gurte und Pads enthalten ausdrücklich ausgewiesene Schätzansätze. Tatsächlichen Schwerpunkt wiegen; die neue Akkuanordnung verlagert ihn entlang z. Die Lage des IMU zur Fahrzeugmitte muss bei der späteren Regelung berücksichtigt werden.

Reale Servo-Befestigungen, BEC und Schutzteile sind noch nicht vollständig im genannten Massenbudget definiert/enthalten. Die Masse und Schwerpunktlage der fertig bestückten Baugruppe sind zu wiegen.
