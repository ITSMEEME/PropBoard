"""P05 motor fasteners and threaded pinion. Standard threads specified by callout.
FreeCAD's built-in fcgear generates the involute, instead of a coarse polygon flank.
"""
import sys,math,importlib.util
from pathlib import Path
import FreeCAD as A,Part
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
_PD=Path(A.getResourceDir())/'Mod/PartDesign'
if not (_PD/'fcgear').exists():_PD=ROOT/'.cfd-tools/freecad/usr/Mod/PartDesign'
if str(_PD) not in sys.path:sys.path.insert(0,str(_PD))
from fcgear import involute,fcgear
V=A.Vector

def washer():return Part.makeCylinder(3.5,.5).cut(Part.makeCylinder(1.6,2,V(0,0,-.5)))

def screw7():
    source=H.parent/'fertigung_p02/Quellen/N01_M3x10.step'
    s=Part.read(str(source));s=s.common(Part.makeBox(20,20,20,V(-10,-10,-7)))
    assert s.isValid() and len(s.Solids)==1 and abs(s.BoundBox.ZMin+7)<1e-5
    return s

def thin_nut():
    # Norm envelope: AF8 x 2.7, nominal M5 hole; actual supplier chamfers unmodeled.
    r=8/math.sqrt(3);vs=[V(r*math.cos(math.radians(30+60*i)),r*math.sin(math.radians(30+60*i)),0) for i in range(6)]
    s=Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(V(0,0,2.7));return s.cut(Part.makeCylinder(2.5,5,V(0,0,-1)))

def pinion():
    w=fcgear.FCWireBuilder();involute.CreateExternalGear(w,1,20,20,split=True,addCoeff=1,dedCoeff=1.25,filletCoeff=.38,shiftCoeff=0)
    wire=Part.Wire([e.toShape() for e in w.wire]);face=Part.Face(wire);probe=face.extrude(V(0,0,1))
    def at(a):return probe.isInside(V(10*math.cos(math.radians(a)),10*math.sin(math.radians(a)),.5),1e-7,True)
    if at(0) and not at(9):phase=9
    elif at(9) and not at(0):phase=0
    else:raise ValueError('Cannot establish standard involute tooth phase')
    s=face.extrude(V(0,0,5.5)).cut(Part.makeCylinder(2.5,8,V(0,0,-1)));s.rotate(V(),V(0,0,1),phase)
    assert s.isValid() and len(s.Solids)==1
    return s,dict(generator='FreeCAD 1.0.2 PartDesign fcgear, split cubic Bezier involute, root fillet coefficient .38',module_mm=1,teeth=20,pressure_angle_deg=20,face_mm=5.5,pitch_diameter_mm=20,tip_diameter_mm=22,root_diameter_mm=17.5,nominal_thread='M5x0.8-6H THROUGH',machining_pretap_drill_mm=4.2,model_thread_bore_mm=5,phase_applied_deg=phase,pinion_thickness_reduction_mm=0,existing_ring_thickness_reduction_mm=.15,mesh_centre_distance_mm=75.1,manufacturing_quality_grade_not_certified=True)

def motor(m,centres):
    body=Part.makeCylinder(14,m['derived_mount_face_to_bell_front_mm']).fuse(Part.makeCylinder(2.5,13,V(0,0,m['derived_mount_face_to_bell_front_mm'])))
    for x,y in centres:
        # Nominal thread allowance limited to the supplied insertion depth, not a
        # claim about the manufacturer's drilled bottom/cone or thread flank form.
        body=body.cut(Part.makeCylinder(1.5,3,V(x,y,0)))
    return body.removeSplitter()
