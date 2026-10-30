# Kreis R04 – Varianten mit und ohne Außenring

> **REKONSTRUKTION vom 30.10.2026.** Der ursprüngliche R04-Stand lag in einer nicht mehr erreichbaren Cloud-Umgebung und wurde nie nach GitHub übertragen. Dazu gehörten FCStd/STEP-Dateien, berichtete Massen-, Struktur- und CFD-Ergebnisse sowie CFD-Rohfälle. Alle Dateien hier wurden neu erstellt oder neu berechnet. Frühere Werte stehen nur in [docs/R03_R04_Rekonstruktion.md](../docs/R03_R04_Rekonstruktion.md), dort als „berichtet, nicht verifiziert“ gekennzeichnet.

## Inhalt und Bearbeitungsstand

| Datei | Inhalt | Stand |
|---|---|---|
| [profil.py](profil.py) | Gemeinsame Geometrie: Kreisbahn, NACA 0012 + 0,4·q¹⁰ mm je Seite (Hinterkante 0,8 mm), R02-Innenkontur | ausgeführt |
| [balken.py](balken.py) | Euler-Bernoulli-Balkenmodell der Pitchwelle | ausgeführt |
| [Struktur_Referenz.json](Struktur_Referenz.json), [Struktur_Sweep.csv](Struktur_Sweep.csv) | 208 Parameterfälle, 8 Diskretisierungsfälle, 6 analytische Prüfungen | erzeugt |
| [cad_erstellen.py](cad_erstellen.py) | Beide FreeCAD-Varianten aus `kreis_r03/Kreis_R03_Layout.FCStd`, Flügelprüfung, Volumen | ausgeführt (FreeCAD 1.0.2) |
| [Kreis_R04_Aussenring.FCStd](Kreis_R04_Aussenring.FCStd) / [.step](Kreis_R04_Aussenring.step) | 1 744 Körper | erzeugt |
| [Kreis_R04_ohne_Aussenring.FCStd](Kreis_R04_ohne_Aussenring.FCStd) / [.step](Kreis_R04_ohne_Aussenring.step) | 948 Körper (796 entfernt, 16 Hüllen umgesetzt) | erzeugt |
| [CAD_Pruefung.json](CAD_Pruefung.json), [CAD_Volumen.csv](CAD_Volumen.csv) | Flügelprüfung, Volumen und Massen je Bauteil-ID | erzeugt |
| [massen_und_anforderungen.py](massen_und_anforderungen.py), [Massen_Szenarien.json](Massen_Szenarien.json)/[.csv](Massen_Szenarien.csv), [Auftriebsanforderungen.csv](Auftriebsanforderungen.csv) | 312 analytische Szenarien | erzeugt |
| [cfd/](cfd/README.md) | Gmsh-Sektornetze, OpenFOAM-Fallgenerator, Auswertung | siehe dort |

## Balkenmodell (neu berechnet)

Stahlwelle Ø 8 mm, L = 640 mm, E = 200 GPa. Nur die Welle trägt. Auftrieb verteilt proportional zu r² über r = 150 … 750 mm. Zentrifugale Zugversteifung wahlweise berücksichtigt; die äußere Lagerung ist axial schwimmend. Flügelschalenmasse aus dem Profilpolygon (CFK 1600 kg/m³): 0,410 kg je Flügel; Welle 0,253 kg.

Referenzfall 50 m/s, vorgeschriebener Gesamtauftrieb entsprechend 200 kg, Zugversteifung, 64 Elemente:

| Variante | max. Durchbiegung | max. nominelle Spannung | Fliehkraft innen |
|---|---:|---:|---:|
| mit Außenring (einfach abgestützt) | 3,54 mm | 123 MPa | 3,68 kN |
| ohne Außenring (Kragarm) | 19,6 mm | 323 MPa | 3,68 kN |

