#!/usr/bin/python3
"""Zwei gegenlaeufige, nominell magnetgefuehrte Fluegelumlaeufe."""
import json
import math
from pathlib import Path
import sys
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
import Part
from umlauf_kinematik import perimeter, state, naca_thickness

HERE = Path(__file__).resolve().parent
p = json.loads((HERE/'umlauf_parameter.json').read_text())
d = App.newDocument('Gegenlaeufiger_Fluegelumlauf')
info = d.addObject('App::FeaturePython', 'Konzeptannahmen')
for key, value in {
    'Status': 'Unvalidierter Konzeptentwurf; keine Personenflugfreigabe',
    'Magnetfuehrung': 'Nur Bauraum: keine Magnet-, Spalt-, Kraft- oder Fangfuehrungsauslegung',
    'Pitch': 'Individuelle Drehachsen; alpha=12 Grad * Tangente_x; Antriebe fehlen',
    'Energie': 'Kein Massen-, Leistungs- oder Akku-Nachweis',
    'Bewegung': 'Momentaufnahme; Animation und Parameteraktualisierung durch Erzeugungsskript'
}.items():
    info.addProperty('App::PropertyString', key)
    setattr(info, key, value)
sheet = d.addObject('Spreadsheet::Sheet','Parameter')
for row, (key, value) in enumerate(p.items(),1):
    sheet.set(f'A{row}',key)
    sheet.set(f'B{row}',str(value))
deck = d.addObject('Part::Box','Standdeck')
deck.Length, deck.Width, deck.Height = 1200,300,40
deck.Placement.Base = App.Vector(-600,-150,250)


def rail(y):
    a, r = p['straight_m']*500, p['radius_m']*1000
    v = lambda x,z: App.Vector(x,y,z)
    edges = [Part.makeLine(v(-a,r),v(a,r)),
             Part.Arc(v(a,r),v(a+r,0),v(a,-r)).toShape(),
             Part.makeLine(v(a,-r),v(-a,-r)),
             Part.Arc(v(-a,-r),v(-a-r,0),v(-a,r)).toShape()]
    path = Part.Wire(edges)
    profile = Part.Wire([Part.makeCircle(p['rail_radius_m']*1000,
                                        v(-a,r),App.Vector(1,0,0))])
    return path.makePipeShell([profile],True,True)


wing_shapes = []
for module, cy in enumerate(p['module_centres_y_m']):
    direction = 1 if module==0 else -1
    g = d.addObject('App::DocumentObjectGroup',f'Modul_{module+1}')
    for side in (-1,1):
        o = d.addObject('Part::Feature',f'Fuehrung_{module}_{side+1}')
        o.Shape = rail((cy+side*p['rail_offset_y_m'])*1000)
        g.addObject(o)
    for i in range(p['wings_per_module']):
        s = perimeter(p['straight_m'],p['radius_m'])*i/p['wings_per_module']
        x,z,tx,tz,beta = state(s,p['straight_m'],p['radius_m'],direction,p['pitch_amplitude_deg'])
        chord = p['chord_m']*1000
        points = []
        xx = [(1-math.cos(math.pi*j/50))/2 for j in range(51)]
        for sign, seq in ((1,xx),(-1,xx[-2:0:-1])):
            points.extend(App.Vector(q*chord,sign*naca_thickness(q)*chord,0) for q in seq)
        points.append(points[0])
        profile = d.addObject('Part::Feature',f'Profil_{module}_{i}')
        profile.Shape = Part.Face(Part.Wire(Part.makePolygon(points).Edges))
        foil = d.addObject('Part::Extrusion',f'Fluegel_{module}_{i}')
        foil.Base = profile
        foil.Dir = App.Vector(0,0,p['span_m']*1000)
        foil.Solid = True
        # Local x: LE->TE; local y: profile thickness; local z: span +y.
        c, s0 = math.cos(beta),math.sin(beta)
        matrix = App.Matrix()
        matrix.A11,matrix.A21,matrix.A31 = -c,0,-s0
        matrix.A12,matrix.A22,matrix.A32 = -s0,0,c
        matrix.A13,matrix.A23,matrix.A33 = 0,1,0
        # Place the generating profile; extrusion direction follows global span.
        profile.Placement = App.Placement(App.Vector(x*1000+.5*chord*c,
                            (cy-p['span_m']/2)*1000,z*1000+.5*chord*s0),App.Rotation(matrix))
        foil.Dir = App.Vector(0,p['span_m']*1000,0)
        foil.addProperty('App::PropertyInteger','Umlaufrichtung')
        foil.Umlaufrichtung = direction
        foil.addProperty('App::PropertyAngle','Nasenwinkel')
        foil.Nasenwinkel = math.degrees(beta)
        g.addObject(profile)
        g.addObject(foil)
        profile.Visibility = False
        wing_shapes.append(foil)
        # Pitch shaft is a placeholder, not a bearing or actuator design.
        shaft = d.addObject('Part::Cylinder',f'Pitchachse_{module}_{i}')
        shaft.Radius,shaft.Height = 4,640
        shaft.Placement = App.Placement(App.Vector(x*1000,(cy-.32)*1000,z*1000),
                                        App.Rotation(App.Vector(0,0,1),App.Vector(0,1,0)))
        g.addObject(shaft)
        for side in (-1,1):
            carriage=d.addObject('Part::Box',f'Schlitten_{module}_{i}_{side+1}')
            carriage.Length,carriage.Width,carriage.Height=36,24,24
            carriage.Placement.Base=App.Vector(x*1000-18,
                                  (cy+side*.32)*1000-12,z*1000-12)
            carriage.addProperty('App::PropertyString','Hinweis')
            carriage.Hinweis='Bauraumplatzhalter um Fuehrung; keine Lager-, Magnet- oder Spaltauslegung'
            g.addObject(carriage)
d.recompute()
for o in d.Objects:
    if hasattr(o,'Shape'):
        assert not o.Shape.isNull(),o.Name
        assert o.Shape.isValid(),o.Name
results = [o for o in d.Objects if hasattr(o,'Shape') and not o.Name.startswith('Profil')]
bb=App.BoundBox()
for o in results: bb.add(o.Shape.BoundBox)
assert bb.XLength<=2100 and bb.YLength<=1700 and bb.ZLength<=600
path=HERE/'Gegenlaeufiger_Fluegelumlauf.FCStd'
d.saveAs(str(path))
Part.export(results,str(HERE/'Gegenlaeufiger_Fluegelumlauf.step'))
App.closeDocument(d.Name)
opened=App.openDocument(str(path))
opened.recompute()
assert all(o.Shape.isValid() for o in opened.Objects if hasattr(o,'Shape'))
report={'saved_and_reopened':True,'wings':len(wing_shapes),
        'bounds_mm':[bb.XLength,bb.YLength,bb.ZLength],
        'structural_validation':False,'magnetic_validation':False}
(HERE/'Umlauf_Pruefbericht.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
