"""Real separable link hardware, in mm. Structural parts are aluminium.

GE8E envelope (8x16x8, outer width5), DIN472 bearing retaining rings and a
DIN1494 sleeve form the purchased bearing families. Internal spherical profiles
are conservative nominal geometry, not falsely labelled OEM STEP. Pins/eyes
are CNC aluminium variants of the headed-clevis-pin/rod-end families.
"""
import math,sys
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
V=A.Vector
def unit(v):v=V(*v) if not isinstance(v,V) else v;return v/v.Length
def cx(r,h,x=0):return Part.makeCylinder(r,h,V(x,0,0),V(1,0,0))
def cy(r,h,y=0):return Part.makeCylinder(r,h,V(0,y,0),V(0,1,0))
def box(a,b,c,x=0,y=0,z=0):return Part.makeBox(a,b,c,V(x,y,z))
def move(s,p):s=s.copy();s.translate(V(*p));return s
def frame(s,p,x,y):
    x,y=unit(x),unit(y);assert abs(x.dot(y))<1e-7,(x,y)
    z=x.cross(y);m=A.Matrix()
    for col,v in enumerate([x,y,z]):
        for row,val in enumerate(v):setattr(m,'A'+str(row+1)+str(col+1),val)
    m.A14,m.A24,m.A34=p;s=s.copy();s.Placement=A.Placement(m).multiply(s.Placement);return s
def hex_x(x,h,af,bore):
    r=af/math.sqrt(3);pts=[V(x,r*math.cos(math.pi/6+i*math.pi/3),r*math.sin(math.pi/6+i*math.pi/3)) for i in range(6)]
    s=Part.Face(Part.Wire(Part.makePolygon(pts+[pts[0]]).Edges)).extrude(V(h,0,0))
    return s.cut(cx(bore,h+2,x-1)) if bore else s
def fork(centre,axis,away,reach=21):
    # Local Y is pin axis, local Z points away from the rod neck.
    s=None
    for y in [-13,9]:
        side=cy(7.5,4,y).fuse(box(12,4,reach,-6,y,0));s=side if s is None else s.fuse(side)
    s=s.fuse(box(12,26,4,-6,-13,reach-2)).cut(cy(4.1,28,-14))
    b,u=unit(axis),unit(away);assert abs(b.dot(u))<1e-7
    # x=b cross away gives a proper right-handed placement.
    return frame(s,centre,b.cross(u),b)
def housing(tip):
    s=cy(12,8.9,-4)
    s=s.cut(cy(7,11,-5)).cut(cy(8.006,7.5,-2.5)).cut(cy(8.4,1.1,2.6))
    s=s.fuse(cx(4,3,9)).fuse(cx(2.45,tip-12,12))
    return s
def outer():return cy(8,5,-2.5).cut(Part.makeSphere(6.74))
def inner():return Part.makeSphere(6.7).common(box(16,8,16,-8,-4,-8)).cut(cy(4.02,12,-6))
def clip():
    # DIN472-16x1 reference contour with a real installation gap and plier eyes.
    s=cy(8.36,1,2.65).cut(cy(6.8,3,1.65));s=s.cut(box(10,3,5,-10,1.6,-2.5))
    for z in [-2.8,2.8]:
        ear=Part.makeCylinder(.95,1,V(-6.8,2.65,z),V(0,1,0));s=s.fuse(ear)
        s=s.cut(Part.makeCylinder(.4,3,V(-6.8,1.65,z),V(0,1,0)))
    return s
def shim():return cy(8,.15,2.5).cut(cy(7.05,1,2.1))
def r_adapter():return cy(6.3,8,-4).fuse(cy(8,5,-2.5)).cut(cy(5.006,12,-6))
def bush():return cy(5,8,-4).cut(cy(4.02,10,-5))
def pin():
    # Head at negative Y: reverse the entire pin mounting for the upper pitch end.
    s=cy(3.98,32,-13).fuse(cy(7,4,-17))
    return s.cut(Part.makeCylinder(.9,12,V(-6,16,0),V(1,0,0)))
def washer():return cy(7.5,1.6,13).cut(cy(4.1,3,12.4))
def cotter():
    # Installed split pin with loop and separated, bent legs. It is a bearing
    # retention item, not substituted by an uncertified aluminium spring clip.
    loop=Part.makeTorus(1.25,.35,V(-5.7,16.3,0),V(0,0,1))
    a=Part.makeCylinder(.35,11,V(-5.7,15.5,0),V(1,0,0));b=Part.makeCylinder(.35,11,V(-5.7,16.5,0),V(1,0,0))
    a=a.fuse(Part.makeCylinder(.35,3,V(5.3,15.5,0),V(.7,0,-.7)))
    b=b.fuse(Part.makeCylinder(.35,3,V(5.3,16.5,0),V(.7,0,.7)))
    return loop.fuse(a).fuse(b)
