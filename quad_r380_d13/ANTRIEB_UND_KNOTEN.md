# Mensch, Flachrippenknoten und Antriebsanzeige

Die [Projektansicht](Projekt.html) zeigt eine zuschaltbare **1,75 m große Person** mit den Schuhsohlen auf z = 244 mm, entsprechend der Oberseite der beiden Fußplatten. Die Fußmitten stehen bei x = ±200 mm. Die Figur ist eine Größenreferenz; ihre Volumenkörper gehen nicht als Fahrzeugbauteile in die Stückliste ein. Die Figur folgt nicht der Verstellung der Fußschlitten. Die 100-kg-Beladung und die voreingestellten 160 kg Gesamtmasse sind getrennte Auslegungsannahmen; die unvollständige CAD-Teilmasse ist keine automatisch bestimmte Abflugmasse.

## Rahmen- und Motoranschlüsse

Die bisherigen gekreuzten Rundstreben werden an beiden Rohrenden durch **integrierte, flache Alu-Rippen** ersetzt. Rahmenseitig liegt eine offene Brücke vor der senkrechten Rahmenklemme: zwei schmale Stege und Querzüge verbinden die einzelnen Rohrschellen mit dem gemeinsamen Knoten. Diese Anordnung vermeidet die beim ersten Entwurf gefundenen Überschneidungen mit Rahmenklemme, Isolierfolie und senkrechtem CFK-Rohr. Am Motor führen die Rippen unter den Kabelbohrungen entlang und steigen erst außerhalb des benötigten Durchführungsraums zum Motoranschluss an. Es gibt keine zusätzliche externe Montageplatte. Ein gemeinsamer Grundkörper trägt die unteren Schellenhälften; die vorhandenen oberen Kappen bleiben einzeln abnehmbar. Dadurch sind Rohr, Isolierliner, Schellenkappe und Schraube getrennt montierbare Teile.

Der Ansatz nutzt 4 mm Rippenstärke und 18 mm nominelle Tiefe der Rippenzüge, 35 mm Klemmlänge sowie die bestehenden M4-Klemmschrauben. Die offene Rahmenbrücke ist 56 mm breit; ihre senkrechten Stege sind 6 mm breit und 4 mm stark. Am Motor bleiben vier symmetrische M6-Durchgänge auf dem bisherigen 50-mm-Lochkreis und die zentrale Durchführung erhalten. Die tatsächliche MN1330-Gewindetiefe ist weiterhin unbekannt. Material und Dichte entsprechen der bisherigen Annahme EN AW-7075 T6 / 2.810 kg/m³; dies ersetzt kein Werkstoffzeugnis oder Fertigungsverfahren.

Die zehn Durchmesser und V1–V5 mit einem bis vier Rohren bleiben verfügbar. CFK-Arme, Kabelvolumina und Schutzliner werden geometrisch unverändert übernommen. Die neue Datei heißt [Quad_Flachrippen_Mensch.FCStd](Ausgabe/Quad_Flachrippen_Mensch.FCStd); das vorherige [Kabelmodell](Ausgabe/Quad_Standardkabelbaum.FCStd) bleibt als reproduzierbarer Ausgangsstand erhalten.

In V4 mit 42-Zoll-Rotoren sinkt die modellierte Masse der beiden Alu-Grundkörper je Ausleger von rund 673 g auf 491 g. Für vier Ausleger sind das rund **0,73 kg weniger**; Kappen und Schrauben bleiben erhalten. Dies ist ein Volumen-/Dichtevergleich der CAD-Teile, keine gewogene Fahrzeugmasse. [Aufbaudaten](Ausgabe/Flachrippen_Aufbau.json) enthalten den Vergleich für alle Varianten.

Prüfumfang: gültiger zusammenhängender Volumenkörper je Anschluss, Symmetrie des Motorträgers, vollständige benötigte Kabelkorridore, native Expressionszuordnung aller 50 Konfigurationen und Kollisionen der geänderten Knoten mit den Montagepartnern. Geometrie und Einbaupositionen stammen direkt aus den gespeicherten BREP-/Placement-Daten der FCStd-Datei. Ein 45°-Ausleger wird geprüft; die anderen drei sind starre Kopien. Eventuelle unveränderte Kontaktbefunde des Ausgangsmodells werden getrennt ausgewiesen. Die 3D-Ansicht wird zusätzlich tatsächlich in allen 50 Stellungen umgeschaltet. Die [neuen Prüfdaten](Ausgabe/Flachrippen_Pruefung.json) sind maßgeblich, nicht die früheren Anschlussprüfungen.

