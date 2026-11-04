# Bewertung der bereitgestellten Kenndaten

**Status: unbestätigter Text-Extrakt. Keine OEM-Freigabe und keine Änderung der physischen CAD-Kaufteile.**

Die empfangene Datei ist unverändert unter `Quellen/Beschaffungsagent/kenndaten.md` archiviert. Ihr SHA256 belegt nur die empfangene Textdatei. Original-PDFs, Original-STEPs und vollständige Quellenbelege sind weiterhin nicht vorhanden.

## Priorität für die nächste Beschaffung

EMRAX188 LV wird als vorrangiger Kandidat für die weitere Datenprüfung geführt. Die angegebenen AC-/LC-Leistungs- und Drehmomentwerte sind ein Anlass zur Prüfung, aber kein belegter R380-Betriebspunkt. AC benötigt laut Extrakt 20 m/s Kühlluft; Rotorabstrom darf nicht ohne lokalen Nachweis gleichgesetzt werden. LC benötigt Pumpe, Kühler, Leitungen und nachgewiesene Wärmeabfuhr. CC kombiniert beide Anforderungen. Kühlbedarf und zusätzliche Masse können die Rangfolge verändern.

## Spannung und Drehzahl

| Kandidat | idealer Leerlauf bei 24S/86,4 V | bei 24S/100,8 V | theoretische Mindestspannung für 5621 U/min |
|---|---:|---:|---:|
| EMRAX188_LV | 6292 U/min | 7340 U/min | 77.2 V |
| EMRAX188_LV28 | 4915 U/min | 5735 U/min | 98.8 V |
| EMRAX208_LV | 5530 U/min | 6452 U/min | 87.8 V |
| TMotor_U15XXL_KV29 | 2506 U/min | 2923 U/min | 193.8 V |

Das ist eine bedingte KV-Rechnung anhand unbestätigter Extraktwerte. Unter Last sinkt die Drehzahl; Feldschwächung ist nicht vorausgesetzt. Für EMRAX188 LV ergibt sich bei angenommenen 3,0 V/Zelle nur 5243 U/min im Leerlauf. Die nutzbare Entladetiefe eines 24S-Packs ist deshalb für den höchsten bisherigen Lastfall nicht nachgewiesen. 24S ist weiterhin nicht festgelegt.

NOVA30-WK: Die genannte Grenze von 5000 U/min wird in den alten 175-/200-kg-Fällen überschritten. Dauerwerte fehlen. Der Prüfbericht zur HV-Ausführung von 2021 ist nicht ohne Variantenabgleich auf die WK-Ausführung von 2026 übertragbar.

## Masse neu schließen

| Motorvariante | Struktur + 100 kg Person + vier Motoren | Rest bis 150 kg für alle anderen Teile |
|---|---:|---:|
| EMRAX188_AC | 149.44 kg | 0.56 kg |
| EMRAX188_LC | 152.64 kg | -2.64 kg |
| EMRAX188_CC | 151.44 kg | -1.44 kg |
| EMRAX208_AC | 158.64 kg | -8.64 kg |
| EMRAX208_LC | 162.24 kg | -12.24 kg |
| EMRAX208_CC | 161.04 kg | -11.04 kg |
| NOVA30_WK | 146.04 kg | 3.96 kg |
| U15XXL | 141.56 kg | 8.44 kg |

Die 150-kg-Rechenfälle sind damit keine geschlossenen D02-Konfigurationen. Beim EMRAX188 AC bleiben nur rund 0,56 kg für Akku, Rotoren, Regler, Kühlung, Kabel, Schutz und Fahrwerk. Beim LC-Motor wird 150 kg bereits ohne diese Teile überschritten.

## Rotor- und Tabellendaten

- Mejzlik30x10_maxon: U×I = 932.40 W, angegeben sind 1314 W (40.9 % mehr). Falls U/I den gleichen DC-Eingangspunkt beschreiben, sind die Angaben unvereinbar. Stromart, tatsächliche Spannung, Leistungsdefinition und Spaltenzuordnung am Original prüfen.
- Mejzlik28x9_4_maxon: U×I = 1762.68 W, angegeben sind 2075 W (17.7 % mehr). Falls U/I den gleichen DC-Eingangspunkt beschreiben, sind die Angaben unvereinbar. Stromart, tatsächliche Spannung, Leistungsdefinition und Spaltenzuordnung am Original prüfen.
- Die T-Motor-NS57-/NS62-Prüfpunkte gelten für 1447,8 bzw. 1574,8 mm große Propeller. Bei 850 mm benachbartem Achsabstand überlappen ihre koplanaren Kreise um 597,8 bzw. 724,8 mm. Diese Rotoren passen nicht in die klassische R380-Anordnung. Gemessene Schübe dürfen nicht auf einen 760-mm-Rotor übertragen werden.
- Der U15XXL KV29 erreicht unter der angenommenen 24S-Grenze idealisiert nur 2923 U/min im Leerlauf. Er ist kein belegter Direktantrieb für den alten R380-Drehzahlbereich.
- Für einen 30-Zoll-Rotor bleiben geometrisch 88 mm zwischen benachbarten nominalen Kreisen. Verformung, Naben-/Blattgeometrie, Schutz und Betriebsspiel sind damit nicht geprüft.

