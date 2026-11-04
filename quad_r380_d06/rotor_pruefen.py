"""Actual-part static checks and conservative 360-degree swept-envelope checks.

A conservative envelope conflict is NOT automatically an actual blade collision.
Separate exact-BRep phase witnesses establish actual collisions where found.
No change to the motor/rail coordinates is hidden by this check.
"""
import sys,json,math,hashlib,itertools
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'QuadR380_D06_Propeller.FCStd';D=A.openDocument(str(native));rows=json.loads((O/'Instanzen.json').read_text());base=[r for r in rows if not r.get('rotor_id')];added=[r for r in rows if r.get('rotor_id')];shapes={r['instance']:D.getObject(r['instance']).Shape for r in rows};byname={r['instance']:r for r in rows};rotors=json.loads((O/'Rotoren.json').read_text());threshold=.1
cache={};static=[];static_pairs=0

def pair_volume(a,b):
    x=D.getObject(a['instance']);y=D.getObject(b['instance']);rel=x.LinkPlacement.inverse().multiply(y.LinkPlacement)
    rm=rel.Rotation.toMatrix();values=list(rel.Base)+[getattr(rm,'A'+str(i)+str(j)) for i in range(1,4) for j in range(1,4)]
    key=(a['id'],b['id'],tuple(round(v,6) for v in values))
    if key not in cache:
        s=y.LinkedObject.Shape.copy();s.Placement=rel.multiply(s.Placement);cache[key]=intersection_volume(x.LinkedObject.Shape,s)
    return cache[key]

for i,a in enumerate(added):
    sa=shapes[a['instance']]
    for b in base+added[i+1:]:
        if not sa.BoundBox.intersect(shapes[b['instance']].BoundBox):continue
        static_pairs+=1;volume=pair_volume(a,b)
        if volume>threshold:
            finding=dict(a=a['instance'],b=b['instance'],a_id=a['id'],b_id=b['id'],a_label=a['label'],b_label=b['label'],volume_mm3=volume);static.append(finding)
            print('Static collision',finding,flush=True)
    if i%25==0:print('Static added',i,static_pairs,len(static),flush=True)

# The corrected four motor-reference instances also changed their actual native
# location relative to D05, so include them against the complete fixed inventory.
for a in [r for r in base if r['id']=='D05_MN1330_LEGACY_REF']:
    for b in base:
        if a['instance']==b['instance'] or not shapes[a['instance']].BoundBox.intersect(shapes[b['instance']].BoundBox):continue
        volume=pair_volume(a,b);static_pairs+=1
        if volume>threshold:static.append(dict(a=a['instance'],b=b['instance'],a_id=a['id'],b_id=b['id'],a_label=a['label'],b_label=b['label'],volume_mm3=volume))

# For every rotating part a cylindrical annulus encloses all its phases. Rectangular
# XY bounds give a conservative inner/outer radius. Blades and cores were explicitly
# clipped by the R380 cylinder; the root block lies wholly inside that radius.
hulls=[];seen=set();sweep_candidates=[];envelope_shapes={}
for a in added:
    centre=V(*a['rotor_axis_mm']);local=shapes[a['instance']].copy();local.translate(-centre);local.rotate(V(),V(0,0,1),-a['rotor_part_angle_deg']);bb=local.BoundBox
    dx=max(bb.XMin,0,-bb.XMax);dy=max(bb.YMin,0,-bb.YMax);inner=math.hypot(dx,dy);outer=max(math.hypot(x,y) for x in [bb.XMin,bb.XMax] for y in [bb.YMin,bb.YMax])
    if a['id'].startswith(('D06_BLADE_','D06_CORE_')):outer=min(380,outer)
    key=(a['rotor_id'],a['id'],round(inner,5),round(outer,5),round(bb.ZMin,5),round(bb.ZMax,5))
    if key in seen:continue
    seen.add(key);z=centre.z+bb.ZMin;height=bb.ZLength;hull=Part.makeCylinder(outer,height,V(centre.x,centre.y,z))
    if inner>1e-6:hull=hull.cut(Part.makeCylinder(inner,height+2,V(centre.x,centre.y,z-1)))
    hid='H'+str(len(hulls)+1);envelope_shapes[hid]=hull;hulls.append(dict(id=hid,rotor_id=a['rotor_id'],source_instance=a['instance'],source_part=a['id'],inner_radius_mm=inner,outer_radius_mm=outer,zmin_mm=z,zmax_mm=z+height))
    for b in base:
        if not hull.BoundBox.intersect(shapes[b['instance']].BoundBox):continue
        vol=intersection_volume(hull,shapes[b['instance']])
        if vol>threshold:sweep_candidates.append(dict(hull_id=hid,rotor_id=a['rotor_id'],source_instance=a['instance'],source_part=a['id'],fixed_instance=b['instance'],fixed_part=b['id'],fixed_label=b['label'],conservative_envelope_intersection_mm3=vol))
    print('Sweep',hid,a['rotor_id'],a['id'],len(sweep_candidates),flush=True)

