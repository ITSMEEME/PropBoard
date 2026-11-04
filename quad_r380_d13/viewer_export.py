from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign,MeshPart
D=A.openDocument(str(O/'Quad_Standardkabelbaum.FCStd'));meta=json.loads((O/'Aufbau.json').read_text());data=json.loads((R/'quad_r380_d12/Ausgabe/projekt.js').read_text()[len('globalThis.QD_MODEL='):].strip().rstrip(';'));old=[r for r in data['instances'] if r.get('group')=='Innenverkabelung'];data['instances']=[r for r in data['instances'] if r.get('group')!='Innenverkabelung'];new=json.loads((O/'Kabel_Instanzen.json').read_text());data['native_sha256']=meta['native_sha256'];data['source_D12_structural_native_sha256']=meta['source_D12_native_sha256'];data['harness_spec']=json.loads((H/'parameter.json').read_text());data['harness_plan']=json.loads((O/'Kabelplanung.json').read_text());data.pop('esc_integration',None);data['electrical_harness_closed']=False
for r in new:
 key=r['id'];obj=D.getObject(key)
 if key not in data['meshes']:
  m=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.3,AngularDeflection=.5,Relative=False);vs,fs=m.Topology;data['meshes'][key]=dict(vertices_mm=[[round(float(x),5) for x in v] for v in vs],faces=fs,label=obj.Label)
 data['instances'].append(r)
for c in data['configurations']:
 a=[r for r in old if r['propeller_index']==c['propeller_index'] and r['variant']==c['variant']];b=[r for r in new if r['propeller_index']==c['propeller_index'] and r['variant']==c['variant']];c['visible_config_instances']+=len(b)-len(a);c['mass_modeled_excluding_propellers_kg']+=sum(r['mass_kg'] for r in b)-sum(r['mass_kg'] for r in a)
used={r['id'] for r in data['instances']};data['meshes']={k:v for k,v in data['meshes'].items() if k in used}
(O/'projekt.js').write_text('globalThis.QD_MODEL='+json.dumps(data,separators=(',',':'),ensure_ascii=False)+';\n');print('D13 viewer exported',len(data['instances']),len(data['meshes']),flush=True)
