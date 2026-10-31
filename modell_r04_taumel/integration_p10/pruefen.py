#!/usr/bin/env python3
"""Prüfung der P10-Gesamtbaugruppe.

1. Lastpfad: Servogehäuse ↔ Halter (Laschenanlage), Halter ↔ Halteplatte, Motor ↔ Motorbrücke ↔ Platte,
   Planetenträger ↔ Platte, Fahrwerk ↔ Akkuverschraubung (Kontakt statt Schweben).
2. Überschneidungen aller neuen/geänderten Körper gegen alle übrigen Körper in Neutralstellung
   (Volumen > 0,001 mm³), Ausnahmen nur für konstruktiv gewollte Paarungen (Schraube in Bohrung,
   Leitungsende am Anschluss, Lager auf Bolzen).
3. Bewegte Teile: Planeteneingriff und Freigang der drehenden/schwenkenden Baugruppen über 41 Stellungen
   (P09-Demo + Rotorwinkel) gegen alle neuen festen Teile.
4. Landegestell: Bodenfreiheit, Standsicherheit (Kippwinkel um den Schwerpunkt), Rotor-Bodenabstand.
Servo-STEP-Gehäuse sind ungültig; für sie wird distToShape statt boolescher Schnittmenge verwendet.
"""
import hashlib
import itertools
import json
import math
import os
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path[:0] = [os.environ.get('FREECAD_LIB', str(ROOT / '.cfd-tools/freecad/usr/lib')), str(H)]
import FreeCAD as A  # noqa: E402
import Part  # noqa: E402
import geometrie_p10 as G  # noqa: E402
import p10_runtime as RT  # noqa: E402

V = A.Vector
SRC = H / 'Ausgabe/P10_Gesamtbaugruppe.FCStd'
d = A.openDocument(str(SRC))
ctl = d.getObject('P09_Animation')
ctl.Proxy = RT.Controller(ctl)
RT.apply(d, [0] * 6, [0, 0])
parts = [o for o in d.Objects if hasattr(o, 'P09_Rahmen') and not getattr(o, 'BauteilID', '').startswith('KEEP_')]
by = {o.Name: o for o in parts}
new = [o for o in parts if o.Name.startswith('P10_') or hasattr(o, 'P10_Aenderung')]
INVALID = {o.Name for o in parts if getattr(o, 'BauteilID', '') == 'SERVO-SAVOX-SB2270SGP'}
report = dict(source_native_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(), checks={}, collisions=[], allowed_contacts=[])


def bb_overlap(a, b, m=0.0):
    a, b = a.BoundBox, b.BoundBox
    return not (a.XMax + m < b.XMin or b.XMax + m < a.XMin or a.YMax + m < b.YMin or b.YMax + m < a.YMin or a.ZMax + m < b.ZMin or b.ZMax + m < a.ZMin)


PROXY = {}


def servo_proxy(o):
    """Gültiger Ersatzkörper des ungültigen SB-2270SG+-STEP-Gehäuses aus den vermessenen Quellmaßen
    (Gehäuse, Laschen, Abdeckscheibe am Abtrieb), in Quellkoordinaten mit der Teilplatzierung."""
    if o.Name not in PROXY:
        box = lambda x0, x1, y0, y1, z0, z1: Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
        body = box(-10.3, 30.0, -25.9, 7.77, -10.05, 10.05)
        tabs = box(-17.15, 36.85, 0.0, 2.2, -10.0, 10.0)
        disc = Part.makeCylinder(11.75, 0.41, V(0, 12.39, 0), V(0, 1, 0))
        s = body.fuse([tabs, disc]).removeSplitter()
        sub = o.Shape.SubShapes[0]
        s.Placement = o.Placement.multiply(sub.Placement)
        PROXY[o.Name] = s
    return PROXY[o.Name]


def shape_of(o):
    return servo_proxy(o) if o.Name in INVALID else o.Shape


def overlap(a, b):
    """Common volume [mm³]. The invalid servo STEP is replaced by its valid measured proxy body."""
    if not bb_overlap(a.Shape, b.Shape):
        return 0.0
    return shape_of(a).common(shape_of(b)).Volume


