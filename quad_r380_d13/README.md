# Quad D13 – interner Standard-Kabelbaum

[3D-Ansicht](Projekt.html) · [FreeCAD-Modell](Ausgabe/Quad_Standardkabelbaum.FCStd) · [Schnittstellen und Pinbelegung](SCHNITTSTELLEN.md) · [Pinliste CSV](Ausgabe/Pinbelegung.csv) · [Zuschnitt CSV](Ausgabe/Zuschnitt.csv)

Die internen Kabel und Schutzliner wurden im nativen D12-Modell ersetzt. Alle zehn Propellergrößen und fünf Rohrvarianten bleiben umschaltbar. Rahmen, Motoraufnahmen und Landefüße haben gegenüber D12 identische geprüfte BREP-Geometrien. Die strukturellen Nachweisdefizite aus der [D12-Studie](../quad_r380_d12/Ausgabe/Festigkeit/BERICHT.md) bestehen damit fort.

## Kabelauswahl und Führung

| Netz | Vorgesehener Aufbau | Maximaler Außen-Ø im Entwurf |
|---|---|---:|
| DC+ / DC−, je Leitung | flexibles Silikon, AWG10, nominal 5,26 mm² | 6,0 mm |
| CAN | geschirmt, 2×2×0,25 mm², H/L als 120-Ω-Paar | 6,5 mm |
| PWM | geschirmt, 3×0,25 mm² | 4,2 mm |
| Service | geschirmt, 5×0,25 mm², passiv nummeriert | 6,5 mm |

**Diese Durchmesser sind Beschaffungsobergrenzen, keine gemessenen OEM-Durchmesser.** AWG legt den Leiterquerschnitt fest, nicht den Außendurchmesser einschließlich Isolation. Auch IEC-Steckernormen legen nicht jedes Kaufteilgehäuse fest. Erst ein konkreter Kabeltyp beziehungsweise eine Messung bestätigt die Abmessungen. Der vorhandene OEM-Signalkabel-Ø 4,2 mm gilt für dessen fünfadrige Leitung und wird nicht als Nachweis des neuen PWM-Kabeltyps ausgegeben. Die OEM-Encoderleitung bleibt hinsichtlich Außen-Ø unbekannt.

| Variante | Rohr 1 | Rohr 2 | Rohr 3 | Rohr 4 |
|---|---|---|---|---|
| V1: ein größeres Rohr | DC-Paar, CAN, PWM, Service | – | – | – |
| V2 / V3: zwei Rohre | DC-Paar | CAN, PWM, Service | – | – |
| V4: drei Rohre | DC-Paar | CAN und PWM | Service | – |
| V5: vier Rohre | DC-Paar | CAN und PWM | Service | frei |

Die zusammen geführten DC-Leitungen verkleinern die Stromschleife. In den 20/17-mm-CFK-Rohren liegt ein durchgehender PTFE-Liner mit nominal 16,2 mm Innen- und 16,8 mm Außendurchmesser. Für die Beschaffung wird ein tatsächlicher Liner-Innen-Ø von mindestens 16,0 mm verlangt. Kabel werden vor der Endmontage der außenliegenden Stecker eingezogen. Steckverbinder werden nicht durch die Rohre geführt.

## Ergebnisse der Geometrieprüfung

- Alle 50 Konfigurationen bestehen die nominale Querschnitts- und Längenbudgetprüfung. Kleinster Kabel-Kabel-Abstand: **0,601 mm**, bei V2/V3. Kleinster Abstand Kabel–Liner im nativen Modell: **0,750 mm**.
- 250 native Kabelachsen und Außenradien wurden gegen die zugehörigen Rohre/Liner geprüft; die vollständigen verwendeten Liner-Innenräume sind im untersuchten Wurzel- und Motoranschlussbereich frei. Es wurden keine Durchführungsbohrungen in tragende Teile hinzugefügt.
- Die CAD-Umschaltung wird für alle 50 Stellungen geprüft. [Native Prüfdaten](Ausgabe/Kabel_Pruefung.json), [Planung](Ausgabe/Kabelplanung.json), [Aufbau und unveränderte Strukturgeometrien](Ausgabe/Aufbau.json).

