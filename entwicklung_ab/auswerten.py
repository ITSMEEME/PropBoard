"""A/B report, plots, requirement register and constrained motor-out allocation."""
from pathlib import Path
import json,math,csv,hashlib,html,zipfile,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/propboard-ab-mpl')
import numpy as np
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
H=Path(__file__).resolve().parent;cfg=json.loads((H/'parameter.json').read_text());aero=json.loads((H/'Leistungsbedarf.json').read_text());rows=aero['rows'];byid={r['id']:r for r in rows}
cad={c['id']:json.loads((H/'Ausgabe'/c['id']/'Pruefung.json').read_text()) for c in cfg['cases']}
geo={r['id']:r for r in json.loads((H/'Geometrie_Pruefung.json').read_text())}
selected=['P14_R750','P14_R800','QUAD_R380','HEXA_R265_B4']
def f(x,n=1):return f'{x:.{n}f}'.replace('.',',')
def csvout(name,data):
    keys=list(dict.fromkeys(k for r in data for k in r))
    with (H/name).open('w',newline='') as file:
        w=csv.DictWriter(file,keys);w.writeheader();w.writerows(data)
failures=[]
for e in json.loads((H/'Ausfall_Eingaben.json').read_text()):
    n=len(e['signs']);M=np.array([[1]*n,[p[0]/1000 for p in e['coords']],[p[1]/1000 for p in e['coords']],e['signs']],float)
    objective=np.r_[np.zeros(n),1];Aub=np.c_[np.eye(n),-np.ones(n)];Aeq=np.c_[M,np.zeros(4)]
    bnds=[(0,0) if i==e['failed_motor_index'] else (0,None) for i in range(n)]+[(0,None)]
    result=linprog(objective,A_ub=Aub,b_ub=np.zeros(n),A_eq=Aeq,b_eq=[1,0,0,0],bounds=bnds,method='highs')
    factor=result.x[-1]*n if result.success else None
    failures.append(dict(id=e['id'],failed_motor_index=e['failed_motor_index'],static_allocation_possible=bool(result.success),required_healthy_thrust_factor=factor,required_healthy_power_factor_similarity=factor**1.5 if factor else None,covered_by_30pct_power_reserve=bool(factor and factor<=1.3**(2/3)+1e-9),scope='Fixed vertical axes, equal torque/thrust ratio, ideal static force/moment allocation; no dynamics or real motor map'))
csvout('Motor_Ausfall_Screen.csv',failures)
spinup=[];requirements=[];battery=[]
for r in rows:
    I=geo[r['id']]['blade_polar_inertia_each_motor_kgm2'];w=r['rpm']*2*math.pi/60
    for t in [3,5,10]:
        extra=I*w/t;spinup.append(dict(id=r['id'],spinup_time_s_assumed=t,blade_inertia_each_kgm2=I,additional_blade_acceleration_torque_Nm=extra,hover_plus_acceleration_torque_Nm=r['torque_Nm']+extra,scope='constant acceleration at final hover-pitch drag; blades only, no ESC/current/thermal transient model'))
    md=r['mass_kg']-12;k=r['electric_kW']/r['mass_kg']**1.5
    for density in [180,220,300]:battery.append(dict(id=r['id'],pack_Whkg_assumed=density,nominal_12kg_hover_min=12*density/1000*.8/r['electric_kW']*60,ideal_similarity_max_hover_min=2*md*density/1000*.8/(k*(3*md)**1.5)*60,unconstrained_optimal_battery_kg=2*md))
    for comp,demand,evidence in [
        ('Motor',f'{f(r["rpm"],0)} /min; {f(r["torque_Nm"])} Nm; {f(r["minimum_shaft_rating_30pct_kW"])} kW Welle mit 30% Reserve; Verlustleistung etwa {f(r["electric_per_motor_kW"]-r["per_motor_shaft_kW"])} kW je Motor','MN1330: 46,25 Nm höchstes Prüfmoment; 3,4kW/180s, keine Dauerdaten; klassische Motoren nicht ausgewählt'),
        ('Rotor',f'{r["blades"]} Blätter; R={r["radius_mm"]}mm; {f(r["rpm"],0)} /min; Spitzen-Mach {f(r["tip_Mach"],3)}','P14-CAD bzw. symmetrische Profilnennhülle; kein vermessenes Rotorfeld, kein Laminat-/Fliehkraft-/Ermüdungsnachweis'),
        ('ESC',f'{f(r["per_motor_input_current_at_92V_A"])} A im Schwebepunkt bei 92V je Motor; 24S voll =100,8V nur bei 4,2V/Zelle; Transienten und Spannung unter Last gesondert','Für neue Motoren kein Regler gewählt; MN1330-M200A24S-Empfehlung ist keine Anwendungsfreigabe'),
        ('Batterie',f'{f(r["continuous_pack_current_at_92V_A"])} A gesamt; etwa {f(r["c_rate_at_92V"])} C bei 2,64kWh; rechnerisch {f(r["hover_minutes_energy_only"])}min','12kg und 220Wh/kg sind freie Packannahmen, kein ausgewähltes Pack und keine Hochstrom-/Temperaturprüfung')]:requirements.append(dict(id=r['id'],component=comp,required_operating_point=demand,evidence_available=evidence,verified=False))
