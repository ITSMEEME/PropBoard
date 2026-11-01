# P12 variieren

Die aktuelle symmetrische Architektur besteht aus zwei gegenläufigen Rotorebenen und drei festen Rollen je Ring. Innerhalb dieser Architektur steuern153 numerische Eingaben die vorhandenen Bauteile und deren Anschlüsse. Noch nicht konstruierte Pitchlager-/Taumelscheibenteile können dadurch nicht automatisch entstehen.

## In FreeCAD

1. Den gesamten Ordner `mn1330_p12` behalten und `P12_oeffnen.FCMacro` in FreeCAD ausführen. Dadurch ist der mitgelieferte Python-Proxy vor dem Öffnen der nativen Datei verfügbar.
2. Tabelle **Parameter — hier ändern** öffnen. Gelbe Werte in SpalteB bearbeiten; Namen, Einheiten und Einzelgrenzen stehen daneben. Für mehrere voneinander abhängige Änderungen erst alle Werte setzen, dann F5 drücken.
3. **P12_Modell → Modellstatus** prüfen. `Error` muss leer sein. Die Tabelle **Abgeleitet** enthält daraus berechnete Anschlusspositionen, Längen und Außenmaße.
4. Speichern. Für aktualisierte STEP/STL, Stückliste und Kollisionsbericht `P12_Exportieren.FCMacro` ausführen. Ein reines Speichern der FCStd-Datei aktualisiert externe Exporte nicht.

Beim direkten Öffnen der FCStd ohne aktivierten Proxy bleibt die gespeicherte Geometrie sichtbar; für zuverlässige Bearbeitung den Öffnen-Makro verwenden. Die Pythondateien müssen neben den Makros erhalten bleiben. FreeCAD kann beim Wiederherstellen die Freigabe eines Python-Proxys verlangen; das ist eine lokale Einstellung der Installation.

Ungültige Kombinationen werden vor der Übernahme neuer Körper verworfen. **Die letzte gültige Geometrie bleibt dann sichtbar**; der Modellstatus lautet ausdrücklich `UNGUELTIG_LETZTE_GUELTIGE_GEOMETRIE_ANGEZEIGT` und `Error` nennt die Gründe. Diese sichtbare Geometrie gehört dann nicht zu den ungültigen Tabellenwerten. Erst nach Korrektur und erfolgreicher Neuberechnung exportieren.

## Wichtigste Parameter

| Zweck | Eingaben | Abhängigkeiten |
|---|---|---|
| Rotorgröße | `rotor_radius`, `blade_root`, `blade_chord` | Flügel, Laufbahndurchmesser, Rollenposition, Außenrahmen, Querträger |
| Flügelform | `blade_thickness`, `blade_taper`, `blade_twist`, `blade_te`, `pitch_axis` | Neuer gelofter Profilkörper; Referenz, noch kein CFK-Fertigungsteil |
| Blattzahl | `blade_count` | Flügelzahl, Membranarme, Distanzsäulen und Innenringbohrungen |
| Pitch | `pitch_neutral`, `pitch_min`, `pitch_max` | Neutralgeometrie und konservative Hüllraumprüfung; keine vollständige Pitchbewegungsprüfung |
| Ebenenabstand | `level_spacing` | Rotorhöhen, Motoren, Pfostenlänge, Mittelstütze, Rollenhalter, Bauhöhe |
| Motor | `motor_diameter`, `motor_length`, `motor_face_offset` | Kaufteilhülle, Tragplattenhöhe, Mitnehmer- und Rahmenposition |
| Motoranschlüsse | `motor_rotor_pcd`, `motor_rotor_holes`, `motor_stator_pcd`, `motor_stator_holes`, Phasen | Naben-/Statorbohrungen; Gewindetiefen weiterhin unbekannt |
| Rahmen | `frame_post_margin`, `frame_beam_y`, `post_*`, `beam_*`, `flange_*`, `middle_*` | Rohre, Flansche, Klemmsättel, Druckhülsen, End- und Mittelanschlüsse |
| Mitnehmer | `hub_*`, `membrane_*`, `drive_*`, `carrier_*` | Nabe, Membran, Distanzsäulen, Innenring und zugehörige Lochbilder |
| Laufbahn und Rollen | `track_tip_margin`, `track_half_height`, `groove_angle`, `roller_*`, `guide_gap` | Passende V-Profile, radiale Rollenlage und äußere Abstützung |
| Feste Rollenwinkel | `guide_angle_1`, `guide_angle_2`, `guide_angle_3` | Jeweilige Gabeln, Außenpfosten und Radialstege folgen mit |
| Lager und Klemmkette | `bearing_*`, `cap_*`, `axle_*`, `inner_spacer_d` | Lagersitze, Deckel, Distanzen, Achse und Gabelhöhen |
| Lastszenario | `total_mass_kg`, `rpm`, `load_factor` | Dokumentierter Schub-/Spitzengeschwindigkeits-Rechenwert, keine automatische Festigkeitsfreigabe |

