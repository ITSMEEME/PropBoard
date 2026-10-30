#!/usr/bin/env python3
"""Readable report, plots and an explicitly unverified product shortlist."""
import json,math,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pruefen as K
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'Mechanikpruefung.json').read_text());kin=r['kinematics']
points=json.loads((HERE/'Betriebspunkte_H01.json').read_text())['scenarios']
mount=json.loads((HERE.parent/'halterungen/Ausgabe/Geometriepruefung_H01.json').read_text())

fig,ax=plt.subplots(figsize=(8,4.5))
for servo_mass in (9,20,60):
 a=[q for q in r['load_sensitivity'] if q['label']=='tw2_model' and q['assumed_servo_mass_g']==servo_mass]
 ax.plot([q['mu_assumed'] for q in a],[q['with_factor_2_kgcm'] for q in a],marker='o',label=f'6 x {servo_mass} g Servo; {a[0]["vehicle_mass_kg"]:.3f} kg gesamt')
ax.set(xlabel='Angenommener effektiver Gleitreibwert μ',ylabel='Servomoment je Servo mit Faktor 2 [kg·cm]',title='Bedingte Vorauslegung bei Modell-Schub/Gewicht = 2')
ax.grid(alpha=.3);ax.legend();fig.tight_layout();fig.savefig(HERE/'Servomoment_Reibung.png',dpi=160);plt.close(fig)
pose,_=K.fit_pose(21,4,0,1);angles=np.arange(0,361,2);actual=[];wanted=[]
for a in angles:
 desired=np.array([(21+4*math.sin((a+360*k/K.N)*K.DEG))*K.DEG for k in range(K.N)])
 th,_=K.forward(pose,float(a),1,desired);actual.append(th[0]/K.DEG);wanted.append(desired[0]/K.DEG)
fig,(ax,bx)=plt.subplots(2,1,figsize=(8,5),sharex=True,gridspec_kw={'height_ratios':[2,1]})
ax.plot(angles,wanted,label='vorgegebener Sinus');ax.plot(angles,actual,'--',label='geschlossene 15-mm-Gestänge');ax.set_ylabel('Blattpitch [°]');ax.legend();ax.grid(alpha=.3)
bx.plot(angles,np.array(actual)-wanted,color='tab:red');bx.set(xlabel='Rotorazimut [°]',ylabel='Abweichung [°]');bx.grid(alpha=.3)
fig.suptitle('Feste Taumelscheibenlage: 21° kollektiv + 4° zyklisch, oben');fig.tight_layout();fig.savefig(HERE/'Pitchvergleich.png',dpi=160);plt.close(fig)

shortlist={'status':'BLOCKED_MANUFACTURER_DATA_ACCESS_NOT_A_PURCHASE_OR_FIT_APPROVAL',
 'requirements':{'number':6,'servo_horn_proposal_mm':8,'proposed_shaft_orientation':'tangent_to_rotor_circle',
   'required_proposed_travel_deg':[float(min(kin['servo_min_deg'])),float(max(kin['servo_max_deg']))],
   'speed_design_target_s_per_60deg':.12,'speed_target_is_measured_under_load':False,
   'low_friction_effective_mu_0_03_target_class_kgcm':7,
   'sliding_mu_0_1_with_60g_servo_target_class_kgcm':15,
   'sliding_mu_0_2_with_60g_servo_target_class_kgcm':25,
   'voltage':'dedicated regulated BEC at selected servo rated voltage; never direct 6S',
   'electrical':'3.3 V FC signal compatibility and pulse/frame format must be documented; BEC peak sizing from datasheet stall currents and measured loads'},
 'candidates':[{'name':'KST X15-755X','role':'candidate for revised low-friction pitch root',
   'data_status':'not retrieved; torque, speed, dimensions, mounting, pulse format, mass and current unverified',
   'supplier_search':'https://kstservos.com/search?q=X15-755X'},
   {'name':'Savox SB-2270SG','role':'candidate for higher torque conventional-servo revision',
    'data_status':'not retrieved; torque, speed, dimensions, mounting, pulse format, mass and current unverified',
    'supplier_search':'https://www.savoxusa.com/search?q=SB-2270SG'}],
 'observed_access':{'kstservos.com':'HTTPS CONNECT HTTP 403', 'www.savoxusa.com':'HTTPS CONNECT HTTP 403'},
 'next_step':'allow manufacturer domains through environment settings or provide product datasheets; then check required rated-voltage torque, continuous load/temperature, travel, horn, voltage/current and actual mounting geometry'}
