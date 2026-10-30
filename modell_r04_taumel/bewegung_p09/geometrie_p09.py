"""Compact captured blade joints and explicit root retainers, P09 design geometry."""
import sys,importlib.util
from pathlib import Path
import FreeCAD as A,Part
V=A.Vector
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_p09_g08',H.parent/'fertigung_p08/geometrie.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)

def stud():
    h=G.hexagon(3,.8);h.rotate(V(),V(0,1,0),90);h.translate(V(-4.8,0,0))
    return Part.makeSphere(2.4).fuse(G.cyl(1,2,(-4,0,0),(1,0,0))).fuse(h).fuse(G.cyl(1,3,(-7.8,0,0),(1,0,0))).removeSplitter()
def body():
    s=G.cyl(3.6,5.9,(-3,0,0),(1,0,0)).fuse(G.cyl(2,2.9,(0,0,2.6)))
    cavity=Part.makeSphere(2.43).fuse(G.cyl(2.43,3.1,(-3.1,0,0),(1,0,0))).fuse(G.cyl(2.75,1.9,(-3.1,0,0),(1,0,0)))
    return s.cut(cavity).cut(G.cyl(1,2.8,(0,0,2.8))).removeSplitter()
def cap():
    s=G.cyl(2.75,1.8,(-3,0,0),(1,0,0)).fuse(G.cyl(3.4,.6,(-3.6,0,0),(1,0,0)))
    s=s.cut(G.box(10,5,10,(-5,3,-5))).cut(G.box(10,5,10,(-5,-8,-5)))
    return s.cut(Part.makeSphere(2.43)).cut(Part.makeCone(2.5,1.65,2.4,V(-3.6,0,0),V(1,0,0))).removeSplitter()
def rod():return G.cyl(1,8.6,(0,0,3.2)).fuse(G.hexagon(2.5,2,6.5)).removeSplitter()
def axial_washer():
    s=G.cyl(5.75,.7).cut(G.cyl(1.1,.9,(0,0,-.1)));s.rotate(V(),V(0,1,0),90);s.translate(V(28.8,0,0));return s

def axial_bolt():
    s=G.bolt().common(G.box(20,20,12,(-10,-10,-8)));s.rotate(V(),V(0,1,0),-90);s.translate(V(28.8,0,0));return s

def insert():return G.cyl(1.75,7,(30,0,0),(1,0,0)).cut(G.cyl(1,7.2,(29.9,0,0),(1,0,0)))
def bond():return G.cyl(1.8,7,(30,0,0),(1,0,0)).cut(G.cyl(1.75,7.2,(29.9,0,0),(1,0,0)))
def blade(C):return C.blade_shape().cut(G.cyl(1.8,8,(30,0,0),(1,0,0)))
def pitch_horn(C,sign):
    s=C.horn_shape(sign)
    y=sign*9
    bridge=G.box(7.8,6,4.1,(25.2,y-3,-1.5))
    boss=G.box(3,6,6.5,(25.2,y-3,2))
    s=s.fuse(bridge).fuse(boss)
    s=s.cut(G.cyl(3.8,8,(29,y,5.5),(1,0,0))).cut(G.cyl(1,3.1,(25.1,y,5.5),(1,0,0)))
    return s.removeSplitter()
def rotating_ring(C,sign):
    # Actual 58mm bearing OD seat; top shoulder is outside the bearing width.
    s=C.ring(29.03,36,-3.5,8).fuse(C.ring(27.5,29.04,3.5,1))
    s=s.cut(C.rotz(C.box(28.9,37,-1.7,1.7,-10,10),-sign*7))
    for k in range(8):
        y=sign*9;a=k*45
        s=s.cut(C.rotz(G.cyl(3.8,8,(29,y,-5.5),(1,0,0)),a))
        s=s.cut(C.rotz(G.cyl(1,3.6,(34,0,-3.5)),a))
    return s.removeSplitter()
def ring_retainer(C,sign):
    s=C.ring(27.5,36,-4.5,1)
    for k in range(8):
        y=sign*9;a=k*45
        bridge=G.box(9.3,6,1.2,(25.2,y-3,-4.8))
        boss=G.box(3,6,4.9,(25.2,y-3,-8.5))
        s=s.fuse(C.rotz(bridge.fuse(boss),a))
        s=s.cut(C.rotz(G.cyl(3.8,8,(29,y,-5.5),(1,0,0)),a))
        s=s.cut(C.rotz(G.cyl(1,3.1,(25.1,y,-5.5),(1,0,0)),a))
        s=s.cut(C.rotz(G.cyl(1.85,1.05,(28.2,y,-5.5),(1,0,0)),a))
        s=s.cut(C.rotz(G.cyl(1.1,2,(34,0,-5)),a))
    return s.removeSplitter()
def retainer_bolt():
    s=G.bolt().common(G.box(20,20,8,(-10,-10,-4)))
    s.rotate(V(),V(1,0,0),180);s.translate(V(34,0,-4.5));return s

def hub(C,sign):
    s=C.hub_shape()
    # Inner-wall relief, retaining the outer 5mm supporting the blade pins.
    for k in range(8):
        y0,y1=(3,14) if sign>0 else (-14,-3)
        pocket=C.box(34,38.8,y0,y1,1,13.5)
        s=s.cut(C.rotz(pocket,k*45))
    return s.removeSplitter()