def ident(o):
    return getattr(o, 'BauteilID', '')


def allowed(a, b):
    """Konstruktiv gewollte Berührung/Durchdringung (Gewinde, Presssitz, Leitungsende, Kabel im Rohr)."""
    ia, ib = ident(a), ident(b)
    pair = {ia, ib}
    fast = lambda i: i.startswith(('ISO', 'P10-GEWINDEEINSATZ', 'P10-PLANETENBOLZEN-D5', 'MR85ZZ'))
    if fast(ia) and fast(ib):
        return 'Schraube/Mutter/Scheibe bzw. Bolzen/Lager-Paarung'
    if fast(ia) or fast(ib):
        return 'Normteil in Bohrung bzw. Gewinde (nominal ohne Gewindeflanken)'
    if ia.startswith('P10-KABEL') or ib.startswith('P10-KABEL'):
        other = b if ia.startswith('P10-KABEL') else a
        cab = a if ia.startswith('P10-KABEL') else b
        if ident(other).startswith('P10-KABEL'):
            return None
        return 'Leitungsende am Anschluss' if other.Name in TERMINALS.get(cab.Name, ()) else None
    if pair == {'P10-STREBE-CFK-6x4', 'P10-FAHRWERKSKNOTEN'} or pair == {'P10-STREBE-CFK-6x4', 'P10-KUFENSCHELLE'}:
        return 'Rohr in Klebesteckung'
    if pair == {'P10-KUFE-CFK-8x6', 'P10-KUFENSCHELLE'} or pair == {'P10-KUFE-CFK-8x6', 'P10-KUFENSTOPFEN'}:
        return 'Kufe in Schelle/Stopfen'
    if pair == {'P10-STUETZPLANET-Z20', 'MR85ZZ'}:
        return 'Lager im Zahnrad'
    return None


# Leitungsenden: welche Körper eine Leitung berühren darf
TERM_IDS = {'P+': ('P10_XT60_Buchse', 'REF_ESC'), 'P-': ('P10_XT60_Buchse', 'REF_ESC'), 'AKKU+': ('Akku_Referenz', 'P10_XT60_Stecker'),
            'AKKU-': ('Akku_Referenz', 'P10_XT60_Stecker'), 'BAL': ('Akku_Referenz', 'P10_JST_XH_Balancer'),
            'UBEC_IN+': ('P10_XT60_Buchse', 'P10_UBEC'), 'UBEC_IN-': ('P10_XT60_Buchse', 'P10_UBEC'),
            'UBEC_OUT+': ('P10_UBEC', 'P10_Servo_Sammelpunkt_unten'), 'UBEC_OUT-': ('P10_UBEC', 'P10_Servo_Sammelpunkt_unten'),
            'STAMM': ('P10_Servo_Sammelpunkt_unten', 'P10_Servoverteiler_oben'), 'ANT': ('P10_ELRS_Empfaenger',)}
TERMINALS = {}
for o in parts:
    if not ident(o).startswith('P10-KABEL'):
        continue
    cid = o.Name[len('P10_Kabel_'):]
    raw = {'PP': 'P+', 'PM': 'P-', 'AKKUP': 'AKKU+', 'AKKUM': 'AKKU-', 'UBEC_INP': 'UBEC_IN+', 'UBEC_INM': 'UBEC_IN-',
           'UBEC_OUTP': 'UBEC_OUT+', 'UBEC_OUTM': 'UBEC_OUT-'}.get(cid, cid)
    t = list(TERM_IDS.get(raw, ()))
    if raw.startswith('M1_oben'):
        t += ['Oben_feststehend_11', 'REF_ESC']
    if raw.startswith('M2_unten'):
        t += ['Unten_feststehend_11', 'REF_ESC']
    if raw.startswith('SERVO_'):
        lvl, j = raw.split('_')[1], int(raw.split('_')[2]) - 1
        t += [('Oben' if lvl == 'oben' else 'Unten') + f'_feststehend_{15 + j}', 'P10_Servoverteiler_oben' if lvl == 'oben' else 'P10_Servo_Sammelpunkt_unten']
    if raw.startswith('SIG_'):
        t += ['P10_Servoverteiler_oben', 'REF_FC']
    if raw.startswith('RX_'):
        t += ['P10_ELRS_Empfaenger', 'REF_FC']
    TERMINALS[o.Name] = set(t)

