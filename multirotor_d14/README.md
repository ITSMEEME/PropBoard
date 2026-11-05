# Multirotor D14 – Bauweisen, Dreiecksverbinder und Motorträger

[3D-Ansicht](Projekt.html) · [Parameter](parameter.json) · [Auslegung aller Konfigurationen](Ausgabe/Auslegung.json) · [Kollisions- und Massenprüfung](Ausgabe/Pruefung.json) · [native FreeCAD/STEP-Dateien](Ausgabe/nativ/)

D14 führt die **Bauweise** als neue Modellvariable ein. Zusammen mit Propeller (10 HEP-S-Größen) und Auslegervariante (V1–V3) ergeben sich 4 × 10 × 3 = **120 Konfigurationen**, die alle als Volumenkörper gebaut und geprüft werden.

| Bauweise | Rotorpositionen | Motoren | Auslegerpaare / Dreiecksverbinder | Zentralrahmen | Motorradius |
|---|---:|---:|---:|---|---|
| Multirotor 4-Rotor (`QUAD`) | 4 | 4 | 2 | Quadrat | D10/D13-Abstände unverändert |
| Multirotor 6-Rotor (`HEXA`) | 6 | 6 | 3 | Sechseck | berechnet |
| Multirotor 8-Rotor (`OKTO`) | 8 | 8 | 4 | Achteck | berechnet |
| Multirotor Coaxial (`KOAX`, X8) | 4 | 8 | 2 | Quadrat | wie Quad |

Der Zentralrahmen ist ein regelmäßiges CFK-Prisma mit der D04–D13-Seitenlänge von 205 mm und Rohrebenen bei z = ±110 mm. Beim Quad entspricht das dem bisherigen Würfel. Hexa und Okto erhalten ein Sechs- bzw. Achteck gleicher Seitenlänge. Die Motorradien für Hexa/Okto folgen aus dem größeren Wert von zwei Bedingungen: mindestens 0,10 · D Blattspitzenabstand und mindestens 20 mm Grundrissabstand zwischen Rotorkreis und Rahmen/Verbinder.

## Paarweise Ausleger und Dreiecksverbinder

Die Ausleger von **Motor 1 und Motor 2** (allgemein M2k−1 und M2k) laufen V-förmig zu einem gemeinsamen **Dreiecksverbinder** in der Mitte einer Rahmenseite (Skizze Anhang 3). Hexa und Okto nutzen jede zweite Rahmenseite.

**Warum der Verbinder die Last in die Rahmenecken leitet:** Eine einfache Klemme in Seitenmitte würde das 20/17-Rahmenrohr quer auf Biegung belasten. Überschlägig: Beim Quad mit 42 Zoll ergeben 160 kg × Lastfaktor 3 rund 6 kN Querkraft in Seitenmitte und damit etwa 900 MPa Biegespannung im Rohr. Der Verbinder hat deshalb je Rahmenebene zwei Dreiecksplatten (5 mm, mit Erleichterungsausschnitt). Sie bilden in der Draufsicht das Dreieck „Arbeitspunkt – linke Ecke – rechte Ecke“ und sind mit M8-Passschrauben an Laschen der beiden Eckknoten verschraubt. Damit liegen die Kräfte in den Ebenen der Rahmenringe und fließen über die Eckknoten in Ringrohre und Pfosten. Die Rahmenrohre selbst werden vom Verbinder nicht berührt.

Weitere Merkmale:

- **Zentrische Systemlinien:** Bei V2/V3 laufen alle Rohrachsen eines Auslegers in der Senkrechtebene so, dass sie sich auf der Motorachse schneiden (z = 50 mm). Der Rotorschub erzeugt damit im Gelenkstabmodell nur Längskräfte (Obergurt Druck, Untergurt Zug); in den CFK-Rohren entsteht kein planmäßiges Biegemoment. Wurzelseitig liegen die Gurte in den Rahmenebenen z = ±110 mm, also in der Ebene der Dreiecksplatten.
- **Hülsen:** Bohrung = Rohr-Ø + 2 × 0,3 mm, darin eine 0,25-mm-Isolierhülse gegen galvanische Korrosion zwischen CFK und Aluminium. Jede Hülse hat einen 22 mm langen starren Teil, an den Platten bzw. Stege anbinden, und einen 28 mm langen Klemmteil mit 1-mm-Schlitz, Klemmnase und 2 × M4. Steckt man ein Rohr bis zum Anschlag, bleibt je Ende 0,25 mm Stirnspalt (Zuschnitt = Systemmaß − 0,5 mm).
- **Kabelführung:** Hinter jedem Rohrende liegt eine Kabelkammer mit Rohr-Innendurchmesser. Motorseitig führt ein seitliches Kabelfenster nach außen; wurzelseitig öffnen sich die Kammern zum Arbeitspunkt.
- **Werkstoff/Fertigung:** EN AW-7075 T6 als Frästeil oder AlSi10Mg im SLM-Verfahren. Nicht schweißen.

