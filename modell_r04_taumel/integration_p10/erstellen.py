#!/usr/bin/env python3
"""P10 Gesamtbaugruppe: Servohalter mit Lastpfad, Planetenstufe, Kabelbaum, Landegestell.

Ausgangsstand ist die native P09-Baugruppe (Servo bis Rotorblatt). Alle neuen und geänderten
Körper sind Konstruktionsentwurf; keine Fertigungs-, Festigkeits- oder Flugfreigabe.

    .cfd-tools/freecad/usr/bin/python modell_r04_taumel/integration_p10/erstellen.py
"""
import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path[:0] = [os.environ.get('FREECAD_LIB', str(ROOT / '.cfd-tools/freecad/usr/lib')), str(H),
                str(H.parent / 'bewegung_p09'), str(H.parent / 'bewegung')]
import FreeCAD as A  # noqa: E402
import Part  # noqa: E402
import geometrie_p10 as G  # noqa: E402
import kabel_p10 as K  # noqa: E402
import p10_runtime as RT  # noqa: E402

R, M, V = RT.R, RT.M, A.Vector
OUT = H / 'Ausgabe'
(OUT / 'STEP').mkdir(parents=True, exist_ok=True)
SRC = H.parent / 'bewegung_p09/Ausgabe/P09_Servo_bis_Rotorblatt_Bewegung.FCStd'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = load('_p10_cad', H.parent / 'cad/erstellen.py')
C.HO['r_center'] = 33
C.LID['driver_angle'] = 7
C.LID['slot'] = [9, 12]
C.LID['slot_y0'] = 1.5
C.PL['rod_hole_d'] = 14
G5 = load('_p10_g05', H.parent / 'fertigung_p05/geometrie.py')

# Effektive Dichten [kg/m³] = Werkstoff × angenommener Füllgrad (wie F01/H01), Stahl/Alu voll.
RHO = {'PA-CF_85': 1170 * 0.85, 'PA-CF_70': 1170 * 0.70, 'PETG_50': 1270 * 0.50, 'PETG_65': 1270 * 0.65,
       'Stahl': 7850.0, 'Alu': 2700.0, 'POM': 1410.0, 'Messing': 8500.0, 'CFK': 1550.0, 'TPU': 1200.0}
FIXED_MASS_G = {'P10-REF-UBEC': 12.0, 'P10-REF-SERVO-SAMMELPUNKT': 3.0, 'P10-SERVOVERTEILER-PCB': 4.0,
                'P10-REF-ELRS-EMPFAENGER': 2.0, 'P10-REF-XT60-STECKER': 4.0, 'P10-REF-XT60-BUCHSE': 4.0,
                'P10-REF-JST-XH-7': 1.5, 'MR85ZZ': 0.6}

d = A.openDocument(str(SRC))
neutral = RT.state([0] * 6, [0, 0])['frames']
for l, sign in ((0, 1), (1, -1)):
    for k in range(3):
        neutral[f'planet:{l}:{k}'] = RT.planet_frame(sign, k, 0.0)
group = d.addObject('App::DocumentObjectGroup', 'P10_Integration')
group.Label = 'P10 Integration (Servohalter, Planetenstufe, Kabel, Landegestell)'
records = []
removed_mass_model = []


def lw(sign):
    return M.local_world(sign)


def local_to_world(shape, sign, az=0.0):
    s = shape.copy()
    s.Placement = lw(sign).multiply(M.placement(rotation=M.rotz(az))).multiply(s.Placement)
    return s


def bake(o, s):
    o.Shape = Part.makeCompound([s.copy()])
    o.Placement = A.Placement()


def prop(o, name, value, typ='App::PropertyString', grp='P10'):
    if not hasattr(o, name):
        o.addProperty(typ, name, grp)
    setattr(o, name, value)


