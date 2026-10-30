# Kreis R04 – 3D-Sektor-CFD (unvollständig)

> **REKONSTRUKTION vom 30.10.2026 – CFD-STUDIE UNVOLLSTÄNDIG.** Es liegt **kein einziges akzeptiertes CFD-Ergebnis** vor. In dieser Umgebung wurde kein Strömungslöser ausgeführt. Die ursprünglichen Rohfälle, Logs, Strömungsbilder und die SHA1-Kompatibilitätskorrektur aus der verlorenen Cloud-Umgebung sind nicht vorhanden. Berichtete Werte daraus stehen nur in [docs/R03_R04_Rekonstruktion.md](../../docs/R03_R04_Rekonstruktion.md) und sind nicht freigegeben.

## Modell

- 45°-Sektor mit zyklischen Randbedingungen, Gebiet r = 0,03 … 1,5 m, z = ±1,2 m; die innere Begrenzung bei r = 0,03 m ist künstlich (slip).
- Je Ebene ein Flügel: äußere Kontur NACA 0012 + 0,4·q¹⁰ mm je Seite (Hinterkante 0,8 mm), interpolierende Splines, Pitch 12°. Die CAD-Kontur ist polygonal; beide sind angenähert, nicht identische BRep-Flächen.
- Vereinfachte stationäre C-Führungsprofile: innen immer, außen nur in der Variante `ring`.
- Zwei gegenläufige MRF-Zonen (Zellzonen `MRF_lower` +ω, `MRF_upper` −ω um z); ω = U / 0,45 m. Die Führungen sind `nonRotatingPatches`. Drehsinn: Die untere Ebene läuft im CFD-Modell in +θ. Das ist gegenüber der CAD-Konvention gespiegelt und physikalisch gleichwertig.
- Stationäre inkompressible RANS-Rechnung, simpleFoam mit kOmegaSST, ρ = 1,225 kg/m³, ν = 1,5·10⁻⁵ m²/s.
- Nicht enthalten: Schrauben, Wagen, Pilot und vollständiger Rahmen.

**Grenzen:** nur Schwebefall, kein Nachweis bei 80 km/h; keine zeitaufgelöste Flügelpassage, Überdeckung und Versatz sind eingefrorene Stellungen; vollturbulent ohne validiertes Transitionsmodell; keine experimentelle Validierung. Die 2D-LBM-Studien bei Re ≈ 40 sind davon getrennt.

## Bearbeitungsstand

| Schritt | Werkzeug | Stand |
|---|---|---|
| Vernetzung | [gmsh_mesh.py](gmsh_mesh.py), Gmsh 4.15.2 | ausgeführt, 4 Netze, siehe unten |
| OpenFOAM-Fall | [case.py](case.py) für OpenFOAM v1912 | Dictionaries erzeugt; **ungetestet**, OpenFOAM nicht installiert |
| gmshToFoam, createPatch, checkMesh | `Allrun` im Fall | **nicht ausgeführt** |
| Solver | simpleFoam | **nicht ausgeführt** |
| Auswertung | [auswerten.py](auswerten.py) | ausgeführt: 0 akzeptierte Fälle ([Auswertung.json](results/Auswertung.json), [CFD_Ergebnisse.csv](results/CFD_Ergebnisse.csv)) |
| Fortsetzung, Feldmapping | `weiterrechnen.py` | nicht rekonstruiert |
| Strömungsbilder | `flow_export.py` | nicht rekonstruiert, keine Felder vorhanden |
| SHA1-Kompatibilität OpenFOAM | `sha1_compat.*` | nicht rekonstruiert; neu zu implementieren und zu prüfen |
| Installationsskript mit Versions-/Quellmanifest | – | offen |

### Neue Gmsh-Netze

Stufe `c`; Bezeichnung „u40“ für die vorgesehene Rechnung bei 40 m/s:

| Fall | Variante | Versatz | Tetraeder | min. SICN | Gmsh-Prüfung |
|---|---|---:|---:|---:|---|
| free_tet_c_u40 | ohne Außenring | 0° | 693 370 | 0,093 | bestanden |
| ring_tet_c_u40 | mit Außenring | 0° | 971 322 | 0,081 | bestanden |
| free_tet_c_off22_u40 | ohne Außenring | 22,5° | 481 110 | 0,089 | bestanden |
| ring_tet_c_off22_u40 | mit Außenring | 22,5° | 758 618 | 0,092 | bestanden |

Die Gmsh-Prüfung umfasst nur Tetraeder, positive Volumina, min. SICN > 0,05, periodische Knotenzuordnung und vollständige Randgruppen. Sie **ersetzt OpenFOAM `checkMesh` nicht**. Dass das Ringnetz hier gelingt, klärt den im Original berichteten Gmsh-Abbruch von `ring_tet_c_u40` nicht auf: Die rekonstruierte Führungsgeometrie ist ein vereinfachtes, revolviertes C-Profil und nicht die Originalgeometrie. Die Netze (`*.msh`) liegen unter `cases/` und sind per `.gitignore` ausgeschlossen. Sie lassen sich mit dem Skript in etwa 20 s neu erzeugen.

## Akzeptanzprüfung (`auswerten.py`)

Alle Kriterien sind erforderlich: Netzprüfung bestanden (und `checkMesh` „Mesh OK.“, falls ein Log vorliegt), Solver regulär beendet, mindestens 200 Kraftausgabepunkte, Kraftdrift im letzten Fenster < 3 %, relative Kraftstreuung < 5 %, Massenbilanzabweichung < 1 %, Impuls-Anfangsresiduen < 10⁻⁴.

Die vertikale Sektorkraft wird mit 8 auf den Vollkreis hochgerechnet. Horizontale Sektorkomponenten werden wegen der gedrehten Sektoren nicht so behandelt. Die Leistung ergibt sich aus Mz und dem Drehsinn der jeweiligen Zone. Kraftverläufe über SIMPLE-Iterationen zeigen numerische Konvergenz, keine physikalische Zeit. F/g ist ein Brutto-Kraftäquivalent; `allowable_payload_kg` bleibt `null`.

## Ablauf

```sh
python gmsh_mesh.py free_tet_c_u40 --variant free            # --offset 22.5, --level h|c|m|f, --threads 1 --log
python gmsh_mesh.py ring_tet_c_u40 --variant ring
python case.py free_tet_c_u40 --u 40                         # erzeugt cases/<fall>/ (nicht versioniert)
(cd cases/free_tet_c_u40 && ./Allrun)                        # OpenFOAM v1912 erforderlich
python auswerten.py
```

Rohfälle unter `cases/` vor jeder Änderung der Umgebung separat sichern.
