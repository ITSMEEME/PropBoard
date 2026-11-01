# P12 · MN1330 · mechanischer Zwischenstand

Separate Großmaßstab-Revision. Der kleine P11-Stand wird nicht überschrieben. Nutzer bestätigt150kg Gesamtmasse und850min⁻¹ als Auslegungswerte. Akku wird vorerst nicht als Auslegungsgrenze verwendet. Eine Überdrehzahl ist noch nicht definiert.

## Parametrisches Modell

**153 numerische Eingaben** treiben die vorhandenen Körper und Anschlüsse über native FreeCAD-Ausdrücke. Für die Bearbeitung `P12_oeffnen.FCMacro` ausführen und in der gelben Spalte der Tabelle `Parameter` ändern. Danach F5; STEP/STL und Stückliste mit `P12_Exportieren.FCMacro` aktualisieren.

[Bedienung und Parameterübersicht](PARAMETER.md) · [Aktuelle Parameter](parameter.json) · [Parametrik-Prüfung](Ausgabe/Parametrik_Pruefung.json)

## Aktueller CFK-Rahmen

Standard ist jetzt `frame_mode=1`: tragende Rundrohre CBU20171005TG,20×17×1000mm. Schräge Streben verbinden Motorplatten und polygonalen Außenrahmen. Sämtliche Hauptrohre bleiben ohne Querbohrungen; geteilte Klemmen und Isolierlagen bilden die Schnittstellen. Lokale Motor-/Mittelstützenplatten, Führungen und Knoten bleiben metallisch.

[CFK-Aufbau und Grenzen](CFK_RAHMEN.md) · [Zuschnittliste](Ausgabe/CFK_Zuschnitt.csv) · [Beschaffung](Ausgabe/CFK_Beschaffung.json)

Der Ausgangsstand aus Aluminium bleibt mit `frame_mode=0` verfügbar. Seine native Referenz liegt unter `Varianten/Aluminium/`. Die Rohrwahl ist noch kein Tragfähigkeitsnachweis.

[Schrägansicht](Ausgabe/Zwischenstand_P12_Perspektive.png) · [Drauf-/Vorderansicht](Ausgabe/Zwischenstand_P12_Orthogonal.png) · [FreeCAD](Ausgabe/P12_MN1330.FCStd) · [STEP](Ausgabe/P12_MN1330.step)

Aktueller Standard:735 Instanzen,155 Geometrietypen, Außenmaße1790×1784,1×776mm.77 Zuschnitte benötigen nach der aktuellen Packung25 Rohlinge, entsprechend1125,50€ reinem Rohrpreis.

Die aktuelle Stückzahl und die gemessenen Außenmaße stehen in `Ausgabe/Pruefung.json`. Die BRep-Körper enthalten Fertigungsmerkmale, Nennkonturen und offene Punkte. Gewinde werden durch Kern-/Nenndurchmesser und Beschriftung beschrieben; keine helikalen Gewindeflanken. Flügel sind massive aerodynamische Referenzkörper, keine gefertigten CFK-Bauteile.

## Noch offen — nicht als fertig darstellen

Schrauben und Muttern, Klemmdruck-/CFK-/Knotennachweise, Pitchwellen und deren Lagergehäuse, Verbindung der äußeren Laufbahn zum Rotor, Taumelscheibenlager und vollständige Aktuator-/Pitchanlenkung, Motor-Gewindetiefen, Lagerpassungen/Vorspannung, Schweißnahtbemessung, Oberflächen/Härte, CFK-Laminat und Wellenanbindung. Diese Punkte verhindern derzeit eine Fertigungsfreigabe. Keine Fertigung nach diesem Zwischenstand beauftragen.

Die Membran soll axiale Lasten vom Motorlager entkoppeln. Dass ihre Steifigkeit und Dauerfestigkeit dazu ausreichen, ist noch zu berechnen. Ebenso ist die voll belastete V-Rollenführung noch nicht bemessen. Vorläufige Werkstoffe und Standardlager sind keine Tragfähigkeitszusage.

## Reproduzieren

```bash
./p12.sh
./p12.sh --set rotor_radius=650 --set level_spacing=300 --output /tmp/P12_Kompakt
/usr/bin/python3 ansichten_exportieren.py
MPLCONFIGDIR=/tmp/propboard-mpl python ansichten_plotten.py
```

FreeCAD1.0-Pythonmodule, NumPy und Matplotlib erforderlich. Ansichten werden aus den tatsächlich gespeicherten BRep-Körpern erzeugt, nicht generativ erstellt.
