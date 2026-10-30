# Kreis R03/R04 – Übernahme- und Rekonstruktionsprotokoll

Stand: 30.10.2026. Ausgangscommit auf GitHub: `bba1004788c9c9a435b395b44e7c1b3e9df62db0` („Detail Horizontal Z R02 assembly and document feasibility limits“).

## 1. Ausgangslage und Prüfung

Übernommen werden sollte ein ungesicherter Arbeitsstand aus der Cloud-Umgebung `/workspace/PropBoard` auf Branch `work`: geändertes `README.md`, `kreis_r03/`, `kreis_r04/`, lokale Werkzeuge unter `.cfd-tools/` und CFD-Rohfälle unter `kreis_r04/cfd/cases/`.

Ergebnis der Prüfung am 30.10.2026:

- `/workspace/PropBoard` existiert auf dem verfügbaren Rechner nicht. Eine Dateisuche nach `kreis_r03`, `kreis_r04`, `Kreis_R0*` und `.cfd-tools` blieb ohne Treffer.
- Der lokale Klon war sauber auf `bba1004`, ohne Stash.
- GitHub (`git ls-remote`) enthält nur `main` auf `bba1004`, keinen Branch `work`.
- Damit war **keine Sicherung des Originalstands möglich**. Die originalen FCStd/STEP-Dateien, Prüfberichte, Solver-Logs, CFD-Rohfälle, Strömungsbilder und die lokale OpenFOAM-/SHA1-Infrastruktur sind hier nicht vorhanden. Wiederherstellen lassen sie sich nur, falls die Cloud-Umgebung oder eine Kopie davon wieder auftaucht.

Auf Wunsch wurde danach eine **Rekonstruktion** aus der Übergabebeschreibung erstellt. Sie ist in jeder Datei als solche gekennzeichnet.

## 2. Was rekonstruiert wurde und in welchem Zustand

| Bereich | Dateien | Zustand |
|---|---|---|
| R03 Geometrievergleich | `kreis_r03/grundriss.py`, `Vergleich.*`, `Grundriss_Vergleich.*` | neu berechnet; Werte identisch mit der Beschreibung |
| R03 Layoutmodell | `kreis_r03/erstellen.py`, `Kreis_R03_Layout.FCStd/.step`, `Pruefbericht.json` | mit FreeCAD 1.0.2 erzeugt, gespeichert und wieder geöffnet |
| Profil mit 0,8-mm-Hinterkante | `kreis_r04/profil.py` | ausgeführt; Hinterkante 0,800 mm geprüft |
| R04 CAD-Varianten | `kreis_r04/cad_erstellen.py`, `Kreis_R04_Aussenring.*`, `Kreis_R04_ohne_Aussenring.*`, `CAD_Pruefung.json`, `CAD_Volumen.csv` | erzeugt, alle Formen gültig, wieder geöffnet |
| Massen/Auftrieb | `kreis_r04/massen_und_anforderungen.py`, `Massen_Szenarien.*`, `Auftriebsanforderungen.csv` | erzeugt (312 Fälle) |
| Balkenmodell | `kreis_r04/balken.py`, `Struktur_Referenz.json`, `Struktur_Sweep.csv` | neu berechnet (208 + 8 + 6 Fälle) |
| CFD-Vernetzung | `kreis_r04/cfd/gmsh_mesh.py`, `results/Netzpruefung_*.json` | neu ausgeführt mit Gmsh 4.15.2, Ergebnisse siehe 3 |
| CFD-Falldefinition | `kreis_r04/cfd/case.py` | geschrieben; **OpenFOAM nicht verfügbar, ungetestet** |
| CFD-Auswertung | `kreis_r04/cfd/auswerten.py`, `results/Auswertung.json`, `results/CFD_Ergebnisse.csv` | ausgeführt; **keine Solverdaten, kein akzeptierter Fall** |

