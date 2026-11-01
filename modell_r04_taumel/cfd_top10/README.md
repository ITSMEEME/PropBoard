# P11 – unabhängige 3D-CFD der zehn Suchkandidaten

[Rechen- und Prüfstatus mit tatsächlichen Strömungsbildern](Ausgabe/CFD_Vergleich.html) · [maschinenlesbare Auswertung](Ausgabe/CFD_Auswertung.json) · [Eingabe-Planformen](Ausgabe/Top10_Planformen.png) · [Profilfamilie](Ausgabe/Top10_Profile.png).

Die CFD-Rangfolge ist von der [vereinfachten Top-10-Suche](../simulation/Ergebnisse/P11/Top10_Kandidaten.md) unabhängig. Noch laufende, nicht konvergierte oder nicht akzeptierte Rechnungen dürfen keinen Gesamtsieger begründen. Die aktuelle Auswertung nennt den Status jedes einzelnen Falls. Die vorliegenden Verfahren beweisen keine „perfekte“ Flügelform.

## Was tatsächlich gerechnet wird

- OpenFOAM 2412, `simpleFoam`, voller 360°-Bereich mit sämtlichen Blättern beider Ebenen, zwei gegenläufige MRF-Zonen. Docker-Image mit unveränderlicher Prüfsumme `opencfd/openfoam-default@sha256:1ba02114b1c025c370f2e269a07677c16c9bea8d990fcd75ac8378aff9d41b50`.
- Parametrische symmetrische NACA-Kontur mit der jeweiligen relativen Dicke, endlicher Hinterkante (Polynomkoeffizient −0,1015), Wurzeltiefe, Zuspitzung, linearer Verwindung und Neutralpitch aus dem jeweiligen Kandidaten. 13 radiale Querschnitte, 49 Kosinuspunkte je Profilseite. Wurzel und Spitze sind flach geschlossen. Keine Wiederherstellung der historischen CAD-Blattform und keine Untersuchung aller denkbaren Profilwölbungen.
- Drehzahl, Durchmesser, Blattzahl und Ebenenabstand gemäß Suchkandidat. Vorgegebene Drehzahl ist eine Randbedingung; der EMAX wird dadurch nicht als leistungsfähig bestätigt. Die Simulation ermittelt die dazu nötige Wellenleistung aus beiden Drehmomenten.
- Inkompressible Luft mit ρ = 1,225 kg/m³ und ν = 1,5·10⁻⁵ m²/s. Druckoffene Außenränder, ruhende Umgebung, Quadergrenzen ±3 Rotorradien. Keine angesetzte Anströmung von außen. Freie Turbulenzgrößen k = 0,01 m²/s², ω = 10 1/s sind Annahmen.
- Vollturbulentes k–ω-SST mit kontinuierlicher Spalding-Wandfunktion. **Gemischte Wandauflösung, kein vollständig wandaufgelöster Nachweis.** Die ersten Schichten sind auf 10 µm ausgelegt; scharfe Wurzel-, Spitzen- und Hinterkanten verhindern lokal vollständige Schichtabdeckung.
- Oberer Rotor +Ω, unterer −Ω; eingefrorene relative Blattstellung. Keine zeitaufgelöste Blattpassage, keine Sliding-Mesh-URANS/LES. Nabe, Motor, Führungsrollen und Halter sind nicht im Strömungsraum enthalten.

Jeder Fall enthält `case.json` mit allen elf Parametern, CAD-Prüfsumme, Suchbericht-Prüfsumme, Luftwerten, Solver und Image. Rohe Rechenfälle liegen lokal unter `cases/` und sind wegen ihrer Größe ignoriert; `erstellen.py` erzeugt sie reproduzierbar. Die angegebene Strukturmasse wird bei anderen Blattgeometrien nicht automatisch neu ausgelegt.

## Numerische Annahme und Akzeptanz

Das Grundnetz entsteht mit `blockMesh`, die Flügel werden mit `snappyHexMesh` ausgeschnitten und körperangepasst. `surfaceCheck` prüft geschlossene, gültige Dreiecke. Vor der Solverphase müssen die grundlegende Geometrie-/Topologieprüfung und mindestens 70 % schichtbelegte Wandflächen bestehen. Die zusätzliche Prüfung vergleicht außerdem die aus dem Fluidnetz verdrängte Festkörpermenge mit dem integrierten STL-Volumen (Abweichung <5 %). Die ausführliche `allGeometry`-Diagnose wird separat erhalten, einschließlich Hinweisen auf konkave Polyeder.

