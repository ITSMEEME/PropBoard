"""Export the engineering study, scientific figures and reviewable PDF.
All conclusions preserve material/contact/model uncertainties;no release stamp.
"""
from pathlib import Path
import json,math,csv,hashlib,re,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from balken import arm_model
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe/Festigkeit';read=lambda n:json.loads((O/n).read_text());S=read('Statik_Uebersicht.json');J=read('Verbindungen.json');B=read('Klebung_Stirnkontakt.json');Q=read('Querschnitt_Verbindung_Details.json');D=read('Landestoss_Simulation.json');V=read('Solver_Validierung.json');C=read('CAD_Geometrie.json');OPT=read('Aenderungsoptionen.json');sha=C['native_sha256'];assert all(x['native_sha256']==sha for x in [S,J,B,Q,D,V,OPT]);assert V['passed'] and B['verification']['passed'];assert all(x['passed'] for x in D['implementation_checks']);assert hashlib.sha256((H/'Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd').read_bytes()).hexdigest()==sha
cfg=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());m0=next(x for x in S['cases'] if x['propeller_index']==9 and x['variant']=='V4' and x['contact_mode']=='stick');j0=next(x for x in J['cases'] if x['propeller_index']==9 and x['variant']=='V4');bc=next(x for x in B['cases'] if x['leg']==0 and x['end']=='top' and x['Ga_assumed_MPa']==1000 and x['deltaT_K']==0 and x['end_GFK_E_assumed_MPa']==10000 and x['contact_enabled']);worst=max(j0['clamps'],key=lambda x:x['resultant_slip_demand_N']);capacity=worst['friction_capacity_N_mu02_normal_factorPi'];plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140,'savefig.bbox':'tight'})

def save(fig,name):
 fig.tight_layout();fig.savefig(O/(name+'.png'));fig.savefig(O/(name+'.pdf'));plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.7))
for v in ['V1','V2','V3','V4','V5']:
 a=sorted([x for x in S['cases'] if x['variant']==v and x['contact_mode']=='stick'],key=lambda x:x['propeller_index']);ax.plot([cfg[x['propeller_index']]['diameter_mm'] for x in a],[max(x['peak_arm_tension_MPa'],x['peak_arm_compression_MPa']) for x in a],'-o',label=v)
ax.set(xlabel='Propeller-Bezugsdurchmesser [mm]',ylabel='Längsspannungsbedarf der Armrohre [MPa]',title='Linearer FE-Bedarf:160 kg,3 g auf2 Füßen,E=50 GPa,G=3 GPa');ax.grid(alpha=.2);ax.legend(ncol=5);fig.text(.02,-.035,'Ideale Wurzeln/Motorknoten;Boden seitlich haftend.Rohrzulässigkeiten nicht belegt.Große Verformungen sind Extrapolationen.',fontsize=8);save(fig,'01_Armrohre_50_Konfigurationen')
fig,axes=plt.subplots(1,2,figsize=(10,4));mu=np.linspace(.05,.6,100);Fp=worst['two_M4_8p8_preload_each_assumed_N']
for retain in [1,.7,.5]:axes[0].plot(mu,mu*2*math.pi*Fp*retain/1000,label=f'{retain*100:.0f}% Vorspannung')
axes[0].axhline(worst['resultant_slip_demand_N']/1000,color='crimson',label='berechneter Bedarf');axes[0].set(xlabel='Angenommener Reibwert',ylabel='Haltekraft [kN]',title='Zwei M4-8.8,günstiger gleichmäßiger Kontakt');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
a=[x for x in B['cases'] if x['leg']==0 and x['end']=='top' and x['deltaT_K']==0 and x['end_GFK_E_assumed_MPa']==10000 and x['contact_enabled']];a.sort(key=lambda x:x['Ga_assumed_MPa']);axes[1].plot([x['Ga_assumed_MPa'] for x in a],[x['peak_longitudinal_adhesive_shear_MPa'] for x in a],'-o',label='mit Druck-Stirnkontakt');axes[1].axhline(1074/(2*math.pi*8.3*29.7),color='gray',ls='--',label='nur mittlere Axialschubspannung');axes[1].set(xlabel='Angenommener Klebstoff-Schubmodul [MPa]',ylabel='Elastische Längsschubspitze [MPa]',title='Oberer Fitting:1,074 kN +65,85 Nm');axes[1].legend(fontsize=8);axes[1].grid(alpha=.2);save(fig,'02_Klemmung_und_Klebung')
fig,axes=plt.subplots(1,2,figsize=(10,4.3))
for r in D['trace_cases']:
 if not (r['terrain_pattern']=='level' or r['terrain_pattern']=='one_first' and r['pad_c_assumed_Ns_m']==0):continue
 if r['terrain_pattern']=='level' and r['pad_c_assumed_Ns_m']==500 or r['pad_k_assumed_N_mm']==500 or r['pad_k_assumed_N_mm']==30000:
  t=r['trace'];label=f"{r['terrain_pattern']},k={r['pad_k_assumed_N_mm']:.0f},c={r['pad_c_assumed_Ns_m']:.0f}";ms=np.array(t['time_s'])*1000;axes[0].plot(ms,np.sum(t['force_each_foot_N'],axis=1)/(160*9.81),label=label);axes[1].plot(ms,np.max(t['pad_compression_mm'],axis=1),label=label)
