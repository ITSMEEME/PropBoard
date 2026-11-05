# Grundsatzprüfung: Sind 20-mm-Carbonrohre die richtige Wahl?

**Kurzantwort:** Der Durchmesser 20 mm (20/17, 1,5 mm Wand) ist für Quad, Koax und Hexa bis 36″ richtig. Größere Rohre lösen das eigentliche Problem nicht. Dieses Problem ist die **Topologie**: Die D14-Ausleger V1–V3 liegen in einer senkrechten Ebene und sind deshalb seitlich sehr weich. Ihre erste seitliche Eigenfrequenz liegt bei nur 2–8 Hz, unabhängig davon, ob 20- oder 40-mm-Rohre verbaut sind. Das liegt mitten im Arbeitsbereich der Flugregelung.

Abhilfe schafft ein räumliches Fachwerk. Dabei läuft ein zusätzlicher Obergurt (R3) oder ein Ober- und Untergurt (R4) zum benachbarten Rahmeneckknoten, an dem schon die Laschen des Dreiecksverbinders sitzen. So steigt die seitliche Eigenfrequenz auf das 4- bis 5-Fache, mit unverändert 20-mm-Rohren und etwa 0,25 kg Mehrgewicht je Ausleger.

Für 42″ an Hexa und Koax genügen 22/20 im R4. Das Okto 42″ erreicht mit keiner geprüften Kombination vernünftigen Gewichts genug Steifigkeit und braucht ein anderes Konzept.

## Fragestellung und Vorgehen

Geprüft hat das Skript [`rohrstudie.py`](rohrstudie.py) folgende Kombinationen:
- **Rohre:** 23 handelsübliche gewickelte CFK-Rohre von 16/14 bis 60/56 mm.
- **Topologien:** V1 (Einrohr), V2 (Zweigurt) und V3 (Dreirohrsäule) wie in D14 sowie die neuen Raumfachwerke R3 und R4.
- **Konfigurationen:** alle 4 Bauweisen × 10 Propeller, insgesamt 3.800 Bewertungen.

Die Auslegergeometrie wird je Rohrgröße mit `auslegung.arm()` neu berechnet (Hülsen, Wurzelabstand, Kragmaß am Motorträger). Die Motorpositionen bleiben wie in D14.

| Kriterium | Ansatz |
|---|---|
| Festigkeit | Schweben × 3 g mit der echten Abflugmasse aus dem [Flugsimulator](../flugsimulator/README.md) (mind. 160 kg). Dazu Querbiegung aus Motormoment (46 Nm, MN1330-Prüfmaximum) plus Kreiselmoment bei 2 rad/s. Summe ≤ 300 MPa. |
| Knicken | Euler über die freie Rohrlänge, Abminderung 1,5 für Imperfektion und Kerben dünnwandiger CFK-Rohre |
| Resonanz | Ein-Massen-Schwinger am Auslegerende (Motor, Propeller, Motorträger, Regleranteil). Vertikale und seitliche Eigenfrequenz dürfen nicht innerhalb ±15 % der 1P- oder 2P-Anregung liegen, gerechnet von 0,85 × Schwebedrehzahl bis zur Maximaldrehzahl. |
| Mindestfrequenz | ≥ 15 Hz, damit Struktur und Flugregelung bzw. Böenanregung getrennt bleiben |
| Wand | D/t ≤ 25 und t ≥ 1 mm (Klemmung, Ovalisierung, Handhabung) |
| Masse | Rohre plus Aluhülsen; daraus folgt die Wirkung auf die Schwebeleistung (P ~ m^1,5) |

## Ergebnisse

### 1. Seitlich sind V1–V3 grundsätzlich zu weich

Die Gurte eines V2/V3-Auslegers liegen übereinander. Vertikal wirken sie als Fachwerk, seitlich nur über ihre eigene Biegesteifigkeit.

