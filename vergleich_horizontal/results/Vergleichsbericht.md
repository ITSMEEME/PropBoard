# Vergleichsversuch: horizontale Bänder in zwei z-Ebenen

**Nur lokale 2D-Strömung gerader Abschnitte bei Re = 40; keine 3D-Simulation der gesamten Umläufe.**

| Versuch | Gitter | Schritte | Mittlerer Cz gesamt, letzte fünf Durchgänge |
| --- | --- | ---: | ---: |
| single_c16 | [64, 240] | 32000 | 0.05953 |
| stack_240_c16 | [64, 240] | 32000 | 0.22025 |
| stack_360_c16 | [64, 240] | 32000 | 0.15689 |
| stack_240_c24 | [96, 360] | 48000 | 0.25588 |

240-mm-Stapel / zwei unabhängige Einzelreihen: **1.850**.

360-mm-Stapel / zwei unabhängige Einzelreihen: **1.318**.

Gitterunterschied des 240-mm-Stapels (16/24 Zellen pro Sehne): **13.9 %**.

Änderung des mittleren Cz der letzten zwei Fünferblöcke:

- single_c16: 25.8 %.
- stack_240_c16: 7.2 %.
- stack_360_c16: 11.4 %.
- stack_240_c24: 7.3 %.

Die Kennwerte gelten nur für dieses vereinfachte Rechenmodell. Die Kraftreferenz ist eine Profilsehne pro Einheitsspannweite, beim Stapel wird über beide Reihen summiert. Der Vergleichsfaktor verwendet deshalb zweimal den Einzelreihenwert. Keine Umrechnung auf reale Traglast oder elektrische Leistung.

Der frühere vertikale Umlauf hatte eine andere Geometrie und eine andere Kraftnormierung. Ein direkter Leistungsvergleich zwischen beiden vollständigen Fahrzeugvarianten ist mit diesen 2D-Rechnungen nicht zulässig.

Grenzen: künstliche Viskosität, grobe Profilauflösung, treppenförmige bewegte Wände, periodische gerade Flügelreihen, gedämpfte äußere Ränder, keine Kurvenfahrt, keine endliche Spannweite, keine Führung/Schlitten, kein Deck und kein Mensch. Der eigene Solver ist nicht quantitativ gegen einen externen Referenzfall validiert. Zwei Gitter und die beobachteten Zeitverläufe sind kein vollständiger Konvergenznachweis.
