# Quad R380 D06 – Propeller ergänzt, Einbaukonflikt nachgewiesen

Vier eigene **Dreiblattpropeller mit R380 / Ø760 mm**, zwei CW und zwei CCW, sind im nativen Modell ergänzt. Die MN1330-Motorvorgabe und sämtliche D05-Rahmen-/Fußplattenpositionen bleiben erhalten. **Die Propeller sind beim vollständigen Umlauf nicht freigängig.** Es gibt bestätigte Kollisionen mit den bestehenden Schienen-Endknoten und Strebenanschlüssen. Dieser Entwurf erfüllt die gewünschte Produktionsreife noch nicht.

Zusätzlich ist ein D05-Bezugsfehler korrigiert: Die -14-mm-Normalisierung der alten Motorreferenz war nur in der Master-Platzierung gespeichert, die FreeCAD-App-Links ignorierten. Damit lagen die Motoren in der nativen D05-Datei tatsächlich bei z102..168, während die Vorschau und der beabsichtigte Bezug z88..154 nutzten. D06 bettet dieselbe unveränderte Geometrie mit Identitätsplatzierung ein: Die vier Motoren liegen nun auch nativ bei z88..154. Alle Instanz-Boundingboxen werden gegen die für die Vorschau transformierte Mastergeometrie geprüft. Die Motoren werden dadurch nicht vergrößert/verkleinert; der alte D05-Stand bleibt als Quelle erhalten.

[Interaktive CAD-Ansicht](Mechanik.html) · [Gesamtansicht](Propeller_Gesamt.png) · [Nabendetail](Propellernabe.png) · [Blattinneres](Blattinneres.png) · [Konfliktlage](Rotor_Konflikt.png) · [Bemaßte Rotoranordnung](Rotoranordnung.svg)

[Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D06_Propeller.FCStd) · [STEP-Baugruppe](Ausgabe/QuadR380_D06_Propeller.step) · [CAD-Paket](QuadR380_D06_Detailpaket.zip) · [Stückliste](Ausgabe/Stueckliste.csv)

## Modellierte Teile

- Zwölf profilierte, spanweitig verwundene CFK-Blattkörper als gültige Einzelkörper, keine Platten-/Quaderersatzblätter. Eigenes NACA-Viersteller-Rechenprofil mit 2 % Wölbung bei 40 % Sehne und variablem Dickenverhältnis; verrundete Wurzel, endliche Hinterkante, Begrenzung aller Blattpunkte durch den R380-Zylinder. CW ist die geometrisch exakte Spiegelung von CCW an der XZ-Ebene; die Wölbung bleibt nach oben gerichtet.
- Je Blatt zwei tatsächlich ausgesparte Innenkammern und passende Schaumkerne, massive Wurzel/Spitze sowie durchgehendes CFK-Material zwischen den Kammern und an Vorder-/Hinterkante. Der 1,2-mm-Wert ist ein Profil-Innenversatz in lokaler Sehnennormalrichtung, **kein verifizierter konstanter Hautdicken- oder Laminatnachweis**. Der unabhängige Flächenloft kann lokale Wandstärken verändern.
- Vier dreispeichige Aluminium-Naben mit zentralem Ø12-Durchgang und zwölf Ø5,5-Durchgängen auf PCD40. Das Lochbild ist um 15° gegenüber den Nabenarmen versetzt und dadurch an die tatsächlich eingebauten alten Motorreferenzen ausgerichtet; alle 48 Naben-/Motor-Lochachsen sind im nativen CAD geprüft. Drei Wurzelauflagen pro Nabe; zwölf Klemmplatten mit je zwei Durchgängen. Nabenstärke 9 mm, Wurzel 8 mm, Klemmplatten 6 mm. Die Blattwurzel erhält definierte ebene Auflage-/Klemmflächen bis r134, 2 mm über die Klemmteile hinaus; die verwundene Blattunterseite durchdringt keine Nabenarme.
- Je Blatt zwei Titan-Druckhülsen Ø8/5,5 ×8 in Ø8,2-Wurzelbohrungen und als eigene Geometrie erfasste radiale 0,1-mm-Klebefugen. Insgesamt 24 ISO4762 M5×35, 24 ISO7719 M5 und 48 ISO7089 M5. Normgewinde sind echte nominale Helixkörper; eine Festigkeitsklasse, Vorspannung oder realer Sicherungseffekt wird daraus nicht abgeleitet.
- Nabe liegt auf der alten Motor-Referenzebene z154. Wurzel z163..171; Klemmplatten z171..177. Keine verdeckte Änderung der Motorhöhe oder des Rahmens.

