#!/usr/bin/python3
import json, math, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.extend(['/usr/lib/freecad/lib',str(HERE.parent/'cad')])
import FreeCAD as App
import Part
from umlauf_kinematik import state,perimeter,naca_thickness
p=json.loads((HERE/'parameter.json').read_text())
d=App.newDocument('Horizontal_Z_gegenlaeufig')
info=d.addObject('App::FeaturePython','Annahmen')
for key,value in {'Status':p['note'], 'Pitch':'Nase entlang Geschwindigkeit, konstant 12 Grad nach oben; radial gerichtete Pitchachsen',
                  'Fuehrung':'Schienen und Schlitten nur Bauraum. Kein Magnetlager, Linearmotor oder Fangsystem ausgelegt.',
                  'Parameter':'JSON bearbeiten und Skript erneut ausfuehren; Tabelle ist Dokumentation.'}.items():
    info.addProperty('App::PropertyString',key);setattr(info,key,value)
sheet=d.addObject('Spreadsheet::Sheet','Parameter')
for i,(key,value) in enumerate(p.items(),1): sheet.set(f'A{i}',key);sheet.set(f'B{i}',str(value))
deck=d.addObject('Part::Box','Standdeck')
deck.Length,deck.Width,deck.Height=1200,300,40
deck.Placement.Base=App.Vector(-600,-150,250)
length=perimeter(p['straight_m'],p['radius_m'])
foils=[]
for layer,z in enumerate(p['levels_z_m']):
    direction=1 if layer==0 else -1
    g=d.addObject('App::DocumentObjectGroup',f'Band_{layer}')
    # Offset stadium paths: inner/outer radii, same straight segment length.
    for side in (-1,1):
        radius=(p['radius_m']+side*p['rail_radial_offset_m'])*1000
        a=p['straight_m']*500
        h=p['rail_radius_m']*1000
        v=lambda x,y:App.Vector(x,y,z*1000-h)
        def oval_face(r):
            edges=[Part.makeLine(v(-a,r),v(a,r)),
                   Part.Arc(v(a,r),v(a+r,0),v(a,-r)).toShape(),
                   Part.makeLine(v(a,-r),v(-a,-r)),
                   Part.Arc(v(-a,-r),v(-a-r,0),v(-a,r)).toShape()]
            return Part.Face(Part.Wire(edges))
        rail=d.addObject('Part::Feature',f'Fuehrung_{layer}_{side+1}')
        rail.Shape=oval_face(radius+h).cut(oval_face(radius-h)).extrude(App.Vector(0,0,2*h));g.addObject(rail)
    for i in range(p['wings_per_level']):
        x,y,tx,ty,_=state(i*length/p['wings_per_level'],p['straight_m'],p['radius_m'])
        # Fixed geometric outward radial direction, independent of motion.
        radial=App.Vector(-ty,tx,0)
        tangent=App.Vector(direction*tx,direction*ty,0)
        alpha=math.radians(p['pitch_deg'])
        nose=tangent*math.cos(alpha)+App.Vector(0,0,math.sin(alpha))
        thick=tangent*(-math.sin(alpha))+App.Vector(0,0,math.cos(alpha))
        span=(-nose).cross(thick) # flips with direction; same symmetric span.
        chord=p['chord_m']*1000
        xx=[(1-math.cos(math.pi*j/50))/2 for j in range(51)]
        pts=[App.Vector(q*chord,sign*naca_thickness(q)*chord,0)
             for sign,seq in ((1,xx),(-1,xx[-2:0:-1])) for q in seq]
        pts.append(pts[0])
        profile=d.addObject('Part::Feature',f'Profil_{layer}_{i}')
        profile.Shape=Part.Face(Part.Wire(Part.makePolygon(pts).Edges))
        mat=App.Matrix()
        for col,vector in enumerate((-nose,thick,span),1):
            for row,val in enumerate((vector.x,vector.y,vector.z),1): setattr(mat,f'A{row}{col}',val)
        centre=App.Vector(x*1000,y*1000,z*1000)
        profile.Placement=App.Placement(centre+nose*(chord/2)-span*(p['span_m']*500),App.Rotation(mat))
        foil=d.addObject('Part::Extrusion',f'Fluegel_{layer}_{i}')
        foil.Base=profile;foil.Dir=span*(p['span_m']*1000);foil.Solid=True
        foil.addProperty('App::PropertyInteger','Umlaufrichtung');foil.Umlaufrichtung=direction
        foil.addProperty('App::PropertyAngle','Pitch');foil.Pitch=p['pitch_deg']
        g.addObject(profile);g.addObject(foil);profile.Visibility=False;foils.append(foil)
        shaft=d.addObject('Part::Cylinder',f'Pitchachse_{layer}_{i}')
        shaft.Radius=4;shaft.Height=640
        shaft.Placement=App.Placement(centre-radial*320,App.Rotation(App.Vector(0,0,1),radial));g.addObject(shaft)
        for side in (-1,1):
            box=d.addObject('Part::Box',f'Schlitten_{layer}_{i}_{side+1}')
            box.Length,box.Width,box.Height=24,24,24
            box.Placement.Base=centre+radial*(side*320)-App.Vector(12,12,12);g.addObject(box)
d.recompute()
parts=[o for o in d.Objects if hasattr(o,'Shape') and o.TypeId!='App::DocumentObjectGroup']
assert all(not o.Shape.isNull() and o.Shape.isValid() for o in parts)
visible=[o for o in parts if not o.Name.startswith('Profil')]
bb=App.BoundBox()
for o in visible:bb.add(o.Shape.BoundBox)
assert bb.XLength<2100 and bb.YLength<1700 and bb.ZLength<600
intersections=[]
for i,a in enumerate(foils):
    for b in foils[i+1:]:
        if a.Shape.common(b.Shape).Volume>1e-5:intersections.append([a.Name,b.Name])
assert not intersections,intersections
path=HERE/'Horizontal_Z_gegenlaeufig.FCStd'
d.saveAs(str(path));Part.export(visible,str(HERE/'Horizontal_Z_gegenlaeufig.step'))
App.closeDocument(d.Name)
opened=App.openDocument(str(path));opened.recompute()
assert all(o.Shape.isValid() for o in opened.Objects if hasattr(o,'Shape'))
report={'saved_reopened':True,'wings':16,'snapshot_bounds_mm':[bb.XLength,bb.YLength,bb.ZLength],
        'wing_intersections_snapshot':intersections,'continuous_collision_check':False,
        'flight_or_magnetic_validation':False}
(HERE/'CAD_Pruefung.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
