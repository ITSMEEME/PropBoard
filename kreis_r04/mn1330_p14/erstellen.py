#!/usr/bin/env python3
"""P14 CAD, exact baseline mass properties and animation-neutral export."""
import argparse,csv,hashlib,json
from pathlib import Path
from geometrie import *
import Import,MeshPart
def dump(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=H/'parameter.json');ap.add_argument('--output',type=Path,default=H/'Ausgabe');ap.add_argument('--no-step',action='store_true');args=ap.parse_args();O=args.output;O.mkdir(exist_ok=True,parents=True)
    c=json.loads(args.config.read_text());p,scene,q=build(c);print('Geometrie aufgebaut',len(p),len(scene),flush=True)
    for f in ['STEP_Sonderteile','STEP_Referenzen','STL_Nenngeometrie']:(O/f).mkdir(exist_ok=True)
    for f in ['STEP_Sonderteile','STEP_Referenzen','STL_Nenngeometrie']:
        for old in (O/f).iterdir():
            if old.stem not in p:old.unlink()
    d=A.newDocument('P14_MN1330_Leichtbau');data=[];props={};meshes={};bodyobjects=[];bom=[]
    for id,t in p.items():
        s=t['shape'];solid=s.Solids[0];mat=t['material'];rho=(2810 if '7075' in mat else 2700) if 'Aluminium' in mat else (c['operating']['cfk_density_assumed_kg_m3'] if mat=='CFK' else 2200 if mat=='PTFE' else 7850)
        m=t['mass_override_kg'] if t['mass_override_kg'] is not None else s.Volume*rho*1e-9
        J=solid.MatrixOfInertia;cg=solid.CenterOfMass;factor=m/s.Volume*1e-6
        inertia=[[getattr(J,'A'+str(i+1)+str(j+1))*factor for j in range(3)] for i in range(3)]
        props[id]={k:v for k,v in t.items() if k!='shape'}|dict(volume_mm3=s.Volume,mass_kg=m,cg_mm=list(cg),inertia_cg_kgm2=inertia,density_assumed_kg_m3=rho,bbox_mm=[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength])
        folder='STEP_Referenzen' if t['kind'].startswith('Norm') or t['kind'] in ['Motor','Servo','Anschlussreserve'] else 'STEP_Sonderteile'
        s.exportStep(str(O/folder/(id+'.step')))
        mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.6,AngularDeflection=.35,Relative=False);vv,ff=mesh.Topology
        meshes[id]=dict(vertices_mm=[[v.x,v.y,v.z] for v in vv],triangles=ff)
        if t['kind']=='Sonderteil':mesh.write(str(O/'STL_Nenngeometrie'/(id+'.stl')))
    for unit,centre in enumerate(q['unit_centres_mm']):
        for sign,label in [(1,'Oben'),(-1,'Unten')]:
            for idx,row in enumerate(scene):
                if row['frame']=='shared' and sign<0:continue
                id=row['id'];s=row['shape'].copy();index=0
                root_parts={'A16A','CFK01','F6_ROOT'}
                if sign>0 and id=='A13':
                    id='A13U';s=p[id]['shape'].copy();s.rotate(V(),V(1,0,0),row['theta']);s.rotate(V(),V(0,0,1),row['a']);s.translate(V(0,0,row['z']))
                if sign>0 and id in root_parts:
                    index=-24
                    axis=V(math.cos(row['a']*D),math.sin(row['a']*D),0)
                    s.rotate(V(0,0,q['level_mm']),axis,index)
                t=p[id];local=s.copy()
                if sign<0:s.rotate(V(),V(0,1,0),180)
                s.translate(V(*centre))
                name=f'U{unit+1}_{label}_{row["name"]}'
                o=d.addObject('Part::Feature','Teil_'+str(len(bodyobjects)));o.Label=name;o.Shape=s
                for field,val in dict(BauteilID=id,Werkstoff=t['material'],Fertigung=t['kind'],Hinweis=t['note'],Bewegungsgruppe=row['frame'],Freigabe='ENTWICKLUNG_KEINE_PRODUKTIONSFREIGABE').items():o.addProperty('App::PropertyString',field,'P14');setattr(o,field,val)
                bodyobjects.append(o)
                # Template -> neutral pod shape is a rigid placement, never geometry scaling.
                rel=local.Placement.multiply(t['shape'].Placement.inverse());mat=rel.toMatrix()
                values=[getattr(mat,'A'+str(i)+str(j)) for i in range(1,5) for j in range(1,5)]
                rec={k:v for k,v in row.items() if k!='shape'}|dict(name=name,unit=unit,sign=sign,root_mount_index_deg=index,neutral_transform=values,part=id,native_object=o.Name)
                data.append(rec);bom.append(dict(instanz=name,id=id,material=t['material'],masse_kg=props[id]['mass_kg'],status='NICHT_PRODUKTIONSFREIGEGEBEN'))
    d.recompute();native=O/'P14_MN1330_Leichtbau.FCStd';d.saveAs(str(native));print('Native Baugruppe gespeichert',len(bodyobjects),flush=True)
    if not args.no_step:Import.export(bodyobjects,str(O/'P14_MN1330_Leichtbau.step'));print('Gesamt-STEP gespeichert',flush=True)
    with (O/'Stueckliste.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(bom[0]),delimiter=';');w.writeheader();w.writerows(bom)
    mass=sum(r['masse_kg'] for r in bom);cfk=sum(r['masse_kg'] for r in bom if r['material']=='CFK');alu=sum(r['masse_kg'] for r in bom if 'Aluminium' in r['material'])
    totals=dict(dry_cad_mass_assumed_kg=mass,cfk_assumed_kg=cfk,aluminium_assumed_kg=alu,motor_masses_assumed=False,motor_mass_source=c['operating'].get('motor_mass_source','Nutzerangabe'),bearing_masses_assumed=True,servo_mass_source='ROBOTIS855g PH54-200',total_scenario_mass_kg=mass+c['operating']['payload_kg']+c['operating']['battery_mass_assumed_kg']+c['operating']['electronics_mass_assumed_kg'],scope='CAD-Struktur inkl dokumentierter Motor-/Servo-Massen und Lagerannahmen; Schrauben, reale Kabel, Akkugehäuse und Personendeck nicht vollständig enthalten; keine gewogene Fahrzeugmasse')
    report=dict(revision='P14',production_ready=False,body_count=len(bodyobjects),type_count=len(p),native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),all_valid=all(o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.Volume>0 for o in bodyobjects),outer_frame_removed=True,tip_support_removed=True,actuator_belt_spindles_removed=True,mass=totals,limitations=['CFK- und Ermuedungsnachweise offen','Servo Original-STEP nicht erreichbar; Nennmassmodell, Horn-/Montagebezug offen','MN1330:3400W für180s;16270W-Prüfpunkt ohne Haltedauer; Sonderrotor-/Dauerbetrieb nicht belegt','Alu-Verbindungsmittel und Gewindetiefen muessen real ausgelegt werden','Keine Personen-/Flugfreigabe'])
    dump(O/'Pruefung.json',report);dump(O/'Teile.json',list(props.values()));dump(O/'Szenengraph.json',data);dump(O/'Eingaben.json',c);dump(O/'Abgeleitet.json',q);dump(O/'Meshes.json',meshes)
    model=dict(config=c,derived=q,types=props,scene=data,mass=totals,source_native_sha256=report['native_sha256'],production_ready=False)
    dump(O/'Modell.json',model);(O/'modell.js').write_text('globalThis.P14_MODEL='+json.dumps(model,ensure_ascii=False,separators=(',',':'))+';\n');(O/'mesh.js').write_text('globalThis.P14_MESH='+json.dumps(meshes,separators=(',',':'))+';\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
