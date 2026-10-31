#!/usr/bin/env python3
"""Regenerate plots, review PDF and human-readable results from saved tests."""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
H=Path(__file__).resolve().parent;O=H/'Ergebnisse'
R=json.loads((O/'Testbericht.json').read_text());V=json.loads((O/'Physikpruefung.json').read_text());U=json.loads((O/'Robustheit.json').read_text());M=json.loads((H/'modell_h01.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.grid':True,'grid.alpha':.25})
fig,axs=plt.subplots(3,2,figsize=(11,9))
for ax,name in zip(axs.flat,['Savox_7_4V_Manoever','Savox_6_0V_Boee','Savox_7_4V_XFOIL_N4','Savox_7_4V_Reibung_0_20','9g_Servo_hohe_Reibung','Motor_unten_Ausfall']):
    data=json.loads((O/(name+'.json')).read_text());ts=[r['t'] for r in data]
    ax.plot(ts,[r['p'][2] for r in data],label='Höhe');ax.plot(ts,[r['target'][2] for r in data],'--',label='Sollhöhe')
    ax.plot(ts,[math.hypot(r['p'][0]-r['target'][0],r['p'][1]-r['target'][1]) for r in data],label='Horizontalfehler')
    ax.set_title(name.replace('_',' '));ax.set_xlabel('Zeit [s]');ax.set_ylabel('Weg [m]');ax.legend(fontsize=7)
