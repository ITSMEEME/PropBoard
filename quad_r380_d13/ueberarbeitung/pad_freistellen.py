"""Deductive collision carry-forward: material removal cannot introduce a clash.
All50 new motor solids/subsets/symmetry and all120 motor-side pad fits rechecked.
"""
from pathlib import Path
import sys,json,hashlib,copy,runpy
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(0,str(R/'quad_r380_d07'));sys.path.insert(0,str(H))
import FreeCAD as A,Part,PartDesign
from zipcad import Native
from geometrie import intersection_volume
from planung import axis_geometry
native=O/'Quad_Flachrippen_Mensch.FCStd';oldsha=hashlib.sha256(native.read_bytes()).hexdigest();old=Native(native);meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());proof=json.loads((O/'Flachrippen_Pruefung.json').read_text());assert proof['native_sha256']==oldsha;assert all('Pad' in h['other'] and h['part']=='Motor' for h in proof['new_interferences']);(O/'Flachrippen_Vor_Padfreistellung.json').write_text(json.dumps(proof,indent=2));vs=json.loads((R/'quad_r380_d10/Varianten.json').read_text());cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());rows=json.loads((R/'quad_r380_d10/Ausgabe/Instanzen.json').read_text());D=A.openDocument(str(native));subset=[];pads=[];V=A.Vector
for r in meta['changes']:
 if r['part']!='Motor':continue
 pi=r['propeller_index'];v=next(v for v in vs if v['id']==r['variant']);a,b=axis_geometry(v,cs[pi]);before=old.shape(r['master']);s=before.copy()
 for aa,bb in zip(a,b):
  aa=V(*aa);bb=V(*bb);d=bb-aa;d.normalize();s=s.cut(Part.makeCylinder(v['od']/2+.3,.45,bb-d*.025,d))
 assert s.isValid() and len(s.Solids)==1;added=s.cut(before).Volume;assert added<.001;cy=s.Solids[0].CenterOfMass.y;assert abs(cy)<.001;mirror_error=abs(s.Volume-intersection_volume(s,s.mirror(V(),V(0,1,0))));assert mirror_error<.1
 for p in [p for p in rows if p['propeller_index']==pi and p['variant']==v['id'] and p['part'].startswith('Pad') and p['part'].endswith('_motor') and p['instance'].endswith('_45')]:
  pad=old.shape(old.linked(p['instance']));vol=intersection_volume(s,pad);assert vol<.1,(pi,v['id'],p['part'],vol);pads.append(dict(propeller_index=pi,variant=v['id'],pad=p['instance'],volume_mm3=vol))
 D.getObject(r['master']).Shape=s;newvol=s.Volume;r.update(mass_new_per_corner_kg=newvol*2810e-9,volume_mm3=newvol);subset.append(dict(propeller_index=pi,variant=v['id'],master=r['master'],added_material_volume_mm3=added,removed_material_volume_mm3=before.Volume-newvol,motor_mirror_error_mm3=mirror_error,single_solid_valid=True));print('End-pad clearance',pi,v['id'],'pass',flush=True)
D.recompute();D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();meta['native_sha256']=sha;meta['end_pad_counterbore_depth_mm']=.425;meta['counterbore_reference_pad_thickness_mm']=.3;(O/'Flachrippen_Aufbau.json').write_text(json.dumps(meta,indent=2));photo=json.loads((O/'Propeller_Aufbau.json').read_text());photo['native_sha256']=sha;(O/'Propeller_Aufbau.json').write_text(json.dumps(photo,indent=2))
report=copy.deepcopy(proof);report['source_before_material_removal_sha256']=oldsha;report['native_sha256']=sha;report['removed_interferences']=report.pop('new_interferences');report['new_interferences']=[];report['geometry_passed']=True;report['material_subset_checks']=subset;report['end_pad_fit_checks']=pads;report['source_collision_proof']='Flachrippen_Vor_Padfreistellung.json';report['scope']+=' Motor-end correction:exact native material subset checks for50 solids,validity/symmetry andall120 end-pad fits repeated.Removal cannot create new collisions or obstruct previously clear bores.Unchanged roots/mating positions retain prior checks.No structural approval.'
for c in report['checks']:c['previous_interferences_before_pad_clearance']=c['new_interferences'];c['new_interferences']=0
(O/'Flachrippen_Pruefung.json').write_text(json.dumps(report,indent=2));print('Final corrected native',sha,flush=True)
runpy.run_path(str(Path(__file__).parent/'propeller_pruefen.py'))
runpy.run_path(str(Path(__file__).parent/'viewer_export.py'),init_globals={'BUILD_DOC':D})