Die drei Blätter sind fest gepitcht; dieses Quad-Modell enthält keine Taumelscheibe. Drehrichtung ist von +Z nach unten auf das Fahrzeug definiert: R1/R3 CCW, R2/R4 CW. Die Drehrichtung ist eine Integrationsvorgabe, noch keine bestätigte Reglerparametrierung. Der Schieber im Viewer ändert nur die CAD-Stellung.

## Masse und Prüfungen

| Umfang | Erfasste Masse |
|---|---:|
| D05 vor Propellern | 31.002 kg |
| Vier Propellerbaugruppen | 3.570 kg |
| D06 Teilbaugruppe | **34.572 kg** |

1052 Instanzen, 49 Teiletypen. CFK-, Schaum-, Kleber- und Titanmassen beruhen auf dokumentierten Entwurfsdichten; Laminat/Harzaufnahme, Lack, Auswuchtmittel und Fertigungstoleranzen sind nicht geschlossen. Die Motoren behalten die XLS-Massenüberschreibung 4×2,75 kg einschließlich Anschlussdraht. Akku, Regler, Versorgungskabelbaum, Rotorschutz, Fahrwerk und Motor-Naben-Schrauben fehlen in dieser Masse.

- Alle nativen Prototypen sind gültige Einzelkörper. STEP-Gesamtbaugruppe zurückgelesen: 1052 Körper; zusätzlich alle zehn eigenen Propeller-Prototypen separat als gültige STEP-Einzelkörper zurückgelesen. Eine Gültigkeitsprüfung jedes einzelnen Körpers der vollständigen STEP-Rückimportbaugruppe wird nicht behauptet.
- Unabhängiger Neuaufbau reproduziert Stückliste, Platzierungen, Teiletypen und Masse bis 0 kg Differenz. D05-Bestandsdaten und native Geometriemetriken sind unverändert; die alten 202 Gewindepaarungen behalten ihre ursprünglichen D05-Prüfberichte und Dateihashes.
- 24 neue nominale Blattwurzel-Gewindepaarungen mit 0,1-mm³-Berichtsgrenze geprüft. Fehlresultate von OCC werden nicht als kollisionsfrei gewertet: Bei einem Common-Fehler wird nur eine gültige Volumensubtraktion als Gegenprüfung akzeptiert; fehlschlagende Phasenkandidaten werden verworfen, fehlschlagende Endprüfungen brechen ab. Bloße Berührung wird vorab über die räumlichen Grenzen erkannt.
- 598 statische Kandidatenpaarungen aller neuen Teile gegen Bestand und neue Nachbarn: **0 Befunde über 0,1 mm³** in der gespeicherten Ausgangsstellung. Die Ausgangsstellung ersetzt keinen Umlaufnachweis.
- Konservative ringförmige Hüllkörper umschließen alle Winkel jeder neuen rotierenden Komponente. **48 Hüllraumkonflikte** im festen Bestand. Einzelne Hüllraumüberschneidungen können zu konservativ sein; separat wurden **20 tatsächliche Blatt-/Festteil-Kollisionen mit Winkel und BRep-Schnittvolumen bestätigt**. Winkelzeugen wurden für Strukturkörper gesucht; ISO-Schrauben-Hüllraumkandidaten bleiben ohne gesonderte Winkelprüfung offen. Das Abtasten im 5°-Raster liefert Kollisionszeugen, niemals eine Kollisionsfreiheit zwischen Stützstellen.
- 52 Fußverstellzustände gegen alle invarianten Rotorhüllen: 0 Befunde. Der feste Streben-/Endknoten-Konflikt besteht unabhängig von der Fußplattenverstellung. Ein Personen-/Schuh-/Kleidungshüllraum ist nicht modelliert.
- 72 gerade Werkzeug-Anfahrkorridore geprüft; bestanden: True. Nur 35-mm-Korridore, einschließlich hohlem Steckschlüssel-Anfahrraum unter den Wurzelmuttern; keine Freigabe für Griffraum, Drehmoment, Anzugsfolge oder alle Rotorstellungen.
- Benachbarte Motorachsen 850 mm, Rotorkreise nominal 90 mm getrennt. Die vier Kreise benötigen 1610×1610 mm; innerhalb 1700 mm bleiben nominal 45 mm je Außenkante. Toleranz, Durchbiegung und vollständiger Schutzbauraum sind daraus noch nicht abgedeckt.

Bestätigte betroffene Bauteilbezeichnungen:

- Carbon Schienenstrebe D04
- Oberer Strebenport -1/-1 A
- Oberer Strebenport -1/-1 B
- Oberer Strebenport -1/-1 Isolierung
- Oberer Strebenport -1/1 A
- Oberer Strebenport -1/1 B
- Oberer Strebenport -1/1 Isolierung
- Oberer Strebenport 1/-1 A
- Oberer Strebenport 1/-1 B
- Oberer Strebenport 1/-1 Isolierung
- Oberer Strebenport 1/1 A
- Oberer Strebenport 1/1 B
- Oberer Strebenport 1/1 Isolierung
- Schienen-Endknoten D04