Die Abstände gelten für die festgelegten runden Hüllkonturen. Kabelverformung, Einziehbarkeit unter Reibung, Maßstreuungen der Rohre sowie tatsächliche Biegeradien und Zugentlastungen sind damit nicht freigegeben. Die native Prüfung betrifft die internen Geraden und die angegebenen Anschlusskorridore, keinen vollständig konfektionierten Kabelbaum.

## Längen und verbleibender Einbauumfang

Der interne Abschnitt wird mit 30 mm wurzelseitigem und 4 mm motorseitigem Überstand modelliert. Für DC werden zusätzlich 100 mm am Wurzelanschluss, 300 mm am Motor und 100 mm Montagereserve angesetzt. Die ursprünglichen 1.200-mm-Regler-Eingangsleitungen reichen unter diesem Budget auch beim größten Ausleger; der Anschluss liegt dabei an einem **lokalen Abzweigverteiler an der Armwurzel**. Die zentrale Batteriezuleitung bis dorthin ist ein gesonderter, noch nicht modellierter Leistungsstrang.

Für die neuen Steuer-/Serviceverlängerungen werden je Arm 1.200 mm vorgesehen: interner Abschnitt plus 250 mm wurzelseitig, 50 mm Steckerseite und 100 mm Reserve. Die OEM-Enden mit 500 mm Signal- beziehungsweise 460 mm Serviceleitung verbleiben außerhalb des Rohres beim Regler; ein Budget von 300 mm bis zum Projektadapter ist vorgesehen. Die Adapterpositionen, originalen Kabelaustritte und Außenbögen sind noch nicht geometrisch geschlossen. Längenbudgets ersetzen diesen Nachweis nicht.

## Modellqualität und Grenzen

Kupfer, Isolation und Schirmhüllen sind getrennte Volumenkörper; Steuerleitungen enthalten einzelne Leiter. Verseilung und Schirmgeflecht sind nicht aufgelöst. Kabelmassen beruhen auf modellierten Volumina mit angenommenen Dichten (Kupfer 8.960, Polymer 1.400, PTFE 2.200 kg/m³), nicht auf Lieferanten-Wiegungen. Die Regler-Katalogmasse von 748 g einschließlich OEM-Leitungen wird separat ausgewiesen; neue Kabelvolumina und diese Katalogmasse dürfen nicht pauschal doppelt addiert werden.

**Die Kaufteilgehäuse der neuen Stecker und die äußeren Kabelbögen sind nicht als fertige Baugruppen modelliert.** Es wurden keine vermeintlich maßhaltigen Herstellergehäuse erfunden. Die genormten Steckgesichter und projektierten Einbaureserven sind in der Schnittstellendatei definiert; exakte Artikelnummern und Hersteller-CAD sind noch erforderlich.

Elektrische Dauerstrom-/Temperaturnachweise, EMV, Isolation gegen leitfähiges CFK, Sicherung/Schütz/Vorladung und die OEM-Adapterzuordnung bleiben offen. Die V200A-Angabe 100 A Dauer-Ausgang ist kein belegter 100-A-Batteriestrom oder Kabelbelastbarkeitsnachweis; 200 A gilt nur unter 10 s. Keine Produktions- oder Flugfreigabe.

## Reproduktion

Parameter: [parameter.json](parameter.json). Reihenfolge: `python3 planung.py`, `/usr/bin/python3 bauen.py`, `/usr/bin/python3 pruefen.py`, `/usr/bin/python3 viewer_export.py`, `node viewer_pruefen.cjs` im D13-Verzeichnis. FreeCAD benötigt seine Python-Bibliotheken im Suchpfad, der Browserprüfer Playwright und Chromium. Das native Modell wird aus dem unveränderten D12-Ausgangsmodell erzeugt; Prüfdaten enthalten die zugehörigen SHA-256-Werte. Der Browserprüfer testet die exportierte 3D-Darstellung zusätzlich zur nativen Geometrie.
