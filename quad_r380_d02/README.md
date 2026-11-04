# Quad R380 D02 – Carbonrahmen und zwei verstellbare Fußplatten

D02 setzt die neue Rahmenvorgabe um: **CBU20171005TG Ø20/17 mm** aus dem früheren Koaxialaufbau, dessen **originale geteilte Aluminiumklemmen und Isolierlagen** sowie zwei unabhängig verstellbare Fußplatten statt des großen Decks. Dies ist ein mechanischer Entwicklungsstand, keine Produktionsfreigabe.

- [Interaktive CAD-Ansicht mit zwei Verstellreglern](Mechanik.html)
- [Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D02_CFK.FCStd) · [STEP-Austauschbaugruppe](Ausgabe/QuadR380_D02_CFK.step)
- [Gesamtansicht](Tragwerk_Ansicht.png) · [Fußschlitten im Detail](Fussschlitten_Detail.png)
- [Bewertung des eingegangenen Kenndaten-Extrakts und gezielter Nachauftrag](KENNDATEN_BEWERTUNG.md)
- [Fehlende Herstellerdaten für Antrieb, Akku und Elektronik](HERSTELLERDATEN.md)
- [Elektrischer Integrationsplan](Elektrische_Integration.json) · [Stückliste](Ausgabe/Stueckliste.csv)
- [CAD- und Freigabestatus](Ausgabe/Status.json) · [Fußverstellung](Ausgabe/Fussverstellung_Pruefung.json) · [Kollisionsbefund](Ausgabe/Struktur_Kollisionen.json)
- [Detailpaket mit CAD, Quellen und Prüfsummen](QuadR380_D02_Detailpaket.zip)

## Mechanischer Aufbau

Vier Ausleger bestehen jeweils aus vier parallelen Carbonrohren zwischen gefrästen Aluminiumschotten und den originalen P12-Flanschklemmen. Die Ø20-mm-Rohre werden nicht als einzelner Ersatz für die früheren Ø50-mm-Aluminiumprofile verwendet. Die räumliche Rohrgruppe ist ein neuer Lastpfad und benötigt eigene CFK-/Knoten-/Kontakt-/Schwingungsnachweise. Ein Aluminiumnachweis aus D01 gilt hierfür nicht.

Die beiden oberen, durchgehenden Carbonrohre sind 760 mm lang, liegen bei y = +/-75 mm und werden über Aluminiumknoten und Carbonstreben abgestützt. Zwei Aluminium-Fußplatten, je **300 x 140 x 5 mm**, gleiten mit je zwei geteilten Klemmbacken auf beiden Rohren. Die 300-mm-Seite liegt quer zu den Schienen. Die Plattenmittelpunkte lassen sich links von -250 bis -130 mm und rechts von +130 bis +250 mm verschieben. Daraus ergibt sich ein Mittenabstand von **260 bis 500 mm**; die Standardposition beträgt 400 mm.

Schrauben müssen zur Verstellung gelöst und danach mit einer erst noch zu qualifizierenden Anzugstrategie wieder geklemmt werden. Der Mechanismus ist nicht für eine Verstellung unter Belastung oder während des Flugs freigegeben. Nennbohrung Ø20,6 mm und an das Istmaß angepasste Isolierlagen folgen dem P12-Prinzip. Keine Querbohrung oder Gewinde im CFK. Rutschhemmende Auflagen, Einspannsicherung und Endanschläge sind noch zu detaillieren.

In FreeCAD `Fussverstellung.Links` und `.Rechts` ändern: alle zugehörigen Platten, Backen, Isolierlagen und Verbindungsmittel folgen über Ausdrücke. Neun Grenz-/Zwischenkombinationen wurden anhand der nativen Platzierungen und der Längshüllen geprüft. Das ist noch keine vollständige Kollisionsprüfung des gesamten Verstellwegs gegen spätere Rotoren, Kabel und Anbauteile.

