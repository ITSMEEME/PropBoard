# Quad HEP-S: zehn Durchmesser × vier Auslegervarianten

**Abgeschlossene Gesamtprüfung: 128 gemeldete Überschneidungen an Motorträgern/Statorschrauben in neun Größen-/Variantenkombinationen. Die Anschlussintegration ist nicht bestanden. Die nominalen Rotorhüllen sind weiterhin frei.** [Befunde](Ausgabe/Integration_Pruefung.json)

[Lieferpaket](Quad_HEPS_10_Groessen_V1_V4.zip) · [3D-Modell](Projekt.html) · [FreeCAD-Datei](Ausgabe/Quad_HEPS_Parametrisch.FCStd) · [Rechenvergleich als PDF](Ausgabe/Propeller_Struktur_Vergleich.pdf) · [Prüfstatus](Ausgabe/Status.json)

**Voreinstellung: HEP-S 42×16 mit V4 als Prüfkonfiguration. Keine Flug- oder Produktionsfreigabe.** Die Vorauswahl beruht auf Größen-/Energieberechnungen unter Annahmen; kein HEP-S-Typ ist anhand eines Herstellerkennfeldes für diesen Aufbau freigegeben.

## Was im CAD variabel ist

In FreeCAD im Modellbaum **Variantensteuerung** wählen. Im Reiter **Daten** lassen sich **Propeller** und **Variante** unabhängig umschalten. Alle zehn angegebenen HEP-S-Größen sind mit V1/V2/V3/V4 kombiniert: 40 vorberechnete Konfigurationen. Motorposition, Rohrlänge, integrierter Motorträger, Rohrkappen, Schrauben, Leitungsverlauf und Rotorhülle wechseln gemeinsam. Die Browseransicht verwendet die exportierten nativen Geometrien und dieselben beiden Auswahlen. Maßänderungen außerhalb der zehn Stufen erfordern einen Neuaufbau.

**Darstellungsgrenze:** Die drei Ringe pro Rotor markieren einen angenommenen Umlaufraum bei z124/154/184 mm. Sie sind keine schematischen Ersatzblätter und kein T-Motor-OEM-Propellermodell. Durchmesser und Steigung definieren weder Blattprofil, Sehne, Verwindung, Blattzahl noch Nabenanschluss. Die realen HEP-S-Blätter und ihre Naben bleiben ohne Herstellerzeichnung/STEP unmodelliert. Die Ringe haben keine Bauteilmasse.

Die übrige Mechanik ist mit Volumenkörpern, Rohrinnenräumen, geteilten Klemmungen, Isolierlagen und tatsächlichen Gewindeformen modelliert. Die Motoren bleiben die frühere MN1330-Zeichnungsreferenz. Die Rahmenaufnahme behält bei den Größenwechseln ihre Rohrwinkel; der Abstand der motorseitigen Rohrenden und die verbindenden Aluminiumrippen passen sich an. So werden Aluminiumkörper nicht einfach gestreckt. V1 benötigt weiterhin das zusätzliche, nicht belegte Rohr Ø35/32; V2–V4 verwenden Ø20/17.

## Größen und Vorauswahl

Vergleichsfall: **100 kg Nutzlast**, 35 kg angenommene Fahrzeugmasse ohne Akku, 5 Minuten Schweben, 150 Wh/kg Packenergie vor 20 % Reserve, Gütegrad 0,65, Motor-/Reglerwirkungsgrad 0,82, Luftdichte 1,225 kg/m³. Akku und Leistungsbedarf werden iterativ gekoppelt. Sensitivitäten für Gütegrad 0,55/0,65/0,75 und 3/5/8 Minuten sind in den Rohdaten enthalten. Die 35 kg sind ein Budget, keine geschlossene Fertigstückliste.

| HEP-S | Durchmesser | Breite ohne Schutz | Gesamtmasse im Rechenfall | Welle je Motor |
|---|---:|---:|---:|---:|
| HEP-S 18×6.7 | 457.2 mm | 1.297 m | 294.5 kg | 47.09 kW |
| HEP-S 22×7.2 | 558.8 mm | 1.399 m | 218.3 kg | 24.58 kW |
| HEP-S 26×8.8 | 660.4 mm | 1.590 m | 194.1 kg | 17.44 kW |
| HEP-S 28×9 | 711.2 mm | 1.681 m | 186.8 kg | 15.29 kW |
| HEP-S 29×11 | 736.6 mm | 1.727 m | 183.8 kg | 14.41 kW |
| HEP-S 30×10.5 | 762.0 mm | 1.782 m | 181.2 kg | 13.63 kW |
| HEP-S 32×11 | 812.8 mm | 1.873 m | 176.7 kg | 12.31 kW |
| HEP-S 34×11.5 | 863.6 mm | 1.964 m | 173.0 kg | 11.23 kW |
| HEP-S 36×12 | 914.4 mm | 2.054 m | 170.0 kg | 10.32 kW |
| HEP-S 42×16 | 1066.8 mm | 2.317 m | 163.2 kg | 8.32 kW |