## Motorträger (Anhang 4)

Die Rohre enden in gestapelten Klemmhülsen. Ein 12 mm starkes Knotenblech in der Auslegerebene verbindet Hülsen, Streben (Ø16 mm, bei V1 Ø24 mm), Nabe (Ø34 mm) und den Motorflansch (Ø82 × 8 mm, 4 × M6 auf Lochkreis 50 mm, Zentrierbohrung Ø16 mm) zu einem Formteil. Seine Kontur ist die konvexe Hülle dieser Elemente; zwischen den Gurtstreben bleibt ein Erleichterungsloch. Die Streben setzen die Gurtachsen bis zum Systempunkt auf der Motorachse fort.

Beim **Koax** trägt dieselbe Nabe zusätzlich einen unteren Flansch für den hängenden Motor. Die untere Rotorebene wird je Konfiguration so tief gelegt, dass zwischen der ±25-mm-Rotorhülle und allen Rohren im Rotorkreis mindestens 20 mm bleiben.

Der Kragabstand c<sub>e</sub> (Rohrende bis Motorachse) ist eine Folge der zentrischen Geometrie. Benachbarte Hülsen brauchen 32 mm Mittenabstand, und die Gurte laufen erst auf der Motorachse zusammen. Bei **V3** (drei Rohre wie in Anhang 4) wird der Motorträger daher etwa doppelt so lang wie bei **V2**. **V2 ist die leichtere und kompaktere Auslegung; V3 entspricht der Bildvorlage und hat ein statisch überzähliges Mittelrohr.**

## Fußschlitten, Landefüße, Reglerhalter und Propeller

Alle Baugruppen werden für jede der 120 Konfigurationen neu erzeugt und mit dem ganzen Fahrzeug auf Überschneidung geprüft. Ihre Lasten gehen in die **Eckknoten** des Zentralrahmens, nicht in die Mitte von Rahmenrohren und nicht zwischen die Knoten eines Auslegers. Beides war in D12/D13 jeweils ein Schwachpunkt.

### Fußschlitten

- **Übernommen aus D12/D13:** Verstellbacken, Isolierung, Fußplatten, Indexierleisten mit Indexierschrauben sowie M5-Normteile. Die Originalkörper liegen unter `Quellen/Fussschlitten/`.
- **Neu:** Je Schienenende sitzt ein **Schienenbock**. Er hat Hülsen für Schiene, Querrohr und Strebe sowie eine Lasche mit M4 in die gekürzte Indexierleiste.
- Über den Rahmenecken trägt je Schiene ein geteilter **Schienensattel** mit kurzer Stütze. Streben und Stützen enden in Zusatzhülsen der vier oberen Eckknoten, die der Schiene am nächsten liegen. Die alten Strebensättel in der Mitte des Rahmenrohrs entfallen.
- Die Schienenebene liegt 6 mm höher als in D13 (z = 226 mm). So bleiben über jeder Rotorhülle mindestens 20 mm frei.
- **Anpassung je Konfiguration:** Die Schienenlänge (bis ±380 mm) wird so gewählt, dass Böcke und Streben außerhalb der Rotorkreise bleiben. Daraus folgt der mögliche Bereich der Fußmitte.
- Ist kein Platz für Bock mit Strebe (Rotoren zu nah oder Eckknoten zu weit außen), wechselt der Aufbau automatisch zu „Endbock ohne Strebe“. Die Schiene kragt dann über den Sattel aus.

### Landefüße (Eckfüße)

- Vorgabe: Das Fußgestell darf nicht tiefer reichen als der Zentralwürfel.
- Jeder untere Eckknoten (4 bei Quad/Koax, 6 bei Hexa, 8 bei Okto) trägt einen angeformten Alu-Fußstutzen (Ø30 mm) mit Fußplatte (Ø64 × 8 mm) und eine TPU-Sohle (Ø70 × 8 mm, 4 × M5 versenkt).
- **Bodenlage:** z = −154 mm. Das sind 10 mm unter dem tiefsten Rahmenteil, den M8-Köpfen der unteren Dreiecksplatten bei −144 mm.
- **Lastpfad:** Die Landelast geht senkrecht über Stutzen und Eckknoten in den Rahmenpfosten. Ausleger und Rahmenrohre werden nicht auf Biegung belastet.
- **Folge:** Die Standbreite entspricht dem Rahmen; die Kippkante liegt 102,5 / 177,5 / 247,5 mm von der Mitte (Quad/Koax, Hexa, Okto). Kippsicherheit beim Landen und Abstellen mit stehender Person ist damit nicht gegeben und muss gesondert gelöst werden, etwa mit klappbaren Stützen oder einer Bodenstation.
- Beim Koax liegen die unteren Propeller dicht über dem Boden. Das wird je Größe geprüft.

