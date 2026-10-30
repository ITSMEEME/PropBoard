# R04 Auftriebssimulator (lokal, interaktiv)

`R04_Simulator.html` direkt im Browser öffnen (Doppelklick; kein Server, keine Internetverbindung nötig).

**Vereinfachtes Modell, kein Nachweis.** Ergebnisse sind Modellwerte für den Schwebeflug und nicht durch CFD oder Versuch validiert.

## Einstellbar

Drehzahl, Pitch oben/unten (gekoppelt oder getrennt, mit „Drehmoment ausgleichen“), Flügelzahl je Ebene, Flügeltiefe, Innen-/Außenradius, Profildicke, Verwindung, Ebenenabstand. Dazu kommt eine Referenzlinie aus Fahrzeugmasse und Person. Die erfassten CAD-Massen aus R04 sind unvollständig.

## Modell

| Teil | Methode | Grenzen |
|---|---|---|
| Auftrieb, Leistung, Drehmoment (`r04_physik.js`) | Blattelement-Impuls-Theorie je Ringrotor, Prandtl-Spitzen- und -Wurzelverlust, vereinfachte NACA-00xx-Polare mit Re-abhängigem Strömungsabriss | Polare nicht validiert; der untere Rotor sieht den kontrahierten Nachlauf des oberen (Aktuatorscheibenentwicklung, Drall mit Drehimpulserhaltung, weicher Rand); keine Rückwirkung unten → oben, keine Blattpassagen, keine Führungen oder Rahmen, kein Bodeneffekt, kein Vorwärtsflug |
| 2D-Strömung/Turbulenz (`lbm.js`) | D2Q9-Lattice-Boltzmann mit Smagorinsky-Modell; abgewickelter Zylinderschnitt bei wählbarem Radius, zwei gegenläufige Flügelreihen, periodisch | Re künstlich niedrig (10³…4·10⁴ statt ~3·10⁵), unendlich lange Flügel ohne Spitzenverluste, treppenförmige bewegte Ränder (Rauschen in Blattnähe); nur qualitativ. Voll entwickelt nach etwa 30–60 s |
| 3D-Ansicht | Flügel nach Geometrie und Pitch; Partikel im BEMT-Nachlauffeld (axial, Drall, Kontraktion) | keine 3D-CFD; Spitzenwirbel sind nicht aufgelöst |

## Erste Erkenntnisse am R04-Referenzpunkt

850 U/min (≈ 40 m/s bei r = 450 mm), 12° Pitch:
- Das Modell liefert rund **263 N** (≈ 27 kg Kraftäquivalent) bei etwa 2,9 kW aerodynamischer Leistung.
- Die induzierte Abwärtsströmung senkt den effektiven Anstellwinkel auf etwa 1–4°.
- Der untere Rotor liefert im Nachlauf nur etwa ein Drittel des oberen. Drehmomentgleichgewicht ergibt sich bei etwa 14,7° Pitch unten.
- Die frühere analytische Rechnung mit frei angenommenem CL (`Massen_Szenarien.json`) liegt deutlich höher, weil sie die induzierte Strömung nicht berücksichtigt.

## Prüfung

```sh
node pruefen.js
```

Geprüft werden Impulsbilanz, Gütegrad < 1, Nullfälle, n²-Skalierung, Drehmomentausgleich sowie Stabilität und Abwärtsströmung des LBM.

## Testmodell 1:4

Knopf „Testmodell 1:4 laden“ oder `R04_Simulator.html#testmodell`: lädt die Phase-1-Auslegung aus `modell_r04/auslegung`. Dabei wird das Antriebsmodell (ECO II 2306 KV1900, Stirnrad 6,5:1, Tattu 1550 mAh 6S) aktiviert, und es werden Motorstrom, Motordrehzahl, Tastgrad, elektrische Leistung und Laufzeit angezeigt. Übersetzung und Akkuladezustand sind einstellbar. Die Seite lädt dazu `../../modell_r04/auslegung/antrieb.js`; der Projektordner muss also vollständig vorliegen.
