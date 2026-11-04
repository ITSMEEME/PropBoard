"""Actual nominal threaded-pair intersections, including new socket/core threads."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());byname={r['instance']:r for r in rows};base=H.parent/'quad_r380_d05/Ausgabe/Gewindepruefung.json';prior=json.loads(base.read_text())['pairs'];rotor=json.loads((H.parent/'quad_r380_d06/Ausgabe/Rotor_Pruefung.json').read_text())['root_nominal_thread_pairs'];pairs=[dict(bolt=p['bolt'],mate=p['mate'],family=p.get('family','Übernommene Nominalverbindung')) for p in prior+rotor if p['bolt'] in byname and p['mate'] in byname];pairs+=json.loads((O/'Neue_Gewindepaare.json').read_text());threshold=.1;cache={};results=[];phasefile=O/'Gewindephasen.json';phases=json.loads(phasefile.read_text()).get('phases',{}) if phasefile.exists() else {}

def evaluate(a,b):
    rel=b.LinkPlacement.inverse().multiply(a.LinkPlacement);rm=rel.Rotation.toMatrix();key=(byname[a.Name]['id'],byname[b.Name]['id'],tuple(round(v,6) for v in list(rel.Base)+[getattr(rm,'A'+str(i)+str(j)) for i in range(1,4) for j in range(1,4)]))
    if key not in cache:
        shape=a.LinkedObject.Shape.copy();shape.Placement=rel.multiply(shape.Placement);cache[key]=intersection_volume(b.LinkedObject.Shape,shape)
    return cache[key]

for index,pair in enumerate(pairs):
    bolt=D.getObject(pair['bolt']);mate=D.getObject(pair['mate']);base_rotation=bolt.LinkPlacement.Rotation;axis=base_rotation.multVec(V(0,0,1));position=bolt.LinkPlacement.Base;best=None
    for phase in [0,15,-15,30,-30,45,-45,60,-60,90,120,150,180,210,240,270,300,330]:
        pose=A.Placement(position,A.Rotation(axis,phase).multiply(base_rotation));bolt.LinkPlacement=pose
        try:volume=evaluate(bolt,mate)
        except (ValueError,Part.OCCError):continue
        if best is None or volume<best[0]:best=(volume,phase)
        if volume<=threshold:break
    if best is None or best[0]>threshold:
        seed=best[1] if best else 0
        for phase in [seed+d for d in range(-15,16,3)]:
            bolt.LinkPlacement=A.Placement(position,A.Rotation(axis,phase).multiply(base_rotation))
            try:volume=evaluate(bolt,mate)
            except (ValueError,Part.OCCError):continue
            if best is None or volume<best[0]:best=(volume,phase)
            if volume<=threshold:break
    assert best is not None and best[0]<=threshold,(pair,best)
    bolt.LinkPlacement=A.Placement(position,A.Rotation(axis,best[1]).multiply(base_rotation))
    if abs(best[1])>1e-8:phases[bolt.Name]=phases.get(bolt.Name,0)+best[1]
    result=dict(**pair,intersection_mm3=best[0],additional_fitted_phase_deg=best[1],passed=True);results.append(result);print('Thread',index+1,len(pairs),pair['family'],round(best[0],6),flush=True)
for row in rows:
    obj=D.getObject(row['instance']);row['placement_mm']=list(obj.LinkPlacement.Base);row['placement_quaternion']=list(obj.LinkPlacement.Rotation.Q)
D.recompute();D.saveAs(str(native));digest=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Instanzen.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False));phasefile.write_text(json.dumps(dict(phases=phases,scope='Assembly screw phase calibration relative to the D06 input and unphased D07 recipe; reusable deterministic rebuild input, not a thread-tolerance release'),indent=2))
(O/'Gewindepruefung.json').write_text(json.dumps(dict(native_sha256=digest,passed=True,pairs=results,pair_count=len(results),reporting_threshold_mm3=threshold,scope='Actual solid intersections of surviving old nominal thread pairs,24 propeller-root pairs and32 new socket M4 pairs. All changed core-port connections rechecked. True nominal helices; no manufacturing tolerance, preload or CFK strength release.16 motor internal threads remain OEM-unverified; motor-nabe bolts absent.'),indent=2,ensure_ascii=False))
status=json.loads((O/'Status.json').read_text());status.update(native_sha256=digest,thread_pair_count=len(results),nominal_threads_passed=True,thread_phase_input_sha256=hashlib.sha256(phasefile.read_bytes()).hexdigest());(O/'Status.json').write_text(json.dumps(status,indent=2,ensure_ascii=False))
pose=[]
for row in rows:
    obj=D.getObject(row['instance']);s=obj.LinkedObject.Shape.copy();s.Placement=obj.LinkPlacement.multiply(s.Placement);delta=max(abs(getattr(s.BoundBox,k)-getattr(obj.Shape.BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']);assert delta<1e-5;pose.append(dict(instance=row['instance'],max_bbox_delta_mm=delta))
(O/'Native_Platzierung_Pruefung.json').write_text(json.dumps(dict(native_sha256=digest,passed=True,checks=pose),indent=2));print('D07 nominal threads verified',len(results),flush=True)
