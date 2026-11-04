# Quad D12 – kombinierte Reglerhalter und Landefüße

Vier kombinierte Halter ersetzen die D11-Regleraufnahmen. Jede Einheit besitzt zwei kurze CFK-Druckstützen und eine gemeinsame schmale Aufsetzsohle. Der Reglerbauraum ist seitlich hochkant angeordnet. Der Entwurf ist ein mechanisch modellierter Leichtbau-Aufbau, ohne qualifizierten Landestoß-, Klemm- oder Klebenachweis.

[3D-Ansicht](Projekt.html) · [Landefuß Detail](Ausgabe/Landefuss_42_V4.png) · [Native FreeCAD-Baugruppe](Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd) · [Geometrische Prüfung](Ausgabe/Reglerhalter_Pruefung.json) · [Last-/Massenscreening](Ausgabe/Landelast_Screening.json) · [Vorbemessung mit Zuschnitt](Ausgabe/Landelast_Kurzbericht.md)

## Aktuelle Festigkeitsuntersuchung

[Rechenbericht als PDF](Ausgabe/Festigkeit/D12_Festigkeit_Landestoss.pdf) · [vollständiger Bericht](Ausgabe/Festigkeit/BERICHT.md) · [maschinelles Ergebnis](Ausgabe/Festigkeit/Ergebnis.json)

Die erweiterte Untersuchung ist abgeschlossen: 150 räumliche FE-Hauptbedingungen, 600 proportional skalierte lineare Lastkombinationen, 425 eindeutige vertikale Landestoßsimulationen und 36 verfeinerte Klebfugen-/Stirnkontaktfälle. Das Ergebnis ist **kein positiver Tragfähigkeitsnachweis**. Für V4/42 Zoll bei 160 kg und 3 g auf zwei Füßen ergibt das lineare Referenzmodell etwa 580 MPa Arm-Längsspannungsbedarf und 38,5 mm Weg. Die untere Wurzelklemmung benötigt etwa 9,32 kN Zughaltevermögen; das angenommene Zwei-M4-8.8-/µ0,2-Modell mit gleichmäßiger Ringpressung liefert nur 4,48 kN. Klebfittings tragen zudem erhebliche Biegemomente. Die früheren reinen Axial-/Mittelwert-Screens ersetzen diese Untersuchung nicht.

Material-/Reib-/Sohlenkennwerte bleiben Annahmen. Die numerische Implementierung wurde durch analytische Vergleiche sowie Netz-/Zeitschritt- und Energieprüfungen verifiziert; reale Fahrzeug-/Werkstoffversuche wurden nicht durchgeführt. Der Bericht kennzeichnet Extrapolationen und Abbruchgrenzen. Die native D12-CAD-Datei und ihr Hash bleiben unverändert.

## V200A-24S-Daten ergänzt

Die Zeichnung ist durch die Nutzerangaben dem **V200A 24S** zugeordnet: 146 × 74 × 39,5 mm, 748 g einschließlich Leitungen, 100 A Dauer-Ausgangsstrom und 200 A für unter 10 s. Vier Einheiten ergeben 2,992 kg Katalogmasse einschließlich Leitungen; diese wird wegen der alten Kabel-Planungsgeometrien separat geführt. Der echte Signalkabel-OD beträgt 4,2 statt 4,0 mm. Auf den alten V2/V3-Achsen entsteht dadurch eine nominelle Überschneidung; die Verkabelung ist anzupassen. Gehäuse-/Portdetails und die übrigen Kabelaußendurchmesser fehlen weiterhin.

[Reglerdaten und Folgen für Einbau/Verkabelung](REGLER_V200A24S.md) · [Datenabgleich](Ausgabe/V200A24S_Integration.json)

## Aufbau und Lastpfad

**Sohle → ausgefräster Aluminiumfuß → untere Klebefittings → zwei axiale CFK-Stützen → obere Fittings mit Rohrschellen → unterstes Armrohr.** Der geplante Landestoß läuft an Reglergehäuse und dessen M3-Befestigung vorbei. Die seitlichen dünnen Montageschienen tragen den Regler, keine rechnerische Landelast.