**Nicht rekonstruiert**, weil sie sich ohne die Originale oder ohne OpenFOAM nicht prüfen ließen und sonst erfunden wären: `weiterrechnen.py`, `flow_export.py`, `sha1_compat.cpp`, `sha1_compat_bauen.py`, `SHA1_Kompatibilitaetspruefung.json`, `results/flow/ring_feature_u40.png/.npz` sowie sämtliche Solver-Ergebnisse.

## 3. Neu berechnete Ergebnisse

**Geometrie R03:** Bahnlänge 2,8274 m (R02: 3,8274 m); idealisierte überstrichene Ringfläche je Ebene 1,69646 m² (R02: 2,29646 m²), also −26,1 %; Flügelfläche gesamt 1,152 m². Die Werte stimmen exakt mit der Übergabe überein und gelten nur geometrisch.

**Profil:** Hinterkantendicke 0,800 mm. Schalenquerschnitt mit unveränderter R02-Innenkontur 427,3 mm², also 0,410 kg CFK je Flügel.

**Balken** (`balken.py`), Referenzfall 50 m/s mit Gesamtauftrieb entsprechend 200 kg und Zugversteifung: mit Außenring 3,54 mm / 123 MPa, ohne Außenring 19,6 mm / 323 MPa. Sechs Euler-Bernoulli-Prüfungen bestanden (max. rel. Abweichung 1,6·10⁻⁴). Diskretisierung 16…128 Elemente: Spannungsänderung < 1 %. Kein Festigkeitsnachweis.

**CFD-Netze** (Gmsh 4.15.2, Stufe `c`): `free_tet_c_u40` 693 370 Tetraeder, `ring_tet_c_u40` 971 322, dazu je ein Fall mit 22,5° Versatz. Alle bestehen die Gmsh-Qualitätsprüfung; `checkMesh` wurde nicht ausgeführt. Die Netze sind nicht mit den Originalnetzen vergleichbar.

**CAD R03/R04** (FreeCAD 1.0.2): R03 und R04 mit Außenring haben je 1 744 Ergebniskörper (16 × 102 mobil, 24 Ringkörper, 79 zentrale R02-Referenzen, 9 Pilotreferenzen). R04 ohne Außenring hat 948 Körper: 796 entfernt, 8 Motor- und 8 Encoderhüllen der unteren Ebene auf die Innenseite gespiegelt. Fahrzeughülle ohne Pilot 1580 × 1693 × 523 mm bzw. 1540 × 1693 × 523 mm. Rahmen und Ringhalter fehlen, die Hülle ist daher unvollständig.

**Flügelprüfung** (`CAD_Pruefung.json`): alle 16 Flügel mit Pitch 12,0°, Spannweite radial und Sehne tangential (Richtungskosinus ≥ 0,9997); Radialbereich 150,0 … 752,3 mm; untere Ebene im, obere gegen den Uhrzeigersinn. Der Schwerpunkt liegt 9,8 mm vor der Pitchachse (Profilschwerpunkt ≈ 42 % Sehne). Exakte Mindestabstände: Nachbarflügel 22,1 mm, übereinanderliegende Flügel 211,8 mm, Flügel zu Führungsring 9,1 mm (mit) bzw. 13,7 mm (ohne Außenring). Keine Kollision.

**Erfasste Modellmasse** (nur Körper mit Werkstoffklasse CFK/Aluminium/Stahl; Elektroblech als Stahl gezählt): 63,23 kg mit, 26,67 kg ohne Außenring, Differenz 36,56 kg. Das ist **keine Fahrzeugmasse**. Referenzbauräume (≈ 4,2 bzw. 2,4 dm³), Batteriezellen, Magnet-/Spulensysteme, Elektronik und Tragstruktur fehlen. Die analytischen Mindestgeschwindigkeiten bei frei angenommenem CL liegen zum Beispiel für S1 mit Außenring zwischen 40,6 m/s (CL 1,2) und 62,9 m/s (CL 0,5). Sie berücksichtigen weder induzierte Strömung noch Interferenz und sind kein Nachweis.

