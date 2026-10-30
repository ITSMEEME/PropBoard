"""Dimensioned P08 linkage candidates. Threads use explicit nominal callouts.
Not a manufacturing/strength release. All dimensions in millimetres.
"""
import math
import FreeCAD as A,Part
V=A.Vector

def cyl(r,h,p=(0,0,0),axis=(0,0,1)):
    return Part.makeCylinder(r,h,V(*p),V(*axis))
def box(x,y,z,p):return Part.makeBox(x,y,z,V(*p))
def hexagon(af,h,z=0):
    r=af/math.sqrt(3)
    pts=[V(r*math.cos(math.radians(30+60*i)),r*math.sin(math.radians(30+60*i)),z) for i in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h))
def translate(s,p):s=s.copy();s.translate(V(*p));return s

def nut():return hexagon(4,1.6).cut(cyl(1,2,(0,0,-.2)))
def washer():return cyl(2.5,.3).cut(cyl(1.1,.5,(0,0,-.1)))
def bolt():
    # M2x12; ISO4762 nominal head3.8x2, hex1.5 socket.
    s=cyl(1,12,(0,0,-12)).fuse(cyl(1.9,2))
    return s.cut(hexagon(1.5,1.1,1.0)).removeSplitter()
def ball_stud():
    # Seat at x=-6.3; sphere at origin. M2x0.4 stem4mm.
    h=hexagon(4,1.5);h.rotate(V(),V(0,1,0),90);h.translate(V(-6.3,0,0))
    return Part.makeSphere(2.4).fuse(cyl(1,2.8,(-4.8,0,0),(1,0,0))).fuse(h).fuse(cyl(1,4,(-10.3,0,0),(1,0,0))).removeSplitter()
def socket_body():
    # Ball inserted from -X through M6x0.5 mouth before cap is threaded in.
    s=cyl(4,6.7,(-3.5,0,0),(1,0,0)).fuse(cyl(2,4.4,(0,0,2.6)))
    cavity=Part.makeSphere(2.43).fuse(cyl(2.43,3.7,(-3.7,0,0),(1,0,0))).fuse(cyl(3,2.3,(-3.6,0,0),(1,0,0)))
    return s.cut(cavity).cut(cyl(1,3.6,(0,0,3.5))).removeSplitter()
def socket_cap():
    s=cyl(3,2.2,(-3.5,0,0),(1,0,0)).fuse(cyl(3.7,.8,(-4.3,0,0),(1,0,0)))
    # Two wrench flats AF6.4, no decoration-only screw representation.
    s=s.cut(box(12,5,12,(-6,3.2,-6))).cut(box(12,5,12,(-6,-8.2,-6)))
    cone=Part.makeCone(2.7,1.6,3.0,V(-4.3,0,0),V(1,0,0))
    return s.cut(Part.makeSphere(2.43)).cut(cone).removeSplitter()
def turnbuckle(length):
    # RH lower / LH upper; central AF3 x4. No in-flight length change.
    return cyl(1,length-8,(0,0,4)).fuse(hexagon(3,4,length/2-2)).removeSplitter()
def horn(profile):
    # Body plane y=-9.5..-5.5. Ball stud seated on arm front y=-6.3.
    hub=cyl(5.5,4,(0,-9.5,0),(0,1,0))
    arm=box(8,2,4,(-8,-8.3,-2)).fuse(cyl(2,2,(-8,-8.3,0),(0,1,0)))
    boss=cyl(2,8,(5.5,-7.5,-4))
    s=hub.fuse(arm).fuse(boss).cut(profile)
    s=s.cut(cyl(1.1,3,(-8,-8.8,0),(0,1,0))).cut(cyl(1.1,10,(5.5,-7.5,-5)))
    s=s.cut(box(10,6,.5,(0,-10.5,-.25)))
    return s.removeSplitter()
