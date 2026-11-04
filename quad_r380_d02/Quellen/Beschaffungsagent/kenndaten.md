# Kenndaten-Extrakt Antriebs-Quellen (Stand 2026-11-03)

Die Werte unten wurden per Web-Abruf als Text ausgelesen. Die Originaldateien liegen nicht vor, und es gibt keine SHA256-Werte. Ein Abruf mit einem Sprachmodell kann Tabellenspalten vertauschen, deshalb sind auslegungsrelevante Werte vor der Nutzung am Original zu prüfen. Als Spiegel markierte Quellen stammen nicht vom Herstellerserver.

## EMRAX 188 – Datenblatt V1.7 (kein Datum)

- Ø188 × 79 mm. Masse AC/LC/CC 7,1 / 7,9 / 7,6 kg.
- Spitzenleistung 60 kW (S2, 30 s) bei 6500 min⁻¹. S1-Dauerleistung AC/LC/CC 23 / 29 / 33 kW.
- Spitzendrehmoment 100 Nm, Dauerdrehmoment 34 / 43 / 48 Nm. Grenzdrehzahl 8000 min⁻¹, Betriebsspannung 50–830 V DC, Wirkungsgrad bis 96 %.
- 10 Polpaare, Sternschaltung. Lager 6205 / 3204. J = 0,0147 kg·m² (LC/AC) bzw. 0,0144 kg·m² (CC).

| Wicklung | HV | MV | LV | LV+28 | LV+43 | LV+100 |
|---|---|---|---|---|---|---|
| U Spitzenleistung [V] | 660 | 390 | 160 | 200 | 230 | 320 |
| KV Leerlauf [min⁻¹/V] | 17,73 | 29,58 | 72,82 | 56,89 | 50,93 | 36,43 |
| KT [Nm/A] | 0,54 | 0,32 | 0,13 | 0,17 | 0,19 | 0,26 |
| I Spitze / Dauer LC [A] | 190/100 | 310/160 | 900/400 | 590/310 | 530/280 | 390/200 |
| R Phase 25 °C [mΩ] | 14,24 | 6,31 | 1,05 | 1,55 | 1,94 | 4,65 |
| Ld/Lq [µH] | 92/102 | 40/44 | 5,2/5,8 | 8,9/9,8 | 10,9/12,1 | 21,5/23,8 |

## EMRAX 208 – Datenblatt V1.7

Die Dateien unter /2025/03/ und /2026/08/ ergaben identische Kennwerte.

- Ø208 × 85 mm. Masse AC/LC/CC 9,4 / 10,3 / 10,0 kg.
- Spitzenleistung 86 kW bei 6000 min⁻¹. HV+42 nur 76 kW bei 4900 min⁻¹, weil die 830-V-Grenze erreicht wird.
- S1-Dauerleistung 33 / 47 / 52 kW, Spitzendrehmoment 150 Nm, Dauerdrehmoment 53 / 75 / 83 Nm. Grenzdrehzahl 7000 min⁻¹.
- Lager 6206 / 3206. J = 0,0239 kg·m² (LC) bzw. 0,0236 kg·m² (AC/CC).

| Wicklung | HV | MV | LV | LV+43 | LV+100 | HV+42 |
|---|---|---|---|---|---|---|
| U Spitzenleistung [V] | 690 | 420 | 170 | 240 | 340 | 830 |
| KV Leerlauf | 15,53 | 25,02 | 64,01 | 44,77 | 32,01 | 10,93 |
| KT [Nm/A] | 0,62 | 0,38 | 0,15 | 0,21 | 0,30 | 0,88 |
| I Spitze / Dauer LC [A] | 240/140 | 400/220 | 1000/560 | 720/400 | 500/280 | 170/95 |
| R Phase [mΩ] | 12,77 | 5,54 | 1,11 | 2,04 | 3,65 | 25,68 |
| Ld/Lq [µH] | 110/115 | 47,2/49,4 | 6,3/6,5 | 13,1/13,7 | 25,6/26,8 | 220/230 |

Temperatur- und Kühlungsgrenzen für 188 und 208:

- Temperaturgrenzen 100 °C am Sensor, 80 °C an der Rotoroberfläche, 120 °C absolut.
- Kühlmittel mindestens 6 l/min bei höchstens 50 °C.
- Luftkühlung mit 20 m/s. Zuluftbedarf am Aufstellort 0,4 m³/min je kW.
- CC braucht zwingend Flüssigkeits- und Luftkühlung.

