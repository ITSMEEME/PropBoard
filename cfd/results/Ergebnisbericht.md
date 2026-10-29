# CFD-Voruntersuchung: Ergebnisse

**Keine realmaßstäbliche Board-Simulation und kein Tragfähigkeitsnachweis.**

| Lauf | Schritte | Mittlerer Cz, Umlauf 1 | Mittlerer Cz, Umlauf 2 | Cmoment, Umlauf 2 |
| --- | ---: | ---: | ---: | ---: |
| forward_c12 | 18654 | 0.21284 | 0.16690 | 1.02969 |
| forward_c16 | 24873 | 0.19741 | 0.15908 | 1.00655 |
| reverse_c16 | 24873 | 0.19725 | 0.15746 | -1.01624 |
| zero_pitch_c12 | 18654 | 0.00179 | 0.00577 | 0.85430 |

Gitterunterschied (12 gegen 16 Zellen/Sehne): **4.9 %** bezogen auf Cz des feineren Gitters, jeweils zweiter Umlauf.

Änderung Cz vom ersten zum zweiten Umlauf im feineren Vorwärtslauf: **19.4 %**. Periodisches Einschwingen ist damit nicht nachgewiesen.

Differenz der getrennten Umlaufrichtungen im zweiten Umlauf: **1.0 %**. Momente mit entgegengesetztem Vorzeichen: **True**. Dies belegt keinen vollständigen Momentenausgleich des gekoppelten Boards.

Ruhekontrolle: 248 Schritte; maximaler absoluter Kraftbeiwert 9.48e-13.

Null-Pitch-Kontrolle: |Cz| beträgt 3.45 % des aktiven groben Vergleichslaufs.

Alle Werte stammen aus einem eigenen 2D-LBM-Prototyp bei Re = 40. Die Kontrollen ersetzen keine quantitative Referenzvalidierung des Solvers. Die Rechnung zeigt das Verhalten dieses numerischen Modells; daraus folgen keine reale Traglast, Flugzeit oder elektrische Leistung.

Eine belastbare 3D-CFD bei realistischer Reynolds-Zahl wurde nicht ausgeführt. Grenzen und Reproduktionsbefehle stehen in [README.md](../README.md).