# Exact phase witnesses for structural bodies. Fastener hull candidates remain
# explicitly unresolved; the structural collisions already disprove free rotation.
# Start near the fixed body's azimuth rather than spend time on irrelevant phases.
# Absence at samples is never a clearance proof.
witnesses=[];phase_samples=[]
for c in [c for c in sweep_candidates if c['source_part'].startswith('D06_BLADE_') and not c['fixed_part'].startswith('ISO')]:
    a=byname[c['source_instance']];s=shapes[a['instance']];fixed=shapes[c['fixed_instance']];centre=V(*a['rotor_axis_mm']);witness=None
    bb=fixed.BoundBox;angle=math.degrees(math.atan2((bb.YMin+bb.YMax)/2-centre.y,(bb.XMin+bb.XMax)/2-centre.x))-a['rotor_part_angle_deg'];phases=sorted(range(0,360,5),key=lambda phase:abs((phase-angle+180)%360-180))
    for phase in phases:
        moving=s.copy();moving.rotate(centre,V(0,0,1),phase)
        if not moving.BoundBox.intersect(fixed.BoundBox):continue
        volume=intersection_volume(moving,fixed)
        if volume>threshold:
            witness=dict(rotor_id=a['rotor_id'],blade=a['instance'],fixed_instance=c['fixed_instance'],fixed_part=c['fixed_part'],fixed_label=c['fixed_label'],extra_phase_deg=phase,actual_intersection_mm3=volume);witnesses.append(witness);break
    phase_samples.append(dict(source_instance=a['instance'],fixed_instance=c['fixed_instance'],actual_collision_found=witness is not None,search_step_deg=5,phase_order='nearest fixed-body azimuth first; stop at first actual collision'))
    print('Blade witness',c['rotor_id'],c['fixed_part'],None if witness is None else witness['extra_phase_deg'],flush=True)

# Foot-grid sweep only needs to evaluate moving foot solids against invariant
# annuli; all fixed neighbours were covered above. It does not certify a person.
foot_conflicts=[];foot_cases=0;control=D.getObject('Fussverstellung')
for side in ['Links','Rechts']:
    moving=[r for r in base if r.get('foot_side')==side]
    for pos in range(130,251,10):
        for stroke in [0,10]:
            control.Links=-pos if side=='Links' else -200;control.Rechts=pos if side=='Rechts' else 200;control.Entriegelung=stroke;D.recompute();foot_cases+=1
            for r in moving:
                s=D.getObject(r['instance']).Shape
                for hull in hulls:
                    h=envelope_shapes[hull['id']]
                    if not h.BoundBox.intersect(s.BoundBox):continue
                    vol=intersection_volume(h,s)
                    if vol>threshold:foot_conflicts.append(dict(side=side,position_mm=pos,stroke_mm=stroke,instance=r['instance'],hull=hull['id'],volume_mm3=vol))
control.Links=-200;control.Rechts=200;control.Entriegelung=0;D.recompute()

separation=[]
for a,b in itertools.combinations(rotors,2):
    distance=math.dist(a['centre_mm'][:2],b['centre_mm'][:2]);separation.append(dict(a=a['id'],b=b['id'],axis_distance_mm=distance,nominal_disk_edge_gap_mm=distance-760))
assert len(separation)==6 and min(s['nominal_disk_edge_gap_mm'] for s in separation)>89.999
threads=[]
for p in json.loads((O/'Neue_Gewindepaare.json').read_text()):
    a=byname[p['bolt']];b=byname[p['mate']];v=pair_volume(a,b);threads.append(dict(**p,intersection_mm3=v,passed=v<=threshold))
assert len(threads)==24 and all(x['passed'] for x in threads)
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),static_new_part_candidates=static_pairs,static_new_part_interferences=static,static_new_part_interference_count=len(static),continuous_sweep_hulls=hulls,continuous_sweep_candidates=sweep_candidates,continuous_sweep_candidate_count=len(sweep_candidates),actual_blade_collision_witnesses=witnesses,actual_blade_collision_count=len(witnesses),phase_search=phase_samples,phase_witness_scope='Structural bodies only; ISO fastener envelope conflicts remain unresolved candidates, not separately searched for exact phase witnesses.',foot_cases=foot_cases,foot_sweep_envelope_conflicts=foot_conflicts,rotor_disk_separation=separation,root_nominal_thread_pairs=threads,mechanically_clear=not sweep_candidates and not static and not foot_conflicts,production_ready=False,reporting_threshold_mm3=threshold,scope='All196 added propeller parts versus all856 D05 parts and each other at the default pose, plus corrected native motor references versus all fixed neighbors. Continuous conservative annular envelopes enclose full rotation of every added part. Hull intersections are candidates; separate exact-BRep blade phase witnesses on structural bodies confirm actual collisions. ISO envelope conflicts remain unresolved.52 foot-system cases versus all invariant annuli. Nominal rigid CAD, no deflection/tolerances/person envelope; motor-to-hub bolts not selected, OEM motor reference incomplete. Existing D05-to-D05 structural fastener tests are inherited, not rerun here.')
(O/'Rotor_Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print('D06 rotor checks: static',len(static),'envelope',len(sweep_candidates),'actual',len(witnesses),'foot',len(foot_conflicts),flush=True)