## Noch offene Verbindung zum MN1330

PCD40/12×M5 stammt aus dem alten Projekt-Zeichnungsbezug, nicht aus einer neu bestätigten Herstellerzeichnung. Die P14-Referenz enthält an dieser Stelle nur Ø5,3-Nennbohrungen mit **4 mm modellierter Tiefe**. Das bestätigt weder die echte nutzbare Gewindetiefe noch Werkstoff oder Auszugslast. Deshalb sind Motor-Naben-Schrauben bewusst **nicht ausgewählt oder eingesetzt**. Eine tragfähige Schraubenlänge und ein Zentrier-/Rundlaufbezug müssen aus OEM-Daten folgen; die Schrauben allein werden nicht als präzise Zentrierung behauptet. Die Baugruppe ist hier noch nicht real montierbar freigegeben. Ebenso offen: Motorlager-Schublast, Lüftung, tatsächliche Stirnkontur und die alte Höhenabweichung 65/66 mm.

## Betriebspunkt und nächster Konstruktionsschritt

Der eigene neue Propeller ist aerodynamisch nicht vermessen oder optimiert. Die frühere angenommene R380-Schwebedrehzahl wird **nicht** auf diese neue Blattgeometrie übertragen. NS52×20-Kennwerte gehören weiter zu einem anderen, viel größeren Propeller. Für den MN1330 bleiben 24S/KV40 und ideal 4032 U/min bei 100,8 V eine Leerlaufreferenz; keine zulässige Betriebsdrehzahl. Ein konkreter Akku/Regler ist damit nicht konstruiert.

Bei 100 kg Person plus 34.572 kg erfasster Teilbaugruppe beträgt die ideale Schwebe-Untergrenze außerhalb des Bodeneffekts bereits **22.75 kW Wellenleistung insgesamt**, ohne Profil-, Drall- oder elektrische Verluste und noch ohne Akku/Regler. Die vier 3,4-kW-Angaben mit 180-s-Zeitbezug liefern im bedingten Wellenleistungs-Rechenfall 13,6 kW. Höhere, zeitlich unbestätigte Prüfstandswerte belegen keine Dauerleistung. Daraus folgt weiterhin kein nachgewiesener personentragender Schwebebetrieb.

Der vorhandene Rahmen muss an den nachgewiesenen Konfliktstellen konstruktiv überarbeitet werden, bevor dieser Rotorumlauf freigegeben werden kann. Eine größere Höhenverschiebung oder ein verlängertes Nabensystem wäre eine neue Tragwerks-/Lagerlastentscheidung und wird in diesem Stand nicht als fertige Lösung dargestellt. Anschließend sind Motor-Naben-Anschluss, CFK-Laminat und Wurzelverbindung, Auswuchten, Schwingung/Festigkeit und ein gemessener Schub-/Leistungs-/Temperaturbetriebspunkt zu schließen.

## Reproduktion und Quellen

`normteile_erstellen.py` nutzt die unveränderte gepinnte D05-Fasteners-Methode für die zusätzliche M5×35-Geometrie. Danach `propeller_einbauen.py`, `basis_pruefen.py`, `rotor_pruefen.py`, `montage_pruefen.py`, `betrieb_pruefen.py`, `ableiten.py`, `export_motorbezug_pruefen.py`, `viewer_daten_erstellen.py`, `viewer_pruefen.cjs`, `neuaufbau_pruefen.py`, `dokumentieren.py`, `paket_erstellen.py`. `ableiten.py` darf unabhängig von der Rotorprüfung laufen; die Viewer-Daten werden erst danach mit übereinstimmenden CAD-Hashes verbunden. Für einen unabhängigen Neubau `D06_OUTPUT_DIR=/tmp/quad-d06-fresh-check /usr/bin/python3 quad_r380_d06/propeller_einbauen.py` verwenden.

Die Geometriegleichungen und sämtliche Maße sind eigener Entwurf in [geometrie.py](geometrie.py) und [parameter.json](parameter.json); es wird kein Herstellerprodukt oder Original-OEM-STEP vorgetäuscht. Die Massen beruhen auf CAD-Volumen und dokumentierten Dichteannahmen. Die vorhandenen Motor-XLS-/STEP-Quellen bleiben im eingebundenen D05-Quellenordner erhalten. [Blattstationen](Ausgabe/Blattstationen.csv) · [Prüfprotokoll](Ausgabe/Rotor_Pruefung.json) · [Betriebsgrenzen](Ausgabe/Betriebsgrenzen.json) · [Erhaltener D05-Bestand](Ausgabe/D05_Basis_Pruefung.json).
