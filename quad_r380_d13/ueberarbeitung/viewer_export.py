from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
D=globals().get('BUILD_DOC') or A.openDocument(str(O/'Quad_Flachrippen_Mensch.FCStd'));meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());proof=json.loads((O/'Flachrippen_Pruefung.json').read_text());p=O/'projekt.js';data=json.loads(p.read_text()[len('globalThis.QD_MODEL='):].strip().rstrip(';'))
# Idempotent exporter. Reset changed mass from each original/new contribution.
previous=data.get('flat_yokes',{}).get('changes',[])
for pi in range(10):
 for vi in ['V1','V2','V3','V4','V5']:
  c=next(x for x in data['configurations'] if x['propeller_index']==pi and x['variant']==vi)
  delta=sum(4*(r['mass_new_per_corner_kg']-r['mass_old_per_corner_kg']) for r in meta['changes'] if r['propeller_index']==pi and r['variant']==vi)-sum(4*(r['mass_new_per_corner_kg']-r['mass_old_per_corner_kg']) for r in previous if r['propeller_index']==pi and r['variant']==vi);c['mass_modeled_excluding_propellers_kg']+=delta
for r in meta['changes']:
 for instance in r['instances']:
  item=next(x for x in data['instances'] if x['instance']==instance);item['mass_kg']=r['mass_new_per_corner_kg'];item['label']='Flachrippenknoten '+r['part'];item['connection_revision']='flat_rib_yoke'
# Native shape replaced in the same masters; export once per master, not400 times.
photo=json.loads((O/'Propeller_Aufbau.json').read_text());prop_proof=json.loads((O/'Propeller_Pruefung.json').read_text());previous_photo_count=4 if data.get('photo_propellers') else 0
for c in data['configurations']:c['visible_config_instances']+=4-previous_photo_count
ids={r['master'] for r in meta['changes']}|{r['id'] for r in meta['human']}|{r['id'] for r in photo['instances']}|{f'P{i}_Rotorhuelle' for i in range(10)}
for name in ids:
 o=D.getObject(name);m=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.4,AngularDeflection=.4,Relative=False);vertices,faces=m.Topology;data['meshes'][name]=dict(vertices_mm=[[round(float(x),5) for x in v] for v in vertices],faces=faces,label=o.Label)
data['instances']=[r for r in data['instances'] if r.get('group') not in ['Mensch','Bildpropeller']]+meta['human']+photo['instances'];data['native_sha256']=meta['native_sha256'];data['source_D13_native_sha256']=meta['source_native_sha256'];data['flat_yokes']=meta;data['flat_yoke_geometry_passed']=proof['geometry_passed'];data['strength_revalidation_required']=True;data['human_reference']=dict(height_mm=1750,sole_z_mm=244,default_foot_centres_x_mm=[-200,200],payload_reference_kg=100,mass_in_BOM=False,stance_follows_foot_sliders=False)
data['photo_propellers']=photo;data['photo_propeller_checks']=prop_proof
p.write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('Updated meshes',len(ids),'person parts',len(meta['human']),flush=True)
