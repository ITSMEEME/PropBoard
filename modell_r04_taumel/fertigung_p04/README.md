# P04 – Motoranschluss nach der bereitgestellten EMAX-Zeichnung

Die bemaßte Zeichnung hat Vorrang vor der vorherigen Textrecherche. Sie zeigt **4–M3 auf einem Lochkreis Ø16 mm**, nicht 16×16 mm. Das entspricht einem quadratischen Achsabstand von **11,3137 mm**. Die ursprüngliche F01/H01/P02-Anordnung war korrekt. Die zwischenzeitliche P03-Rasteränderung wurde verworfen; falsche CAD-/STEP-/DXF-Dateien wurden entfernt und der historische Erzeuger gegen versehentliche Benutzung gesperrt.

## Aktuelle Dateien

- [`Ausgabe/P04_Baugruppe_PCD16_GESPERRT.FCStd`](Ausgabe/P04_Baugruppe_PCD16_GESPERRT.FCStd): aktuelle Kaufteil-Ansicht mit korrekten Motorplatten und zwei Motor-Anschlussmodellen.
- [`Ausgabe/EMAX_ECOII2306_Anschlussmodell_P04.FCStd`](Ausgabe/EMAX_ECOII2306_Anschlussmodell_P04.FCStd) und STEP: aus Zeichnungsmaßen erzeugtes **Kaufteil-Einbaumodell**, kein heruntergeladenes Original-CAD und keine Motor-Eigenfertigungszeichnung.
- [`Ausgabe/TM08_P04_Motorplatte_PCD16_ENTWURF.FCStd`](Ausgabe/TM08_P04_Motorplatte_PCD16_ENTWURF.FCStd) und STEP: ursprüngliche korrekte Plattengeometrie; weitere eigene Schnittstellen bleiben offen.
- `Ausgabe/Motorbohrbild_P04.csv` und `Nur_Motorbohrbild_P04_PCD16_ENTWURF.dxf`: ausschließlich die vier Motor-Freibohrungen D3,4 auf PCD16. Keine vollständige freigegebene Fertigungszeichnung.
- `Ausgabe/Pruefbericht_P04.json`: geometrische Proben des richtigen/falschen Lochbilds, Motormodellhöhe 31,6 mm, native Wiederöffnung und nominale Motor-/Ritzelprüfung.

`P04_oeffnen.FCMacro` öffnet die aktuelle Baugruppe. Die gekauften Lager/Motoren/Servos werden nicht zur Eigenfertigung ihrer Innenteile aufgeteilt.

## Aus der Zeichnung übernommen

| Merkmal | Zeichnungswert |
|---|---:|
| Befestigung | 4×M3 auf Ø16-Lochkreis |
| Außendurchmesser | 28 mm |
| Gesamthöhe | 31,6 mm |
| Abtriebsüberstand ab Glockenfront | 13 mm |
| Abtriebsspitze bis untere Glockenkante | 25,3 mm |
| Lager-/Innenwelle | 4 mm |
| Propelleranschluss | M5 |
| KV1900-Masse ohne Silikonkabel | 30,2 g |
| Aufbau | 12N14P |
| Leerlaufstrom bei 10 V / Widerstand | 1,3 A / 62 mΩ |
| Zellen / Spitzenstrom laut Tabelle | 3–6S / 46 A bei 6S |
| Maximalleistung laut Tabelle | 1160 W bei 6S, keine bestätigte Dauerleistung |
| Leitung | 20 AWG, 120 mm |

Aus den axialen Maßen folgen 18,6 mm von der Montagefläche bis zur Glockenfront, 6,3 mm bis zur unteren Glockenkante und 12,3 mm Glockenhöhe. Diese Daten sind in `Motordaten_EMAX_Zeichnung_P04.json` erfasst. Quelle ist das von dir bereitgestellte Herstellerbild; eine separat heruntergeladene Originaldatei oder Quellen-URL liegt nicht vor.

Das Einbaumodell verwendet die belegten Achs-/Montage-/Außenmaße. Die nicht bemaßte Fußkontur und Lüftungsöffnungen werden nicht erfunden. In diesen Bereichen ist die Ø28-Grenzhülle konservativ. Die vier Gewindepositionen sind am separaten Anschlusspunkte-Objekt auf der Montagefläche markiert; eine nicht bekannte M3-Blindtiefe wird nicht als tatsächlich ausgeführte Bohrung vorgetäuscht. Die Ø5-Abtriebshülle beschreibt den M5-Anschluss, keine verifizierte glatte Ø5-Passwelle. Die innere Ø4-Welle ist davon zu unterscheiden.

