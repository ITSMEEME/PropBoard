"""Independent closure, travel and native rigid-motion checks for P14."""
import json,copy,math,hashlib,sys
from pathlib import Path
from kinematik import *
O=H/'Ausgabe'
def unit(v):
    l=dist(v,[0,0,0]);return [x/l for x in v]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def align(v,a,b):
    a,b=unit(a),unit(b);k=cross(a,b);w=cross(k,v);ww=cross(k,w);d=1+dot(a,b)
    return [v[i]+w[i]+ww[i]/d for i in range(3)]
def axis_angle(a,b):return math.acos(min(1,abs(dot(unit(a),unit(b)))))/D
def main():
    c=json.loads((O/'Eingaben.json').read_text());errors=[];count=0;max_closure=0;pitch=[100.,-100.];servorange=[100.,-100.];pin_radial=pin_tangent=0.;port_envelope=0.;fixtures=[];joint_angle=0.;r_angle=0.
    for n in [4,6,8,10,12]:
        for spacing in [360,440]:
            v=copy.deepcopy(c);v['geometry']['blades_per_rotor']=n;v['geometry']['rotor_spacing_mm']=spacing;q=derive(v);g=v['geometry'];neutral=solve(v)
            for collective in [-3.5,0,3.5]:
                for tx,ty in [(0,0),(.5,0),(-.5,0),(0,.5),(0,-.5),(.5/math.sqrt(2),.5/math.sqrt(2))]:
                    for az in range(0,360,30):
                        s=solve(v,collective,tx,ty,az);count+=1
                        for pts in s['pitch_points_mm']:max_closure=max(max_closure,abs(dist(*pts)-q['pitch_link_length_mm']))
                        for pts in s['servo_points_mm']:max_closure=max(max_closure,abs(dist(*pts)-q['servo_link_length_mm']))
                        for i,(p0,p1) in enumerate(s['pitch_points_mm']):
                            initial=neutral['pitch_points_mm'][i];old=rz([initial[1][k]-initial[0][k] for k in range(3)],az*D);new=[p1[k]-p0[k] for k in range(3)];ba=i*360/n
                            for normal,mount in [(rz(q['pitch_lower_pin_axis'],(ba+q['pitch_joint_delta_deg'])*D),tilt(rz(q['pitch_lower_pin_axis'],(ba+q['pitch_joint_delta_deg']+az)*D),tx*D,ty*D)),(rz(tilt(q['pitch_pin_axis_local'],g['neutral_pitch_deg']*D,0),ba*D),rz(tilt(q['pitch_pin_axis_local'],s['pitches_deg'][i]*D,0),(ba+az)*D))]:
                                joint_angle=max(joint_angle,axis_angle(align(rz(normal,az*D),old,new),mount))
                        for i,pts in enumerate(s['servo_points_mm']):
                            ref=neutral['servo_points_mm'][i];old=[ref[1][k]-ref[0][k] for k in range(3)];new=[pts[1][k]-pts[0][k] for k in range(3)];normal=rz([0,1,0],i*120*D);outer=align(normal,old,new)
                            lower=axis_angle(outer,normal);upper=axis_angle(outer,tilt(rz(normal,s['stationary_phase_deg']*D),tx*D,ty*D));joint_angle=max(joint_angle,upper,lower)
                            if i==0:r_angle=max(r_angle,lower)
                        for i,(lower,upper) in enumerate(s['pitch_points_mm']):
                            p0,p1=neutral['pitch_points_mm'][i];t=(q['level_mm']-31-p0[2])/(p1[2]-p0[2]);centre=[p0[k]+t*(p1[k]-p0[k]) for k in [0,1]]
                            a0=rz(lower,-az*D);a1=rz(upper,-az*D);cosine=abs((a1[2]-a0[2])/dist(a1,a0))
                            for zz in [q['level_mm']-35,q['level_mm']-27]:
                                t=(zz-a0[2])/(a1[2]-a0[2]);xy0=[a0[k]+t*(a1[k]-a0[k]) for k in [0,1]]
                                port_envelope=max(port_envelope,dist(xy0,centre)+g.get('pitch_link_envelope_radius_mm',3)/cosine)
                        pitch=[min(pitch[0],*s['pitches_deg']),max(pitch[1],*s['pitches_deg'])];servorange=[min(servorange[0],*s['servo_deg']),max(servorange[1],*s['servo_deg'])]
                        if min(s['pitches_deg'])<4 or max(s['pitches_deg'])>20:errors.append(('pitch',n,spacing,collective,tx,ty,az))
                        # Intersect the vertical drive pin with the tilted slot
                        # plane and transform back into the rotating ring frame.
                        normal=tilt([0,0,1],tx*D,ty*D)
                        for offset in [0,180]:
                            phase=180/n+q['pitch_joint_delta_deg']+offset;pin=rz([q['phase_pin_r_mm'],0,0],(phase+az)*D)
                            z=s['swash_z_mm']-(normal[0]*pin[0]+normal[1]*pin[1])/normal[2]
                            vector=[pin[0],pin[1],z-s['swash_z_mm']]
                            # inverse Rx*Ry then inverse Rz (not another forward tilt)
                            x,y,z0=vector;y,z0=math.cos(tx*D)*y+math.sin(tx*D)*z0,-math.sin(tx*D)*y+math.cos(tx*D)*z0
                            x,z0=math.cos(ty*D)*x-math.sin(ty*D)*z0,math.sin(ty*D)*x+math.cos(ty*D)*z0
                            local=rz([x,y,z0],-(phase+az)*D);pin_radial=max(pin_radial,abs(local[0]-q['phase_pin_r_mm']));pin_tangent=max(pin_tangent,abs(local[1]))
                        if spacing==360 and collective==3.5 and tx==.5 and az in [0,90]:fixtures.append(dict(config=v,inputs=[collective,tx,ty,az],solution=s))
    assert not errors,errors[:8];assert max_closure<1e-6;assert pin_radial<2 and pin_tangent<.15;assert port_envelope<c['geometry']['pitch_rod_port_radius_mm'];assert joint_angle<12 and r_angle<1e-4,(joint_angle,r_angle)
    out=dict(states=count,max_link_closure_error_mm=max_closure,blade_lever_pitch_range_deg=pitch,servo_range_deg=servorange,max_phase_slot_radial_offset_mm=pin_radial,max_phase_slot_tangent_offset_mm=pin_tangent,slot_available_centre_travel_mm=[2,.15],passed=True,scope='Rigid kinematics, not tolerance/wear/elastic load qualification',fixtures=fixtures)
    out['rod_port_envelope_radius_mm']=port_envelope;out['rod_port_min_screen_clearance_mm']=c['geometry']['pitch_rod_port_radius_mm']-port_envelope
    out['joint_articulation_screen']=dict(max_spherical_misalignment_deg=joint_angle,nominal_limit_deg=12,max_R_leg_out_of_plane_deg=r_angle,states=count,passed=True,scope='Nominal axes over supported blade counts and spacing; OEM profile/ratings/tolerances remain unqualified')
    if '--native' in sys.argv:
        from animieren import Animation,local_delta
        import FreeCAD as A
        sha=hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest()
        d=A.openDocument(str(O/'P14_MN1330_Leichtbau.FCStd'));runtime=Animation(d);all_valid=True;motion=[];overlaps=[]
        rows=runtime.scene;upper=[r for r in rows if r['sign']==1]
        find=lambda part,index=None:next(r for r in upper if r['part']==part and (index is None or r['blade_index']==index or (r['blade_index']<0 and r['servo_index']==index)))
        pairs=[('A09','A18'),('A09','ROD_PITCH_0'),('A09','A21'),('A09','A22'),('A09','A13U'),('A09','A16A'),('A24','A21'),('A20','B61832'),('A19','A05'),('A21','ROD_PITCH_0'),('A25','ROD_SERVO_0'),('CFK01','CFK01')]
        extra=[];last=c['geometry']['blades_per_rotor']-1
        for i in [0,last]:
            for end in ['L','U']:
                eye=next(r for r in upper if r.get('joint_key')==f'P{i}_{end}' and r.get('joint_role')=='eye')
                for host in ([find('A20')] if end=='L' else [find('A18',i),find('A18',(i+1)%c['geometry']['blades_per_rotor'])]):extra.append((eye,host))
        for state in [(0,0,0,0,0),(45,3.5,-3.5,.35,.35),(90,-3.5,3.5,-.5,0),(180,3.5,3.5,0,-.5),(270,-3.5,-3.5,.35,-.35)]:
            angle,cu,cl,cx,cy=state;poses=runtime.pose(*state)
            for row in rows:
                s=d.getObject(row['native_object']).Shape;all_valid=all_valid and s.isValid() and len(s.Solids)==1
            for pa,pb in pairs:
                aa=find(pa,0 if pa in ['A18','CFK01'] else None);bb=find(pb,1 if pa==pb else None);sa=d.getObject(aa['native_object']).Shape;sb=d.getObject(bb['native_object']).Shape
                if sa.BoundBox.intersect(sb.BoundBox):
                    volume=abs(sa.common(sb).Volume)
                    if volume>.1:overlaps.append(dict(state=state,part_a=pa,part_b=pb,volume_mm3=volume))
            for aa,bb in extra:
                sa=d.getObject(aa['native_object']).Shape;sb=d.getObject(bb['native_object']).Shape
                if sa.BoundBox.intersect(sb.BoundBox):
                    volume=abs(sa.common(sb).Volume)
                    if volume>.1:overlaps.append(dict(state=state,part_a=aa['name'],part_b=bb['name'],volume_mm3=volume))
            for row in upper:
                if row['frame'] not in ['fixed','shared']:
                    p=local_delta(row,c,poses[1],angle,runtime.q['neutral']).toMatrix();motion.append(dict(state=state,row=row,matrix=[getattr(p,'A'+str(i)+str(j)) for i in range(1,5) for j in range(1,5)]))
        runtime.reset();reset_error=max((d.getObject(name).Placement.Base-p.Base).Length for name,p in runtime.base.items());assert reset_error<1e-8 and all_valid
        out['native']=dict(all_moved_shapes_valid=all_valid,poses=5,reset_translation_error_mm=reset_error,selected_pair_count=len(pairs)+len(extra),selected_dynamic_overlaps=overlaps,scope='Selected root/link/neighbor pairs at5 poses; not a complete swept-volume test')
        assert sha==hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest(),'Native changed during check'
        out['native_sha256']=sha
        (O/'Bewegung_Referenzen.json').write_text(json.dumps(motion,separators=(',',':')))
    (O/'Kinematik_Pruefung.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['fixtures']},indent=2),flush=True)
if __name__=='__main__':main()
