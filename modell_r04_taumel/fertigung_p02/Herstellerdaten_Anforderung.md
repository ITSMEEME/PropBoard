# Fehlende Herstellerdaten – Cohexial Study R04

Lager, Motoren und Servos werden als **komplette Kaufteile** verwendet. Fertigungszeichnungen ihrer Innenteile sind daher nicht erforderlich. Für die Integration helfen Original-STEP-Dateien und bemaßte Hersteller-PDFs. Wenn es keine STEP-Datei gibt, genügt eine vollständige Anschlusszeichnung für die Modellierung.

## 1. Motor – zuerst beschaffen

**2× EMAX ECO II 2306 KV1900**, exakte Version:

- Montage-Lochbild: Raster oder Lochkreis mit genauen Achsabständen.
- Befestigungsgewinde und maximal zulässige Einschraubtiefe.
- Abtriebswelle: Ø beziehungsweise Gewinde, Flachstellen, Schulter, nutzbare Länge und Haltemutter/-schraube.
- Gehäuse-/Glockenmaße, Montagefläche und erforderliche Freiräume.
- Originaldatenblatt der konkreten Version, möglichst mit tatsächlicher Masse.

**Grund:** Das aktuelle CAD besitzt einen Lochkreis Ø16 mm, entsprechend 11,3137×11,3137 mm quadratischem Raster. Das ist nicht 16×16 mm. Die tatsächliche Motorzeichnung muss vor Fertigung der Platte abgeglichen werden.

## 2. Wälzlager – zuerst beschaffen

- **4× 6806-2RS, 30×42×7 mm**.
- **2× 6809-2RS, 45×58×7 mm**.

Für beide Baugrößen fehlen:

- Hersteller und genaue Bestellbezeichnung einschließlich Dichtungs-/Lagerluftsuffix.
- Original-CAD oder Maßblatt mit Fasen/Radien und zulässigen Schulter-/Anlagedurchmessern.
- Grenzmaße/Toleranzen von Bohrung und Außendurchmesser, Lagerluftvariante und Passungshinweise.
- Statische/dynamische Tragzahlen und zulässige Drehzahl der konkreten Dichtungs-/Schmierungsvariante.

## 3. Servo – fehlende Anschlussdetails ergänzen

**6× Savöx SB-2271SG(+):**

- Exakte Variante SG oder SG+ auf dem tatsächlichen Artikel.
- Dicke und Lage der Befestigungslaschen, Loch-/Schlitzdurchmesser.
- Abtriebsverzahnung mit Durchmesser/Einsteckhöhe oder Zeichnung eines kompatiblen Kaufhorns.
- Gewinde, Länge und Anlage der Horn-Halteschraube.

Gehäusemaße, Befestigungsraster, 69 g, Spannungsbereich und Drehmoment-/Stellzeitangaben wurden bereits aus deinen Angaben übernommen; diese müssen nicht nochmals geliefert werden.

**Zusätzlich für die elektrische Auslegung/Inbetriebnahme:** Leerlauf-/Stell-/Blockierstrom, PWM-Neutralpunkt und Pulsbereich, zulässige Wiederholrate, Signalpegelverträglichkeit, tatsächlicher Stellbereich sowie vorhandene Last-/Dauerlastkennlinien.

## 4. Servohörner

**6× gekauftes, mit dem Savöx kompatibles 25T-Horn**, Anlenkradius **8 mm**:

- Hersteller/Artikelnummer.
- Abtriebsaufnahme und passende Halteschraube.
- Anlenkbohrung/Gewinde und Abstand ihrer Ebene zur Servoachse.
- Anschluss des gewählten Kugelbolzens.

## 5. Kugelbolzen und Gestängeköpfe

Für **16 Blattgestänge und 6 Servogestänge**:

- Konkrete Artikelnummern von Kugelbolzen und passenden Pfannen/Gestängeköpfen.
- Kugeldurchmesser, Gewinde, Schulter-/Kopfabmessungen und Verschraubung.
- Kleinste/größte einstellbare Kugelmittenlänge und Gewindeeingriff.
- Gelenkhülle und zulässiger Gelenkwinkel, möglichst Belastbarkeitsangaben.

Der bisherige Entwurf verwendet nominell 4,8-mm-Kugeln und M2-Anschlüsse. Diese Werte sind noch keiner konkreten vollständigen Produktfamilie zugeordnet.

## 6. FC-/ESC-Montage

**SpeedyBee F405 V4 / 55-A-ESC entsprechend deiner Zeichnung:**

- Exakte Gummitüllen-/Dämpfermaße, Schraubenbohrung und Einbauhöhe.
- Tatsächliche Anlageebenen der Platinen und benötigte Distanzhöhen inklusive Dämpfern.
- Falls verfügbar: komplettes Stack-STEP beziehungsweise Montagezeichnung.

Die bereits gelieferten Platinen-Außenmaße und das 30,5-mm-Raster sind vorhanden.

## 7. Werkstoffdaten für die Eigenfertigung

Für die endgültige Fertigungsfestlegung zusätzlich: genaue verwendete PA-CF-/PETG-Sorte samt Herstellerdatenblatt; bei Metallhalbzeugen Werkstoffbezeichnung/Zustand. Druckorientierung, Nachbearbeitung und erreichbare Sitzmaße müssen anschließend am tatsächlichen Prozess festgelegt werden. Das sind keine fehlenden Motor-/Lager-Innenteilzeichnungen.