## Akku und Hochstromversorgung

P45B/P50B bleiben Kandidaten mit Spiegelquellen; P60C ist ausdrücklich vorläufig. Keine der genannten Maximalstromangaben wird als thermisch nachgewiesener Pack-Dauerstrom übernommen. Zellkurven, Kontaktierung, Kühlung und Alterung sind erforderlich. Wh/kg mit typischer Energiemenge und maximaler Masse darf nicht ohne Bezugsprüfung direkt verglichen werden.

Der bisherige R380-Rechenbereich beträgt bei 92 V und pauschal 82 % Wirkungsgrad etwa 504–773 A im Hauptzweig. Das überschreitet bereits den im Extrakt genannten 500-A-Kontaktstrom des EV200. Damit ist dieser Typ keine bestätigte Hauptschütz-Auswahl für diese angenommene Versorgung. Eine andere Spannung, Last oder Aufteilung muss vollständig neu geprüft werden. Abschaltvermögen bleibt unabhängig davon offen.

Die Littelfuse-Unterlage enthält laut Extrakt vorläufige Typen und einen Revisionskonflikt. Aus Nennstrom und I²t allein folgt weder ein geeigneter Haupt-/Abzweigschutz noch Selektivität. Entsprechende Typen werden nicht bestellt oder in die finale Stückliste übernommen.

## Gezielter Nachauftrag

1. Original-PDFs EMRAX188 V1.7 und Users Manual V1.7 plus vollständige Wicklungs-/Reglerliste und AC-/LC-Kennfelder beschaffen. Kühlbedingungen, RMS-/Spitzen-/Phasen-/DC-Stromdefinitionen, Temperaturwiderspruch, Lagerlasten und Motorvariante klären. Verbindliche Montage-/Wellen-/Flanschzeichnung und passendes STEP liefern. Ø188×79 allein reicht nicht.
2. Für einen tatsächlich geeigneten Rotor nahe Ø760 mm: Herstellerkennfelder, maximal zulässige Drehzahl, CW/CCW, Nabe, Befestigung und Zeichnung/STEP beschaffen. Die beiden maxon-Tabellen im Original prüfen und korrigiert mit Seiten-/Spaltenbezug abgeben.
3. Konkreten LV-/MV-Regler passend zur bestätigten Wicklung mit elektrischen/thermischen Dauergrenzen, Motorgeber-Kompatibilität, STEP und Pinout belegen. Die vorliegende HV-Reglerauswahl schließt diesen Punkt nicht.
4. Originaldatenblätter P45B/P50B, Entladekurven und verlässliche Maße liefern. BMS, DC/DC, Flugsteuerung, Stromsensor, Kontakte/Stecker, Kabel und Kühlkomponenten als konkrete Lieferteile beschaffen. Packkonfiguration und Spannung erst danach festlegen.
5. TE-Originaldatenblatt 5-1773450-5_sec7_EV200A und Varianten-CAD beschaffen; DC-Abschaltvermögen, Derating und Economizerdaten prüfen. Geeignete Sicherungstypen samt aktuellem Originaldatenblatt, Halterzeichnung und Zeit-Strom-Kurven liefern.
6. CBU20171005TG beim Lieferanten eindeutig bestätigen; Warenkorb-ID und plausible Artikelnummer sind kein Identitätsnachweis. ID-Toleranz, Laminatkennwerte und zulässige Klemmpressung nachfordern.

Netzwerkhinweis für den Beschaffungsagenten: Der Extrakt nennt zusätzlich `plettenbergmotors.com`, `mgm-compro.cz` und `cn.tmotor.com`. Diese Hosts unterscheiden sich teilweise von der bisherigen Domainliste. Konkrete Download-Hosts anhand der Original-URLs freigeben lassen; das Datenportal nicht umgehen.

Je Original: Hersteller, exakte Variante, Revision, Original-URL, Abrufdatum, Seite/Tabelle und Dateihash. Einen fehlenden Originalhash nicht durch den Hash dieses Extrakts ersetzen.

Reproduktion: `python3 kenndaten_pruefen.py`. Ergebnisse sind bedingte Plausibilitätsrechnungen mit den bisherigen unbestätigten Aerodaten, keine neue gemessene Simulation.
