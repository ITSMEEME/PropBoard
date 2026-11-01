#!/usr/bin/env python3
"""Supplier inquiry drawings, material/size screening and an auditable file index."""
import argparse,csv,hashlib,html,json,math,sys,textwrap
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
import TechDraw

def dump(name,value):(O/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def screen(types,config,report):
    subtotal=0;unknown=[];by_type=[];cfk_nominal=0
    for t in types:
        material=t['material'];rho=None
        if not t['reference']:
            if '6082' in material:rho=2700
            elif '7075' in material:rho=2810
            elif any(v in material for v in ['42CrMo4','100Cr6','DC01','C45']):rho=7850
            elif '1.4310' in material:rho=7900
        volume=t['volume_mm3']*t['count']
        if rho:
            mass=volume*1e-9*rho;subtotal+=mass;by_type.append(dict(id=t['id'],count=t['count'],assumed_density_kg_m3=rho,mass_kg=mass))
        else:
            unknown.append(dict(id=t['id'],material=material,reference=t['reference'],reason='Lieferteilmasse oder freigegebene Werkstoff-/Laminatdichte fehlt'))
        if 'CFK' in material:cfk_nominal+=volume*1e-9*1600
    p=config['parameters'];m=config['mechanics'];F=p['total_mass_kg']*9.80665*p['load_factor'];per_blade=F/(2*p['blade_count'])
    rpm=p['rpm'];omega=rpm*math.pi/30;blade_span=(p['rotor_radius']-p['blade_root'])/1000
    # Screening, no invented manufacturer allowables or CFK certification.
    d,D,L=.026,.030,.61;I=math.pi*(D**4-d**4)/64;E=35e9
    pcr=math.pi**2*E*I/L**2
    bb=report['bounding_box_mm'];limits=dict(x=2100,y=1700,z=600)
    return dict(design_load_scenario=dict(total_mass_kg=p['total_mass_kg'],rpm=rpm,assumed_load_factor=p['load_factor'],total_thrust_case_N=F,uniform_thrust_case_per_blade_N=per_blade),
       identified_manufactured_metal_mass_kg=subtotal,cfk_solid_volume_mass_if_1600kg_m3_kg=cfk_nominal,
       mass_scope='Vollmetallkörper mit zuordenbarer angenommener Nenndichte; keine vollständige Fahrzeugmasse; Normteilmassen/Kabel/Elektronik/Akku/Laminat offen',
       minimum_with_100kg_person_kg=subtotal+100,exceeds_150kg_even_without_unknown_parts=subtotal+100>150,
       identified_metal_parts=sorted(by_type,key=lambda r:r['mass_kg'],reverse=True),unknown_masses=unknown,
       vehicle_limits_mm=limits,actual_box_mm=bb,dimension_targets_met={k:bb[k]<=limits[k] for k in limits},
       actuator_screen=dict(force_case_N=500,speed_case_m_s=.1,mechanical_power_minimum_W=50,screw_lead_mm=4,assumed_efficiency=.9,torque_case_Nm=500*.004/(2*math.pi*.9),speed_rpm=1500,
           interpretation='Anforderungs-/Wirkungsgradfall, keine geprüfte Dauerleistung eines Produkts'),
       cfk_brace_buckling_case=dict(tube_mm='30×26',length_m=L,E_assumed_Pa=E,pinned_euler_N=pcr,interpretation='Idealisierter beidseitig gelenkiger gerader Stab; kein orthotroper, Imperfektions-, Knoten- oder Drucknachweis'),
       manufacturing_release=False,flight_release=False)

def drawing(t,path):
    folder='STEP_Nennkonturen' if t['reference'] else 'STEP_Sonderteile'
    s=Part.read(str(O/folder/(t['id']+'.step')))
    bb=s.BoundBox;s.translate(-bb.Center);dims=[bb.XLength,bb.YLength,bb.ZLength]
    views=[('Draufsicht',A.Vector(0,0,1),(dims[0],dims[1])),('Vorderansicht',A.Vector(0,-1,0),(dims[0],dims[2])),('Seitenansicht',A.Vector(1,0,0),(dims[1],dims[2]))]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">',
         '<rect width="420" height="297" fill="white"/><style>text{font-family:DejaVu Sans,sans-serif;fill:#142c3d}path,line,circle,ellipse{vector-effect:non-scaling-stroke}</style>',
         '<rect x="8" y="8" width="404" height="281" fill="none" stroke="#223b4b" stroke-width=".3"/>',
         f'<text x="14" y="19" font-size="6">{html.escape(t["id"])} · {html.escape(t["name"])}</text>',
         '<text x="14" y="27" font-size="3.5" fill="#a13e26">ANFRAGEZEICHNUNG · Nenngeometrie · keine Fertigungsfreigabe</text>']
    for i,(title,direction,span) in enumerate(views):
        cx=76+i*134;cy=96;scale=min(112/max(span[0],1),100/max(span[1],1),4)
        projected=TechDraw.projectToSVG(s,direction)
        svg.append(f'<text x="{cx}" y="39" text-anchor="middle" font-size="4">{title}</text>')
        svg.append(f'<g transform="translate({cx},{cy}) scale({scale})" stroke="#142c3d" stroke-width=".2" fill="none">{projected}</g>')
        svg.append(f'<text x="{cx}" y="157" text-anchor="middle" font-size="3.5">Hülle {span[0]:.3f} × {span[1]:.3f} mm · Maßstab {scale:.3g}:1</text>')
    lines=[f"Menge: {t['count']} · Werkstoff: {t['material']}",f"Verfahren: {t['process']}","Merkmale: "+t['features'],"Offen: "+t['open'],
           'Unbemaßte Längen ISO2768-1m als Anfragebasis; Funktionspassungen separat nach ISO286.',
           'Geometrische GPS-Toleranzen/Bezüge nach ISO22081 mit Fertiger abstimmen. STEP enthält Nennmaße.',
           'Datum01.11.2026 · P13 · Herkunft/Normfamilie und Grenzen siehe Stückliste und Anfrageunterlagen.']
    y=174
    for line in lines:
        for text in textwrap.wrap(line,125):
            svg.append(f'<text x="14" y="{y}" font-size="3.1">{html.escape(text)}</text>');y+=5
    svg.append('</svg>');path.write_text('\n'.join(svg))

