# P02 – komplette Kaufteile und tatsächlicher Fertigungsstand

**Deine Entscheidung ist übernommen: Lager, EMAX-Motoren und Savöx-Servos werden komplett gekauft.** Für deren Innenteile brauchen wir keine Eigenfertigungszeichnungen. Die Artikel und Anschlüsse müssen zur Baugruppe passen. Dazu gehören auch reale Servohörner, Gelenke, Befestigungen, Sitze und Sicherungen.

Die Baugruppe ist **noch nicht produktionsfertig**. Der P02-Stand macht den Fortschritt und die noch blockierten Teile im nativen Dokument prüfbar, statt unbelegte Innengeometrie als Fertigungszeichnung auszugeben.

## Konkret umgesetzt

- Vier tatsächliche STEP-Normteilmodelle aus der FreeCAD Parts Library importiert: ISO4762 M3×10, M3×12, M3×40 und ISO4032 M3-Mutter. Quelle, feste Git-Revision, Originaldateien, SHA256 und Lizenz sind enthalten.
- Gültige Einzelvolumen, Schraubenlänge unter Kopf, Kopfdurchmesser/-höhe und Mutternhöhe/Schlüsselweite geprüft. Konservative OCC-Boundingboxen wurden nicht blind als Kopfdurchmesser übernommen; Zylinderflächen und feines Mesh wurden geprüft. Gewinde sind nominale Kaufteilschnittstellen, keine bestätigten detaillierten Flankengeometrien.
- Acht vorhandene Schraubenschaft-Referenzen durch vollständige Kopf-/Schaftmodelle ersetzt und vier echte Muttern an der unteren Anschlussplatte ergänzt. M3×12: Kopfauflage z=−104, 8 mm Platten-/Kappendurchgang, Mutter z=−96…−93,6, Schraubenende z=−92; damit 1,6 mm Überstand im Nennmodell. Kopffreiheit und Kontaktvolumina geprüft.
- Bei M3×40 liegt der Kopf unter der oberen Endkappe bei z=96; die obere FC-Klemmung bleibt bis zu echten Dämpfermaßen offen. Keine beliebigen Mutternlagen oder fremden Schraubenlängen als fertige Montage eingetragen. M3×80/M2×35 bleiben offen, soweit passende Daten fehlen.
- Die willkürlichen Lagerkugeln/Käfige und Motor-Innenteile wurden aus der P02-Fertigungsansicht entfernt. Komplette Kaufteile sind dort Anschlussreferenzen mit sichtbarem Sperrstatus. Die eigenständige M01-Kinematikdemo bleibt erhalten.
- Native Baugruppe und STEP mit eindeutigem Namen `GESPERRT` exportiert; der Gesamtstatus ist im Dokument `False`. Es wurde keine allgemeine Fertigungsfreigabe behauptet.

[Native Baugruppe](Ausgabe/P02_Kaufteile_Integration_GESPERRT.FCStd) · [Normteilkatalog](Ausgabe/P02_Normteilkatalog.FCStd) · [Status-CSV](Ausgabe/Fertigungsstatus_P02.csv). `P02_oeffnen.FCMacro` öffnet die Ansicht und färbt: grün = Normteilmaße geprüft, orange = Kaufteil-Anschlussdaten offen, gelb = Eigenfertigungsentwurf. Grün bedeutet keine Gesamtfreigabe.

## Wichtiger Motorplattenbefund

Der aktuelle Entwurf verwendet einen **Lochkreis Ø16 mm**. Vier Löcher bei 45°/135°/225°/315° ergeben Achsabstände von **11,3137 × 11,3137 mm**. Das ist **nicht** ein 16×16-mm-Motorbefestigungsraster. Die tatsächliche EMAX-Version muss anhand der Herstellerzeichnung geprüft werden. Hier wird nicht behauptet, dass der reale Motor zwingend das eine oder andere Raster hat.

Außerdem muss die echte Abtriebswelle geklärt werden: Ø5, ein M5-Gewinde, Flachstelle, Schulter und Nutzlänge sind unterschiedliche Schnittstellen. Der bisherige nominale Ritzelbohrungs-/Wellenkörper enthält noch keine belastbar definierte Drehmomentübertragung oder axiale Sicherung.