def mass_props(shape, rho=None, mass_g=None):
    """Masse [kg], Schwerpunkt [m], Trägheit um Schwerpunkt [kg m²] (CAD-Rahmen)."""
    solids = shape.Solids
    vol = sum(s.Volume for s in solids)
    if vol <= 0:
        raise ValueError('Körper ohne Volumen')
    m = mass_g / 1000.0 if mass_g is not None else rho * vol * 1e-9
    cg = sum((s.CenterOfMass * s.Volume for s in solids), V()) * (1.0 / vol)
    J = [[0.0] * 3 for _ in range(3)]
    for s in solids:
        I = s.MatrixOfInertia
        rows = [[I.A11, I.A12, I.A13], [I.A21, I.A22, I.A23], [I.A31, I.A32, I.A33]]
        dvec = s.CenterOfMass - cg
        dd = [dvec.x, dvec.y, dvec.z]
        for i in range(3):
            for j in range(3):
                J[i][j] += rows[i][j] + s.Volume * ((dvec.Length ** 2 if i == j else 0.0) - dd[i] * dd[j])
    scale = m / vol * 1e-6  # mm^5 → m^5 · (kg/mm³→kg) ; J[mm^5]·(m/vol)[kg/mm³]·1e-6 = kg m²
    return m, [cg.x / 1000, cg.y / 1000, cg.z / 1000], [[J[i][j] * scale for j in range(3)] for i in range(3)]


def record(o, ident, kind, material, group_tag='body', rho=None, mass_g=None, note='', export=None):
    shape = o.Shape
    if o.P09_Rahmen != 'fixed':
        shape = shape.copy()
    m, cg, J = mass_props(shape, rho, mass_g)
    rec = dict(name=o.Name, ident=ident, kind=kind, material=material, mass_kg=m, cg_m=cg, inertia_cg_kgm2=J,
               group=group_tag, frame=o.P09_Rahmen, note=note, valid=o.Shape.isValid())
    records.append(rec)
    prop(o, 'P10_Masse_g', f'{m * 1000:.3f}')
    if export:
        Part.export([o], str(OUT / 'STEP' / (export + '.step')))
    return rec


def add(name, world_shape, ident, kind, material, note, key='fixed', local_shape=None, rho=None, mass_g=None,
        group_tag='body', export=None, color=None, darstellung='Konstruierter Festkoerper (P10-Entwurf)'):
    o = d.addObject('Part::Feature', name)
    if key == 'fixed':
        bake(o, world_shape)
    else:
        s = local_shape.copy()
        s.Placement = neutral[key].multiply(s.Placement)
        bake(o, s)
    prop(o, 'BauteilID', ident)
    prop(o, 'P09_Rahmen', key, grp='P09 Bewegung')
    prop(o, 'P09_Neutralrahmen', neutral.get(key, A.Placement()), 'App::PropertyPlacement', 'P09 Bewegung')
    prop(o, 'P10_Art', kind)
    prop(o, 'P10_Werkstoff', material)
    prop(o, 'P10_Hinweis', note)
    prop(o, 'P06_Darstellung', darstellung)
    prop(o, 'P06_Fertigungsbereit', False, 'App::PropertyBool')
    if color:
        prop(o, 'P10_Farbe', list(color), 'App::PropertyFloatList')
    assert o.Shape.isValid(), name
    group.addObject(o)
    record(o, ident, kind, material, group_tag, rho, mass_g, note, export)
    return o


def replace(o, world_shape, note, ident=None, key=None, local_shape=None):
    if key is None:
        bake(o, world_shape)
    else:
        s = local_shape.copy()
        s.Placement = neutral[key].multiply(s.Placement)
        bake(o, s)
        o.P09_Rahmen = key
        o.P09_Neutralrahmen = neutral[key]
    if ident:
        o.BauteilID = ident
    prop(o, 'P10_Aenderung', note)
    assert o.Shape.isValid(), o.Name
    return o


report = dict(revision='P10_ENTWURF_KEINE_FREIGABE', source=str(SRC.relative_to(ROOT)),
              source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest())