Ein abgeschlossener Screeningfall benötigt mindestens 200 Kraftpunkte, positive Schub-/Leistungswerte, Kraft- und Leistungsstreuung <3 %, Drift im letzten 200er-Fenster <2 %, relative globale Flussbilanz <1 % sowie Druck- und Impuls-Anfangsresiduen <10⁻⁴ im letzten 20er-Fenster. Die mechanische Leistung darf die ideale Impulsscheiben-Untergrenze nicht unterschreiten. Für die bedingte Spalding-Wandfunktions-Auswertung gelten zusätzlich mittleres Wand-y+ <30 und maximales Wand-y+ <500 auf beiden Rotoren. Die tatsächlichen Werte werden vollständig angegeben; diese Grenzen sind keine Aussage, dass die Wandströmung überall aufgelöst ist.

Ein strenger anfänglicher Zielwert „mittleres y+ <3“ wurde bei den scharfen Kanten auch im feineren Piloten nicht erreicht. Deshalb werden solche Rechnungen ausdrücklich als **bedingtes Wandfunktions-RANS-Screening** behandelt. Der erste Vorlauf ohne ausreichende Schichten wurde verworfen und lokal als `K01_rejected_v1` erhalten. Er wird nie für die Vergleichsrangliste verwendet. Eine numerisch konvergierte Vorauswahl ersetzt weder die Netz-/Gebiets-/Transitionssensitivität noch Messungen.

## Vergleichsmaßstab

Die zehn ursprünglichen Kandidaten erreichen im vereinfachten Modell ungefähr denselben Zielschub, in der unabhängigen CFD jedoch nicht zwangsläufig. Deshalb werden zuerst tatsächlicher CFD-Schub, Drehmoment und Wellenleistung verglichen. Zur Vorauswahl wird zusätzlich `P · (T_Ziel/T)^(3/2)` mit `T_Ziel = Masse · g · 1,055` berechnet. Das ist eine **Ähnlichkeitsabschätzung**, keine CFD am nachgetrimmten Betriebspunkt. Eine belastbare Endauswahl muss am tatsächlichen Zielschub nachgerechnet werden. Die Rotor-Gütezahl ist ideale induzierte Leistung / mechanische Leistung; sie ist kein elektrischer Motorwirkungsgrad.

Eine feinere Pilotrechnung prüft insbesondere die Wandbehandlung; kurze Diagnosevorläufe sind keine konvergierten Netzstudien. Kleine Leistungsunterschiede dürfen erst nach einer vergleichbaren, konvergierten Netz- und Gebietsprüfung als Formvorteil interpretiert werden. Bei Blattspitzen-Machzahlen um 0,3 ist zusätzlich die inkompressible Näherung zu prüfen. Ein eindeutiges globales Optimum wird nicht behauptet.

## Reproduzieren

Aus dem Repository-Stamm, mit NumPy, SciPy, Matplotlib und einem erreichbaren lokalen Docker-Daemon:

```sh
python3 modell_r04_taumel/cfd_top10/erstellen.py --iterations 500
python3 modell_r04_taumel/cfd_top10/rechnen.py --ranks 1,7,9,8,2,3,4,5,6,10 --jobs 2
python3 modell_r04_taumel/cfd_top10/beobachten.py
python3 modell_r04_taumel/cfd_top10/auswerten.py
```

Der Generator verweigert das Überschreiben vorhandener berechneter Netze. Für neue Eingaben den bisherigen generierten Fall zuerst archivieren; aktive Fälle niemals umbenennen oder überschreiben.

`--steps auto --until 750` setzt vorhandene vollständige Felder fort. Zuvor gespeicherte Felder bleiben erhalten; der Auswerter vermischt keine unterschiedlichen Fortsetzungsfenster. `--level fine` erzeugt eine feinere Geometrie-/Wandbehandlungsvariante. Zwei Solverprozesse pro Fall; zwei gleichzeitige Fälle passen zur lokalen CPU-Quote von vier Kernen.

```sh
python3 modell_r04_taumel/cfd_top10/stroemung_exportieren.py --rank 1 --time 500
python3 modell_r04_taumel/cfd_top10/plotten.py --rank 1 --time 500
```

Der Feldexport arbeitet in einer isolierten Kopie, damit aktive Kraftdateien nicht überschrieben werden. Bilder zeigen Druckbeiwerte und projizierte Relativströmung in einem Schnitt bei 70 % Radius, keine nachgebildeten Strömungspartikel. Rohdaten der dargestellten Schnitte liegen komprimiert daneben. SIMPLE-Kraftverläufe sind numerische Iterationsfolgen, keine physikalischen Zeitverläufe.