- Zwei senkrechte CFK-Rohre Ø20/17 mm je Fuß verwenden denselben nominellen Rohrartikel CBU 2017 1005 TG wie der Rahmen. Die Länge folgt Rohrvariante, Armlänge und Bodenebene.
- Zwei geteilte Schellen mit 32 mm Greiflänge je Einheit verteilen die Kontaktlast gegenüber D11 mit 16 mm. Die vorhandenen Motor-/Rahmenschellen bleiben unverändert. Jedes Armrohr bleibt ohne zusätzliche Querbohrung; interne Kabel aus D10 bleiben erhalten.
- Die Stützen sitzen konzentrisch unter dem ausgewählten Armrohr. V1/V3 verwenden Rohrindex 0, V2 Index 1, V4/V5 Index 2 (Zählung ab null). So durchstoßen senkrechte Beine kein darunterliegendes Armrohr. Bei V3/V5 folgen ihre Y-Positionen der Rohrspreizung.
- Obere Klebefittings gehören zum durchgängigen Aluminiumträger; die unteren zum durchgängigen Aufsetzfuß. Die CFK-Stirnflächen stützen sich über die GFK-Endringe an den Fittingflanschen ab. Die Klebung sichert unter anderem Auszug und Querkräfte; das Screening legt konservativ die gesamte axiale Kraft auch auf die Klebfuge. Die Stützen besitzen keine zusätzliche Gelenkverschraubung. Nominell 30 mm lange Hohlzapfen mit Ø16,6 mm lassen im nominalen Ø17-mm-Rohr eine 0,2-mm-Klebefuge pro Seite. 0,3-mm-GFK-Endringe trennen die CFK-Stirnflächen vom Aluminium. Die tatsächliche Kleblänge beträgt wegen der Endisolierung 29,7 mm.
- Zwei M4 × 30 je Schelle halten die abnehmbaren Deckel. Die Verschleißsohle wird mit zwei versenkten M3 × 6, Scheiben und im Alufuß gehaltenen M3-Muttern befestigt. Die Nut-/Schrauben-Geometrien besitzen echte normative Gewindeflächen; reale Festigkeitsklasse und Drehmoment sind noch festzulegen.
- Der Aluminiumfuß besitzt eine gerundete Grundkontur von etwa 124 × 24 mm, zwei Taschen und integrierte Hohlzapfen. Die gerundete Sohle misst 128 × 28 × 8 mm, mit vier flachen Querrillen. Werkstoffannahme: TPU 95A mit 1.200 kg/m³; kein freigegebenes Herstellerteil und kein qualifizierter Stoßdämpfer.

## Einbaulage und Bodenfreiheit

Die vier Sohlen liegen auf der nominalen ebenen Bodenebene Welt-Z −180 mm. Der niedrigste alte Zentralrahmenverbinder liegt nominell bei −134 mm, entsprechend 46 mm Abstand. Der hochkant geplante Reglerbauraum liegt zwischen Z −114 und −40 mm und hat damit 66 mm Bodenfreiheit. Reale Stecker, Kabelbögen und Verformungen sind noch nicht erfasst.

Die M3-Schraubenköpfe der Sohle sind nominal 3 mm oberhalb der Kontaktfläche versenkt. Dies ist kein zulässiger Federweg: Verschleiß, Toleranzen und reale Sohlenkompression müssen unter dieser Grenze bleiben beziehungsweise durch eine überarbeitete Befestigung berücksichtigt werden. Alle vier Füße haben nur für den ebenen, unverformten CAD-Zustand definierten Erstkontakt. Kipp-, Seitenlast-, Unebenheits- und Landestoßverhalten sind nicht freigegeben.

