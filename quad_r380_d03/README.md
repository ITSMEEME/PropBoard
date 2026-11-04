# Quad R380 D03 – indexierte Fußplatten

Weiterbau des Carbonrahmens: zwei äußere Aluminium-Rasterleisten sichern die Fußposition formschlüssig; die Carbonrohre bleiben ungebohrt. Die Fußplatten besitzen bündig versenkte ISO10642-Schrauben. Dies ist ein überprüfter mechanischer Entwicklungsstand, keine Produktions- oder Flugfreigabe.

- [Interaktive CAD-Ansicht](Mechanik.html) · [Gesamtansicht](Tragwerk_Ansicht.png) · [Fußmechanismus im Detail](Fussschlitten_Detail.png)
- [Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D03_CFK.FCStd) · [STEP-Baugruppe](Ausgabe/QuadR380_D03_CFK.step)
- [Gesamtpaket mit notwendigen Quelldateien](QuadR380_D03_Detailpaket.zip)
- [Stückliste](Ausgabe/Stueckliste.csv) · [Bauzustand](Ausgabe/Status.json)
- [Gewindeprüfung](Ausgabe/Gewindepruefung.json) · [Verstell-/Bauraumprüfung](Ausgabe/Bauraum_Pruefung.json) · [Exportprüfung](Ausgabe/Export_Pruefung.json)
- [Bewertung der vorhandenen Antriebsdaten](../quad_r380_d02/KENNDATEN_BEWERTUNG.md) · [Fehlende Herstellerdaten](../quad_r380_d02/HERSTELLERDATEN.md)

## Gebaute Änderungen

CBU20171005TG Ø20/17 mm und die originalen P12-Aluminiumklemmen samt Isolierlagen bleiben erhalten. Die Endplatten der beiden oberen Rohrschienen sind für die Rasterleisten verbreitert. Die neuen Leisten sind 770 x 24 x 10 mm groß und an den metallischen Endplatten verschraubt. Je Leiste gibt es 26 Ø6,4-mm-Rasterbohrungen und vier native M4-Anschlussgewinde. Beide Fußplatten greifen mit je zwei M6-Indexierschrauben ein. Die unteren Klemmbacken tragen gefräste Bügel, die unter der Rasterleiste hindurchführen; 2 mm Abstand unter der Leiste sowie nominal 1 mm seitlich an der Außenwange sind geometrisch vorgesehen. Die Rasterleisten berühren die Carbonrohre nicht.

Die Fußplatten bleiben 300 x 140 mm groß. Ihre Dicke steigt von5 auf6 mm. Acht Senkungen je Platte, Ø11,6/90°, nehmen ISO10642 M5x50 auf; die oben liegenden Scheiben entfallen. Die tatsächliche Normteilgeometrie wurde aus derselben gepinnten Fasteners-Bibliothek erzeugt. Alle16 Köpfe liegen nominal0,2 mm unter der Standfläche. Unter der Senkung bis zum Ø5,5-mm-Durchgang verbleiben rechnerisch2,95 mm. Lasten, Vorspannung, Reibwerte und lokaler Kontakt sind noch zu qualifizieren.

Das Raster ist10 mm. Beide Fußmittelpunkte sind separat zwischen130 und250 mm Abstand zur Mitte einstellbar: Mittenabstand260–500 mm. In FreeCAD steuern `Fussverstellung.Links`, `.Rechts` und `.Entriegelung` die Lage. Die Entriegelungsdarstellung zeigt nur die geprüften Endstellungen0/10 mm. M6-Regelgewinde hat1 mm Steigung: real sind für10 mm Rückzug10 Umdrehungen nötig. Eine nur geradlinige reale Verschiebung durch das Gewinde ist nicht vorgesehen. Nur Rasterpositionen in10-mm-Schritten sind verriegelbar.

## Bedienfolge des Entwurfs

1. Fußplatten vollständig entlasten.
2. Alle vier Indexierschrauben10 mm zurückschrauben und die Rohrklemmungen lösen.
3. Jede Fußplatte auf eine Rasterposition verschieben.
4. Beide Indexierschrauben je Fußplatte vollständig einrasten/einschrauben; erst anschließend die Rohrklemmung mit einem noch zu qualifizierenden Verfahren anziehen.

Die Indexierschrauben besitzen beim vollständigen Rückzug nominal0,6 mm Abstand zur äußeren Leistenfläche und verbleiben im Gewindebügel. Diese Konstruktion ist keine automatisch verriegelnde Schnellverstellung. Es gibt noch keine freigegebenen Anzugsmomente oder zulässigen Personenlasten. Rutschhemmung der Standflächen, Verschleiß-/Vibrationssicherung und Fehlbedienungsnachweise sind offen.

