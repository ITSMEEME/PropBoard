# CFK-Flügel – technische Anfragegrundlage

**Anfrage- und Entwicklungsstand, keine Bestellfreigabe.** Die Geometrie dient dem Gespräch mit einem qualifizierten CFK-Dienstleister. Eine Belastungsfreigabe, ein Laminatplan und verbindliche Fertigungstoleranzen liegen nicht vor.

Für die Standardkonfiguration werden 16 gleiche symmetrische Flügel benötigt. [CFK01.step](Ausgabe/STEP_Sonderteile/CFK01.step) ist ein einzelner geschlossener CAD-Körper. Die STL ist eine Darstellungs-/Prototypreferenz und ersetzt die STEP-Geometrie nicht. Oben/unten entstehen durch die Montageindexierung, nicht durch eine unbelegte zweite Materialvariante.

| Merkmal | Standardgeometrie |
|---|---|
| Innenradius / Außenradius | 199.47 / 710 mm |
| Spannweite | 510.53 mm |
| Profiltiefe | 120 mm |
| Pitchachse | 25 % der Profiltiefe |
| Äußeres Profil | symmetrische NACA-00xx-artige Polygonreferenz, außen t/c = 0,12 |
| Wurzelbereich | mindestens t/c = 0,30 bzw. 35,4 mm Bauraum, Übergang zum Außenprofil |
| Nennschale | 1,2 mm vertikale Modellannahme; keine überall konstante Normal-Wanddicke |
| Innenstruktur | geschlossener Kastenspar, 32 mm Nennbreite / 2 mm nominale Wand, geometrisch an Profil angepasst |
| Wurzel | aufgedickter Bereich, mechanisch gefasster Flansch; außenliegender4×M6-Spannkreis aufØ64, AußenplatteØ78 |
| Einsatzraum | nominalØ32,4mm für den70mm langen Integralmandrel; galvanische Trenn-/Fügelage auslegen |
| Massendichte | angenommene 1.600 kg/m³; reale Laminatdichte zu bestimmen |

Das CAD enthält keine einzelnen Gelege, Klebfugen, Trennlagen, Aushärteverzüge oder geprüften Bohrungs-/Insertaufbau. Die Innenkontur ist eine vereinfachte Geometrie. Die geschlossene Außenhaut und der interne Spar sollen einen durchgängigen Lastpfad ermöglichen; daraus folgt noch keine belastbare Laminatfestigkeit.

Vom Dienstleister zu erarbeiten sind: Faserorientierung und Lagenfolge für Biegung/Torsion/Fliehkraft, Wurzel- und Bohrungsverstärkung, Inserts und Klemmdruck, galvanische Trennung zu Aluminium, Klebe-/Fügeprozess, tatsächliche Wanddicken, Formteilung, Auswuchtbarkeit, Prüfbarkeit und reproduzierbare Bauteilmasse. Entlüftung, Formbarkeit und Montage des inneren Einsatzes müssen gemeinsam mit der realen Fertigung bewertet werden.

Der [Lastscreen](Ausgabe/Lastscreen.json) enthält einen 2-g-Massenszenariofall, Querschnittswerte aus 41 CAD-Schnitten, Fliehkraftfälle und Pitch-Trägheitsmomente. Er nutzt ein homogenes Ersatz-E-Modul und keine orthotrope Laminattheorie. Kerben, Flansch-/Bohrungsversagen, Delamination und Lebensdauer sind damit nicht nachgewiesen. Vor einer Bestellung sind die Lastfälle einschließlich Hochlauf, Unwucht, zyklischem Pitch, Böen und Nachbarrotor-Anregung verbindlich festzulegen und zu prüfen.