# ============================================================================ 1. Planetenstufe
level_name = {1: 'Oben', -1: 'Unten'}
lid_izz = {}
for l, sign in ((0, 1), (1, -1)):
    lvl = level_name[sign]
    lid = d.getObject('Rotor_oben_1' if sign > 0 else 'Rotor_unten_1')
    old = lid.Shape.copy()
    old.Placement = lid.P09_Neutralrahmen.inverse().multiply(old.Placement)
    new = G.lid_p10(C, sign)
    for tag, s in (('alt', old), ('neu', new)):
        m, cg, J = mass_props(s, RHO['PA-CF_70'])
        lid_izz[(lvl, tag)] = dict(mass_kg=m, Izz_axis_kgm2=J[2][2] + m * ((cg[0]) ** 2 + (cg[1]) ** 2))
    replace(lid, None, 'P10: Außenzahnkranz Z130 durch innenverzahntes Hohlrad Z130 m1 (Kranz Ø140) ersetzt; innerer Deckel unverändert.',
            'TM-DECKEL-HOHLRAD-130', f'rotor:{l}', new)
    lid.Label = f'P10_Deckel_Hohlrad_Z130_{lvl}'
    prop(lid, 'P06_Offen', 'Hohlrad-Verzahnungsqualität, Rundlauf, Werkstoff (PA-CF-Druck vs. gefräst) und Zahnfußfestigkeit nachweisen.')
    prop(lid, 'P06_Darstellung', 'Konstruierter Festkoerper (P10-Entwurf)')
    rec = record(lid, 'TM-DECKEL-HOHLRAD-130', 'Eigenfertigung', 'PA-CF Druck, Füllgrad 0,7 (Annahme)', 'upper' if sign > 0 else 'lower',
                 RHO['PA-CF_70'], export='Deckel_Hohlrad_Z130_oben' if sign > 0 else None)
    removed_mass_model.append(lid.Name)

    # Motor + P05-Schrauben/-Scheiben: Motor rückt auf den Planetenkreis (r = 54,8 mm, 330°) und 4 mm höher.
    cx, cy = G.motor_centre()
    T_local = M.placement((cx, cy, G.PLANET['motor_lift'])).multiply(M.placement(rotation=M.rotz(G.PLANET['phi_drive']))).multiply(M.placement((-75.1, 0, 0)))
    T = lw(sign).multiply(T_local).multiply(lw(sign).inverse())
    moved = []
    motor = d.getObject(f'{lvl}_feststehend_11')
    for o in [motor] + [d.getObject(f'P05_Motor{kind}_{lvl}_{i}') for kind in ('schraube', 'scheibe') for i in range(4)]:
        s = o.Shape.copy()
        s.Placement = T.multiply(s.Placement)
        replace(o, s, 'P10: mit Motor auf Planetenposition r=54,8 / 330° verschoben, Anlagefläche an der Motorbrücke z_lokal=47.')
        moved.append(o.Name)
    m_motor = mass_props(motor.Shape, mass_g=32.0)
    prop(motor, 'P10_Masse_g', '32.000')
    records.append(dict(name=motor.Name, ident='MOTOR-ECO2-2306', kind='Kaufteil', material='EMAX ECO II 2306', mass_kg=m_motor[0], cg_m=m_motor[1],
                        inertia_cg_kgm2=m_motor[2], group='body', frame='fixed', note='verschoben', valid=True))
    removed_mass_model.append(motor.Name)

    # Angetriebener Planet = bestehendes P05-Gewinderitzel Z20 (Lücke bei 0°) + Kontermutter, drehen mit der Motorwelle.
    pin_shape = G5.pinion()[0]
    pin_shape.translate(V(0, 0, G.PLANET['z_gear'][0]))
    pinion = d.getObject(f'{lvl}_feststehend_13')
    replace(pinion, None, 'P10: Ritzel Z20 arbeitet als angetriebener Planet im Hohlrad (Innenverzahnung, gleicher Drehsinn).',
            key=f'planet:{l}:0', local_shape=pin_shape)
    rec_p = record(pinion, 'RITZEL-M1-Z20', 'Eigenfertigung', 'C45E (P05-Vorschlag)', 'body', RHO['Stahl'])
    removed_mass_model.append(pinion.Name)
    nut = d.getObject(f'P05_Kontermutter_M5_{lvl}_')
    nut_shape = G5.thin_nut()
    nut_shape.translate(V(0, 0, G.PLANET['z_gear'][1]))
    replace(nut, None, 'P10: Kontermutter oberhalb des Planetenritzels, dreht mit der Motorwelle.', key=f'planet:{l}:0', local_shape=nut_shape)
    record(nut, 'ISO4035-M5', 'Kaufteil', 'Stahl', 'body', RHO['Stahl'])

    add(f'P10_Motorbruecke_{lvl}', local_to_world(G.motor_bridge(), sign), 'P10-MOTORBRUECKE', 'Eigenfertigung', 'PA-CF Druck, Füllgrad 0,85',
        'Trägt den Motor oberhalb der Halteplatte (Anlagefläche z_lokal 47); 3 × M3 zur Platte, 4 × M3x7 (P05-Stapel) in den Motor.',
        rho=RHO['PA-CF_85'], export='Motorbruecke' if sign > 0 else None)
    for i, (ident, s) in enumerate(G.bridge_fasteners()):
        add(f'P10_Motorbruecke_{lvl}_{ident}_{i}', local_to_world(s, sign), ident, 'Kaufteil', 'Stahl 8.8 (Vorschlag)', 'Motorbrücke ↔ Halteplatte', rho=RHO['Stahl'])
    for k, phi in enumerate(G.PLANET['phi_idlers'], start=1):
        cxy = G.polar(G.PLANET['centre'], phi)[:2]
        add(f'P10_Stuetzplanet_{lvl}_{k}', None, 'P10-STUETZPLANET-Z20', 'Eigenfertigung', 'POM-C gefräst (Vorschlag)',
            'Mitlaufender Planet Z20 m1, 2 × MR85ZZ; zentriert das Hohlrad, überträgt kein Antriebsmoment.',
            key=f'planet:{l}:{k}', local_shape=G.idler_gear(), rho=RHO['POM'], export='Stuetzplanet_Z20' if sign > 0 and k == 1 else None)
        for b, s in enumerate(G.mr85_pair()):
            add(f'P10_Stuetzplanet_{lvl}_{k}_MR85_{b}', None, 'MR85ZZ', 'Kaufteil', 'Wälzlager 5 × 8 × 2,5', 'Hüllkörper, kein Herstellermodell',
                key=f'planet:{l}:{k}', local_shape=s, mass_g=FIXED_MASS_G['MR85ZZ'], darstellung='Nennmassreferenz')
        for part, ident, mat, rho, note, exp in (
                (G.planet_carrier(phi), 'P10-PLANETENBOLZENTRAEGER', 'EN AW-6082 (Vorschlag)', RHO['Alu'], 'Flansch unter der Halteplatte, Säule bis über das Zahnrad', 'Planetenbolzentraeger'),
                (G.planet_pin(), 'P10-PLANETENBOLZEN-D5', 'Stahl gehärtet, h6 (Vorschlag)', RHO['Stahl'], 'Kopf hält Lager axial, Presssitz in der Säule', 'Planetenbolzen_D5'),
                (G.planet_spacer(), 'P10-DISTANZSCHEIBE-5', 'Stahl', RHO['Stahl'], 'Spannt die Lagerinnenringe gegen die Säule', None)):
            add(f"P10_{ident.replace('P10-', '').replace('-', '_')}_{lvl}_{k}", local_to_world(G.at_xy(part, cxy), sign), ident, 'Eigenfertigung', mat, note, rho=rho,
                export=exp if sign > 0 and k == 1 else None)
        for i, (ident, s) in enumerate(G.carrier_fasteners(phi)):
            add(f'P10_Traeger_{lvl}_{k}_{ident}_{i}', local_to_world(s, sign), ident, 'Kaufteil', 'Stahl 8.8 (Vorschlag)', 'Bolzenträger ↔ Halteplatte', rho=RHO['Stahl'])