| Quad 42″, seitliche / vertikale Eigenfrequenz | 20/17 | 25/22 | 30/27 | 40/37 |
|---|---|---|---|---|
| V2 (D14) | 3,7 / 36 Hz | 5,3 / 40 Hz | 7,0 / 44 Hz | 11 / 51 Hz |
| R3 (Obergurt zur Rahmenecke, 102 mm Spreizung) | 17 / 34 Hz | 19 / 38 Hz | 21 / 42 Hz | – |
| R4 (Ober- und Untergurt zur Ecke) | 24 / 50 Hz | 27 / 57 Hz | 30 / 62 Hz | – |

Selbst 40/37 bringt V2 nur auf 11 Hz und wiegt 1,9-mal so viel wie 20/17. Beim Einrohr V1 sind für die Festigkeit sogar mindestens 50/46 nötig, und auch damit bleibt die Frequenz bei 13 Hz.

**Mit dem D14-Rohr 20/17 besteht keine der 16 schwebefähigen V2/V3-Konfigurationen die Mindestfrequenz.** Bei Hexa/Okto/Koax 42″ (V2) und den langen Okto-Armen fällt zusätzlich der Knicknachweis mit der Abminderung 1,5 durch.

### 2. Größer ist nicht automatisch besser

Dickere Rohre heben die vertikale Eigenfrequenz in das 1P-Band, also die Drehfrequenz der Rotoren. Beim Quad 42″ liegt das Band bei 39–73 Hz einschließlich ±15 % Abstand. 25/22 im V2 (40 Hz) und 30/27 im R3 (42 Hz) treffen es bereits. Bei R4 liegt schon 20/17 mit 50 Hz darin, nur 16/14 (37 Hz) bleibt darunter.

Dünnwandige große Rohre (30/28, 35/33, 40/38) verletzen D/t ≤ 25 und sind beim Klemmen gefährdet.

### 3. Empfehlung je Bauweise (leichtestes Rohr, das alle Kriterien erfüllt)

| Bauweise / Propeller | R3 | R4 | heute (V2, 20/17) |
|---|---|---|---|
| Quad 42″ | **20/17**, 0,73 kg/Arm, 17/34 Hz | 16/14, 0,69 kg/Arm, 18/37 Hz | 0,49 kg/Arm, 3,7/36 Hz, Knicken knapp |
| Hexa 36″ | **20/17**, 0,75 kg, 17/32 Hz | 16/14, 0,71 kg | 3,5 Hz seitlich |
| Hexa 42″ | 28/25, 1,12 kg | **22/20**, 1,00 kg, 15/30 Hz | 2,6 Hz, Knicken |
| Koax 36″ | **20/17**, 0,70 kg, 15/30 Hz | 16/14, 0,67 kg | 3,2 Hz |
| Koax 42″ | 30/27, 1,07 kg | **22/20**, 0,92 kg, 15/32 Hz | 2,7 Hz, Knicken |
| Okto 34–36″ | 28/25–35/32, 1,1–1,4 kg | **20/18–20/17**, 0,9–1,1 kg | 2,4–2,7 Hz |
| Okto 42″ | – | 32/29, 1,96 kg je Arm (+10,7 kg gesamt) | 1,8 Hz, Knicken |

Die Masse je Arm umfasst Rohre und Hülsen. Die geänderten Eckknoten (weitere Hülse) sind nicht enthalten.

**Mehrgewicht:** R3 mit 20/17 bringt gegenüber D14-V2 rund +0,25 kg je Ausleger, also etwa 1 kg beim Quad und 1,5 kg beim Hexa. Das kostet rund 1 % Schwebeleistung und ist für eine 4- bis 5-fach höhere Seitensteifigkeit ein guter Tausch.

## Nachtrag: Umordnen statt Material hinzufügen (V4)

Mit [`ausleger_anordnung.py`](ausleger_anordnung.py) habe ich geprüft, ob die vorhandenen Rohre ohne zusätzliches Material seitlich stabiler angeordnet werden können. Bewertet wurden alle Zuordnungen von 2 bzw. 3 Rohren 20/17 zu den vorhandenen Anschlusspunkten: Dreiecksverbinder oben/Mitte/unten (W+, W0, W−) und benachbarter Rahmeneckknoten oben/unten (E+, E−). Jedes Rohr wird als Balken modelliert, axial und quer ([Anordnung.json](Ausgabe/Rohrstudie/Anordnung.json)).

