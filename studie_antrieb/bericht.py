"""Build reproducible German report, figures, PDF, HTML and sensitivity data."""
from pathlib import Path
import json, math, csv, hashlib, zipfile, html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

H=Path(__file__).resolve().parent
data=json.loads((H/'Ergebnisse.json').read_text()); pairs=data['rows']
single=json.loads((H/'Einzelrotoren.json').read_text())['rows']
compact=json.loads((H/'Kompakt.json').read_text())['rows']
mixed=json.loads((H/'Mischanordnungen.json').read_text())['rows']
valid=lambda rows:[r for r in rows if r['found']]
best=lambda rows:min(valid(rows),key=lambda r:r['electric_kW']) if valid(rows) else None
classic={n:best([r for r in compact if r['motors']==n and r['rotor_envelope_fits'] and r['layout']=='classic_ring']) for n in [4,6,8,10]}
grid={n:best([r for r in compact if r['motors']==n and r['rotor_envelope_fits'] and r['layout']=='rectangular_grid']) for n in range(1,11)}
pb=best([r for r in pairs if r['rotor_envelope_fits']]); reference=next(r for r in pairs if r['units']==1 and r['blades']==8 and r['radius_mm']==710)
selected=[('P14 koaxial, optimiert',pb)]+[(f'{n} Motoren, klassischer Ring',r) for n,r in classic.items() if r]
def name(n):return {1:'Einrotor',2:'Bicopter',3:'Tricopter',4:'Quadrokopter',6:'Hexakopter',8:'Oktokopter',10:'Dekakopter'}.get(n,f'{n}-Motor-Konzept')
def fmt(x,d=1):return f'{x:.{d}f}'.replace('.',',')
def export(name,rs):
    keys=list(dict.fromkeys(k for r in rs for k in r))
    with (H/name).open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rs)

# Seeded uncertainty propagation: assumptions, not fitted probability distributions.
rng=np.random.default_rng(20261102); trials=10000
mass_added=rng.uniform(0,20,trials); motor_eta=rng.uniform(.75,.9,trials); aero_factor=rng.uniform(.85,1.25,trials)
sens=[]; battery=[]; motor_mass=[]
for label,r in selected:
    p=r['electric_kW']*((r['mass_kg']+mass_added)/r['mass_kg'])**1.5*.82/motor_eta*aero_factor
    sens.append(dict(concept=label,nominal_kW=r['electric_kW'],scenario_p05_kW=float(np.quantile(p,.05)),scenario_median_kW=float(np.median(p)),scenario_p95_kW=float(np.quantile(p,.95)),samples=trials))
    md=r['mass_kg']-12;k=r['electric_kW']/r['mass_kg']**1.5
    for density in [180,220,300]:
        mb=2*md;tmax=(mb*density/1000*.8)/(k*(md+mb)**1.5)*60
        battery.append(dict(concept=label,Wh_per_kg_assumed=density,dry_with_payload_kg=md,optimal_battery_kg_similarity=mb,max_hover_minutes_similarity=tmax,nominal_12kg_hover_minutes=12*density/1000*.8/r['electric_kW']*60))
    for kw in [10,20,30,40,60]:
        for sp in [1,3,6]:
            m=r['mass_kg']+r['motors']*(kw/sp-2.75);scale=(m/r['mass_kg'])**1.5
            per=r['per_motor_shaft_kW']*scale
            motor_mass.append(dict(concept=label,rated_shaft_kW=kw,specific_shaft_power_kWkg_assumed=sp,motor_mass_each_kg=kw/sp,revised_mass_kg=m,revised_electric_kW=r['electric_kW']*scale,required_with_30pct_shaft_kW=per*1.3,reserve_covered=kw>=1.3*per))
export('Unsicherheit.csv',sens);export('Batterie_Rueckkopplung.csv',battery);export('Motormassen_Sensitivitaet.csv',motor_mass)
export('Mischanordnungen.csv',mixed)
# Full rating screen on redesigned classical configurations.
ratings=[]
for r in valid(compact):
    for kw in [3.4,10,20,30,40,60]:
        ratings.append({**r,'rated_shaft_kW_assumed':kw,'hover_power_covered':kw>=r['per_motor_shaft_kW'],'reserve_30pct_covered':kw>=1.3*r['per_motor_shaft_kW'],'power_only_thrust_weight_estimate':(kw/r['per_motor_shaft_kW'])**(2/3)})
export('Kompakt_Motorkombinationen.csv',ratings)

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(10,5))
for layout,label in [('classic_ring','Klassischer Ring'),('rectangular_grid','Rechteckraster')]:
    vals=[best([r for r in compact if r['motors']==n and r['rotor_envelope_fits'] and r['layout']==layout]) for n in range(1,11)]
    ax.plot(range(1,11),[r['electric_kW'] if r else np.nan for r in vals],marker='o',label=label)
