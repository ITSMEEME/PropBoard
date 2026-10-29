---
title: "PropBoard – Technisches Datenblatt"
subtitle: "PB-HZ-STEH-DS-001 · Revision 0.1 · Entwicklungsstand"
lang: de-DE
---

**Entwurfsvariante:** zwei horizontale, gegenläufige Flügelumläufe, übereinander entlang z. Hauptvariante: **Stehen**. Datenbasis: CAD-/Dokumentationsstand `dcb1602` im Repository ITSMEEME/PropBoard.

**Status:** Konstruktionsvorentwurf. Keine freigegebene Produktspezifikation, keine Fertigungs- oder Personenflugfreigabe. Angaben zur Tragfähigkeit und Leistung sind bisher nicht durch einen realen Antrieb, Prüfstand oder Flugversuch bestätigt.

## 1. Hauptkennwerte

| Kennwert | Aktueller Wert | Einordnung |
| --- | --- | --- |
| Nachgewiesene zulässige Tragfähigkeit | **Noch nicht bestimmt** | Weder strukturell noch im Flug nachgewiesen |
| Personengewicht | **Bis 100 kg als Zielanforderung** | Ausrüstung zusätzlich; keine bestätigte Nutzlast |
| Fahrzeug-Leermasse | Noch nicht bestimmt | Kein geschlossenes Massenbudget |
| Gesamt-/Startmasse | Noch nicht bestimmt | Fahrzeug, Akku, Person und Ausrüstung müssen zusammen bewertet werden |
| Fahrzeughülle, modellierte Stellung | **2080 × 1698 × 558 mm** | CAD-Wert ohne Personenreferenz; Schutz und Toleranzen nicht vollständig integriert |
| Maximale Fahrzeugabmessungen | 2100 × 1700 × 600 mm | Zielvorgabe einschließlich Schutz, ohne Person |
| Flugzeit | Mindestens 15 min angestrebt | Nicht nachgewiesen |
| Zielgeschwindigkeit | Ungefähr 80 km/h | Nicht nachgewiesen |
| Reichweite | Noch nicht bestimmt | Keine Ableitung aus Zielgeschwindigkeit × Zielflugzeit |
| Batterie-Nennkapazität | **Noch nicht ausgewählt: Ah und kWh offen** | Zwei CAD-Einbauräume sind kein ausgewähltes Akkusystem |
| Elektrische Leistungsaufnahme | **Noch nicht bestimmt, kW offen** | Schwebe-, Missions- und Spitzenleistung fehlen |
| Batteriestrom | **Noch nicht bestimmt, A offen** | Spannung und elektrische Last fehlen |

**Leseregel:** „Zielanforderung“ ist kein nachgewiesener Leistungswert. „CAD-Wert“ beschreibt nur die idealisierte Geometrie. „Noch nicht bestimmt“ bedeutet weder 0 kg Tragfähigkeit noch 0 A Stromaufnahme.

\newpage

## 2. Mechanischer und geometrischer Aufbau

| Merkmal | Modelldaten / Konzept |
| --- | --- |
| Anordnung | Zwei horizontale Bahnen in x-y, entgegengesetzte Umlaufrichtungen |
| Ebenen | z = −120 / +120 mm; Abstand 240 mm |
| Flügel | 16 insgesamt, acht je Ebene |
| Profil | NACA-0012-Geometrie; kein validierter realer Profil-/Flügelaufbau |
| Sehne / Spannweite | 120 / 600 mm je Flügel |
| Summe geometrischer Flügelflächen | 1,152 m²; keine unabhängig durchströmte Rotorscheibenfläche |
| Pitch in der gespeicherten Stellung | 12° Referenzanstellung; kein freigegebener Stellbereich |
| Endschlitten | 32, zwei je Flügel |
| Pitchantrieb | 16 koaxiale Motor-Bauraumreferenzen; Produktauswahl und Leistungsnachweis fehlen |
| Umlenkgeometrie | Mittlerer Radius 450 mm, gerade Abschnitte je 500 mm |
| Führungsradien im Bogen | Innen 130 mm, außen 770 mm |
| Führung / Vorschub | Magnetführungs- und segmentiertes Linearantriebskonzept; noch nicht funktionsvalidiert |
| Rahmen | CFK-Rohrkonzept mit isolierten Metall-Klemmknoten; Laminat und Festigkeit offen |
| Deck / Fußauflagen | Deckoberseite z = 346 mm; Auflageoberseite z = 358 mm |
| Alternative Pilotenlayouts | Niedriger Langsitz und Bauchlage als separate Konzepte |
| Regelungsziel | Selbststabilisierende Winkelregelung entsprechend ANGLE MODE; System-/Reglernachweis fehlt |