Die Motor-Montageflächen bleiben in der bisherigen Baugruppe bei lokal z=43 mm. Mit realen 31,6 mm Gesamthöhe liegt die obere Abtriebsspitze bei Welt-z=41,4 mm, die untere bei −41,4 mm. Motor und vorhandenes nominales Ritzel überschneiden sich nicht. **Das beweist noch keine geeignete Ritzelklemmung, Gewindetragfähigkeit oder axiale Sicherung.** Die exakte M5-Gewindelänge und maximale M3-Einschraubtiefe fehlen.

Die Motor-Komponentenmasse ist mit 30,2 g ohne Silikonkabel beschriftet. Die älteren H01/M01-Gesamtmassen-/Flugrechnungen werden dadurch nicht unbemerkt als neu berechnet ausgegeben. Sie enthalten weiterhin ihre dokumentierten Motor-/Kabelannahmen. Die statische P04-Kaufteil-Ansicht ist keine neue dynamische Flugvalidierung.

## Einordnung der zusätzlich eingefügten Textrecherche

Die Textrecherche bleibt als historische, nicht primär belegte Quelle getrennt erfasst (`../fertigung_p03/Eingang/…` und `Datenabgleich_P03.json`). Die neue Motorzeichnung bestätigt einige Werte und widerlegt das 16×16-Raster.

- **Savöx SB-2271SG+:** 8,4 V/25 kg·cm sowie neue Stellzeiten, Strom-/PWM-Angaben stammen aus der unverklinkten Recherche, nicht aus der vorliegenden Motorzeichnung. Die frühere Tabelle nannte 6,0–7,4 V und leicht andere Stellzeiten. SG/SG+-Versionen und Quellen dürfen nicht vermischt werden. Es wurde keine reale BEC-/PWM-Konfiguration automatisch auf 8,4 V umgestellt. Bei 7,4 A je blockiertem Servo sind für sechs Servos rechnerisch 44,4 A beziehungsweise 328,56 W an 7,4 V möglich; das ist ein Spitzenfall, kein Dauerstrom. Die 8,4-V-Stromaufnahme ist nicht angegeben.
- **Horn:** „8 mm Extended“ belegt keinen 8-mm-Anlenkradius. Artikelidentität und Lochradius bleiben ungeprüft. Die angebliche M3-Anlenkung passt nicht automatisch zu den bisherigen M2-Anschlüssen. Der 8-mm-Radius ist ein Konstruktionsziel; für ein konkretes verfügbares Horn mit anderem Radius kann die Kinematik neu berechnet werden.
- **Lager:** Übertragene Toleranzen eines ähnlichen Lagers werden nicht als Grenzmaße beider gewählten Artikel freigegeben. Schulter- und Laufbahndetails folgen nicht allein aus ISO-15-Hauptmaßen. Die tatsächlichen Artikel/Varianten und ihre Daten sind noch festzulegen.
- **Gestänge:** Ein generisches 78-mm-Gestänge passt nicht zu den 15-mm-Blattgestängen dieser Eigenkonstruktion. Reale kurze Gelenke und Verstellbereiche sind nötig; der Verweis auf eine fremde Modell-Bauanleitung löst diese Schnittstelle nicht.
- **Elektronik:** V3/60A-Grommet-Beispiele werden nicht auf den vorgesehenen V4/55A-Stack übertragen. Aus einer Bezeichnung „M3×8“ lässt sich keine vollständige Tüllengeometrie ableiten.

## Verbleibende Fertigungspunkte

Siehe [`Noch_benoetigte_Daten_P04.md`](Noch_benoetigte_Daten_P04.md). Original-STEP ist hilfreich, aber nicht zwingend, wenn alle relevanten Anschlüsse vollständig bemaßt oder am tatsächlichen Kaufteil belastbar gemessen sind. Die bereits geklärten Motormaße werden nicht erneut angefragt.

Die Gesamt-Fertigungsfreigabe bleibt **gesperrt**: unter anderem Schraubeneingriff/M5-Ritzelverbindung, passende Horn-/Gelenkprodukte, tangentiale Servohalter, Lagerpassungen/-sicherungen, montierbare Kugel-/Innenringpaarung, Werkstoff-/Prozessfestlegung und Kabeldurchführungen sind noch zu konstruieren beziehungsweise abzugleichen. Für diese Eigenfertigungsaufgaben werden die fehlenden Anschlussdaten benötigt; es geht nicht um Motor-/Servo-Innenfertigung.

```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
python modell_r04_taumel/fertigung_p04/daten_erstellen.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p04/erstellen.py
```

Regeneration der Baugruppe benötigt den vollständigen Checkout samt P02-Basis. Die gespeicherten nativen P04-Dokumente sind statisch und zum Öffnen von Community-Erzeugern unabhängig.
