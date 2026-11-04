# Quad D11 – motornahe Reglerhalter

Der vorausgehende Stand D10 ist als `6b5d0f24aebf15275e134a535a4cd5977d6c2650` auf `origin/main` gepusht. D11 ergänzt vier motornahe Montageeinheiten für alle zehn HEP-S-Durchmesser und fünf Rohrvarianten. Die Regler selbst sind mangels eindeutiger Kaufteilunterlagen noch nicht fertig modelliert oder elektrisch angeschlossen.

[3D-Ansicht öffnen](Projekt.html) · [Detailbild der Halter](Ausgabe/Reglerhalter_42_V4.png) · [FreeCAD-Baugruppe](Ausgabe/Quad_Motornahe_Reglerhalter.FCStd) · [Montagedaten](Ausgabe/Regler_Montage.json) · [Kollisionsprüfung](Ausgabe/Reglerhalter_Pruefung.json) · [Browserprüfung](Ausgabe/Viewer_Pruefung.json)

## Mechanischer Aufbau

Je Motor liegt die Mitte des geplanten Reglers radial 140 mm zur Rahmenmitte versetzt, tangential über dem ausgewählten oberen beziehungsweise ersten Rohr. Zwei unabhängige, geteilte 16-mm-Schellen befestigen den Träger am Rohr. Die vorhandene Motor-/Schubklemmung wird nicht mitbenutzt; das Carbon erhält keine Querbohrungen. V1 wird an Ø35/32 mm angepasst, V2–V5 an Ø20/17 mm. Das größere V1-Rohr ist eine Beschaffungsannahme, kein belegter CBU-Artikel.

Der zusammenhängende Aluminiumkörper besitzt zwei 146 × 10 × 2 mm Montageschienen, Querstege und offene C-Stützen. Die Schellen haben modellierte Deckel, M4 × 30-Schrauben, Muttern und Scheiben. 0,3-mm-GFK-Zwischenlagen trennen Aluminium und Carbon geometrisch. Die Werkstoffannahmen sind EN AW-6082-T6, Stahl und GFK; daraus folgt keine Festigkeitsfreigabe. Die dünnen Stützen und die nur 16 mm langen Klemmstellen müssen insbesondere auf Schwingung, Ermüdung, Schlupf und CFK-Querdruck bemessen werden.

Die reine modellierte Montageeinheit wiegt ungefähr 112 g, bei V1 ungefähr 125 g, einschließlich Befestigung und isolierender Teile. Vier Einheiten addieren etwa 447–500 g. Die unbekannte tatsächliche Reglermasse ist nicht enthalten.

## Reglerzeichnung und Schrauben

Die vom Nutzer gezeigte Zeichnung enthält 74 × 146 × 39,5 mm sowie ein 66 × 126 mm Raster mit vier M3-Gewinden, Gewindetiefe 4 mm. Ihr genauer Reglertyp und Revisionsstand sind unbestätigt. M200A24S ist eine vorhandene Empfehlung zum MN1330, keine verifizierte Zuordnung dieser Zeichnung. Die Zeichnungsreferenz steht im [Datennachtrag](../quad_r380_varianten/DATENNACHTRAG.md).

Vier M3 × 6 mit 0,5-mm-Scheiben durchsetzen die 2-mm-Schiene und ein 0,5-mm-Isolierpad. Daraus folgen nominell 3 mm Gewindeeingriff. Die tatsächliche Normteilgeometrie reicht wegen des modellierten Gewindeendes 3,6375 mm in den angenommenen Blindraum hinein; zur gezeichneten Tiefe bleiben 0,3625 mm. Das ist keine Toleranz- oder Drehmomentfreigabe. Herstellerseitige Tiefe, Fasen, Innengewinde und vorgeschriebene Befestigungsrichtung müssen bestätigt werden.

Der orange Kantenrahmen ist ausschließlich der unbestätigte Einbaubauraum. Er wird ausdrücklich nicht als fertiges OEM-Gerät, Kühlkörper oder massiver Regler gezählt. Schienenoberkante liegt bei Welt-Z −50 mm, geplanter Regler bei −92 bis −52,5 mm. Dadurch liegt diese Planung unter den Rotorhüllen; reale Anschlüsse und bewegte Leitungsenden sind noch nicht erfasst.