Das Endprotokoll kennzeichnet die 25 aus einem abgeschlossenen Prüfabschnitt übernommenen Konfigurationen. [Teilprotokoll und damaliger Prüfquellcode](Ausgabe/Flachrippen_Vorlauf.json) dokumentieren deren native SHA-256, Bindungen, Kollisionsresultate und den Code mit den bereits bestandenen Bohrungsassertionen. Die übrigen Konfigurationen wurden auf derselben gespeicherten Geometrie fortgesetzt. Die Fortsetzung speichert wiederverwendete exakte Begrenzungskästen zwischen, damit sie nicht für jeden Montagepartner erneut berechnet werden müssen. [Bindungsprüfung](Ausgabe/Bindungen_Pruefung.json) kontrolliert zusätzlich alle 400 Anschlusspositionen und die 730 gespeicherten CFK-/Kabelgeometrien gegenüber dem Ausgangsmodell; dokumentierte Rundungsgrenzen sind 0,000001 mm für Begrenzungskästen und 0,001 mm³ für die symmetrische Volumendifferenz.

Der vollständige Erstlauf fand bei 42 Zoll drei kleine Überdeckungen mit den 0,3-mm-Rohr-Endauflagen in V2/V5. Die Motor-Endtaschen wurden deshalb durchgehend auf 0,425 mm freigestellt (0,125 mm axialer Freigang für die 0,3-mm-Auflage). Das [Protokoll vor dieser Korrektur](Ausgabe/Flachrippen_Vor_Padfreistellung.json) bleibt erhalten. Die Abschlussprüfung prüft alle 50 korrigierten Motorträger auf gültigen Einzelkörper, Symmetrie und die Teilmengeneigenschaft gegenüber dem zuvor geprüften Körper sowie alle 120 motorseitigen Auflagenpassungen erneut. Reiner Materialabtrag kann weder eine neue Volumenkollision erzeugen noch einen zuvor freien Kabelkanal verschließen; diese bestehenden Ergebnisse werden auf dieser expliziten Grundlage übernommen. Eine Festigkeitsfreigabe folgt daraus nicht.

**Dies ist eine geometrische Überarbeitung.** Die D12-Studie hatte bereits Defizite an Armen, Klemmung und Klebung gezeigt. Für die neuen Knoten sind deren Steifigkeit, Spannungen und Lastübertragung neu nachzuweisen. Freie Kabelkorridore und ein einzelner CAD-Volumenkörper belegen keine ausreichende Tragfähigkeit. Mindestwanddicken unter Toleranzen, Werkzeugzugänge, Verrundungen, Oberflächenschutz und Fertigungszeichnungen sind vor Fertigungsfreigabe zu schließen.

## Was die Antriebsanzeige berechnet

Der Nutzer stellt tatsächliche Rotordrehzahl, Batteriespannung und angenommene Gesamtmasse ein. Der Durchmesser und die geometrische Steigung kommen aus der ausgewählten HEP-S-Größe. Die Anzeige nennt Gesamtschub und Schub je Rotor als **kgf**, Drehzahl in min⁻¹, DC-Batteriestrom in A und elektrische Eingangsleistung in kW. kgf ist ein Gewichtskraftäquivalent; 1 kgf entspricht 9,80665 N. Die Drehzahleinstellung ist kein Gashebelmodell und keine Zusicherung, dass der Motor diese Drehzahl unter Last erreicht.

Ein belastbares HEP-S-Schubkennfeld liegt weiterhin nicht vor. Deshalb wird ein ausdrücklich ungeprüftes statisches Koeffizientenmodell verwendet:

\[
T=C_T\rho n^2D^4,\quad P_\mathrm{Welle}=C_P\rho n^3D^5,\quad
P_\mathrm{DC}=P_\mathrm{Welle}/\eta,\quad I_\mathrm{DC}=P_\mathrm{DC}/U.
\]

D steht in Metern, n in Umdrehungen pro Sekunde; es gelten vier Rotoren und eine Luftdichte von 1,225 kg/m³. Referenzwerte für CT, CP und den Antriebswirkungsgrad werden als Mediane aus den 19 Zeilen der vorhandenen [MN1330-/NS52×20-Nutzertabelle](../quad_r380_d05/Quellen/MN1330/MN1330_NS52x20_Nutzertabelle.csv) gebildet. Wellenleistung wird dort aus Drehmoment und Drehzahl berechnet. Diese Tabelle ist **kein HEP-S-Kennfeld** und kein belegter Dauertest.

Die Übertragung auf die HEP-S-Varianten ist eine zusätzliche Annahme: mit k = (P/D)/(20/52) wird CT = CT_ref × k und CP = CP_ref × k^1,5 angesetzt. Der Referenzwirkungsgrad bleibt konstant. Diese vereinfachte Skalierung beschreibt weder reale Blattgeometrie noch Reynolds-, Mach- oder Belastungseinflüsse. Der Einfluss der unterschiedlichen Steigungen wird damit lediglich angenähert. Die Zahlen dürfen nicht als Herstellerversprechen oder Antriebsnachweis verwendet werden.