report['planetenstufe'] = dict(ring_teeth=130, planet_teeth=20, module_mm=1.0, ratio=6.5, centre_distance_mm=G.PLANET['centre'],
                               nominal_centre_distance_mm=55.0, drive_planet_deg=G.PLANET['phi_drive'], idler_planets_deg=list(G.PLANET['phi_idlers']),
                               motor_sense='gleichsinnig zum Rotor (Innenverzahnung)', motor_moved_objects=moved, lid_spin_inertia=
                               {f'{k[0]}_{k[1]}': v for k, v in lid_izz.items()}, sun_gear=False,
                               note='Stützplaneten übertragen kein Moment; ohne Sonnenrad keine Momentenaufteilung.')

# ============================================================================ 2. Halteplatte P10 + Servohalter
for l, sign in ((0, 1), (1, -1)):
    lvl = level_name[sign]
    plate = d.getObject(f'{lvl}_feststehend_10')
    replace(plate, local_to_world(G.plate_p10(C), sign),
            'P10: Servoausleger mit Halterverschraubung, Motorarm 330° mit Motordurchbruch und Litzennut, Arme für Planetenbolzenträger 105°/195°; alter Motorarm entfällt.')
    plate.Label = f'P10_Halteplatte_{lvl}'
    prop(plate, 'P06_Offen', 'Festigkeit Ausleger/Kragen, Klemmschraube Kragen, Druckparameter. Servo-Lastpfad jetzt vorhanden.')
    prop(plate, 'P06_Darstellung', 'Konstruierter Festkoerper (P10-Entwurf)')
    record(plate, 'TM-HALTEPLATTE', 'Eigenfertigung', 'PETG Druck, Füllgrad 0,5', 'body', RHO['PETG_50'], export='Halteplatte_P10' if sign > 0 else None)
    removed_mass_model.append(plate.Name)
    for j, az in enumerate(G.SERVO_AZ):
        add(f'P10_Servohalter_{lvl}_{az}', local_to_world(G.servo_bracket(), sign, az), 'P10-SERVOHALTER', 'Eigenfertigung', 'PA-CF Druck, Füllgrad 0,85',
            'Steg mit Gehäusedurchtritt an der Laschenanlage (lokal y=−22,3), 2 Füße mit 4 × M3 zur Halteplatte, 4 Rippen.',
            rho=RHO['PA-CF_85'], export='Servohalter' if sign > 0 and j == 0 else None)
        for i, (ident, s) in enumerate(G.bracket_fasteners()):
            add(f'P10_Servohalter_{lvl}_{az}_{ident}_{i}', local_to_world(s, sign, az), ident, 'Kaufteil', 'Stahl 8.8 (Vorschlag)',
                'Servolasche ↔ Halter' if i < 16 else 'Halterfuß ↔ Halteplatte', rho=RHO['Stahl'])