## Was geprüft wurde

- 28 Gewindepaarungen an Rasterleisten, Indexierbügeln und Schienenflanschen sowie16 Senkschrauben-/Mutterpaarungen der Fußklemmungen: **44 nominale Paarungen bestanden**. Die Geometriephasen sind eingestellt; gleiche lokale Gewindegeometrien verwenden nachgewiesene Phasenreferenzen. Das ist kein Vorspannungs- oder Toleranznachweis.
- Statisch: Strukturkörper plus vollständige Fußbefestigungen und die28 neuen bzw. nachbearbeiteten Gewindeschrauben. Übrige alte ISO-Verbindungen sind ausdrücklich nicht Teil dieser globalen Prüfung.
- Dynamische Stichproben: jede der13 Rasterpositionen je Fuß, jeweils mit0/10 mm Rückzug, insgesamt52 Zustände. Das gesamte bewegte Fußsystem wurde gegen **alle festen Nachbarkörper**, einschließlich alter Normschrauben, geprüft. Keine Überschneidung über0,1 mm³ gefunden.
- Zusätzlich liegen sämtliche bewegten Bauteile innerhalb der jeweiligen140-mm-Plattenbreite in Schienenrichtung. Damit bleiben auch alle169 Kombinationen der verriegelten Fußpositionen zueinander frei; kleinster Abstand120 mm. Das ist ein geometrischer Trennnachweis, kein Last- oder Ermüdungsnachweis.
- Alle verwendeten nativen Prototypen sind gültige Einzelkörper. STEP wieder eingelesen:640 Körper vorhanden. Die Gültigkeitsprüfung jedes einzelnen STEP-Rückimportkörpers wurde hier nicht erneut durchgeführt; sie wird nicht behauptet.

Die Masse des modellierten Umfangs beträgt **22,554 kg**. CFK-Dichte bleibt eine Annahme. Mit100 kg Person und vier EMRAX188-AC-Motoren à7,1 kg aus dem unbestätigten Extrakt ergäben sich schon150,95 kg, ohne Akku, Rotoren, Regler, Kühlung, Schutz und Fahrwerk. Ein vollständiger150-kg-Fahrzeugfall ist damit nicht geschlossen.

## Was weiterhin fehlt

Originale OEM-Kennfelder, Motor-/Rotor-/Regler-Anschlusszeichnungen und STEP fehlen weiterhin. EMRAX188 LV ist lediglich Beschaffungspriorität. Batteriepack, BMS, Verkabelung, Kühlung, Schutz und Landegestell sind noch nicht physisch integriert. Die Kennwertdatei ist ein ausdrücklich unbestätigter Extrakt, keine Grundlage für erfundene OEM-Geometrien.

Weitere offene Nachweise: zulässige CFK-Klemmpressung/PU-Oberfläche/Isolierlagen, globale Tragfähigkeit, Rohr-/Knotensteifigkeit, Indexierschrauben und deren Gewindebereiche unter Querlast, Leistenknicken, Schraubensicherung, Toleranzen und Ermüdung. Die übrigen P12-Gewindekernkonturen sind noch nicht vollständig in fertige Gewinde überführt. Eine bestandene D01-Prüfung gilt nicht pauschal für diesen Aufbau.

## Reproduktion und Quellen

System-Python mit FreeCAD/PartDesign/MeshPart, Node/Playwright und Chromium. Reihenfolge: `weiterbauen.py`, `fussplatten_buendig.py`, `gewinde_pruefen.py`, danach `bauraum_pruefen.py` und `ableiten.py`, abschließend `viewer_pruefen.cjs`. Die Prüfungen beziehen sich auf den gespeicherten Standardzustand. Änderungen an Geometrie oder Lage machen betroffene Prüfergebnisse ungültig.

Eingang ist die erhaltene D02-Baugruppe mit `Bauteile.json` und `Instanzen.json`. Normteil-BReps liegen teils unter D01/D02, der neue ISO10642-Datensatz unter `Quellen/Normteile`. Das Paket enthält diese relativen Abhängigkeiten sowie die drei ursprünglichen P12-STEP-Quellen. `normteile_erstellen.py` benötigt nur zur Neugenerierung den gepinnten Fasteners-Quellstand `fddd07af422b7d3a69098b32333711c5eeae184c`; Maßtabelle und Lizenz werden mitgeliefert. Gewindeklassen und Festigkeitsklassen sind Beschaffungsanforderungen, keine Lieferzertifikate.
