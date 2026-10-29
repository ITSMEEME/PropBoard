# Vergleich der Anordnungen

| Eigenschaft | Bisherige Variante | Neue Vergleichsvariante |
| --- | --- | --- |
| Bahnebenen | vertikal, x-z | horizontal, x-y |
| Lage der beiden Bänder | nebeneinander, y = ±500 mm | übereinander, z = ±120 mm |
| Flügel | 2 × 8, NACA 0012 | 2 × 8, NACA 0012 |
| Sehne / Spannweite | 120 / 600 mm | 120 / 600 mm |
| Summe geometrischer Flügelflächen | 1,152 m² | 1,152 m² |
| Gerader Bahnabschnitt | 1300 mm | 500 mm |
| Mittlerer Umlenkradius | 180 mm | 450 mm |
| Spannweitenrichtung | quer zum Fahrzeug, y | radial zur Bahn in x-y |
| Pitch-Vorgabe | 12° × Tangente_x im x-z-Schnitt | Nase 12° über horizontaler Geschwindigkeit |
| Achse des nominellen Umlauf-Drehimpulses | y | z |
| Vollständige 3D-CFD | fehlt | fehlt |

Die Summe der Flügelflächen ist keine unabhängig durchströmte Rotorscheibenfläche und darf nicht in das frühere Rotor-Schwebemodell eingesetzt werden. Beim Stapel überlagern sich die Arbeitsbereiche in der Draufsicht.

Die Ovalmaße und die Pitch-Vorgabe mussten für die neue Anordnung geändert werden. Deshalb ist dies ein Vergleich zweier Konzeptvarianten, kein isolierter Test einer einzigen geometrischen Variable. Die neue CAD-Momentaufnahme misst 2056 × 1564 × ungefähr 422 mm; die alte ungefähr 1707 × 1664 × 493 mm. Beide enthalten neue Strukturannahmen und keine geschlossenen Massennachweise.

Bei derselben rein illustrativen Umlaufgeschwindigkeit von 10 m/s ergibt `v²/r` ungefähr 556 m/s² bei 180 mm Radius bzw. 222 m/s² bei 450 mm Radius. Das entspricht rund 57 bzw. 23 g für den Schwerpunkt auf der jeweiligen mittleren Bahn. Diese Zahlen sind kinematische Beschleunigungen, keine nachgewiesenen Lagerlasten. Flügelmasse, Schlittenmasse, Eigenrotation, Pitch-Bewegung und Lastverteilung fehlen.

Der lokale Strömungsversuch in `results/Vergleichsbericht.md` prüft ausschließlich zwei gerade, übereinanderliegende Flügelreihen. Er liefert keine Rangfolge der vollständigen Fahrzeugvarianten. Für diese Rangfolge fehlen insbesondere realmaßstäblicher 3D-Schub, Antriebsleistung, Führungsverluste, Strukturmasse und ein gemeinsames Missionsprofil.
