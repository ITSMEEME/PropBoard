#!/usr/bin/python3
"""Reproduzierbare Konzeptmodelle; keine Fertigungs- oder Flugfreigabe."""
import json
import math
from pathlib import Path
import sys

sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App
import Part

OUT = Path(__file__).resolve().parent
REPORT = {}


def document(name):
    d = App.newDocument(name)
    info = d.addObject('App::FeaturePython', 'Hinweise')
    info.addProperty('App::PropertyString', 'Status')
    info.Status = 'KONZEPT: keine Tragfaehigkeits-, Schutz- oder Flugvalidierung'
    info.addProperty('App::PropertyString', 'NeueAnnahmen')
    info.NeueAnnahmen = ('Rahmenquerschnitte, Motorplatzhalter, Deckstuetzen und '
                         'Fahrwerk sind neue Visualisierungsannahmen, keine Originalrekonstruktion.')
    return d


def group(d, name):
    return d.addObject('App::DocumentObjectGroup', name)


def box(d, g, name, dimensions, origin):
    o = d.addObject('Part::Box', name)
    o.Length, o.Width, o.Height = dimensions
    o.Placement.Base = App.Vector(*origin)
    g.addObject(o)
    return o


def cylinder(d, g, name, radius, height, origin):
    o = d.addObject('Part::Cylinder', name)
    o.Radius, o.Height = radius, height
    o.Placement.Base = App.Vector(*origin)
    g.addObject(o)
    return o


def check_save(d):
    d.recompute()
    shapes = [o for o in d.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()]
    invalid = [o.Name for o in shapes if not o.Shape.isValid()]
    if invalid:
        raise RuntimeError(invalid)
    path = OUT / (d.Name + '.FCStd')
    d.saveAs(str(path))
    name = d.Name
    App.closeDocument(name)
    reopened = App.openDocument(str(path))
    reopened.recompute()
    assert all(o.Shape.isValid() for o in reopened.Objects
               if hasattr(o, 'Shape') and not o.Shape.isNull())
    REPORT[name] = {'saved_and_reopened': True, 'valid_shapes': len(shapes)}
    App.closeDocument(reopened.Name)