Alle sechs analytischen Euler-Bernoulli-Prüfungen bestanden, maximale relative Abweichung 1,6·10⁻⁴. Die Diskretisierung von 16 bis 128 Elementen ändert die Spannung um weniger als 1 %. Der S355-Wert ist nur ein angenommener Vergleich; das Wellenmaterial ist nicht ausgewählt.

**Kein Festigkeitsnachweis.** Nicht abgedeckt: tatsächliche CFK-Tragwirkung, Fügestellen, Torsion, Ermüdung, Magnetführung, Dynamik und Eigenfrequenzen, Fluid-Struktur-Kopplung sowie die ohne Außenring neu auszulegende Flügelwurzel, Lagerung und Drehmomentübertragung.

## CAD-Varianten (Skript)

- **Mit Außenring:** alle R03-Körper; die Flügelschalen erhalten die neue Außenkontur mit 0,8 mm Hinterkante. Die Innenkontur bleibt die skalierte R02-Kontur und wurde nicht neu ausgelegt. Die CAD-Kontur ist polygonal abgetastet, die Gmsh-Kontur nutzt Splines; beide Flächen sind nur angenähert gleich.
- **Ohne Außenring:** äußere Führungsringe und alle mobilen Körper mit Schwerpunktradius > 600 mm entfernt; Flügelschale und Pitchwelle bleiben. Die Motor- und Encoderhüllen der **unteren** Ebene werden lokal an y = 0 auf die Innenseite gespiegelt. Bei der oberen Ebene zeigt die lokale +y-Achse wegen der Gegenläufigkeit bereits nach innen (`y = z × Bewegungsrichtung`, wie in R02).
- `CAD_Pruefung.json` enthält je Flügel Weltschwerpunkt, Radius, Winkel, Pitch, Ausrichtung und Bewegungsrichtung sowie die Mindestabstände zwischen Nachbarflügeln, zwischen den Ebenen und zu den Führungsringen.

Ergebnis der Flügelprüfung: alle 16 Flügel mit Pitch 12,0°, korrekt radial und tangential ausgerichtet; untere Ebene im, obere gegen den Uhrzeigersinn; Radialbereich 150,0 … 752,3 mm. Exakte Mindestabstände: Nachbarflügel 22,1 mm (im Grundriss an der Wurzel nur ≈ 2,3°), übereinander 211,8 mm, zum Führungsring 9,1 mm (mit) bzw. 13,7 mm (ohne Außenring). Keine Kollision.

Deck, Akkugehäuse und weitere Einbauteile stammen aus R02. Es handelt sich um Konzeptmodelle, nicht um Fertigungsunterlagen.

## Massen und Auftrieb (Skript)

`massen_und_anforderungen.py` summiert die CAD-Volumina mit CFK 1600, Aluminium 2700 und Stahl 7850 kg/m³; Elektroblech wird als Stahl gezählt. Erfasste Modellmasse: **63,23 kg mit, 26,67 kg ohne Außenring** (Differenz 36,56 kg). Referenzbauräume, Magnete, Elektronik, Batterien und die neue Tragstruktur fehlen; das Ergebnis ist **keine Fahrzeugmasse**. Die 312 Fälle ergeben sich aus 13 Geschwindigkeiten (10 … 70 m/s) × 4 angenommenen CL (0,5 / 0,8 / 1,0 / 1,2) × 2 Varianten × 3 frei gewählten Massenszenarien, Person jeweils 100 kg. Induzierte Strömung und Flügelinterferenz sind nicht berücksichtigt; die Ergebnisse sind getrennt von CFD zu behandeln. `allowable_payload_kg` bleibt `null`.

## Erzeugung

```sh
python profil.py
python balken.py                                         # numpy
FREECAD_LIB=/pfad/zu/freecad/lib python3 ../kreis_r03/erstellen.py
FREECAD_LIB=/pfad/zu/freecad/lib python3 cad_erstellen.py
python massen_und_anforderungen.py
```