**CFD-Ergebnisse:** keine. `auswerten.py` meldet 0 akzeptierte Fälle.

**Bei der Rekonstruktion gefundene und behobene eigene Fehler:** Im ersten Entwurf von `gmsh_mesh.py` war die Punktfolge der Profilunterseite umgekehrt. Dadurch entstand eine fehlerhafte Flügelgeometrie, an der die Flächenvernetzung hing. Ein daraus vorschnell abgeleiteter „Überlappungsbefund“ an der Flügelwurzel wurde zurückgenommen. Tatsächlich bleiben an der Wurzel im Grundriss nur etwa 2,3° (rund 6 mm) zwischen Nachbarflügeln, ohne Überlappung.

## 4. Werkzeuge der Rekonstruktion

FreeCAD 1.0.2 (offizielles AppImage `FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage`, SHA256 `e00be00a…904f61`, gegen die veröffentlichte Prüfsumme geprüft), Gmsh 4.15.2 (PyPI), numpy und matplotlib, lokal unter `.cfd-tools/` (nicht versioniert). Aufruf zum Beispiel: `FREECAD_LIB=.cfd-tools/freecad/usr/lib .cfd-tools/freecad/usr/bin/python kreis_r03/erstellen.py`. OpenFOAM war nicht verfügbar.

## 5. Berichtete, nicht verifizierbare Werte des verlorenen Stands

Die folgenden Angaben stammen ausschließlich aus der Übergabebeschreibung. Sie konnten nicht geprüft werden und sind **nicht** in Ergebnisdateien übernommen worden.

| Angabe | berichteter Wert | Status |
|---|---|---|
| R03 / R04 mit Außenring, Ergebniskörper | 1 733 | Rekonstruktion: 1 744 |
| R04 ohne Außenring | 945 Körper, 788 entfernt, 8 Motor- + 8 Encoderhüllen umgesetzt | Rekonstruktion: 948 / 796 / 8 + 8 |
| Erfasste Modellmasse (vor Hinterkantenänderung) | 55,75 kg mit / 23,87 kg ohne Außenring, Differenz ≈ 31,88 kg | Rekonstruktion (nach Hinterkantenänderung, eigene Werkstoffzuordnung): 63,23 / 26,67 kg; Abweichung ungeklärt, keine Fahrzeugmasse |
| Balken-Referenzfall 50 m/s, 200 kg | 3,75 mm / 127 MPa mit, 20,53 mm / 336 MPa ohne Außenring | Rekonstruktion ergibt 3,54 mm / 123 MPa bzw. 19,6 mm / 323 MPa; Abweichung durch abweichende Modelldetails |
| `ring_feature_u40` | ≈ 149,6 N vertikal (≈ 15,26 kg Kraftäquivalent), ≈ 4,76 kW | **diagnostisch, nicht freigegeben**: Netz nicht akzeptiert, Konvergenz unzureichend |
| `free_tet_c_u40` (Original) | Netzprüfung bestanden, 177 855 Tetraeder; Solverlauf nicht bestätigt | nicht verifiziert |
| `ring_tet_c_u40` (Original) | Vernetzung an einer Gmsh-1D-Kurve gescheitert, Ursache offen | nicht verifiziert |
| Couette-Kontrollfall | Wandkräfte analytisch übereinstimmend; prüft nur Erhaltung der initialisierten Lösung und die Wandkraftauswertung | nicht verifiziert |
| Ruhe-Kontrollfall | Kräfte und Flüsse null, auf älterem Netz | nicht verifiziert |
| SHA1-LD_PRELOAD-Korrektur | Referenzprüfung bestanden; ändert keine Strömungsgleichungen | nicht verifiziert, Quelle fehlt |
| Weitere Rohfälle | `ring_coarse_u40`, `ring_plain_u40`, `free_medium_u40`, `ring_medium_u40`, `free_feature_u40`, `ring_b08_c2_u40`, `free_b08_c2_u40`, `rest_control`, `validation_couette` | Rohdaten fehlen; mehrere snappyHexMesh-Netze waren laut Bericht unzulässig |

