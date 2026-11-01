# P13 – Ergebnis und offene Mechanik

Die Motorzeichnung wurde übernommen. Lagerung, Pitchwellen/-hebel, CFK-Flügelteile,
Taumelscheiben, Aktorfüße, Fachwerke, Deck und Fahrwerk sind geometrisch ergänzt.
Der Stand ist ein technischer Anfrageentwurf. **Die Mechaniklücken sind noch nicht
vollständig geschlossen; dies ist kein bestellfähiger Endstand.**

## Abgeschlossene Prüfungen

- 4780 native Körper / 303 aktive Geometrietypen: jeweils gültiger einzelner Volumenkörper.
- 1120 obere/untere Rotorbauteilpaare: Spiegellage und Volumen geprüft.
- Schnittstellenverweise: 0 fehlende Bauteilreferenzen.
- 16931 räumlich überlappende Kandidatenpaare per BRep-Schnitt geprüft:
  **32 tatsächliche Überschneidungen größer0.01mm³ bleiben offen.**
- Idealisierter Gelenkschluss über6912 Stellungen bestanden; Aktorhub−5.143..+3.148mm
  innerhalb12mm. Scherenreichweite geprüft. Keine vollständige Bewegungskollisionsprüfung.
- Analytische Spiegeloperation mit9 unabhängigen Form-/Lagefällen geprüft.

## Wesentliche Zielkonflikte

Identifizierbare gefertigte Metallteile ergeben bei angenommenen Nenndichten
**125.6kg**. Kaufteile, Energieversorgung und CFK sind darin
nicht vollständig enthalten. Mit100kg Person ergeben allein diese Metallteile bereits
225.6kg; das150kg-Gesamtszenario wird damit verfehlt.
Die beiden massiven Außenringe tragen rund35.7kg bei. Der CFK-Volumenscreen ergibt
18.4kg bei angenommener Dichte1600kg/m³; dies ist keine Laminat-Massenfreigabe.

Die tatsächliche Hülle beträgt1810×1784×1067mm. Die bisherigen Grenzwerte
2100×1700×600mm werden inY undZ überschritten.

## Verbleibende geometrische Konflikte

Die offenen Schnitte betreffen die Scherenführung, den Taumelträger und benachbarte
Fachwerkpylone. Ein gemeinsamer Bauraumentwurf dieser Baugruppen ist erforderlich;
weitere kleine Freistiche ersetzen keine tragfähige Anordnung. Jeder Schnitt ist in
`Ausgabe/Kollisionen.json` mit Instanznamen und Schnittvolumen dokumentiert.

| Betroffene CAD-Typen | Paare | größter Schnitt mm³ |
| --- | ---: | ---: |
| P13-FACHWERK-PYLON / STD-ISO7089-M6-GELENK | 6 | 70.065 |
| P13-FACHWERK-PYLON / STD-DIN1444B-6x35 | 4 | 274.721 |
| P13-TAUMEL-AUSSEN / P13-TAUMEL-INNEN | 2 | 360.000 |
| P13-FACHWERK-PYLON / P13-FACHWERK-PYLON-MITNEHMER | 2 | 321.880 |
| P13-SCHERENLASCHEN / P13-TAUMEL-AUSSEN | 2 | 110.530 |
| P13-FACHWERK-PYLON-MITNEHMER / P13-SCHERENLASCHEN | 2 | 109.970 |
| P13-FACHWERK-PYLON / P13-SCHERENDISTANZ-6 | 2 | 40.150 |
| P13-TAUMEL-AUSSEN / STD-GE6-AUSSEN | 2 | 11.751 |
| P13-FACHWERK-PYLON / STD-DIN94-1.6 | 2 | 8.157 |
| P13-TAUMEL-AUSSEN / STD-DIN472-14 | 2 | 4.421 |
| P13-FACHWERK-PYLON-MITNEHMER / STD-DIN1444B-6x35 | 2 | 1.238 |
| P13-FACHWERK-PYLON-MITNEHMER / P13-TAUMEL-AUSSEN | 2 | 1.101 |
| P13-FACHWERK-PYLON / P13-SCHERENDISTANZ-2 | 2 | 0.492 |

## Exportgrenze

Der Gesamt-STEP liefert beim erneuten Einlesen4782 statt4780 Körper. Er wird
deshalb nicht ausgeliefert. Die native FreeCAD-Baugruppe und Einzel-STEP-Dateien
stehen zur Prüfung bereit. Alle395 Einzel-STEPs lassen sich als jeweils ein
gültiger Körper einlesen. Bei den beiden Außenring-Varianten bleibt der
Volumenvergleich außerhalb der gesetzten0.01%-Prüfgrenze:0.182% bzw.0.073%.
Diese STEP-Dateien sind ausdrücklich Prüfgeometrie; für diese Ringe vor
Fertigungsfreigabe Konturen und Rückimport gegen die native Geometrie prüfen.
Einzelteilprüfung und Exportdiagnose sind separat
dokumentiert; ein fehlerhafter Gesamtexport wird nicht als bestanden ausgegeben.

## Beschaffung und Fertigung

Normteilfamilien und Sonderteile sind getrennt. Konkrete Lieferkonturen und
Tragzahlen müssen abgeglichen werden. `RFQ_Fertigungsvarianten.csv` enthält die
STEP-Variantenmengen; `Beschaffungsfamilien.csv` fasst geteilte CAD-Lagerringe und
Gelenkköpfe zu vollständigen Kaufbaugruppen zusammen.

Die57 Ansichtsblätter sind Anfragezeichnungen. CFK-Laminat, Klebungen,
Passungen, Vorspannungen, Schraubensicherungen, Festigkeit und Ermüdung bleiben
freizugeben. Aktor-Riemenspannung, Klemmnaben, Endlagen und Halteverhalten sind
Dienstleisteranforderungen. Motor-Gewindetiefen wurden mangels Bemaßung als
Montageannahmen geführt; elektrische Stecker/Pinbelegung sind nicht abgeleitet.

Priorität für die weitere Konstruktion: Masse-/Bauraumkonzept überarbeiten,
Scheren und Pylone gemeinsam anordnen, reale Aktor-/Lagerbaugruppen integrieren,
danach alle statischen und bewegten Freigänge erneut prüfen.
