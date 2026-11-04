# Quad R380 D05 – MN1330 KV40 aus dem alten Aufbau

**Motorvorgabe durch den Nutzer: vier MN1330 KV40.** Die Motoren sind als verbindliche Auswahl im Modell und in der Stückliste erfasst. Ihre vorhandenen P14-Zeichnungsreferenzen sind an den vier Quad-Achsen eingesetzt. Die zugehörigen Motorträger sind neu mechanisch modelliert.

**Wichtig zum Modellumfang:** Das übernommene Motor-STEP ist ein vereinfachtes altes Projektmodell mit Außenmaß und Anschlussbohrungen, kein detailliertes Original-OEM-CAD. Es wird ausdrücklich als Referenz gekennzeichnet. Unbekannte Motorinnenteile, Lüftungskonturen, Kabelausgänge oder Gewindetiefen werden nicht erfunden. Die Vorgabe „keine schematischen Fertigteile“ ist damit für den Motor selbst noch nicht vollständig erfüllt; die Referenz ist kein Ersatz für eine spätere Originalgeometrie.

- [Interaktive CAD-Ansicht](Mechanik.html) · [Motorträger im Detail](MN1330_Motortraeger.png)
- [Native FreeCAD-Baugruppe](Ausgabe/QuadR380_D05_MN1330.FCStd) · [STEP-Baugruppe](Ausgabe/QuadR380_D05_MN1330.step)
- [Gesamtpaket](QuadR380_D05_Detailpaket.zip) · [Stückliste](Ausgabe/Stueckliste.csv)
- [Quellen und Originaldateien](Quellen/MN1330/Provenienz.json) · [Motor-Schnittstellen](Ausgabe/Motor_Schnittstellen.json)
- [Bauraumprüfung](Ausgabe/Bauraum_Pruefung.json) · [Montagezugänge](Ausgabe/Motor_Montage_Pruefung.json) · [Gewindeprüfung](Ausgabe/Gewindepruefung.json)
- [Betriebsgrenzen](Ausgabe/MN1330_Betriebsgrenzen.json) · [Elektrischer Integrationsplan](Elektrische_Integration.json)

## Motorträger und Montage

Die vier Motorachsen liegen weiterhin bei x/y=±425 mm. Jeder neue Träger ist160 x150 x8 mm groß, hat vier Ø6,6-mm-Durchgänge auf PCD50 sowie unterseitige Ø11-mm-Kopfsenkungen mit2 mm Tiefe. Das entspricht dem übernommenen4×M6-Motoranschluss. ISO4762 M6x12 werden von unten eingesetzt. Der Motorboden ist geschlossen; es wird kein Motordurchgang für Rahmen oder Kabel angenommen. Das zentrale Servicefenster des Trägers istØ24 mm.

Die beiden Träger-Schottverschraubungen liegen nun bei tangential±65 mm statt±45 mm und exakt radial544 mm. Damit liegen Köpfe und Scheiben außerhalb der Ø150-mm-Motorreferenz. Das Endschott verwendet dieselbe vorhandene Schottgeometrie mit±65-mm-M6-Gewinden wie die Wurzelschotte. Die verstellbaren Fußplatten und der plattenfreie Carbon-Zentralrahmen bleiben erhalten.

Montageannahme der Motorschrauben:6 mm nominaler Motoreingriff, wie im früheren P14-Entwurf. Diese Tiefe ist **nicht vom Hersteller bestätigt**. Die Altmodellbohrungen enthalten keine qualifizierte Motor-Innengewindegeometrie. Vor realer Montage müssen Gewindetiefe, Eingriff, Schraubenlänge, Material, Vorspannung und Anzugsmoment bestätigt werden. Aus der nominalen Passung ergibt sich keine Bestell-/Montagefreigabe.

Die XLS nennt Ø150 x65 mm; die alte Zeichnungsreferenz ist66 mm lang. D05 verwendet unverändert die größere66-mm-Referenz und verschiebt ausschließlich deren alten z14..80-Bezug auf z0..66. Die Einbauebene liegt bei z88 mm. Die Motorhöhe und alle realen Anschlussbezüge bleiben zu bestätigen. Motorlager-Axiallasten und das Tragen des Rotorschubs sind ebenfalls offen.

## Masse

| Umfang | Masse |
|---|---:|
| D04 mechanische Baugruppe | 19.841 kg |
| Vier MN1330 inklusive Anschlussdraht laut Nutzer-XLS | 11,000 kg |
| D05 einschließlich neuer Träger und Schrauben | **31.002 kg** |