axes[0].axhline(3,color='crimson',ls='--',label='angenommenes3-g-Ziel');axes[1].axhline(3,color='crimson',ls='--',label='nominelle Metallkontaktgrenze');axes[0].set(xlabel='Zeit seit Erstkontakt [ms]',ylabel='Gesamte Bodenreaktion / Gewichtskraft',title='V4/42,160 kg,0,5 m/s;3-DOF-Sensitivität');axes[1].set(xlabel='Zeit [ms]',ylabel='Größte Sohlenkompression [mm]',title='Sohlenparameter sind keine gemessenen TPU-Daten')
for a in axes:a.grid(alpha=.2);a.legend(fontsize=6.8)
save(fig,'03_Landestoss_Zeitverlauf')
fig,ax=plt.subplots(figsize=(8,4));xs=[x['radial_offset_mm'] for x in Q['foot_sections']];ax.plot(xs,[x['centre_point_nominal_bending_MPa'] for x in Q['foot_sections']],'-o',label='mittiger Punktkontakt am Boden');ax.plot(xs,[x['uniform_ground_nominal_bending_MPa'] for x in Q['foot_sections']],'-s',label='gleichmäßig verteilte Bodenauflage');ax.axhline(250,ls='--',color='gray',label='hypothetische Al-Streckgrenze250 MPa');ax.set(xlabel='Querschnitt rechts der Fußmitte [mm]',ylabel='Nominelle Biegespannung [MPa]',title='Tatsächliche CAD-Fußquerschnitte;F=2,354 kN');ax.grid(alpha=.2);ax.legend(fontsize=8);save(fig,'04_Alufuss_Bodenauflage')
# Physical FE centreline deformation,not an OEM CAD surface or a solid stress contour.
c=next(x for x in C['configurations'] if x['propeller_index']==9 and x['variant']=='V4');model=arm_model(c,mesh_mm=25);model.nodes[model.foot]['dofs']=[2,3,4,5];model.assemble();r=model.result(model.foot,[0,0,2354.4,0,0,0]);u=r['_u'];fig,ax=plt.subplots(figsize=(9,4.5))
from matplotlib.collections import LineCollection
segments=[];values=[]
for e,er in zip(model.elements,r['elements']):
 i,j=e['i'],e['j'];a=model.nodes[i]['p'];b=model.nodes[j]['p'];ax.plot([a[0],b[0]],[a[2]+88,b[2]+88],color='#c4cbd0',lw=1);segments.append([[a[0]+u[i,0],a[2]+88+u[i,2]],[b[0]+u[j,0],b[2]+88+u[j,2]]]);values.append(max(er['tensile_demand_MPa'],er['compressive_demand_MPa']))
lc=LineCollection(segments,cmap='plasma',linewidths=3);lc.set_array(np.array(values));ax.add_collection(lc);ax.autoscale();ax.set_aspect('equal',adjustable='box');fig.colorbar(lc,ax=ax,label='linearer Längsspannungsbedarf [MPa]');ax.set(xlabel='Radialkoordinate ab Armwurzel [mm]',ylabel='Welt-Z [mm]',title='V4/42:FE-Mittellinien,Verformung1×,2,354 kN/Fuß');ax.grid(alpha=.2);fig.text(.02,-.035,'Graue Lage unverformt.Obere Rohrpaare überlagern sich in der Projektion.Keine Volumen-/Laminat-Spannungs-FEA.',fontsize=8);save(fig,'05_FE_Verformung_V4')

def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x) for x in row)+' |' for row in rows])
variant=[]
for v in ['V1','V2','V3','V4','V5']:
 x=next(x for x in S['cases'] if x['variant']==v and x['propeller_index']==9 and x['contact_mode']=='stick');variant.append([v,f"{x['foot_displacement_mm']:.1f}",f"{max(x['peak_arm_tension_MPa'],x['peak_arm_compression_MPa']):.0f}",f"{x['linearized_buckling_factor']:.2f}",f"{x['required_ground_mu']:.3f}"])
imp=[]
for speed,kp,pat in [(.5,500,'level'),(.5,30000,'level'),(.5,500,'one_first'),(.5,30000,'one_first'),(1,500,'level'),(1,30000,'one_first')]:
 x=next(x for x in D['cases'] if x['propeller_index']==9 and x['variant']=='V4' and x['contact_mode']=='stick' and x['sink_speed_m_s']==speed and x['pad_k_assumed_N_mm']==kp and x['pad_c_assumed_Ns_m']==0 and x['terrain_pattern']==pat and x['mass_kg']==160 and x['gyration_radius_assumed_m']==.5 and x['cg_xy_m']==[0,0]);imp.append([speed,int(kp),pat,f"{x['max_observed_total_load_factor']:.2f}",f"{x['max_observed_foot_force_N']:.0f}",f"{x['max_pad_compression_mm']:.2f}",'vollständig' if x['full_peak_computed'] else 'Abbruch vor Spitze'])
refined=[]
for x in B['cases']:
 if x['leg']==0 and x['end']=='top' and x['contact_enabled'] and x['end_GFK_E_assumed_MPa']==10000:refined.append([int(x['Ga_assumed_MPa']),int(x['deltaT_K']),f"{x['peak_longitudinal_adhesive_shear_MPa']:.1f}",f"{x['max_ideal_end_pressure_MPa']:.0f}",f"{x['max_plug_longitudinal_MPa']:.0f}"])
