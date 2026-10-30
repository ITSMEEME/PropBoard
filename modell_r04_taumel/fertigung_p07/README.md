# P07 – ausgewählter Kaufservo Savöx SB-2270SG+

Der Nutzer hat den **SB-2270SG+ ausdrücklich anstelle des bisherigen SB-2271SG(+) gewählt**. Die hochgeladene Datei `SB-2270SGP.STEP` wird unverändert unter `Quellen/` aufbewahrt. Ihr STEP-Dateikopf nennt `SB-2270SG+`, SolidWorks 2024 und den 15.04.2025. Herkunft: Nutzerupload; Herstellerauthentizität und gesonderte Lizenz wurden nicht unabhängig bestätigt.

## Import und Einbau

- Detaillierte Gehäuse-, Laschen-, Schrauben- und Abtriebsgeometrie statt des bisherigen generierten Servohüllkörpers.
- Sechs Instanzen in der statischen Gesamtbaugruppe; die sechs separaten schematischen Abtriebszylinder wurden entfernt, da die STEP bereits den Abtrieb enthält.
- Keine Skalierung. Die aus Zylinderflächen ermittelte Abtriebsachse (Quell-X=0, Z=0, Richtung Y) liegt an den bisherigen sechs Kinematikachsen. Die freie Spitze bei Quell-Y=16,8 mm wird auf die bisherige Hornreferenzebene gelegt. Das ist ein dokumentierter Vergleichsbezug, keine freigegebene Horn-Anlagehöhe.
- Die vorhandenen 8-mm-Funktionshörner bleiben ausdrücklich ungeklärt. Die Datei enthält kein separat identifiziertes verwendbares Servoarm-Kaufteil. Tatsächliches Horn, Aufstecktiefe, Halteschraube und Gelenkanschluss sind weiter auszulegen.

`Ausgabe/P07_SB2270SGP_Baugruppe_GESPERRT.FCStd` ist der neue statische CAD-Integrationsstand. `Ausgabe/SB2270SGP_Originalimport_GEOMETRIEPRUEFUNG.FCStd` enthält den isolierten Originalimport. Beide lassen sich ohne externe Python-Proxys öffnen. Die ursprünglichen Baugruppenstände bleiben historische Referenzen.

## Tatsächlicher Geometriebefund

**FreeCAD 1.0.2 meldet den importierten Festkörper als ungültig.** Die erweiterte Prüfung liefert `Sub-shape not in shape`. Eine Toleranzreparatur mit `Shape.fix(1e-7,1e-7,1e-3)` und eine getrennte `removeSplitter`-Probe stellen keine gültige Geometrie her. Diese Versuche werden protokolliert; ihre veränderten Ergebnisse werden nicht als Original ausgegeben und nicht eingebaut.

Der unveränderte Import wird daher nicht zur Fertigung, für boolesche Halterableitungen oder als belastbarer Kollisionsnachweis freigegeben. Nötig ist ein gültiger erneuter STEP-Export (alternativ Parasolid/BREP, falls verfügbar) oder eine nachgewiesene Reparatur mit Prüfung der Anschlussflächen. Für das komplette Kaufservo werden weiterhin keine selbst zu fertigenden Innenteile verlangt.

Gesamtabmessungen, Topologie, SHA-256 und Prüfresultate stehen in `Ausgabe/Importpruefung_P07.json`. Die Gesamthülle umfasst auch Anbaumerkmale und ist nicht automatisch das Gehäuse-Nennmaß. Aus den 25 zylindrischen Flächen am Abtrieb wird keine unbelegte vollständige Verzahnungstoleranz oder Halteschraubenspezifikation abgeleitet.

## Leistungsdaten und Simulation

`Servowahl.json` hält die neue Auswahl verbindlich fest. Masse, Spannung, Drehmoment, Geschwindigkeit und PWM des SB-2270SG+ sind noch nicht aus einer passenden Quelle übernommen. Die zuvor gelieferten SB-2271-Daten werden nicht auf den anderen Servo übertragen. H01-/M01-Flugversuche und deren Massenbudget bleiben historische Berechnungen mit dem alten Profil; P07 ist kein neu validiertes Flugmodell.

Die offenen Konstruktionspunkte aus [P06](../fertigung_p06/README.md) bleiben bestehen, insbesondere Servohalter, reale Gelenke/Hörner, Montage der Kugelpfanne, Klemmen und axiale Sicherungen. Eine detaillierte Kaufteil-STEP allein schließt diese nicht.

## Reproduzieren

Vollständiger Checkout einschließlich P06, FreeCAD 1.0.2:

```sh
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p07/importieren.py
```