servo_cases = [o for o in d.Objects if getattr(o, 'BauteilID', '') == 'SERVO-SAVOX-SB2270SGP']
for o in servo_cases:
    prop(o, 'P10_Befestigung', 'P10-Servohalter: 4 × M3x12 durch die Laschen (Ø4,68 mit Scheibe) in den Haltersteg.')

# ============================================================================ 3. H01/H04, Akkuverschraubung
for name in ('Mitte_2', 'Mitte_3'):
    o = d.getObject(name)
    z = 95.0 if name == 'Mitte_2' else -101.0
    replace(o, o.Shape.cut(G.cyl(8.0, 6.0, (0, 0, z))), 'P10: zentrale Kabeldurchführung Ø16 in der Adapterplatte.')
    record(o, 'H01', 'Eigenfertigung', 'PETG, Füllgrad 0,65', 'body', RHO['PETG_65'], export='H01_P10_Kabeldurchfuehrung' if name == 'Mitte_2' else None)
    removed_mass_model.append(name)
h04 = d.getObject('Akku_Anschlussplatte')
relief = [local_to_world(G.servo_body_relief_local(1.0), -1, az) for az in G.SERVO_AZ]
inserts_holes = [G.cyl(2.0, 6.0, (cx, cy, -105.0)) for cx, cy in G.CORNERS]
h04_before = h04.Shape.copy()
replace(h04, h04.Shape.cut(Part.makeCompound(relief + inserts_holes)),
        'P10: Freistellung unter den unteren Servogehäusen (vorher Berührung), Ø4,0-Aufnahmen für M3-Gewindeeinsätze.')
record(h04, 'H04', 'Eigenfertigung', 'PETG, Füllgrad 0,65', 'body', RHO['PETG_65'], export='H04_P10')
removed_mass_model.append('Akku_Anschlussplatte')
report['h04_relief_removed_mm3'] = h04_before.Volume - h04.Shape.Volume
for i, (cx, cy) in enumerate(G.CORNERS):
    o = d.getObject(f'M3_Akku_{i}')
    o_c = o.Shape.BoundBox.Center
    cx, cy = (round(o_c.x), round(o_c.y))
    replace(o, G.gear_bolt(cx, cy), 'P10: ISO 4762 M3x80 von unten durch Fahrwerksknoten, Wanne und Distanz in Gewindeeinsatz H04.', 'ISO4762-M3x80')
    record(o, 'ISO4762-M3x80', 'Kaufteil', 'Stahl 8.8', 'body', RHO['Stahl'])
    removed_mass_model.append(o.Name)
    s = G.heatset_m3()
    s.translate(V(cx, cy, -104.0))
    add(f'P10_Gewindeeinsatz_M3_{i}', s, 'P10-GEWINDEEINSATZ-M3', 'Kaufteil', 'Messing', 'Einpressmutter M3 × 4, Rändel nicht dargestellt', rho=RHO['Messing'],
        darstellung='Nennmassreferenz')