sens=[[x['name'],f"{x['displacement_mm']:.1f}",f"{x['peak_arm_stress_MPa']:.0f}",f"{x['buckling_factor']:.2f}"] for x in S['sensitivities']]
opts=[[f"{x['od_mm']}/{x['id_mm']}",f"{x['peak_arm_stress_MPa']:.0f}",f"{x['peak_root_pullout_N']/1000:.2f}",f"{x['arm_CFK_added_four_arms_kg']:.3f}"] for x in OPT['options'] if x['option']=='arm_diameter']
maxEnergy=max(x['energy_balance_relative_error'] for x in D['cases']);maxForce=max(x['force_balance_error'] for x in S['cases']);maxMoment=max(x['moment_balance_error'] for x in S['cases']);Aframe=next(x for x in OPT['options'] if x['option']=='ideal_pinned_A_frame_reference');contactMax=max(x['uniform_ground_nominal_bending_MPa'] for x in Q['foot_sections']);pointMax=max(x['centre_point_nominal_bending_MPa'] for x in Q['foot_sections'])
text=f'''# D12 – Festigkeits- und Landestoßuntersuchung

Stand 04.11.2026. Unveränderte CAD-Basis: `Quad_Reglerhalter_Landefuesse.FCStd`, SHA-256 `{sha}`.

## Ergebnis und Bedeutung

Unter den ausgewiesenen Studienannahmen ergibt sich **kein positiver Tragfähigkeits- oder Landefreigabenachweis für D12**. Die Rechnung zeigt konkrete Nachweisdefizite bei Armrohren, axialer Klemmkraftübertragung, biegemomentbelasteten Klebefittings und ungünstiger Bodenauflage. Fehlende Werkstoff-/Kontaktkennwerte kommen zu diesen Rechenbefunden hinzu. Die CAD-Geometrie wurde für diese Untersuchung nicht geändert.

V4/42 Zoll,160 kg,3 g auf zwei Füßen: {m0['force_per_foot_N']:.0f} N je Fuß, {m0['foot_displacement_mm']:.1f} mm linearer Weg und rund {max(m0['peak_arm_tension_MPa'],m0['peak_arm_compression_MPa']):.0f} MPa Längsspannungsbedarf in den Armrohren. Mit dem vorgeschlagenen Studienfaktor1,5 wären dafür rund {m0['required_longitudinal_allowable_with_study_factor1p5_MPa']:.0f} MPa entsprechende Projektzulässigkeit nötig; diese ist für das vorhandene Rohr nicht belegt. Das ist eine Anforderungsrechnung,keine Behauptung einer gemessenen Rohrspannung oder eines bekannten Bruchwertes.

Die kritische Wurzelverbindung muss {worst['resultant_slip_demand_N']/1000:.2f} kN Zug halten. Zwei angenommene M4-8.8 mit je {worst['two_M4_8p8_preload_each_assumed_N']:.0f} N Vorspannung und Reibwert0,2 liefern selbst bei günstiger gleichmäßiger Ringpressung nur {capacity/1000:.2f} kN. Dieses ausdrücklich bedingte Verbindungskriterium ist schon ohne Faktor1,5 um etwa Faktor{worst['resultant_slip_demand_N']/capacity:.2f} unterdeckt.

Die obere Stützenverbindung erfährt neben etwa1,07 kN Druck und0,54 kN Querkraft ein Biegemoment von65,85 Nm. Daher ersetzt die frühere mittlere Klebschubspannung von etwa0,76 MPa keinen Klebfugennachweis. Das verfeinerte reduzierte Kontaktmodell liefert bei den Referenz-Steifigkeiten rund{bc['peak_longitudinal_adhesive_shear_MPa']:.0f} MPa elastische Längsschubspitze und rund{bc['max_ideal_end_pressure_MPa']:.0f} MPa ideale Endauflagepressung. Auch hierfür fehlen zulässige Werte und eine Prozessqualifikation.

## 1. Gegebene Daten,Annahmen und Quellenqualität

Belegt sind die D12-BREP-Geometrie,die nominellen Rohre20/17 mm,die vom Nutzer genannte Außentoleranz±0,2 mm,die0°/90°-Faserorientierungen und100 kg Nutzlast. Die50 CAD-Konfigurationen enthalten1,2,2,3 oder4 Armrohre. Das V1-Rohr35/32 mm ist weiterhin eine nicht beschaffungsbestätigte Annahme. Motoren,Akku und Regler sind nicht vollständig über einen tatsächlichen Gesamtmassen-/Schwerpunktbericht geschlossen.

160 kg Gesamtmasse,0,2–1,0 m/s Sinkgeschwindigkeit,E_L=30/50/70 GPa,G=2/3/5 GPa,Schubkorrekturfaktor0,5,Kontakt-/Klebstoffsteifigkeiten und Reibwerte sind ausdrücklich Rechenannahmen beziehungsweise Sensitivitäten. Es wurden keine Herstellerzulässigkeiten für CFK,Laminat,Querdruck,GFK-Endringe,Aluminium oder Klebstoff erfunden. Die frühere lokale Beschaffungsnotiz enthält keine verifizierten CFK-E-/Festigkeitswerte und keinen Original-Nachweis für den Faseranteil80/20; dieser Anteil wurde nicht als gesicherter Laminataufbau verwendet.

M4-Eigenschaftsklassen8.8/10.9/12.9 werden als hypothetische Normklassen mit nominalen Prüfspannungen580/830/970 MPa untersucht. Das belegt nicht die tatsächlich eingebauten Schrauben. Der Studienfaktor1,5 ist ein offen vorgeschlagener Projektfaktor,keine behauptete Luftfahrt-/Zulassungsanforderung. Aluminium-Streckgrenze250 MPa wird nur als Beispiel für einzelne Querschnittsscreens verwendet;es liegt kein Abnahmezeugnis vor.

## 2. Modellaufbau und Rückverfolgbarkeit

Die Achsen,Außen-/Innenradien und Endpunkte sämtlicher120 Armrohre und100 Landestützen wurden aus den tatsächlichen zylindrischen BREP-Flächen ausgelesen. Alle50 Konfigurationen stimmen mit dem Generator bis maximal{C['max_generator_endpoint_error_mm']:.2e} mm überein. Die Rechnung verwendet also die reale D12-Geometrie als Mittellinienmodell.

Räumliche12-DOF-Timoshenko-Balken bilden Zug/Druck,zwei Biegerichtungen,Querkraft und Torsion ab. E_L und G sind unabhängige äquivalente Querschnittskennwerte;es handelt sich nicht um plyweise Laminat-FEA oder Tsai-Wu-/Hashin-Auswertung. Die35-mm-Armklemmzonen werden an ihren inneren freien Rohrenden ideal eingespannt;der gemeinsame Motorknoten ist zunächst starr. Die32-mm-Landeklemmungen sitzen an ihren tatsächlichen Rohrpositionen. Starre Exzentrizitäten verbinden Armmitte,Fittings,CFK-Stützen und Fuß;die Querkräfte und Momente werden dadurch mitgerechnet.

Der Zentralrahmen und der Pilot werden nicht als deformierbare Struktur modelliert. Die ideale Wurzelfixierung ist eine günstige Annahme für den lokalen Arm;zusätzliche Wurzel-Drehfedern zeigen die Empfindlichkeit. Die Stützen-Fittingrotation wird ebenfalls variiert. Lokale Kontaktspannungen,Schraubenprying,Laminatablösung,Fatigue und Fertigungsfehler sind nicht aus einer Volumen-/Kontakt-FEA berechnet.

Drei Boden-Grenzfälle werden getrennt behandelt: point=freie Fußverschiebung/-rotation unter vorgeschriebener Vertikalkraft;stick=seitlich haftender,rotatorisch freier Fuß;flat=zusätzlich ideal festgehaltene Fußrotation. Die Haftreaktionen müssen durch Bodenreibung und positive Sohlenpressung möglich sein. Beispielsweise benötigt V4/stick nur etwa0,009 Bodenreibwert,V1/stick etwa1,03. Flat-Fälle mit erforderlichem Druckmittelpunkt außerhalb±64/±14 mm sind bereits geometrisch keine zulässige vollflächige Auflage. Eine günstige Randbedingung darf daher nicht pauschal als reale Bodenlage angenommen werden.

## 3. Numerische Verifikation

Axialstab,Kragbalken mit Schubanteil,Torsion,einfach gelagerter Balken,starre Körperbewegung und schubweiches Säulenknicken wurden gegen unabhängige geschlossene Lösungen geprüft. Für den D12-Referenzfall wurden50/25/12,5-mm-Netze verglichen. Verschiebung und Nennspannungen sind praktisch identisch;der letzte Knickfaktorunterschied liegt unter0,001 %. Die Kraftbilanzfehler der150 statischen Hauptbedingungen liegen höchstens bei{maxForce:.2e},die Momentenbilanzfehler bei{maxMoment:.2e}.

Der Landestoßsolver wurde gegen den analytischen Spitzenwert eines ungedämpften symmetrischen Feder-Masse-Systems geprüft. Der Unterschied beträgt etwa0,00066 %. Die Zeitschrittverfeinerung0,4 auf0,1 ms ändert die ausgewerteten Spitzen um weniger0,002 %. Der größte relative Energiebilanzfehler aller{len(D['cases'])} eindeutigen Kontakt-Simulationen beträgt{maxEnergy:.2e}. Die Klebfugenrechnung besitzt eigene Kraft-/Momentenbilanzen,Netzverfeinerung und einen unabhängigen Volkersen-Vergleich.

**Diese Prüfungen verifizieren die numerische Implementierung. Sie validieren weder die Materialannahmen noch das reale Fahrzeug.**

## 4. Carbonarme:Ergebnisse für42-Zoll-Bezugsrotoren

Referenz:3 g auf zwei Füßen,je2354 N,E_L50 GPa,G3 GPa,ideale Wurzel/Motorknoten,Bodenmodus stick.

{table(['Variante','Weg mm','max.Längsbedarf MPa','linearer Knickfaktor','Boden-µ benötigt'],variant)}

Der lineare Knickfaktor bezieht sich auf genau den gewählten Kontakt-/Verbindungsfall und den aktuellen proportionalen Lastvektor. Er ist kein genereller Rohr-Sicherheitsfaktor. Bei V4 fällt er im seitlich freien point-Fall auf etwa0,47;im haftenden Fall beträgt er etwa3,23. Diese starke Abhängigkeit erfordert die reale Boden-/Lagerbedingungenklärung. Ein Faktor kleiner1 im freien Modell ist ein Instabilitätsindikator,dessen Modell über diese Grenze hinaus nicht als reale Nachknickantwort fortgesetzt werden darf.

Bei vielen hoch belasteten Fällen werden5° Rotation,5 % Spannweitenweg oder0,5 % berechnete Längsdehnung überschritten. Diese Markierungen sind Modellwarnungen,keine erfundenen CFK-Bruchgrenzen. Die Zahlen bleiben lineare Anforderungs-/Extrapolationswerte;ein geometrisch nichtlinearer Laminat- und Verbindungsnachweis fehlt.

Die Datei Lastfallmatrix_linear.csv enthält600 proportional abgeleitete Kombinationen:alle50 Geometrien,je drei Bodenmodi und1 g/vier Füße,3 g/vier Füße,3 g/zwei Füße sowie3 g/ein Fuß. Ein Ein-Fuß-Fall ist ein äquivalenter kurzzeitiger Lastfall eines Arms,keine Aussage,dass das ganze Fahrzeug auf einem Fuß statisch im Gleichgewicht bleibt.

![Armrohre](01_Armrohre_50_Konfigurationen.png)

![FE-Mittellinien](05_FE_Verformung_V4.png)

## 5. Einfluss unsicherer Steifigkeiten und Toleranzen

{table(['Sensitivität','Weg mm','max.Arm-MPa','Knickfaktor'],sens)}

Die Variante root1e5 bedeutet eine angenommene Drehsteifigkeit100000 Nmm/rad an jeder Wurzelrotation. Weiche Wurzeln verschlechtern die Ergebnisse stark. Eine zehnfach erhöhte lokale Biegesteifigkeit der Landeklemmzone beseitigt den hohen Gesamtbedarf nicht. Weiche Fittinggelenke können Biegemomente reduzieren,führen hier aber zu einem Instabilitätsproblem. Ihre Nachgiebigkeit ist keine alleinige Reparatur.

Die bekannte Rohrtoleranz passt nicht automatisch zur nominellen Zwischenlage:20,6-mm-Schellenbohrung minus zweimal0,3-mm-GFK ergibt20,0 mm effektive Bohrung. Ein20,2-mm-Rohr hat0,2 mm diametrales Übermaß. Für rein geometrischen Nullspalt wären bei Rohren19,8/20,0/20,2 mm Zwischenlagen0,4/0,3/0,2 mm nötig. Tatsächliche Toleranzen,Kompressibilität und Vorspannung müssen gemeinsam geschlossen werden;eine starre0,3-mm-Zwischenlage darf nicht als toleranzunempfindlich gelten.

## 6. Klemmverbindungen und Schrauben

Für die notwendige Reibübertragung wird die Kombination aus axialem Zug und Torsion angesetzt: F_slip=sqrt(N_Zug²+(T/R)²). Axialdruck kann an vorhandenen Endanschlägen anliegen;deren Stirndrucktragfähigkeit ist separat offen. Für Biegung/Querkraft wird ein projektierter Pressungsscreen V/(D L)+6 M_b/(D L²) ausgewiesen. Er ist keine Kontaktspannungs-Lösung.

Zwei M4-8.8 bei70 % der angenommenen Prüfbelastbarkeit liefern je etwa3565 N Vorspannung. Im günstigen Modell gleichmäßiger Ringpressung beträgt das integrierte Normalkraftmaß pi mal der Summe der beiden Schraubenkräfte. Beiµ0,2 entstehen deshalb nur etwa4,48 kN axiale Haltekraft gegenüber9,32 kN Bedarf an der unteren Wurzelklemmung. Ohne Setzverlust ist mindestensµ≈0,416 erforderlich;mit30 % Vorspannverlust bereits etwa0,595. Ein Studienfaktor1,5 erhöht diese Anforderungen weiter.

Am kritischen Wurzelport beträgt der projektierte äußere Pressungsbedarf etwa44,6 MPa,zuzüglich etwa10,2 MPa mittlerem Vorspann-Pressungsanteil im Beispiel. Das ist ein Kontaktmodell-Indikator,kein exakt bestimmter CFK-Druckspitzenwert. Die zulässige lokale Rohrpressung und die tatsächliche Verteilung sind unbekannt.

Höhere Schraubenklasse erhöht die mögliche Vorspannung,zugleich aber Rohrpressung,Laschenbiegung und Setz-/Schädigungsrisiko. Schraubenklasse allein stellt deshalb keine Lösung dar. Die Tabellen untersuchen70-%-Vorspannungen,50/70/100-%-Erhalt,µ0,1/0,2/0,35/0,5 sowie Laschen-Hebelannahmen2/4/6 mm. Schraubenprying,Gewindetragfähigkeit,Innengewindetiefe und tatsächliche Schraubenklasse sind nicht freigegeben.

![Klemmung und Klebung](02_Klemmung_und_Klebung.png)

## 7. Klebeverbindungen mit Biegung und Stirnauflage

Das einfache mittlere Schubmodell wird durch elastischen zylindrischen Shear-Lag für Axialkraft,Biegung und Torsion ersetzt. Zusätzlich wurde ein reduziertes gekoppeltes N/M-Modell mit unterschiedlichen CFK-/Al-EA/EI und einseitig drückender Stirnauflage über64 Winkelsektoren gerechnet. Klebstoff-Schubmodul und GFK-Endsteifigkeit sind dabei Sensitivitäten. Die Rechnung verteilt Kräfte/Momente zwischen Klebfuge und Stirnfläche;radiale Randablösung,Kohäsivbruch und Delamination werden dadurch noch nicht berechnet.

Am kritischen oberen Fitting liegt das Biegemoment65,85 Nm. Die Exzentrizität M/N beträgt61,3 mm und ist deutlich größer als der10-mm-Rohraußenradius. Reiner axialer Druckkontakt an der Stirnfläche kann diese Kombination deshalb nicht allein übertragen. Die Klebung beziehungsweise eine andere zugfähige Verbindung muss wesentlich am Momententransfer teilnehmen.

{table(['Ga MPa','DeltaT K','Klebschubspitze MPa','Endpressung MPa','Zapfenlängsbedarf MPa'],refined)}

Referenz mit Ga1000 MPa und angenommener GFK-E10 GPa:etwa50 MPa elastische Klebschubspitze,105 MPa ideale Endauflagepressung und168 MPa maximaler nominaler Längsspannungsbedarf im Aluminiumzapfen. Der schwächere/stärkere Endkontakt verändert insbesondere die Auflagepressung und die Lastaufteilung. Die allbond-Querschnittshülle und die reduzierte Kontaktrechnung dürfen nicht als identische physische Lastpfade addiert werden.

Die alten allbond-Spitzen können über60 MPa erreichen. Das ist ein elastischer Bedarfswert,kein mit einer pauschalen Datenblatt-Lap-Shear-Zahl direkt vergleichbarer freigegebener Klebfugenwert. Plastische Umverteilung,Bruchenergie,Schälfestigkeit,Laminatablösung,Klebefugenporen und Prozessstreuung fehlen. Für±40 K wurden hypothetisch20e-6/K CTE-Differenz angesetzt;dies verschärft beziehungsweise verschiebt die Schubspitzen. Die freie radiale Fehlpassung beträgt dabei etwa6,6 µm,bezogen auf die0,2-mm-Klebfuge etwa3,3 %.

## 8. Aluminiumfittings und Aufsetzfuß

Die nominale Hohlzapfen-Geometrie16,6/12,6 mm wurde mit den tatsächlichen FE-Endkräften untersucht. Wenn die gesamten Resultierenden über den dünnen Zapfen laufen,erfordert der obere Zapfen einschließlich Studienfaktor1,5 eine hypothetische Streckgrenze von bis348 MPa. Druck-Stirnauflage kann diesen Lastpfad deutlich entlasten;im reduzierten Referenz-Kontaktmodell verbleiben etwa168 MPa Längsbedarf vor Kerben,Querkraft und Faktor. Keine dieser Varianten ist ein vollständiger3D-Kontaktnachweis oder ein Werkstoffzeugnis.

Die17 maßgeblichen Alufuß-Querschnitte wurden direkt aus dem BREP geschnitten;auch Taschen und Sohlen-Mutternbohrungen sind enthalten. Bei symmetrischen Endkräften liefern zwei idealisierte Bodenauflagen unterschiedliche Ergebnisse:gleichmäßige Auflage maximal etwa{contactMax:.0f} MPa Nennbiegespannung;mittiger Punktkontakt maximal etwa{pointMax:.0f} MPa. Gegenüber einer nur hypothetischen250-MPa-Streckgrenze würde der Punktkontaktfall bereits ohne Faktor1,5 versagen. Lokale Kerben und die tatsächlich unsymmetrischen Stützenmomente sind in diesem einfachen Fußbalkenscreen noch nicht enthalten.

Die tatsächliche anfängliche Sohlenkontaktfläche beträgt etwa{Q['sole_nominal_initial_contact_area_mm2']:.0f} mm². Im2354-N-Fall ergibt das etwa{Q['sole_pressure_at_design_force_MPa']:.2f} MPa mittlere Sohlenpressung. Nennhärte TPU95A und Dichte bestimmen keine Kraft-Weg-Kennlinie.

![Alufuß](04_Alufuss_Bodenauflage.png)

## 9. Landestoßsimulation

Es wurden{len(D['cases'])} eindeutige Kontaktfälle gerechnet. Das Modell besitzt Hub/Nick/Roll eines starren Körpers auf vier einseitigen Kontakten. Die CAD-basierten Arm-/Stützenfedern liegen jeweils in Reihe mit einer hypothetischen Kelvin-Voigt-Sohle. Untersucht wurden0,2–1,0 m/s,120–200 kg,Trägheitsradien0,35/0,5/0,65 m,Schwerpunktversatz0/100 mm,ebener Erstkontakt sowie ein/zwei Füße zuerst mit bis10 mm Bodenhöhenunterschied. Seitenbewegung,Haft-/Gleit-Dynamik,verteilte Fersenauflage,Arm-Eigenträgheit und ein deformierbarer Zentralrahmen fehlen. Das ist ein verifiziert integriertes Sensitivitätsmodell,kein experimentell validierter6-DOF-Fahrzeugnachweis.

Sohlensteifigkeiten100–30000 N/mm und Dämpfung0/500 Ns/m sind Hypothesen. Die weichen Fälle sind keine Behauptung über solides TPU95A. Insbesondere werden auch steife Sohlenfälle berücksichtigt;es gibt keine Abstützung auf einen günstig ausgewählten Einzelwert. Im Grundfall sind Rotoren entlastet beziehungsweise ohne Restschub angenommen.

{table(['v m/s','k N/mm','Erstkontakt','beob.n','max.Fuß N','Sohle mm','Auswertung'],imp)}

Bei3 mm Sohlenkompression wird wegen der nominellen Schraubenkopflage abgebrochen;ebenso bei Zentralrahmenkontakt,5° Modellwinkel oder dem jeweiligen linearen Instabilitätsindikator. Abgebrochene Fälle zeigen nur die bis zum Abbruch beobachteten Kräfte,**keine vollständige Lastspitze**. Die Lastfaktoren sind gesamte Bodenreaktion geteilt durch Gewichtskraft;die vertikale Schwerpunktbeschleunigung in g ist n-1.

425 physikalisch eindeutige Parameterkombinationen ersetzen nicht die fehlenden Materialmessungen. Die zeitlich aufgelösten Referenzspuren und alle Abbruchgründe sind in den JSON-/CSV-Dateien enthalten. Bei0,5 m/s erfordert das gewählte3-g-Ziel bereits eine Anpassung der Kraft-Weg-Kennlinie oder der zulässigen Landegeschwindigkeit;die Annahme3 g darf nicht einfach als nachgewiesene reale Lastspitze übernommen werden.

![Landestoß](03_Landestoss_Zeitverlauf.png)

## 10. Konkrete Änderungshebel ohne CAD-Änderung

Ein rein rechnerischer Querschnittsvergleich zeigt folgende Hebel für V4/42 unter demselben Lastfall. Die großen Rohre passen **nicht** in die vorhandenen20-mm-Knoten;Aluminiummassen und neue Passungen/Freiräume sind in diesen Referenzmassen nicht enthalten.

{table(['Arm-OD/ID mm','max.Arm-MPa','Wurzelzug kN','zus.CFK/4Arme kg'],opts)}

25/21 mm senkt den Bedarf auf etwa302 MPa,erhöht aber die reine Arm-CFK-Masse um etwa0,70 kg und beseitigt das Zughalteproblem der bestehenden Klemmen nicht. Ein einfacher Lastangriff am Motorknoten statt zwischen den Knoten senkt den Referenzbedarf nur auf etwa523 MPa. Diese Einzelmaßnahmen erzeugen noch keinen positiven Gesamtnachweis.

Eine ideal gelenkige A-Abstützung zwischen Rahmenknoten,Motorknoten und Aufsetzfuß wurde als Lastpfad-Referenz gerechnet. Die beiden CFK-Stäbe wären etwa{Aframe['long_leg_mm']:.0f}/{Aframe['short_leg_mm']:.0f} mm lang,trügen etwa{Aframe['axial_leg_forces_N'][0]:.0f}/{Aframe['axial_leg_forces_N'][1]:.0f} N axial und erhöhten die CFK-Masse der vier Füße um etwa{Aframe['added_four_feet_CFK_only_kg']*1000:.0f} g ohne Gelenke. Der Armspannungsbedarf bliebe in dieser Referenz etwa417 MPa. Seitenstabilität,Ankerknoten,Gelenke,Schrauben,Klebungen und Freiräume sind dabei nicht nachgewiesen;es wurde kein neuer sicherer Rahmen behauptet oder stillschweigend in D12 eingebaut.

Die Priorität liegt deshalb auf einer geschlossenen Lastpfad-Neukonstruktion:zugfeste Endanschlüsse statt ausschließlich ungesicherter Reibhaltung,beherrschte Fittingmomente,qualifizierte Sohlen-/Dämpfungskennlinie und eine Fußbasis für Teilauflage. Größere Rohre allein oder höherfeste M4-Schrauben schließen diese Punkte nicht gemeinsam.

## 11. Prüfauftrag mit konkreten Belastungen

Vor einer positiven Freigabe sind mindestens folgende Ergebnisse nötig. Der Faktor1,5 bleibt ein zu bestätigender Projektvorschlag.

- Rohr-/Laminatwerte an der tatsächlich beschafften Charge:Axialzug/-druck,Biegung,Schub,Umfangs-/Querdruck und Ermüdungsdaten mit Temperatur/Feuchte-Knockdowns. Innendurchmesser,Wandstärke,Ovalität und Rohraußendurchmesser sind zu vermessen. Kein aus Faserwinkeln geschätzter Wert ersetzt diese Daten.
- Untere Arm-Endklemmung mit tatsächlicher Beschichtung,Isolierung und Schraubencharge:Zuglast9,32 kN im Limitfall,vorläufig13,98 kN bei Faktor1,5,zusammen mit den ausgewiesenen Querkräften/Momenten. Vorspannstreuung,Setz-/Temperaturverlust,Schlupfbeginn und Rohrquetschung sind zu erfassen. Ein vorgeschlagenes messbares Schlupfkriterium unter0,1 mm ist mit Funktionsanforderungen abzugleichen und kein Herstellergrenzwert.
- Kritischer oberer Stützenfitting:Kombinationslast etwa1,074 kN axial,0,536 kN quer und65,85 Nm Biegung;bei Faktor1,5 etwa1,611 kN,0,804 kN und98,77 Nm. Erforderlich sind echte CFK/Al/GFK/Klebstoff-Proben mit definiertem Oberflächenprozess,Aushärtung,Fugendicke und Einsatztemperaturen. Abziehen,Biegung,Schälen,Heiß-/Feuchtzustand und Ermüdung sind zu prüfen;ein reiner axialer Zugversuch reicht nicht.
- Instrumentierter Landestoßversuch nach bestandenem statischem Aufbau:160-kg-Dummy,anfangs0,2/0,3 m/s,dann Ziel0,5 m/s;ebene und versetzte Auflagen.0,5 m/s entspricht ohne Luft-/Antriebswirkung etwa12,7 mm freier Fallhöhe. Kraftmessung an allen Füßen,Beschleunigung,Rohrdehnungen,Klemmschlupf,Sohlenhub und Rahmenbodenfreiheit sind gemeinsam aufzuzeichnen. Ein vorgeschlagener Abtastwert mindestens10 kHz ist auf die tatsächlichen Impulszeiten abzustimmen. Diese Versuche wurden nicht durchgeführt.
- Zulässige Sinkgeschwindigkeit,Gesamtmasse,Schwerpunkt,Bodenarten,Einsatztemperaturen und Lastkollektiv sind als Anforderungen festzulegen. Ein positiver Einzellastnachweis wäre noch kein Lebensdauer- oder Produktionsnachweis.

## 12. Dateien und Reproduktion

CAD_Geometrie.json enthält die BREP-Geometrie;Statik_Uebersicht.json/.csv die150 FE-Hauptbedingungen;Lastfallmatrix_linear.csv600 linear skalierte Lastkombinationen;Verbindungen.json die50 Verbindungssätze;Klebung_Stirnkontakt.json36 verfeinerte Lastaufteilungsfälle;Querschnitt_Verbindung_Details.json die echten Fußschnitte und hypothetischen Schrauben-/Passungssweeps;Landestoss_Simulation.json und Landestoss_Uebersicht.csv die{len(D['cases'])} Kontaktfälle. Solver_Validierung.json und die eingebetteten Dynamik-/Klebungsprüfungen dokumentieren Implementierungsverifikation.

Die Skripte liegen unter nachweise/. Reihenfolge:cad_geometrie.py mit FreeCAD-Python,danach validieren.py,statisch.py,landestoss.py,querschnitte.py mit FreeCAD-Python,klebkontakt.py,optionen.py und bericht.py. NumPy,SciPy,Matplotlib und ReportLab werden verwendet. Kein Solverlauf ändert die native CAD-Datei.

Methodische Grundlage sind die lineare3D-Timoshenko-Balkenformulierung,konsistente geometrische Steifigkeit,virtuelle Arbeit für starre Exzentrizitäten,Volkersen-Shear-Lag und die Energie-/Impulsbilanz der einseitigen Federkontakte. Die zylindrischen und N/M-Kontakt-Erweiterungen sind hier explizit implementierte Reduktionsmodelle. Normklassenannahmen und Literaturformeln ersetzen keine Werkstoffzeugnisse oder Versuchsvalidierung.
'''
# Keep the actual unique case count consistent if the parameter sweep changes.
text=text.replace('425 physikalisch eindeutige',f"{len(D['cases'])} physikalisch eindeutige")
# Improve typographic spacing without changing numbers or model identifiers.
text=re.sub(r'(?<!\d),(?=\S)',', ',text)
text=re.sub(r';(?=\S)','; ',text)
words='alle|je|etwa|rund|maximal|mindestens|mit|von|auf|bis|unter|über|Studienfaktor|Schubkorrekturfaktor|Steifigkeiten|Prüfspannungen|Ga|GFK-E|E_L'
text=re.sub(r'\b('+words+r')(?=\d)',r'\1 ',text)
text=re.sub(r'(?<=\d)(?=(?:kg|MPa|GPa|mm|kN|Nm|m/s|Ns/m|g)(?:\b|/))',' ',text)
protected=[]
def protect(m):
 protected.append(m.group(0));return '§'+str(len(protected)-1)+'§'