ax.scatter([2],[pb['electric_kW']],marker='*',s=170,label='P14-Koaxialpaar')
ax.set(xlabel='Motoranzahl',ylabel='Elektrischer Schwebebedarf [kW]',title='Beste untersuchte Variante je Motoranzahl innerhalb Rotor-Bauraum')
ax.set_xticks(range(1,11));ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(H/'Motoranzahl.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4.5))
for b in [4,6,8,10,12]:
    rr=[r for r in pairs if r['units']==1 and r['blades']==b]
    axes[0].plot([r['radius_mm'] for r in rr],[r['electric_kW'] for r in rr],marker='o',label=f'{b} Blätter')
axes[0].set(xlabel='Rotorradius [mm]',ylabel='Elektrische Leistung [kW]',title='P14: Blattzahl und Radius');axes[0].legend(fontsize=8)
for n in [4,6,8,10]:
    rr=[r for r in compact if r['motors']==n and r['blades']==4 and r['layout']=='classic_ring' and r['found']]
    axes[1].plot([r['radius_mm'] for r in rr],[r['electric_kW'] for r in rr],marker='.',label=f'{n} Motoren')
axes[1].set(xlabel='Rotorradius [mm]',ylabel='Elektrische Leistung [kW]',title='Klassische Ringanordnung, 4 Blätter');axes[1].legend(fontsize=8)
for ax in axes:ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(H/'Blattzahl_Radius.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));labels=[s['concept'] for s in sens];nom=[s['nominal_kW'] for s in sens]
ax.barh(labels,nom,color='#347a9c',alpha=.65);ax.errorbar([s['scenario_median_kW'] for s in sens],range(len(sens)),xerr=np.array([[s['scenario_median_kW']-s['scenario_p05_kW'] for s in sens],[s['scenario_p95_kW']-s['scenario_median_kW'] for s in sens]]),fmt='ko',label='Szenario: Median und 5–95 %')
ax.set(xlabel='Elektrischer Schwebebedarf [kW]',title='10.000 angenommene Unsicherheitsszenarien je Konzept');ax.legend();fig.tight_layout();fig.savefig(H/'Unsicherheit.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5))
for label,r in selected:
    md=r['mass_kg']-12;mb=np.linspace(1,400,300);k=r['electric_kW']/r['mass_kg']**1.5
    t=mb*.220*.8/(k*(md+mb)**1.5)*60;ax.plot(mb,t,label=label)
ax.axhline(15,color='red',linestyle='--',label='Ziel: 15 Minuten');ax.set(xlabel='Batteriemasse [kg]',ylabel='Schwebedauer [min]',title='Batterie-Massenrückkopplung, 220 Wh/kg, 80 % nutzbar');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(H/'Batterie.png',dpi=160);plt.close(fig)

pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=13
for key in ['Normal','BodyText','Title','Heading2']:styles[key].fontName='DejaVu-Bold' if key in ['Title','Heading2'] else 'DejaVu'
story=[];md=[];ht=[]
def title(t):
    story.append(Paragraph(html.escape(t),styles['Title']));md.append('# '+t+'\n');ht.append('<h1>'+html.escape(t)+'</h1>')
def heading(t):
    story.append(Spacer(1,.3*cm));story.append(Paragraph(html.escape(t),styles['Heading2']));md.append('\n## '+t+'\n');ht.append('<h2>'+html.escape(t)+'</h2>')
def para(t):
    story.append(Paragraph(html.escape(t),styles['BodyText']));story.append(Spacer(1,.13*cm));md.append(t+'\n');ht.append('<p>'+html.escape(t)+'</p>')
def table(headers,rows):
    raw=[headers]+[[str(x) for x in r] for r in rows]
    widths=[17*cm/len(headers)]*len(headers)
    t=Table([[Paragraph(html.escape(x),styles['BodyText']) for x in r] for r in raw],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d9e9f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,.2*cm))
    md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
    ht.append('<table>'+''.join('<tr>'+''.join(('<th>' if i==0 else '<td>')+html.escape(x)+('</th>' if i==0 else '</td>') for x in r)+'</tr>' for i,r in enumerate(raw))+'</table>')
def figure(file,caption):
    story.append(Image(str(H/file),width=17*cm,height=8.5*cm));para(caption);md.append(f'![{caption}]({file})\n');ht.append(f'<img src="{file}" alt="{html.escape(caption)}">')
def page():story.append(PageBreak())

title('PropBoard: Vergleich von 1 bis 10 Motoren und Rotorvarianten')
para('Ausführliche parametrische Vorstudie auf Basis P14. Stand: 2. November 2026. Schwerpunkt: stationärer Schwebeflug mit 100 kg Nutzlast; klassische Multicopter, koaxiale Rotorpaare und Mischanordnungen.')
heading('1. Ergebnis und Entscheidung')
quad=classic[4];hexa=classic[6];octo=classic[8];deca=classic[10]
para('Ein universell bestes System lässt sich aus Motoranzahl und Nennleistung allein nicht bestimmen. Größere wirksame Rotorfläche senkt den induzierten Leistungsbedarf, zusätzliche Motoren und Mechanik erhöhen die Masse. Im festen Bauraum entscheidet deren Zusammenspiel. Die Ergebnisse unten gelten für die geprüften Geometrien, die angenommenen Massen und die vereinfachte Aerodynamik; sie sind keine globalen Optima.')
para(f'Das effizienteste untersuchte P14-Koaxialpaar benötigt rechnerisch {fmt(pb["electric_kW"])} kW elektrisch: zwei Motoren, je vier Blätter, {fmt(pb["radius_mm"],0)} mm Radius. Pro Motor ergeben sich {fmt(pb["per_motor_shaft_kW"])} kW Wellenleistung und {fmt(pb["torque_Nm"])} Nm im Schwebepunkt. Mit 30 % Leistungsreserve wären mindestens {fmt(pb["minimum_motor_shaft_kW_30pct"])} kW mechanische Dauerleistung je Motor erforderlich, sofern Drehmoment und Kühlung dies zulassen.')
if quad:para(f'Der beste untersuchte klassische Quadrokopter innerhalb der reinen Rotorhülle liegt bei {fmt(quad["electric_kW"])} kW elektrisch, {quad["blades"]} Blättern und {fmt(quad["radius_mm"],0)} mm Rotorradius. Seine Rahmenmasse ist geschätzt; deshalb ist die Rangfolge gegenüber dem CAD-näheren P14-Konzept vorläufig.')
para('Für eine Weiterentwicklung sind ein großes, niedrig belastetes Rotorsystem und ein klassischer Quad-/Hexakopter als konkurrierende Konzepte sinnvoll. Oktokopter und Dekakopter werden wegen zusätzlicher Regelmöglichkeiten mitgeführt; ein Nachweis von Motor-Ausfalltoleranz folgt aus der Motoranzahl nicht. Die geforderten 15 Minuten werden mit der angenommenen 12-kg-Batterie von keiner der empfohlenen Varianten erreicht.')
page();heading('2. Verbindliche Ausgangsdaten und Abgrenzung')
table(['Größe','Projektbasis / Interpretation'],[['Nutzlast','100 kg; Person plus zusätzliche Ausrüstung noch offen'],['Fahrzeugziel','2100 × 1700 × 600 mm einschließlich Rotoren und Schutz'],['Flugdauer / Geschwindigkeit','15 min / etwa 80 km/h; hier nur stationärer Schwebeflug'],['P14-Geometrie','710 mm Radius, 120 mm Tiefe, 360 mm Rotorabstand, 8 Blätter je Rotor'],['P14-CAD-Masse','60,56 kg pro 8-Blatt-Rotorpaar; kein vollständiges Fahrzeug'],['Batterie / Elektronik','12 kg / 2 kg als bisherige Annahmen'],['Motorreferenz','MN1330 KV40; 2,75 kg je Motor; etwa 92 V'],['Elektrischer Wirkungsgrad','0,82 als Annahme; Nebenverbraucher nicht enthalten'],['Atmosphäre','Dichte 1,225 kg/m³; Schallgeschwindigkeit 340 m/s']])
para('Aktuellster Bezug ist P14 laut Projekt-README. P11 und frühere kleine Modelle werden nicht mit P14 vermischt. Die alten sechs Rotorpositionen aus historischen Entwürfen sind keine verbindliche neue Motoranzahl. Die Nutzeranforderung 1–10 Motoren ersetzt diese Einschränkung für die Vergleichsstudie.')
para('Die Bauraumprüfung umfasst Rotorhüllen in der Ebene und 80 mm angenommene Abstände zwischen benachbarten Scheiben. Schutz, Personendeck, Landegestell, Kabel, Strukturverformung und Fertigungsspiel sind nicht vollständig enthalten. Ein positiver Hüllencheck ist daher kein Nachweis der vollständigen Fahrzeugabmessungen. Für P14 bleibt die bekannte 360-mm-Ebenentrennung erhalten; neue klassische Rahmen besitzen noch keine ausgearbeitete Höhenkonstruktion.')
para('Blattlänge bedeutet hier die freie aerodynamische Spannweite ab dem inneren Profilbeginn. Rotorradius ist der Abstand zwischen Drehachse und Spitze. Der Durchmesser beträgt das Doppelte des Radius. Diese Größen sind wegen Nabe und Blattanschluss ausdrücklich unterschiedlich.')
heading('3. Untersuchte Architekturen')
table(['Architektur','Motorzahlen','Umfang'],[['P14-Koaxialpaare','2, 4, 6, 8, 10','1–5 Paare; je 4/6/8/10/12 Blätter; Radius 650/710/750/800 mm'],['Große getrennte Rotoren','1–10','P14-nahe Blattgeometrie, gleiche Radien und Blattzahlen'],['Klassische Multicopter','1–10','Getrennte Rotoren, Ring und Raster; 2/3/4/6/8/10/12 Blätter; 15 Radien zwischen 150 und 800 mm'],['Mischsysteme','3–10','Je mögliche Mischung aus Paaren und Einzelrotoren; 8 Blätter; Radius 710/800 mm']])
para('Klassischer Quadrokopter: vier getrennte Rotoren, einschließlich einer X-Anordnung als gedrehter regelmäßiger Viererring. Hexa-, Okto- und Dekakopter: regelmäßige Ringe mit sechs, acht beziehungsweise zehn Motoren. Zusätzlich werden Rechteckraster betrachtet. Ring und Raster besitzen im isolierten Schwebemodell gleiche Aerodynamik, unterscheiden sich aber in der Hülle. Interaktionen benachbarter Einzelrotoren sind nicht modelliert.')
para('Ein Motor ohne Heckrotor beziehungsweise anderes Gegenmomentsystem ist nur ein aerodynamischer Rechenfall. Bicopter benötigen geeignete Schwenk-/Pitchmechanik; Tricopter und andere ungerade Anzahlen benötigen einen gesonderten Gierausgleich. Gleiche Lasten bei ungerader Anzahl gegenläufiger identischer Rotoren liefern kein ausgeglichenes Giermoment. Diese Fälle werden nicht als fertig regelbare Fluggeräte empfohlen.')
page();heading('4. Physikalisches Modell und Rechenverfahren')
para('Verwendet wird die vorhandene Blattelement-Impuls-Theorie aus kreis_r04/simulation/r04_physik.js. Sie berechnet Profilkräfte und induzierte Geschwindigkeiten über radiale Elemente. Die Polaren sind vereinfachte symmetrische NACA-artige Ersatzpolaren mit Reynolds- und Abrissabhängigkeit, keine vermessenen P14-Profile.')
para('Für Koaxialpaare liegt der untere Rotor im kontrahierten Nachlauf des oberen. Seine Pitchstellung wird innerhalb des vorhandenen P14-Gestängestellbereichs auf annähernd gleiche Gegenmomente getrimmt. Die Rückwirkung des unteren Rotors auf den oberen, instationäre Blattbegegnungen und komplexe 3D-Nachläufe fehlen. Ein Einzelrotor nutzt ausschließlich das obere, ungestörte Rotormodell; der rechnerisch mitberechnete untere Rotor wird verworfen.')
para('Je Geometrie werden obere Pitchwerte von 10°, 12° und 14° geprüft. Die Drehzahl wird iterativ so angepasst, dass Gesamtschub und Gewicht übereinstimmen. Unter den zulässigen Pitchfällen wird der niedrigste elektrische Leistungsbedarf gewählt. Bei Mischanordnungen tragen alle seitlich getrennten Rotorpositionen denselben Anteil der Gesamtlast; diese Lastverteilung ist eine Annahme und keine globale Optimierung.')
table(['Beziehung','Bedeutung'],[['T = m × g','Erforderlicher Schwebeschub'],['Pideal = T^(3/2) / sqrt(2 × rho × A)','Idealer induzierter Leistungsbedarf'],['Pelektrisch = PWelle / 0,82','Angenommene Motorumwandlung'],['Q = PWelle / omega','Erforderliches Motordrehmoment'],['t = mAkku × e × 0,8 / Pelektrisch','Energiebasierte Schwebedauer'],['PNenn >= 1,3 × PSchweben','Gewählte 30-%-Reserve in Leistung, keine Ausfallfreigabe']])
para('Zulässigkeitsfilter: Blattspitzen-Machzahl höchstens 0,65; maximal 10 % abgerissene radiale Spannweite; maximal 0,5 % Schubabweichung. Für Koaxialpaare zusätzlich weniger als 0,1 % Momentabweichung. Die Grenzen sind Screeningschwellen, keine validierten Betriebsgrenzen. Die Machgrenze ersetzt insbesondere kein kompressibles Profilmodell.')
para('Die Koaxialfläche wird als eine gemeinsame Ringfläche gezählt. Zwei übereinanderliegende Rotoren besitzen nicht die doppelte unabhängige Scheibenfläche. Seitlich getrennte Rotoren erschließen mehr Fläche, benötigen aber mehr Platz. Daher werden geometriefreie und bauraumbegrenzte Vergleiche getrennt ausgewiesen.')
heading('5. Massemodelle: belastbare Anker und freie Annahmen')
table(['Blätter pro Rotor','P14-CAD-Masse pro Paar [kg]'],[[str(n),fmt(json.loads((H.parent/'kreis_r04/mn1330_p14/Ausgabe/Massenvarianten.json').read_text())['cases'][str(n)]['mass_kg'],2)] for n in [4,6,8,10,12]])
para('Nur diese Massen bei 710 mm Referenzradius stammen aus vorhandenen CAD-Varianten. Radiusänderungen erhalten eine grobe lineare Korrektur der CFK-Masse: Paarmasse = CAD-Masse + 8,84 kg × (Blattzahl/8) × (freie Spannweite / Referenzspannweite - 1). Neue Naben-, Lager- und Strukturmassen werden damit nicht nachgewiesen. Mehrere Rotorpaare benötigen außerdem einen Verbindungsrahmen, dessen Masse fehlt.')
para('Getrennte große Rotoren übernehmen als Näherung die halbe Paarmasse je Modul. Für kompakte Neuentwürfe gilt die ausdrücklich freie Skalierung mModul = 2,75 kg + (45,13/2 - 2,75) kg × (R/0,71 m)² × (0,65 + 0,35 × B/4). Sie beinhaltet eine angenommene Struktur-/Antriebsreserve, aber keinen neu konstruierten Rahmen. Die Motormasse bleibt dabei zunächst bei 2,75 kg. Dadurch sind Vergleiche mit höheren Motorleistungen nur Anforderungsstudien. Eine separate Motormassen-Sensitivität korrigiert diesen Effekt näherungsweise.')
para('Die kompakten Rotoren erhalten eine angenommene Blatttiefe c = max(0,06 m; 0,12 m × sqrt(R/0,71 m)) und einen inneren Profilradius r0 = max(0,09 m; 1,05 × B × c / (2 pi)). Die freie Spannweite muss mindestens 100 mm betragen. Diese Geometrie ist ein Neuentwurf, keine verkleinerte, fertig passende P14-Mechanik. Mehrblättrige Varianten verlieren durch größere Wurzelradien aktive Spannweite.')
page();heading('6. Vergleich der klassischen Quad-, Hexa-, Okto- und Dekakopter')
table(['Konzept','Blätter / Radius [mm]','Masse [kg]','Elektrisch [kW]','min. Welle je Motor +30 % [kW]'],[[name(n),f'{r["blades"]} / {fmt(r["radius_mm"],0)}',fmt(r['mass_kg']),fmt(r['electric_kW']),fmt(r['minimum_motor_shaft_kW_30pct'])] if r else [name(n),'kein zulässiger Fall','—','—','—'] for n,r in classic.items()])
table(['Konzept','Freie Blattlänge [mm]','Drehzahl [1/min]','Moment je Motor [Nm]','Rotorhülle [m]'],[[name(n),fmt(r['free_blade_length_mm'],0),fmt(r['rpm'],0),fmt(r['torque_Nm']),f'{fmt(r["envelope_x_m"],2)} × {fmt(r["envelope_y_m"],2)}'] if r else [name(n),'—','—','—','—'] for n,r in classic.items()])
para('Diese Tabelle enthält jeweils den besten zulässigen untersuchten regelmäßigen Ring innerhalb der Rotorhülle. Die Auswahl wird nicht mit dem besten Raster verwechselt. Kleine Rotoren verlangen hohe Drehzahlen und geeignete andere Motoren. MN1330 KV40 liefert bei 92 V eine ideale Leerlaufreferenz von etwa 3680/min; deutlich höhere erforderliche Drehzahlen sind mit dieser Spannungs-/KV-Kombination nicht abgedeckt. Die Tabellenwerte wählen daher keinen konkreten Kaufmotor aus.')
para('Beim klassischen Dekakopter liefert das geprüfte Feld keinen Fall, der gleichzeitig Rotorhülle, Machgrenze, Mindestspannweite und Schwebelast erfüllt. Das ist eine Grenze dieses Parameterfeldes und kein allgemeiner Unmöglichkeitsbeweis für Dekakopter. Ein zehnmotoriges Rechteckraster besitzt dagegen zulässige Rechenfälle; die folgende Übersicht trennt diese Anordnungen.')
para('Ein Quadrokopter bietet geringe Motor- und Regleranzahl sowie einfache Grundarchitektur. Hexa-, Okto- und Dekakopter verteilen die Leistung auf mehr Motoren, verlangen aber mehr Anschlüsse, Tragstruktur und Fehlerbehandlung. Im engen Bauraum sinkt der maximal mögliche Rotordurchmesser bei klassischen Ringen mit zunehmender Motoranzahl. Die geringere Leistung je Motor ist deshalb nicht gleichbedeutend mit geringerem Gesamtenergiebedarf.')
figure('Motoranzahl.png','Vergleich der jeweils besten bauraumkompatiblen Varianten. Ungerade Zahlen sind aerodynamische Fälle ohne nachgewiesenen Giertrim.')
heading('7. Vollständiger Überblick über 1–10 Motoren')
table(['Motoren','Bezeichnung','Bestes Raster: B / R [mm]','Elektrisch [kW]','Bewertung'],[[str(n),name(n),f'{r["blades"]} / {fmt(r["radius_mm"],0)}' if r else 'kein zulässiger Fall',fmt(r['electric_kW']) if r else '—','Gierausgleich offen' if n%2 else ('Schwenk-/Pitchkonzept nötig' if n==2 else 'Regelung nicht nachgewiesen')] for n,r in grid.items()])
para('Die Rastertabelle beantwortet die vollständige Motoranzahlfrage. Sie dient zum Vergleich innerhalb des festen Rechtecks, auch wenn eine Anordnung beispielsweise acht Rotoren auf einem teilweise besetzten 3×3-Raster verteilt. Schwerpunkt, unbesetzte Positionen und Momente sind dort noch nicht konstruktiv optimiert. Der Ringvergleich ist für klassische Multicopter die aussagekräftigere Referenz.')
page();heading('8. P14, getrennte Großrotoren und Mischanordnungen')
table(['P14-Variante','B / Radius [mm]','Elektrisch [kW]','Welle/Motor [kW]','Moment [Nm]'],[['Standardgeometrie, Pitch optimiert',f'8 / 710',fmt(reference['electric_kW']),fmt(reference['per_motor_shaft_kW']),fmt(reference['torque_Nm'])],['Beste untersuchte P14-Variante',f'{pb["blades"]} / {fmt(pb["radius_mm"],0)}',fmt(pb['electric_kW']),fmt(pb['per_motor_shaft_kW']),fmt(pb['torque_Nm'])]])
para('Mehr Rotorblätter reduzieren bei gleicher Geometrie und Last häufig die notwendige Drehzahl. Gleichzeitig erhöhen sie Profilwiderstand, bewegte Masse und Anforderungen an Nabe und Pitchmechanik. Deshalb gewinnt im geprüften P14-Feld eine kleinere Blattzahl. Daraus folgt keine allgemeine Zwei- oder Vierblattregel für alle Profilformen und Lastfälle.')
same=next(r for r in single if r['motors']==pb['motors'] and r['blades']==pb['blades'] and r['radius_mm']==pb['radius_mm'])
para(f'Bei gleicher angenommener Masse und Blattgeometrie benötigen zwei getrennte große Rotoren {fmt(same["electric_kW"])} kW statt {fmt(pb["electric_kW"])} kW im Koaxialpaar. Das sind {fmt((1-same["electric_kW"]/pb["electric_kW"])*100)} % weniger elektrischer Bedarf in diesem Modell. Die Rotorhülle wächst jedoch auf {fmt(same["envelope_x_m"],2)} × {fmt(same["envelope_y_m"],2)} m und überschreitet das Projektziel. Dieser Vergleich zeigt den Flächen-/Bauraumkonflikt, nicht einen allgemeingültigen Koaxialverlust.')
table(['Motoren','Günstigste reine Paaranordnung: B / R','Elektrisch [kW]','Rotorhülle passt?'],[[str(n),f'{r["blades"]} / {fmt(r["radius_mm"],0)}',fmt(r['electric_kW']),'ja' if r['rotor_envelope_fits'] else 'nein'] for n in [2,4,6,8,10] for r in [best([x for x in pairs if x['motors']==n])]])
para('Die Mischstudie enthält beispielsweise 4 Motoren als 1 Paar + 2 Einzelrotoren, 6 Motoren als 1 Paar + 4 Einzelrotoren oder 2 Paare + 2 Einzelrotoren. Alle Kombinationen mit mindestens einem Paar und einem Einzelrotor bis 10 Motoren werden für 710 und 800 mm Radius berechnet. Wegen mindestens zwei getrennten großen Rotorpositionen passen diese untersuchten Mischsysteme nicht in den Bauraum. Kompakte Mischrotoren, unterschiedliche Radien oder unterschiedliche Pitchwerte je Einzelposition bleiben ein weiterer Optimierungsschritt.')
table(['Motoren','Bester Mischfall: Paare + Einzel','Elektrisch [kW]','Rotorpositionen'],[[str(n),f'{r["pairs"]} + {r["singles"]}',fmt(r['electric_kW']),str(r['sites'])] for n in range(3,11) for r in [best([x for x in mixed if x['motors']==n])] if r])
figure('Blattzahl_Radius.png','Radius- und Blattzahleinfluss; rechte Kurven enthalten auch Fälle außerhalb des Zielbauraums.')
page();heading('9. Nennleistung, Drehmoment und Leistungsfähigkeit')
para('Untersuchte hypothetische Motor-Nennleistungen: 3,4 / 10 / 20 / 30 / 40 / 60 kW mechanische Wellenleistung je Motor. Die 3,4-kW-Klasse ist ausschließlich eine hypothetische Vergleichsklasse. Sie darf nicht mit der realen MN1330-Angabe 3400 W für 180 s bei unklarer Leistungsseite gleichgesetzt werden. Dauerleistung, elektrische Aufnahme und kurzzeitige Prüfmaxima sind unterschiedliche Größen.')
table(['Konzept','Schweben/Motor [kW Welle]','mit 30 % [kW]','Kleinste geprüfte Klasse [kW]'],[[label,fmt(r['per_motor_shaft_kW']),fmt(1.3*r['per_motor_shaft_kW']),str(next((k for k in [3.4,10,20,30,40,60] if k>=1.3*r['per_motor_shaft_kW']),'keine'))] for label,r in selected])
para('30 % Leistungsreserve entsprechen bei unveränderter Geometrie und Ähnlichkeit nur etwa 19 % zusätzlichem Schub: 1,3^(2/3) = 1,191. Für 30 % Schubreserve wären etwa 48 % zusätzliche Wellenleistung nötig. Leistungsklasse allein genügt nicht: Ein Motor muss das erforderliche Drehmoment bei der benötigten Drehzahl und Temperatur tatsächlich dauerhaft liefern. Ein größerer Hochdrehzahlmotor kann für einen langsamen Großrotor ungeeignet sein.')
para('Die CSV-Dateien enthalten zusätzlich einen idealisierten Leistungs-Screen. Unter unveränderter Lastcharakteristik gilt Tmax/TGewicht ungefähr (verfügbare Wellenleistung / Schwebewellenleistung)^(2/3). Das ist ausschließlich eine leistungsbegrenzte Ähnlichkeitsabschätzung. Neue Drehzahlen, Abriss, Spitzen-Machzahl, Festigkeit, Drehmomentgrenzen, Strom und Kühlung werden darin nicht erneut nachgewiesen. Die Zahl ist kein maximal zulässiger Schub.')
para('Ohne Begrenzung von Gesamtleistung, Motormasse, Batterie oder Kosten gewinnt bei maximalem theoretischem Schub trivial die größte eingesetzte Leistung. Eine sinnvolle Bewertung vergleicht daher zusätzlich Leistungsreserve pro Masse, Energiebedarf und Bauraum. Es wird keine unbegründete absolute „leistungsfähigste“ Hardwarekombination benannt.')
heading('10. Abgleich mit den vorhandenen MN1330-Daten')
table(['Dokumentierte Angabe','Aussage für diese Studie'],[['2,75 kg / Motor','Referenzmasse; nicht jede neue Leistungsklasse wiegt so wenig'],['3400 W / 180 s','Keine Dauerleistung für 15 min; Leistungsseite ungeklärt'],['16,27 kW elektrische Prüfaufnahme','Haltedauer unbekannt; keine Dauerleistungsfreigabe'],['46,25 Nm höchstes Prüfmoment','Kein vollständiges Drehmoment-Drehzahl-Kennfeld'],['NS52×20-Prüfpropeller','Keine direkte Schubübertragung auf den P14-Sonderrotor']])
para(f'Schon die verbesserte P14-Variante fordert {fmt(pb["torque_Nm"])} Nm je Motor und damit deutlich mehr als das höchste dokumentierte Prüfmoment. Selbst wenn ein Leistungswert ausreichend erschiene, wäre der Betriebspunkt damit nicht belegt. Für klassische kompakte Rotoren sind die hohen Drehzahlen und ein anderes KV-/Spannungsniveau zusätzlich zu prüfen. Die Studie empfiehlt Leistungsanforderungen, keinen ungeprüften Motorzukauf.')
page();heading('11. Energie und Batterie-Massenrückkopplung')
table(['Konzept','12-kg-Akku: min','15 min: Akku kg bei eingefrorener Masse','max. min mit Massenrückkopplung'],[[label,fmt(12*.220*.8/r['electric_kW']*60),fmt(r['electric_kW']*.25/(.220*.8)),fmt(next(b['max_hover_minutes_similarity'] for b in battery if b['concept']==label and b['Wh_per_kg_assumed']==220))] for label,r in selected])
para('Annahmen: 220 Wh/kg auf Packebene, 80 % nutzbare Energie, keine Zusatzleistungsverbraucher. Die Spalte mit eingefrorener Masse ist nur eine erste Energieumrechnung und kein konsistenter Akkuauslegungswert. Ein schwererer Akku erhöht den Schwebebedarf. Die Rückkopplungsrechnung setzt Pelektrisch = k × mGesamt^(3/2) bei unveränderter Geometrie und angenommenem konstantem Wirkungsgrad.')
para('Mit Trockenmasse einschließlich Nutzlast md und Batteriemasse mb gilt t = 0,8 × e × mb / [k × (md + mb)^(3/2)]. Das theoretische Maximum liegt bei mb = 2 × md. Selbst dieses mathematische Maximum ist kein realisierbarer Betriebswert: Tragstruktur, Motorleistung, Drehzahl und Batterieleistung reichen bei solchen Massen möglicherweise nicht aus. Es liefert eine günstige Näherung innerhalb des Ähnlichkeitsmodells. Die Zusatzdatei untersucht außerdem 180 und 300 Wh/kg.')
figure('Batterie.png','Eine größere Batterie verlängert die Schwebedauer wegen ihres Eigengewichts nicht beliebig. Das 15-Minuten-Ziel wird in diesen Rechenfällen verfehlt.')
para('Die Auswertung berücksichtigt weder einen 80-km/h-Flug noch eine vollständige Mission mit Start, Steigen, Wind, Ausweichmanövern und Landung. Vorwärtsflug kann induzierte Leistung verändern und erzeugt zugleich zusätzlichen Widerstand. Ohne entsprechendes Modell lässt sich daraus keine belastbare Missionsreichweite ableiten.')
page();heading('12. Unsicherheit und Motormassen-Sensitivität')
para('Für jedes ausgewählte Konzept wurden 10.000 Szenarien mit festem Zufallsstartwert 20261102 gerechnet. Unabhängige Gleichverteilungen: 0–20 kg zusätzliche Systemmasse, Motorwirkungsgrad 0,75–0,90 und aerodynamischer Leistungsmultiplikator 0,85–1,25. Diese Bereiche sind frei gesetzte Annahmen. Die Quantile beschreiben diese Szenarioverteilung; sie sind keine statistisch validierten Vertrauensintervalle für reale Fluggeräte.')
table(['Konzept','Nennwert kW','Szenario 5 %','Median','Szenario 95 %'],[[s['concept'],fmt(s['nominal_kW']),fmt(s['scenario_p05_kW']),fmt(s['scenario_median_kW']),fmt(s['scenario_p95_kW'])] for s in sens])
figure('Unsicherheit.png','Die Unsicherheitsbereiche überlappen. Kleine Unterschiede zwischen Konzepten rechtfertigen ohne vermessene Rotoren und reale Rahmenmassen keine endgültige Rangfolge.')
para('Die separate Motormassentabelle untersucht mechanische spezifische Leistungen von 1, 3 und 6 kW/kg sowie 10–60 kW Nennleistung je Motor. Die vorhandenen 2,75 kg werden ersetzt durch mMotor = PNenn / spezifische Leistung. Anschließend wird die neue Masse mittels m^(3/2) auf den Bedarf zurückgeführt. Es handelt sich nicht um eine Marktübersicht realer Motormassen.')
para('Damit kann eine nominell stärkere Motorvariante durch höhere Eigenmasse ihre Reserve teilweise wieder verlieren. Zusätzlich größere Regler, Kabel und Batterieanschlüsse sind weiterhin offen. Die Konsequenz ist, zuerst einen nachgewiesenen Betriebspunkt samt thermischem Dauerzustand und Masse zu wählen und danach die Fahrzeugmasse erneut zu schließen.')
page();heading('13. Numerische Prüfung und Grenzen')
c24=data['checks'][0]['result'];c48=data['checks'][1]['result'];old=data['checks'][2]['result']
table(['Prüffall','Drehzahl [1/min]','Elektrisch [kW]'],[['Neuberechnung, 24 Elemente',fmt(c24['rpm']),fmt(c24['electric_kW'],3)],['Neuberechnung, 48 Elemente',fmt(c48['rpm']),fmt(c48['electric_kW'],3)],['Vorhandene P14-Funktion, 32 Elemente',fmt(old['rpm']),fmt(old['electricalPowerAssumed_W']/1000,3)]])
para(f'Die Verdopplung der radialen Auflösung verändert den elektrischen Bedarf im 12°-Referenzfall um {fmt(abs(c48["electric_kW"]/c24["electric_kW"]-1)*100,2)} %. Die Reproduktion des vorhandenen P14-Schwebefalls liegt ebenfalls nahe. Das prüft numerische Konsistenz, nicht die physikalische Genauigkeit der Ersatzpolaren. Die Vergleichsgrundlage ist bewusst der 12°-Fall; die Optimierung darf einen anderen Pitch wählen.')
para('Nicht modelliert: instationäre 3D-Strömung, gegenseitige Rückwirkung koaxialer Rotoren, seitliche Nachlaufinteraktionen, Person-/Deckabschattung, Bodeneffekt, Kompressibilität, Aeroelastik, echte Blattprofilpolaren, Laminatfestigkeit, Ermüdung, Lagerlebensdauer, Akustik, Motor-/ESC-Kennfelder, Kühlung und Flugreglerausfälle. P14-Servostellbereich wird für Koaxialfälle geprüft; Servokräfte und Strukturfestigkeit für neue Geometrien werden nicht neu nachgewiesen.')
para('Die Studie ist eine analytisch-numerische Entwurfsstudie mit stationärer BEMT. Es wurde keine neue 3D-CFD durchgeführt. Historische Re=40-Versuche sind keine Validierung der hier berechneten Rotoren. Aus reinem Schweben und einer Momentbilanz folgt weder dynamische Stabilität noch Motor-Ausfalltoleranz. Für einmotorige und ungerade Anordnungen bleibt ein Gegenmomentsystem erforderlich.')
heading('14. Konkrete Empfehlung für die nächste Revision')
para('A: P14 als kompakte Koaxialreferenz mit 4 statt 8 Blättern und 750–800 mm Radius weiter untersuchen. Das verringert im vorhandenen Masse-/Aeromodell den Bedarf, verlangt jedoch weiterhin erheblich höhere dauerhaft belegte Motormomente als in den MN1330-Prüfdaten. Die 800-mm-Variante lässt innerhalb 1,70 m Breite nur 100 mm für beide Schutzseiten zusammen; der vollständige Schutzbauraum muss geschlossen werden.')
para('B: Einen klassischen Quadrokopter und einen Hexakopter mit den oben angegebenen besten geprüften Radien als neue Rahmenentwürfe aufbauen. Zuerst Masse und Rotorfreiraum konstruktiv schließen, dann die Rangfolge mit echten Herstellerkennfeldern beziehungsweise Messdaten neu bewerten. Für alle Varianten Blätter, Motoren, Regler und Akkus über ihren gesamten Betriebspunkt prüfen; 30 % Leistungsreserve alleine genügt nicht.')
para('C: Okto- und Dekakopter weiterführen, wenn Regelbarkeit und potenzielle Fehlerbeherrschung gegenüber Komponentenanzahl höher gewichtet werden. Ein Motor-Ausfallfall benötigt eine eigene Kraft-/Momentverteilung und Leistungsreserve der verbleibenden Antriebe. Ein Standardquad ist ohne besondere Maßnahmen üblicherweise nicht auf den vollständigen Ausfall eines Motors ausgelegt. In dieser Studie wurde kein Ausfallflug nachgewiesen.')
para('D: Das 15-Minuten-Ziel als eigenständigen Machbarkeitskonflikt behandeln. Dafür sind wesentlich geringere Trockenmasse, mehr Rotorfläche, ein anderes Missionsprofil oder eine andere Energieversorgung zu untersuchen. Die Energietabelle zeigt, warum allein eine höhere Motor-Nennleistung oder ein größerer Akku das Ziel nicht löst.')
heading('15. Reproduzierbarkeit und Dateien')
total=len(pairs)+len(single)+len(compact)+len(mixed)
para(f'Berechnet wurden {total} Geometrie-/Anordnungsfälle einschließlich geometrisch oder aerodynamisch ausgeschlossener Varianten. Ring- und Rastervarianten zählen als getrennte Anordnungen, teilen aber denselben isolierten Rotorbetriebspunkt. Pro Fall werden bis zu drei Pitchwerte geprüft. Die Motor-Kombinationstabellen enthalten sechs hypothetische Nennleistungsklassen. Die Unsicherheitsanalyse umfasst {len(selected)*trials} Szenarien.')
para('Ausführung im Projektverzeichnis: node studie_antrieb/simulieren.cjs; node studie_antrieb/einzelrotoren.cjs; node studie_antrieb/kompakt.cjs; node studie_antrieb/mischanordnungen.cjs; MPLCONFIGDIR=/tmp/propboard-mpl python studie_antrieb/bericht.py. Voraussetzungen: Node.js sowie Python mit NumPy, Matplotlib und ReportLab. Es werden keine externen Dienste oder Dateien aus dem Netz benötigt.')
table(['Datei','Inhalt'],[['Rotorvergleich.csv / Motorkombinationen.csv','P14-nahe Koaxialpaare, Leistungs-Screen'],['Einzelrotoren_1_bis_10.csv','Große seitlich getrennte P14-nahe Rotoren'],['Kompakte_Anordnungen.csv / Kompakt_Motorkombinationen.csv','Klassische Ring- und Rastervarianten mit Motor-Klassen'],['Mischanordnungen.csv','Paare und Einzelrotoren gemeinsam'],['Batterie_Rueckkopplung.csv','Energie mit Massenrückkopplung'],['Unsicherheit.csv / Motormassen_Sensitivitaet.csv','Szenarioquantile und schwerere Motoren'],['Ergebnisse.json / weitere JSON','Rohdaten und numerische Vergleichsprüfungen'],['Manifest_SHA256.json','Integrität der Studienartefakte und verwendeten Projektquellen']])
para('Projektquellen: README.md; kreis_r04/mn1330_p14/parameter.json; ERGEBNIS.md; MOTOR_DATEN.md; Ausgabe/Massenvarianten.json; Motor_Daten.json; vorhandene BEMT- und P14-Physikquellen. Dies sind interne Projektstände mit dokumentierten Annahmen, keine neu geprüften Herstellerfreigaben. Die Studie verändert weder CAD noch die vorhandenen Flugsimulatoren.')
(H/'Studie.md').write_text('\n'.join(md))
(H/'Studie.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>PropBoard Antriebsstudie</title><style>body{font:16px/1.55 system-ui;max-width:1100px;margin:40px auto;padding:20px;color:#163044}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bccbd4;padding:8px;text-align:left}th{background:#dfedf4}img{max-width:100%}h2{margin-top:2em}</style>'+''.join(ht)+'</html>')
def footer(canvas,doc):
    canvas.setFont('DejaVu',8);canvas.drawString(1.8*cm,1.1*cm,'PropBoard | Vorstudie | 02.11.2026');canvas.drawRightString(19.2*cm,1.1*cm,str(doc.page))
SimpleDocTemplate(str(H/'Studie.pdf'),pagesize=(21*cm,29.7*cm),rightMargin=1.8*cm,leftMargin=1.8*cm,topMargin=1.6*cm,bottomMargin=1.7*cm,title='PropBoard: Antriebsstudie 1 bis 10 Motoren',author='PropBoard Entwicklungsstudie').build(story,onFirstPage=footer,onLaterPages=footer)
summary={'geometry_cases':total,'classic_best':classic,'p14_best':pb,'monte_carlo_scenarios':len(selected)*trials,'numerical_difference_24_48_fraction':abs(c48['electric_kW']/c24['electric_kW']-1)}
(H/'Zusammenfassung.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
sources=[H.parent/p['file'] for p in data['inputs']]+[H.parent/'kreis_r04/mn1330_p14/MOTOR_DATEN.md',H.parent/'kreis_r04/mn1330_p14/Motor_Daten.json']
manifest={str(f.relative_to(H.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in list(H.iterdir())+sources if f.is_file() and f.name not in ['Manifest_SHA256.json','Studienpaket.zip']}
(H/'Manifest_SHA256.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(H/'Studienpaket.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in H.iterdir():
        if f.is_file() and f.name!='Studienpaket.zip':z.write(f,'studie_antrieb/'+f.name)
    for f in dict.fromkeys(sources):
        if f.parent!=H:z.write(f,str(f.relative_to(H.parent)))
print(json.dumps(summary,ensure_ascii=False,indent=2))
