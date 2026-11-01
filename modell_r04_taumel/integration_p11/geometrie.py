"""P11 parametric construction, millimetres. Motor envelopes are explicitly not purchase parts."""
import json,math,sys
from pathlib import Path
import FreeCAD as A,Part
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'integration_p10'))
import geometrie_p10 as G
P=json.loads((H/'parameter.json').read_text());V=A.Vector
def cyl(r,h,x=0,y=0,z=0):return Part.makeCylinder(r,h,V(x,y,z))
def ring(ri,ro,z,h,x=0,y=0):return cyl(ro,h,x,y,z).cut(cyl(ri,h+2,x,y,z-1))
def rot(s,a):s=s.copy();s.rotate(V(),V(0,0,1),a);return s
def box(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def smooth_lid(old):
    # Preserve the actual P10 linkage slots, holes, pin interfaces and lower disk.
    disk=old.common(cyl(70,3.0,z=10.5))
    return disk.fuse(ring(64.4,70,13.5,8)).removeSplitter()
def rotor_cup():
    # Integral annular motor carrier, joined to the retained lid in the generator.
    return ring(70,92,10.5,3).fuse(ring(89,92,13.5,18)).removeSplitter()
def guide_insert():return ring(64.4,65.4,15.1,6.4)
def stator():
    s=ring(77.5,86.5,15,15)
    for az in P['stator_post_azimuths_deg']:
        a=math.radians(az);s=s.cut(cyl(1.25,7,82*math.cos(a),82*math.sin(a),24))
    return s.removeSplitter()
def plate(old):
    # Remove the obsolete motor sector below the servo mounts. Retain original
    # servo supports, guide fork and collar, including all supported holes.
    hole=G.polar(54.8,330);s=old.cut(cyl(25.5,5,hole[0],hole[1],42.5))
    arms=[]
    for az in P['stator_post_azimuths_deg']:
        arm=box(20,-4,43,67,8,4)
        # Retain the existing servo-link clearances by only adding between servos.
        arm=rot(arm,az);a=math.radians(az);x,y=82*math.cos(a),82*math.sin(a)
        arm=arm.fuse(cyl(3.5,13,x,y,30)).cut(cyl(1.7,25,x,y,25)).cut(cyl(3.6,6,x,y,46))
        arms.append(arm)
    # Restore a load path at the former drive-motor position for the third guide.
    x,y=G.polar(54.8,330)[:2]
    pad=cyl(15,4,x,y,43).fuse(rot(box(20,-7,43,35,14,4),330))
    s=s.fuse(arms+[pad]).removeSplitter()
    for side in [-1,1]:
        a=math.radians(330);bx=x-side*10*math.sin(a);by=y+side*10*math.cos(a)
        s=s.cut(cyl(1.7,6,bx,by,42))
    # Bore the COMPLETE fused plate, including material of retained servo arms.
    for az in P['stator_post_azimuths_deg']:
        a=math.radians(az);x,y=82*math.cos(a),82*math.sin(a)
        s=s.cut(cyl(1.7,25,x,y,25)).cut(cyl(3.6,6,x,y,46))
    return s.removeSplitter()
def xy(phi,r=54.8,t=.15):
    a=math.radians(phi);return r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a)
def carrier(phi):
    x,y=xy(phi,54.8,0);sx,sy=xy(phi,54.6,0)
    s=cyl(14,3,x,y,40).fuse(cyl(6,18.5,x,y,21.5)).cut(cyl(2.5,14,sx,sy,21.4))
    a=math.radians(phi)
    for k in [-1,1]:s=s.cut(cyl(1.7,6,x-k*10*math.sin(a),y+k*10*math.cos(a),39))
    # M3 radial locking screw through the aluminium pillar into the eccentric stem.
    origin=V(x+2.2*math.cos(a),y+2.2*math.sin(a),32)
    s=s.cut(Part.makeCylinder(1.25,5,origin,V(math.cos(a),math.sin(a),0)))
    return s.removeSplitter()
def eccentric(phi):
    x,y=xy(phi);sx,sy=xy(phi,54.6,0)
    return cyl(3.5,.8,x,y,14.6).fuse([cyl(2.5,6.1,x,y,15.4),cyl(2.5,13.5,sx,sy,21.5)]).removeSplitter()
def locking_screw(phi):
    x,y=xy(phi,54.8,0);a=math.radians(phi)
    return Part.makeCylinder(1.5,3.5,V(x+2.1*math.cos(a),y+2.1*math.sin(a),32),V(math.cos(a),math.sin(a),0))
