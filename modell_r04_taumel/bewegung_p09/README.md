# P09 – eine geschlossene Bewegung vom Servo bis zum Rotorblatt

**Eine gemeinsame FreeCAD-Baugruppe und ein gemeinsamer Kinematiklauf** ersetzen die bisher getrennte M01-Rotoranimation und die isolierte P08-Servoverbindung. Dies ist ein detaillierter Bewegungs-/Konstruktionsentwurf, keine Fertigungs- oder Flugfreigabe.

## Durchgängige Verbindung

SB-2270SG+-Gehäuse (fest) → tatsächlich aus der STEP abgetrennter Abtriebsbereich (dreht) → geschlitzter P08-Klemmhebel → gefasste P08-Kugelgelenke und RH/LH-Stange → stationärer Taumelring → komplettes 6809-Kauflager → Drehring und verschraubter Blattgelenkträger → 16 gefasste kurze Blattgestänge → angeschraubte Kugelbolzen am Pitchhebel → Vierkant und axiale Blattwurzel-Sicherung → Rotorblatt.

„Geschlossen“ bedeutet übereinstimmende Gelenkmitten und feste Gestängelängen. Vorgesehene Lauf- und Passungsspiele bleiben erhalten; bewegliche Teile werden nicht zu einem unbrauchbaren einzigen Festkörper verschmolzen.

### Servo und Abtrieb

Das gekaufte Servo bleibt äußerlich aus der gelieferten STEP abgeleitet. Der lokale Abtriebsbereich ist ein gültiger Körperverbund und dreht mit dem Klemmhebel. Der Rest des Gehäuses steht fest. **Die ursprüngliche Gesamt-STEP und ihr Gehäuserest sind weiterhin geometrisch ungültig.** Die boolesche Trennung ist deshalb keine Reparatur oder Fertigungsfreigabe; der kleine Volumenfehler der Partition wird im Prüfbericht genannt. Keine erfundenen Servo-Innenteile.

### Blattgestänge und Befestigung

Die bisherigen 16 Zylinder und 32 schwebenden Kugeln werden durch 16 mechanisch gefasste Gelenkstangen ersetzt, jeweils mit zwei Kugelbolzen, zwei Pfannenkörpern, zwei eingeschraubten Haltekappen und einer RH/LH-Stange. Die Kugel wird vor dem Einschrauben der Kappe eingesetzt. M2-Stangenanschlüsse und Mundgewinde M5,5×0,35 sind als eigene Mikromechanik-Konstruktion ausgelegt, nicht als behauptetes existierendes Kaufteil.

Die Kugelmitten bleiben 15 mm auseinander. Der radiale Bezug der Blattgelenke steigt von 32 auf 33 mm, damit die Pfannen am Lager vorbeikommen. Die gesamte Blattpitch-Lösung wird mit 33 mm neu berechnet. Die sechs Servo-Gestängelängen und Servoachsen aus P08 bleiben erhalten.

Pitchhebel und Gelenkträger besitzen echte radiale M2-Aufnahmen und Freistellungen. Jeder Pitchhebel bekommt eine Axialscheibe und M2×8-Schraube. In der Blattwurzel ist ein M2-Metalleinsatz mit explizit modellierter 0,05-mm-Klebefuge vorgesehen. Die Eignung dieses Kleb-/Material-/Lastpfads ist **nicht nachgewiesen**; er ist eine konkrete Konstruktionsannahme, keine bestehende Zertifizierung.

### Lager, Mitnahme und Freiräume

Der Drehring erhält einen Lagersitz entsprechend Ø58 mm (nominale Entwurfsbohrung Ø58,06) und eine Schulter erst oberhalb der 7-mm-Lagerbreite. Ein abnehmbarer unterer Gelenkträger mit acht M2×4-Schrauben bildet den unteren äußeren Haltering und trägt die acht Blatt-Kugelbolzen je Rotor.

Mitnehmer und genutzter Schlitz werden auf die den Gestängefenstern abgewandte 7°-Position verlegt. Die Deckelfenster sind 9×12 mm. Die Nabeninnenwand erhält Freistellungen für die neuen Pfannen; der äußere Bereich an den Blatt-Querstiften bleibt bestehen. Diese Änderungen benötigen anschließend eine eigene Festigkeits- und Fertigungsauslegung.

## Direkt im Browser ansehen

