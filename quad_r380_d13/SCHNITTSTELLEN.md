# Elektrische Projektschnittstellen D13

Maschinenlesbar: [Parameter](parameter.json) · [Pinliste](Ausgabe/Pinbelegung.csv). Dies sind projektseitige Anschlussdefinitionen. **Sie beschreiben nicht die unbekannte Pinbelegung des V200A-JP-/M6-Anschlusses.** Kabelfarben, „M6“ und die Anzahl der Adern erlauben keine sichere Funktionszuordnung. Originalleitungen bleiben erhalten; Adapter werden erst nach bestätigtem Schaltplan oder fachgerechter Zuordnungsprüfung konfektioniert.

## DC: XDC

Anderson-SB120-Familie, zweipolig, passende Gehäusefarbe/Codierung. Gehäusemarkierung + erhält DC+, − erhält DC−; diese Markierung ist maßgeblich, nicht eine Ansicht von vorn oder hinten. Herstellerfreigegebener Kontakt für AWG10 beziehungsweise zugelassener Reduziereinsatz erforderlich. Die vorgesehene Anwendung verlangt eine dokumentierte Auslegung auf mindestens 150 V DC und die erforderliche Dauerstromklasse unter tatsächlichen Temperaturbedingungen. Eine Familienbezeichnung ersetzt weder Kontaktwahl noch Derating.

Projektreserve im gesteckten Zustand: **140×75×40 mm**, ausschließlich als Einbaubudget; kein behauptetes SB120-Herstellermaß. Exakte SKU, Kontakt, Gehäusepaar und CAD fehlen. Lasttrennen und Antiblitzfunktion sind nicht belegt; Schütz, Sicherung und Vorladung müssen separat ausgelegt werden. Keine hot-plug-Freigabe.

## CAN: XCAN

M12, A-codiert, fünfpolig; mechanische Steckfamilie nach IEC 61076-2-101. Funktionszuordnung angelehnt an CANopen/CiA 303-1:

| Pin | Funktion |
|---|---|
| 1 | Schirm/Drain |
| 2 | nicht belegt; keine Versorgung |
| 3 | CAN-Bezugspotential GND |
| 4 | CAN-H |
| 5 | CAN-L |

Das H/L-Paar wird durchgängig verdrillt als 120-Ω-Paar beschafft. Der zweite Leiterpaarplatz dient Bezugspotential/Reserve. Schirmführung und Gehäusekontaktierung sind im EMV-Konzept festzulegen; sie führen keinen Motorstrom. Die Pinzahlen beziehen sich auf die Kontaktkennzeichnung am gewählten Kaufteil. Rückseitenansichten sind gegenüber Steckansichten gespiegelt.

Vorgesehen sind vier getrennte Zwei-Knoten-Segmente mit je einem Regler, keine passive Sternverkabelung mit vier langen Armen. Zentral werden vier CAN-Kanäle oder ein passendes Gateway benötigt; diese Hardware ist noch nicht integriert. Je Segment 120 Ω zwischen H und L an beiden physischen Enden; eine vorhandene OEM-Terminierung zählt mit. 500 kbit/s ist ein Projektziel, nicht bestätigte V200A-Konfiguration. Protokoll, Bitrate, Isolation und Bezugspotentialverträglichkeit müssen bestätigt werden.

## PWM: XPWM

M8, A-codiert, dreipolig; mechanische Steckfamilie nach IEC 61076-2-104. **Projektbelegung**, kein allgemeingültiges PWM-Herstellerpinout:

| Pin | Funktion |
|---|---|
| 1 | nicht belegt; keine BEC-Versorgung |
| 3 | Signal-GND |
| 4 | PWM-Befehl |

Der V200A hat keine BEC. Bordelektronik benötigt eine eigene Versorgung. PWM-Logikpegel, Eingangsreferenz und eventuelle galvanische Trennung sind noch zu klären. Die übermittelten Werte 1040–1940 enthalten keine ausdrücklich genannte Einheit; µs darf erst nach Bestätigung als Regleranforderung gelten.

## Fünfadrige Serviceleitung: XSERVICE

M12, **B-codiert**, fünfpolig nach mechanischer Steckfamilie IEC 61076-2-101. B-Codierung unterscheidet diesen Anschluss von CAN-A-Codierung. Pins 1–5 führen ausschließlich die passiv nummerierten Adern SERVICE_W1 bis SERVICE_W5. Dies ist **keine Profibus-Belegung**, keine Encoder-ABZ-Belegung und keine Aussage über Versorgung/Signalrichtung am originalen „M6-Flugzeugkopf“. Der Originalstecker bleibt am OEM-Ende erhalten. Vor einer Verlängerung muss außerdem geklärt sein, ob diese Leitung einen Encoder oder eine andere Servicefunktion führt und ob eine Verlängerung zulässig ist.

## Gehäuse, Kabel und Qualifikation

M12-Projektreserve je Steckerhälfte: 20×20×60 mm; M8: 14×14×45 mm. Das sind maximale Beschaffungs-Einbaubudgets, **keine universellen IEC-Gehäuseabmessungen**. Kupplung, Knickschutz, erforderlicher Verschraubungsraum und tatsächlicher Kabel-Klemmbereich müssen anhand konkreter Artikel zusammenpassen. Es sind noch keine exakten Kaufteilkonturen im CAD vorhanden. M12/M8 dürfen ausschließlich die Steuerkreise führen, nicht die 24S-Leistung.

Die internen Projektleitungen werden nach den Außen-Ø-Obergrenzen 6,0 / 6,5 / 4,2 / 6,5 mm aus dem README beschafft. Für alle Leitungen werden mindestens 300 V Isolationsauslegung verlangt, für DC zusätzlich Silikon und mindestens 180 °C Materialklasse; das sind Auswahlforderungen, keine nachgewiesenen Produkteigenschaften. Die Temperaturklasse ist keine Freigabe für den Betrieb des Gesamtaufbaus bei dieser Temperatur. Plan-Biegeradien mindestens 50 mm (DC/CAN/Service), 30 mm (PWM), bis Hersteller strengere Werte vorgibt.

Noch erforderlich: konkrete Kabel- und Steckertypen samt Datenblättern/CAD, gemessene OEM-Außen-Ø und Kabelaustritte, bestätigter JP-/M6-Schaltplan, Kontakt-/Crimpfreigaben, Zugentlastung und Biegeführung, Durchgangs-/Isolationsprüfung, Strom-/Temperaturtest und EMV-Prüfung. Die mechanische Querschnittspassung ist unter den dokumentierten Entwurfsmaßen geprüft; die vollständige elektrische Konfektion ist nicht freigegeben.