(HERE/'Servoauswahl_OFFEN.json').write_text(json.dumps(shortlist,ensure_ascii=False,indent=2))

lines=['# Mechanikprüfung Koaxialrotor / zwei Taumelscheiben', '',
 'Stand 30.10.2026. Bezug: F01-Rotor, neue FC/ESC-/Akkuhalter H01. **Rechnerische Prüfung mit ausdrücklich bedingten Lastannahmen; keine mechanische oder betriebliche Freigabe.**','',
 '## Ergebnis', '',
 '**Das Taumelscheibenprinzip ist kinematisch plausibel; der aktuelle Aufbau ist mechanisch unvollständig. Ein 9-g-Mikroservo ist nicht pauschal ausreichend.** Fehlende echte Servoarme, Kugelanschlüsse, axiale Sicherungen und die reibende Fliehkraftabstützung verhindern eine belastbare Hardwarefreigabe. Die frühere Aussage „Standard-Mikroservos reichen“ wird durch diese Prüfung nicht bestätigt.','',
 '## Nachweise und Prüfumfang','',
 f'- Unabhängige Vorwärts-/Rückwärtskinematik: {kin["samples"]} Zustände, {kin["blade_closure_checks"]} Blatt-Gestängeschlüsse, beide Drehrichtungen, Kollektiv −2…21°, Zyklik bis 4°, Zyklikrichtung in 30°-Schritten, Rotorwinkel in 10°-Schritten.',
 f'- Größter numerischer Restfehler im mathematisch geschlossenen 15-mm-Gestänge: {kin["max_closed_link_error_mm"]:.3g} mm. Dies ist keine Aussage über reales Gelenkspiel.',
 f'- Größte Abweichung vom vorgegebenen Sinus: {kin["max_requested_pitch_error_deg"]:.3f}°. Acht feste Stangen lassen bei endlichen Winkeln keinen beliebigen idealen Sinus mit nur drei Taumelscheiben-Freiheitsgraden zu.',
 '- Zwölf Vergleichsfälle mit dem bestehenden FreeCAD-Posesolver stimmen bis etwa 10⁻¹² in den Posekomponenten überein. Das prüft die Rechengeometrie; es validiert keine Material- oder Reibannahmen. Die F01-Kollisionsgeometrie verwendet den vorgegebenen Pitch. Für eine mechanische Freigabe muss sie mit den tatsächlich geschlossenen Vorwärtswinkeln und realen Gelenken erneut untersucht werden.',
 '- Die virtuelle Arbeit nutzt die vollständige 8-Blatt-/3-Servo-Jacobimatrix. Nicht einfach die Kraft eines Blattes durch drei teilen.',
 '- Lastauswertung an 7 Kollektivwerten, 12 Zyklikrichtungen plus Nullzyklik, beiden Rotorseiten und vier Rotorazimuten je 45°-Periode. Kein kontinuierlicher Extremwert- oder Resonanznachweis.','',
 '## Funktionsprüfung und tatsächlich offene Mechanik','',
 '1. **Koaxiale Drehrichtung:** Die untere lokale Rotorachse wird im CAD nach −z gespiegelt; gleiche lokale Drehung ergibt entgegengesetzte Weltdrehung. Bei der Zyklik sind die stationären Servoazimute oben 60/180/300°, unten im Fahrzeug 120/0/240°. Den Mischer nicht unverändert kopieren; Vorzeichen und dynamische Phasenlage am Prüfstand identifizieren.',
 '2. **Servoanlenkung:** F01 zeichnet veränderlich lange Stangen zu festen Punkten bei z60. Ein realer Servoarm und ein festes Servogestänge fehlen. Die neue Rechnung schlägt 8-mm-Horn, tangentiale Abtriebsachse, radial-vertikale Hornebene und r58,3/z60 als Geometrie vor. Das ist ein berechneter Vorschlag, kein verifiziertes Produktlochbild.',
 f'3. **Stellweg:** Etwa {min(kin["servo_min_deg"]):.1f}…+{max(kin["servo_max_deg"]):.1f}° relativ zum Schwebezustand, also rund 35°. Ein typischer ±60°-Servo wäre vom Weg her ausreichend; tatsächliche elektronische Endpunkte und Kollisionsräume müssen mit dem gewählten Produkt geprüft werden.',
 '4. **Drehzahl und Bandbreite:** Für gleichbleibende Zyklik bleibt die stationäre Taumelscheibe geneigt. Die Servos müssen nicht pro Rotorumdrehung hin und her laufen. Rotierende Pitchglieder tun dies; deren Beschleunigung, Reibung, Spiel und Ermüdung bleiben relevant. 0,12 s/60° ist ein Entwurfsziel für den Servo, kein gemessener Regelbandbreitennachweis.',
 '5. **Pitchwurzel:** Die gedruckte Nut und zwei D2-Stifte nehmen die Fliehkraft gleitend auf. Deren Reibmoment μ·Fz·4,8 mm kann die Servoauslegung dominieren. Eine definierte Radiallagerung und eine separate, gering reibende axiale Fliehkraftabstützung sind die bevorzugte nächste Revision. Ein nominell stärkerer Servo ersetzt diesen Nachweis nicht.',
 '6. **Sicherungen/Lastpfade:** Die F01-Pitchhebel besitzen keinen fertigen Kugelbolzenanschluss und keine ausgearbeitete axiale Sicherung. Stationäre Taumelarme besitzen keine ausdefinierten Bolzensitze. Der geschlitzte Motor-/Servoträger hat noch keine Klemmschraube und die Lagerringe keine nachgewiesene axiale Sicherung. Die geschlossene Kugelpaarung benötigt eine plausible Montagefolge oder konstruktive Teilung. Die neuen Endadapter sichern die Halter, schließen diese offenen Rotoranschlüsse aber nicht.',
 '7. **Spiel:** Der effektive vertikale Pitchhebel ist 9·cos(θ) − 5,5·sin(θ), bei 25° nur etwa 5,83 mm. 0,1 mm wirksames Spiel kann dort rund 0,98° Pitchfehler bedeuten. Die alte konstante 9-/12-mm-Hebelabschätzung genügt nicht. Reale Kugelgelenke, Wurzel und Servogetriebe auf Gesamtspiel prüfen.','',
 '## Bedingte Servolast mit neuer Haltermasse','',
 'CAD-Trägheit statt pauschalem Rechteck: Blattmasse 8,920 g bei angenommener homogener effektiver Dichte, Schwerpunkt r109,464 mm. Tatsächliche Druckinfill-Verteilung muss gewogen/gemessen werden. Verwendet werden Fliehkraft-Twistmoment, Pitch-Beschleunigung aus geschlossener Kinematik, BEMT-Mittelschub mit 25-%-Sehnenhebel und Gleitreibung. Beträge werden ohne hilfreiche Vorzeichenkompensation addiert. Der Luftkraftansatz ist kein validierter Worst-Case-Grenzwert; insbesondere zyklische Luftlasten und echte Profilmomentenkennfelder fehlen.','',
 '| Servomasse je Stück | Gesamtmasse H01 | Schweben, Modell | Schub/Gewicht 2, Modell |', '|---|---:|---:|---:|']