### Propeller

- Die zweiblättrigen Bildreferenz-Propeller aus D13 werden unverändert übernommen (STEP aus `quad_r380_d13/Ausgabe/Propeller_STEP/`).
- Die Nabenunterseite sitzt auf der Motoroberseite (z = 154 mm). Ungerade Motornummern drehen CCW, gerade CW, wie in D13.
- Beim Koax ist der untere Propeller an der Unterseite des hängenden Motors gespiegelt eingebaut und läuft gegen.
- Die Rotorhüllen für alle Freiraum- und Kollisionsprüfungen kommen jetzt aus der realen axialen Ausdehnung des jeweiligen Propellers (z. B. 42″: 136–183 mm) statt aus einer pauschalen Annahme.

### Reglerhalter (V200A 24S)

- Der Regler sitzt seitlich am Ausleger direkt vor den Klemmhülsen des Motorträgers, damit das 250-mm-Phasenkabel den Motor erreicht.
- Die Halterplatte ist an Ober- und Untergurt befestigt, über geteilte Schellen mit Isolierlage und 2 × M4. Der Regler hält mit 4 × M3 auf dem Lochbild 126 × 66 mm.
- Beim Koax gibt es zwei Regler je Ausleger, einen je Seite; die beiden Halterhälften klemmen das Rohr gemeinsam.
- Passt der Regler liegend nicht zwischen Motorträger und Verbinder (kurze Ausleger), wird er hochkant eingebaut.
- Der Regler ist ein Bauraum (146 × 74 × 39,5 mm) ohne erfundene Gehäusedetails.

**Ergebnisse Ausrüstung** (Standardpropeller 42″, V2; alle Werte in [Auslegung.json](Ausgabe/Auslegung.json)):

| Konfiguration | Schiene / Lagerung | Fußmitte möglich | Landefüße / Kippkante | Regler je Ausleger, Abstand Reglerende–Motorachse | Ausrüstung ohne Regler |
|---|---|---|---|---|---:|
| QUAD V2 42″ | ±380 mm, Bock mit Strebe | ±152 … ±287 mm | 4 / 102,5 mm | 1 × liegend, 188 mm | 6,45 kg |
| HEXA V2 42″ | ±380 mm, Bock mit Strebe | ±228 … ±287 mm | 6 / 177,5 mm | 1 × liegend, 217 mm | 6,98 kg |
| OKTO V2 42″ | ±390 mm, Endbock ohne Strebe | ±298 … ±298 mm | 8 / 247,5 mm | 1 × liegend, 257 mm | 7,13 kg |
| KOAX V2 42″ | ±380 mm, Bock mit Strebe | ±152 … ±287 mm | 4 / 102,5 mm | 2 × liegend, 188 mm | 7,18 kg |

- **Kollisionen:** Alle 120 Konfigurationen sind einschließlich Fußschlitten, Eckfüßen, Reglern, Propeller-Rotorhüllen und aller Schrauben kollisionsfrei. Insgesamt 77.220 Volumenpaare wurden geprüft, mit einer gemeinsamen Geometriesignatur.
- **Fußschlitten:** 84 Konfigurationen haben Schienenböcke mit Strebe; 36 nutzen automatisch den Endbock ohne Strebe. Das sind Hexa 18″/22″, weil die Rotoren zu nah sind, und alle Okto: Die oberen Eckknoten liegen dort bei x = ±247,5 mm, und innerhalb der D13-Schienenlänge von ±380 mm ist neben dem Sattel kein Platz mehr für Bock und Strebe. Die Schiene kragt dann über den Sattel aus.
  - Bei Hexa und Okto liegen die oberen Eckknoten weiter außen (x = ±177,5 bzw. ±247,5 mm). Die Fußmitte beginnt dort erst bei ±227,5 bzw. ±297,5 mm; der D13-Nennstand ±200 mm ist nur bei Quad/Koax möglich.
  - Bei Hexa 18″/22″ liegt der Endbock zudem nur etwa 14 mm über der Rotorhülle; das ist als offen markiert.