Alle Eingaben und Bereiche stehen in `parameter_schema.py`; die JSON-Vorgaben in `parameter.json`. Die Tabelle enthält dieselben Namen. Maße sindmm, WinkelGrad, Dicke/Zuspitzung dimensionslos. Abgeleitete Maße sind **keine zusätzlichen unabhängigen Eingaben**.

Bei `frame_mode=0` bleibt die Aluminiumvariante wählbar: `rotor_radius=650` ergibt1300mm nominalen Rotor und1720mm äußeren Rahmen;300mm Ebenenabstand ergeben872mm Bauhöhe. Standard ist jetzt `frame_mode=1` für den CFK-Speichenrahmen. Dessen Außenmaße stammen aus dem tatsächlich aufgebauten Polygonrahmen und stehen in `Pruefung.json` bzw. `Abgeleitet`. Solche Änderungen dürfen später erforderliche Steifigkeits-, Lager-, Drehzahl- und Belastungsnachweise nicht ersetzen.

## Per Kommandozeile

```bash
./p12.sh
./p12.sh --set rotor_radius=650 --set level_spacing=300 --output /tmp/P12_Kompakt
./p12.sh --set blade_count=6 --set blade_taper=0.8 --set blade_twist=-4 --output /tmp/P12_Sechsblatt
/usr/bin/python3 ansichten_exportieren.py --output /tmp/P12_Kompakt
python ansichten_plotten.py --output /tmp/P12_Kompakt
```

Die Pythonumgebung für den CAD-Aufbau muss die FreeCAD-Module besitzen; unter dieser Umgebung ist dies `/usr/bin/python3`. Das Ansichtsprogramm benötigtNumPy/Matplotlib. Verschiedene Varianten in getrennte Ausgabeordner schreiben.

`Parameter_Eingefroren.json` enthält den tatsächlich exportierten Parameterstand, abgeleitete Werte, Werkstoffe und Parameterhash. Er kann mit `--config /pfad/Parameter_Eingefroren.json` erneut aufgebaut werden. Änderungen in der nativen Tabelle überschreiben `parameter.json` nicht automatisch: Die JSON definiert den Startstand; jede gespeicherte FCStd enthält ihren eigenen aktuellen Tabellenstand.

## Prüfgrenzen

Geprüft werden Eingabebereiche, ganze Anzahlen, Rohrwände, Lochbild-/Senkungsabstände, Membrananschlüsse, Säulenlänge, Lager-/Nutwand, Deckel-/Gabelabstände, eine konservative Flügelhülle und die Verteilung der drei Rollen. Beim Export folgt zusätzlich eine exakte BRep-Volumenprüfung im Neutralzustand. Geometrisch unzulässige Fälle können trotz gültiger Einzelbereiche entstehen und werden dann im Prüfbericht gemeldet.

153 freie Zahlen bedeuten keine153 freigegebenen Auslegungsparameter. Insbesondere Lagerabmessungen wählen noch kein verfügbares Kaufteil aus. Geänderte Motorabmessungen skalieren den realen MN1330 nicht. Toleranzen, Wärmeeinfluss, Vorspannung, Ermüdung, Strukturverformung und vollständige Bewegungsfreiheit bleiben gesonderte Nachweise. Akku bleibt außerhalb dieser mechanischen Auslegung.

## Fertigungsvarianten

Die Stückliste benennt pro Instanz eine `manufacturing_variant` und die dazugehörige `manufacturing_step`. Gespiegelte Unterseiten werden zusätzlich als `_MZ.step` exportiert; die Anschlusslaschen erhalten explizite X/Y-Varianten. So werden bei geänderten, unsymmetrischen Lochbildphasen nicht versehentlich gleiche CNC-Dateien für unterschiedliche Gegenstücke verwendet. Die Datei ohne Suffix ist der nominale Grundtyp; für die konkrete Instanz gilt der STEP-Verweis der Stückliste.

## Gewähltes CFK-Rohr

`frame_mode=1` verwendet CBU20171005TG, nominal20×17×1000mm. Diese drei Bestellmaße sind für dieses Kaufprodukt bewusst gebunden. `cfk_actual_od` erlaubt19.8..20.2mm zur Berücksichtigung des gemessenen Außendurchmessers; Isolierlagen passen sich an. Klemmlänge, Knotenabstand, Sägefuge, Endbeschnitt und Preis sind ebenfalls zentral erfasst. Alte Vierkantrohrparameter steuern nur `frame_mode=0`; sie skalieren das gewählte CFK-Kaufteil nicht. Einzelheiten in [CFK_RAHMEN.md](CFK_RAHMEN.md).
