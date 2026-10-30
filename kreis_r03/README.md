# Kreis R03 – Umstellung auf eine Kreisbahn

> **REKONSTRUKTION vom 30.10.2026.** Der ursprüngliche R03-Stand (u. a. `Kreis_R03_Layout.FCStd` mit berichteten 1 733 Ergebniskörpern) lag in einer nicht mehr erreichbaren Cloud-Umgebung und wurde nie nach GitHub übertragen. Alle Dateien hier wurden neu erstellt. Berichtete Zahlen aus dem verlorenen Stand sind in [docs/R03_R04_Rekonstruktion.md](../docs/R03_R04_Rekonstruktion.md) getrennt aufgeführt und nicht verifiziert.

Die zwei geraden Abschnitte der R02-Umlaufbahn entfallen (`straight_mm` 500 → 0). Übrig bleibt eine Kreisbahn mit r = 450 mm, zwei Ebenen bei z = ±120 mm, je 8 gegenläufigen Flügeln (600 × 120 mm, Pitch 12°) und Führungen bei r = 130 / 770 mm.

| Datei | Inhalt | Stand |
|---|---|---|
| [grundriss.py](grundriss.py) | Geometrievergleich R02/R03 | ausgeführt |
| [Vergleich.md](Vergleich.md) / [.pdf](Vergleich.pdf) / [.json](Vergleich.json) / [.csv](Vergleich.csv) | Ergebnis des Vergleichs | erzeugt |
| [Grundriss_Vergleich.png](Grundriss_Vergleich.png) / [.svg](Grundriss_Vergleich.svg) | Grundrisse | erzeugt |
| [vergleich_pdf.py](vergleich_pdf.py) | Markdown → PDF (Chrome headless) | ausgeführt |
| [erstellen.py](erstellen.py) | FreeCAD-Layoutmodell aus den gespeicherten R02-Dateien | ausgeführt (FreeCAD 1.0.2) |
| [Kreis_R03_Layout.FCStd](Kreis_R03_Layout.FCStd) / [.step](Kreis_R03_Layout.step) | 1 744 Ergebniskörper, alle gültig | erzeugt |
| [Pruefbericht.json](Pruefbericht.json) | Körperzahlen, Hülle, Wiederöffnung | erzeugt |

`erstellen.py` übernimmt die 102 Ergebniskörper der mobilen R02-Baugruppe 16-fach auf die Kreisbahn, ergänzt geschlossene C-Ringführungen und kopiert die zentralen Einbaureferenzen (Deck, Akku, Fußauflage, Kabelreferenzen) unverändert aus R02. Es ist ein **Layoutmodell**. Rahmenanbindung, Ringhalter, Schutz und Kabelwege sind nicht konstruiert. Das Modell hat 1 744 Ergebniskörper: 1 632 mobil, 24 Ringkörper, 79 zentrale Referenzen und 9 Pilotreferenzen.

## Erzeugung

```sh
python grundriss.py                       # benötigt optional matplotlib für PNG
FREECAD_LIB=/pfad/zu/freecad/lib python3 erstellen.py   # FreeCAD 1.0
python vergleich_pdf.py
```

Die Kennwerte im Vergleich sind geometrisch. Sie sind kein Strömungs- oder Tragfähigkeitsnachweis.
