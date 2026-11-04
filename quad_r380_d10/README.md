# Quad D10 – Innenverkabelung und materialreduzierte Aufnahmen

[Native CAD-Datei](Ausgabe/Quad_HEPS_Innenverkabelung.FCStd) · [3D-Ansicht](Projekt.html) · [Kabelprüfung](Ausgabe/Innenverkabelung_Pruefung.json) · [Materialvergleich](Ausgabe/Materialvergleich.json) · [Diagramm](Ausgabe/Materialreduzierung.pdf)

Die bisherigen V1–V4 bleiben erhalten. V5 ergänzt vier Carbonrohre. Die zehn Propellergrößen ergeben mit den fünf Varianten50 vorberechnete Stellungen. In FreeCAD: Variantensteuerung → Daten → Propeller beziehungsweise Variante. In FreeCAD blendet CarbonAuslegerAnzeigen die Auslegerrohre aus. Im Viewer lassen sich die Carbonrohre ebenfalls ausblenden, um die Innenleitungen zu sehen.

## Kabelkonzept

Die langen DC-Zuleitungen sind in die Ausleger verlegt; dafür müssen die Regler nahe den Motoren angeordnet werden. Regler und deren Halter sind noch nicht als konkrete Kaufteile integriert. Die kurzen Motorphasen am Motor und die Hauptversorgung sind in dieser Revision nicht vollständig modelliert. Damit gibt es noch keinen anschlussfertigen Kabelbaum.

V1 verwendet weiterhin den noch nicht herstellerseitig belegten Ø35/32-Rohrentwurf; V2–V5 verwenden Ø20/17. V1: beide35-mm²-DC-Leiter und Signalhülle im Ø35/32-Rohr. V2/V3: je eine DC-Leitung im Ø20/17-Rohr, Signal zusätzlich im Plus-Rohr. V4/V5: Plus und Minus in getrennten Rohren, Signal im dritten; bei V5 bleibt das vierte Rohr frei. Leiter und Isolierung sind getrennte Körper. Rohrwände wurden nicht quer angebohrt.

Neu sind axiale Kabeldurchgänge in den Aluminiumaufnahmen, ringförmige Endpolster und0,3mm dicke Innenliner (Werkstoffannahme PTFE) mit0,1mm nominalem radialem Abstand zum Carbon. Rahmenseitig stehen30mm und motorseitig4mm gerade Leitungsstücke heraus; Anschlüsse, reale Biegeradien und Zugentlastungen müssen noch konstruiert werden.

Prüfung der tatsächlichen CAD-Zylinderachsen und Radien: **True**, 1200 Einzelprüfungen. Kleinster nominaler Abstand zwischen Kabelmantel und Linerinnenfläche: **0.100mm**. Diese knappe Belegung bei zwei Rohren ist nicht toleranzfreigegeben. Kabel-OD12mm (35mm²) und Signalhülle4mm sowie der Rohr-ID sind bislang Nenn-/Entwurfswerte. Signal ist eine Ersatzhülle, kein konfektionierter mehradriger Kabelsatz.

Die bisher geplanten18-mm-Hauptleitungen passen nicht durch17mm Rohr-ID. Sie werden hier nicht fälschlich als intern verlegt ausgewiesen. Für die Hauptversorgung ist eine gesonderte Trasse oder eine vollständig neu geprüfte Leitungsaufteilung nötig. Motornahe Regler benötigen zusätzlich eine Freigabe der DC-Leitungslänge und gegebenenfalls zusätzliche Zwischenkreiskondensatoren. Strombelastbarkeit, Kühlung in den CFK-Rohren, EMV, Isolationsfestigkeit und Abriebfestigkeit sind nicht freigegeben.

## Weniger Aluminium

Die Wurzelknoten erhalten eine zentrale12-mm-Durchgangsbohrung und kleine Durchgangstaschen in den Verbindungsrippen. Klemmflächen und Schraubensitze bleiben im Modell erhalten; zusätzliche axiale Kabelpassagen öffnen die bisherigen Endstopfen. Die Endanschlagauflage ist dadurch kleiner und muss neu auf Pressung geprüft werden. Die Motorträger erhalten zusätzlich Freistellungen für die Statorschraubenköpfe, um die D09-Befunde konstruktiv zu bearbeiten.

| Variante | Rohre je Motor | Wurzel vorher | Wurzel nachher | Ersparnis je Wurzel |
|---|---:|---:|---:|---:|
| V1 | 1 | 325.16g | 292.09g | 33.07g (10.2%) |
| V2 | 2 | 397.72g | 370.36g | 27.37g (6.9%) |
| V3 | 2 | 423.89g | 400.47g | 23.42g (5.5%) |
| V4 | 3 | 537.23g | 506.13g | 31.09g (5.8%) |
| V5 | 4 | 630.11g | 596.87g | 33.24g (5.3%) |

Massenvergleich bei gleicher angenommener Aluminiumdichte2810kg/m³. Vier Wurzelknoten je Gesamtfahrzeug; reine Aluminiumeinsparung an den Wurzelknoten ist viermal der Tabellenwert. Die zusätzlichen Innenliner bringen eigene Masse mit; eine Netto-Gewichtsersparnis des vollständigen Fahrzeugs ist damit nicht nachgewiesen. Dies ist ein geometrischer Materialvergleich, kein Nachweis gleicher Festigkeit oder ein globales Gewichtsoptimum. Für die neuen Taschen, die hohlen Knoten und V5 fehlen Festigkeits-, Kontakt- und Ermüdungsnachweise.

Nominaler Rotor-Hüllraum in allen Größen frei: **True**. Die reale HEP-S-Geometrie, Blattverformung und Freilauf unter Last bleiben unbekannt. Der neue Kabeltest ersetzt keine vollständige statische Anschluss-/Werkzeugzugangsprüfung und keine elektrische Qualifikation. Die gezielte Nachprüfung der Statorschrauben und Motorträger ist mit200 Paaren bestanden. Sie verwendet einen Ausleger je Kombination; die anderen Ecken sind gedrehte Kopien. Schraubenvorspannung, OEM-Gewindetiefe und Tragfähigkeit sind damit nicht bestätigt. [Gezielte Statorprüfung](Ausgabe/Statorfit_Pruefung.json)

## Reproduktion

`/usr/bin/python3 quad_r380_d10/aufbau.py`, danach `fertigstellen.py`, `innen_pruefen.py`, `freiraum_pruefen.py`, `viewer_export.py` und `abschluss.py`. Voraussetzung FreeCAD1.0; Quellen/Abhängigkeiten wie D09 mit eigener `Varianten.json` einschließlich V5. Bei Geometriealgorithmusänderungen Cache invalidieren. Numerische Boolean-Ausweichoperationen bis0,0001mm sind Rechenhilfen, keine Fertigungstoleranzen.

**Keine Produktions- oder Flugfreigabe.**