text=re.sub(r'`[^`]*`|\b(?:D12|V[1-5]|M[34]|root1e[56]|bond1e[46]|grip_EI10|E[357]0|OD_minus0p2|OD_plus0p2)\b',protect,text)
text=re.sub(r'([a-zäöüß])(?=\d)',r'\1 ',text)
text=re.sub(r'§(\d+)§',lambda m:protected[int(m.group(1))],text)
text=text.replace('physikalisch eindeutige','unterschiedliche')
(O/'BERICHT.md').write_text(text)
summary=dict(native_sha256=sha,status='Nachweisdefizite_unter_Studienannahmen',production_ready=False,experimental_validation=False,FE_conditions=len(S['cases']),linear_load_combinations=600,impact_cases=len(D['cases']),bond_contact_cases=len(B['cases']),default=dict(variant='V4',propeller_index=9,mass_kg=160,load_factor=3,feet=2,foot_force_N=2354.4,arm_stress_demand_MPa=max(m0['peak_arm_tension_MPa'],m0['peak_arm_compression_MPa']),foot_deflection_mm=m0['foot_displacement_mm'],root_pullout_demand_N=worst['resultant_slip_demand_N'],conditional_root_capacity_8p8_mu02_N=capacity,refined_bond_shear_MPa=bc['peak_longitudinal_adhesive_shear_MPa']),implementation_verified=True,maximum_impact_energy_balance_error=maxEnergy,critical_missing=['CFK laminate strengths,transverse allowables and tolerances','Actual bolt grade/preload retention and friction','Adhesive/GFK force/strength/thermal/process data','Sole force-stroke/friction/temperature/wear data','Measured vehicle mass/inertia,global-frame and nonlinear contact validation'])
(O/'Ergebnis.json').write_text(json.dumps(summary,indent=2))
# Portable report with embedded scientific plots and a visible qualification limit on every page.
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
font=Path('/usr/share/fonts/truetype/dejavu')
for n,f in [('DV','DejaVuSans.ttf'),('DV-Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(n,str(font/f)))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold');styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyDV',fontName='DV',fontSize=9,leading=13,spaceAfter=5));styles.add(ParagraphStyle(name='CellDV',fontName='DV',fontSize=7,leading=9));styles.add(ParagraphStyle(name='H1DV',fontName='DV-Bold',fontSize=18,leading=22,spaceBefore=10,spaceAfter=10));styles.add(ParagraphStyle(name='H2DV',fontName='DV-Bold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=7))
def markup(t):
 t=html.escape(t);t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t);t=re.sub(r'`(.*?)`',r'<font name="Mono" size="7">\1</font>',t);return t