# ============================================================================ 4. Landegestell
for i, (cx, cy) in enumerate(G.CORNERS):
    add(f'P10_Fahrwerksknoten_{i}', G.gear_node(cx, cy), 'P10-FAHRWERKSKNOTEN', 'Eigenfertigung', 'PA-CF Druck, Füllgrad 0,85',
        'Unter der Akkuwanne, geklemmt durch M3x80; Rohrsteckung Ø6 für die Strebe (eingeklebt, Kleber offen).', rho=RHO['PA-CF_85'],
        export='Fahrwerksknoten' if i == 0 else None)
    add(f'P10_Fahrwerksstrebe_{i}', G.strut_tube(cx, cy), 'P10-STREBE-CFK-6x4', 'Kaufteil/Zuschnitt', 'CFK-Rohr 6 × 4', 'Strebe Knoten → Kufenschelle',
        rho=RHO['CFK'], export='Strebe_CFK_6x4' if i == 0 else None)
    add(f'P10_Kufenschelle_{i}', G.skid_clamp(cx, cy), 'P10-KUFENSCHELLE', 'Eigenfertigung', 'PA-CF Druck, Füllgrad 0,85',
        'Ringschelle: Bodenkontakt am Ringboden; klemmt die Kufe (Schlitz 1 mm, M3x8 in Gewindeeinsatz) und nimmt die Strebe auf.', rho=RHO['PA-CF_85'], export='Kufenschelle' if i == 0 else None)
    for k, (ident, s) in enumerate(G.skid_clamp_fasteners(cx, cy)):
        add(f'P10_Kufenschelle_{i}_{ident}_{k}', s, ident, 'Kaufteil', 'Stahl 8.8', 'Klemmschraube Kufenschelle', rho=RHO['Stahl'])
for side in (-1, 1):
    tag = 'links' if side > 0 else 'rechts'
    add(f'P10_Kufe_{tag}', G.skid(side), 'P10-KUFE-CFK-8x6', 'Kaufteil/Zuschnitt', 'CFK-Rohr 8 × 6, Enden warm gebogen oder Bogenstücke',
        'Kufenunterkante z = −218 (CAD), 2,5 mm über dem Ringboden der Schellen; Enden 40° aufgebogen', rho=RHO['CFK'], export='Kufe_CFK_8x6' if side > 0 else None)
    for end in (-1, 1):
        add(f'P10_Kufenstopfen_{tag}_{end + 1}', G.skid_end_cap(side, end), 'P10-KUFENSTOPFEN', 'Eigenfertigung', 'TPU 95A', 'Endkappe', rho=RHO['TPU'])

# ============================================================================ 5. Elektronik-Bauräume
pcb, feet = G.top_distributor()
male, female = G.xt60_pair()
for name, shape, ident, note, color in (
        ('P10_UBEC', G.ubec(), 'P10-REF-UBEC', 'UBEC 7,4 V für die Servos (Bauraum, Artikel/Strombelastbarkeit offen)', (0.2, 0.3, 0.6)),
        ('P10_Servo_Sammelpunkt_unten', G.lower_junction(), 'P10-REF-SERVO-SAMMELPUNKT', 'Lötpunkt/PCB: 3 untere Servos + UBEC → Stammkabel', (0.1, 0.5, 0.25)),
        ('P10_Servoverteiler_oben', pcb, 'P10-SERVOVERTEILER-PCB', 'Lötpads für 3 obere Servos, Stammkabel, Signalband zum FC', (0.1, 0.5, 0.25)),
        ('P10_ELRS_Empfaenger', G.receiver(), 'P10-REF-ELRS-EMPFAENGER', 'Bauraum ELRS-Empfänger, Klebepad', (0.15, 0.15, 0.15)),
        ('P10_XT60_Stecker', male, 'P10-REF-XT60-STECKER', 'Akkuseite', (0.9, 0.75, 0.1)),
        ('P10_XT60_Buchse', female, 'P10-REF-XT60-BUCHSE', 'Fahrzeugseite: Hauptleitung + UBEC-Abgriff', (0.9, 0.75, 0.1)),
        ('P10_JST_XH_Balancer', G.jst_balancer(), 'P10-REF-JST-XH-7', 'Balancerstecker im reservierten Zugang', (0.95, 0.95, 0.95))):
    add(name, shape, ident, 'Kaufteil' if 'REF' in ident else 'Eigenfertigung', 'Bauraumreferenz', note, mass_g=FIXED_MASS_G[ident],
        darstellung='Bemasste Bauraumreferenz', color=color)