## EMRAX Users Manual V1.7 (28.01.2026)

- Befestigung: mindestens 6 Schrauben der Klasse 10.9.
  - 188: M6, 16 Nm trocken / 13 Nm geschmiert, Einschraubtiefe 10–22 mm.
  - 208: M8, 40 / 32 Nm, Einschraubtiefe 16–22 mm.
- FSI-Flansch:
  - 188: 6 × M6x20 mit 16 Nm.
  - 208: 6 × M8x25 mit 40 Nm.
- LC-Kühlung: 6–11 l/min. Druckabfall bei 6 l/min: 0,2 bar (188) bzw. 0,5 bar (208). Zulaufdruck max. 2 bar(g), Partikel max. 50 µm, verträglich mit Aluminium und VMQ70.
- Lager sind vorgespannt und lebensdauergeschmiert. **Zulässige Lagerlasten und Lebensdauer sind nicht angegeben**, dazu muss man bei EMRAX anfragen.
- Wellenversatz max. 0,03 mm. Einsatzhöhe max. 6500 m.
- **Widerspruch im Handbuch:** Kap. 1.5 nennt 100 °C als Sensorgrenze, Kap. 3.6 nennt 120 °C. Das muss EMRAX klären.

## EMRAX-Reglerliste V1.4 (10.04.2026)

Die Liste enthält 30 Einträge, aber keine Zuordnung zu einzelnen Wicklungen. Für HV-Wicklungen in Frage kommende Regler (U max ≥ 690 V):

| Regler | U max [V] | I Spitze/Dauer [A] | Masse | Sensor |
|---|---|---|---|---|
| EMSISO H10B | 870 | 75/60 | 5 kg | RM44SC |
| EMSISO H20B | 870 | 210/170 | 7,3 kg | RM44SC |
| NX E8160 | 850 | 350/300 | 4,5 kg | – |
| NX R300 | 850 | 560/350 | 6,7 kg | – |
| DTI HV-850 | 800 | 600/365 | 6,8 kg | RM44SI |
| Cascadia CM200DZ | 840 | 400/200 | 6,75 kg | Resolver |
| Unitek Bamocar 700-160 | 700 | 120/80 | 3,5 kg | Resolver |
| Scott SD300 / SD500 | 800 | 600/450 bzw. 900/700 | 16,5 kg | – |

Die vollständige Liste mit LV- und MV-Reglern steht im Original. Der Hersteller empfiehlt FOC. Bei 2×UVW sind zwei Regler mit geteiltem Positionssignal möglich.

## Plettenberg NOVA 30-50-B10 P50 WK – Datenblatt V1.5 (15.06.2026)

- KV 15, Spannungsbereich 100–350 V, 50 Pole.
- R = 85 mΩ und L = 182 µH, jeweils Phase–Phase.
- Spitzenleistung 30 kW. Spitzendrehmoment 80 Nm für max. 5 s bei sensorgeführtem Regler, mit sensorlosem Regler 10–20 % weniger. n max 5000 min⁻¹.
- Masse 6250 g, Ø197 × 96 mm, Montage vorn.
- Wasserkühlung 7 l/min bei max. 40 °C Einlass und max. 2 bar. IP53. Stator max. 100 °C.
- Sensoren: Hall-Sensoren, NTC 47 kΩ.
- **Nicht angegeben:** Dauerstrom, Dauerleistung, Dauerdrehmoment.

## Plettenberg Prüfstandsbericht NOVA 30-50-B10 P50 HV + MST 400-133 (01.04.2021), 350 V

- Kenngrößen: kV 14,5, kT 76,44 Ncm/A, I₀ 4,9 A, n₀ 5016,7 min⁻¹.
- Systemwirkungsgrad einschließlich Regler:

| I [A] | n [min⁻¹] | P ein [W] | P aus [W] | M [Nm] | η [%] |
|---|---|---|---|---|---|
| 20 | 4884 | 6994 | 5916 | 11,57 | 84,6 |
| 40 | 4614 | 13984 | 12977 | 26,86 | 92,8 |
| 48 | ≈4520 | ≈16780 | ≈15610 | ≈33,0 | ≈93,0 (interpoliert) |
| 50 | 4502 | 17480 | 16265 | 34,50 | 93,05 |
| 80 | 4226 | 27952 | 25417 | 57,43 | 90,9 |
| 110 | 3988 | 38423 | 33564 | 80,37 | 87,4 |

