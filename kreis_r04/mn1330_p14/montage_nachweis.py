"""Source-bound nominal assembly paths, with explicit stage fixtures.

This is geometric evidence at sampled translations, not a manufacturing,
tolerance, tool-force or OEM interface qualification.
"""
import argparse,json,hashlib,math,sys,csv
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
from animieren import Animation,local_delta
V=A.Vector
def write_register(O,q):
    # Geometry prototypes share a core contour; the manufacturing variants
    # must explicitly distinguish the two thread hands at each occurrence.
    register=[];linkmap={l['key']:l for l in q['linkages']}
    for u,centre in enumerate(q['unit_centres_mm']):
        for sign in [1,-1]:
            for j in q['joints']:
                key=j['family']+str(j['link_index']);hand='RH' if j['end']==0 else 'LH';p=j['centre_mm'];b=j['head_axis'];world=[sign*p[0]+centre[0],p[1]+centre[1],sign*p[2]+centre[2]]
                register.append(dict(unit=u+1,pod='oben' if sign>0 else 'unten',joint=j['key'],kind=j['kind'],eye_order_variant='J_EYE_'+j['family']+'_'+hand,thread='M6x1 '+hand,jam_nut_variant='M6 '+hand,nominal_eye_STEP='STEP_Sonderteile/J_EYE_'+j['family']+'.step',bearing=j['bearing'],min_thread_engagement_mm=linkmap[key]['min_thread_engagement_mm'],x_mm=world[0],y_mm=world[1],z_mm=world[2],pin_withdraw_x=sign*b[0],pin_withdraw_y=b[1],pin_withdraw_z=sign*b[2]))
    with (O/'Gelenk_Register.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(register[0]),delimiter=';');w.writeheader();w.writerows(register)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');args=ap.parse_args();O=args.output
    native=O/'P14_MN1330_Leichtbau.FCStd';sha=hashlib.sha256(native.read_bytes()).hexdigest()
    d=A.openDocument(str(native));run=Animation(d,O);c=run.c;q=run.q;rows=run.scene
    upper=[r for r in rows if r['unit']==0 and r['sign']==1]
    shape=lambda r:d.getObject(r['native_object']).Shape
    find=lambda part,bi=None:next(r for r in upper if r['part']==part and (bi is None or r['blade_index']==bi))
    paths=[]
    def path(label,moving,obstacles,axis,stroke,step=2):
        axis=V(*axis);axis.normalize();steps=max(1,math.ceil(stroke/step));bad=[];worst=0.;checks=0
        for k in (range(1) if stroke==0 else range(steps+1)):
            offset=stroke*k/steps;s=moving.copy();s.translate(axis*offset)
            for r,b in obstacles:
                if not s.BoundBox.intersect(b.BoundBox):continue
                checks+=1;v=abs(s.common(b).Volume);worst=max(worst,v)
                if v>.1:bad.append(dict(offset_mm=offset,obstacle=r,volume_mm3=v))
        paths.append(dict(operation=label,stroke_mm=stroke,sample_step_max_mm=step,samples=steps+1,exact_common_checks=checks,max_overlap_mm3=worst,failures=bad,passed=not bad))
        print(label,'PASS' if not bad else 'FAIL',len(bad),flush=True)
    # Entire remaining assembly is present during pin removal, except the
    # washer/split pin explicitly removed beforehand. Pods are rigidly indexed.
    for sign in [1,-1]:
        podrows=[r for r in rows if r['unit']==0 and r['sign']==sign]
        for joint in q['joints']:
            pin=next(r for r in podrows if r.get('joint_key')==joint['key'] and r.get('joint_role')=='pin')
            excluded={r['native_object'] for r in podrows if r.get('joint_key')==joint['key'] and r.get('joint_role') in ['pin','cotter','pin_washer']}
            obs=[(r['name'],shape(r)) for r in rows if r['native_object'] not in excluded]
            # Continuous conservative translation envelope: filled pin cross-hole,
            # round head and shank; no gaps between sampled pin positions.
            axis=V(*joint['head_axis']);p=V(*joint['centre_mm']);axis=V(sign*axis.x,axis.y,sign*axis.z);p=V(sign*p.x,p.y,sign*p.z)+V(*q['unit_centres_mm'][0]);stroke=32.5
            swept=Part.makeCylinder(7,4+stroke,p+axis*13,axis).fuse(Part.makeCylinder(3.98,32+stroke,p-axis*19,axis))
            path('Bolzen ausziehen '+('oben ' if sign>0 else 'unten ')+joint['key'],swept,obs,[1,0,0],0,1)
            paths[-1].update(stroke_mm=stroke,method='continuous conservative cylindrical pin translation envelope')
    # These tests name the actual assembly stage, rather than checking insertion
    # through components which are installed later.
    def stage(label,part,obs,axis,stroke,bi=None):
        path(label,shape(find(part,bi)),[(r['name'],shape(r)) for r in obs],axis,stroke,2)
    stage('7212 unten von oben auf nackte Welle','B7212',[find('A04'),find('A03')],[0,0,1],120)
    stage('Hauptlagerpatrone ueber unteres7212','A05',[find('A04'),find('A03'),find('B7212')],[0,0,1],100)
    bearings=[r for r in upper if r['part']=='B7212'];top=max(bearings,key=lambda r:shape(r).Solids[0].CenterOfMass.z)
    path('7212 oben in offene Patrone',shape(top),[(r['name'],shape(r)) for r in [find('A04'),find('A05'),find('B7212')]], [0,0,1],100,2)
    stage('D57 Flansch von oben','A04F',[find('A04'),find('A08'),find('A05')],[0,0,1],90)
    stage('Wurzelstern auf Zentrierbund','A09',[find('A04'),find('A04F'),find('A04N')],[0,0,1],90)
    roots=[r for r in upper if r['part']=='B7205' and r['blade_index']==0];outer=max(roots,key=lambda r:shape(r).Solids[0].CenterOfMass.x);inner=min(roots,key=lambda r:shape(r).Solids[0].CenterOfMass.x)
    pre=shape(inner).copy();pre.translate(V(-20,0,0))
    path('7205 innen von oben in offene Hebeltasche',pre,[(find('A09')['name'],shape(find('A09')))], [0,0,1],80,2)
    path('7205 innen aus Hebeltasche20mm einschieben',shape(inner),[(find('A09')['name'],shape(find('A09')))],[-1,0,0],20,1)
    path('7205 aussen durch offene Sitzoeffnung',shape(outer),[(r['name'],shape(r)) for r in [find('A09'),inner,find('A12',0)]],[1,0,0],70,1)
    shaftpart='A13U' if any(r['part']=='A13U' for r in upper) else 'A13'
    shaftpieces=[find(shaftpart,0),find('A13C',0),find('A13D',0)]
    path('Pitchwelle mit Integralflansch und Distanzen von aussen',Part.Compound([solid for r in shaftpieces for solid in shape(r).Solids]),[(r['name'],shape(r)) for r in [find('A09'),inner,outer,find('A11O',0)]],[1,0,0],105,3)
    import gelenke as J,MeshPart
    tools=O/'Montagewerkzeuge';tools.mkdir(exist_ok=True)
    raw=J.cotter_raw();raw.exportStep(str(tools/'Splint_vor_Umbiegen.step'))
    path('Splint gerade in Bolzenquerloch',raw,[('J_PIN8',J.pin())],[-1,0,0],14,1)
    if any(r['part']=='A20C' for r in upper):
        stage('Kugelpfannen-Oberhaelfte von oben','A20C',[find('A19'),find('A20'),find('POM02'),find('POM02U')],[0,0,1],55)
        stage('Kugelpfannen-Unterhaelfte von unten','A20',[find('A19'),find('POM02'),find('POM02U')],[0,0,-1],55)
        stage('61832 von oben in offenen Ring','B61832',[find('A20'),find('A20C'),find('A21')],[0,0,1],65)
        swashparts=['A19','POM01','A20','A20C','POM02','POM02U','A21','A21C','B61832','A22','F3_CUP','F3_TAUMEL']
        swash=Part.Compound([solid for r in upper if r['part'] in swashparts for solid in shape(r).Solids])
        path('Vormontierte Taumeleinheit von oben vor Rotorstern',swash,[(r['name'],shape(r)) for r in [find('A04'),find('A05'),find('A06O')]], [0,0,1],100,2)
        shaft=find('A26');key=find('A26K');horn=find('A27')
        path('Umlenkwelle mit Passfeder von hinten vor Lagern',Part.Compound([*shape(shaft).Solids,*shape(key).Solids]),[(r['name'],shape(r)) for r in [find('A25'),horn]],[0,-1,0],80,2)
        sb=[r for r in upper if r['part']=='B6002' and r['servo_index']==0]
        for bearing in sb:
            direction=-1 if shape(bearing).Solids[0].CenterOfMass.y < -40 else 1
            path('6002 von freiem Wellenende '+str(direction),shape(bearing),[(r['name'],shape(r)) for r in [find('A25'),shaft,key,horn,find('A26S')]],[0,direction,0],55,2)
    types={t['id']:t for t in json.loads((O/'Teile.json').read_text())};tool_results=[]
    for part in ['F5_MOTOR','F6_STATOR','F6_HUB','F4_CRADLE','F6_SUPPORT','F4_HOUSING','F3_CAP','F3_ROOT_CAP','F6_ROOT_OUT','F6_PITCH_END','F6_ROOT','A18B','F3_CUP','F3_TAUMEL']:
        sock=types[part].get('socket')
        if not sock:continue
        row=find(part);p=V(*sock['face_mm']);axis=V(*sock['access_axis']);depth=sock['depth_mm']
        bit=J.hex_x(-depth+.05,depth+30,sock['af_mm']-.1,0)
        bit.Placement=A.Placement(p,A.Rotation(V(1,0,0),axis))
        m=A.Matrix()
        for ii in range(4):
            for jj in range(4):setattr(m,'A'+str(ii+1)+str(jj+1),row['neutral_transform'][4*ii+jj])
        bit.Placement=A.Placement(m).multiply(bit.Placement)
        # Order-specific access: carrier screws before servo/transmission;
        # stator before middle block; housing on the bench before motor.
        excluded=set()
        if part=='F6_STATOR':excluded={r['native_object'] for r in rows if r['part'] not in ['A01','MN1330','F6_STATOR'] or r['sign']<0}
        if part=='F4_HOUSING':excluded={r['native_object'] for r in rows if r['part'] not in ['A03','A05','F4_HOUSING'] or r['sign']<0}
        if part=='F3_CAP':excluded={r['native_object'] for r in rows if r['part'] not in ['A03','A04','A05','A06O','A07','B7212','A08','A08W','F3_CAP','F4_HOUSING'] or r['sign']<0}
        if part in ['F3_CUP','F3_TAUMEL']:excluded={r['native_object'] for r in rows if r['part'] not in swashparts or r['sign']<0}
        if part=='F6_ROOT_OUT':excluded={r['native_object'] for r in rows if r['part'] in ['A13','A13U','A16A','CFK01','F6_ROOT']}
        obs=[(r['name'],shape(r)) for r in rows if r['native_object'] not in excluded]
        path('SW-Bit30mm Zugang '+part,bit,obs,[1,0,0],0,1);tool_results.append(part)
    # Closed-body rigid transforms must retain common centres and permit the
    # inner ring to articulate without relying on a centre-line-only rod.
    angles=[];centre_error=0.;articulation_overlaps=[]
    for state in [(0,0,0,0,0),(45,3.5,-3.5,.35,.35),(90,-3.5,3.5,-.5,0),(180,3.5,3.5,0,-.5),(270,-3.5,-3.5,.35,-.35)]:
        poses=run.pose(*state);pose=poses[1]
        for joint in q['joints']:
            jr=[r for r in upper if r.get('joint_key')==joint['key']]
            eye=next(r for r in jr if r.get('joint_role')=='eye');inside=next(r for r in jr if r.get('joint_role') in ['inner_race','bush'])
            de=local_delta(eye,c,pose,state[0],q['neutral']);di=local_delta(inside,c,pose,state[0],q['neutral']);p=V(*joint['centre_mm']);axis=V(*joint['mount_axis'])
            centre_error=max(centre_error,(de.multVec(p)-di.multVec(p)).Length)
            a=de.Rotation.multVec(axis);b=di.Rotation.multVec(axis);ang=math.degrees(math.acos(min(1,abs(a.dot(b)))))
            angles.append(ang)
            for other in jr:
                if other.get('joint_role') not in ['eye','outer_race','adapter','clip','outer_shim']:continue
                aa,bb=shape(inside),shape(other)
                if aa.BoundBox.intersect(bb.BoundBox):
                    v=abs(aa.common(bb).Volume)
                    if v>.1:articulation_overlaps.append(dict(state=state,joint=joint['key'],part=other['part'],volume_mm3=v))
    run.reset()
    write_register(O,q)
    links=q['linkages'];passed=all(p['passed'] for p in paths) and len(tool_results)==14 and not articulation_overlaps and centre_error<1e-6 and max(angles)<12 and min(l['min_thread_engagement_mm'] for l in links)>=10.5
    out=dict(native_sha256=sha,passed=passed,joint_count_per_pair=2*len(q['joints']),assembly_paths=paths,hex_bit_access_families=tool_results,max_joint_centre_error_mm=centre_error,max_bearing_articulation_deg=max(angles),nominal_GE_articulation_screen_limit_deg=12,articulation_states=5,articulation_overlaps=articulation_overlaps,min_M6_engagement_mm=min(l['min_thread_engagement_mm'] for l in links),minimum_stud_tip_gap_mm=min(l['minimum_tip_gap_mm'] for l in links),scope='Nominal CAD, baseline8 blades, indexed neutral pin-removal and stated assembly stages; All44 pin sweeps explicit in both pods; bearing stages/14 representative bit families at upper core. Continuous conservative pin sweeps; other paths sampled.30mm hex-bit access, not complete hand/tool envelope. No OEM-servo mount/tolerance/strength approval.',unresolved=['OEM Servo-Horn und Gehaeusebefestigung fehlen','Lieferprofil/Tragzahlen GE8E und Sicherungsringe qualifizieren','Anzuege, Passungen und Toleranzkette fertigungstechnisch qualifizieren'])
    assert sha==hashlib.sha256(native.read_bytes()).hexdigest()
    (O/'Montage_Pruefung.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='assembly_paths'},indent=2),flush=True)
    if not passed:sys.exit(1)
if __name__=='__main__':main()