- **Regler:** Bei 28 Konfigurationen liegt das motorseitige Reglerende weiter als 250 mm (Phasenkabel V200A) von der Motorachse (27 × V3, 1 × V2 Okto 42″). Dort sind Motorleitungs- bzw. Phasenverlängerungen nötig.
  - Kurze Ausleger bekommen den Regler hochkant: HEXA_HEP_S_18_6p7_V1, HEXA_HEP_S_18_6p7_V2, HEXA_HEP_S_18_6p7_V3, HEXA_HEP_S_22_7p2_V3, OKTO_HEP_S_18_6p7_V3.
  - Bei HEXA 18″ V3 reicht der Platz auch hochkant nicht ganz; markiert.
- **Landefüße:** Der Boden liegt bei z = −154 mm, die Pfostenbelastung bei 3 g auf zwei Füßen ist unkritisch (Knickausnutzung 0,01).
  - Kritisch ist die Kippsicherheit wegen der kleinen Standfläche.
  - Bei Koax 42″ liegt die untere Propellerhülle nur 14 mm über dem Boden (Grenze 20 mm); markiert.
- **Massen:** Die Ausrüstung wiegt etwa 6,5–7,2 kg ohne Regler. Den größten Anteil haben die übernommenen D12-Aluteile: Fußplatten 140 × 300 × 6 mm, Indexierleisten und Verstellbacken. Die Regler zählen separat mit ihrer Katalogmasse von 748 g je Stück.


## Varianten

| Variante | Rohre | Wurzel-z [mm] | Tragverhalten |
|---|---|---|---|
| V1 | 1 × 35/32 | 0 | Kragarm auf Biegung, nicht zentrisch |
| V2 | 2 × 20/17 | +110 / −110 | zentrisches Zweigurt-Fachwerk |
| V3 | 3 × 20/17 | +110 / 0 / −110 | zentrisch, Mittelrohr überzählig (Anhang 4) |

## Ergebnisse

Gesamtlauf: **alle 120 Konfigurationen sind kollisionsfrei**, geprüft wurden 77.220 Volumenpaare mit einer Toleranz von 0,001 mm³. Verglichen wurden Verbinder, Eckknoten, Motorträger, Isolierhülsen, Schrauben, CFK-Rohre, Rahmenrohre, Motorhüllen, reale Propeller-Rotorhüllen sowie Fußschlitten, Eckfüße und Regler am ganzen Fahrzeug. Alle Knoten sind gültige Einzelvolumenkörper. [Prüfprotokoll](Ausgabe/Pruefung.json)

Standardpropeller HEP-S 42×16 (Massen = CAD-Volumen × Dichte; nur Struktur, ohne Motoren, Regler, Akku, Plattform):

| Konfiguration | Motorradius | c<sub>e</sub> | Verbinder | Motorträger | Struktur gesamt (Stand vor Eckfüßen) | max. Knickausnutzung Gurt |
|---|---:|---:|---:|---:|---:|---:|
| QUAD V2 | 884 mm | 117 mm | 1004 g | 527 g | 7,8 kg | 0,68 |
| QUAD V3 | 884 mm | 233 mm | 1163 g | 905 g | 9,9 kg | 0,42 |
| HEXA V2 | 1175 mm | 146 mm | 1002 g | 573 g | 12,3 kg | 0,98 |
| HEXA V3 | 1175 mm | 291 mm | 1161 g | 1025 g | 15,9 kg | 0,63 |
| OKTO V2 | 1535 mm | 186 mm | 1033 g | 637 g | 17,6 kg | **1,66** |
| OKTO V3 | 1535 mm | 372 mm | 1202 g | 1192 g | 23,3 kg | **1,08** |
| KOAX V2 | 884 mm | 117 mm | 1004 g | 1027 g | 9,9 kg | 0,68 |
| KOAX V3 | 884 mm | 233 mm | 1163 g | 1532 g | 12,5 kg | 0,42 |

Ein oberer Eckknoten wiegt 270 g, ein unterer mit Eckfuß 362 g; je Rahmenecke gibt es einen oberen und einen unteren Knoten.

Ergebnisse des Screenings:

- **V1 (Einrohr-Kragarm)** fällt in 36 von 40 Kombinationen durch: bei Quad und Koax bei allen Propellergrößen, bei Hexa und Okto ab 26 Zoll. Biegung statt Fachwerk ist für 160 kg nicht tragfähig.
- **Okto 42″** fällt auch mit V2/V3 im Gurtknicken durch: Der Ausleger ist dort 1,27 m lang. Hier sind größere Rohre oder eine Zwischenabstützung nötig.
- Bei Hexa/Okto bestimmt der Blattspitzenabstand (0,1 · D) den Radius; bei Hexa 18″ ist der Rahmenfreiraum maßgebend.

