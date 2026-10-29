# Gegenläufiger Flügelumlauf: explorative CFD

Diese Untersuchung ist ein **selbst implementierter, noch nicht gegen einen externen Referenzfall quantitativ validierter 2D-CFD-Prototyp**. Sie ist keine realmaßstäbliche Simulation des vollständigen Boards. Aus ihren Kräften dürfen keine reale Traglast, elektrische Leistung, Flugzeit oder Personenflugfähigkeit abgeleitet werden.

## Was berechnet wird

Ein einzelnes Ovalmodul mit acht bewegten NACA-0012-Profilen wird in einer zweidimensionalen x-z-Schnittebene simuliert. Die beiden Drehrichtungen werden in getrennten Rechnungen untersucht. Ihre dreidimensionale gegenseitige Beeinflussung wird nicht berechnet.

Methode: D2Q9-Lattice-Boltzmann, BGK-Kollision, bewegte Halfway-Bounce-back-Randbedingungen, Impulsaustausch an Fluid/Festkörper-Grenzen und Impulskorrektur für überdeckte/freigegebene Zellen. Anfangs ruht das Fluid; die Bewegung beginnt ohne Anfahrrampe. Außen liegt ein periodisches Gebiet mit einer Dämpfungszone zur Ruhegleichverteilung. Das ist eine vereinfachte Fernfeldbehandlung, keine geprüfte offene Ausströmrandbedingung. Es gibt keine Bodenfläche.

Die Bewegung und Pitch-Verstellung werden vorgeschrieben, nicht aus Magnet-, Motor- oder Strukturkräften berechnet. Leitbahnen, Schlitten, Deck, Mensch und Flügelspitzen fehlen in der Strömungsrechnung. Die Profilkontur verwendet die geschlossene NACA-0012-Dickenformel; am groben Gitter wird sie treppenförmig angenähert.

## Annahmen

Die Geometrie stammt aus `cad/umlauf_parameter.json`: gerader Bahnabschnitt 1,3 m, Umlenkradius 0,18 m, Sehne 0,12 m, acht Flügel je Modul. Im CAD beträgt die Spannweite 0,6 m; CFD behandelt unendliche Spannweite bzw. Kräfte pro Einheitsspannweite. Der Nasenwinkel folgt der Bewegungstangente zuzüglich `alpha = 12° × Tangente_x`. Dies ist ein neuer Steueransatz, kein optimierter Pitch-Verlauf.

**Reynolds-Zahl Re = 40**, bezogen auf Umlaufgeschwindigkeit und Sehne. Die Lattice-Geschwindigkeit beträgt 0,04, die Gitterauflösung 12 bzw. 16 Zellen pro Sehne. Das hält den ersten Rechentest numerisch handhabbar, entspricht aber ausdrücklich nicht dem realen Luftbetrieb. Bei der nur als Referenz angenommenen Umlaufgeschwindigkeit 10 m/s ergäbe Luft mit kinematischer Viskosität 1,5×10⁻⁵ m²/s etwa Re = 80.000. Der Rechentest bei Re = 40 entspräche dann einer künstlichen Viskosität von 0,03 m²/s.

Das Rechengebiet misst ungefähr 2,9 × 1,5 m bei Skalierung auf die CAD-Sehne. Gebietseinfluss, Zeitauflösung und Gitterunabhängigkeit sind nicht abschließend nachgewiesen. Eine stabile Rechnung allein bedeutet keine Genauigkeit oder Konvergenz.

## Reproduzieren

Im Repository-Verzeichnis, mit Python 3.12:

```sh
python -m pip install --target .cfd-tools -r cfd/requirements.txt
NUMBA_NUM_THREADS=2 python cfd/umlauf_lbm.py --cycles 2 --name forward_c16
NUMBA_NUM_THREADS=1 python cfd/umlauf_lbm.py --cycles 2 --direction -1 --name reverse_c16
NUMBA_NUM_THREADS=1 python cfd/umlauf_lbm.py --cycles 2 --chord-cells 12 --name forward_c12
NUMBA_NUM_THREADS=1 python cfd/umlauf_lbm.py --cycles 2 --chord-cells 12 --pitch 0 --name zero_pitch_c12
NUMBA_NUM_THREADS=1 python cfd/umlauf_lbm.py --cycles 0.02 --stationary --name rest_control
python cfd/auswerten.py
MPLCONFIGDIR=/tmp/propboard-matplotlib python cfd/visualisieren.py
```

Die Visualisierung benötigt zusätzlich Matplotlib, das in dieser Umgebung bereits vorhanden ist. CAD-Erzeugung separat mit `/usr/bin/python3 cad/umlauf_erstellen.py` (FreeCAD-Python-Modul für Python 3.13). Die beiden Python-Installationen nicht vertauschen.

## Ergebnisse und Prüfumfang

JSON-Dateien enthalten Laufparameter, Schritte, Stabilitätsbeobachtungen und Umlaufmittelwerte. CSV-Dateien enthalten jeden zehnten Schritt; NPZ-Dateien die vollständige Krafthistorie und das letzte Strömungsfeld. `Auswertung.json` und `Ergebnisbericht.md` fassen die tatsächlich abgeschlossenen Läufe zusammen.

Kraftbeiwerte sind normiert auf `0,5 × rho × U² × 8 × Sehne` pro Einheitsspannweite. Für den Momentenbeiwert kommt die Sehne als Hebellängenreferenz hinzu. Positive z-Kraft ist nach oben gerichtet. Der ausgegebene `wall_power_proxy` enthält keine vollständige Arbeitsbilanz beim Freigeben von Gitterzellen und darf nicht als Wellen- oder elektrische Leistung verwendet werden.

Der Ruhezustand kontrolliert das Erhalten einer ruhenden Strömung. Der Null-Pitch-Lauf untersucht den Einfluss der Pitch-Steuerung. Der Gittervergleich zeigt Auflösungseinfluss; zwei Gitter allein sind kein Konvergenznachweis. Der Vergleich erster/zweiter Umlauf zeigt Einschwingeffekte. Die getrennten Gegenlaufergebnisse liefern keine vollständige Momentenbilanz eines gekoppelten Fahrzeugs.

## Nächste belastbare Untersuchung

Benötigt werden ein festgelegter Betriebspunkt, ein geschlossenes Massenbudget und eine höher aufgelöste, verifizierte 3D-Strömungsrechnung bei realistischer Reynolds-Zahl. Sie muss bewegte/pitchende Körper, Flügelspitzen, beide Module, Deck und die relevanten Störkörper berücksichtigen. Zusätzlich sind Gitter-, Zeit- und Gebietsstudien, periodisches Einschwingen sowie eine vollständige Kraft-, Momenten- und Leistungsbilanz erforderlich. Eine spätere Prüfstandsmessung muss das Modell überprüfen.

Magnetkräfte, Verlustleistung der Führung, Fangführung, Regelung, Ausfall einer Bahn und Ermüdung sind eigene Untersuchungen. Bei 10 m/s und 0,18 m Umlenkradius beträgt bereits die Zentripetalbeschleunigung 556 m/s², etwa 57 g. Dies ist eine Kinematikrechnung, kein Lastnachweis; die bewegte Masse ist noch unbekannt.