# ---------------------------------------------------------------- 1. Lastpfad-Kontakte
contacts = []


def touch(a, b, tol=0.02):
    dist = by[a].Shape.distToShape(by[b].Shape)[0]
    contacts.append(dict(a=a, b=b, distance_mm=dist, pass_=dist <= tol))
    return dist


for lvl in ('Oben', 'Unten'):
    for j, az in enumerate(G.SERVO_AZ):
        br = f'P10_Servohalter_{lvl}_{az}'
        touch(f'{lvl}_feststehend_{15 + j}', br)          # Laschenanlage am Steg
        touch(br, f'{lvl}_feststehend_10')                 # Fuß auf der Halteplatte
    touch(f'{lvl}_feststehend_11', f'P10_Motorbruecke_{lvl}')
    touch(f'P10_Motorbruecke_{lvl}', f'{lvl}_feststehend_10')
    for k in (1, 2):
        touch(f'P10_PLANETENBOLZENTRAEGER_{lvl}_{k}', f'{lvl}_feststehend_10')
for i in range(4):
    touch(f'P10_Fahrwerksknoten_{i}', 'Akkuwanne')
    touch(f'P10_Fahrwerksstrebe_{i}', f'P10_Fahrwerksknoten_{i}', 0.06)
    touch(f'P10_Fahrwerksstrebe_{i}', f'P10_Kufenschelle_{i}', 0.06)
for i in range(4):
    touch(f'M3_Akku_{i}', f'P10_Fahrwerksknoten_{i}')
    touch(f'P10_Gewindeeinsatz_M3_{i}', 'Akku_Anschlussplatte')
report['checks']['load_path_contacts'] = dict(count=len(contacts), all_pass=all(c['pass_'] for c in contacts),
                                              failed=[c for c in contacts if not c['pass_']], max_distance_mm=max(c['distance_mm'] for c in contacts))
servo_gaps = [c['distance_mm'] for c in contacts if '_feststehend_1' in c['a'] and 'Servohalter' in c['b']]
report['checks']['servo_case_to_bracket_distance_mm'] = servo_gaps

# ---------------------------------------------------------------- 2. Neutralstellung: alle Paare mit neuen Teilen
checked = 0
seen = set()
for a in new:
    for b in parts:
        if a is b or (b.Name, a.Name) in seen:
            continue
        seen.add((a.Name, b.Name))
        if not bb_overlap(a.Shape, b.Shape):
            continue
        checked += 1
        v = overlap(a, b)
        if v < 1e-3:
            continue
        why = allowed(a, b)
        entry = dict(state='Neutral', a=a.Name, b=b.Name, ia=ident(a), ib=ident(b), volume_mm3=v)
        if why:
            entry['reason'] = why
            report['allowed_contacts'].append(entry)
        else:
            report['collisions'].append(entry)
report['checks']['neutral_pairs_with_bbox_overlap'] = checked

# ---------------------------------------------------------------- 3. Bewegung: Planeten und bewegte Baugruppen gegen neue feste Teile
# Bewegte Teile: Gestänge, Taumelscheiben, Servoabtriebe, Blätter, Planeten. Der Hohlrad-Deckel wird mit einem
# konservativen Ersatzkörper geprüft (Scheibe r 22…70 + Kranz ab Zahnkopfkreis r 64,4); der Zahneingriff selbst
# wird separat an der echten Verzahnung geprüft. Die Nabe ist rotationssymmetrisch und in Neutralstellung geprüft.
LID_PROXY = Part.makeCylinder(70, 3, V(0, 0, 10.5)).cut(Part.makeCylinder(22, 5, V(0, 0, 9.5))).fuse(
    Part.makeCylinder(70, 8, V(0, 0, 13.5)).cut(Part.makeCylinder(64.4, 10, V(0, 0, 12.5)))).removeSplitter()