def board(name, packs=False):
    d = document(name)
    p = d.addObject('Spreadsheet::Sheet', 'Parameter')
    for row, (label, value, alias) in enumerate([
        ('Rotordurchmesser', '650 mm', 'RotorD'),
        ('Raster X', '690 mm', 'RasterX'),
        ('Raster Y halber Abstand', '505 mm', 'RasterY'),
        ('Ring aussen', '680 mm', 'RingD'),
        ('Ring innen', '668 mm', 'RingInnenD'),
        ('Ringhoehe', '70 mm', 'RingH'),
        ('Deck Laenge', '1200 mm', 'DeckL'),
        ('Deck Breite', '300 mm', 'DeckB'),
        ('Deck Hoehe', '60 mm', 'DeckH'),
        ('Deck Unterseite', '170 mm', 'DeckZ'),
    ], 1):
        p.set(f'A{row}', label)
        p.set(f'B{row}', value)
        p.setAlias(f'B{row}', alias)
    frame, drives, rings, rotors, deckg, battery, feet = [group(d, n) for n in
        ('Rahmen_Annahme', 'Motoren_Platzhalter', 'Ringe_KeinSchutznachweis',
         'Rotorwirkflaechen_Referenz', 'Deck', 'Akku_Gehaeuse', 'Fahrwerk_Annahme')]
    deck = box(d, deckg, 'Standdeck', (1200, 300, 60), (-600, -150, 170))
    for prop, expr in [('Length', 'DeckL'), ('Width', 'DeckB'), ('Height', 'DeckH')]:
        deck.setExpression(prop, 'Parameter.' + expr)
    deck.setExpression('Placement.Base.x', '-Parameter.DeckL / 2')
    deck.setExpression('Placement.Base.y', '-Parameter.DeckB / 2')
    deck.setExpression('Placement.Base.z', 'Parameter.DeckZ')
    # New illustrative structure, deliberately independent of historical claims.
    box(d, frame, 'Laengstraeger', (1500, 60, 30), (-750, -30, 35))
    for i, x in enumerate((-690, 0, 690)):
        arm = box(d, frame, f'Quertraeger{i}', (40, 1010, 30), (x-20, -505, 35))
        arm.setExpression('Placement.Base.x', f'{i-1} * Parameter.RasterX - 20 mm')
        arm.setExpression('Placement.Base.y', '-Parameter.RasterY')
        arm.setExpression('Width', '2 * Parameter.RasterY')
    for i, x in enumerate((-580, 580)):
        box(d, frame, f'Deckstuetze{i}', (20, 40, 105), (x-10, -20, 65))
    for ix in range(3):
        for iy, sy in enumerate((-1, 1)):
            tag = f'{ix}{iy}'
            x, y = (ix-1)*690, sy*505
            motor = cylinder(d, drives, 'Motor'+tag, 36, 50, (x, y, -25))
            outer = cylinder(d, rings, 'RingAussen'+tag, 340, 70, (x, y, -35))
            inner = cylinder(d, rings, 'RingInnen'+tag, 334, 70, (x, y, -35))
            ring = d.addObject('Part::Cut', 'Ring'+tag)
            ring.Base, ring.Tool = outer, inner
            rings.addObject(ring)
            rotor = cylinder(d, rotors, 'RotorReferenz'+tag, 325, 1, (x, y, 0))
            for o in (motor, outer, inner, rotor):
                o.setExpression('Placement.Base.x', f'{ix-1} * Parameter.RasterX')
                o.setExpression('Placement.Base.y', f'{sy} * Parameter.RasterY')
            outer.setExpression('Radius', 'Parameter.RingD / 2')
            inner.setExpression('Radius', 'Parameter.RingInnenD / 2')
            for o in (outer, inner):
                o.setExpression('Height', 'Parameter.RingH')
                o.setExpression('Placement.Base.z', '-Parameter.RingH / 2')
            rotor.setExpression('Radius', 'Parameter.RotorD / 2')
            outer.Visibility = False
            inner.Visibility = False
            rotor.Visibility = False
    for i, (x, y) in enumerate([(-500,-110),(-500,110),(500,-110),(500,110)]):
        box(d, feet, f'Landefuss{i}', (40, 40, 125), (x-20, y-20, -90))
    pack_objects = []
    if packs:
        for i, x in enumerate((-440,-190,190,440)):
            for j, y in enumerate((-57,57)):
                pack_objects.append(box(d, battery, f'Tattu_{i}_{j}',
                                        (230,104,70), (x-115,y-52,70)))
    d.recompute()
    # Parameter change and reset, then direct geometry checks.
    p.set('B1', '600 mm')
    d.recompute()
    assert abs(d.getObject('RotorReferenz00').Radius.Value - 300) < 1e-8
    p.set('B1', '650 mm')
    d.recompute()
    results = [o for g in (frame, drives, deckg, battery, feet) for o in g.Group]
    results += [o for o in rings.Group if o.TypeId == 'Part::Cut']
    bounds = App.BoundBox()
    for o in results:
        bounds.add(o.Shape.BoundBox)
    assert all(abs(a-b)<1e-6 for a,b in zip(
        (bounds.XLength,bounds.YLength,bounds.ZLength), (2060,1690,320)))
    if packs:
        distances = [a.Shape.distToShape(b.Shape)[0] for i,a in enumerate(pack_objects)
                     for b in pack_objects[i+1:]]
        assert min(distances) >= 10-1e-6
        other = [o for o in results if o not in pack_objects]
        assert all(a.Shape.distToShape(b.Shape)[0] > 0 for a in pack_objects for b in other)
    check_save(d)
    REPORT[name].update({'outer_mm': [2060,1690,320],
                         'rotor_parameter_change_and_reset': True,
                         'packs': len(pack_objects),
                         'pack_clearances_checked': packs})


board('Hexacopter_650_Konzept')
board('Hexacopter_Tattu41000_8Packs', True)
d = document('Tmotor_X605_Bauraum')
g = group(d, 'VereinfachterBauraum')
cylinder(d, g, 'Motorkoerper', 36, 112.3, (0,0,0))
envelope = box(d, g, 'Referenzhuelle', (124.8,72,121), (-36,-36,0))
envelope.addProperty('App::PropertyString', 'Annahme')
envelope.Annahme = 'Achse bei x=0; asymmetrische Huelle x=-36 bis +88.8; Bezugslage unbestaetigt'
check_save(d)
(OUT / 'Pruefbericht.json').write_text(json.dumps(REPORT, indent=2), encoding='utf-8')
print(json.dumps(REPORT, indent=2))