Die Radialposition bleibt 140 mm vor der jeweiligen Motorachse zur Rahmenmitte. Das Regler-Bezugsvolumen 146 × 39,5 × 74 mm ist gegenüber D11 um die radiale Achse hochkant gedreht. Seine 126 × 66 mm Lochanordnung liegt auf zwei vertikalen Montageschienen. Das ist eine neue Einbaulagenannahme. Der Reglertyp V200A 24S ist inzwischen vom Nutzer zugeordnet; zulässige Kühllage, Anschlusspositionen und Original-CAD fehlen weiterhin. Der orange Kantenrahmen stellt ausschließlich diesen Bauraum dar. Es wurden keine unbekannten Gehäuse- oder Steckeroberflächen erfunden.

## Gewicht und Vorbemessung

Der Default V4/42 Zoll liegt ungefähr bei 305 g je vollständiger Halter-/Fußeinheit, insgesamt etwa 1,22 kg. Gegenüber vier D11-Reglerhaltern sind das rund 0,77 kg zusätzlich. Die Katalogmasse des V200A 24S ist inzwischen mit 748 g einschließlich Leitungen bekannt. Die bisherigen CAD-Teilmassen enthalten das reale Regler-/OEM-Leitungspaket noch nicht; es wird separat geführt, um doppelte Leitungszählung zu vermeiden. CFK-Stützen sparen hier etwa 120 g gegenüber acht geometrisch identischen Aluminiumrohren. Ein globales Gewichtsoptimum oder eine freigegebene Mindestwandstärke ist damit nicht nachgewiesen.

Das [Screening](Ausgabe/Landelast_Screening.json) berücksichtigt alle 50 Konfigurationen und vergleicht vier vertikale Lastfälle: 1 g auf vier Füßen sowie 3 g auf vier, zwei oder einem Fuß. Angenommen werden 160 kg Gesamtmasse einschließlich 100 kg Nutzlast. 3 g auf zwei Füßen ergeben rund 2,35 kN je Fuß. Gerechnet werden ideale axiale Stützenbeanspruchung, Eulerlast, mittlere Klebschub- und Kontaktspannung, jeweils ohne qualifizierte Materialzulässigkeiten. Ungleichlast wird zusätzlich als gesamte Fußlast auf einer Stütze ausgewiesen. Es handelt sich weder um FEA noch um eine validierte dynamische Simulation.

Bei 0,5 m/s Sinkgeschwindigkeit müssen bei 160 kg bereits 20 J Bewegungsenergie aufgenommen werden. Für ideal konstante Verzögerung bei insgesamt 3 g wären etwa 6,37 mm Weg nötig. Bei nur 2 mm Weg läge der entsprechende Faktor bei etwa 7,37 g. Ohne gemessene Kennlinien von Sohle und Gesamtrahmen ist der angenommene 3-g-Lastfall deshalb keine Aussage über eine tatsächlich beherrschte Landung.

## Offene Freigabepunkte

Der CFK-Hersteller muss Laminataufbau, Längsdruck-/Biegekennwerte, zulässige Querdruckbeanspruchung und tatsächliche Innendurchmessertoleranzen belegen. Die genannte Außentoleranz ±0,2 mm belegt keine Innentoleranz. Auch Schellen und 0,3-mm-Zwischenlagen sind bislang nur nominal modelliert; die Passung muss mit gemessenen Rohren und abgestimmten Zwischenlagen einschließlich Vorspannung geschlossen werden. Klebefittings benötigen einen qualifizierten Klebstoff, definierte Oberflächenvorbereitung einschließlich PU-Beschichtung, galvanischen Schutz, Fugen-/Aushärteprozess und Versuche auf Druck, Abziehen, Schälbeanspruchung, Ermüdung, Feuchte und Temperatur. Die gewählten Bondfugen sind bisher geometrische Annahmen.

