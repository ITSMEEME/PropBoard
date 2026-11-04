"""Transparent geometric tube-mass and single-tube beam screening, not a release.

No laminate strength, joint stiffness, buckling or multi-tube frame stiffness is
invented. A larger single-tube article is a candidate, not existing inventory.
"""
import json,math
from pathlib import Path
H=Path(__file__).resolve().parent
rho=1600
def section(d,di):
    return dict(area_mm2=math.pi/4*(d*d-di*di),I_mm4=math.pi/64*(d**4-di**4),J_mm4=math.pi/32*(d**4-di**4))
variants=json.loads((H/'Varianten.json').read_text())
for v in variants:
    s=section(v['od'],v['di']);lengths=[math.dist(a,b) for a,b in zip(v['start'],v['end'])]
    v.update(tube_cut_lengths_assumed_mm=lengths,tube_mass_assumed_kg=sum(lengths)*s['area_mm2']*rho*1e-9,section=s,motor_and_frame_nodes_mass_kg=None,assembly_mass_kg=None)
F=400;L=.420;torque=20;E=70e9;G=5e9;cases=[]
for d,di,source in [(20,17,'Vorhandener Querschnitt CBU20171005TG'),(35,32,'Neuer Vergleichsquerschnitt, kein bestätigter Artikel')]:
    s=section(d,di);I=s['I_mm4']*1e-12;J=s['J_mm4']*1e-12
    cases.append(dict(od_mm=d,id_mm=di,source=source,mass_per_m_kg=s['area_mm2']*rho*1e-6,root_moment_Nm=F*L,bending_stress_MPa=F*L*(d/2000)/I/1e6,tip_deflection_mm=F*L**3/(3*E*I)*1000,torsional_shear_stress_MPa=torque*(d/2000)/J/1e6,twist_deg=torque*L/(G*J)*180/math.pi,beam_model='Uniform rigidly clamped single circular tube;420mm idealized load arm',strength_pass=None))
