# Lokale CFD unter Linux mit Docker

Dieses Paket erstellt echte OpenFOAM-Fälle für zehn Geometrien, verfeinert gültige Kandidaten und vergleicht Feinmesh und größere Rechendomäne. Die Cloud-Rechenkampagne bleibt pausiert. Es werden keine Modellkräfte auf die Großausführung hochgerechnet.

Voraussetzungen: Linux x86-64, Docker Engine mit Compose v2, ausreichend freier Plattenplatz (mindestens 30 GB empfohlen). Standard: vier CPU-Kerne, zwei MPI-Prozesse, ein Fall gleichzeitig, 12 GB Container-RAM. Das ist keine garantierte Speicherobergrenze des benötigten Netzes: bei Speichermangel bricht der Fall ab. Für große Feinmesh-Fälle mehr RAM bereitstellen. Internet wird zum Herunterladen/Bauen der Images benötigt; Rechencontainer laufen danach ohne Netzwerk und ohne Docker-Socket.

```bash
chmod +x start-cfd.sh
cp local.env.example local.env
./start-cfd.sh build
./start-cfd.sh preflight
./start-cfd.sh prepare
./start-cfd.sh serve
./start-cfd.sh pilot
./start-cfd.sh run
```

Dashboard: http://127.0.0.1:8766/fullscale/Ausgabe/CFD_Vergleich.html

Der Pilot ist ein 50-Iterationen-Funktionstest mit einer bekannten kleinen Modellgeometrie, kein gültiger Großmaßstab-Kandidat. `run` berechnet die zehn vorbereiteten Großmaßstab-Fälle im Vordergrund. Ein zweites Terminal kann `status`, `serve` oder `stop` ausführen. `stop` fordert einen geschriebenen Checkpoint an; den Solver danach auslaufen lassen. `down` ist kein Ersatz für diesen geordneten Stopp. `run` setzt unvollständige Fälle am letzten rekonstruierten vollständigen Feld fort. Ergebnisse liegen dauerhaft unter `work/fullscale/`.

Nach der ersten Serie:

```bash
./start-cfd.sh resume       # nur numerische Fortsetzungen geeigneter Fälle vormerken
./start-cfd.sh run
./start-cfd.sh refine --count 6
./start-cfd.sh run
./start-cfd.sh verify
./start-cfd.sh report
```

`optimize --count 6` führt eine begrenzte Runde aus: zehn Saaten, numerische Fortsetzung, sechs neue Formen, deren Fortsetzung und eine Fein-/Domänenprüfung. Ohne numerisch gültige Eltern wird abgebrochen. Weitere Verfeinerungen sind ausdrücklich separat startbar, maximal 40 Kandidaten. `--profile model` verwendet stattdessen den kleinen Originalmaßstab in einem eigenen Arbeitsordner. Profile vor `prepare` konfigurieren; ein bereits eingefrorenes Profil wird nicht still überschrieben.

## Was verglichen wird

Die Großausführung hat Ø1500 mm, Wurzelradius150 mm, Ebenenabstand240 mm und zunächst848,826 min⁻¹. Saaten übernehmen nur Formen der Modell-Top10; ihre unterschiedlichen Blattzahlen bleiben erhalten. Referenzkonstruktion: acht Blätter je Ebene. CFD variiert Sehne, relative Dicke, Zuspitzung, Verwindung und den Pitch beider Ebenen. Drehzahl, Durchmesser und Abstand sind in diesem Profil bewusst konstant, damit die Formwirkung vergleichbar bleibt. Für andere Betriebspunkte sind getrennte Studien nötig.

Schubäquivalent in kg ist Kraft/9,81, keine Nutzlast. Mechanische Leistung stammt aus CFD-Drehmoment × Winkelgeschwindigkeit. P/V ist lediglich die ideale Untergrenze des gesamten DC-Stroms; reale Motor-/ESC-Verluste und tatsächlicher Strom sind ohne Kennfelder unbekannt. Die Rangfolge nach P/T^(3/2) bewertet aerodynamische Effizienz; gleicher Zielschub wird damit nicht direkt nachgewiesen. Dafür müssen Finalisten zusätzlich bei angepasster Drehzahl gerechnet werden.

Numerische Zulässigkeit verlangt Netz-/Schichtprüfungen, stationäre Kräfte, Residuen, Massenbilanz und plausible Leistung. SST-RANS mit Wandfunktionen ist eine Näherung, keine voll wandaufgelöste Rechnung. Feinmesh-Score muss sich um weniger als5%, die größere Domäne um weniger als3% ändern. Eine ausgewählte feinere Stufe allein belegt keine vollständige Netzunabhängigkeit. Es wird kein global perfektes Profil behauptet. Stall, Transienten, Taumelscheibenausschläge und Strukturfestigkeit sind damit nicht validiert.

Das Dashboard zeigt vorhandene echte Ergebnisse, STL-Geometrien und nach Abschluss Kraftverläufe/Strömungsschnitte. Es erfindet keine Ergebnisse vor dem Rechnen. Geometrien umfassen zunächst die Flügel; Motoren, Rahmen, Mitnehmer und Ringschatten fehlen aerodynamisch.

## Hardwaregrenzen

84 V Ladeschluss entsprechen beim angegebenen NMC-Pack 20S, widersprechen der Angabe24S. 72V ×50A erlauben nominal3600W Dauerleistung für das ganze System. Bei Ø1,5m ergibt das selbst ideal nur ungefähr39kg Gesamtschub vor Verlusten. Das 150kg-Rechenszenario ist mit diesem Akku bereits energetisch ausgeschlossen. 150A für1–3s sind keine Dauerleistung. Die widersprüchlichen Motorangaben75kg/3400W werden im Preflight sichtbar gehalten.

MN1330 hat laut Nutzer keinen durchgehenden axialen Durchgang. Externe Taumelscheibenabstützung siehe `Direktantrieb_MN1330.md`. Die CFD-Dateien sind keine Fertigungsfreigabe für diese Mechanik.

Technische Prüfung: [Validierung](Validierung.md). Die schematische [Motoranordnung](Anordnung_MN1330.svg) zeigt die äußeren Motorpositionen.
