# P06 – Fertigungsvollständigkeit der gesamten Baugruppe

**Die Anforderung „keine schematischen Bauteile, vollständig fertigungsbereit“ ist im vorhandenen Stand noch nicht erfüllt.** P06 dokumentiert den tatsächlichen Stand der P05-Baugruppe vollständig, statt Geometrien ohne Anschlussdaten zur Fertigung freizugeben. P06 ist eine Prüfung, keine fertig ausgearbeitete neue Konstruktion.

[Bauteilbericht mit Mengen und konkreten Lücken](Bauteilbericht.md), maschinenlesbar als `Ausgabe/Vollstaendigkeitspruefung.json` und `Ausgabe/Bauteile_und_offene_Fertigungspunkte.csv`.

Die native Datei `Ausgabe/P06_Bauteilpruefung_NICHT_FERTIGUNGSBEREIT.FCStd` enthält bei jedem Bauteil die Eigenschaften `P06_Darstellung`, `P06_Beschaffung`, `P06_Offen` und `P06_Fertigungsbereit`. Freiräume sind ausdrücklich keine Bauteile. Auch in der Baugruppe noch nicht vorhandene Servo-Montagehalter und Sicherungsbefestigungen werden als fehlend erfasst. Ein geometrisch gültiger Festkörper bekommt dadurch keine Fertigungsfreigabe.

Die Prüfung vergleicht die gespeicherte Baugruppe mit P05. Sie lässt Geometrie und Positionen unverändert, korrigiert aber die veraltete Kaufteilkategorie des selbst zu fertigenden M5-Ritzels und kennzeichnet die Savöx-Anschlussreferenzen. M01 bleibt ein historisches Funktions-/Bewegungsmodell mit schematischen Innenteilen, kein Fertigungsdatensatz. Diese Innenteile wurden schon in P02 zugunsten kompletter Kaufteilreferenzen entfernt.

## Benötigte externe Anschlussdaten

- Servo: tatsächliche SG/SG+-Variante, Laschendicke, Loch-/Schlitzmaße, konkretes kompatibles 25T-Horn einschließlich Halteschraube, radialer Kugelposition und Hornhöhe.
- Lager: tatsächliche 6806-/6809-Artikel mit Fasen-/Schultergrenzen, Grenzmaßen und Lagerluftvariante. Hersteller-STEP ist optional; eine vollständige Anschlusszeichnung reicht.
- Gelenke: konkrete Kugelbolzen und Pfannen samt Gewinde, Außenmaßen und Schwenkbereich; insbesondere eine reale Lösung für 15 mm Kugelmittenabstand.
- F405-V4-/55A-Stack: tatsächliche Dämpfer und Anlagehöhen.

Die Motorangaben M3 maximal 3 mm / M5 nutzbar 9 mm und der Lochkreis Ø16 sind bereits übernommen. Innenzeichnungen der komplett gekauften Lager, Motoren und Servos werden nicht benötigt.

## Noch zu leistende eigene Konstruktion

Servo-Montagehalter und Lastpfad, montierbare Kugel-/Pfannenpaarung, reale Kugelbolzenanschlüsse, axiale Pitchhebel-/Rotor-/Stiftsicherungen, Klemmschraubverbindungen, Lagerpassungen, abschließende Kabelwege sowie Werkstoff-/Prozess- und Fertigungstoleranzen. Diese Aufgaben sind Konstruktionsarbeit und werden nicht durch bloße Herstellerdaten ersetzt. Festigkeit und Betriebsnachweise sind zusätzlich zur Fertigungsgeometrie zu behandeln.

Normgerecht vereinfachte Gewindedarstellung ist zulässig, wenn Gewinde, Tiefe, Toleranz und Anlageflächen eindeutig dokumentiert sind. Kosmetisch modellierte Gewindeflanken allein lösen keine der genannten Lücken.

## Wiederholen

Mit FreeCAD 1.0.2 aus dem Projektstamm:

```sh
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p06/pruefen.py
```

Jede Bauteilkennung muss ausdrücklich bewertet sein; unbekannte Kennungen brechen die Prüfung ab. Das Ergebnis ist an den SHA-256-Wert des geprüften P05-Datensatzes gebunden. Eine spätere neue Baugruppe muss erneut bewertet werden.