- Der Bericht enthält keine Temperaturen, der thermische Dauerbetriebspunkt ist daher offen.
- Die 48-A-Zeile ist **von mir interpoliert** und nicht aus dem Bericht gelesen. Der Bericht enthält 2-A-Schritte, der echte Wert steht im Original.

## Plettenberg COTS-Broschüre V1.3 (13.05.2024)

- Die Broschüre listet NOVA 30-50-B10 P50 WK mit Datenblatt V1.3 und 6300 g. Das aktuelle Datenblatt V1.5 nennt 6250 g, die Broschüre ist also veraltet.
- iMST 80-240: 15–80 V, 17,6 kW Dauerleistung.
  - Dauerstrom 220 A bei 25 °C, 175 A bei 50 °C, 125 A bei 75 °C. Spitzenstrom 400 A für 2 s.
  - Schnittstellen: RS232 plus wahlweise CAN, PWM oder analog.
  - Batteriekabel insgesamt höchstens 1 m.
  - **Für 350 V ungeeignet.**
- Neuere HD-Broschüre: plettenbergmotors.com/wp-content/uploads/2025/03/Plettenberg-COTS-Product-Brochure_HD.pdf (nicht gelesen).

## Mejzlik-Rotoren – maxon-Messung (Dok. 9970557/en/02, 09.04.2025)

Gemessen mit maxon EC 87 flat UAV, Artikelnr. 773484.

| Rotor | Masse | n max empf. | Messpunkt | I [A] | Schub [g] | P [W] | g/W |
|---|---|---|---|---|---|---|---|
| 30x10 | 96 g | 6000 | 3000 min⁻¹ (kurzzeitig, 37 V) | 25,2 | 7283 | 1314 | 5,5 |
| 28x9.4 | 78 g | 6400 | 3750 min⁻¹ (12S, 44,4 V) | 39,7 | 8845 | 2075 | 4,3 |

Einordnung: Das sind Messwerte von maxon (Drittquelle) und laut Dokument nur als Referenz gedacht. Beim 28x9.4 war die Spaltenzuordnung der Tabelle im Extrakt nicht eindeutig.

## T-Motor U15XXL KV29 (Stand Downloads 25.06.2026)

- Motor: 5130 g, Φ151,5 × 106 mm, 20 mΩ, 36N42P, Welle 25 mm, 24S, Spitzenstrom 210 A für 80 s, Nennleistung 3300 W.
- Testdaten bei 32 °C Umgebung:

| Rotor | Messpunkt | U [V] | I [A] | Schub [kgf] | n | P [W] | gf/W |
|---|---|---|---|---|---|---|---|
| NS57x22 | 50 % | 98 | 34,4 | 29,6 | 1374 | 3382 | 8,8 |
| NS57x22 | 100 % | 97 | 169,4 | 85,5 | 2310 | 16395 | 5,2 |
| NS62x24 | 50 % | 98 | 37,9 | 33,2 | 1296 | 3727 | 8,9 |
| NS62x24 | 100 % | 96 | 209,1 | 101,4 | 2203 | 20089 | 5,0 |

- Die Temperaturangaben sind unklar: 158 °C bzw. 184 °C stehen in der 30-%-Zeile, die Messung ist aber für 100 % Gas beschrieben.
- CAD-Downloads:
  - STEP: cn.tmotor.com/uploadfile/downloads/tmotor-u15xxl-motor-3d-model.step
  - 2D-Zeichnung: cn.tmotor.com/uploadfile/downloads/tmotor-u15xxl-motor-2d-drawings-en.pdf
- Leitfaden vom 17.06.2026: U15XXL schafft 100 kg Schub pro Motor. Empfohlenes MTOW 200 kg (Quad/Coax-Quad), für U15XL 160 kg, für U15L 120 kg. Regler jeweils Thunder 300A 24S, 870 g.

## Molicel-Zellen

