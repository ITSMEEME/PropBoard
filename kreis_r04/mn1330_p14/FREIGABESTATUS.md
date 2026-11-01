# Freigabestatus P14

**Produktionsreif: nein. Bestellfreigabe: nein. Personen-/Flugfreigabe: nein.** Animierbarkeit und gültige CAD-Körper sind separat geprüft; sie ersetzen diese Freigaben nicht. Das große Modell bleibt deshalb als eigener Entwicklungsprüfstand neben H01.

| Bereich | Erledigt | Noch erforderlich |
|---|---|---|
| Außenrahmen / Spitzenlager | vollständig im neuen Modell entfernt | Folgen für Elastik, Unwucht und Schwingungen nachweisen |
| Zentrale Struktur | Rücken-an-Rücken-Motoren, gemeinsame Anker, separate Hauptlager, monolithischer Wurzelstern mit Lastplatte | Gesamtlastpfad per FE, Flanschsteifigkeit, Befestigung, Hochlauf-/Unwucht-/Ausfallfälle |
| Freitragende Flügel | Schale/Spar/Wurzel und mechanische Flanschfassung modelliert | orthotropes Laminat, Delamination, Flanschbohrungen, Klemmung, Fliehkraft-/Dauerversuche |
| Aluminium-Verbindungen | Strukturwellen, Klemmungen und wichtige Schrauben-/Mutternkonturen aus Alu | reale verfügbare Verbindungsmittel, Gewinde, Sicherungen, Vorspannung, Setzen, Korrosion und Ermüdung |
| Servo | PH54-200-S500-R ausgewählt; extern gelagerte Umlenkwelle, Passfederhebel und verschraubter Träger | OEM-STEP/Zeichnung, tatsächliches Horn und Gehäusebefestigung, Dauerbetrieb/Kühlung, Steuerungsbandbreite |
| Gestänge | 44 trennbare Gelenke je Paar, GE8E-Nennlager und ein geführtes R-Gelenk je Kopf; RH/LH-Einstellung, Bolzen/Splinte/Spacers modelliert und animiert | konkrete Lager-/Ring-Lieferprofile, Tragzahlen, Alu-Augen/Bolzen/Gewinde unter Last, Verschleiß und Toleranzen |
| Montage | abnehmbarer Hauptflansch, offene äußere Blattlagersitze, geteilte Kugelpfanne und Taumellagerdeckel; dokumentierte Einbauwege und Bitzugänge | Fertigungstoleranzen, Montagekräfte, vollständige Hand-/Werkzeughüllen, Vorspannungs-/Anzugsvorgaben und OEM-Servo-Schnittstelle |
| Lager / Gleitführung | Normgrößen und Anordnung modelliert | Hersteller/Lieferausführung, Tragzahlen, Vorspannung, thermische Passungen, Sicherung, Lebensdauer, PTFE-Reibung und Verschleiß |
| Motor | Nutzerzeichnung, 2,75-kg-Angabe aus XLS, 24S/ca.92V und19 NS52×20-Prüfpunkte übernommen | 65/66-mm-Montagebezug, Gewindetiefen, tatsächliche Masse wiegen; 3,4-kW-Angabe auf180s begrenzt, Prüfmaxima ohne Haltedauer; vollständige Sonderrotor-/Dauerkennlinie und Lagergrenzen fehlen |
| Kabel / Versorgung | Bauraum und Verbraucherbedarf als Untersuchungsgrenze benannt | realer Kabelbaum, Stecker, Biegeradien, 24-V-Servo-Zweig, Akku, Gehäuse, Kühlung und Massenerfassung |
| Nutzlast / Boden | gemeinsamer Zentralanschluss, Punktmassenszenario, idealer Simulatorboden | Personendeck, Rückhalt, Schutzkonzept, reale Landestruktur, entsprechende Lasten/Massen |
| Mehrere Rotorpaare | parametrische nicht überlappende Anordnung; neue Gesamtmasse und Trägheit | konstruktiver Verbindungsrahmen, Versorgung, Regelung und Zielmaßnachweis je Anordnung |
| Simulation | separate parametrische Entwicklungsrechnung mit tatsächlichen CAD-Massendaten | Messabgleich, dynamische Rotor-/Servomodelle, elastische Kopplung, Flugregler, tatsächliche Motorgrenzen |

Das vollständige statische Kollisionsprotokoll steht in [Kollisionen.json](Ausgabe/Kollisionen.json), ohne pauschale Kontakt-Ausnahmen. Die dynamische Stichprobe steht in [Kinematik_Pruefung.json](Ausgabe/Kinematik_Pruefung.json), die Montageprüfung in [Montage_Pruefung.json](Ausgabe/Montage_Pruefung.json). Diese Prüfungen gelten mit ihrem jeweiligen Umfang; Variantenkörper allein belegen keine Kollisionsfreiheit aller Parameterkombinationen.

Die nächste Freigabestufe benötigt die gültige Servo-Montage-/Hornzeichnung und die Qualifikation der gewählten Lager-/Gelenk-Lieferteile. Die Tragfähigkeit hängt außerdem von der MN1330-Grenz-/Dauerkennlinie und der CFK-/Alu-Auslegung ab. Die NS52×20-Prüflinie deckt den berechneten Sonderrotor-Schwebebedarf nicht ab. Der Zusatz180s ist keine Dauerleistungsfreigabe.