Der Motor erhält eine dokumentierte Massenüberschreibung von2,75 kg je Stück. Masse oder Trägheit werden nicht aus dem künstlichen Referenzvolumen abgeleitet. Akku, Regler, Rotoren, Versorgungskabel, Kühlsystem, Schutz und Fahrwerk sind nicht in dieser Summe enthalten. Zusätzliche Motorleitungen dürfen bei der späteren Kabelbaummasse nicht nochmals als bereits enthaltene150-mm-Anschlussdrähte gezählt werden.

## Prüfungen

- 202 nominale Gewindepaarungen im dokumentierten Struktur-/Träger-Prüfbereich bestanden. Dazu gehören acht geänderte Träger-Schott-Verbindungen. Die16 Motor-Innengewinde sind ausdrücklich nicht Teil dieser Aussage.
- 1630 statische Kandidatenpaarungen im gewählten Prüfbereich, 0 Überschneidungen über0,1 mm³. Motorprüfungen beziehen sich auf die alte Nennreferenz, nicht auf reale Lüftungs-/Kabelkonturen.
- 52 Zustände der Fußverstellung gegen alle festen Nachbarn geprüft; insgesamt 0 gemeldete Überschneidungen.
- 24 gerade Werkzeugzugänge für16 unterseitige Motor- und acht oberseitige Trägerschrauben geprüft. Analytische Zylinder: Radius3,6 mm, Länge35 mm. Kein Nachweis für Werkzeuggriffe, Handhabung, Anzug oder spätere Leitungen.
- Separate Neugenerierung reproduziert Teilezahl, Positionen und Massen. STEP wurde wieder eingelesen; alle856 Körper sind vorhanden. Die Prototypen sind gültige Einzelkörper; eine erneute Gültigkeitsprüfung jedes STEP-Rückimportkörpers wird nicht behauptet.

## Motorwahl und Flugnachweis sind unterschiedliche Schritte

KV40 ergibt an24S rechnerisch maximal4032 U/min im Leerlauf bei100,8 V. Der frühere angenommene R380-Dreiblatt-Rechenbereich liegt bei4868–5621 U/min. Dieser Rotorbetriebspunkt ist mit dem gewählten Motor nicht belegt; ein passender realer Rotor und belastbare Kennfelder sind erforderlich. Die NS52×20-Prüftabelle gehört zu einem rund1321-mm-Propeller und lässt sich nicht auf einen760-mm-Rotor übertragen.

Die bereitgestellte XLS nennt3400 W mit180 s Zeitbezug, ohne eindeutig bezeichnete Leistungsseite. Die höheren Prüfwerte bis16270 W elektrisch besitzen keine bekannte Haltedauer und werden nicht als Dauerleistung oder180-s-Freigabe verwendet.

Selbst wenn man3400 W je Motor als Wellenleistung ansetzt, ergeben vier Motoren13,6 kW in diesem Referenzfall. Bei100 kg Person und der aktuellen Teilmasse von31.002 kg beträgt die ideale Freiluft-Schwebe-Untergrenze außerhalb des Bodeneffekts bereits rund21.85 kW. Sie setztρ=1,225 kg/m³, vier R380-Scheiben und keinerlei Profil-, Drall- oder elektrische Verluste voraus. Das ist eine bedingte physikalische Grenze des3,4-kW-Rechenfalls, keine vollständige Vermessung aller Motorbetriebspunkte. Aus den zeitlich unbestätigten höheren Prüfwerten folgt keine Flugfreigabe.

24S und M200A24S sind zunächst Versorgungsreferenz beziehungsweise Reglerempfehlung aus der XLS. Ein konkreter Regler, Akku/BMS und Kabelbaum sind noch nicht physisch integriert. Die geänderten Motorlasten erfordern außerdem neue CFK-, Verbindungs-, Schwingungs- und Ermüdungsnachweise.

## Reproduktion

`normteile_erstellen.py` erzeugt bei Bedarf die neue M6x12-Normgeometrie aus dem gepinnten Fasteners-Stand. Danach `motoren_einbauen.py`, `gewinde_pruefen.py`, `bauraum_pruefen.py`, `motor_montage_pruefen.py`, `ableiten.py`, `viewer_pruefen.cjs` und `dokumentieren.py`. Der unabhängige Neuaufbau wurde mit `D05_OUTPUT_DIR=/tmp/quad-d05-fresh-check` ausgeführt und mit `neuaufbau_pruefen.py` verglichen.

Das Paket enthält die D04-Eingangsbaugruppe, deren Register, die erforderlichen Normteil-BReps, die ursprüngliche P14-Motorreferenz und die unveränderten Nutzer-XLS-/CSV-Dateien. Das ursprüngliche OEM-CAD fehlt weiterhin; kein Dateiname oder Prüfergebnis erklärt die Referenz zu einem Hersteller-Fertigungsmodell.