Native Dateien für alle 4 Bauweisen × 3 Varianten am Standardpropeller (einschließlich Fußschlitten, Landegestell und Regler) liegen in [Ausgabe/nativ](Ausgabe/nativ/): FCStd mit Bauteilen und App::Link-Instanzen sowie STEP. Jede andere Konfiguration lässt sich mit `--konfig … --nativ` nativ erzeugen. Bilder: [Gesamt Quad](Ausgabe/Gesamt_QUAD_42_V2.png), [Dreiecksverbinder Hexa](Ausgabe/Dreiecksverbinder_HEXA_30_V2.png), [Fußschlitten Okto](Ausgabe/Fussschlitten_OKTO_30_V2.png), [Koax seitlich](Ausgabe/Koax_42_V3_seitlich.png), [Regler](Ausgabe/Regler_QUAD_42_V2.png).

## Grenzen

**Dies ist eine Geometrie- und Screening-Revision, keine Festigkeits- oder Flugfreigabe.**

- Das Stabwerk-Screening ist ein ebenes Gelenkstabmodell für Schweben × Lastfaktor 3 bei 160 kg. Es nimmt eine reine CFK-Dehnsteifigkeit an und rechnet Euler-Knicken mit K = 1 über die freie Länge zwischen den Hülsenmündungen. Nicht enthalten sind:
  - Klemm- und Klebeverbindungen,
  - Knotenbleche, Laschen und Eckknoten (dafür sind FE-Analyse und Versuch nötig),
  - seitliche und Torsionslasten aus Rotormoment und Manövern,
  - Landestoß sowie Ermüdung.
- Die Ringrohre und Pfosten des Zentralrahmens werden über die Eckknoten belastet und sind nicht nachgewiesen. Die Reibschlüssigkeit der Klemmhülsen gegen Axialschub (Rohr rutscht aus der Hülse) ist ebenfalls nicht nachgewiesen.
- Die Landefüße sitzen nur unter dem Rahmen; die Standfläche ist entsprechend klein und die Kippsicherheit nicht nachgewiesen. Der Landestoß ist nur als statischer 3-g-Lastfall auf zwei Füßen in den Rahmenpfosten gerechnet, ohne Sohlenkennlinie.
- Die Propeller sind Bildreferenzen aus D13, keine OEM-Geometrie. Masse, Nabenbefestigung und Blattverformung sind nicht freigegeben.
- Das Fußschlitten-Screening ist ein Einfeldträger zwischen Sattel und Bock mit 100 kg × 3 auf zwei Füßen. Klemmung von Backen und Sätteln sowie die Indexierung sind nicht nachgewiesen.
- Regler: Kühlung, Steckerlage, Phasen- und DC-Leitungsführung sind nicht modelliert. Die D13-Kabelzuordnung (Netze je Rohr) muss für V1–V3 neu geplant werden; Kabelfenster und Biegeradien sind nicht nachgewiesen.
- Motor und Rotoren sind Bauraumhüllen (MN1330-Nennhülle Ø150 × 66 mm, Rotor ±25 mm axial), keine OEM-Konturen. Die Massen sind CAD-Volumen × angenommene Dichte.
- Werkzeugzugang, Toleranzketten, Verrundungen, Oberflächenschutz und Fertigungszeichnungen fehlen noch.

## Reproduktion

```bash
cd multirotor_d14
python3 auslegung.py                                   # Geometrie, Freiräume, Screening (ohne FreeCAD)
FC=~/Programme/squashfs-root/usr                        # FreeCAD 1.0.2 AppImage, entpackt
LD_LIBRARY_PATH=$FC/lib $FC/bin/python bauen.py --standard-nativ          # alle 120 + FCStd/STEP am Standardpropeller
LD_LIBRARY_PATH=$FC/lib $FC/bin/python bauen.py --konfig HEXA_HEP_S_30_10p5_V2 --nativ   # einzelne Konfiguration nativ
```

`bauen.py` speichert Zwischenkörper als BREP im ignorierten `Cache/`; die Signatur aus `knoten.py`, `auslegung.py` und `parameter.json` macht den Cache ungültig, sobald sich eine dieser Dateien ändert. Die Ansicht `Projekt.html` lädt die Konfigurationen einzeln aus `Ausgabe/viewer/` und funktioniert auch direkt per Datei-URL ohne Server. Der Link-Parameter `#b=HEXA&p=HEP_S_30_10p5&v=V2&a=verbinder` öffnet eine bestimmte Konfiguration und Ansicht.
