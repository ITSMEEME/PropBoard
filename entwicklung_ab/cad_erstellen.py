"""A/B development CAD: exact P14 parts + proposed frame/guard integration.

All dimensions mm. Purchased envelopes and material densities are assumptions.
Native files, component mass registers and explicit rotor-envelope checks.
No strength, containment or OEM compatibility certification.
"""
import sys,math,json,csv,argparse,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path.extend(['/usr/lib/freecad-python3/lib',str(ROOT/'kreis_r04/mn1330_p14')])
import FreeCAD as App,Part,Import
from geometrie import build
from kinematik import derive,solve
V=App.Vector;D=math.pi/180
P=json.loads((H/'parameter.json').read_text())
def box(x,y,z,cx=0,cy=0,cz=0):return Part.makeBox(x,y,z,V(cx-x/2,cy-y/2,cz-z/2))
def cylinder(r,h,z=0,x=0,y=0):return Part.makeCylinder(r,h,V(x,y,z))
def ring(ri,ro,z,h,x=0,y=0):return cylinder(ro,h,z,x,y).cut(cylinder(ri,h+2,z-1,x,y))
def rod(a,b,r):
    a,b=V(*a),V(*b);v=b-a;return Part.makeCylinder(r,v.Length,a,v)
def tube(a,b,outer=30,wall=2):
    a,b=V(*a),V(*b);v=b-a;L=v.Length
    s=Part.makeBox(L,outer,outer,V(0,-outer/2,-outer/2)).cut(Part.makeBox(L+2,outer-2*wall,outer-2*wall,V(-1,-outer/2+wall,-outer/2+wall)))
    s.Placement=App.Placement(a,App.Rotation(V(1,0,0),v));return s
def fuse(shapes):
    s=shapes[0]
    for x in shapes[1:]:s=s.fuse(x)
    return s.removeSplitter()