def main():
    global O
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=O);O=ap.parse_args().output
    types=json.loads((O/'Teile.json').read_text());config=json.loads((O/'Eingaben.json').read_text());report=json.loads((O/'Pruefung.json').read_text())
    native=O/'P13_Mechanik.FCStd';assert report['native_sha256']==hashlib.sha256(native.read_bytes()).hexdigest()
    dump('Lastscreen.json',screen(types,config,report))
    chosen=[t for t in types if t['id'].startswith('P13-') and not t['reference'] and not any(v in t['id'] for v in ['CFK30-STREBE','DISTANZ','GELENKDISTANZ','BUCHSE','DRUCKHUELSE'])]
    drawings=[]
    for t in chosen:
        target=O/'Zeichnungen_RFQ'/(t['id']+'.svg');drawing(t,target);drawings.append(dict(id=t['id'],file='Zeichnungen_RFQ/'+target.name))
    dump('Zeichnungsindex.json',drawings)
    cuts=json.loads((O/'Abgeleitet.json').read_text()).get('additional_cfk_cuts',[])
    with (O/'CFK30_Zuschnitt.csv').open('w',encoding='utf-8-sig',newline='') as f:
        if cuts:
            w=csv.DictWriter(f,fieldnames=list(cuts[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(cuts)
    rows=[];bydrawing={r['id']:r['file'] for r in drawings}
    for t in types:
        folder='STEP_Nennkonturen' if t['reference'] else 'STEP_Sonderteile'
        link=f'{folder}/{t["id"]}.step';draw=bydrawing.get(t['id'])
        rows.append('<tr>'+''.join('<td>'+html.escape(str(t.get(k,'')))+'</td>' for k in ['id','name','count','material','process'])+f'<td><a href="{link}">STEP</a>'+ (f' · <a href="{draw}">Anfrageansicht</a>' if draw else '')+'</td></tr>')
    body='''<!doctype html><html lang="de"><meta charset="utf-8"><title>P13 · technische Anfrage</title><style>body{font:15px system-ui;margin:32px;color:#142c3d}table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ccd5db;text-align:left}aside{padding:16px;background:#fff0d9}</style><h1>P13 · mechanischer Anfrageentwurf</h1><aside>Technische Prüfung und Angebote. Keine Bestell-, Fertigungs- oder Flugfreigabe. Normteil-Nennkonturen sind keine Hersteller-CADs.</aside><p><a href="P13_Mechanik.FCStd">FreeCAD</a> · <a href="P13_Mechanik.step">Gesamt-STEP</a> · <a href="Stueckliste.csv">Stückliste</a> · <a href="RFQ_Sonderteile.csv">Dienstleisterliste</a> · <a href="Pruefung.json">Geometrieprüfung</a> · <a href="Kinematik_Pruefung.json">Kinematik</a> · <a href="Lastscreen.json">Bauraum-/Lastscreen</a></p><table><thead><tr><th>ID</th><th>Teil</th><th>Menge</th><th>Werkstoff</th><th>Verfahren</th><th>Dateien</th></tr></thead><tbody>'''+''.join(rows)+'</tbody></table></html>'
    (O/'Anfrageindex.html').write_text(body)
    print(json.dumps(dict(drawings=len(drawings),types=len(types),lastscreen=str(O/'Lastscreen.json')),ensure_ascii=False))
if __name__=='__main__':main()