**42×16 wird vorrangig weiter untersucht.** Im mittleren Fall sind rund 8,32 kW je Motor erforderlich. Als Vergleich liefert der dokumentierte NS52×20-Prüfpunkt bei 80 % Gas und 10 Minuten rechnerisch 8,916 kW Wellenleistung je Motor. Das ist weder ein universelles Leistungslimit noch eine Freigabe für HEP-S. Bei angenommenen 3000/min braucht 42×16 im Rechenfall einen Schubbeiwert CT≈0,101 und rund 26,50 Nm. Diese Zielwerte muss das echte Kennfeld bestätigen.

**36×12 und 34×11.5 sind nachrangige Kandidaten** für kürzere Flugzeit, eine günstigere geschlossene Masse beziehungsweise höhere belegte Dauerleistung. 18–32 Zoll werden im betrachteten 5-Minuten-Fall zunächst zurückgestellt: Der Leistungsbedarf und teilweise die erforderlichen Schubbeiwerte liegen deutlich höher. Das ist eine Auswahlpriorität aus Annahmen, kein allgemeines Verbot dieser Propeller. Alle Größen bleiben für den Vergleich auswählbar.

Die nominale Steigung ist dokumentiert, geht aber ohne Herstellerkennfeld nicht als erfundene Leistungsverbesserung in die Rechnung ein. CT wird nach T=CT·ρ·n²·D⁴ berechnet, n in Umdrehungen pro Sekunde. Die angegebene 3000/min-Drehzahl ist ein Vergleichspunkt, kein nachgewiesener MN1330-Lastpunkt. Die ideale 24S-Leerlaufgrenze bleibt 4032/min bei vollem Akku, unter Last weniger.

[Studie und Annahmen](Ausgabe/Propeller_Studie.json) · [Vergleich CSV](Ausgabe/Propeller_Vergleich.csv)

## Rotorfreiraum

Alle nominalen Rotorhüllen frei: **True**. Die Mindest-Halbachsweite beträgt 420 mm; deshalb teilen 18 und 22 Zoll den kürzesten mechanisch verwendeten Auslegerstand. Die automatische Achsposition berücksichtigt mindestens 20 mm Planungsabstand zu einem konservativen Rahmen-Rechteck bei Rotorhöhe und mindestens 20 mm Abstand benachbarter Rotorkreise. Tatsächlich liegen die ausgewählten Achsabstände teilweise darüber. Die vollständige Prüfung verwendet die nativen Bauteile und sämtliche 40 Kombinationen einschließlich Kabelrouten.

Geprüfte Annahme: Ringraum von r80 mm bis zum gewählten Außenradius, z124 bis184 mm. Der innere Nabenbereich ist nicht freigegeben. Der Fußverstellbereich bleibt durch Z-Trennung oberhalb dieser Hülle. Die frühere breite untere Endknotenplatte wurde bereits in D08 auf einen 28-mm-Steg zurückgenommen; ihre oberen Anschlüsse bleiben erhalten.

**Eine Garantie für Freilauf unter Last ist noch nicht möglich.** Es fehlen die tatsächliche HEP-S-Umhüllung, Blattverformung, Naben-/Zentriergeometrie, Lagerbewegung, Rahmenverformung und Fertigungstoleranzen. Die 20 mm sind eine Planungsreserve, keine belegte Summe dieser Einflüsse. Die große 42-Zoll-Konfiguration ist rund 2,317 m breit und passt damit nicht in die frühere 1,70-m-Hülle. Schutzraum kommt zusätzlich hinzu.

[40-fache Rotorraumprüfung](Ausgabe/Freiraum_Pruefung.json) · [Statische Verbindungs-/Kabelprüfung](Ausgabe/Integration_Pruefung.json) · [Native Umschalterprüfung](Ausgabe/Umschalter_Pruefung.json)

## Struktur und Klemmung

Die Balken-/Klemmrechnung wurde auf die tatsächlichen neuen Rohrendpunkte aller Größen angepasst. Vergleich: 175 kg, E=70 GPa, G=5 GPa, starre Knoten; Motorreaktionsmoment aus dem Leistungsbedarf bei angenommenen 3000/min.

| Variante bei 42 Zoll | Vertikale Motorauslenkung | Rohrspannungs-Screening | Bewegungsschranke starrer Rotorpunkte |
|---|---:|---:|---:|
| V1 | 23.99 mm | 217.5 MPa | 54.60 mm |
| V2 | 5.25 mm | 119.4 MPa | 29.86 mm |
| V3 | 71.26 mm | 370.6 MPa | 159.56 mm |
| V4 | 5.23 mm | 96.0 MPa | 6.68 mm |

