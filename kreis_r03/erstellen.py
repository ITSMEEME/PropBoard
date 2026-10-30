#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): Kreis R03 Layoutmodell aus gespeicherten R02-Dateien.

Uebernimmt die 102 Ergebniskoerper der mobilen R02-Baugruppe (02_Schlitten_R02_Detail.FCStd)
16-fach auf die Kreisbahn r = 450 mm (8 je Ebene, z = -120/+120 mm, gegenlaeufig) und die
zentralen Einbaureferenzen (Deck, Akku, Fussauflage, Kabelreferenzen) samt deren Verbindungsschrauben
aus 00_Horizontal_Z_R02_Montage.FCStd. Fuehrungen als geschlossene C-Ringe r 130/770 mm.

Layoutmodell: Rahmenanbindung, Ringhalter, Schutz und Kabelwege sind NICHT konstruiert.

    FREECAD_LIB=/pfad/zu/freecad/lib python3 kreis_r03/erstellen.py
    (oder: freecadcmd kreis_r03/erstellen.py)
"""
import csv, json, math, os, sys
from pathlib import Path
OUT = Path(__file__).resolve().parent; ROOT = OUT.parent
sys.path.extend([p for p in (os.environ.get('FREECAD_LIB'), '/usr/lib/freecad/lib') if p]+[str(ROOT/'cad')])
import FreeCAD as App
import Part
from umlauf_kinematik import state, perimeter

R02 = ROOT/'horizontal_z_r02'
RADIUS, LEVELS, PITCH = .45, (-120, 120), 12
FIELDS = ['BauteilID', 'Material_Annahme', 'Prozess_Referenz', 'Bemerkung', 'Freigabe', 'Referenzkoerper']
CENTRAL = {'R02-DECK', 'R02-DECK-HP', 'R02-DECK-STAND', 'R02-FOOT-ADAPTER', 'R02-FOOT-INSERT', 'R02-FOOT-MAT',
           'R02-BAT-BRIDGE', 'R02-BAT-CASE', 'R02-BAT-GUARD', 'R02-BAT-LID', 'R02-BAT-PAD', 'R02-BAT-SEAL', 'R02-BAT-SPACER',
           'R02-BAT-TRAY', 'R02-TRAY-CLAMP', 'R02-TRAY-ISO', 'R02-POTTING', 'R02-HV-CABLE-REF', 'R02-LV-CABLE-REF'}
PITCHED = {'FL-CFK-REF', 'PITCH-G01'}       # wie konstruktion/erstellen.py oriented_copy


def results(d):
    return [o for o in d.Objects if 'BauteilID' in o.PropertiesList]


def mark(o, src, note='', **override):
    for k in FIELDS:
        o.addProperty('App::PropertyString', k); setattr(o, k, override.get(k, getattr(src, k) if src else ''))
    if note:o.Bemerkung = (o.Bemerkung+' | ' if o.Bemerkung else '')+note
    for k in ('Gewinde', 'Nennlaenge_mm', 'Kopfform', 'Gewindedarstellung'):
        if src and k in src.PropertiesList:
            o.addProperty('App::PropertyString', k); setattr(o, k, getattr(src, k))
    return o


def copy(d, g, src, name, placement=None, note=''):
    o = d.addObject('Part::Feature', name); o.Shape = src.Shape.copy()
    if placement is not None:o.Placement = placement.multiply(src.Placement)
    g.addObject(o)
    return mark(o, src, note)


def frame(tangent, pitch_deg):
    """Lokales x = Bewegungsrichtung (mit Pitch), z oben, y = z x x (wie R02)."""
    t = App.Vector(*tangent); a = math.radians(pitch_deg)
    x = t*math.cos(a)+App.Vector(0, 0, math.sin(a)); z = t*(-math.sin(a))+App.Vector(0, 0, math.cos(a)); y = z.cross(x)
    m = App.Matrix()
    for col, v in enumerate((x, y, z), 1):
        for row, val in enumerate((v.x, v.y, v.z), 1):setattr(m, f'A{row}{col}', val)
    return App.Rotation(m)


def ring(rlo, rhi, z0, h):
    return Part.makeCylinder(rhi, h, App.Vector(0, 0, z0)).cut(Part.makeCylinder(rlo, h, App.Vector(0, 0, z0)))


def guides(d, g, levels=LEVELS, sides=(-1, 1), revision='R03'):
    """Geschlossene C-Ringe analog konstruktion/erstellen.py rails(), Kreis statt Stadion."""
    n = 0
    for level in levels:
        for side in sides:
            r = 450+side*320
            spec = [('C_Ring_Rueckwand', (r-16, r-10) if side == -1 else (r+10, r+16), level-30, 60, 'RING-C', 'Aluminium TBD'),
                    ('C_Ring_Flansch_unten', (r-16, r+12) if side == -1 else (r-12, r+16), level-30, 8, 'RING-F', 'Aluminium TBD'),
                    ('C_Ring_Flansch_oben', (r-16, r+12) if side == -1 else (r-12, r+16), level+22, 8, 'RING-F', 'Aluminium TBD'),
                    ('Rueckschluss_Ring', (r-20, r-16) if side == -1 else (r+16, r+20), level-22, 44, 'RING-JOCH', 'Elektroblech TBD'),
                    ('Stator_Wicklungsraum_Ring', (r-16, r-12) if side == -1 else (r+12, r+16), level-15, 30, 'RING-STATOR-REF', 'Wicklungsbauraum'),
                    ('Energie_Primaer_Ring', (r-16, r-12) if side == -1 else (r+12, r+16), level+16, 6, 'RING-IPT-REF', 'Induktivsystem TBD')]
            for name, (lo, hi), z0, h, ident, mat in spec:
                o = d.addObject('Part::Feature', f'{name}_{"aussen" if side > 0 else "innen"}_{level}'); o.Shape = ring(lo, hi, z0, h); g.addObject(o)
                mark(o, None, BauteilID=f'{revision}-{ident}', Material_Annahme=mat, Prozess_Referenz='Geschlossene Ringhuelle; Segmentierung offen',
                     Bemerkung='Layout-Huelle. Ringhalter, Segmentstoesse, Rahmenanbindung und Lastnachweis NICHT konstruiert.',
                     Freigabe='LAYOUT_KEINE_FREIGABE', Referenzkoerper='JA' if 'REF' in ident else 'NEIN')
                n += 1
    return n


def place_wings(d, g, moving):
    length = perimeter(0, RADIUS); placed = []
    for layer, z in enumerate(LEVELS):
        direction = 1 if layer == 0 else -1
        for i in range(8):
            x, y, tx, ty, _ = state(i*length/8, 0, RADIUS)
            for src in moving:
                rot = frame((direction*tx, direction*ty, 0), PITCH if src.BauteilID in PITCHED else 0)
                o = copy(d, g, src, f'W{layer}_{i}_{src.Name}', App.Placement(App.Vector(x*1000, y*1000, z), rot),
                         'R03-Kreisposition; Quelle 02_Schlitten_R02_Detail')
                placed.append(o)
    return placed


def main():
    mdoc = App.openDocument(str(R02/'02_Schlitten_R02_Detail.FCStd')); moving = results(mdoc)
    adoc = App.openDocument(str(R02/'00_Horizontal_Z_R02_Montage.FCStd'))
    d = App.newDocument('Kreis_R03_Layout')
    info = d.addObject('App::FeaturePython', 'Konstruktionsstatus')
    for k, v in {'Status': 'REKONSTRUKTION_LAYOUTMODELL_KEINE_FREIGABE', 'Revision': 'R03 Kreis',
                 'Hinweis': 'Rahmenanbindung, Ringhalter, Schutz und Kabelwege nicht konstruiert'}.items():
        info.addProperty('App::PropertyString', k); setattr(info, k, v)
    gw = d.addObject('App::DocumentObjectGroup', '10_Mobile_Fluegelbaugruppen_Kreis')
    placed = place_wings(d, gw, moving)
    gr = d.addObject('App::DocumentObjectGroup', '08_Fuehrungsringe_Layout'); nring = guides(d, gr)
    gc = d.addObject('App::DocumentObjectGroup', '20_Zentrale_Einbaureferenzen_aus_R02')
    central = [o for o in results(adoc) if o.BauteilID in CENTRAL]; names = {o.Name for o in central}
    joints = json.loads((R02/'Verbindungen.json').read_text())
    bolts = {j['bolt'] for j in joints if j.get('document') == adoc.Name and j.get('targets') and set(j['targets']) <= names}
    central += [adoc.getObject(b) for b in sorted(bolts) if adoc.getObject(b) is not None]
    for o in central:copy(d, gc, o, 'Z_'+o.Name, note='Unveraenderte R02-Lage; Anbindung an neuen Rahmen offen')
    gp = d.addObject('App::DocumentObjectGroup', 'Pilot_Referenz_KEIN_Bauteil')
    for o in results(adoc):
        if o.BauteilID == 'PILOT-REF':copy(d, gp, o, 'P_'+o.Name)
    d.recompute()
    parts = results(d)
    for o in parts:assert not o.Shape.isNull() and o.Shape.isValid(), o.Name
    d.saveAs(str(OUT/'Kreis_R03_Layout.FCStd'))
    vehicle = [o for o in parts if o.BauteilID != 'PILOT-REF']
    Part.export(vehicle, str(OUT/'Kreis_R03_Layout.step'))
    bb = App.BoundBox()
    for o in vehicle:bb.add(o.Shape.BoundBox)
    report = {'status': 'REKONSTRUKTION_LAYOUTMODELL', 'ergebniskoerper': len(parts), 'mobile_koerper': len(placed),
              'mobile_koerper_je_baugruppe': len(moving), 'ring_koerper': nring, 'zentrale_referenzen': len(central),
              'pilot_referenz': len(parts)-len(vehicle), 'fahrzeug_huelle_mm': [bb.XLength, bb.YLength, bb.ZLength],
              'alle_formen_gueltig': True, 'fertigungsfreigabe': False, 'flugnachweis': False}
    for doc_ in (d, mdoc, adoc):App.closeDocument(doc_.Name)
    opened = App.openDocument(str(OUT/'Kreis_R03_Layout.FCStd')); opened.recompute()
    report['gespeichert_und_wieder_geoeffnet'] = all(o.Shape.isValid() for o in results(opened)); App.closeDocument(opened.Name)
    (OUT/'Pruefbericht.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