Die modellierte Steh-Hülle lässt nominell 20 mm Gesamtlängen-, **2 mm Gesamtbreiten-** und 42 mm Gesamthöhenreserve zur Zielhülle. Diese Differenzen sind keine zulässigen Fertigungs-, Bewegungs- oder Sicherheitsabstände. Insbesondere ist die Breitenreserve für ein vollständig ausgestattetes Fahrzeug nicht geschlossen.

Die Bauteile besitzen noch keine nachgewiesene Zulässigkeit für die dynamischen Umlenkkräfte. Eine vollständige kontinuierliche Kollisions- und Luftspaltprüfung fehlt. Die beiden Gegenläufe ersetzen weder einen Struktur- noch einen Ausfallnachweis.

## 3. Batterie und elektrische Daten

| Kennwert | Aktueller Stand |
| --- | --- |
| Geometrische Modulräume | **2 × 400 × 140 × 60 mm** |
| Bauraumvolumen je Modul / gesamt | 3,36 / 6,72 Liter; reine Hüllvolumina |
| Modul-Lage | x = ±240 mm, y = 0; Unterseite z = 165 mm |
| Zellchemie, Zellen und Packaufbau | Nicht festgelegt |
| Serien-/Parallelschaltung | Nicht festgelegt |
| Nenn-/Betriebsspannung, V | Nicht festgelegt |
| Nennkapazität, Ah | Nicht festgelegt |
| Nennenergie / nutzbare Energie, kWh | Nicht festgelegt |
| Batteriegewicht, kg | Nicht festgelegt |
| Dauer-/Spitzenstrom, A | Nicht festgelegt |
| Dauer-/Spitzenleistung, kW | Nicht festgelegt |
| BMS, Sicherungen, Vorladung und Schütze | Funktionaler Bedarf beschrieben, konkrete Auslegung offen |
| Ladeleistung und Ladezeit | Nicht festgelegt |
| Thermischer Betrieb / Brand- und Gasführung | Nicht nachgewiesen |
| HV-/LV-Trassen | CAD-Räume Ø12 / Ø6 mm; keine Aderquerschnitts- oder Strombelastbarkeitsangabe |
| Versorgung bewegter Stellglieder | Induktives Übertragungskonzept als Bauraum; Leistungsübertragung nicht nachgewiesen |

**Aus 6,72 Litern Bauraum lässt sich keine seriöse Batteriekapazität ableiten.** Zellen, Gehäuse, Schutz, thermische Auslegung und die gleichzeitig erforderliche Dauerleistung sind noch offen. Die früher untersuchten Tattu-Packs sind nicht als geeigneter Akku dieses Entwurfs übernommen worden.

## 4. Stromverbrauch und Energiebilanz

Die elektrische Gesamtaufnahme muss Linearantriebe, Führung, Pitchantriebe, Regler, Hilfsversorgung und die jeweils noch nicht erfassten Verluste einschließen. Bislang liegen dafür keine geschlossenen Mess- oder Rechenwerte vor. Deshalb sind weder ein „Schwebestrom“ noch ein Verbrauch in kWh je Flug freigegeben.

Für die spätere Auslegung gelten folgende Beziehungen. Sie sind Rechenregeln, keine Leistungsdaten dieses Entwurfs:

| Größe | Beziehung / Bedingung |
| --- | --- |
| Mittlerer Batteriestrom | Näherungsweise `I [A] = 1000 × P_Batterie [kW] / U_Batterie [V]`; reale zeitabhängige Spannung berücksichtigen |
| Energie für 15 Minuten | `E_nutz [kWh] = 0,25 × P_Batterie,mittel [kW]` bei entsprechender mittlerer Gesamtaufnahme |
| Erforderliche Nennenergie | `E_nenn >= E_nutz / f_nutzbar`; nutzbarer Anteil einschließlich nicht verplanter Energie ist erst festzulegen |
| Nennkapazität | `Q_nenn [Ah] = 1000 × E_nenn [kWh] / U_nenn [V]` für die gewählte Pack-Nennspannung |
| Energiebasierte Dauer | `t [min] = 60 × E_nutz [kWh] / P_Batterie,mittel [kW]`; nur relevant, wenn Dauerleistung und Thermik ebenfalls erfüllt sind |