add('P10_Servoverteiler_Distanzen', feet, 'P10-DISTANZ-VERTEILER', 'Eigenfertigung', 'PA-CF', 'Zwei Klebedistanzen auf H01', rho=RHO['PA-CF_85'])

# ============================================================================ 6. Kabel
def servo_world(sign, j, p):
    az = G.SERVO_AZ[j] if j is not None else 0.0
    pl = lw(sign).multiply(M.placement(rotation=M.rotz(az)))
    q = pl.multVec(V(*p))
    return (q.x, q.y, q.z)


cables = K.cable_list(servo_world)
cable_rows = []
for c in cables:
    shape, length, mass_g = K.build(c)
    assert shape.isValid() and len(shape.Solids) == 1, c['id']
    add('P10_Kabel_' + c['id'].replace('+', 'P').replace('-', 'M'), shape, 'P10-KABEL-' + c['typ'], 'Kaufteil/Konfektion', c['typ'],
        f"{c['von']} → {c['nach']}; {c['adern']} Ader(n); Farbe {c['farbe']}", mass_g=mass_g, color=K.COLORS[c['farbe']],
        darstellung='Leitungsweg (Sweep, Querschnitt flächengleich)')
    cable_rows.append(dict(id=c['id'], von=c['von'], nach=c['nach'], typ=c['typ'], adern=c['adern'], farbe=c['farbe'],
                           durchmesser_mm=K.AWG[c['typ']][0], laenge_mm=round(length, 1), masse_g=round(mass_g, 2)))
removed_mass_model += ['wiring', 'receiver']

# ============================================================================ 7. Animation/Status, Speichern
ctl = d.getObject('P09_Animation')
ctl.Proxy = RT.Controller(ctl)
ctl.Label = 'P10_Animation'
info = d.getObject('P02_Fertigungsstatus')
info.Gesamt_Fertigungsfreigabe = False
info.Begruendung = ('P10: Servohalter mit Lastpfad zur Halteplatte, Planetenstufe (Hohlrad Z130 + 3 Planeten), Kabelbaum und Landegestell '
                    'als Konstruktionsentwurf. Keine Festigkeits-, Verzahnungs-, Elektro- oder Flugfreigabe; Servo-STEP weiterhin ungültig.')
d.Label = 'P10 Gesamtbaugruppe – Servohalter, Planetenstufe, Kabelbaum, Landegestell (Entwurf)'
d.recompute()
RT.apply(d, [0] * 6, [0, 0])
target = OUT / 'P10_Gesamtbaugruppe.FCStd'
d.saveAs(str(target))
A.closeDocument(d.Name)
d = A.openDocument(str(target))
ctl = d.getObject('P09_Animation')
ctl.Proxy = RT.Controller(ctl)
RT.apply(d, [2, -1, 0.5, 0, 1.5, -2], [17.0, 33.0])
RT.apply(d, [0] * 6, [0, 0])
assert not d.getObject('P02_Fertigungsstatus').Gesamt_Fertigungsfreigabe
invalid = [o.Name for o in d.Objects if hasattr(o, 'P09_Rahmen') and not o.Shape.isValid()]
A.closeDocument(d.Name)