Die Landeaufnahmen bringen Punktlasten zwischen den Armknoten ein; auch die Biegung des gewählten Armrohrs zwischen den Knoten ist deshalb ausdrücklich zu prüfen. Der gesamte Kraftfluss in Carbonarme und Rahmenknoten einschließlich Klemmschlupf, Quetschung, Vorspannung, Querlast, Knicken und Stabilität muss nachgewiesen werden. Die Rohrmodul-Annahme von 50 GPa im axialen Screening ist kein Herstellerwert. Rahmen-/Pilot-Schwerpunkt und Kippstabilität bleiben offen. Zur Sohlenwahl fehlen Druck-/Weg-, Reibungs-, Verschleiß- und Temperaturdaten. CNC-Innenradien, Fertigungs-/Passungstoleranzen und vollständige Zeichnungen sind noch zu schließen.

Die neuen [V200A-Reglerdaten](REGLER_V200A24S.md) schließen die Modellzuordnung und einige Nennwerte. Akku-/Steckerdetails, Gehäuseports und geometrisch vollständige Phasenleitungen bleiben offen. D11 dokumentiert den früheren Datenstand. Die bisherigen DC- und Signalwege wurden durch diesen Aufbau nicht elektrisch vervollständigt. Keine Produktions- oder Flugfreigabe.

## Abgeschlossene geometrische Prüfung

Alle 50 nativen Konfigurationen und alle 50 Browserstellungen sind bestanden. Die Volumenprüfung meldet bei 12500 Vergleichskandidaten keine Überschneidungen oberhalb 0,1 mm³. Alle neuen Bauteile bleiben mindestens 43.34 mm unter der angenommenen Rotorunterkante. Für alle 50 Fälle wurden gleiche Sohlenhöhe und positive Bodenfreiheit der übrigen Teile festgestellt: alter Rahmen mindestens 46 mm, geplanter Regler 66 mm, eingelassene Sohlen-Schraubenköpfe 3 mm. Die Sichtbarkeit von Normteilen, Reglerbauraum und allen vier kombinierten Einheiten ist separat geprüft.

Diese Ergebnisse gelten für die native Datei mit SHA-256 `23478d47053133dacca31e4ffcfead23af2fe1c7aad34f8ae371195ffa0a58c0`. Viewer, geometrische Prüfberichte, Last-/Massenscreening und Bedienprüfung referenzieren denselben Hash. Es handelt sich um nominale Geometrieprüfungen, keine Landetragfähigkeits- oder Fertigungstoleranzfreigabe.

## Dateien und Reproduktion

`parameter.json` steuert Bodenhöhe, Schellen, CFK-Stützen, Klebefittings und Reglerlage. `landegeometrie.py` erzeugt die konkreten Bauteilflächen; `bauen.py` baut aus D10 eine vollständige native Baugruppe mit denselben 50 Variantenstellungen auf. Die Schraubenteile werden aus den bestehenden, dokumentierten BREP-Normteilen aus D01, D11 und der Variantenbaugruppe übernommen. Die ursprünglichen Materialdichten bleiben Annahmen: CFK 1.600, Aluminium 2.700, GFK 1.900, Stahl 7.850 kg/m³.

`pruefen.py` prüft neue Teile gegen den gewählten Altstand an allen vier Armen, interne Bauteilpaare an einem Arm (die anderen drei sind starre Kopien), Einheiten untereinander und den hochkant gestellten Reglerbauraum gegen Altteile und eigene Halterteile. Nur die geplanten Reglerschrauben dürfen in diesen Bezugsraum greifen. Die Überschneidungsschwelle beträgt 0,1 mm³. Die Z-Lage aller neuen Bauteile wird zusätzlich gegen die angenommene Rotorunterkante 124 mm geprüft. Die alten Rotorhüllen-Nachweise bleiben als D10-Quellnachweis kenntlich.

`D12_GROUP=0` bis `3` teilt die native Prüfung nach Propellerindex modulo vier auf; `pruefberichte_zusammenfuehren.py` verlangt anschließend alle 50 disjunkten Konfigurationen mit identischem Datei-Hash. `viewer_export.py` exportiert tatsächliche CAD-Oberflächen. `viewer_pruefen.cjs` prüft alle 50 Browserzustände und erstellt Ansichten. `lastfaelle.py` berechnet Massen, Zuschnitt und die ausdrücklich nicht qualifizierten Lastfälle.