- **Mit 2 Rohren gibt es keine gute Anordnung.** Zwei Stäbe bleiben immer in einer Richtung weich (≤ 5 Hz).
- **Mit den 3 Rohren von V3 genügt eine Umordnung:** Das Mittelrohr bleibt am Dreiecksverbinder (W0), Ober- und Untergurt laufen zum Rahmeneckknoten (E+/E−). Das ist **V4**, mit gleicher Rohrzahl, gleichem Durchmesser und praktisch gleicher Rohrlänge.

| 20/17, seitlich / vertikal | V3 (alle am Verbinder) | V4 (umgeordnet) |
|---|---|---|
| Quad 42″ | 4,3 / 34,5 Hz | **21 / 39 Hz** |
| Quad 36″ | 5,2 / 41 Hz | **24 / 45 Hz** |
| Hexa 36″ | 4,1 / 33 Hz | **20 / 34 Hz** |
| Koax 36″ | 3,8 / 30 Hz | **18 / 33 Hz** |
| Hexa / Koax 42″ | 3,1–3,2 Hz | 15,4–15,6 Hz (Grenze 15 Hz knapp) |
| Okto 42″ | 2,1 Hz | 10,6 Hz (zu weich) |

Auch das Knicken wird günstiger: beim Quad 42″ 0,44 statt 0,68. Der vertikale Lastfall läuft fast nur über die beiden Gurte zur Rahmenecke; das Mittelrohr trägt die seitliche Komponente.

**Nur wo die Umordnung nicht reicht, braucht es mehr Material:**
- Hexa und Koax 42″: 22/19 im V4 (15,7 Hz, +0,04 kg je Arm)
- Okto 36″: 25/22
- Okto 42″: erreicht auch mit 30/27 nur 12,6 Hz und braucht ein anderes Konzept

V4 ist als vollständige CAD-Variante gebaut. Das Mittelrohr steckt im Dreiecksverbinder, die Gurte stecken in einer zusätzlichen Hülse der Eckknoten. Der Reglerhalter klemmt auf den beiden Gurten; beim Koax sitzen beide Regler außen hintereinander, weil innen das Mittelrohr verläuft.

## Umgesetzte Maßnahmen für die verbleibenden Fälle

Die Maßnahmen sind in `parameter.json` unter `konfig_overrides` hinterlegt und gelten nur für die jeweilige V4-Konfiguration. Alle Fälle erfüllen danach dieselben Kriterien: seitlich und vertikal ≥ 15 Hz, unterhalb des 1P-Bands, und Knicken ≤ 1 mit realer Abflugmasse und Abminderung 1,5.

| Konfiguration | Maßnahme | seitlich / vertikal | Knicken (streng) |
|---|---|---|---|
| Hexa 42″ V4 | Gurte 22/19 statt 20/17 | 14,9 → **16,5** / 27,4 Hz | 0,92 |
| Koax 42″ V4 | Gurte 22/19 | 14,9 → **16,3** / 30,0 Hz | 0,54 |
| Okto 36″ V4 | UD-verstärktes CFK-Rohr 20/17, E 100 GPa (Annahme, Herstellernachweis nötig) | 13,7 → **20,5** / 33,5 Hz | 0,66 |
| Okto 42″ V4 | Zentralrahmen 250 statt 205 mm Seitenlänge, Gurte 28/25 | 10,0 → **16,1** / 22,4 Hz | 0,76 |