| Zelle | Kap. typ/min [mAh] | I Dauer max | I Laden max | Ri AC/DC [mΩ] | Masse max | Wh/kg | Version |
|---|---|---|---|---|---|---|---|
| P45B | 4500/4300 | 45 A | 13,5 A | 7 / 15 | 70 g | 242 | v1.2 (Spiegel) |
| P50B | 5000/4850 | 60 A | 25 A | 6,5 / 12,8 | 71 g | 260 | v1.1 (Spiegel) |
| P60C | 6000/5850 | 60 A Std / 100 A max | 30 A | 6,5 / 12,8 | 75 g | 284 | **v0.1 Tentative, 23.10.2025** |

- Für alle drei Zellen gilt: 3,6 V nominal, Ladeschluss 4,2 V, Entladeschluss 2,5 V, Abschaltung beim Entladen bei 80 °C.
- Das Datenblatt der P60C ist vorläufig. Deren Ri-Werte sind identisch mit denen der P50B, was auf Platzhalterwerte hindeuten kann.

## TE EV200AAANA (1618002-7)

Nur Produktkarte, das eigentliche Datenblatt wurde nicht gelesen.

- Belastbar sind nur diese Angaben:
  - Kontaktspannung bis 900 VDC, Nennstrom 500 A.
  - Spule 9–36 VDC.
  - Form X (SPST-NO), Bolzenanschlüsse, Flanschmontage.
- TE-CN bezeichnet 900 VDC als Spulenspannung. Das ist offensichtlich eine Fehlzuordnung.
- Der Spulenwiderstand von 3,14 Ω würde bei 24 V rund 180 W bedeuten. Das ist für einen Halte-Betrieb unplausibel und passt nur zum Einzugsstrom mit Economizer. **Nicht verwenden, bis das Original-Datenblatt (5-1773450-5_sec7_EV200A) vorliegt.**
- **Fehlt:** Ausschaltvermögen, Isolation, Masse, Anzugsmomente, Lebensdauer.
- CAD-Dateien als STP, IGS und DXF sind bei TE gelistet, aber nicht abrufbar.

## Littelfuse 30EV1K – Spiegel TTI, Revision 23.11.2023

**Versionsabweichung:** Die CSV nennt die Revision vom 15.10.2024 (vorläufig), gelesen wurde die vom 23.11.2023.

- 1000 V DC, Ausschaltvermögen 30 kA, Anzugsmoment 12 ± 1 Nm, Einsatzbereich −40 bis +125 °C.
- Die Typen 150–225 A sind **als „in Entwicklung“ markiert**, die Werte sind vorläufig.

| Typ | I²t [A²s] | Dauerstrom 20 °C | 85 °C | 125 °C |
|---|---|---|---|---|
| 150 A | 60 000 | 120 | 112 | 102 |
| 175 A | 103 000 | 140 | 131 | 119 |
| 200 A | 135 000 | 160 | 150 | 136 |
| 225 A | 164 000 | 180 | 168 | 153 |

- Maße fehlen im gelesenen Dokument.

## Carbonrohr 20x17x1000 (Carbonwebshop)

- Preis 45,02 € inkl. MwSt., lieferbar.
- Typkarte „High Performance“: Twill-Deckschicht, Prepreg mit 80 % UD 0° und 20 % UD 90°, Toleranz ±0,2 mm.
- **Artikelnr. CBU 2017 1005 TG ist nicht bestätigt**, die Seite nennt sie nicht (Warenkorb-ID 104368). Zum Vergleich: Das Schwesterrohr 18x15 hat die Artikelnr. CBU 1815 1005 TG, das Schema ist also plausibel.
- Masse, E-Modul und Steifigkeit sind nicht angegeben.

## Weiterhin offen

- **MGM COMPRO HBC 400400 / HBCi 320120:** aeroexpo und mgm-compro.cz sind gesperrt. Keine Daten.
- **Mejzlik OTS-Liste und Datenportal:** Die Liste war nicht auffindbar, das Portal ist formulargeschützt.
- **Plettenberg Maßblatt NOVA-30-50-WK:** Nicht verlinkt, über die Suche nicht gefunden.
- **TE EV200:** Das Original-Datenblatt und die CAD-Dateien fehlen.
- **Alle Einträge:** Es gibt keine SHA256-Werte. Die lassen sich nur mit dem Download-Skript oder nach einer Domain-Freigabe ermitteln.