csvout('Hochlauf_Screen.csv',spinup);csvout('Komponenten_Nachweismatrix.csv',requirements);csvout('Batterie_Rueckkopplung.csv',battery)
(H/'leistungsdaten.js').write_text('globalThis.AB_POWER='+json.dumps(rows,separators=(',',':'))+';\n')

# Technical plan drawings with the same centres and guard dimensions as native CAD.
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for cid in selected:
    c=cad[cid];R=c['case']['radius_mm'];fig,ax=plt.subplots(figsize=(8,7))
    ax.add_patch(Rectangle((-1050,-850),2100,1700,fill=False,edgecolor='#9c3940',linestyle='--',label='Zielhülle 2100×1700'))
    for i,(x,y) in enumerate(c['centres_mm']):
        ax.add_patch(Circle((x,y),R,fill=False,edgecolor='#147c9d',linewidth=1.3,label='Nomineller Rotor' if i==0 else None));ax.add_patch(Circle((x,y),R+37,fill=False,edgecolor='#b48631',linewidth=2,label='Schutzring außen' if i==0 else None));ax.scatter([x],[y],s=18,color='#485d6a')
        if c['case']['type']=='classic':ax.plot([0,x],[0,y],color='#8c9da8',linewidth=5,zorder=0)
    ax.add_patch(Rectangle((-310,-180),620,360,facecolor='#173e54',alpha=.35,label='Personendeck 620×360'))
    if c['case']['type']=='coax':
        for sign in [-1,1]:ax.add_patch(Rectangle((sign*450-150,-100),300,200,facecolor='#58855f',alpha=.5))
    ax.set(aspect='equal',xlim=(-1130,1130),ylim=(-950,950),xlabel='x [mm]',ylabel='y [mm]',title=cid+' · Draufsicht mit Schutzraum');ax.legend(loc='upper left',fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(H/(cid+'_Draufsicht.svg'));fig.savefig(H/(cid+'_Draufsicht.png'),dpi=160);plt.close(fig)

render=json.loads((H/'Renderdaten.json').read_text())
for item in render:
    cid=item['id'];fig=plt.figure(figsize=(10,6.6),facecolor='#f3f7f9');ax=fig.add_subplot(111,projection='3d');polys=[];col=[]
    for mesh in item['meshes']:
        v=np.asarray(mesh['vertices']);faces=np.asarray(mesh['faces']);tri=v[faces];polys.append(tri);col.extend([mesh['colour']]*len(tri))
    ax.add_collection3d(Poly3DCollection(np.concatenate(polys),facecolors=col,edgecolors='none',rasterized=True));r=item['report'];ax.set(xlim=(-1100,1100),ylim=(-950,950),zlim=(-340,360),xlabel='x [mm]',ylabel='y [mm]',zlabel='z [mm]');ax.set_box_aspect([2200,1900,700]);ax.view_init(27,-58);fig.suptitle(cid+' · Oberflächen aus der nativen CAD-Datei',fontsize=14)
    fig.text(.08,.045,'Feines Gitter für die Übersicht ausgeblendet · Bauteilmassen und Anschlussdetails teilweise angenommen',fontsize=8);fig.subplots_adjust(top=.91,bottom=.1);fig.savefig(H/(cid+'_CAD.png'),dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4.7));x=np.arange(len(selected));ax.bar(x,[byid[k]['electric_kW'] for k in selected],color=['#6699aa','#34758b','#b28f3d','#7b9b58']);ax.set_xticks(x,selected);ax.set(ylabel='Elektrischer Schwebebedarf [kW]',title='Neuberechnung mit CAD-erfassten Massen, 100 kg Nutzlast');ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(H/'Leistungsvergleich.png',dpi=160);plt.close(fig)

pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles=getSampleStyleSheet()
for k in ['Normal','BodyText','Title','Heading2']:styles[k].fontName='DVB' if k in ['Title','Heading2'] else 'DV'
styles['BodyText'].fontSize=8.5;styles['BodyText'].leading=12
story=[];md=[];ht=[]
def heading(t):story.extend([Spacer(1,.25*cm),Paragraph(html.escape(t),styles['Heading2'])]);md.append('\n## '+t+'\n');ht.append('<h2>'+html.escape(t)+'</h2>')
def p(t):story.extend([Paragraph(html.escape(t),styles['BodyText']),Spacer(1,.16*cm)]);md.append(t+'\n');ht.append('<p>'+html.escape(t)+'</p>')
def tab(headers,rs):
    raw=[headers]+[[str(x) for x in row] for row in rs];t=Table([[Paragraph(html.escape(x),styles['BodyText']) for x in row] for row in raw],colWidths=[17.2*cm/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf2')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,.2*cm)])
    md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rs)+'\n');ht.append('<table>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in raw)+'</table>')
def img(file,caption,h=8):
    from PIL import Image as PILImage
    wpx,hpx=PILImage.open(H/file).size;scale=min(17.2/wpx,h/hpx)
    story.append(Image(str(H/file),width=wpx*scale*cm,height=hpx*scale*cm));p(caption);md.append(f'![{caption}]({file})\n');ht.append(f'<img src="{file}" alt="{html.escape(caption)}">')
def page():story.append(PageBreak())
title='A/B-Entwicklung: P14-Vierblatt, Quadrokopter und Hexakopter'
story.append(Paragraph(title,styles['Title']));md.append('# '+title+'\n');ht.append('<h1>'+title+'</h1>')
p('Stand 2. November 2026. Folgestudie mit nativen FreeCAD-Rahmenentwürfen, Schutzgeometrie, Massenregister und neu berechneten Betriebspunkten. Die bestehende Antriebsstudie und die ursprüngliche P14-Konstruktion bleiben als Vergleich erhalten.')
heading('1. Ergebnis und Entscheidungen')
p('A ist mit vier Blättern bei 750 und 800 mm Radius als neue integrierte CAD-Variante umgesetzt. B besitzt neue Rahmen für den klassischen Quadrokopter und Hexakopter. Die früheren besten Radien 400/275 mm werden zusätzlich als Vergleichsentwürfe gebaut; mit dem angesetzten Schutzraum überschreiten sie die Zielbreite. Die weitergeführten Radien sind 380 mm beim Quadrokopter und 265 mm beim Hexakopter.')
p('Nach dem Schließen des erfassten Massenumfangs benötigt der 265-mm-Hexakopter mit drei Blättern eine zu hohe Spitzen-Machzahl für die gewählte Grenze 0,65. Eine zusätzliche Vierblattvariante hält diese Grenze ein. Die neuen Massen stammen aus CAD-Volumina für Rahmen und Schutz sowie dokumentierten beziehungsweise ausdrücklich angenommenen Kaufteil-/Blattmassen. Vollständig ausgelegte Verbindungsmittel, Kabel, thermische Hardware und Schutzrückhalt fehlen weiterhin.')
tab(['Variante','Blätter je Rotor','Erfasste Masse +100kg [kg]','Elektrisch Schweben [kW]','Hülle / Rotorraum / Aero'],[[k,str(byid[k]['blades']),f(byid[k]['mass_kg']),f(byid[k]['electric_kW']),' / '.join('ja' if v else 'nein' for v in [byid[k]['rotor_hull_fits'],byid[k]['rotor_clearance_screen_pass'],byid[k]['aerodynamic_screen_pass']])] for k in selected])
p('Unter diesen Annahmen hat der klassische Quadrokopter den niedrigsten Schwebebedarf. P14 bietet die größte kompakte Einzelscheibe, verlangt aber sehr hohe Motormomente und zusätzliche Außenstützen für Deck und Fahrwerk. Der Hexakopter benötigt mehr Leistung und höhere Drehzahl. Keine Variante ist durch die vorliegenden Herstellerdaten als dauerbetriebsfähig belegt; die Rangfolge ist eine bedingte Entwurfsbewertung.')
page();heading('2. Schutzraum verändert die Auslegung')
tab(['Variante','Radius [mm]','Komplette modellierte Hülle [mm]','Zielhülle eingehalten'],[[k,str(cad[k]['case']['radius_mm']),' × '.join(f(x,0) for x in cad[k]['bounds_mm']),'ja' if cad[k]['envelope_pass'] else 'nein'] for k in cad])
p('Ziel: 2100 × 1700 × 600 mm ohne Person. Die Schutzringe liegen radial von R+25 bis R+37 mm. Benachbarte Schutzringe besitzen 10 mm nominalen Abstand. Runde Distanzrohre, Drahtgitter, Lastpfade, Personendeck, Batteriebauräume und Kufen sind enthalten. Die zusätzliche Toleranzprüfung erweitert jede Außenkante um 3 mm. Ein positiver Hüllencheck umfasst die modellierten Teile; zusätzliche Serienhardware kann den verbleibenden Raum beanspruchen.')
tab(['Variante','Tatsächlicher neutraler Spitzenradius [mm]','Ring innen [mm]','Rest nach 15mm Verformung +3mm Toleranz [mm]'],[[k,f(cad[k]['tip_swept_radius_mm'],2),str(cad[k]['guard_inner_radius_mm']),f(cad[k]['radial_reserve_after_18mm_mm'],2)] for k in selected])
p('Die tatsächliche CAD-Blattkontur reicht seitlich über den nominellen Radius hinaus. Deshalb wird die Restluft nicht einfach aus R+25 minus R berechnet. Die angesetzten 15 mm Verformung sind eine freie Reserve, kein Elastizitätsnachweis. Die verbleibenden etwa 1–2 mm müssen nach einer wirklichen Blatt-/Rahmenverformungsrechnung neu beurteilt werden. Der axiale Hüllraum enthält Pitch bis 20°, Profildicke sowie dieselben 18 mm Reserve; eine vollständige aeroelastische Hülle ist damit nicht bewiesen.')
p('Das Drahtgitter besitzt 1,2 mm Nenndraht und 30 mm Teilung. Daraus folgt für eine ideale rechtwinklige Lage eine geometrische freie Fläche von etwa 92 %. Das ist kein aerodynamischer Wirkungsgrad. Gitterbefestigung, Durchgriff, elastische Auslenkung und Blattfragment-Rückhalt sind nicht nachgewiesen. Insbesondere ist das Gitter kein belegtes Containment.')
img('QUAD_R380_Draufsicht.png','Quadrokopter: Schutzringe und Deck im vorgegebenen Rechteck.',9)
page();heading('3. A – Lastpfad und Aufbau der P14-Varianten')
p('Die vier M8-Nennanschlüsse am vorhandenen A29-Zentralblock bleiben Bezug für das neue Decktragwerk. Vier 50×50×3-mm-CFK-Unterarme liegen im Zwischenraum der Rotoren bei z=-20 mm. Runde Außenpfosten umgehen die Rotorscheiben. Vier 40×40×2,5-mm-Oberträger tragen das 620×360×8-mm-Deck oberhalb des oberen Rotors. Metallische Adapter besitzen getrennte Massen; CFK wird nicht mit Aluminiumdichte vermischt.')
p('Landebeine bleiben außerhalb des erweiterten Rotorraums und werden erst unter dem unteren Rotor nach innen zu den Kufen geführt. Zwei symmetrische 6-kg-Batteriebauräume liegen bei x=±450 mm zwischen den Rotoren; dadurch entfällt eine Stütze durch einen geschlossenen Motor oder durch eine Rotorscheibe. Die Akkus und Querträger schatten den Nachlauf teilweise ab. Dieser neue Strömungseinfluss ist in der BEMT nicht enthalten und muss vermessen oder dreidimensional berechnet werden.')
p('Die größeren Unterarme wurden gegen die vorhandenen Servo-/Gestängebauteile positioniert. Geprüft werden sowohl der konservative Rotorringraum als auch die tatsächlichen geerbten CAD-Körper. Die Dateien stehen in einer neutralen mechanischen Pose; die berechnete Schwebetrimmung hat andere Kollektivstellungen innerhalb des P14-Stellbereichs. Eine neue bewegte Last-/Kontaktprüfung für alle Posen und elastischen Zustände bleibt offen.')
img('P14_R800_CAD.png','P14 R800: genaue native Oberflächen mit neuen Außenlastpfaden; feines Schutzgitter ausgeblendet.',8.5)
tab(['P14','CAD-Kern [kg]','Neue statische Teile [kg]','Akku / Elektronik [kg]'],[[k,f(cad[k]['mass_categories_kg']['P14_existing']),f(cad[k]['mass_categories_kg']['new_static']),'12 / 2'] for k in ['P14_R750','P14_R800']])
page();heading('4. B – neue klassische Rahmen')
p('Quadrokopter: vier getrennte Rotoren in X-Anordnung. Hexakopter: sechs Rotoren als regelmäßiger Ring mit wechselnden Drehrichtungen. Zentralrahmen und Ausleger verwenden CFK-Rohrnennquerschnitte 40×40×2,5 mm. Die Motorträger sind 170×170×8-mm-Aluplatten. Vier zentrale Stützen tragen das Personendeck über den Rotorebenen. Batterie und Elektronik sind als eigene Bauraum-/Massenanteile erfasst, das Kufenfahrwerk liegt darunter.')
p('Die Motorbauräume Ø150×66 mm und die 2,75-kg-Masse sind Platzhalter. PCD50 ist eine Anschlussannahme; es wird kein neuer Motor als passend behauptet. Die Naben besitzen geometrische Stege und formgleiche Blattwurzel-Nennsitze, deren Kräfte noch nicht durch Schrauben-, Klemm- oder Laminatnachweise freigegeben sind. Die aerodynamische Blattspannweite beginnt bei 90 mm Radius. Klassische Blätter stehen im CAD bei 14° festem Pitch.')
p('Die Rotorblätter werden als äußere Vollprofilhülle gezeigt. Für ihre Rechenmasse wird stattdessen eine geschätzte 2×1,2-mm-Schale plus Wurzel-/Sparbudget verwendet; sie sind keine massiv gefertigten CFK-Blätter. Die Aluminium-Nabenstege, Träger, Rohre und Schutzteile werden aus ihren tatsächlichen CAD-Volumina gewichtet. Dies wird in jeder Stücklistenposition separat ausgewiesen.')
tab(['Variante','Motoren [kg]','Rotoren/Naben [kg]','Rahmen/Schutz statisch [kg]','Akku/Elektronik [kg]'],[[k,f(cad[k]['mass_categories_kg']['motor']),f(cad[k]['mass_categories_kg']['rotor']),f(cad[k]['mass_categories_kg']['new_static']),'12 / 2'] for k in ['QUAD_R380','HEXA_R265_B4']])
img('HEXA_R265_B4_CAD.png','Hexakopter R265 mit vier Blättern je Rotor und neuem Rahmen.',8.5)
page();heading('5. Neue Betriebspunkte und Motorauslegung')
tab(['Variante','Drehzahl [1/min]','Welle je Motor [kW]','Moment je Motor [Nm]','Mind. Welle +30% [kW]'],[[k,f(byid[k]['rpm'],0),f(byid[k]['per_motor_shaft_kW']),f(byid[k]['torque_Nm']),f(byid[k]['minimum_shaft_rating_30pct_kW'])] for k in selected])
p('Berechnung: vorhandene stationäre Blattelement-Impuls-Theorie mit 32 radialen Elementen, Luftdichte 1,225 kg/m³, angenommener elektrischer Antriebswirkungsgrad 0,82. Koaxialfall mit oberem Nachlauf und Momenttrim des unteren Rotors. Klassische Rotoren werden ohne gegenseitige Strömungsinteraktion gerechnet. Die Geometrie-, Schutz- und Deckeinflüsse verändern die Masse, erzeugen aber in diesem Modell keinen zusätzlichen Strömungswiderstand. Die Daten sind deshalb optimistische Anforderungen für das integrierte Fahrzeug.')
p('30 % Wellenleistungsreserve ergeben unter idealer Ähnlichkeit lediglich rund 19 % Schubreserve. Für 30 % mehr Schub wären rund 48 % mehr Leistung nötig. In Lastpunkte.csv werden die Schubfaktoren 1,00 / 1,19 / 1,30 / 1,50 erneut mit BEMT gerechnet. Dabei werden Drehzahl, Moment, Leistung und Spitzen-Machzahl erfasst. Höhere Lastfälle sind keine erlaubten Betriebszustände.')
img('Leistungsvergleich.png','Vergleich mit dem neuen Massenregister; Nebenverluste der integrierten Schutz-/Deckgeometrie fehlen.',7.5)
heading('6. Warum MN1330 und eine Nennleistung allein nicht genügen')
p('Die vorhandenen MN1330-Daten belegen 2,75 kg Motormasse und eine Prüflinie mit NS52×20 bei etwa 92 V. 3400 W beziehen sich auf 180 s bei ungeklärter Leistungsseite. Höchste dokumentierte Werte: 46,25 Nm und 16,27 kW elektrische Aufnahme ohne Haltedauerangabe. Das ist kein Dauermoment- oder Dauerleistungskennfeld für diese Rotoren.')
p('P14 verlangt im neuen Betriebspunkt mehr Moment als das höchste dokumentierte Prüfmoment. Die klassischen Rotoren verlangen deutlich höhere Drehzahlen als die etwa 3680/min ideale Leerlaufreferenz von KV40 bei 92 V. Für B sind andere Motoren erforderlich. Ein rechnerisch passender kW-Wert ohne Drehzahl, Drehmoment, Masse und Kühlung ist keine Komponentenauswahl.')
page();heading('7. Strom, Regler, Batterie und Wärme')
tab(['Variante','Gesamtstrom bei 92V [A]','Je Motor bei 92V [A]','Elektrisch minus Welle/Motor [kW]','Energie-Schwebedauer [min]'],[[k,f(byid[k]['continuous_pack_current_at_92V_A'],0),f(byid[k]['per_motor_input_current_at_92V_A'],0),f(byid[k]['electric_per_motor_kW']-byid[k]['per_motor_shaft_kW']),f(byid[k]['hover_minutes_energy_only'])] for k in selected])
p('Die Differenz zwischen elektrischer Aufnahme und Wellenleistung ist ein Verlustleistungsbedarf des angenommenen Antriebsmodells. Ohne Aufteilung von Motor-/ESC-Verlusten, Kühlluft und Temperaturmessung kann daraus keine zulässige Dauerbelastung abgeleitet werden. Regler müssen die tatsächliche Zellzahl, volle Spannung, Einbrüche, Spitzenströme und die Motorinduktivität unterstützen. 92 V sind die Prüfreferenz; 24S mit 4,2 V/Zelle ergibt 100,8 V voll.')
p('Batterieannahme: 12 kg, 220 Wh/kg, 80 % nutzbar, 2,112 kWh nutzbare Energie. Die benötigte Stromabgabe liegt bei hohen C-Raten. Es ist nicht belegt, dass ein reales Pack gleichzeitig diese spezifische Energie und diesen Strom bei zulässiger Temperatur erreicht. Die CAD-Bauraumkästen sind keine vermessenen Serienakkus. Für P14 ist die Batterie außerdem geteilt; Verschaltung und Stromaufteilung fehlen.')
p('Die vollständige Komponenten-Nachweismatrix enthält für jede Variante die Anforderungen an Motor, Rotor, Regler und Akku sowie die verfügbaren Quellen. Alle vier Komponentenarten bleiben für das integrierte Fluggerät unbestätigt. Es werden keine Prüfmaxima in Dauerkennlinien umgedeutet.')
tab(['Variante','15min: Akku kg, Masse eingefroren','Max. min im günstigen Batterie-Ähnlichkeitsmodell'],[[k,f(byid[k]['electric_kW']*.25/(.220*.8)),f(next(b['ideal_similarity_max_hover_min'] for b in battery if b['id']==k and b['pack_Whkg_assumed']==220))] for k in selected])
p('Die 15-Minuten-Energieumrechnung unterschätzt den eigentlichen Bedarf: ein schwererer Akku verlangt mehr Leistung. Batterie_Rueckkopplung.csv verwendet P=k×m^(3/2) und untersucht 180/220/300 Wh/kg. Sein mathematisches Maximum bei mAkku=2×Trockenmasse ignoriert Motor-, Struktur- und Drehzahlgrenzen und ist keine mögliche Serienkonfiguration. Das Projektziel bleibt in diesen günstigen Rechenfällen deutlich verfehlt.')
page();heading('8. Lastpfad, Verformung und Hochlauf')
tab(['Variante / Balken','2g-Kraft [N]','Biegemoment [Nm]','Nennspannung [MPa]','Durchbiegung bei E=70GPa [mm]'],[[d['id']+' / '+d['member'],f(d['force_N'],0),f(d['root_moment_Nm']),f(d['nominal_bending_stress_MPa']),f(d['cantilever_deflection_mm'],2)] for d in aero['demand'] if d['id'] in selected and d['E_assumed_Pa']==70e9])
p('Der Lastscreen nutzt einfache, einseitig eingespannte homogene Balken bei 2g sowie E=70/110 GPa. Er berechnet Nachfragewerte aus den gewählten Querschnitten. Er enthält keine zulässigen Spannungen für das konkrete Laminat, keine Klemmnachgiebigkeit, Schubverformung, Torsion, Beulen, Ermüdung oder Schwingungsresonanzen. Die Unter-/Oberträger von P14 wurden gegenüber der ersten Rahmenannahme auf 50×50×3 beziehungsweise 40×40×2,5 mm vergrößert; der neue Leistungsbedarf enthält deren Masse.')
p('Auch eine kleine Balkendurchbiegung schließt das Tragwerk nicht ab. Die A29-Adapter, CFK-Rohrklemmen, Motorplatten, Deckauflagen, Kufenverbindungen und Blattwurzelanschlüsse benötigen eigene Schrauben-, Kontakt- und Laminatnachweise. Absichtliche geometrische Überlappungen an Rohrknoten sind Verbindungsplatzhalter und keine behaupteten lasttragenden CFK-Schweißnähte.')
tab(['Variante','Blatt-Trägheit/Motor [kgm²]','Zusatzmoment für 3s [Nm]','Schweben + Zusatz [Nm]'],[[s['id'],f(s['blade_inertia_each_kgm2'],3),f(s['additional_blade_acceleration_torque_Nm']),f(s['hover_plus_acceleration_torque_Nm'])] for s in spinup if s['id'] in selected and s['spinup_time_s_assumed']==3])
p('Der Hochlaufscreen benutzt die nativen Blade-Geometrien und deren Rechenmassen. Naben, Wellen, Klemmen und Motorrotoren fehlen in dieser Trägheit. Bei gleichmäßiger Beschleunigung gilt zusätzlich Q=I×omega/t. Die Tabelle addiert den Blattanteil zum Endpunkt-Schwebemoment. Sie ist keine dynamische ESC-/Thermikrechnung und beweist keinen realen 3-s-Hochlauf. 5- und 10-s-Fälle liegen in der CSV bei.')
page();heading('9. Motor-Ausfallprüfung: 30 % reichen nicht automatisch')
tab(['Variante','Statische Kraft-/Momentverteilung nach Ausfall','Erforderlicher Leistungsfaktor gesunder Motoren','Mit 30% Leistungsreserve?'],[[k,'möglich' if next(v for v in failures if v['id']==k)['static_allocation_possible'] else 'nicht möglich',f(next(v for v in failures if v['id']==k)['required_healthy_power_factor_similarity'],2) if next(v for v in failures if v['id']==k)['static_allocation_possible'] else '—','ja' if all(v['covered_by_30pct_power_reserve'] for v in failures if v['id']==k) else 'nein'] for k in selected])
p('Für jeden einzelnen Motorausfall wird eine lineare Optimierung der Schubverteilung gerechnet. Bedingungen: Gewicht ausgleichen, Roll-, Nick- und Giermoment null, nur positive Schübe, ausgefallener Antrieb null. Die Minimierung begrenzt den maximal nötigen Schub eines gesunden Motors. Gleiche Drehmoment-/Schubverhältnisse und starre vertikale Achsen sind Annahmen. Drehzahländerungen verändern dieses Verhältnis in Wirklichkeit; es gibt keine Flugregler- oder Transientensimulation.')
p('P14 mit nur einem verbleibenden Motor besitzt ohne zusätzliches Gegenmomentsystem keinen ausgeglichenen Gierbetrieb. Der konventionelle Quadrokopter löst die vier Gleichgewichtsbedingungen nach einem Ausfall ebenfalls nicht. Der Standardhexakopter kann im idealisierten statischen Modell trimmen, benötigt dabei deutlich mehr Leistung pro belastetem Motor als 30 % Reserve bereitstellen. Damit wird keinem Entwurf Ausfalltoleranz zugesichert.')
heading('10. Sensitivität und Rangfolge')
p('Die neue Sensitivität verwendet zusätzliche Systemmassen von 0/5/10/20 kg und Wirkungsgrade von 0,75/0,82/0,90. Je Massenzustand wird der Schwebepunkt neu berechnet. Zusätzliche aerodynamische Integrationsverluste werden als separate Faktoren +0/+10/+20 % auf die elektrische Leistung gezeigt; das sind Szenarien, keine gemessenen Gitterkennwerte.')
tab(['Variante','Nennbedarf [kW]','+10kg, eta0,82 [kW]','Nennmasse, +20% Integrationsverlust [kW]'],[[k,f(byid[k]['electric_kW']),f(next(v['electric_kW'] for v in aero['sens'] if v['id']==k and v['extra_mass_kg']==10 and v['motor_eta_assumed']==.82)),f(byid[k]['electric_kW']*1.2)] for k in selected])
p('Motor_Massenschluss.csv ersetzt die 2,75 kg durch hypothetische 10/15/20/25/30/40-kW-Motoren mit 1/3/6 kW/kg mechanischer spezifischer Leistung. Der neu berechnete Bedarf entscheidet erneut über die 30-%-Reserve. Diese Kennwerte sind angenommene Klassen, keine am Markt validierten Motoren. Zwischen P14 und Quad können unterschiedliche Integrationsverluste oder reale Motormassen die Rangfolge verschieben.')
page();heading('11. Prüfumfang und reproduzierbare Dateien')
tab(['Variante','Native Körperobjekte','STEP-Rahmenvolumen Abweichung [%]','Neue Teile im Rotorraum','Neue Teile gegen P14-Kern'],[[k,str(cad[k]['body_count']),f(geo[k]['relative_frame_step_volume_difference']*100,5),str(len(cad[k]['rotor_envelope_intersections'])),str(len(cad[k]['new_vs_inherited_static_intersections']))] for k in selected])
p('Alle nativen Körper werden unabhängig auf Gültigkeit geprüft. Die Rahmen-STEPs werden zurückgelesen, Solidzahl und Volumen mit dem Register verglichen. Bei P14 enthält die native Datei den vollständigen übernommenen Kern plus neue Rahmenanteile; der zusätzliche STEP exportiert nur den neuen Rahmen einschließlich Batterie-/Elektronikreserven. Die klassische STEP-Datei enthält alle modellierten Komponenten. Koaxiale und klassische BEMT-Betriebspunkte werden zusätzlich mit 64 Elementen verglichen.')
tab(['Variante','Leistungsänderung 32→64 Elemente [%]'],[[k,f(byid[k]['numerical_power_difference_32_64_fraction']*100,3)] for k in selected])
p('Numerische Übereinstimmung ist keine physikalische Validierung. Nicht geprüft sind neue 3D-CFD, Vorwärtsflug mit 80km/h, reale Regelung, Mensch-/Deckabschattung, Aeroelastik, Akustik, Stromspitzen, Motorkühlung, Batterietemperatur, Materialermüdung, Schutzrückhalt oder die vollständige Montage. Ein positiver Rotorraum-Screen ist kein Nachweis aller zulässigen Bewegungen und Lastfälle.')
heading('12. Nächste verbindliche Nachweisstufe')
p('Der konkrete reviewbare Stand sind vier weitergeführte native CAD-Entwürfe plus drei Vergleichsvarianten, vollständige Stücklisten für den modellierten Umfang und Betriebspunktanforderungen. Vor der endgültigen Rangfolge werden passende Dauermotoren mit Drehmoment-/Drehzahl-/Temperaturfeld, konkrete Regler, reale Rotorpolaren beziehungsweise Schub-/Momentmessungen und ein stromfähiger Batteriepack benötigt. Mit den vorhandenen MN1330-Prüfpunkten ist dieser Abschluss nicht möglich.')
p('Für A: zuerst A29-Anbindung, Außenlastpfad, Blattwurzel, CFK-Verformung und Nachlaufabschattung durch geteilte Akkus prüfen. Für B: konkrete Motor-/Nabenanschlüsse und Verbindungsdetails des neuen Rahmens ausarbeiten; den Hexakopter in der Vierblattvariante weiterführen. Für beide: vollständige Masse mit realen Kaufteilen schließen und anschließend BEMT/Messabgleich und Antriebs-/Temperaturtests wiederholen. Fertigungs- und Flugfreigaben bleiben offen.')
p('Die interaktive Modelle.html zeigt ausgewählte tatsächliche CAD-Netze. Sie ist ein Geometrieviewer, kein neuer Flugsimulator. Die neutralen P14-Rotoren werden dort nicht animiert. SVG-Draufsichten, CAD-Ansichten, CSV/JSON, native FCStd, Rahmen-STEP, Quellen und ein SHA256-Manifest liegen separat bei. Bestehende P14-Dateien und die erste Studie wurden nicht überschrieben.')
(H/'Entwicklungsbericht.md').write_text('\n'.join(md));(H/'Entwicklungsbericht.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>'+title+'</title><style>body{font:16px/1.55 system-ui;max-width:1050px;margin:30px auto;padding:20px;color:#17384c}table{border-collapse:collapse;width:100%;font-size:14px}td{border:1px solid #bdcbd3;padding:7px}tr:first-child{background:#dcebf2}img{max-width:100%}</style>'+''.join(ht)+'</html>')
def foot(c,d):c.setFont('DV',8);c.drawString(1.8*cm,1.1*cm,'PropBoard | A/B-Entwicklung | 02.11.2026');c.drawRightString(19.2*cm,1.1*cm,str(d.page))
SimpleDocTemplate(str(H/'Entwicklungsbericht.pdf'),pagesize=(21*cm,29.7*cm),leftMargin=1.8*cm,rightMargin=1.8*cm,topMargin=1.6*cm,bottomMargin=1.7*cm,title=title).build(story,onFirstPage=foot,onLaterPages=foot)
(H/'Motor_Ausfall_Screen.json').write_text(json.dumps(failures,indent=2));print('A/B report and requirement registers generated')
