"""Replace both ends of every tube in all50 configurations, add scale person.
Source D13 remains untouched; new native file and revision-specific checks.
"""
from pathlib import Path
import sys,json,math,hashlib
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';CACHED=H/'Cache/Flachrippen';CACHED.mkdir(parents=True,exist_ok=True)
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(H));sys.path.insert(0,str(Path(__file__).resolve().parent))
import FreeCAD as A,Part,PartDesign
from knoten import make_nodes
from mensch import human
from propeller_einbauen import install
from geometrie import placed,trim_core
from planung import axis_geometry
V=A.Vector
print('Loading source native',flush=True)
source=O/'Quad_Standardkabelbaum.FCStd';D=A.openDocument(str(source));print('Source loaded',flush=True);lib=D.getObject('Bauteilbibliothek');asm=D.getObject('Montage');ctl=D.getObject('Variantensteuerung');rows=json.loads((R/'quad_r380_d10/Ausgabe/Instanzen.json').read_text());vs=json.loads((R/'quad_r380_d10/Varianten.json').read_text());cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());p=json.loads((R/'quad_r380_d07/parameter.json').read_text());S=A.openDocument(str(R/'quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd'));core=placed(trim_core(S.getObject('D07_ROOT_TOP').Shape.copy()),(-65,0,22),A.Rotation(V(0,0,1),90));out=[];roots={};masters=set();signature=hashlib.sha256((Path(__file__).parent/'knoten.py').read_bytes()).hexdigest()
print('Core loaded; protect cables',flush=True)
protected={o.Name:hashlib.sha256(o.Shape.exportBrepToString().encode()).hexdigest() for o in D.Objects if o.TypeId=='Part::Feature' and (o.Name.startswith('H13_') or any(o.Name.endswith('_Tube'+str(j)) for j in range(4)))}
print('Protected',len(protected),flush=True)
oldnames={D.getObject(r['instance']).LinkedObject.Name for r in rows if r['part'] in ['Root','Motor']}
oldshapes={n:D.getObject(n).Shape.copy() for n in oldnames}
oldmasses={n:s.Volume*2810e-9 for n,s in oldshapes.items()}
volumes={}
print('Starting50 yokes',flush=True)
for pi in reversed(range(10)):
 for v in vs:
  a,b=axis_geometry(v,cs[pi]);key=hashlib.sha256(json.dumps([signature,v,cs[pi],p],sort_keys=True).encode()).hexdigest();prefix=CACHED/key
  cached=all(Path(str(prefix)+'_'+n+'.brep').exists() for n in ['Root','Motor'])
  if cached:
   shapes=[]
   for n in ['Root','Motor']:
    s=Part.Shape();s.read(str(prefix)+'_'+n+'.brep');assert s.isValid() and len(s.Solids)==1;shapes.append(s)
   root,motor=shapes
  else:
   root,motor=make_nodes(v,cs[pi],a,b,core,p,roots.get(v['id']))
   for n,s in [('Root',root),('Motor',motor)]:s.exportBrep(str(prefix)+'_'+n+'.brep')
  roots[v['id']]=root.copy()
  for part,s in [('Root',root),('Motor',motor)]:
   rs=[r for r in rows if r['propeller_index']==pi and r['variant']==v['id'] and r['part']==part];m=D.getObject(rs[0]['instance']).LinkedObject
   if m.Name not in masters:m.Shape=Part.Compound([s]);masters.add(m.Name)
   for r in rs:assert D.getObject(r['instance']).LinkedObject==m
   vk=(v['id'],part,pi if part=='Motor' else 9)
   if vk not in volumes:volumes[vk]=s.Volume
   volume=volumes[vk]
   out.append(dict(propeller_index=pi,variant=v['id'],part=part,master=m.Name,instances=[r['instance'] for r in rs],mass_old_per_corner_kg=oldmasses[m.Name],mass_new_per_corner_kg=volume*2810e-9,volume_mm3=volume,valid=s.isValid(),solids=len(s.Solids),motor_COM_y_mm=s.Solids[0].CenterOfMass.y if part=='Motor' else None,geometry_cache=cached))
  print('New yokes',pi,v['id'],'g',round(volumes[(v['id'],'Root',9)]*.00281,1),round(volumes[(v['id'],'Motor',pi)]*.00281,1),flush=True)
if not hasattr(ctl,'MenschAnzeigen'):ctl.addProperty('App::PropertyBool','MenschAnzeigen','Ansicht')
ctl.MenschAnzeigen=True;people=[]
for name,shape,colour in human():
 m=D.addObject('Part::Feature','MENSCH_'+name.replace('-','m'));m.Label='Größenreferenz '+name;m.Shape=shape;lib.addObject(m);m.Visibility=False
 o=D.addObject('App::Link',m.Name+'_Referenz');o.setLink(m);asm.addObject(o);o.setExpression('Visibility','Variantensteuerung.MenschAnzeigen == 1 ? 1 : 0');people.append(dict(instance=o.Name,id=m.Name,label=m.Label,group='Mensch',role='anthropometric_reference',colour=colour,mass_kg=0,placement_mm=[0,0,0],placement_quaternion=[0,0,0,1],reference_only=True))
photo=install(D,H)
ctl.Variante='V4';ctl.Propeller=cs[-1]['label'];ctl.Hinweis='D13 Flachrippenknoten: neue Rahmen-/Motoranschlüsse und 1.75m Größenreferenz. Antrieb nur Koeffizientenschätzung, strukturelle Freigabe offen.';D.Label='Quad D13 – Flachrippenknoten und Mensch';D.recompute()
for n,sig in protected.items():assert hashlib.sha256(D.getObject(n).Shape.exportBrepToString().encode()).hexdigest()==sig,n
native=O/'Quad_Flachrippen_Mensch.FCStd';D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();report=dict(native_sha256=sha,source_native_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_native=str(source.name),changes=out,human=people,human_height_mm=1750,human_sole_z_mm=244,human_stance_x_mm=[-200,200],human_mass_not_in_CAD_BOM=True,cable_and_arm_shapes_unchanged=True,protected_shape_count=len(protected),changed_yoke_master_count=len(masters),strength_revalidation_required=True,production_ready=False)
photo['native_sha256']=sha;(O/'Propeller_Aufbau.json').write_text(json.dumps(photo,indent=2))
(O/'Flachrippen_Aufbau.json').write_text(json.dumps(report,indent=2));print('Saved new native',sha,flush=True)

# Reuse the saved document for proof/export, avoiding repeated large-assembly restore.
import runpy
runpy.run_path(str(Path(__file__).parent/'fast_pruefen.py'))
runpy.run_path(str(Path(__file__).parent/'propeller_pruefen.py'))
runpy.run_path(str(Path(__file__).parent/'viewer_export.py'),init_globals={'BUILD_DOC':D})