Warum nicht überall steifer?
- **Hexa und Koax 42″:** UD-CFK würde sie auf 21 Hz bringen. Die vertikale Frequenz läge dann aber im 1P-Band der Rotoren (≥ 33 Hz), deshalb nur moderat dickere Rohre.
- **Okto 42″, Rahmen:** Ein größerer Rahmen ist der stärkste Hebel (bei 375 mm: 25 Hz). Ab etwa 300 mm stoßen aber die Stütze des Fußschlittens und die vergrößerten Verbinderplatten zusammen, und ab 450 mm fällt die Seitenfrequenz in das 1P-Band (30 Hz).
- **Okto 42″, Sattel:** Mit 250 mm genügen 15 mm Versatz des Schienensattels nach innen; die Lage wird automatisch aus dem Abstand der Stütze zur Plattenkontur bestimmt. Der größere Rahmen verbreitert zugleich die Standfläche, die Kippkante wächst von 248 auf rund 302 mm.


1. **Beim Durchmesser 20 mm (20/17, 1,5 mm Wand) als Standard bleiben.** Er besteht Festigkeit und Knicken für Quad, Koax und Hexa bis 36″, bleibt unterhalb der 1P-Resonanz und ist gut erhältlich. Hülsen, Eckknoten und Kabelkammern bleiben gleich.
   - **20/18 (1 mm Wand)** nur bei kurzen Armen im Raumfachwerk; die Wand ist für Klemmung und Schläge knapp.
2. **Die Topologie ändern statt des Durchmessers, zuerst durch Umordnen (V4, kein Mehrmaterial).** Falls das nicht reicht: Als Raumfachwerk geht der Obergurt (R3) oder Ober- und Untergurt (R4) zusätzlich zum vorhandenen Rahmeneckknoten. Der Eckknoten braucht dafür eine weitere Hülse, der Dreiecksverbinder bleibt.
   - R3 für Quad, Hexa und Koax bis 36″.
   - R4 für Hexa und Koax 42″, dort mit 22/20.
3. **Okto 42″ grundsätzlich überdenken.** Die rund 1 m langen Arme brauchen im R4 32/29 mit ~2 kg je Arm. Alternativen: Ringverband zwischen benachbarten Motoren, ein größerer Zentralrahmen (kürzere Arme) oder auf Hexa/Koax ausweichen.
4. **Rahmenrohre des Zentralwürfels 20/17 beibehalten.** Bei rund 165 mm freier Länge liegt die Euler-Knicklast bei etwa 68 kN, rund das 15-Fache der Stabkräfte aus den Auslegern bei 3 g. 16/14 wäre möglich, spart aber unter 0,15 kg und kostet die Gleichteiligkeit.

## Grenzen

- **Statisches Screening:** Gelenkstab- bzw. Kragträgermodell und Ein-Massen-Schwinger, keine FE-Modalanalyse. Torsion um die Auslegerachse (Motor sitzt ~70 mm über dem Systempunkt), Knotennachgiebigkeit und Hülsenspiel senken die echten Frequenzen weiter. Die Werte sind eher obere Schranken.
- **Werkstoff:** E-Modul 50 GPa und 300 MPa zulässig wie in D14 (konservativ für gewickelte 0/90-Rohre). Unidirektional verstärkte Rohre (E ≈ 100 GPa) würden die Frequenzen um rund 40 % heben; damit verschiebt sich die 1P-Resonanzgrenze und muss neu geprüft werden.
- **Annahmen:** Drehzahlbänder aus der MN1330-Schwebeanalyse, 2-Blatt-Propeller.
- **Geometrie:** R3/R4 sind nicht als CAD gebaut. Freiräume zu Propellern, Fußschlitten und Reglerhalter sowie die Eckknoten-Hülsen sind vor einer Übernahme mit `bauen.py` zu prüfen.

## Dateien

- [Rohrstudie.json](Ausgabe/Rohrstudie/Rohrstudie.json): alle 3.800 Bewertungen und die Empfehlung je Konfiguration
- [Rohrstudie.csv](Ausgabe/Rohrstudie/Rohrstudie.csv): Tabelle zum Filtern
- Reproduktion: `python3 multirotor_d14/rohrstudie.py`; braucht die D14-Ausgaben und `flugsimulator/Ergebnisse/Schwebeanalyse_alle.json`