def assembly(case,reuse_core=False):
    print('START',case['id'],flush=True)
    cid=case['id'];out=H/'Ausgabe'/cid;out.mkdir(parents=True,exist_ok=True)
    doc=App.newDocument(cid);records=[];shapes=[];rotors=[];statics=[];extras=[];base_rotor_static=[]
    def add(key,label,shape,material='CFK',group='frame',override=None,note='Geometrievorschlag; Last-/Montagenachweis offen',prior_record=None):
        if key.startswith('GRID'):print('Adding',key,len(shape.Solids),flush=True)
        if shape.isNull() or (prior_record is None and (not shape.isValid() or not shape.Solids)):raise ValueError('Invalid shape '+key)
        rho={'CFK':1600,'Aluminium':2810,'Steel':7850,'Reserve':0}.get(material,7850)
        mass=override if override is not None else shape.Volume*rho*1e-9
        obj=doc.addObject('Part::Feature',key);obj.Label=label;obj.Shape=shape
        for k,v in {'Materialannahme':material,'Gruppe':group,'Nachweis':note}.items():obj.addProperty('App::PropertyString',k,'Entwicklung');setattr(obj,k,v)
        obj.addProperty('App::PropertyMass','Rechenmasse','Entwicklung');obj.Rechenmasse=str(mass)+' kg'
        obj.addProperty('App::PropertyString','Massenbasis','Entwicklung');obj.Massenbasis='Kaufteil/Reserve: freie oder dokumentierte Masse' if override is not None else f'CAD-Volumen × angenommene Dichte {rho} kg/m³'
        if prior_record is not None:row=dict(prior_record)
        else:
            cg=sum((s.CenterOfMass*s.Volume for s in shape.Solids),V())/shape.Volume
            row=dict(id=key,label=label,group=group,material=material,mass_kg=mass,volume_mm3=shape.Volume,cg_mm=list(cg),solid_count=len(shape.Solids),mass_override=override is not None,note=note)
        records.append(row);shapes.append((key,shape,group));
        if len(records)%50==0:print('Components',len(records),key,flush=True)
        if group=='new_static':extras.append((key,shape))
        return obj
    R=case['radius_mm'];B=case['blades'];coax=case['type']=='coax';guard_in=R+25;guard_out=R+37
    if coax:
        c=json.loads((H/'configs'/f'{cid}.json').read_text())
        if reuse_core:
            oldreport=json.loads((out/'Pruefung.json').read_text());assert oldreport['all_shapes_valid']
            assert oldreport['native_sha256']==hashlib.sha256((out/(cid+'.FCStd')).read_bytes()).hexdigest(),'Native cache changed'
            oldrows=json.loads((out/'Massendaten.json').read_text());old=App.openDocument(str(out/(cid+'.FCStd')))
            copies=[(r,old.getObject(r['id']).Shape.copy()) for r in oldrows if r['group']=='P14_existing'];App.closeDocument(old.Name)
            for r,s in copies:
                add(r['id'],r['label'],s,r['material'],'P14_existing',r['mass_kg'],r['note'],prior_record=r)
                # A stricter cached check includes ALL inherited components.
                base_rotor_static.append((r['id'],s))
                if 'CFK01' in r['label']:rotors.append((r['id'],s))
        else:
            parts,scene,q=build(c)
            for sign in [1,-1]:
              for row in scene:
                if sign<0 and row['frame']=='shared':continue
                id=row['id'];s=row['shape'].copy()
                if sign>0 and id=='A13':
                    id='A13U';s=parts[id]['shape'].copy();s.rotate(V(),V(1,0,0),row['theta']);s.rotate(V(),V(0,0,1),row['a']);s.translate(V(0,0,row['z']))
                if sign>0 and id in {'A16A','CFK01','F6_ROOT'}:s.rotate(V(0,0,q['level_mm']),V(math.cos(row['a']*D),math.sin(row['a']*D),0),-24)
                if sign<0:s.rotate(V(),V(0,1,0),180)
                t=parts[id];mat=t['material'];rho=(2810 if '7075' in mat else 2700) if 'Aluminium' in mat else (1600 if mat=='CFK' else 2200 if mat=='PTFE' else 7850)
                m=t['mass_override_kg'] if t['mass_override_kg'] is not None else t['shape'].Volume*rho*1e-9
                key=f'P14_{len(records):04d}';add(key,f'{sign:+d} {row["name"]}',s,mat,'P14_existing',m,t['note'])
                if row['frame'] in ['rotor','pitch','pitch_link','swash_rotor']:rotors.append((key,s))
                else:base_rotor_static.append((key,s))
        centres=[[0,0]];motors=2;plane=180;guard_bottom=-220;guard_top=220;topgrid=244;bottomgrid=-244
        deckbottom=291;decktop=299;legbottom=-290
        # Existing shared A29 has four M8 clearance holes on radius 122 at 45 deg.
        for i,ang in enumerate([45,135,225,315]):
            co,si=math.cos(ang*D),math.sin(ang*D)
            pad=Part.makeBox(30,26,12,V(113,-13,-18));pad=pad.cut(cylinder(4.3,14,-19,122,0));pad.rotate(V(),V(0,0,1),ang)
            arm=tube([140*co,140*si,-20],[(R+45)*co,(R+45)*si,-20],50,3)
            elbow=box(24,24,28,140*co,140*si,-24)
            post=ring(13,15,-30,301,(R+45)*co,(R+45)*si)
            # Deck-support beam entirely above the upper rotor and upper touch grid.
            beam=tube([(R+45)*co,(R+45)*si,271],[math.copysign(280,co),math.copysign(150,si),271],40,2.5)
            add(f'ADAPTER_{i}','A29-Alu-Anschlussadapter',fuse([pad,elbow]),'Aluminium','new_static',note='Pad mit Ø8,6 auf bestehendem M8-Kreis; CFK-Rohrklemmung und Lastnachweis offen')
            add(f'CAGE_{i}','Lastpfad A29–Außenpfosten–Deck',fuse([arm,post,beam]),'CFK','new_static',note='CFK-Rohrersatz; metallischer Adapter und M8 separat; Verbindungs-/Laminatdetails offen')
            # A real M8 nominal shank crosses the shared A29 hole; head/washer remain outside it.
            bolt=cylinder(4,30,-18,122*co,122*si).fuse(cylinder(6.5,5,12,122*co,122*si))
            add(f'ATTACH_M8_{i}','A29-Anschluss M8 Nennkontur',bolt,'Steel','new_static',note='M8×30 Nennschaft, Kopfreserve; Gewinde/Sicherung/Vorspannung offen')
        motor_mass_known=True
    else:
        motors=case['motors'];spacing=2*guard_out+P['guard_neighbor_gap_mm'];rc=spacing/(2*math.sin(math.pi/motors));phase=45 if motors==4 else 0
        centres=[[rc*math.cos((phase+360*i/motors)*D),rc*math.sin((phase+360*i/motors)*D)] for i in range(motors)]
        plane=0;guard_bottom=-55;guard_top=55;topgrid=67;bottomgrid=-67;deckbottom=95;decktop=103;legbottom=-290
        chord=max(60,120*math.sqrt(R/710));root=90
        case['chord_mm']=chord;case['blade_root_mm']=root
        # One lightweight closed central tube frame with separate metal joint shoes.
        central=[]
        for y in [-100,100]:central.append(tube([-160,y,-110],[160,y,-110],40,2.5))
        for x in [-160,160]:central.append(tube([x,-100,-110],[x,100,-110],40,2.5))
        add('CENTER_FRAME','Zentralrahmen 40×40×2,5',fuse(central),'CFK','new_static',note='Rohranschlüsse als starrer Ersatz; reale Klemmen und Laminatnachweis offen')
        for i,(x,y) in enumerate(centres):
            a=math.atan2(y,x);ca,sa=math.cos(a),math.sin(a)
            add(f'ARM_{i}',f'CFK-Ausleger {i+1}',tube([135*ca,135*sa,-110],[x,y,-110],40,2.5),'CFK','new_static')
            plate=box(170,170,8,x,y,-86)
            for az in [0,90,180,270]:plate=plate.cut(cylinder(3.3,10,-91,x+25*math.cos(az*D),y+25*math.sin(az*D)))
            add(f'MOUNT_{i}','Motorträger 170×170×8, PCD50-Annahme',plate,'Aluminium','new_static',note='4×Ø6,6 auf PCD50 als Platzhalter; neuer Motor noch nicht ausgewählt')
            motor=cylinder(75,66,-82,x,y)
            add(f'MOTOR_{i}','Motorbauraum Ø150×66, neuer Typ offen',motor,'Reserve','motor',2.75,'2,75 kg freie Masseannahme; kein ausgewählter Motor, keine bestätigte Dauerkennlinie oder Montage')
            add(f'HUB_{i}','Rotornabe Nennkörper',cylinder(45,20,-16,x,y),'Aluminium','rotor',note='Anschluss-, Lager- und Blattwurzelkonstruktion noch offen')
            # Symmetric NACA-like closed section, solid geometric shell surrogate.
            for k in range(B):
                wires=[]
                for rr in [root,R]:
                    pts=[]
                    for sg,js in [(1,range(25)),(-1,range(23,0,-1))]:
                        for j in js:
                            u=(1-math.cos(math.pi*j/24))/2;z=sg*5*.12*chord*(.2969*math.sqrt(max(u,0))-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)
                            pts.append(V(rr,(u-.25)*chord,z))
                    wires.append(Part.Wire(Part.makePolygon(pts+[pts[0]]).Edges))
                s=Part.makeLoft(wires,True,True);s.rotate(V(),V(1,0,0),14);s.rotate(V(),V(0,0,1),k*360/B);s.translate(V(x,y,0))
                # Thin laminate + root/spar allowance, explicitly not a designed layup.
                blade_mass=(R-root)*chord*2*1.2e-9*1600+.12
                key=f'BLADE_{i}_{k}';add(key,f'Profilblatt {B}-Blatt-Referenz, Schalenmasse geschätzt',s,'CFK','rotor',blade_mass,'Vollprofil als äußere Hülle, 2×1,2mm Schalenmasse +120g Wurzel/Spar; Laminat und Hubanschluss offen');rotors.append((key,s))
                grip=Part.makeBox(67,48,16,V(38,-24,-8));grip.rotate(V(),V(1,0,0),14);grip.rotate(V(),V(0,0,1),k*360/B);grip.translate(V(x,y,0));grip=grip.cut(s)
                add(f'GRIP_{i}_{k}','Nabensteg mit formgleichem Blattwurzel-Nennsitz',grip,'Aluminium','rotor',note='Geometrische Lastpfadreserve Nabe–Blatt; Teilung, Bolzen, CFK-Klemmdruck, Fliehkraft und Ermüdung offen')
            add(f'ESC_{i}','ESC-Platzhalter 120×65×22',box(120,65,22,x*.55,y*.55,-149),'Reserve','electronics',2/motors*.65,'Massenbudget; Strom, Spannung, Kühlung und Befestigung offen')
        for j,(x,y) in enumerate([(x,y) for x in [-120,120] for y in [-70,70]]):
            add(f'DECK_POST_{j}','Zentrale Deckstütze',tube([x,y,-110],[x,y,80],25,2),'CFK','new_static')
            add(f'DECK_PAD_{j}','Deckauflage',box(40,40,5,x,y,92.5),'Aluminium','new_static')
        # Two parallel transverse beams join the deck posts below the deck plate.
        for j,y in enumerate([-70,70]):add(f'DECK_BEAM_{j}','Deckquerträger',tube([-160,y,80],[160,y,80],30,2),'CFK','new_static')
        motor_mass_known=False
    # Protective rings with explicitly modelled touch mesh; NOT blade containment.
    for i,(x,y) in enumerate(centres):
        for suffix,z in [('LOW',guard_bottom),('HIGH',guard_top)]:add(f'RING_{i}_{suffix}','Schutzring 12×12 Nennquerschnitt',ring(guard_in,guard_out,z-6,12,x,y),'CFK','new_static')
        for j,a in enumerate(range(0,360,45)):
            xx=x+(R+31)*math.cos(a*D);yy=y+(R+31)*math.sin(a*D)
            add(f'GUARD_POST_{i}_{j}','Ringdistanzrohr Ø12×1,5 bis Gitterlagen',ring(4.5,6,bottomgrid-1.25,topgrid-bottomgrid+2.5,xx,yy),'CFK','new_static')
        # Complete circular mesh grids at 30-mm pitch, two non-overlapping layers.
        for suffix,z in [('TOP',topgrid),('BOTTOM',bottomgrid)]:
            print('Build grid',i,suffix,flush=True)
            wires=[]
            for k in range(-int(guard_out/30),int(guard_out/30)+1):
                off=k*30;span=math.sqrt(max(0,(guard_out-3)**2-off**2)) if abs(off)<guard_out-3 else 0
                if span<5:continue
                for axis in [0,1]:
                    zz=z+(.65 if axis else -.65)
                    a=[x-span,y+off,zz] if axis==0 else [x+off,y-span,zz]
                    b=[x+span,y+off,zz] if axis==0 else [x+off,y+span,zz]
                    w=rod(a,b,.6)
                    # Motor/central mechanics need a bounded cutout in the lower mesh.
                    if suffix=='BOTTOM':w=w.cut(cylinder(135 if coax else 82,10,z-5,x,y))
                    if not w.isNull() and w.Solids:wires.append(w)
            print('Compound grid',len(wires),flush=True)
            grid=Part.Compound(wires)
            print('Compound built',flush=True)
            add(f'GRID_{i}_{suffix}','Drahtgitter Ø1,2 / 30 mm, Ausschnitt unten',grid,'Steel','new_static',note='Nennvolumen aus Drahtsegmenten; Befestigung, Maschenverformung, Durchgriff- und Fragmentrückhalt nicht nachgewiesen')
        side=[]
        count=math.ceil(2*math.pi*(R+31)/30)
        for j in range(count):
            a=2*math.pi*j/count;xx=x+(R+31)*math.cos(a);yy=y+(R+31)*math.sin(a)
            side.append(rod([xx,yy,guard_bottom+6],[xx,yy,guard_top-6],.6))
        for z in range(int(guard_bottom+20),int(guard_top-10),30):side.append(ring(R+30.4,R+31.6,z,1.2,x,y))
        add(f'GRID_{i}_SIDE','Seitliches Berührungsgitter',Part.Compound(side),'Steel','new_static',note='Nenn-Drahtgitter; Kreuzungen nicht verschweißt modelliert, kein Containmentnachweis')
        # Three small outriggers connect guard lower ring to motor/central frame outside rotor space.
        if not coax:
            for j,a in enumerate([0,120,240]):
                xx=x+(R+31)*math.cos(a*D);yy=y+(R+31)*math.sin(a*D)
                support=fuse([tube([x,y,-112],[xx,yy,-112],16,1.5),tube([xx,yy,-112],[xx,yy,guard_bottom],16,1.5)])
                add(f'GUARD_ARM_{i}_{j}','Schutzringausleger unter Rotor',support,'CFK','new_static')
    # Payload deck / battery / electronics are carried as separate mass categories.
    deck=box(620,360,8,0,0,(deckbottom+decktop)/2)
    add('DECK','Personendeck 620×360×8, Voll-CFK-Ersatz',deck,'CFK','new_static',note='Vollplatten-Ersatz; Auflagen, Rutschbelag, Laminat, Decklast und Rückhalt offen')
    if coax:
        # Two symmetric 6-kg packs in the stationary space BETWEEN rotor planes.
        # No shaft passes through a motor and no hanger crosses a rotor disc.
        battery_size=[300,200,39];battery_z=6;floor_z=-15.5
        for j,sg in enumerate([-1,1]):
            add(f'BATTERY_{j}','Batteriebauraum 6 kg, symmetrisch im Zwischenraum',box(*battery_size,sg*450,0,battery_z),'Reserve','battery',6,'Je 1,32kWh angenommen; Packtyp, Temperatur, Strom und Auftriebsabschattung offen')
            add(f'BATTERY_TRAY_{j}','Batteriewanne 2mm Alu',box(316,216,2,sg*450,0,floor_z),'Aluminium','new_static')
            for k,y in enumerate([-180,180]):add(f'BATT_RAIL_{j}_{k}','Batterieschiene im Zwischenraum',tube([sg*180,y,-26.5],[sg*620,y,-26.5],20,2),'CFK','new_static')
            for k,x in enumerate([330,570]):add(f'BATT_CROSS_{j}_{k}','Batteriequerträger im Zwischenraum',tube([sg*x,-180,-26.5],[sg*x,180,-26.5],20,2),'CFK','new_static')
    else:
        battery_z=-193;battery_size=[300,220,90]
        add('BATTERY','Batteriebauraum, 12 kg / 2,64 kWh angenommen',box(*battery_size,0,0,battery_z),'Reserve','battery',12,'Packtyp, tatsächliche Masse/Kapazität, Strom, Kühlung und Halterung offen')
        floor_z=battery_z-battery_size[2]/2-2
        add('BATTERY_TRAY','Batteriewanne 2mm Alu',box(battery_size[0]+16,battery_size[1]+16,2,0,0,floor_z),'Aluminium','new_static')
        for j,(x,y) in enumerate([(x,y) for x in [-140,140] for y in [-100,100]]):
            add(f'BATTERY_HANGER_{j}','Batteriewannen-Halter',tube([x,y,-110],[x,y,floor_z],16,1.5),'CFK','new_static')
    add('ELECTRONICS','Restelektronik-/Kabelbudget',box(120,90,25,0,0,deckbottom-20),'Reserve','electronics',2 if coax else 2*.35,'Elektronik insgesamt 2kg einschließlich ESC-Reservemassen; Stecker/Kabel/Kühlung noch unbestimmt')
    # Landing gear joins central frame (classic) or the battery support structure (coax).
    for i,sg in enumerate([-1,1]):
        y=sg*240
        add(f'SKID_{i}','Kufenrohr 30×30×2',tube([-360,y,legbottom+15],[360,y,legbottom+15],30,2),'CFK','new_static')
        for j,x in enumerate([-250,250]):
            if coax:
                ex=math.copysign((R+45)/math.sqrt(2),x);ey=sg*(R+45)/math.sqrt(2)
                leg=fuse([tube([x,y,legbottom+30],[ex,ey,legbottom+30],22,2),ring(9,11,legbottom+30,-30-(legbottom+30),ex,ey)])
            else:leg=tube([x,y,legbottom+30],[x,sg*100,-110],22,2)
            add(f'LEG_{i}_{j}','Kufenstütze außerhalb Rotor oder darunter',leg,'CFK','new_static')
    print('Saving',len(records),'components',flush=True)
    doc.recompute();native=out/(cid+'.FCStd');doc.saveAs(str(native))
    print('Native saved',flush=True)
    # A compact STEP contains the complete new frame plus rotor/motor references.
    frame_objects=[doc.getObject(r['id']) for r in records if r['group']!='P14_existing']
    Import.export(frame_objects,str(out/(cid+'_Rahmen.step')))
    # A complete STEP is intentionally not duplicated for the P14 inherited assembly.
    with (out/'Stueckliste.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,list(records[0]));w.writeheader();w.writerows(records)
    bb=Part.Compound([s for _,s,_ in shapes]).BoundBox
    total=sum(r['mass_kg'] for r in records)+P['payload_kg']
    sums={g:sum(r['mass_kg'] for r in records if r['group']==g) for g in set(r['group'] for r in records)}
    # True planar swept radius from each blade's surface vertices (not nominal R).
    if coax:
        blade_shapes=[s for key,s,g in shapes if 'CFK01' in next(r['label'] for r in records if r['id']==key)]
        tip_swept=max(math.hypot(v.Point.x,v.Point.y) for s in blade_shapes for v in s.Vertexes)
    else:tip_swept=max(math.hypot(v.Point.x-centres[int(key.split('_')[1])][0],v.Point.y-centres[int(key.split('_')[1])][1]) for key,s in rotors for v in s.Vertexes)
    radial_clear=guard_in-tip_swept
    # Conservative full swept blade region including deflection and tolerance.
    zpad=P['rotor_tip_deflection_allowance_mm']+P['geometry_tolerance_allowance_mm']
    chord=120 if coax else case['chord_mm'];halfz=.75*chord*math.sin(20*D)+.06*chord+zpad
    swept=[]
    for i,(x,y) in enumerate(centres):
        for z in ([180,-180] if coax else [0]):swept.append((i,z,ring((177 if coax else 90)-3,tip_swept+zpad,z-halfz,2*halfz,x,y)))
    clearance=[]
    for key,s in extras:
        for site,z,env in swept:
            if not s.BoundBox.intersect(env.BoundBox):continue
            vol=s.common(env).Volume
            if vol>.1:clearance.append(dict(component=key,rotor_site=site,rotor_z=z,envelope_intersection_mm3=vol))
    # Also expose direct static interference with inherited P14 components.
    inherited=[]
    if coax:
        for key,s in extras:
            for old,os in base_rotor_static:
                if not s.BoundBox.intersect(os.BoundBox):continue
                vol=s.common(os).Volume
                if vol>.1:inherited.append(dict(new=key,existing=old,volume_mm3=vol,existing_label=next(r['label'] for r in records if r['id']==old)))
    # New tube joints intentionally intersect geometrically; all non-rotor interfaces still need detailed joints.
    report=dict(case=case,body_count=len(records),solid_count=sum(r['solid_count'] for r in records),all_shapes_valid=all(s.isValid() for _,s,g in shapes if not(reuse_core and g=='P14_existing')),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),mass_categories_kg=sums,total_mass_with_payload_kg=total,dry_without_battery_electronics_payload_kg=total-114,mass_complete=False,motor_mass_verified=motor_mass_known,bounds_mm=[bb.XLength,bb.YLength,bb.ZLength],bounds_min_mm=[bb.XMin,bb.YMin,bb.ZMin],bounds_max_mm=[bb.XMax,bb.YMax,bb.ZMax],envelope_pass=bb.XLength<=2100 and bb.YLength<=1700 and bb.ZLength<=600,tip_swept_radius_mm=tip_swept,guard_inner_radius_mm=guard_in,radial_clearance_mm=radial_clear,radial_reserve_after_18mm_mm=radial_clear-zpad,swept_half_height_mm=halfz,rotor_envelope_intersections=clearance,new_vs_inherited_static_intersections=inherited,centres_mm=centres,guard_containment_verified=False,frame_joints_detailed=False,scope='Volume-based frame/mass and swept geometric screening. Material allowables, OEM interfaces, all joints, mesh fixation, payload restraint and fatigue unresolved.')
    (out/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));(out/'Massendaten.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in report.items() if k not in ['rotor_envelope_intersections','new_vs_inherited_static_intersections']},ensure_ascii=False),flush=True)
    print('Rotor intersections',len(clearance),'inherited static intersections',len(inherited),flush=True)
    App.closeDocument(doc.Name);return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case');ap.add_argument('--reuse-core',action='store_true');args=ap.parse_args()
    for case in P['cases']:
        if args.case and args.case!=case['id']:continue
        try:assembly(case,args.reuse_core)
        except BaseException:
            import traceback
            traceback.print_exc();raise