baseline=json.loads((H/'D06_Bauteile_Quelle.json').read_text())['D05_MOTOR_PLATE']['mass_kg']
report=dict(variants=variants,single_tube_comparison=cases,assumptions=dict(density_kg_m3=rho,E_bending_Pa=E,G_torsion_Pa=G,comparison_force_N=F,comparison_torque_Nm=torque,idealized_load_arm_m=L),removed_separate_D05_motor_plate_mass_each_kg=baseline,removed_separate_D05_motor_plates_four_kg=4*baseline,total_mass_ranking_available=False,strength_release=False,scope='Concept study. Tube lengths run between assumed cut-end coordinates; all clamps/nodes/fasteners/liners/glue are excluded from tube masses.420mm uniform single-tube cantilever screening is independent of385mm conceptual cut lengths plus node offset. Assumed equivalent moduli are not certified laminate data.400N and20Nm are comparison loads, not validated aircraft loads or maximums. No dynamic factor, safety factor, fatigue, local crushing, laminate failure, joint slip or global D06 rotor clearance proof. Separate plate deletion is gross removed mass, not net weight saving; integrated replacement nodes still have mass. Multi-tube stiffness cannot be inferred by simply multiplying single-tube EI, as clamp stiffness and tube separation matter.')
(H/'Screening.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
lines=['# Fünf Varianten für den Motoranschluss','',
'Fünf eigenständige Konzeptbilder für 1, 2, 2, 3 und 4 Carbonrohre. Direktanschluss am starren Rahmenknoten und kompakter Aluminium-Motorknoten mit integrierten Befestigungsaugen am feststehenden Motorfuß; keine separate Motorplatte. Ein tatsächliches Klappgelenk ist nicht ausgelegt. Die vorhandene Motor-/Rotorbaugruppe wird durch diese Bilder nicht umgebaut oder freigegeben.','',
'V1 verwendet Ø35/32 mm als neuen Vergleichsquerschnitt. V2–V5 verwenden den vorhandenen Ø20/17-mm-Querschnitt. Ø35/32 ist kein nachgewiesener Kaufartikel.','',
'| Variante | Rohre | Rohrquerschnitt | Nur Rohrmasse je Arm |','|---|---:|---|---:|']
for v in variants:lines.append(f"| [{v['id']} – {v['title']}]({v['id']}.png) | {v['count']} | Ø{v['od']}/{v['di']} mm | {v['tube_mass_assumed_kg']*1000:.1f} g |")
lines+=['','Rohrmassen beruhen auf den angenommenen Zuschnittkoordinaten und1600kg/m³. **Keine Gesamtmassen-Rangfolge:** Aluminiumknoten, Klemmkappen, Schrauben, Isolierung und Verbindungsmaterial sind noch nicht volumetrisch geschlossen. Weniger Klemmstellen sind ein Gewichtsargument, aber kein Festigkeitsnachweis.','',
f'Die bisherige separate D05-Motorplatte wiegt {baseline*1000:.1f}g je Motor beziehungsweise {4*baseline:.3f}kg für vier Motoren. Ihr Entfall ist eine Brutto-Entnahme; neue integrierte Knoten müssen gegengerechnet werden. Die bisherigen Endschotte sollen durch die direkten Knoten ebenfalls entfallen, sind jedoch nicht als zusätzliche gesicherte Nettoersparnis angesetzt.','',
'## Warum ein einzelnes Rohr nicht automatisch genügt','',
'Vergleichsfall:420mm idealisierter Kragarm,400N Querlast,20Nm Torsionsmoment, angenommener Biegemodul70GPa und Schubmodul5GPa. Diese Lasten und Materialwerte sind Annahmen. Keine Sicherheitsfaktoren und kein Laminat-/Verbindungsnachweis.','',
'| Einzelrohr | Biegespannung | Durchbiegung | Verdrehung |','|---|---:|---:|---:|']
for c in cases:lines.append(f"| Ø{c['od_mm']}/{c['id_mm']} mm | {c['bending_stress_MPa']:.0f} MPa | {c['tip_deflection_mm']:.1f} mm | {c['twist_deg']:.1f}° |")
lines+=['',
'Der größere Einzelquerschnitt wiegt pro Meter weniger als zwei Ø20/17-Rohre zusammen und hat deutlich mehr Eigen-Biegesteifigkeit als ein einzelnes Ø20/17-Rohr. Ob er insgesamt am leichtesten ist und ausreichend trägt, bleibt offen: zulässige Laminatspannungen, Mindeststeifigkeit, Dauer-/Spitzenlasten, CFK-Klemmpressung und Knotenmasse fehlen. Die bestehende Ø20/17-Ausführung wird als einzelner langer Arm durch diesen Vergleich nicht freigegeben.','',
'## Auswahlregel zugunsten des Gesamtgewichts','',
'Zuerst V1 mit tatsächlich verfügbarem, geeignetem Laminat und leichten Knoten auslegen. Wenn Last/Steifigkeit nicht geschlossen werden, V2/V3 mit zwei vorhandenen Rohren vergleichen. V4 nur bei belegtem Nutzen des dritten Rohrs; V5 als Rückfalloption bei zusätzlichem Bedarf. Die größere Zahl Rohre ist kein automatischer Stabilitätsnachweis. Vollständige Materialmassen, Verbindungsmassen und Belastbarkeit gemeinsam bewerten.','',
'Die Visualisierungen sind KI-generierte Gestaltungsvorschläge und nicht maßstäblich. Schrauben, Aufnahmen und Radien sind bildlich dargestellt, nicht aus einem nachgewiesenen parametrischen CAD-Modell abgeleitet. Das nominale Motor-Anschlussbild4×M6/PCD50 stammt aus der alten Projektzeichnung und ist nicht OEM-bestätigt; gezeichnete Schraubenköpfe sind keine verbindliche Montagezeichnung. Maßgeblich für die geometrischen Rechenannahmen sind Varianten.json und die gespeicherten Prompts. Die größeren Rohrdurchmesser von V1 brauchen einen neuen Artikel und eine neue CFK-Klemmung; die alten Ø20/17-Verbinder passen dort nicht. Keine Produktions- oder Flugfreigabe; der bekannte Rotor-/Rahmenkonflikt aus D06 wird hierdurch nicht als gelöst behauptet.','']
(H/'README.md').write_text('\n'.join(lines));print('Tube mass comparison and conditional single-tube screening written')