for s in points:lines.append(f'| {s["assumed_servo_mass_g"]} g | {s["mass_kg"]:.3f} kg | {s["hover"]["rpm"]:.0f} U/min | {s["tw2"]["rpm"]:.0f} U/min |')
lines += ['', '**Erforderliches Moment je Servo bei Modell-Schub/Gewicht 2, bereits mit Faktor 2:**','', '| effektiver Reibwert μ | 9-g-Servos | 20-g-Servos | 60-g-Servos |','|---|---:|---:|---:|']
for mu in (0.,.03,.1,.2):
 vals=[next(x['with_factor_2_kgcm'] for x in r['load_sensitivity'] if x['label']=='tw2_model' and x['assumed_servo_mass_g']==m and x['mu_assumed']==mu) for m in (9,20,60)]
 lines.append(f'| {mu:.2f} | '+ ' | '.join(f'{v:.2f} kg·cm' for v in vals)+' |')
lines += ['', 'μ ist hier eine Sensitivitätsannahme, kein gemessener Werkstoffwert. Ein äquivalenter kleiner Wert für eine überarbeitete Wälzlagerung ist erst durch Messung zu bestätigen. Hersteller-Stallmoment ist kein Dauerbetriebsmoment. Faktor 2 und Stallreserve ersetzen keine Strom-/Temperaturmessung.', '',
 'Reale Servo-Befestigungen, BEC und Schutzteile sind noch nicht vollständig im genannten Massenbudget enthalten. Die Rechnung ist daher eine bedingte Vorauslegung. Mit großen Servos steigt die Masse erheblich. Die 60-g-Variante erreicht rechnerisch etwa 3675 U/min für Schub/Gewicht 2; der 120-%-Screeningfall läge bei etwa 4410 U/min. Das überschreitet den früheren Rechen-/Prüfbereich. Diese Zahl ist **kein Auftrag für einen Schleuderversuch** und keine Drehzahlfreigabe.','',
 '## Servosuche – konkrete Kandidaten, Datenblattprüfung offen','',
 '- **KST X15-755X:** Kandidat für eine leichte Revision mit gering reibender Pitchlagerung. Zielklasse mindestens etwa 7 kg·cm bei tatsächlich gewählter Versorgung. Drehmoment, Masse, Geschwindigkeit, Lochbild, Horn, Signalformat und Strom dieses Produkts sind hier noch nicht aus dem Herstellerdatenblatt verifiziert.',
 '- **Savöx SB-2270SG:** Kandidat für eine stärkere konventionelle Servo-/Halterrevision. Für den angenommenen Reibwert 0,1 bei schweren Servos wäre mindestens die 15-kg·cm-Klasse anzustreben; bei 0,2 eher 25 kg·cm. Auch dieser Kandidat ist ausdrücklich noch nicht mit aktuellen Herstellerdaten oder dem Bauraum abgeglichen. **Keiner ist als Drop-in-Ersatz oder zum Kauf freigegeben.**',
 '- Beide Anbieterzugriffe wurden versucht und vom Umgebungsproxy mit HTTP 403 abgewiesen. Die nötigen Domainergänzungen wurden im Konfigurationsentwurf gespeichert, sind im laufenden Netz noch nicht aktiv. Für eine belastbare Produktauswahl Herstellerzugriff ermöglichen oder Datenblätter bereitstellen. Keine Spezifikationen oder Preise wurden als recherchiert ausgegeben.',
 '- Kandidatenlinks: [KST-Suche](https://kstservos.com/search?q=X15-755X), [Savöx-Suche](https://www.savoxusa.com/search?q=SB-2270SG). Das sind Rechercheziele, keine hier eingesehenen Datenquellen.', '',
 '## Elektrik und nächste messbare Schritte','',
 'Sechs Servos brauchen eine eigene geregelte Versorgung passend zum gewählten Servo. Einen üblichen 6-/7,4-/8,4-V-Servo niemals direkt an den 6S-Akku (bis 25,2 V) anschließen. BEC-Spitzenstrom aus sechs tatsächlichen Servo-Stallströmen und Lastmessungen dimensionieren; Dauerstrom/Temperatur nachweisen. FC-Signalpegel, Neutralpuls und zugelassene Rahmenfrequenz im Datenblatt prüfen; einen 760-µs-Heckservo nicht ungeprüft als Taumelscheibenservo verwenden.',
 'Vor verbindlicher Auswahl: axiale Pitchlagerung schließen, Reibmoment unter radialer Ersatzlast messen, Gesamtspiel messen, echten Servoarm/Servoanschluss einzeichnen. Danach Herstellerdaten gegen Moment, Stellweg, Spannung, Strom und Gehäuse einschließlich Befestigungsflanschen prüfen. Abschließend statische Belastung und niedrige Stellgeschwindigkeiten mit vollständiger Lager-/Schraubensicherung prüfen. Geometrie-, Material-, Temperatur- und Regelungsfreigaben bleiben getrennte Nachweise.','',
 '## Dateien und Reproduktion','',
 '- `Mechanikpruefung.json`, `Kinematik_Sweep.csv`, `CAD_Abgleich.json`: numerische Ergebnisse und Vergleich.',
 '- `Fluegel_Traegheit.json`: aus dem vorhandenen FreeCAD-Blattkörper extrahiert; Füllannahme enthalten.',
 '- `Betriebspunkte_H01.json`: BEMT-/Antriebsmodell mit H01-Masse und Servo-Massensensitivität.',
 '- `Servoauswahl_OFFEN.json`: Anforderungen, unbestätigte Kandidaten und konkret blockierter Datenzugriff.',
 '- `Servomoment_Reibung.png`, `Pitchvergleich.png`, `Mechanikbericht.pdf`: lesbare Darstellung.',
 '```sh', 'export FREECAD_LIB="$PWD/.cfd-tools/freecad/usr/lib"', '.cfd-tools/freecad/usr/bin/python modell_r04_taumel/mechanik/traegheit_erstellen.py', 'node modell_r04_taumel/mechanik/betriebspunkte.js', 'OPENBLAS_NUM_THREADS=2 .cfd-tools/venv/bin/python modell_r04_taumel/mechanik/pruefen.py', 'MPLCONFIGDIR=/workspace/.propboard/cache/matplotlib .cfd-tools/venv/bin/python modell_r04_taumel/mechanik/bericht_erstellen.py','```','']