Die früheren Rotor-Schwebeleistungsrechnungen sind **keine Leistungswerte dieses Flügelumlaufantriebs** und werden nicht zur Angabe eines Stromverbrauchs verwendet. Auch der vorhandene numerische Leistungsproxy aus der 2D-CFD ist kein zulässiger elektrischer Leistungswert.

## 5. Tragfähigkeit und Betriebsgrenzen

Für eine zulässige Personenmasse müssen Strukturtragfähigkeit und ausreichend regelbarer aerodynamischer Schub gleichzeitig nachgewiesen werden. Eine Zielmasse von 100 kg entspricht allein ungefähr 981 N Gewichtskraft der Person. Fahrzeug, Akku und Ausrüstung kommen hinzu. Diese Rechnung ist kein Schubnachweis.

Nicht bestimmt sind zulässige Gesamtmasse, Dauerschub, Maximalschub mit Zeitgrenze, Stellreserven, maximaler Schwerpunktbereich und zulässige dynamische Lasten. Die frühere illustrative Gesamtmasse 185,32 kg wird nicht als Gewicht des aktuellen Detailentwurfs ausgewiesen.

| Betriebs-/Nachweisgröße | Status |
| --- | --- |
| Zulässige Piloten-/Ausrüstungsmasse | Nicht freigegeben |
| Zulässiger Wind, Flughöhe und Temperaturbereich | Nicht festgelegt |
| Regen-/Staub-/Schutzart | Nicht nachgewiesen; keine IP-Klasse angegeben |
| Geräuschpegel | Nicht gemessen |
| Betriebszeit der Antriebe unter Last | Nicht nachgewiesen |
| Landelast, Ermüdung und Ausfallbeherrschung | Nicht nachgewiesen |
| Zulassung / Personenflugfreigabe | Liegt nicht vor |

## 6. Vorhandene Evidenz und Quellen

**Geometrie:** Native FreeCAD- und STEP-Dateien, gespeicherte und erneut geöffnete Baugruppen, Form-/Hüllmaßprüfungen und ausgewählte Abstandsprüfungen. Die 712 markierten Instanzen der Hauptbaugruppe enthalten auch Referenzkörper; ihre Volumina liefern keine verifizierte Fahrzeugmasse.

**Numerik:** Lokale 2D-Strömungsversuche bei Re = 40, darunter der zeitaufgelöste 240-mm-Begegnungsfall mit 48 000 Schritten. Keine realmaßstäbliche 3D-CFD und keine quantitativ unabhängig validierte Antriebsleistungsrechnung. Die neue Detailgeometrie wurde nicht als vollständiges Fahrzeug in CFD getestet.

**Nicht vorhanden:** realer Antriebsprüfstand, belastbare elektrische Leistungsaufnahme, Akkulastprüfung, Struktur-/Laminatnachweis und Flugversuch. Daher sind die offenen Kennwerte nicht durch Schätzwerte ersetzt.

Quellen: `konstruktion/parameter.json`, `konstruktion/Pruefbericht.json`, `konstruktion/Stueckliste_Instanzen.csv`, natives Steh-Hauptmodell, horizontale Geometrieparameter und `begegnung/results/Laufbericht.json`. Die maschinenlesbare Datei `Technisches_Datenblatt.json` enthält die Quellprüfsummen und kennzeichnet nicht bestimmte Leistungswerte mit `null`.

**Nächste Voraussetzung für ein Leistungsdatenblatt:** Schub und vollständige elektrische Aufnahme eines realisierbaren Moduls bestimmen, Massenbudget schließen und ein geeignetes Akkusystem auswählen. Erst danach lassen sich Tragfähigkeit, Kapazität, Stromverbrauch und erreichbare Flugzeit verbindlich beziffern.