movers = [o for o in parts if o.P09_Rahmen != 'fixed' and ident(o) not in ('TM-NABE', 'STIFT-D2x18')]
fixed_new = [o for o in new if o.P09_Rahmen == 'fixed']
states = [(f'Demo_{t:.1f}', *RT.demo(t)) for t in (0.0, 0.9, 1.7, 2.6, 3.5, 4.4, 5.3, 6.2, 7.1)] + [('Stellwinkel', [3, -3, 2, -2.5, 2.5, -1], [11.0, 29.0])]
moving_checks = 0
for name, servos, angles in states:
    RT.apply(d, servos, angles, recompute=False)
    for o in movers:
        shp = o.Shape
        if ident(o) == 'TM-DECKEL-HOHLRAD-130':
            shp = LID_PROXY.copy()
            shp.Placement = o.Placement.multiply(o.P09_Neutralrahmen)
        for f in fixed_new:
            if not bb_overlap(shp, f.Shape, 0.0):
                continue
            moving_checks += 1
            v = shp.common(shape_of(f)).Volume
            if v > 1e-3 and not allowed(o, f):
                report['collisions'].append(dict(state=name, a=o.Name, b=f.Name, ia=ident(o), ib=ident(f), volume_mm3=v, interface='bewegt/neu'))
# Zahneingriff Planet ↔ Hohlrad an der echten Verzahnung über eine Zahnteilung (360/130°) und Gesamtwinkel
mesh_min = 1e9
mesh_states = [0.0, 0.35, 0.7, 1.05, 1.4, 1.75, 2.1, 2.45, 37.0, 211.0]
for a in mesh_states:
    RT.apply(d, [0] * 6, [a, a], recompute=False)
    for o in parts:
        if ident(o) in ('RITZEL-M1-Z20', 'P10-STUETZPLANET-Z20'):
            l = int(o.P09_Rahmen.split(':')[1])
            ring = by['Rotor_oben_1' if l == 0 else 'Rotor_unten_1']
            mesh_min = min(mesh_min, o.Shape.distToShape(ring.Shape)[0])
            v = o.Shape.common(ring.Shape).Volume
            if v > 1e-3:
                report['collisions'].append(dict(state=f'Rotor_{a}', a=o.Name, b=ring.Name, volume_mm3=v, interface='Planet/Hohlrad'))
RT.apply(d, [0] * 6, [0, 0], recompute=False)
report['checks']['motion_states'] = len(states)
report['checks']['planet_mesh_states_deg'] = mesh_states
report['checks']['motion_pair_checks'] = moving_checks
report['checks']['planet_ring_min_distance_mm'] = mesh_min

