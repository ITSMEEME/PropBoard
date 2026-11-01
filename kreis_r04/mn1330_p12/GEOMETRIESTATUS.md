# P12 – Ergänzungen und verbleibende Geometrielücken

Stand: 01.11.2026. Bezug ist die aktive Großausführung aus der Projekt-README.
Historische Revisionen bleiben Archivstände. Das kleine P11-Modell wurde nicht geändert.

## Ergänzt

`befestigungen.py` ergänzt aus den bestehenden Anschlussmaßen:

- vier versenkte M4-Flanschschrauben pro geteilter CFK-Rohrklemme;
- zwei querliegende M4-Klemmschrauben pro CFK-Rohrklemme;
- zwei M5-Klemmschrauben pro Guide-Rohrklemme;
- vier M3-Schrauben pro Rollenlagerdeckel, einschließlich spiegelbildlicher Einbaulagen;
- eine Mutter pro Rollenachse.

Die Körper werden mit den Anschlussbauteilen platziert und bei Parameteränderungen
neu aufgebaut. Das Anschlussregister liegt in `Ausgabe/Befestigungen.json`.
Native Gesamtbaugruppe, Gesamt-STEP, Stückliste und Einzel-STL enthalten die Ergänzungen.
Einzel-STEP der neuen Referenzteile liegen ausdrücklich unter `Ausgabe/Referenz_STEP/`.

Es handelt sich um eigene geometrische Entwürfe. Schraubenköpfe besitzen eine
Sechskantvertiefung; Gewinde sind als glatte Kernkontur mit Spiel dargestellt.
Diese Darstellung unterschätzt den realen Gewindeaußendurchmesser und die Masse.
Sie dient der Montageanordnung und verhindert Scheinkollisionen in Kernbohrungen.
Ein kollisionsfreies Ergebnis dieser Konturen ersetzt keine Gewindepaarungsprüfung.
Normzuordnung, verfügbare Längen, Festigkeitsklasse, Gewindesteigung, Sicherung,
Unterlegscheiben und Vorspannung sind nicht freigegeben. Die Achsmutter ist eine
Sechskant-Referenz mit freigestellter Bohrung; Gewindeeingriff und Sicherung fehlen.

Verifiziert: 1.725 gültige Einzelkörper, 160 Geometrietypen, keine BRep-
Volumenüberschneidungen über 0,01 mm³ im Grundstand. Außenmaße unverändert
1.790 × 1.784,1 × 776 mm. Die vorhandenen 19 Parametrikprüfungen mit 153
Eingaben wurden bestanden, einschließlich Parameteränderung, ungültiger Eingaben
und Speichern/Wiederöffnen. Das ist keine vollständige Bewegungsprüfung.

## Noch fehlend – keine vollständige Geometrie behaupten

| Baugruppe | Fehlende Geometrie / benötigte Grundlage |
| --- | --- |
| MN1330 | Originalkontur, eindeutig zugeordnete Montageseiten, Zentrierungen und Gewindetiefen; bisher nur Ø150×66-Nennhülle. Benötigt Herstellerzeichnung bzw. Original-CAD. |
| Motorbefestigung / Motornabe | Schraubenlängen und Eingriff müssen zu den bestätigten Motor-Gewindetiefen passen. Keine frei erfundenen Blindlochverschraubungen. |
| Membran / Distanzsäulen / Innenring | Vollständige Schrauben-, Scheiben- und Sicherungsketten sowie Montagezugang. Lastverteilung und Klemmung müssen konstruktiv festgelegt werden. |
| Pitchwellen | Wellen, Flügelaufnahme, Hebelanschluss, axiale Sicherung und vollständige Lagersitze. Es gibt noch keinen festgelegten Wellen-/Lagerentwurf für P12. |
| Pitchlagergehäuse | Anschluss an Innenring und Außenlaufbahn, Lagerabstände, Passungen, Deckel und Befestigungen; müssen mit der Pitchwelle gemeinsam ausgelegt werden. |
| Außenlaufbahn | Tragende Verbindung zu Rotor/Pitchlagerträgern; bisher geometrisch separater Laufbahnring. |
| Taumelscheibe | Stationärer und rotierender Ring, Lagerung, Führung, Mitnehmer, Anschläge und vollständige Befestigungen. P11-Abmessungen sind nicht automatisch auf P12 übertragbar. |
| Pitchanlenkung | Ausgewählte Aktuatoren einschließlich Halter, Arme, Gelenke und Gestänge; Hub, Kräfte, Übersetzung und Kollisionsfreiheit im Stellbereich sind festzulegen. |
| Guide-Anschluss | Schrauben zwischen Gabelplatten/-steg und Rohrklemmsattel einschließlich korrekter Gewindezuordnung und Sicherung. |
| Mittelstütze / Mittelbrücke | Durchgehende Schrauben-, Muttern-, Scheiben- und Endplattenverbindungen; Anschlussdetail und Montagefolge fehlen. |
| Lager / Rollen | Reale Hersteller-Schultern und Fasen, Passungen, Freistiche, Vorspann- und Sicherungsdetails. Nennhüllen sind vorhanden. |
| Flügel | Fertigbare CFK-Schalen, Holm, Wellenaufnahme, Fügestellen und Laminat; aktuell massive Profilreferenzen. |
| Elektrik / Deck / Fahrwerk / Schutz | Für P12 noch nicht als vollständiges Fahrzeug konstruiert. Akku ist laut Parameterdatei ausdrücklich außerhalb des aktuellen Umfangs. |

Diese Lücken sind teils fehlende Produktdaten, teils offene Konstruktionsentscheidungen.
Ein Herstellerdownload allein schließt die eigene Pitch- und Taumelscheibenkonstruktion nicht.

## Quellenzugriff

Der Abruf von `https://store.tmotor.com/` wurde am 01.11.2026 durch den
Umgebungsproxy mit `CONNECT tunnel failed, response 403` abgewiesen.
Die aktive Netzrichtlinie erlaubt keine zusätzlichen Hersteller-Domains.
Für weitere Herstellerabrufe sind die konkret benötigten Hosts in den
Umgebungseinstellungen freizuschalten; Original-CAD/Zeichnungen können alternativ
direkt in das Projekt übernommen werden. Es wurden keine Herstellerdateien abgerufen
und keine unbekannten Herstellermaße ergänzt.