## 6. Offene Aufgaben

1. Originale Cloud-Umgebung suchen und sichern. Falls sie auftaucht: Originaldateien gegen diese Rekonstruktion abgleichen und Rohfälle getrennt von Git archivieren. Ein Git-Ignore ist keine Datensicherung.
2. Die Werkstoffzuordnung der Massenrechnung fachlich prüfen (Abweichung gegenüber den berichteten Werten) und ein geschlossenes Massenbudget aufstellen.
3. Ohne Außenring: Flügelwurzel, Lagerung und Drehmomentübertragung neu auslegen; die Welle ist nur eine vereinfachte Referenz. Die Innenkontur der hohlen Flügelschale an die neue Außenkontur anpassen.
4. R03/R04: Rahmenanbindung, Ringhalter, Schutz und Kabelwege konstruieren.
5. Portables Installationsskript mit Versions- und Quellmanifest für OpenFOAM v1912, Gmsh 4.15.2 und gegebenenfalls die SHA1-Kompatibilitätskorrektur erstellen. Die SHA1-Korrektur ist neu zu implementieren und zu prüfen.
6. Akzeptiertes Netz mit Außenring herstellen. Für Fehlersuche: reproduzierbarer Ein-Thread-Lauf mit vollständigem Gmsh-Log (`gmsh_mesh.py … --threads 1 --log`); das ist ein Diagnoseschritt, keine bekannte Ursache.
7. OpenFOAM-Fälle mit `case.py` erzeugen, `checkMesh` ausführen, beide Varianten bei 40 m/s lösen und mit `auswerten.py` die Konvergenz prüfen.
8. Geschwindigkeitsreihe 20/30/40/50/60 m/s, Netzverfeinerung, direkte Überdeckung gegenüber 22,5° Versatz (`--offset 22.5`), Kontroll- und Randgebietssensitivitätsfälle; Ruhe- und Couette-Kontrollfall auf dem akzeptierten Netz wiederholen.
9. Werkzeuge für Fortsetzungsrechnungen (Weitergabe der Gmsh-Netzmetadaten, Feldmapping bei unterschiedlicher Patchanzahl) und für Strömungsvisualisierung neu schreiben. Beide Varianten mit gleichen Farbskalen darstellen und die Strömung zwischen übereinanderliegenden Flügeln ausdrücklich auswerten. Pfeile sind dabei projizierte Vektoren, keine 3D-Stromlinien.
10. CFD-Kräfte, Antriebsleistung, Strukturannahmen und Massenszenarien zusammenführen; ausführlichen deutschen R04-Vergleichsbericht erstellen.

## 7. Physikalische Grenzen (unverändert gültig)

Schwebefall ohne Vorwärtsflug, also kein Nachweis bei 80 km/h. Stationäre MRF-RANS-Rechnung mit eingefrorenen relativen Flügelstellungen, vollturbulent mit kOmegaSST, ohne Transitionsmodell und ohne experimentelle Validierung. Schrauben, Wagen, Pilot und vollständiger Rahmen sind nicht im Strömungsmodell enthalten. Vertikale Kraft durch g ist ein Brutto-Kraftäquivalent und keine zulässige Personenzuladung; `allowable_payload_kg` bleibt `null`. Die früheren 2D-LBM-Studien bei Re ≈ 40 sind davon getrennt und liefern keinen realmaßstäblichen Nachweis.

Die Projektziele (100 kg Person zuzüglich Ausrüstung, maximal 2100 × 1700 × 600 mm, mindestens 15 min Flugzeit, ungefähr 80 km/h) sind **nicht nachgewiesen**. Es fehlen ein geschlossenes Massenbudget, ausgewählte Batterien und ein belastbarer Antriebsnachweis.