## Benötigte Kaufteildaten für die nächste Konstruktion

STEP-Dateien oder vollständig bemaßte Hersteller-Anschlusszeichnungen genügen; bei kompletten Kaufteilen sind keine Fertigungszeichnungen ihrer Innenteile erforderlich:

1. **4× 6806-2RS, 30×42×7 mm und 2× 6809-2RS, 45×58×7 mm:** konkreter Hersteller/Artikel, Dichtungs-/Luftvariante, Fasen/Radien/Schultergrenzen und Passungsdaten. Nicht jede Community-Lagerdarstellung besitzt reale Hersteller-Laufbahnen. Kein passendes Lager wurde durch Skalieren eines 6803 oder 608 ersetzt.
2. **EMAX ECO II 2306 KV1900:** exakte Version, Montage-Lochbild/Gewinde/Einschraubtiefe und vollständige Wellen-/Schulterzeichnung.
3. **Savöx SB-2271SG(+):** genaue Variante, Laschendicke, Bohrungen/Schlitze und Abtriebs-/Halteschraube. Deine Gehäusemaße und 69-g-/6,0–7,4-V-Spezifikation sind bereits übernommen.
4. **Passendes gekauftes 25T-Horn mit 8-mm-Anlenkradius sowie konkrete Kugelbolzen/Stangenköpfe:** Zeichnung oder Artikel mit Schnittstellenmaßen. Aus „25T“ allein lässt sich weder ein fertigungsreifes Spline-Profil noch eine kompatible Verbindung ableiten.

`anforderungen.json` enthält diese Anforderungen und die offenen Eigenfertigungsschnittstellen einzeln. Dazu zählen Servohalter, montierbare Kugel-/Innenringpaarung, reale Kugelaufnahmen, Lager-/Hebel-/Mitnehmersicherungen, Passungen und Material-/Prozessangaben. Die bloße Einfügung vollständiger Kaufteile erledigt diese Konstruktionen nicht automatisch.

## Quellenlage und Grenzen

Die öffentliche FreeCAD Parts Library wurde unter Revision `f5ca01cdcaa2f69b9295a6382719c2d90628780c` geprüft. Sie liefert die importierten Normschrauben/-muttern, aber keine passenden 6806/6809-Modelle. Auch die geprüften Lagerdatentabellen von cq_warehouse (`a57bb7a24762d367d66369f280a24c38a64e73dd`) enthalten die benötigten Baugrößen nicht; außerdem berechnet diese Bibliothek Kugelanzahlen/-geometrie, statt Hersteller-Innenteile zu belegen. Vier öffentliche GitHub-Repositoriesuchen zu den exakten Kaufteilen lieferten keine Treffer. Das ist keine Behauptung, dass solche Daten nirgendwo existieren.

Hersteller-CAD-Portale sind durch die aktuelle Cloud-HTTP-Freigabe nicht zugänglich. Daher wurde bislang kein Original-CAD von SKF/NSK, EMAX oder Savöx abgerufen. Vom Nutzer bereitgestellte Originaldaten können als Nächstes integriert und geprüft werden.

Die Normteilreferenzen sind Community-CAD, kein Material-/Lieferantenzertifikat. Die Repository-Lizenz `LICENSE-Assets` erklärt CAD-Dateien als CC-BY-3.0; die alten FCStd-Standardmetadaten enthalten teilweise leere Autoren und den Default „All rights reserved“. Beide Tatsachen sind im Quellenmanifest dokumentiert. Original-STEPs, feste Quelllinks, Upstream-Lizenz und Attribution bleiben erhalten; es werden keine Herstellerfreigaben daraus abgeleitet.

## Reproduktion

```sh
export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p02/pruefen_normteile.py
.cfd-tools/freecad/usr/bin/python modell_r04_taumel/fertigung_p02/integrieren.py
python modell_r04_taumel/fertigung_p02/status_erstellen.py
```

Normteilquellen sind enthalten. Integration neu erzeugen erfordert zusätzlich den unveränderten H01-/M01-Stand im vollständigen Checkout. Zum Öffnen der gespeicherten P02-Ansicht sind keine Community-Python-Erzeuger nötig.