STEP-Austauschdatei wieder eingelesen: alle 630 Körper vorhanden und individuell geometrisch gültig.

Strukturprüfung: 484 vorselektierte BRep-Paarungen der Strukturkörper, keine Überschneidung über 0,1 mm³. ISO-Befestigungsmittel sind ausdrücklich nicht Teil dieses Befunds; deren Gewindepaarungen und Nachbarfreiräume bleiben offen.

## Quellen und Modellqualität

`Quellteile.json` dokumentiert die unverändert übernommenen P12-STEP-Geometrien samt SHA256. Diese importierten Körper werden im neuen Dokument ausdrücklich als Quellfeatures geführt; ihnen wird keine erfundene Skizzenhistorie zugeschrieben. Neue Platten, Schotten, Rohre und Fußbacken besitzen bearbeitbare PartDesign-Features; neue Stützenknoten sind bearbeitete BRep-Einzelkörper mit Bohrungen. Normschrauben und Muttern besitzen Helixgeometrie.

Wichtig: Die originalen P12-Klemmen besitzen Gewindekernkonturen. Deren Verschraubung mit den neuen ISO-Normschrauben ist kein abgeschlossener Gewindenachweis. Diese Gewindepaarungen sind ausdrücklich ungeprüft und nicht Bestandteil des Struktur-Kollisionsprotokolls. Die 94 bestandenen Gewindepaarungen und die Kollisionsfreiheit des älteren D01 werden nicht auf D02 übertragen.

CAD-Masse: etwa **21,04 kg** für den modellierten Umfang, ohne Antrieb, Akku, Kabelbaum, Schutz und Fahrwerk. CFK-Dichte 1600 kg/m³ ist eine Annahme. Die gesamte Fahrzeugmasse ist erneut zu schließen.

## Elektrischer Umfang

Punkt 3 ist **noch nicht als vollständige physische Baugruppe umgesetzt**. `Elektrische_Integration.json` benennt Leistungs-, Phasen-, Hilfs- und Signalzweige. Es ist ein Integrationsplan, kein gefertigt verlegbarer Kabelbaum. Hersteller, Typen, Packkonfiguration und Leiterquerschnitte bleiben bis zur Kennfeld-/Thermik-/Massenprüfung offen. Die vollständige Datenanforderung steht in `HERSTELLERDATEN.md`.

Vorhandene MN1330-Unterlagen decken den QuadR380-Dauerbetrieb nicht nachweislich ab. EMRAX, Plettenberg, MGM COMPRO, Mejzlik und Molicel sind Beschaffungskandidaten. Ihre Bauformen werden ohne belegte Zeichnungen nicht als schematische Ersatzkörper ins Modell gesetzt. Die neue Rahmenform ersetzt auch keinen Schutz- und Rotorfreiraumnachweis.

## Reproduktion

FreeCAD mit PartDesign, MeshPart und System-Python. `erstellen.py` baut den Rahmen, `ableiten_pruefen.py` prüft die native Verstellung und exportiert die tatsächlichen CAD-Flächen, `kollisionen_pruefen.py` prüft ausdrücklich nur Strukturkörper ohne ISO-Befestigungsmittel; sämtliche Gewindepaarungen und Verbindungsmittelfreiräume bleiben offen, `viewer_pruefen.cjs` testet die Browseransicht. Die Gesamtprüfung kann länger dauern.

Abhängigkeiten im Repository: P12-STEP-Klemmen/Isolierlage unter `../kreis_r04/mn1330_p12/Ausgabe/STEP/` sowie die gepinnten Normteil-BReps unter `../quad_r380_d01/Quellen/Normteile/`. Im ZIP sind diese Abhängigkeiten unter den gleichen relativen Pfaden enthalten. Der zusätzliche M6x40-Datensatz liegt lokal unter `Quellen/Normteile`; die Fasteners-Quellrevision ist unverändert `fddd07af422b7d3a69098b32333711c5eeae184c`.