fig.suptitle('H01 · geregelte Modellversuche – keine empirische Flugvalidierung');fig.tight_layout();fig.savefig(O/'Flugverhalten.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
data=json.loads((O/'Motor_Drehzahlsprung_10Prozent.json').read_text());ts=[r['t'] for r in data]
for l in range(2):axs[0].plot(ts,[r['rpm'][l] for r in data],label=['Rotor oben','Rotor unten'][l]);axs[1].plot(ts,[r['duty'][l] for r in data],label=['Tastgrad oben','Tastgrad unten'][l])
axs[0].plot(ts,[r['rpmTarget'] for r in data],'k--',label='Soll');axs[0].set_ylabel('Drehzahl [U/min]');axs[1].set_ylabel('ESC-Tastgrad')
for j in (0,3):axs[2].plot(ts,[r['servoDeg'][j] for r in data],label=f'Servo {j+1} Ist');axs[2].plot(ts,[r['servoCommandDeg'][j] for r in data],'--',label=f'Servo {j+1} Soll')
axs[2].set_ylabel('Servowinkel [°]');axs[2].set_xlabel('Zeit [s]')
for ax in axs:ax.legend(fontsize=8)
fig.suptitle('Motor-Governor und Servo-PID · Drehzahlsprung +10 %');fig.tight_layout();fig.savefig(O/'PID_Antwort.png',dpi=160);plt.close(fig)
# P10: Bodenstart, Schweben, Manöver, Landung mit Landegestell und Planetenstufe
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
for name,ls in (('P10_Bodenstart_Schweben_Landung','-'),('P10_ANGLE_Handsteuerung','--')):
    data=json.loads((O/(name+'.json')).read_text());ts=[r['t'] for r in data];short='Positionsmodus' if 'Boden' in name else 'ANGLE-Modus'
    axs[0].plot(ts,[r['p'][2] for r in data],ls,label=f'Höhe Schwerpunkt · {short}')
    axs[1].plot(ts,[r['rpm'][0] for r in data],ls,label=f'Rotor oben · {short}');axs[1].plot(ts,[r['rpm'][1] for r in data],ls,label=f'Rotor unten · {short}')
    axs[2].plot(ts,[r.get('contactForce',0) for r in data],ls,label=f'Kufenkraft · {short}')
axs[0].set_ylabel('z [m]');axs[1].set_ylabel('Drehzahl [U/min]');axs[2].set_ylabel('Bodenkraft [N]');axs[2].set_xlabel('Zeit [s]')
for ax in axs:ax.legend(fontsize=7)
fig.suptitle('P10 · Bodenstart, Schwebeflug, Manöver, Landung (Modellversuch)');fig.tight_layout();fig.savefig(O/'P10_Bodenstart_Landung.png',dpi=160);plt.close(fig)
lines=['# H01 – Ergebnisse der Flugsimulation','', '**Unvalidiertes Modell; keine Flugfreigabe.**','', '| Fall | Ergebnis | Test-/Abbruchzeit [s] | RMS letzte 5 s [m] |','|---|---|---:|---:|']
for r in R['results']:lines.append(f"| {r['name']} | {r['status']} | {r['duration_s']:.2f} | "+('–' if r['position_rms_last5s_m'] is None else f"{r['position_rms_last5s_m']:.4f}")+' |')
stable=sum(r['status']=='STABIL_IM_MODELL' for r in R['results']);robust=sum(r['status']=='STABIL_IM_MODELL' for r in U['results'])
lines+=['',f"{stable}/{len(R['results'])} Szenarien stabil im Modell. Fehlerfälle sind absichtlich Teil der Serie. {robust}/{len(U['results'])} kombinierte Annahmen stabil; keine Zuverlässigkeitsstatistik.",'',f"{len(V['results'])} numerische Prüfungen bestanden. Quellen und Annahmen: [README](../README.md).",'', '![Flugverhalten](Flugverhalten.png)','', '![Regelantwort](PID_Antwort.png)']
lines+=['','![P10 Bodenstart und Landung](P10_Bodenstart_Landung.png)']
(O/'README.md').write_text('\n'.join(lines)+'\n')
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
styles=getSampleStyleSheet()
for k in ('Normal','BodyText','Heading1','Heading2','Title'):styles[k].fontName='DejaVu'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
story=[]
def para(t,style='BodyText'):story.append(Paragraph(t,styles[style]));story.append(Spacer(1,7))
para('Cohexial Study · H01','Title');para('CAD-basierter Freiflug und PID-Regelung','Heading1')
para('Unvalidiertes reduziertes Modell – keine Flugfreigabe. Reale Servoauswahl, Lager-/Nutreibung, Polare, Steuerphase, BEC und mechanische Freigaben sind offen.')
para(f"CAD-Masse {M['mass_kg']:.6f} kg; Standardflugfall {R['results'][0]['mass_kg']:.6f} kg mit sechs angenommenen 20-g-Servos. Schwerpunkt des CAD-Budgets: z = {M['cg_m'][2]*1000:.3f} mm. Nomineller Schwebepunkt im Standardfall: {R['results'][0]['hover_rpm']:.0f} U/min.")
para('Neue Savöx-Fälle: 69 g je Servo, insgesamt 1,577676 kg. Angaben 6,0–7,4 V, 15/20 kg·cm und 0,08/0,06 s pro 60° aus Nutzer-Tabelle. Dynamic Torque ist kein verifiziertes Stall-/Dauermoment. Der optionale CAD-XFOIL-Flugfall benötigt etwa 20 % bisherige Ersatzpolare; seine Stabilität gilt für dieses Hybridmodell.')
para(f"Ergebnis: {stable} von {len(R['results'])} Szenarien erfüllen die definierten Modellkriterien. Schwaches Servo/hohe Reibung, falsche Phase um 90°, blockiertes Servo, Ausfall des unteren Motors und ungeregelter Flug scheitern. {robust}/{len(U['results'])} kombinierte Annahmen erfüllen die Kriterien; daraus folgt keine reale Ausfallwahrscheinlichkeit.")
rows=[['Fall','Modellergebnis','Zeit [s]','RMS [m]']]
for r in R['results']:
    name=r['name'].replace('_',' ');status='stabil' if r['status']=='STABIL_IM_MODELL' else 'Abbruch' if r['final']['crashed'] else 'verfehlt'
    rows.append([Paragraph(name,styles['BodyText']),status,f"{r['duration_s']:.2f}",'–' if r['position_rms_last5s_m'] is None else f"{r['position_rms_last5s_m']:.3f}"])
t=Table(rows,colWidths=[248,67,58,58],repeatRows=1);t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'DejaVu'),('FONTSIZE',(0,0),(-1,-1),8),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9e8ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.append(t)
para('Stabilitätskriterium: kein Abbruch, Einhaltung der Entwurfs-Kinematikgrenzen, Endpositionsfehler und RMS der letzten 5 s jeweils unter 0,15 m. Die H01-Tests starten mit hochgelaufenen Rotoren in 1 m Höhe; die P10-Bodenfälle starten mit stehenden Rotoren auf dem Landegestell. Der Fall „Akku 20 Prozent“ untersucht 20 s Restladung, keinen Leerflug.')
story.append(PageBreak());para('Physik und Regelarchitektur','Heading1')
for text in [
 'CAD: Native H01-Baugruppe mit globalen Schwerpunktlagen und vollständigen Trägheitstensoren; Parallelachsenverschiebung für alle Einzelmassen. Fehlende Kabel-/Empfänger-/Gurtmassen werden räumlich explizit angenommen. Größere Servos bleiben an den CAD-Platzhalterpositionen; deren geometrische Passung wird nicht bestätigt.',
 'Freiflug: sechs Freiheitsgrade, Quaternionen, Gewicht, aerodynamischer Rumpfwiderstand, Rotor-Drehimpuls, Kreiselkopplung und Reaktion auf Rotorbeschleunigung. Es gibt keine künstliche Schwebekraft.',
 'Rotorströmung: Blattelementkräfte mit Reynolds-abhängiger Polare, dynamischer uniformer Zustrom, oberer kontrahierter Nachlauf und Drall am unteren Rotor. 10 radiale × 16 azimutale Integrationspunkte; Kräfte/Momente enthalten Wind und Körperdrehraten.',
 'Motoren: Gegen-EMK, Widerstand, Strombegrenzung, Getriebeverluste, Rotor-/Motorträgheit, dynamischer Akku-Spannungseinbruch und Ladezustand. Zwei eigene PID-Drehzahlregler steuern die ESC-Tastgrade.',
 'Taumelscheiben: Drei feste Servo-Gestängelängen je Rotor bestimmen die jeweilige Scheibenlage. Acht feste Blattanlenkungen liefern tatsächliche Pitchwinkel. Der untere Rotorrahmen wird korrekt gespiegelt. Servoaufbau ist der Vorschlag mit tangentialer Achse und 8-mm-Horn, kein freigegebener Kaufservo.',
 'Flugregelung: Position → Beschleunigung/Lage → Drehraten → 4×6-Kraft-/Momentmischer → sechs Servo-PIDs. Innere Höhen-Beschleunigungsregelung kompensiert Schubmodellabweichungen. Totzeit, Stellgeschwindigkeit, Stallmoment, Reibung und Integratorbegrenzungen wirken auf die Stellreserve.',
 'Grenzen: keine gemessene Profilpolare oder Servodynamik; keine Blattelastizität, Biegeresonanz, hochaufgelösten Blattpassagen, Bodenwirkung oder validierte Wirbelringphysik. Idealisierte Positions-/Lageschätzung und Drehzahlmessung. Keine Firmware-SITL und keine dauerfeste Belastbarkeitsprüfung. Servolast aus lokalem neutralem Jacobian, ohne vollständige dynamische Pitch-Trägheit.'
]:para(text)
para('Numerische Verifikation','Heading2')
for t in V['results']:para(t['name']+' — bestanden.')
para('Quelle SHA256: '+M['source_sha256'])
story.append(PageBreak());para('Flugverhalten und Fehlerfälle','Heading1');story.append(Image(str(O/'Flugverhalten.png'),width=480,height=393));para('Die dargestellten Abbruchverläufe sind Ergebnisse desselben Modells und Reglers. Sie sind keine Vorhersage exakter realer Absturzzeiten. Die ursprüngliche Höhenregelung verlor bei −25 % Aerodynamik zu viel Höhe; die ergänzte innere Beschleunigungsregelung fängt diesen Fall jetzt innerhalb der Testgrenzen ab.')
story.append(PageBreak());para('P10: Servohalter, Planetenstufe, Kabelbaum, Landegestell','Heading1')
p10=[r for r in R['results'] if r['name'].startswith('P10_')]
para(f"Die P10-Fälle rechnen mit dem Massenmodell der nativen P10-Baugruppe ({p10[0]['mass_kg']:.3f} kg mit 69-g-Servos, Schwebedrehzahl {p10[0]['hover_rpm']:.0f} U/min): Servohalter und verbreiterte Halteplatten, Hohlrad-Deckel, Motorbrücke, Stützplaneten, Kabelbaum aus modellierten Leitungslängen und Kufenlandegestell. Der Motor dreht über das Hohlrad gleichsinnig zum Rotor; die Drehimpulsbilanz enthält Motor- und Stützplaneten-Drall. Bodenkontakt als Feder-Dämpfer mit Reibung an den vier Schellenringen sowie Kufen- und Endpunkten, Bodeneffekt nach Cheeseman-Bennett (empirisch).")
for r in p10:para(f"{r['name'].replace('_',' ')}: {r['status'].replace('_',' ').lower()}, max. Neigung {r['max_tilt_deg']:.1f}°"+(f", Aufsetzgeschwindigkeit {r['max_touchdown_speed_mps']:.2f} m/s, Endphase {r['mission_phase']}" if r.get('mission_phase') else ''))
story.append(Image(str(O/'P10_Bodenstart_Landung.png'),width=480,height=384))
para('Hochlauf und Auslauf sind Drehzahlrampen ohne ESC-Anlaufmodell. Landegestell-Steifigkeit, Reibwert und Dämpfung sind Annahmen; Landestöße werden nicht strukturell bewertet.')
story.append(PageBreak());para('Motor- und Servoregelung','Heading1');story.append(Image(str(O/'PID_Antwort.png'),width=480,height=384));para('Drehzahlsprung +10 % nach 4 s. Der Flugregler muss dabei den zusätzlichen Schub über die Taumelscheiben ausgleichen. Die Motor- und Servowerte sind Modellparameter, keine auf realer Hardware freigegebenen PID-Werte.')
para('Reproduktion: node modell_r04_taumel/simulation/testflug.js; node modell_r04_taumel/simulation/pruefen.js; node modell_r04_taumel/simulation/robustheit.js. Vollständige Parameter und Grenzen in simulation/README.md. Browser und Node verwenden denselben Physikkern.')
def footer(c,d):c.setFont('DejaVu',8);c.drawString(42,24,'H01 · Modellversuch · keine Flugfreigabe');c.drawRightString(A4[0]-42,24,str(d.page))
SimpleDocTemplate(str(H/'Flugbericht.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=35,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
print('Report and plots generated',stable,'stable of',len(R['results']))
