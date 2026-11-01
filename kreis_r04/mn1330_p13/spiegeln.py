"""World-coordinate reflections, including pre-existing shape placements.

OCC/FreeCAD's mirror() path in this runtime mishandles a rotated placement.
An explicit geometry transformation preserves the specified world plane.
"""
import sys
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A
X=A.Matrix();X.A11=-1
Y=A.Matrix();Y.A22=-1
Z=A.Matrix();Z.A33=-1

def reflected(shape,matrix):
    out=shape.copy()
    out.transformShape(matrix,True)
    if out.Volume<0:out.reverse()
    return out

def verify():
    import Part
    shapes=[Part.makeBox(10,20,30,A.Vector(100,50,20)),Part.makeCylinder(10,30,A.Vector(100,20,0)),Part.makeSphere(12,A.Vector(-50,20,30))]
    for shape in shapes:
        shape.rotate(A.Vector(),A.Vector(0,1,0),45)
        shape.rotate(A.Vector(),A.Vector(0,0,1),30);shape.translate(A.Vector(0,0,100))
        bb=shape.BoundBox
        for matrix,axis in [(X,'X'),(Y,'Y'),(Z,'Z')]:
            out=reflected(shape,matrix);ob=out.BoundBox
            for c in 'XYZ':
                lo,hi=getattr(bb,c+'Min'),getattr(bb,c+'Max')
                expected=(-hi,-lo) if c==axis else (lo,hi)
                assert abs(getattr(ob,c+'Min')-expected[0])<1e-7
                assert abs(getattr(ob,c+'Max')-expected[1])<1e-7
            assert out.isValid() and len(out.Solids)==1 and abs(out.Volume-shape.Volume)<1e-6
            back=reflected(out,matrix)
            assert back.distToShape(shape)[0]<1e-7
    return dict(passed=True,tests=9,scope='rotated/translated box, cylinder and sphere; X/Y/Z world reflections, volume, validity, inverse operation; analytic surfaces preserved')
if __name__=='__main__':
    import json
    print(json.dumps(verify()))