`Ausgabe/P09_Durchgaengige_Animation.html` offline öffnen und „Animation starten“ wählen. Die Zeitleiste zeigt 161 gemeinsam berechnete Stellungen. Mausziehen dreht die Ansicht, das Mausrad zoomt. „Gehäuse, Deckel und Naben ausblenden“ legt die Mechanik frei; ausgeschaltet zeigt es die vollständige Baugruppe. Es werden tatsächliche FreeCAD-Oberflächen mit einer Anzeigeauflösung von 0,01 mm und einer Tessellierungsabweichung von 0,35 mm verwendet, keine Ersatzblöcke. Wiederholte Teile teilen sich nur die Anzeigepuffer; native Geometrie und Einzelbewegung bleiben getrennt. Browser ohne WebGL können die FreeCAD-Datei verwenden.

Bei gesperrtem `file://` im entpackten Paket einen lokalen HTTP-Server starten und die HTML-Seite darüber öffnen.

## In FreeCAD öffnen und animieren

1. Paket vollständig entpacken und Ordnerstruktur erhalten.
2. In **FreeCAD 1.0.2** `bewegung_p09/P09_Bewegung_oeffnen.FCMacro` ausführen.
3. „Gemeinsame Demo starten“ bewegt beide Rotoren, alle 16 Rotorblätter, beide Taumelscheiben und alle sechs Servo-/16 Blattgestänge gemeinsam.
4. Alternativ sechs Servo- und zwei Rotorwinkel manuell einstellen. Unlösbare Kombinationen werden **vor** einer Änderung verworfen. Der angezeigte manuelle ±8°-Eingabebereich ist keine Zusage, dass jede beliebige Kombination zulässig ist.

Die acht Sekunden lange Demo ist periodisch und zeigt die Mechanik in verlangsamt dargestellter Drehung. Sie ist kein neuer Flugversuch für den SB-2270SG+ und verwendet keine ungeprüft übernommenen SB-2271-Motordaten. Native Körper bleiben auch ohne Python-Modul statisch sichtbar; für die Animation wird das Makro gebraucht.

## Dateien

- `Ausgabe/P09_Servo_bis_Rotorblatt_Bewegung.FCStd`: vollständige gemeinsame Baugruppe.
- `Ausgabe/P09_Anschlussdetails_ENTWURF.FCStd` und STEP-Einzelteile: neue Blattgelenk-/Befestigungsdetails.
- `Ausgabe/Aufbaupruefung_P09.json`, `Bewegungspruefung_P09.json`: Wiederöffnen, Gelenkschluss, tatsächliche Kugelmitten und ausgewählte Festkörper-Kontakte.
- `voll_runtime.py`: gemeinsame Kinematik. `geometrie_p09.py`: konkrete neue Bauteilgeometrien.

## Was noch offen bleibt

Servohalter/Lastpfad zum Grundkörper, endgültige Lagerartikel und innere Axialsicherung, gültige Servo-Gesamtgeometrie, Fertigungstoleranzen/Passlehren, Gewindesicherung und Anzug, Werkstoffe/Oberflächen/Klebstoff, Festigkeit, Reibung und Lebensdauer. Die nominale Gewindedarstellung ersetzt keine Gewindeangabe; M2 RH/LH, M5,5×0,35 und die Anschlüsse müssen nach Zeichnung gefertigt werden. Eine vollständige, kontinuierliche Kollisionsprüfung aller Baugruppenpaare liegt nicht vor.

Die Animation ist eine Zwangskinematik mit idealisierten Gelenken. Sie bestimmt keine Kontaktkräfte, Lagerreibung oder elastische Blattverformung und bestätigt keine Flugfähigkeit.

## Wiedererzeugen

Aus dem vollständigen Checkout:

```sh
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/bewegung_p09/erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/bewegung_p09/pruefen.py
```

## Prüfstand und Grenzen der Bedienprüfung

181 numerische Stellungen, davon 41 mit Prüfung der tatsächlichen nativen Kugeloberflächen, und 1.304 ausgewählte Festkörperkontakte: Gelenkschluss < 0,000001 mm; keine gemeldeten Überschneidungen im geprüften Satz. Die native Steuerung hält ihre Servo-/Rotor-Eigenschaften synchron mit der angenommenen Stellung; unzulässige Eingaben hinterlassen keine teilweise aktualisierte Baugruppe. Die Objektpfade aller sechs Servo- und 16 Blattzweige stehen in `Ausgabe/Verbindungskette_P09.json`.

Die Browserbedienung wurde mit Chromium geprüft. Für den FreeCAD-Dialog liegt wegen fehlendem OpenGL-Kontext in der Cloud kein abgeschlossener GUI-Bedientest vor; native Datei, Steuerungsfunktion und Wiederöffnen wurden ohne GUI geprüft. Diese Einschränkung betrifft die Bedienprüfung, nicht die dokumentierten rechnerischen Gelenk-/Kontaktprüfungen.