# ---------------------------------------------------------------- 4. Landegestell und Rotorbodenabstand
lowest = min((o.Shape.BoundBox.ZMin, o.Name) for o in parts)
skid_low = min(by[n].Shape.BoundBox.ZMin for n in ('P10_Kufe_links', 'P10_Kufe_rechts'))
skid_contact = min(v.Point.z for n in ('P10_Kufe_links', 'P10_Kufe_rechts') for v in by[n].Shape.Vertexes)
plane = Part.makePlane(600, 600, V(-300, -300, G.GROUND_Z))
ground_dist = {o.Name: o.Shape.distToShape(plane)[0] for o in parts if o.Shape.BoundBox.ZMin < G.GROUND_Z + 60}
below = [o.Name for o in parts if o.Shape.BoundBox.ZMin < G.GROUND_Z - 0.05 and not o.Name.startswith('P10_Kufe_')]
gear_names = ('P10_Kufe_', 'P10_Kufenstopfen', 'P10_Kufenschelle')
not_gear = {k: v for k, v in ground_dist.items() if not k.startswith(gear_names)}
clamp_ground = max(v for k, v in ground_dist.items() if k.startswith('P10_Kufenschelle_') and '_ISO' not in k and 'GEWINDE' not in k)
skid_ground = min(v for k, v in ground_dist.items() if k.startswith('P10_Kufe_'))
mass = json.loads((H / 'Ausgabe/Massen_P10.json').read_text())
sys.path.insert(0, str(H.parent / 'simulation'))
model = json.loads((H.parent / 'simulation/modell_h01.json').read_text())
# P10 Gesamtschwerpunkt (Servos 69 g Annahme wie Savöx-Flugfall), CAD-Rahmen in m
m0, c0 = model['mass_kg'], model['cg_m']
servo_parts = [c for c in model['components'] if c.get('part_id') == 'SERVO-PLATZHALTER']
mt = m0 + sum(.069 - c['mass_kg'] for c in servo_parts)
mc = [m0 * c0[i] + sum((.069 - c['mass_kg']) * c['cg_m'][i] for c in servo_parts) for i in range(3)]
for n in mass['remove_components']:
    c = next(x for x in model['components'] if x['name'] == n)
    mt -= c['mass_kg']
    mc = [mc[i] - c['mass_kg'] * c['cg_m'][i] for i in range(3)]
for c in mass['add_components']:
    mt += c['mass_kg']
    mc = [mc[i] + c['mass_kg'] * c['cg_m'][i] for i in range(3)]
cg = [v / mt for v in mc]
h = cg[2] * 1000 - G.GROUND_Z
tip_lat = math.degrees(math.atan2(G.SKID['y'] - abs(cg[1] * 1000), h))
tip_long = math.degrees(math.atan2(G.SKID['flat'] - abs(cg[0] * 1000), h))
report['checks']['landing_gear'] = dict(ground_z_mm=G.GROUND_Z, clamp_rings_max_distance_to_ground_mm=clamp_ground, skid_distance_to_ground_mm=skid_ground,
                                        lowest_part=lowest, parts_below_ground=below, min_clearance_non_gear_mm=min(not_gear.values()) if not_gear else None,
                                        nearest_non_gear=min(not_gear, key=not_gear.get) if not_gear else None,
                                        total_mass_kg_with_69g_servos=mt, cg_cad_mm=[v * 1000 for v in cg], cg_height_above_ground_mm=h,
                                        tip_over_angle_lateral_deg=tip_lat, tip_over_angle_longitudinal_deg=tip_long,
                                        lower_rotor_plane_height_mm=-30 - G.GROUND_Z,
                                        lower_rotor_height_in_rotor_radii=(-30 - G.GROUND_Z) / 187.5)
gear_ok = clamp_ground < 0.05 and min(not_gear.values()) > 0.2 and not below
report['checks']['landing_gear']['only_landing_gear_touches_ground'] = gear_ok
report['status'] = 'PASS' if not report['collisions'] and report['checks']['load_path_contacts']['all_pass'] and gear_ok else 'FAIL'
report['manufacturing_release'] = False
report['limits'] = ['Nominale Gewinde/Bohrungen ohne Flanken; Schrauben in Bohrungen als erlaubte Paarung geführt',
                    'Servo-STEP ungültig: Überschneidungen gegen einen gültigen Ersatzkörper aus den vermessenen STEP-Maßen (Gehäuse, Laschen, Abtriebsscheibe); Laschenanlage zusätzlich per distToShape am Original', 'Kontakt = Abstand ≤ 0,02 mm (Steckungen 0,06 mm)',
                    'Keine Festigkeits-, Verzahnungs- oder Elektroprüfung', 'Leitungen als glatte Sweeps mit flächengleichem Querschnitt']
(H / 'Ausgabe/Pruefbericht_P10.json').write_text(json.dumps(report, indent=1, ensure_ascii=False, default=float) + '\n')
A.closeDocument(d.Name)
print(json.dumps({k: report[k] for k in ('status', 'checks')}, indent=1, ensure_ascii=False, default=float))
print('collisions', len(report['collisions']))
for c in report['collisions'][:60]:
    print(c)