Die Bewegungsschranke kombiniert Translation und Verdrehung des ideal starren Rotors; Blattverformung und reale Knoten fehlen. V2 zeigt trotz ähnlicher Vertikalsteifigkeit mehr seitliche Bewegung/Verdrehung als V4. Bei großen V3-Auslenkungen wird außerdem die Kleinverformungsannahme des linearen Modells fragwürdig. V3 ist bei großen Durchmessern im Vergleich zu den Abständen deutlich zu nachgiebig. V4 ist die bevorzugte weitere Prüfkonfiguration, aber nicht freigegeben. Der Nachweis enthält Sensitivitäten für E/G und Lastfaktoren sowie erforderliche Klemm-Normalkräfte bei verschiedenen Reibwerten. Die Spannungen sind isotrope Balkengrößen, keine CFK-Laminatfestigkeiten. Es fehlen die reale Kontaktpressung/Schlupfprüfung, Aluminiumknoten-FEA, Gesamtframe-/Fußschienensteifigkeit, Schraubenvorspannung, Ermüdung, Moden und validierte Werkstoffkennwerte.

[Struktur-/Klemmrechnung](Ausgabe/Struktur_Klemmnachweis.json)

## Verkabelung und weitere offene Punkte

Je Durchmesser werden 26 Leitungsentwürfe aktiviert: vier DC-Paare, zwölf Motorphasen, vier Signalhüllen und ein Haupt-DC-Paar. Leiter und Isolierung sind getrennte Volumenkörper. Die Phasenrouten verlängern sich mit den Auslegern und enden unter den Motoren an ausdrücklich offenen Plananschlüssen. Die in D08 gefundenen Durchdringungen mit V4 wurden durch tiefer geführte Phasenleitungen korrigiert; der neue Stand wird erneut geprüft.

Statische Integration aller Größen bestanden: **False**. Grenzwert 0,1 mm³. Querschnittsannahmen: DC-Abzweige 35 mm², Phasen 25 mm², Hauptleitungen 95 mm². Die Signalhüllen sind kein konfektionierter Kabelsatz. Kabelclips, Stecker/Kabelschuhe, Motorleitungsübergänge, Regler, Akku, Verteiler, Sicherungen und Schütze fehlen. Deshalb besteht weiterhin keine geschlossene elektrische Baugruppe. Strombelastbarkeit, Kühlung, Phasenstrom und Schutzkoordination sind nicht nachgewiesen.

[Leitungsdaten](Ausgabe/Kabelbaum.json) · [Von-nach-Liste](Ausgabe/Kabel_Von_Nach.csv) · [DC-Verlustrechnung](Ausgabe/Elektrische_Auslegung.json)

Benötigte nächste Herstellerdaten: HEP-S-Kennfelder mit konkretem MN1330/Regler/Spannungsstand, CW/CCW, zulässige Drehzahl, Blatt-/Nabenmassen und Trägheiten, Anschlusszeichnung/STEP, Blattverformung und Lastgrenzen; weiterhin Motor-Lagerlasten/Gewindetiefen und CFK-Laminat-/Klemmdaten.

## Reproduktion

FreeCAD 1.0, NumPy, Matplotlib; für Browserprüfung Playwright/Chromium. Aus dem Projektstamm in dieser Reihenfolge:

```sh
python3 quad_r380_d09/propeller_studie.py
python3 quad_r380_d09/struktur.py
/usr/bin/python3 quad_r380_d09/aufbau.py
/usr/bin/python3 quad_r380_d09/fertigstellen.py
/usr/bin/python3 quad_r380_d09/freiraum_pruefen.py
/usr/bin/python3 quad_r380_d09/integration_pruefen.py
python3 quad_r380_d09/elektrik.py
/usr/bin/python3 quad_r380_d09/viewer_export.py
python3 quad_r380_d09/diagramme.py
python3 quad_r380_d09/dokumentieren.py
node quad_r380_d09/viewer_pruefen.cjs
```

Die lokale Geometrie-Zwischenspeicherung unter `Cache/` ist an Konfigurationsparameter gebunden. Bei Änderungen des Geometriealgorithmus Cache löschen oder Algorithmusversion erhöhen. Die native Datei enthält alle Formen und benötigt zum Umschalten keine Python-Skripte. Die Geometrie ist kein vollständiger Featurebaum für beliebige Maßänderungen.

Abhängigkeiten: D08-Eingangsbaugruppe und Instanzlisten, D07-Kerngeometrie/Parameter/Geometriehelfer, ursprüngliche Variantenliste, D06-Oberflächen unveränderter Bauteile. Der neue Stand ersetzt keine fehlenden Herstellerfreigaben durch CAD-Prüfergebnisse.
