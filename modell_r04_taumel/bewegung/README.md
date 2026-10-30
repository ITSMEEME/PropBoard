# M01 – bewegliche FreeCAD-Baugruppe

Starte [`Bewegung_oeffnen.FCMacro`](Bewegung_oeffnen.FCMacro) in FreeCAD 1.0.2 oder neuer. Es öffnet die [native Baugruppe](Ausgabe/Cohexial_R04_M01_Bewegung.FCStd), lädt den Python-Bewegungssolver und zeigt eine Zeitleiste mit Start/Pause, Zeitfaktor, Flugwiedergabe und Servo-Geometrieauswahl. Die Vorschau [`Ausgabe/Vorschau_M01.png`](Ausgabe/Vorschau_M01.png) wurde aus den tatsächlichen BReps in einer bewegten Stellung erzeugt.

**Kinematik und Wiedergabe eines externen Flugmodells; keine Kraft-/Kontaktlösung durch FreeCAD und keine Fertigungsfreigabe.** Der H01-Fertigungsstand bleibt unverändert. Das M01-Modell enthält 348 sichtbare Körper sowie vier ausblendbare Zugangsräume. Motor-/Lagerinnenteile sind Funktionsschemata, keine rekonstruierten Hersteller-Innenteile. Die inneren Getriebestufen eines Kaufservos sind ohne Zeichnungen nicht modelliert.

## Bewegte Teile

- Zwei Naben, Deckel/Zahnkränze und Mitnehmer; 16 Flügel, 16 Pitchhebel, 32 Haltestifte, 32 Blatt-/Ringkugeln und 16 feste Blattgestänge.
- Zwei gleitende Kugelhülsen, zwei kippende stationäre Taumelscheibenringe samt Kugelbolzen/Führungsstiften und zwei rotierende Taumelscheibenringe.
- Sechs Servoabtriebe, 8-mm-Hörner, Hornkugeln und feste Servogestänge. Tangentiale Servoachsen und tatsächliche Kreisbahnen statt variabler Stangenlängen.
- Zwei Ritzel, Motorwellen und Motorglocken. Ritzel/Motor laufen mit −6,5-fachem lokalem Rotorwinkel; die untere komplette Ebene ist umgedreht, sodass beide Rotoren im Fahrzeug gegenläufig drehen.
- Vier Hauptlager und zwei Taumelscheibenlager mit getrennten Innen-/Außenringen, Käfigen und insgesamt 120 schematischen Kugeln. Hauptlager-Innenringe stehen; Außenringe drehen. Taumelscheiben-Innenringe kippen ohne Rotorrotation. Idealisiertes Abrollen bestimmt Käfig-/Kugeldrehung. Kugelzahlen, Laufbahnform und innere Lagermaße sind **angenommen**, nicht herstellerbelegt.

Die Kinematik berechnet aus drei festen Servo-Gestängelängen die jeweilige Taumelscheibenlage. Acht feste 15-mm-Blattgestänge liefern tatsächliche Pitchwinkel über dem Rotorumlauf. Flügel und Hebel sind nicht auf einen beliebig vorgeschriebenen Sinus gesetzt. Die Zuordnung des unteren lokalen Rahmens ist `diag(−1,1,−1)`. Spiel, elastische Verformung und Kontaktkräfte werden nicht gelöst; Mitnehmer-/Führungsfreiheit wird an ausgewählten BRep-Schnittstellen geprüft.

## Deine Servo-Zeichnungen

`ServoTyp` wählt zwischen den aus Nutzerbildern übernommenen nominalen Hüllen:

| | Savöx SB-2271SG(+) | KST X15-755X 760 µs |
|---|---:|---:|
| Gehäuse L×B×H | 40,3×20,2×38,7 mm | 35,5×15×31,6 mm |
| Höhe inklusive Abtrieb | 42,7 mm | 36,6 mm |
| Gesamtlänge über Laschen | 54 mm | 47,5 mm |
| Befestigungsraster | 48×10 mm | 41,5×7,5 mm |
| Abtriebsachse ab Gehäuseende | 10,3 mm | 11,2 mm |
| Masse | 69 g laut Tabelle | unbekannt |
| Ansteuerung | genaue PWM-Daten fehlen | 760 µs auf Bild, weitere Angaben fehlen |

Die Zuordnung der Savöx-Tabelle erfolgt anhand der dazu gelieferten Zeichnung; der Plus-Suffix muss am realen Typ bestätigt werden. Alle Quellenfelder stehen in [`../messdaten/Servodaten_Nutzer.json`](../messdaten/Servodaten_Nutzer.json). Die Herstellerpublikation wurde nicht unabhängig abgerufen.

