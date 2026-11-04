from pathlib import Path
import json
H=Path(__file__).resolve().parent;O=H/'Ausgabe';r=json.loads((O/'Status.json').read_text());m=json.loads((O/'Massenvergleich.json').read_text());p=json.loads((O/'Gewindepruefung.json').read_text());c=json.loads((O/'Bauraum_Pruefung.json').read_text())
plate_mass=sum(x['mass_kg'] for x in m['removed'] if x['id'] in ['D02_CENTRAL_TOP','D02_CENTRAL_BOTTOM'])
s=f'''# Quad R380 D04 – Carbon-Zentralrahmen

Die beiden großen Zentralplatten sind vollständig entfernt. Der zentrale Lastpfad besteht nun aus zwei Carbon-Rohrkränzen und vier senkrechten Carbonrohren, verbunden durch kompakte Aluminiumknoten. Die oberen Schienenstreben sitzen auf zwei geteilten Rohrklemmen mit Isolierlagen. Es gibt keine Bohrung durch die Carbonrohre.

**CAD-Masse: {m['d04_mass_kg']:.3f} kg statt {m['d03_mass_kg']:.3f} kg. Nettoersparnis {m['saved_kg']:.3f} kg beziehungsweise {m['saved_percent']:.1f} %.** Das schließt die zusätzlichen Rohre, Knoten, Klemmen und Schrauben ein. Gleicher mechanischer Umfang wie D03; Antrieb, Akku, Kabel, Schutz und Fahrwerk fehlen in beiden Ständen. Nominalvolumen und angenommene Dichten, keine Wägung oder Belastungsfreigabe.

- [Interaktive CAD-Ansicht](Mechanik.html) · [Carbon-Mitte im Detail](Carbon_Mitte.png)
- [Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D04_CFK.FCStd) · [STEP-Baugruppe](Ausgabe/QuadR380_D04_CFK.step)
- [Gesamtpaket](QuadR380_D04_Detailpaket.zip) · [Stückliste](Ausgabe/Stueckliste.csv)
- [Vollständige Massenänderungsliste](Ausgabe/Massenvergleich.json)
- [Gewindeprüfung](Ausgabe/Gewindepruefung.json) · [Bauraum/Verstellung](Ausgabe/Bauraum_Pruefung.json) · [Exportprüfung](Ausgabe/Export_Pruefung.json)

## Gewicht und Lastpfad

| Vergleich | CAD-Masse |
|---|---:|
| D03 mechanische Baugruppe | {m['d03_mass_kg']:.3f} kg |
| Entfallene Zentralplatten allein | {plate_mass:.3f} kg |
| D04 mechanische Baugruppe einschließlich Ersatzkonstruktion | {m['d04_mass_kg']:.3f} kg |
| Nettoersparnis | {m['saved_kg']:.3f} kg / {m['saved_percent']:.1f} % |

Die neue Mitte enthält zwölf CBU20171005TG-Zuschnitte Ø20/17 mm: acht horizontale Rohre und vier senkrechte Rohre. Obere/untere Knotenmitten liegen bei z=±110 mm und radial145 mm. Die schmalen, verrippten Aluminiumkappen greifen an den bestehenden M6-Gewinden der Auslegerschotte an. Die P12-Flanschklemmhälften und Isolierlagen werden weiterverwendet. Die Portlochbilder der neuen Knoten und die Einbaulage der Klemmen sind um45° abgestimmt, damit die rechtwinkligen Sacklochgruppen sich nicht überkreuzen. Für diese Anschlüsse sind ISO4762 M4x10 mit passend modellierten M4-6H-Gewinden vorgesehen.

Die bisherigen vier Strebenfüße benötigen keine Grundplatte mehr. Zwei gemeinsame, geteilte Aluminiumsättel greifen direkt um die oberen Carbonrohre. Je Sattel halten drei versetzt angeordnete M6x45-Schrauben Ober- und Unterhälfte zusammen. Die Schraubenachsen bleiben außerhalb des Carbonquerschnitts und frei von den schrägen Anschlusskegeln. Die Winkel der vier Fußschienen-Streben und deren obere Metallknoten sind angepasst, ihre Rohre neu zugeschnitten. Metallflächen werden durch angepasste Isolierlagen vom CFK getrennt.

Die Fußplatten, das10-mm-Raster und die versenkten Fußschrauben aus D03 bleiben erhalten. Der Mittenabstand der Fußplatten ist weiterhin260–500 mm. Die äußeren Auslegerrohre und ihre P12-Klemmen bleiben erhalten. Insgesamt sind nun34 Carbonrohrzuschnitte verbaut.

## Prüfungen und Grenzen

- {len(p['pairs'])} nominale Gewindepaarungen im dokumentierten Prüfbereich bestanden. Unveränderte Nachweise dürfen nur bei identischen Master-BRep-Hashes und identischer relativer Lage wiederverwendet werden. Geänderte Klemmen und Verschraubungen wurden neu geprüft.
- Statische Prüfung: Strukturkörper plus das vollständige Fußsystem und die neuen/überarbeiteten Schrauben im aufgeführten Prüfbereich. {c['static_candidates']} Kandidatenpaarungen; {c['static_interference_count']} Überschneidungen über0,1 mm³.
- Fußverstellung: {len(c['travel_cases'])} Zustände, beide Füße mit allen13 Rasterpositionen und je zwei Indexierschrauben-Endstellungen gegen sämtliche festen Nachbarkörper geprüft. Insgesamt {c['total_interference_count']} gemeldete Überschneidungen. Weitere alte ISO-Verbindungen bleiben außerhalb der globalen statischen Prüfung.
- Alle verwendeten nativen Prototypen sind gültige Einzelkörper. STEP wird wieder eingelesen und die Zahl der Körper geprüft; keine zusätzliche Einzelkörper-Gültigkeitsprüfung des STEP-Rückimports behauptet.

Die räumliche Rohrkonstruktion ist ein neuer Lastpfad. Es liegen noch keine nachgewiesenen CFK-Kennwerte, Klemmpressungen, Reib-/Kriechwerte, Knick-, Biege-, Torsions-, Ermüdungs- oder Schwingungsnachweise vor. Starre nominale Kollisionsfreiheit ersetzt diese Nachweise nicht. Der untere Carbonrahmen liegt tiefer als die frühere Platte; Bodenfreiraum und ein passendes Landegestell sind neu zu schließen. Anzugsmomente und Personenlasten sind nicht freigegeben.

Die ursprünglichen P12-Klemmteile besitzen teilweise nur Gewindekernkonturen. Diese alten Queranzugs-/Armverbindungen sind nicht pauschal als geprüft oder fertig ausgeführt deklariert. Antrieb, Batterie, Kabelbaum, Kühlung, Schutz und Fahrwerk sind weiterhin offen; der gelieferte Kenndaten-Extrakt enthält keine verbindlichen OEM-Anschlusszeichnungen oder STEP-Modelle.

## Reproduktion

`normteile_erstellen.py` wird nur zur Neugenerierung der zwei zusätzlichen Normteile benötigt; die BReps, Tabellen und Lizenz liegen bei. `bauen.py` erstellt D04 aus der unveränderten D03-Eingangsbaugruppe. Danach `gewinde_pruefen.py`, `bauraum_pruefen.py`, `ableiten.py`, `viewer_pruefen.cjs` und `dokumentieren.py` ausführen. Die Skripte `sattel_korrigieren.py`, `sattel_freiraum.py` und `rohrsitz_fertigbohren.py` dokumentieren die iterativen Korrekturen und sind beim Neuaufbau nicht nötig; alle Korrekturen sind bereits in `bauen.py` enthalten.

Das Paket enthält die benötigte D03-Baugruppe und deren Teile-/Instanz-/Gewinderegister, die Normteilbibliotheken, Original-P12-Klemmquellen und den vorhandenen unbestätigten Kenndaten-Extrakt. FreeCAD mit PartDesign/MeshPart, Node/Playwright und Chromium erforderlich. Gepinnte Fasteners-Version: `fddd07af422b7d3a69098b32333711c5eeae184c`. Material- und Festigkeitsangaben sind Beschaffungsanforderungen, keine Lieferzertifikate.
'''
(H/'README.md').write_text(s)
print('Documentation updated; net saving',m['saved_kg'])