## Verkabelung und offene Kaufteildaten

D10 führt DC-Plus, DC-Minus und die Signalleitung innerhalb der Carbonarme. Die Enden bleiben bis zur Bestätigung der Anschlüsse offen. In D11 sind noch keine erfundenen Stecker oder Phasenleitungen ergänzt. Für den vollständigen motorennahen Reglereinbau fehlen:

- Exakter Reglertyp, Revision und OEM-STEP oder vollständig bemaßte Gehäuse-/Anschlusszeichnung einschließlich Kühlrippen und Befestigungsseite.
- Position, Richtung, Abmessungen und elektrische Zuordnung der DC-, Phasen- und Signalanschlüsse; mitgelieferte Leitungen, Querschnitte, Außendurchmesser, Mindestbiegeradien, Anschluss- und Zugentlastungsvorgaben.
- Masse und Schwerpunkt; zulässige Einbaulage, Kühlabstände und thermische Randbedingungen.
- Herstellergrenzen für lange batterie-seitige DC-Zuleitungen, erforderliche Stützkondensatoren, Vorladung und Schutzbeschaltung; Dauer-/Spitzenstrom und Spannungsfreigabe zum tatsächlichen Akku und MN1330-Arbeitspunkt.
- Verifizierte Motor-Kabelausgänge und Phasenanschlüsse sowie finale Akku-/Verteiler-/Sicherungs- und Steckerdefinition.

Der nominell enge Signal-/DC-Durchgang aus D10 wird durch D11 nicht größer. Herstellerleitungstoleranzen, thermische Stromtragfähigkeit und Scheuerschutz bleiben zu prüfen. Keine Produktions- oder Flugfreigabe.

## Abgeschlossene Prüfung

Alle 50 nativen Umschalterstellungen und alle 50 Browser-Konfigurationen sind bestanden. Die geometrische Prüfung meldet keine Überschneidungen oberhalb der 0,1-mm³-Schwelle bei 9326 detaillierten Vergleichskandidaten. Die neuen Bauteile bleiben mindestens 41.26 mm unter der angenommenen Rotorunterkante. Alle Berichte und der Viewer beziehen sich auf dieselbe native Datei mit SHA-256 `283a7d862d0970d448144474b2cb1c6ad909b1befcd2f3a91e6a352addceef5e`. Die Browserprüfung erfasst auch eine mobile Ansichtsgröße.

## Prüfumfang und Reproduktion

`pruefen.py` prüft die neuen physischen Bauteile gegen die jeweils gewählten Altteile an allen vier Armen sowie interne Bauteilpaare an einem Arm je Konfiguration; die anderen drei sind starre Kopien. Der unbestätigte Regler wird zusätzlich nur als Bauraumquader gegen die Altteile geprüft. Die Volumenschwelle beträgt 0,1 mm³. Das ist eine nominale CAD-Überschneidungsprüfung, kein Toleranz-, Klemm- oder Festigkeitsnachweis. Die Rotorprüfung aus D10 wird als Quellnachweis beibehalten; die neuen Bauteile werden zusätzlich über ihre Z-Obergrenze gegen die angenommene Rotorunterkante bei 124 mm abgegrenzt.

`normteile.py` erzeugt die M3 × 6 aus dem dokumentierten FastenersWB-Stand; `bauen.py` erzeugt die native Baugruppe aus D10; `viewer_export.py` ergänzt die tatsächlich erzeugten Oberflächen. FreeCAD 1.0 und die vorhandenen D07-Geometriehelfer werden benötigt. `D11_GROUP=0` bis `3` teilt die geometrische Prüfung nach Propellerindex modulo vier auf; die Ergebnisse müssen anschließend zu einem vollständigen 50-Zustände-Bericht mit `pruefberichte_zusammenfuehren.py` zusammengeführt werden. `viewer_pruefen.cjs` prüft die lokale Browserdarstellung mit Playwright/Chromium und erstellt Screenshots.