# ============================================================================ 8. Listen und Massendaten
with open(OUT / 'Kabelliste_P10.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(cable_rows[0]))
    w.writeheader()
    w.writerows(cable_rows)
bom = {}
for r in records:
    key = r['ident']
    e = bom.setdefault(key, dict(BauteilID=key, Anzahl=0, Art=r['kind'], Werkstoff=r['material'], Masse_je_Stueck_g=round(r['mass_kg'] * 1000, 3), Hinweis=[]))
    e['Anzahl'] += 1
    if r['note'] and r['note'] not in e['Hinweis'] and not key.startswith('P10-KABEL'):
        e['Hinweis'].append(r['note'])
for e in bom.values():
    e['Hinweis'] = ' | '.join(e['Hinweis']) if e['Hinweis'] else ('siehe Kabelliste_P10.csv' if e['BauteilID'].startswith('P10-KABEL') else '')
with open(OUT / 'Stueckliste_P10.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['BauteilID', 'Anzahl', 'Art', 'Werkstoff', 'Masse_je_Stueck_g', 'Hinweis'])
    w.writeheader()
    for k in sorted(bom):
        w.writerow(bom[k])

spin_delta = [lid_izz[('Oben', 'neu')]['Izz_axis_kgm2'] - lid_izz[('Oben', 'alt')]['Izz_axis_kgm2'],
              lid_izz[('Unten', 'neu')]['Izz_axis_kgm2'] - lid_izz[('Unten', 'alt')]['Izz_axis_kgm2']]
idler = next(r for r in records if r['ident'] == 'P10-STUETZPLANET-Z20')
idler_izz = idler['inertia_cg_kgm2'][2][2] + 2 * FIXED_MASS_G['MR85ZZ'] / 1000 * (0.004 ** 2 + 0.0025 ** 2) / 2
# Bodenkontakt: vier Schellenringe (z = −220,5); Kufe (−218) und aufgebogene Enden tragen bei Neigung/Einfederung mit.
contacts = [[sx * G.JOINT_X / 1000, s * G.SKID['y'] / 1000, G.GROUND_Z / 1000] for s in (-1, 1) for sx in (-1, 1)]
contacts += [[x / 1000, s * G.SKID['y'] / 1000, (G.SKID['z'] - G.SKID['r']) / 1000] for s in (-1, 1) for x in (-120, 0, 120)]
contacts += [[s2 * 150 / 1000, s * G.SKID['y'] / 1000, -0.2075] for s in (-1, 1) for s2 in (-1, 1)]
mass_export = dict(
    revision='P10', source_native_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    remove_components=sorted(set(removed_mass_model)),
    add_components=[dict(name=r['name'], part_id=r['ident'], group=r['group'], mass_kg=r['mass_kg'],
                         cg_m=r['cg_m'], inertia_cg_kgm2=r['inertia_cg_kgm2']) for r in records],
    rotor_spin_inertia_delta_kgm2=spin_delta,
    idler_planets=dict(count_per_rotor=2, spin_inertia_kgm2=idler_izz, ratio=6.5),
    drive=dict(layout='P10_HOHLRAD_Z130_3_PLANETEN', motor_sense=1, ratio=6.5, gear_efficiency_assumption=0.92),
    landing_gear=dict(contact_points_cad_m=contacts, ground_z_cad_m=G.GROUND_Z / 1000),
    notes=['Effektive Dichten = Werkstoff × angenommener Füllgrad wie F01/H01', 'Kabelmassen aus Richtwerten je AWG, nicht gemessen',
           'Bauraumreferenzen mit angenommenen Massen', 'Servogehäuse: Masse bleibt Simulationsparameter (SB-2270SG+-Datenblatt fehlt)'])
(OUT / 'Massen_P10.json').write_text(json.dumps(mass_export, indent=1) + '\n')
(H.parent / 'simulation/p10_massen.json').write_text(json.dumps(mass_export) + '\n')
added = sum(r['mass_kg'] for r in records)
report.update(native=str(target.relative_to(ROOT)), native_sha256=mass_export['source_native_sha256'], invalid_after_reopen=invalid,
              objects_added_or_changed=len(records), cable_count=len(cable_rows), cable_length_total_mm=round(sum(c['laenge_mm'] for c in cable_rows), 1),
              cable_mass_g=round(sum(c['masse_g'] for c in cable_rows), 2), records_mass_g=round(added * 1000, 2),
              servo_brackets=6, landing_gear=dict(nodes=4, struts=4, skids=2, ground_z_mm=G.GROUND_Z),
              manufacturing_release=False, native_reopen_pass=True)
(OUT / 'Aufbau_P10.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'planetenstufe'}, indent=1, ensure_ascii=False))
