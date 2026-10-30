# P05 – EMAX-Motoranschluss mit bestätigten Anschlussmaßen

Die Nutzerangabe „M5, 9mm + M3 Tiefe = 3mm“ wird als 9 mm nutzbares M5-Ausgangsgewinde und maximal 3 mm M3-Einschraubtiefe ab Motorauflage interpretiert. Das EMAX-Lochbild bleibt 4×M3 auf Teilkreis Ø16 mm, nicht 16×16 mm.

## Montageentwurf

- Je Motor vier M3×7 durch 4 mm Motorplatte und 0,5 mm Scheibe (nominal ISO 7089, 3,2×7×0,5): 2,5 mm Einschraubtiefe, 0,5 mm Reserve.
- Das in anschlussdaten.json vorgeschlagene Annahmebudget ergibt 2,05–2,95 mm. Dies sind zu prüfende Beschaffungs-/Fertigungsgrenzen, keine bestätigten Lieferantentoleranzen.
- Je Motor ein neu konstruiertes Gewinderitzel: Modul 1, 20 Zähne, Eingriffswinkel 20°, Breite 5,50 mm, Innengewinde M5×0,8-6H durchgehend, vorgeschlagen C45E.
- Dünne M5-Kontermutter, nominal ISO 4035, Schlüsselweite 8, Höhe 2,7 mm. Gewindestapel 8,2 mm; 0,8 mm der bestätigten 9 mm verbleiben. Keine zusätzliche 1-mm-M5-Scheibe: damit wären 9,2 mm erforderlich.
- Ritzelunterkante lokal z=11,4 mm; Mutterende z=19,6 mm; Abstand zur Glockenfront 4,8 mm. Axiale Verzahnungsüberdeckung 5,1 mm.

Eine glatte Ø5-Bohrung allein befestigt das Ritzel nicht. Die CAD-Bohrung Ø5 stellt den nominalen Gewinderaum dar; für die Fertigung gilt M5×0,8-6H (Kernloch 4,2 mm), nicht eine glatte Ø5-Passung. M3-Motorbohrungen sind nominelle Einsteckräume mit 3 mm Tiefe. Gewindeflanken und interne OEM-Geometrien werden nicht als vermessen ausgegeben.

## Dateien und Prüfung

Ausgabe/P05_Baugruppe_Motoranschluss_GESPERRT.FCStd enthält die vollständige statische Baugruppe. Ausgabe/P05_Anschlussbauteile.FCStd enthält fünf getrennt angeordnete Anschlussreferenzen; einzelne STEP-Dateien liegen daneben. Mit P05_oeffnen.FCMacro lässt sich die Baugruppe öffnen.

Pruefbericht_P05.json dokumentiert acht Schrauben, acht Scheiben, zwei Ritzel und zwei Muttern, nominale Kollisions-/Auflageprüfungen sowie 16 Stichproben über eine Zahneingriffsperiode. Die native Baugruppe wurde erneut geöffnet. Diese Stichproben sind kein kontinuierlicher Verzahnungs- oder Festigkeitsnachweis.

## Offene Freigaben

Anzugsmomente, Vorspannung/Losdrehsicherung, tatsächliche Gewindeausläufe, Rundlauf, Zahnqualität und Dauerfestigkeit sind noch zu bestimmen. Außerdem fehlen weiterhin verbindliche Servohebel-/Laschenanschlüsse, konkrete Lagerausführungen und Passungen, passende kurze Kugelgelenke sowie abschließende eigene Halter-/Sicherungsdetails. Die Gesamtbaugruppe ist deshalb ausdrücklich nicht zur Fertigung oder zum Flug freigegeben. Frühere Flug- und Massenberichte wurden durch P05 nicht neu validiert.

## Herkunft / Wiedererzeugung

M3×7 ist eine gekürzte Referenz aus dem M3×10-STEP des FreeCAD-Library-Projekts (nur Schaft gekürzt, keine Skalierung), kein originales EMAX-Schraubenmodell. Quellenmanifest und CC-BY-3.0-Lizenz liegen unter Quellen. Ritzelgeometrie nutzt das installierte FreeCAD-PartDesign-fcgear-Modul. Wiedererzeugung mit erstellen.py erfordert den vollständigen Projektcheckout samt P04/P02 und FreeCAD 1.0.2; das ZIP enthält selbständig öffnungsfähige native Ergebnisse.
