from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
D=A.openDocument(str(O/'Quad_Reglerhalter_Landefuesse.FCStd'));raw=(R/'quad_r380_d10/Ausgabe/projekt.js').read_text();data=json.loads(raw[len('globalThis.QD_MODEL='):].strip().rstrip(';'));new=json.loads((O/'Viewer_Komponenten.json').read_text());spec=json.loads((O/'Regler_Montage.json').read_text());data['native_sha256']=spec['native_sha256'];data['esc_configurations']=spec['configurations'];data['esc_reference_only']=True;data['esc_catalog']=spec.get('ESC_catalog');data['landing_configurations']=spec['configurations'];data['rotor_checks']['source_native_sha256']=data['rotor_checks']['native_sha256']
if (O/'V200A24S_Integration.json').exists():
 integration=json.loads((O/'V200A24S_Integration.json').read_text())
 if integration['native_sha256']==spec['native_sha256']:data['esc_integration']=integration
for r in new:
 obj=D.getObject(r['id']);shape=obj.Shape;key=r['id'];row=dict(r)
 if r['role'] in ['hardware','planned_device_bolt']:
  if obj.TypeId=='App::Link':
   tag=next((t for t in ['BoltM4','NutM4','WasherM4','WasherM3','BoltM3','NutM3'] if r['label'].startswith(t+'_')),None)
   if tag:
    key={'BoltM4':'Klemmung_Bolt','NutM4':'Klemmung_Nut','WasherM4':'Klemmung_Washer','WasherM3':'ISO7089_M3','BoltM3':'ESC_ISO4762_M3x6','NutM3':'LAND_ISO4032_M3'}[tag];child=obj.LinkedObject.Shape;local=obj.LinkPlacement;shape=child.copy();shape.Placement=A.Placement();globalpl=A.Placement(A.Vector(*r['placement_mm']),A.Rotation(*r['placement_quaternion'])).multiply(local);row.update(placement_mm=list(globalpl.Base),placement_quaternion=list(globalpl.Rotation.Q))
 if key not in data['meshes']:
  m=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.25,AngularDeflection=.5,Relative=False);vs,faces=m.Topology;data['meshes'][key]=dict(vertices_mm=[[round(x,5) for x in p] for p in vs],faces=faces,label=obj.Label)
 row['id']=key;row['group']='Reglerhalter';data['instances'].append(row)
for c in data['configurations']:
 specrow=next(x for x in spec['configurations'] if x['propeller_index']==c['propeller_index'] and x['variant']==c['variant']);c['mass_modeled_excluding_propellers_kg']+=4*specrow['carrier_mass_each_kg'];c['visible_config_instances']+=sum(r['propeller_index']==c['propeller_index'] and r['variant']==c['variant'] for r in new)
if (O/'Reglerhalter_Pruefung.json').exists():
 proof=json.loads((O/'Reglerhalter_Pruefung.json').read_text());assert proof['native_sha256']==spec['native_sha256'];data['esc_mount_checks']={k:proof[k] for k in ['native_sha256','nominal_clear','new_parts_rotor_Z_gap_mm','scope']}
(O/'projekt.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('ESC viewer exported',len(data['instances']),len(data['meshes']),flush=True)