text='\n'.join(lines);(HERE/'README.md').write_text(text)

font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';pdfmetrics.registerFont(TTFont('DV',font))
styles=getSampleStyleSheet()
for name in ('Normal','Title','Heading1','Heading2','BodyText'):styles[name].fontName='DV'
styles['Normal'].fontSize=9;styles['Normal'].leading=13
story=[Paragraph('Koaxialrotor / Taumelscheiben – Mechanikprüfung H01',styles['Title']),Spacer(1,5*mm)]
# Render the readable text as paragraphs and compact tables; source markdown is
# the complete report and JSON contains every numerical case.
for line in lines[2:]:
 if not line:story.append(Spacer(1,2*mm));continue
 if line.startswith('```') or line.startswith('|---'):continue
 if line.startswith('## '):story.append(Paragraph(line[3:],styles['Heading2']));continue
 if line.startswith('|'):
  cells=[c.strip() for c in line.strip('|').split('|')]
  story.append(Paragraph('  /  '.join(cells),styles['Normal']));continue
 import html,re
 clean=html.escape(line).replace('**','')
 clean=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'\1 (\2)',clean)
 story.append(Paragraph(clean,styles['Normal']))
story.extend([PageBreak(),Paragraph('Servomoment und Reibannahme',styles['Heading2']),Image(str(HERE/'Servomoment_Reibung.png'),width=170*mm,height=95.6*mm),
 Spacer(1,6*mm),Image(str(HERE/'Pitchvergleich.png'),width=170*mm,height=106.2*mm)])
SimpleDocTemplate(str(HERE/'Mechanikbericht.pdf'),pagesize=(210*mm,297*mm),leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=18*mm).build(story)
print('Mechanics report, two plots and blocked-data shortlist written')