def cotter_raw():
    loop=Part.makeTorus(1.25,.35,V(-5.7,16.3,0),V(0,0,1))
    return loop.fuse(Part.makeCylinder(.35,11,V(-5.7,15.5,0),V(1,0,0))).fuse(Part.makeCylinder(.35,11,V(-5.7,16.5,0),V(1,0,0)))
def spacer(y,length=5):return cy(5.25,length,y).cut(cy(4.025,length+2,y-1))
def coupler(length,tip):
    s=hex_x(19,length-38,10,0)
    depth=tip-19+.5
    return s.cut(cx(2.55,depth,19)).cut(cx(2.55,depth,length-19-depth))

def install(c,q,define,put,parts):
    """Place both the rotating and stationary halves, preserving joint centres."""
    from kinematik import D,rz,tilt
    g=c['geometry'];n=g['blades_per_rotor'];ne=q['neutral'];lev=q['level_mm'];r=q['root_r_mm'];sz=g['swash_z_mm'];sy=g['servo_joint_y_mm']
    lengths={'P':q['pitch_link_length_mm'],'S':q['servo_link_length_mm']}
    tips={k:min(33,(L-4)/2) for k,L in lengths.items()};assert min(t-19 for t in tips.values())>=10.5
    common=[('J_GE8_O','GE8E Aussenring',outer(),'Wälzlagerstahl','Normlager'),('J_GE8_I','GE8E Innenring',inner(),'Wälzlagerstahl','Normlager'),('J_CLIP16','Sicherungsring DIN472-16x1',clip(),'Federstahl','Normsicherung'),('J_SHIM16','Passscheibe0.15 fuer GE8',shim(),'Aluminium1050','Sonderteil'),('J_R_ADAPT','R-Gelenk Buchsenadapter',r_adapter(),'Aluminium7075-T6','Sonderteil'),('J_BUSH8','Gleitbuchse DIN1494-8x10x8',bush(),'PTFE','Normlager'),('J_PIN8','Kopfbolzen8 mit Splintloch',pin(),'Aluminium7075-T6','Sonderteil'),('J_W8','Scheibe ISO7092-8',washer(),'Aluminium7075-T6','Normteil'),('J_COTTER','Splint ISO1234-1.6',cotter(),'Sicherungsstahl','Normsicherung'),('J_SP_L','Distanz links5',spacer(-9),'Aluminium7075-T6','Sonderteil'),('J_SP_R','Distanz rechts5',spacer(4),'Aluminium7075-T6','Sonderteil')]
    for id,name,s,mat,kind in common:define(id,name,s,mat,kind,note='Nenngeometrie und Einbau geprüft; Norm-Innenprofile/Massen und Werkstoff-Lebensdauer nach Lieferteil qualifizieren')
    for family,tip in tips.items():
        define('J_EYE_'+family,'Alu-Gelenkauge M6 RH/LH '+family,housing(tip),'Aluminium7075-T6',note='GE8E-Sitz16H7, Schulter und DIN472-Nut;20mm M6-Bereich, Mindestgewindeeingriff10.5mm; Sonderteil')
    nut=hex_x(14,5,10,2.55);define('J_JAM6','Kontermutter M6 RH/LH',nut,'Aluminium7075-T6',note='5mm Kontermutter; Gewindehand je Einbaulage in Gelenkregister')
    # Thrust washers for the guided R leg; matching spacers preserve18mm stack.
    for side in [-1,1]:
        y=4 if side>0 else -4.3
        define('J_PTFE_'+str(side),'R-Anlauf PTFE0.3',cy(7,.3,y).cut(cy(4.1,1,y-.3)),'PTFE','Verschleissteil')
        yy=4.3 if side>0 else -9
        define('J_R_SP_'+str(side),'R-Distanz4.7',spacer(yy,4.7),'Aluminium7075-T6')
    q['joints']=[];q['linkages']=[]
    def mount(s,p,b,across):
        b=unit(b);x=unit(across);x=unit(x-b*x.dot(b));return frame(s,p,x,b)
    def row(id,name,shape,frame_,idx,az,joint,role,servo=-1):
        put(id,name,shape=shape,frame=frame_,a=az,blade_index=idx,servo_index=servo,absolute=True,joint_key=joint,joint_role=role)
    def linkset(family,i,points,axes,frames,azs,headsigns):
        lo,hi=map(lambda p:V(*p),points);d=unit(hi-lo);L=(hi-lo).Length;tip=tips[family];key=family+str(i)
        q['linkages'].append(dict(key=key,centres_mm=points,length_mm=L,stud_tip_mm=tip,coupler_length_mm=L-38,min_thread_engagement_mm=tip-19-.25,minimum_tip_gap_mm=L-2*tip-.5,adjustment_total_mm=.5))
        b=unit(axes[0]);id=('ROD_PITCH_' if family=='P' else 'ROD_SERVO_')+str(i)
        define(id,'Einstellhuelse M6 RH/LH '+key,coupler(L,tip),'Aluminium7075-T6',note='SW10, zwei gegenläufige M6; Gewinde-Kernkontur; keine Nennachsen-Stange durch Gelenke')
        motion='pitch_link' if family=='P' else 'servo_link';bi=i if family=='P' else -1;si=i if family=='S' else -1
        row(id,key+'_Einstellhuelse',frame(parts[id]['shape'],lo,d,b),motion,bi,0,key,'coupler',si)
        for end,(centre,normal,mframe,az,head) in enumerate(zip([lo,hi],axes,frames,azs,headsigns)):
            normal=unit(normal);toward=d if end==0 else -d;endkey=key+('_L' if end==0 else '_U');isR=family=='S' and i==0 and end==0
            for part,role in [('J_EYE_'+family,'eye'),('J_CLIP16','clip'),('J_SHIM16','outer_shim'),('J_JAM6','jam_nut')]+([('J_R_ADAPT','adapter')] if isR else [('J_GE8_O','outer_race')]):
                row(part,endkey+'_'+role,frame(parts[part]['shape'],centre,toward,normal),motion,bi,az,endkey,role,si)
            # Installed bearing inner follows its mount; the outer follows the rod.
            across=toward-normal*toward.dot(normal)
            row('J_BUSH8' if isR else 'J_GE8_I',endkey+'_Innen',mount(parts['J_BUSH8' if isR else 'J_GE8_I']['shape'],centre,normal,across),motion if isR else mframe,bi,az,endkey,'bush' if isR else 'inner_race',si)
            if isR:
                for side in [-1,1]:
                    for part,role in [('J_PTFE_'+str(side),'thrust'),('J_R_SP_'+str(side),'spacer')]:row(part,endkey+'_'+part,mount(parts[part]['shape'],centre,normal,across),motion if role=='thrust' else mframe,bi,az,endkey,role,si)
            else:
                for part in ['J_SP_L','J_SP_R']:row(part,endkey+'_'+part,mount(parts[part]['shape'],centre,normal,across),mframe,bi,az,endkey,'spacer',si)
            # Negative local Y carries the head. Reverse the mounting normal
            # for an outward-facing head, retaining a proper rigid placement.
            pn=normal*(-head)
            for part,role in [('J_PIN8','pin'),('J_W8','pin_washer'),('J_COTTER','cotter')]:row(part,endkey+'_'+role,mount(parts[part]['shape'],centre,pn,across),mframe,bi,az,endkey,role,si)
            q['joints'].append(dict(key=endkey,family=family,link_index=i,end=end,kind='R' if isR else 'S',centre_mm=list(centre),mount_axis=list(normal),outer_axis=list(normal),mount_frame=mframe,head_axis=list(normal*head),mount_az_deg=az,bearing='DIN1494-8x10x8' if isR else 'GE8E-8x16x8-C5',inner_width_mm=8,clevis_gap_mm=18,spacer_length_mm=4.7 if isR else 5,selected_stack_nominal_mm=18,pin_diameter_mm=7.96,pin_hole_mm=8.2,retention='ISO2341-family aluminium headed pin + ISO7092 washer + ISO1234 split pin',steel_only='bearing internals, retaining rings and split pins'))
    b0=q['pitch_pin_axis_local']
    for i,points in enumerate(ne['pitch_points_mm']):
        az=i*360/n;delta=az+q['pitch_joint_delta_deg'];upperAxis=rz(tilt(b0,g['neutral_pitch_deg']*D,0),az*D);lowerAxis=rz(q['pitch_lower_pin_axis'],delta*D)
        linkset('P',i,points,[lowerAxis,upperAxis],['swash_rotor','pitch'],[delta,az],[1,1])
    for i,points in enumerate(ne['servo_points_mm']):
        az=i*120;b=rz([0,1,0],az*D)
        linkset('S',i,points,[b,b],['servo_horn','swash_fixed'],[az,az],[-1,-1])
