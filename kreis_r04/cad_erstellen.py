#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): Kreis R04, zwei native CAD-Varianten aus Kreis_R03_Layout.FCStd.

- Kreis_R04_Aussenring: alle R03-Koerper, Fluegelschalen mit 0.8-mm-Hinterkante (profil.py).
- Kreis_R04_ohne_Aussenring: aeussere Fuehrungsringe und alle mobilen Koerper der Aussenseite
  (Weltradius Schwerpunkt > 600 mm; ausser Fluegelschale und Pitchwelle) entfernt. Motor- und
  Encoderhuellen der unteren Ebene (lokal +y = aussen) lokal an y = 0 gespiegelt auf die Innenseite.
  Obere Ebene: lokal +y zeigt wegen gegenlaeufiger Bewegung bereits nach innen.

Die Welle bleibt vereinfachte Referenz, kein ausgelegter Kragarm. Fluegelwurzel, Lagerung und
Drehmomentuebertragung ohne Aussenring sind NICHT neu konstruiert. Innenkontur der Hohlschale = R02.

    FREECAD_LIB=/pfad/zu/freecad/lib python3 kreis_r04/cad_erstellen.py
"""
import csv, json, math, os, sys
from pathlib import Path
OUT = Path(__file__).resolve().parent; ROOT = OUT.parent
sys.path.extend([p for p in (os.environ.get('FREECAD_LIB'), '/usr/lib/freecad/lib') if p]+[str(OUT)])
import FreeCAD as App
import Part
import profil

DENSITY = {'CFK': 1600., 'Aluminium': 2700., 'Stahl': 7850.}
LIMIT_MM = (2100, 1700, 600)
KEEP_OUTSIDE = {'FL-CFK-REF', 'PITCH-W01'}
MOVE_INSIDE = {'PITCH-MOT-REF', 'ENC-REF'}


def results(d):
    return [o for o in d.Objects if 'BauteilID' in o.PropertiesList]


def wing_shape():
    def face(pts):
        v = [App.Vector(x, 0, z) for x, z in pts]
        return Part.Face(Part.Wire(Part.makePolygon(v+[v[0]]).Edges))
    shell = face(profil.outline()).cut(face(profil.inner_outline_r02()))
    return shell.extrude(App.Vector(0, profil.SPAN, 0)).translated(App.Vector(0, -profil.SPAN/2, 0))


def clone(d, src):
    o = d.addObject('Part::Feature', src.Name); o.Shape = src.Shape.copy(); o.Placement = src.Placement
    for k in src.PropertiesList:
        if k in ('BauteilID', 'Material_Annahme', 'Prozess_Referenz', 'Bemerkung', 'Freigabe', 'Referenzkoerper',
                 'Gewinde', 'Nennlaenge_mm', 'Kopfform', 'Gewindedarstellung'):
            o.addProperty('App::PropertyString', k); setattr(o, k, getattr(src, k))
    return o


def set_local(o, shape):
    pl = o.Placement; o.Shape = shape; o.Placement = pl


def radius(o):
    c = o.Shape.BoundBox.Center; return math.hypot(c.x, c.y)


def wing_checks(d):
    wings = sorted([o for o in results(d) if o.BauteilID == 'FL-CFK-REF'], key=lambda o: o.Name)
    rows = []
    for o in wings:
        layer, i = int(o.Name.split('_')[0][1:]), int(o.Name.split('_')[1])   # Name W<ebene>_<index>_<quelle>
        c = o.Shape.Solids[0].CenterOfMass if o.Shape.Solids else o.Shape.BoundBox.Center
        rot = o.Placement.Rotation; xl = rot.multVec(App.Vector(1, 0, 0)); yl = rot.multVec(App.Vector(0, 1, 0))
        theta = math.degrees(math.atan2(c.y, c.x)) % 360
        tangent = App.Vector(-c.y, c.x, 0); tangent.normalize()
        rows.append({'name': o.Name, 'ebene': layer, 'index': i, 'schwerpunkt_mm': [round(c.x, 3), round(c.y, 3), round(c.z, 3)],
                     'radius_schwerpunkt_mm': round(math.hypot(c.x, c.y), 3), 'winkel_deg': round(theta, 3),
                     'pitch_deg': round(math.degrees(math.asin(max(-1, min(1, xl.z)))), 4),
                     'sehne_tangential_cos': round(abs(App.Vector(xl.x, xl.y, 0).normalize().dot(tangent)), 6),
                     'spannweite_radial_cos': round(abs(yl.dot(App.Vector(c.x, c.y, 0).normalize())), 6),
                     'bewegungsrichtung': 'gegen_uhrzeigersinn' if App.Vector(xl.x, xl.y, 0).dot(tangent) > 0 else 'im_uhrzeigersinn',
                     'r_min_mm': None, 'r_max_mm': None})
        pts = [v.Point for v in o.Shape.Vertexes]; rr = [math.hypot(p.x, p.y) for p in pts]
        rows[-1]['r_min_mm'] = round(min(rr), 3); rows[-1]['r_max_mm'] = round(max(rr), 3)
    by = {(r['ebene'], r['index']): o for r, o in zip(rows, wings)}
    gaps_same = [by[(l, i)].Shape.distToShape(by[(l, (i+1) % 8)].Shape)[0] for l in (0, 1) for i in range(8) if (l, i) in by and (l, (i+1) % 8) in by]
    gaps_level = [by[(0, i)].Shape.distToShape(by[(1, i)].Shape)[0] for i in range(8) if (0, i) in by and (1, i) in by]
    rings = [o for o in results(d) if o.BauteilID.endswith(('RING-F', 'RING-C'))]
    clear = [min((w.Shape.distToShape(r.Shape)[0] for r in rings if abs(r.Shape.BoundBox.Center.z-w.Shape.BoundBox.Center.z) < 60), default=None) for w in wings]
    return {'fluegel': rows, 'anzahl': len(rows),
            'min_abstand_nachbarfluegel_gleiche_ebene_mm': min(gaps_same) if gaps_same else None,
            'min_abstand_uebereinander_mm': min(gaps_level) if gaps_level else None,
            'min_abstand_fluegel_zu_fuehrungsring_mm': min(c for c in clear if c is not None) if any(c is not None for c in clear) else None,
            'sehnen_halbwinkel_wurzel_deg': math.degrees(math.atan(profil.CHORD/2*math.cos(math.radians(profil.PITCH_DEG))/profil.R_WING[0])), 'teilung_deg': 45,
            'hinweis': 'An der Wurzel r 150 mm bleiben im Grundriss nur ca. 2.3 Grad zwischen Nachbarfluegeln; Abstaende oben sind exakte BRep-Werte.'}


def classify(o):
    mat = o.Material_Annahme.lower()
    if o.Referenzkoerper == 'JA' or o.BauteilID == 'PILOT-REF':return None
    if o.BauteilID.startswith('BF-'):return 'Stahl'
    if 'cfk' in mat:return 'CFK'
    if 'alumin' in mat:return 'Aluminium'
    if 'stahl' in mat or 'wellenwerkstoff' in mat or 'elektroblech' in mat:return 'Stahl'
    return None


def build(src, name, outer):
    d = App.newDocument(name); g = d.addObject('App::DocumentObjectGroup', 'Kreis_R04_Koerper')
    info = d.addObject('App::FeaturePython', 'Konstruktionsstatus')
    for k, v in {'Status': 'REKONSTRUKTION_KONZEPTMODELL_KEINE_FREIGABE', 'Variante': name,
                 'Hinweis': 'Fluegelwurzel/Lagerung/Drehmoment ohne Aussenring nicht konstruiert' if not outer else 'Layout mit Aussenring'}.items():
        info.addProperty('App::PropertyString', k); setattr(info, k, v)
    shell = wing_shape(); removed = moved = 0
    for s in results(src):
        if not outer:
            if s.BauteilID.startswith('R03-RING') and s.Shape.BoundBox.XMax > 700:removed += 1; continue
            if s.Name.startswith('W0_') and s.BauteilID in MOVE_INSIDE:
                o = clone(d, s); local = s.Shape.copy(); local.Placement = App.Placement()
                set_local(o, local.mirror(App.Vector(0, 0, 0), App.Vector(0, 1, 0)))
                o.Bemerkung += ' | R04: auf Innenseite gespiegelt (lokal y -> -y)'; g.addObject(o); moved += 1; continue
            if s.Name.startswith('W') and radius(s) > 600 and s.BauteilID not in KEEP_OUTSIDE:removed += 1; continue
        o = clone(d, s); g.addObject(o)
        if s.BauteilID == 'FL-CFK-REF':
            set_local(o, shell.copy()); o.Bemerkung += ' | R04: Aussenkontur NACA0012 + 0.4*q^10 mm (HK 0.8 mm), Innenkontur R02'
    d.recompute()
    parts = results(d)
    for o in parts:assert not o.Shape.isNull() and o.Shape.isValid(), o.Name
    d.saveAs(str(OUT/f'{name}.FCStd'))
    vehicle = [o for o in parts if o.BauteilID != 'PILOT-REF']
    Part.export(vehicle, str(OUT/f'{name}.step'))
    bb = App.BoundBox()
    for o in vehicle:bb.add(o.Shape.BoundBox)
    dims = [bb.XLength, bb.YLength, bb.ZLength]
    rep = {'ergebniskoerper': len(parts), 'entfernt': removed, 'motor_encoder_umgesetzt': moved,
           'fahrzeug_huelle_mm': dims, 'innerhalb_2100x1700x600': all(a <= b for a, b in zip(dims, LIMIT_MM)),
           'alle_formen_gueltig': True, 'fluegelpruefung': wing_checks(d)}
    vol = {}
    for o in vehicle:
        key = (o.BauteilID, o.Material_Annahme, classify(o)); n, v = vol.get(key, (0, 0.)); vol[key] = (n+1, v+o.Shape.Volume)
    App.closeDocument(d.Name)
    opened = App.openDocument(str(OUT/f'{name}.FCStd')); opened.recompute()
    rep['gespeichert_und_wieder_geoeffnet'] = all(o.Shape.isValid() for o in results(opened)); App.closeDocument(opened.Name)
    return rep, vol


def main():
    src = App.openDocument(str(ROOT/'kreis_r03'/'Kreis_R03_Layout.FCStd'))
    report = {'status': 'REKONSTRUKTION_KONZEPTMODELLE_KEINE_FERTIGUNGSFREIGABE', 'dichten_kg_m3': DENSITY,
              'hinterkante_mm': 2*profil.half_thickness_mm(1.), 'quelle': 'kreis_r03/Kreis_R03_Layout.FCStd'}
    rows = []
    for name, outer in (('Kreis_R04_Aussenring', True), ('Kreis_R04_ohne_Aussenring', False)):
        rep, vol = build(src, name, outer); report[name] = rep
        for (ident, mat, cls), (n, v) in sorted(vol.items()):
            rows.append({'Variante': name, 'BauteilID': ident, 'Material_Annahme': mat, 'Werkstoffklasse': cls or 'nicht_bewertet',
                         'Anzahl': n, 'Volumen_cm3': round(v/1000, 4), 'Dichte_kg_m3': DENSITY.get(cls, ''),
                         'Masse_kg': round(v*1e-9*DENSITY[cls], 5) if cls else ''})
        print(name, {k: v for k, v in rep.items() if k != 'fluegelpruefung'}, flush=True)
    App.closeDocument(src.Name)
    (OUT/'CAD_Pruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    with (OUT/'CAD_Volumen.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
    main()