Laschendicke 2 mm ist Darstellungsannahme. Der Savöx-Lochdurchmesser fehlt und wird im Schema mit 3,2 mm dargestellt; der KST-Bohrungswert ist aus der Zeichnung abgelesen. Spline-Außendurchmesser, Zahnprofil und passende Hornbefestigung fehlen: Der Abtrieb ist trotz bekannter Savöx-25T-Bezeichnung nur ein Zylinder-Schema. **Diese Hüllen sind keine druckbaren Ersatzgehäuse oder fertigen Servohalter.** Die vorhandene horizontale H01-Platte benötigt zusätzliche, noch nicht konstruierte Halter für die tangentialen Achsen/Laschenebenen.

## Wiedergabe

`Kinematik_Demo` dreht mit absichtlich langsamen 7,5 U/min und verändert Kollektiv/Zyklik. Das ist kein Betriebsdrehzahlpunkt. Die drei Savöx-Flugkanäle geben das 69-g-Servomodell aus der [Flugsimulation](../simulation/README.md) wieder: Manöver bei 7,4 V, Böe bei 6 V und angenommene Reibung 0,2. Masse und Servo-Hüllen stammen aus deiner Angabe; Totzeit, vollständige Dynamik, Stromaufnahme und Reibung sind weiterhin Annahmen.

KST lässt sich nur in `Manuell`/`Kinematik_Demo` wählen. Es fehlen Masse, Drehmoment und Stellzeit; **760 µs sind nicht ungeprüft mit einem üblichen 1500-µs-Setup austauschbar**. Beim Umschalten auf KST wechselt das Makro deshalb zum Geometrie-Demo.

Bei Flugwiedergabe beziehen sich Positionen auf den Schwerpunkt; der Solver transformiert alle Teile korrekt aus dem CAD-Rahmen. Winkelfortschritt wird aus den gespeicherten Rotordrehzahlen integriert und unaufgewickelt interpoliert. Hochdrehende Rotoren können bei normaler Bildschirmrate optisch flimmern/stroboskopisch stehen. Mit kleinem Zeitfaktor wird die Bewegung sichtbar. Die Wiedergabe übernimmt die angenommene ideale Positions-/Lageschätzung des Flugmodells und berechnet keine neue Flugdynamik in FreeCAD.

Ohne Makro kann FreeCAD die statisch gespeicherte Neutralstellung öffnen. Für erneutes Rechnen müssen `bewegung_runtime.py` und `servo_geometrie.py` im Python-Pfad liegen; das erledigt das Makro. `Manuell` erlaubt sechs relative Servo-Winkel und zwei Rotorwinkel. Persistente Parameter liegen am Objekt `Bewegungssteuerung`; keine native Assembly-Workbench-Gelenkstruktur und kein PartDesign-Baum wird behauptet.

## Prüfung und Reproduktion

[`Ausgabe/Validierung_M01.json`](Ausgabe/Validierung_M01.json) enthält den nativen Wiederöffnungstest, Bewegung über einen vollen Rotorumlauf und ausgewählte Kontakte für beide Gehäusevarianten. Es werden Servo/Horn/Hülle, Servo-/Blattgestänge/Platte/Deckel, Führung/Mitnehmer, Motor-Glocke/Stator und acht Verzahnungsstellungen geprüft. Das ist kein vollständiger All-Pairs-Test für jede zulässige Stellung. Originale offene Blatt-Kugelaufnahmen, axiale Sicherungen, Festigkeit und die echte Servobefestigung bleiben offen.

Der tatsächliche FreeCAD-GUI-Prozess wurde im Qt-Offscreen-Modus auf Makro-Panel, Zeitleiste, Savöx-Szenariowechsel und KST-Beschränkung geprüft (`GUI_Pruefung.json`). Ein OpenGL-Viewport konnte in diesem Offscreen-Modus nicht geprüft werden; die native Geometrie wurde separat headless getestet und für die Vorschau trianguliert.

```sh
# Aus dem Repository-Stamm, offizielle FreeCAD 1.0.2:
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/venv/bin/python modell_r04_taumel/bewegung/daten_erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/bewegung/erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/bewegung/servo_traegheit.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/bewegung/pruefen.py
```

Neue Geometrie erfordert danach ein erneutes Rechnen der zugehörigen Flugversuche. M01-Lager-/Motor-Innenvolumina dürfen nicht als neue realistische Massenträgheitsverteilung interpretiert werden. Die Flugsimulation behält H01 für die übrigen Massen und ersetzt ausschließlich die sechs Servo-Massenverteilungen durch nominale, homogen gewichtete Savöx-Hüllen. Neue Halter und BEC-Masse fehlen weiterhin.