story=[];lines=text.splitlines();i=0
while i<len(lines):
 line=lines[i].strip()
 if not line:i+=1;continue
 if line.startswith('# '):story.append(Paragraph(markup(line[2:]),styles['H1DV']))
 elif line.startswith('## '):story.append(Paragraph(markup(line[3:]),styles['H2DV']))
 elif line.startswith('|'):
  cells=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   parts=[x.strip() for x in lines[i].strip().strip('|').split('|')]
   if not all(re.fullmatch('[-: ]+',x) for x in parts):cells.append([Paragraph(markup(x),styles['CellDV']) for x in parts])
   i+=1
  n=len(cells[0]);widths=[174*mm/n]*n;tab=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7ee')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#a6b5bf')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([tab,Spacer(1,6)]);continue
 elif line.startswith('!['):
  imagefile=re.search(r'\]\((.*?)\)',line).group(1);im=Image(str(O/imagefile));im.drawWidth=174*mm;im.drawHeight=im.imageHeight*im.drawWidth/im.imageWidth;story.extend([im,Spacer(1,7)])
 else:
  paragraph=[line]
  while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#','|','![')) and not lines[i+1].startswith('- '):i+=1;paragraph.append(lines[i].strip())
  t=' '.join(paragraph);story.append(Paragraph(markup(('• '+t[2:]) if t.startswith('- ') else t),styles['BodyDV']))
 i+=1
def footer(canvas,doc):
 canvas.setFont('DV',7);canvas.setFillColor(colors.HexColor('#6b2424'));canvas.drawString(18*mm,12*mm,'D12 Berechnungsstudie – keine Material-/Landefreigabe');canvas.setFillColor(colors.black);canvas.drawRightString(192*mm,12*mm,str(doc.page))
pdf=O/'D12_Festigkeit_Landestoss.pdf';doc=SimpleDocTemplate(str(pdf),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=18*mm,topMargin=17*mm,bottomMargin=20*mm,title='D12 Festigkeits- und Landestoßuntersuchung',author='PropBoard Berechnungsstudie');doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Report and PDF created',len(D['cases']),'unique impact cases;status remains not released')
