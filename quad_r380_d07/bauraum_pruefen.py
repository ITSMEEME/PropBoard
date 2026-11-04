"""All changed V3 parts versus current assembly, plus inherited rotor witnesses."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';BASE=H.parent/'quad_r380_d06/Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'QuadR380_D07_V3.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());byname={r['instance']:r for r in rows};shapes={r['instance']:D.getObject(r['instance']).Shape for r in rows};selected=[r for r in rows if r['id'].startswith('D07_') or r['label']=='V3 Rohrklemmung M4x20'];selected_names={r['instance'] for r in selected};unchanged=[r for r in rows if r['instance'] not in selected_names];cache={};findings=[];candidates=0
threads=json.loads((O/'Gewindepruefung.json').read_text());known={frozenset((p['bolt'],p['mate'])):p['intersection_mm3'] for p in threads['pairs']}
def check(a,b):
    aa=shapes[a['instance']];bb=shapes[b['instance']]
    if not aa.BoundBox.intersect(bb.BoundBox):return
    global candidates
    candidates+=1;pair=frozenset((a['instance'],b['instance']))
    if pair in known:volume=known[pair]
    else:
        x=D.getObject(a['instance']);y=D.getObject(b['instance']);rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement);m=rel.Rotation.toMatrix();values=list(rel.Base)+[getattr(m,'A'+str(i)+str(j)) for i in range(1,4) for j in range(1,4)];key=(a['id'],b['id'],tuple(round(v,6) for v in values))
        if key not in cache:
            s=y.LinkedObject.Shape.copy();s.Placement=rel.multiply(s.Placement);cache[key]=intersection_volume(x.LinkedObject.Shape,s)
        volume=cache[key]
    if volume>.1:
        finding=dict(a=a['instance'],b=b['instance'],a_id=a['id'],b_id=b['id'],a_label=a['label'],b_label=b['label'],intersection_mm3=volume);findings.append(finding);print('Collision',finding,flush=True)
for i,a in enumerate(selected):
    for b in unchanged+selected[i+1:]:check(a,b)
    if i%20==0:print('V3 static',i,len(selected),candidates,len(findings),flush=True)

# The retained props are unchanged. Full Z separation proves that no new V3
# part enters any of their phases, not merely the stored static orientation.
rotor=[r for r in rows if r.get('rotor_id')];rotormin=min(shapes[r['instance']].BoundBox.ZMin for r in rotor);newmax=max(shapes[r['instance']].BoundBox.ZMax for r in selected);gap=rotormin-newmax;assert gap>0,(rotormin,newmax)
feet=[r for r in rows if r.get('foot_side')];footmin=min(shapes[r['instance']].BoundBox.ZMin for r in feet);footgap=footmin-newmax;assert footgap>0

# Re-evaluate all20 known actual D06 structural collision witnesses at their
# measured angles. They are not discarded or relabelled as solved by V3.
old=json.loads((BASE/'Rotor_Pruefung.json').read_text());witnesses=[]
for w in old['actual_blade_collision_witnesses']:
    a=byname[w['blade']];moving=shapes[a['instance']].copy();moving.rotate(V(*a['rotor_axis_mm']),V(0,0,1),w['extra_phase_deg']);fixed=shapes[w['fixed_instance']];volume=intersection_volume(moving,fixed)
    witnesses.append(dict(**w,current_intersection_mm3=volume,still_present=volume>.1))
    print('Existing rotor witness',w['rotor_id'],w['fixed_part'],round(volume,3),flush=True)
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),new_static_candidates=candidates,new_static_interference_count=len(findings),new_static_interferences=findings,new_V3_parts_below_entire_rotor_sweep=True,new_part_max_z_mm=newmax,retained_rotor_min_z_mm=rotormin,conservative_new_part_rotor_Z_gap_mm=gap,all_V3_parts_below_moving_foot_system=True,foot_system_min_z_mm=footmin,new_part_foot_Z_gap_mm=footgap,foot_pose_scope='Foot raster changes X and index-unlock changes Y only; Z separation covers both feet at all13 positions and2 unlock endpoints. No person/shoe envelope.',existing_D06_rotor_witnesses=witnesses,existing_D06_rotor_collisions_still_present=sum(w['still_present'] for w in witnesses),full_aircraft_mechanically_clear=False,reporting_threshold_mm3=.1,scope='All changed V3 bodies,8 new tubes,16 caps,16 liners,16 end pads and32 screws versus every current assembly instance and each other at default pose. Nominal rigid surfaces; screws checked with nominal helical proof. Full-Z-separation proof for all new parts versus all rotor phases and foot adjustment positions.20 old actual rotor/foot-support collision witnesses explicitly retested; this is not a fresh exhaustive global sweep/tolerance/flexibility proof for unchanged parts.')
(O/'Bauraum_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('V3 clearance: new findings',len(findings),'rotor Zgap',gap,'old rotor conflicts',report['existing_D06_rotor_collisions_still_present'],flush=True)
