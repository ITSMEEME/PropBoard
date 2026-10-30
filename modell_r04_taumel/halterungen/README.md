# FC/ESC- und Akkuhalter H01

**Geometrie- und Montageentwurf, keine Festigkeits-, Temperatur- oder Betriebsfreigabe.** Der vorhandene F01-Rotor wird unverändert übernommen. Die beiden Kappen und das Mittelrohr werden in der neuen Gesamtbaugruppe durch die H01-Anschlussgeometrie ersetzt. Das ursprüngliche F01-Paket bleibt unverändert.

- [Vorschau](Ausgabe/Vorschau_H01.png)
- [Gesamtbaugruppe FreeCAD](Ausgabe/R04_Taumelmodell_Halterungen_H01.FCStd) / [STEP](Ausgabe/R04_Taumelmodell_Halterungen_H01.step)
- [7-seitiger Zeichnungssatz](Ausgabe/Halterungen_H01_Zeichnungen.pdf)
- [Einzelteile](Ausgabe/Einzelteile/), [STEP](Ausgabe/STEP/), [STL](Ausgabe/STL/)
- [Stückliste](Ausgabe/Stueckliste_H01.csv), [Validierung](Ausgabe/Validierung_H01.json)
- [Montage- und Fertigungshinweise](Ausgabe/Fertigungshinweise.md)
- [Mechanikprüfung und Servobewertung](../mechanik/README.md)

## Übernommene Maße

Die vom Nutzer bereitgestellte SpeedyBee-Zeichnung gibt FC 39 × 39 mm, Bauhöhe 4,9 mm, ESC 40,9 × 44,9 mm, Bauhöhe 8 mm und jeweils 1,6 mm Leiterplattendicke an. Das vorhandene 30,5 × 30,5-mm-Lochbild wird verwendet; in der Abbildung ist die horizontale Teilung angegeben. Der senkrechte Abstand folgt der bisherigen Stack-Spezifikation. Die Abbildung spezifiziert keine Dämpfer-, Lochdurchmesser oder exakte Bauteilverteilung ober-/unterhalb der PCB.

Der Akku ist nach Nutzerangabe **78 × 37 × 52 mm, 254 ±20 g, 1550 mAh, 6S/22,2 V, 150C, XT60 und JST-XHR**. Der C-Wert ist eine übernommene Produktangabe, kein verifizierter Belastbarkeitsnachweis.

## Öffnen und ändern

In FreeCAD 1.0.2 `Halterungen_oeffnen.FCMacro` ausführen; dadurch sind die lokalen Python-Features bekannt und die reservierten Kabelzugangsräume werden ausgeblendet. Einzelteile besitzen die editierbare Eigenschaft **ParameterJSON** am Objekt **Bauteil**. Änderungen neu berechnen. Die Hüllmaßbezüge folgen dem Teil. Textliche Nennmaßtabellen und Exporte sind Momentaufnahmen und müssen für eine neue Revision gemeinsam neu erzeugt werden. Die Gesamtbaugruppe folgt separat bearbeiteten Einzelteilen nicht automatisch.

Erzeugen aus dem Repository:

```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/halterungen/erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/halterungen/pruefen.py
.cfd-tools/venv/bin/python modell_r04_taumel/halterungen/pdf_erstellen.py
```

PDF-Export benötigt svglib/reportlab sowie DejaVu Sans. Für Körperneuberechnung ist das mitgelieferte Modul `halterungen_features.py` erforderlich; die gespeicherten BReps bleiben ohne Neuberechnung sichtbar.
