# Antriebsstudie: 1–10 Motoren

[Ausführliche Studie als PDF](Studie.pdf) · [HTML](Studie.html) · [Markdown](Studie.md) · [Gesamtpaket mit Rechenskripten und Eingabedaten](Studienpaket.zip)

Verglichen werden klassische Quad-, Hexa-, Okto- und Dekakopter, Rechteckraster,
P14-Koaxialpaare und Mischanordnungen. Jede Motoranzahl von 1 bis 10 ist enthalten.
Die Studie umfasst 2230 Geometrie-/Anordnungsfälle, sechs hypothetische
Motor-Leistungsklassen und 40000 Szenarien zur Unsicherheit der ausgewählten Konzepte.
Ring und Raster verwenden denselben isolierten Rotorbetriebspunkt; ihre Hüllen unterscheiden sich.

Es handelt sich um stationäre BEMT und analytische Auslegungsrechnungen, keine neue
3D-CFD oder validierte Flugleistung. Massen neuer Rahmen, Motor-Dauerkennfelder,
Regelbarkeit, Vorwärtsflug und Ausfallverhalten sind nicht nachgewiesen.
Für den klassischen Zehnerring ergibt das untersuchte Feld keinen zugleich
aerodynamisch und geometrisch zulässigen Fall; das zehnmotorige Raster hat zulässige Fälle.

Die wichtigsten Ergebnisse, Annahmen und Grenzen stehen vollständig in der Studie.
Alle Rohdaten liegen als CSV und JSON bei. Das Paket enthält die kleinen notwendigen
Projektquellen, nicht das vollständige CAD-Projekt.

## Reproduktion

Im Projektverzeichnis (oder im entpackten Paket mit den Verzeichnissen `studie_antrieb`
und `kreis_r04`) ausführen:

```bash
node studie_antrieb/simulieren.cjs
node studie_antrieb/einzelrotoren.cjs
node studie_antrieb/kompakt.cjs
node studie_antrieb/mischanordnungen.cjs
MPLCONFIGDIR=/tmp/propboard-mpl python studie_antrieb/bericht.py
```

Benötigt: Node.js, Python, NumPy, Matplotlib, ReportLab sowie DejaVu Sans unter
`/usr/share/fonts/truetype/dejavu`. Die Berichtsausgabe verwendet einen festen
Zufallsstartwert. `Manifest_SHA256.json` dokumentiert Quellen und Ergebnisse.