Angezeigt werden zudem illustrative Empfindlichkeiten von ±25 % auf CT und ±35 % auf CP. Das sind **keine statistischen Konfidenzintervalle und keine garantierten Fehlergrenzen**. Bordverbraucher, Standby, zusätzliche Leitungsverluste, Spannungseinbruch, Regler-/Motortemperatur, Rotorinteraktion und Bodeneffekt sind nicht separat modelliert.

## Grenzen des Betriebspunkts

Die Anzeige warnt bei Drehzahlen ab KV × U. Diese ideale Leerlaufgrenze ist eine notwendige Obergrenze; das tatsächliche Lastmoment reduziert die erreichbare Drehzahl weiter. Zusätzlich werden das höchste Tabellenmoment von 46,25 Nm und die höchste dort geprüfte Drehzahl von 2.744 min⁻¹ als Grenzen des vorhandenen Datenumfangs markiert. Innerhalb dieser Grenzen ist der Dauerbetrieb ebenfalls nicht bestätigt.

Die vorhandene Leistungsangabe 3,4 kW für 180 s ist ebenfalls hinterlegt; ihre elektrische/mechanische Bezugsseite ist nicht eindeutig bestätigt. Überschreitet bereits die berechnete Wellenleistung diesen Wert, erscheint ein Hinweis, auch für den rechnerischen Schwebezustand. Die erheblich höheren Spitzenleistungen der NS52-Tabelle besitzen keinen bestätigten Dauernachweis und ersetzen diese Klärung nicht.

Für die eingegebene Gesamtmasse wird die rechnerische Schwebedrehzahl aus dem Koeffizientenmodell bestimmt. Dazu werden Schwebestrom und Überschreitungen der genannten Grenzen angezeigt. Ein rechnerisches Schubgewicht oberhalb der Gesamtmasse ist **keine Flugfreigabe**.

DC-Strom ist der rechnerische Eingangsstrom je Regler beziehungsweise die Summe aller vier Regler. Er ist nicht mit dem angegebenen 100-A-Dauer-Ausgang des V200A gleichzusetzen; dessen genaue Phasenstromdefinition fehlt. Motor-, Kabel-, Stecker-, Batterie- und Reglergrenzen müssen am vollständigen Betriebspunkt nachgewiesen werden.

## Reproduktion

Im Repository-Hauptverzeichnis: `python3 quad_r380_d13/ueberarbeitung/antrieb_daten.py`, anschließend `/usr/bin/python3 quad_r380_d13/ueberarbeitung/bauen.py`. Der Builder speichert das neue native Modell einschließlich Bildpropellern und führt Anschlussprüfung, Umlaufprüfung und Viewerexport aus. Danach `/usr/bin/python3 quad_r380_d13/ueberarbeitung/bindungen_pruefen.py`, `node quad_r380_d13/ueberarbeitung/antrieb_pruefen.cjs` und `node quad_r380_d13/viewer_pruefen.cjs`. FreeCAD, Playwright und Chromium sind erforderlich. Der Geometriecache liegt im ignorierten D13-Cacheverzeichnis. `fast_pruefen.py` und `propeller_pruefen.py` lesen die tatsächlichen gespeicherten BREP-/Placement-Daten direkt aus der FCStd-Datei. `viewer_export.py` kann separat auf dem gespeicherten Modell laufen; dann wird die große Baugruppe erneut geöffnet.

Die Datei `ansicht_anpassen.py` dokumentiert die einmalige Migration der HTML-/JS-Oberfläche und soll nicht nochmals auf die bereits migrierten Dateien angewendet werden. Nach einem Export des ursprünglichen D13-Kabelviewers muss der Flachrippenexport erneut ausgeführt werden. [Aufbau](Ausgabe/Flachrippen_Aufbau.json), [Annahmen](Ausgabe/Antrieb_Annahmen.json), [Rechentests](Ausgabe/Antrieb_Pruefung.json) und [Viewerprüfung](Ausgabe/Viewer_Pruefung.json) dokumentieren den jeweiligen Stand.

`node quad_r380_d13/solo_pruefen.cjs` prüft zusätzlich alle zehn Propeller-Einzelansichten, die Rotorstellung und den Rückweg zum Gesamtmodell; [Ergebnis](Ausgabe/Solo_Pruefung.json). Die Skripte `patch_bauen.py` und `pad_freistellen.py` dokumentieren die einmaligen Übergänge während dieser Überarbeitung. Der vollständige Builder enthält die offene Brücke, Bildpropeller und 0,425-mm-Endtaschen bereits unmittelbar.
