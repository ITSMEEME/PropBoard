# P11 – Top 10 der endlichen Parametersuche

Aerodynamische Entwürfe – Motor offen

Masse: 2.583 kg. 5120 Parameterentwürfe; 9134 stationäre Rechnungen. 379 aerodynamisch vorgeprüft; 47 auf beiden feineren Rastern bestätigt; 0 innerhalb der elektrischen Suchgrenzen.

Sortiert nach mechanischer Rotorleistung; elektrische Zahlen außerhalb EMAX-Grenzen sind extrapoliert.

| Rang | D mm | Blätter | RPM | Pitch O/U ° | Schub kg-Äquiv. | Rotorleistung W | EMAX Bedarf W |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 498.7 | 2 | 3937 | 3.34 / 6.38 | 2.725 | 205.0 | 569.8 |
| 2 | 496.0 | 2 | 3874 | 3.43 / 7.28 | 2.725 | 207.1 | 590.4 |
| 3 | 490.9 | 2 | 3919 | 3.04 / 7.14 | 2.725 | 210.1 | 597.5 |
| 4 | 486.5 | 2 | 4065 | 3.51 / 7.58 | 2.725 | 212.5 | 583.1 |
| 5 | 495.6 | 2 | 4063 | 2.78 / 6.60 | 2.725 | 214.5 | 590.6 |
| 6 | 493.1 | 2 | 4172 | 3.32 / 7.03 | 2.725 | 216.7 | 582.1 |
| 7 | 474.6 | 7 | 3436 | 16.46 / 18.77 | 2.725 | 219.7 | 756.4 |
| 8 | 463.0 | 8 | 3425 | 16.78 / 19.46 | 2.725 | 219.8 | 758.9 |
| 9 | 471.2 | 4 | 3690 | 14.19 / 17.84 | 2.719 | 220.4 | 695.8 |
| 10 | 481.9 | 2 | 4494 | 3.06 / 6.49 | 2.725 | 223.8 | 561.9 |

Rangfolge aus 10×16-Suchwerten; alle veröffentlichten Kandidaten bestehen die Kriterien auch bei 20×32 und 40×64. Die höhere Auflösung ersetzt keine Messvalidierung.

Alle elf Parameter und Vergleichsgrößen: [CSV](Top10_Kandidaten.csv), vollständiger Suchbericht und Grenzen: [JSON](Kandidatensuche.json).

- Finite sampled search, not all continuous combinations or a proven global optimum
- Unchanged P11 mass/inertia for all geometries; no structural or CAD clearance validation
- Simplified polar and coaxial inflow; no measured real-world efficiency
- Electrical EMAX extrapolations outside limits are not operating points; future motor efficiency unknown
- 20 A default screening limit is an assumption, not verified continuous thermal rating; 46 A is model peak cap
- Conservative planar blade-overlap screen; full 3D kinematics not checked
- Reject mechanical power below T^1.5 / sqrt(2 rho pi R^2), rho=1.225 kg/m3, common coaxial disk area including hub; necessary plausibility test only
