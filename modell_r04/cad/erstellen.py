#!/usr/bin/env python3
"""R04-Testmodell 1:4 – parametrisches FreeCAD-Modell, Phase 2, Entwurf V1. Millimeter.

Erzeugt aus parameter.json:
  R04_Testmodell_1zu4.FCStd / .step   Baugruppe in Schwebestellung (Pitch oben 14 Grad, unten 16,7 Grad)
  stl/*.stl                           Druckteile in Druckorientierung
  Pruefbericht.json, Stueckliste.csv  Druckbett, Kollisionen, Verzahnung, Massen, Unwucht

Konzept: feststehendes Mittelrohr D30; je Rotor eine Nabentrommel auf zwei 6806-Lagern mit 8 radialen
Servotaschen (Servowelle = Pitchachse). Fluegelzapfen in der Trommelwand, Fliehkraft ueber zwei
Querstifte in einer Nut, Drehmoment ueber Mitnehmer am Servohorn. Zahnkranz 91 Z als Trommeldeckel,
Motor mit Ritzel 14 Z auf Halteplatte. Unterer Rotor = oberer Rotor um 180 Grad gekippt (gleiche Teile).
Entwurf ohne Festigkeits-, Toleranz- oder Fertigungsfreigabe.

    FREECAD_LIB=/pfad/zu/freecad/lib python3 modell_r04/cad/erstellen.py
"""
import csv, json, math, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.extend([p for p in (os.environ.get('FREECAD_LIB'), '/usr/lib/freecad/lib') if p])
import FreeCAD as App
import Part, Mesh, MeshPart

P = json.loads((HERE / 'parameter.json').read_text())
V = App.Vector
BL, HUB, SV, GR, MO, PL = P['blade'], P['hub'], P['servo'], P['gear'], P['motor'], P['plate']
N = BL['count']
STL = HERE / 'stl'; STL.mkdir(exist_ok=True); (HERE / 'vorschau').mkdir(exist_ok=True)


def cyl(r, h, base=(0, 0, 0), axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*base), V(*axis))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def rotz(shape, deg):
    s = shape.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), deg); return s


def poly_face(pts2d, plane='xy', offset=0.0):
    if plane == 'xy': vs = [V(x, y, offset) for x, y in pts2d]
    else: vs = [V(offset, y, z) for y, z in pts2d]   # 'yz' bei x = offset
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


# ---------------------------------------------------------------- Evolventenverzahnung
def gear_points(m, z, alpha_deg, backlash, n=10):
    a = math.radians(alpha_deg); r = m * z / 2; rb = r * math.cos(a); ra = r + m; rf = r - 1.25 * m
    inv = lambda x: math.tan(x) - x
    half = math.pi / (2 * z) - backlash / (2 * r)
    theta = lambda rr: half + inv(a) - inv(math.acos(min(1.0, rb / rr)))
    rs = max(rf, rb); radii = [rs + (ra - rs) * i / n for i in range(n + 1)]
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        tooth = ([(rf, c - theta(rs))] if rf < rs else []) + [(rr, c - theta(rr)) for rr in radii] + \
                [(rr, c + theta(rr)) for rr in reversed(radii)] + ([(rf, c + theta(rs))] if rf < rs else [])
        pts += tooth
        a0, a1 = c + theta(rs), c + 2 * math.pi / z - theta(rs)
        pts += [(rf, a0 + (a1 - a0) * t) for t in (0.25, 0.5, 0.75)]
    return [(rr * math.cos(t), rr * math.sin(t)) for rr, t in pts], (r, ra, rf)


def spur_gear(m, z, face, backlash, bore_r, phase_deg=0.0):
    pts, radii = gear_points(m, z, GR['pressure_angle'], backlash)
    s = poly_face(pts).extrude(V(0, 0, face)).cut(cyl(bore_r, face + 2, (0, 0, -1)))
    return rotz(s, phase_deg), radii


# ---------------------------------------------------------------- Fluegel (lokal: x radial, y Sehne/Nase +, z Dicke)
def naca_half(q, tc, te):
    q = min(max(q, 0.0), 1.0)
    return 5 * tc * (0.2969 * math.sqrt(q) - 0.126 * q - 0.3516 * q * q + 0.2843 * q ** 3 - 0.1036 * q ** 4) * BL['chord'] + te / 2 * q ** 10


def blade_shape():
    c, tc, te = BL['chord'], BL['tc'], BL['te_mm']
    qs = [(1 - math.cos(math.pi * i / 60)) / 2 for i in range(61)]
    upper = [((0.5 - q) * c, naca_half(q, tc, te)) for q in qs]
    lower = [((0.5 - q) * c, -naca_half(q, tc, te)) for q in reversed(qs[1:])]
    foil = poly_face(upper + lower, 'yz', BL['r_airfoil_start']).extrude(V(BL['r_tip'] - BL['r_airfoil_start'], 0, 0))
    rb = BL['boss_d'] / 2
    boss = cyl(rb, BL['r_airfoil_start'] - BL['boss_r_in'] + 0.5, (BL['boss_r_in'], 0, 0), (1, 0, 0))
    groove = cyl(rb + 1, BL['groove_w'], (BL['groove_r'] - BL['groove_w'] / 2, 0, 0), (1, 0, 0)).cut(
        cyl(rb - BL['groove_depth'], BL['groove_w'] + 2, (BL['groove_r'] - BL['groove_w'] / 2 - 1, 0, 0), (1, 0, 0)))
    slot = box(BL['boss_r_in'] - 1, BL['boss_r_in'] + BL['slot_depth'], -BL['slot_w'] / 2, BL['slot_w'] / 2, -rb - 1, rb + 1)
    return foil.fuse(boss).removeSplitter().cut(groove).cut(slot)


def pitched(shape, deg):
    s = shape.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), deg); return s   # Nase (+y) nach +z


# ---------------------------------------------------------------- Servo-Platzhalter und Tasche (lokal fuer Fluegel 0)
def servo_parts(clear=0.0):
    rb, H, L, W, so = SV['r_bottom'], SV['H'], SV['L'], SV['W'], SV['shaft_off']
    body = box(rb - clear, rb + H + clear, -W / 2 - clear, W / 2 + clear, -so - clear, L - so + clear)
    t0 = -so - (SV['tab_total'] - L) / 2
    tabs = box(rb + SV['tab_h'] - clear, rb + SV['tab_h'] + SV['tab_t'] + clear, -W / 2 - clear, W / 2 + clear, t0 - clear, t0 + SV['tab_total'] + clear)
    spline = cyl(SV['spline_d'] / 2 + clear, SV['spline_h'], (rb + H, 0, 0), (1, 0, 0))
    return body, tabs, spline


def servo_shape():
    b, t, s = servo_parts(); return b.fuse(t).fuse(s)


def driver_shape():   # Mitnehmer auf dem Servohorn: Scheibe + Zunge in den Zapfenschlitz
    D = P['driver']; x0 = SV['r_bottom'] + SV['H'] + 0.5
    disk = cyl(D['r'], D['t'], (x0, 0, 0), (1, 0, 0))
    tongue = box(x0 + D['t'], BL['boss_r_in'] + D['tongue_len'], -D['tongue_w'] / 2, D['tongue_w'] / 2, -D['r'] + 1, D['r'] - 1)
    return disk.fuse(tongue).removeSplitter().cut(cyl(SV['spline_d'] / 2, D['t'] + 1, (x0 - 0.5, 0, 0), (1, 0, 0)))


def pocket_tool():
    b, t, s = servo_parts(HUB['pocket_clear'])
    open_up = box(SV['r_bottom'] - HUB['pocket_clear'], SV['r_bottom'] + SV['H'] + HUB['pocket_clear'],
                  -SV['W'] / 2 - HUB['pocket_clear'], SV['W'] / 2 + HUB['pocket_clear'], 0, HUB['z_max'] + 1)
    t0 = -SV['shaft_off'] - (SV['tab_total'] - SV['L']) / 2
    tabs_up = box(SV['r_bottom'] + SV['tab_h'] - HUB['pocket_clear'], SV['r_bottom'] + SV['tab_h'] + SV['tab_t'] + HUB['pocket_clear'],
                  -SV['W'] / 2 - HUB['pocket_clear'], SV['W'] / 2 + HUB['pocket_clear'], t0, HUB['z_max'] + 1)
    D = P['driver']
    driver_space = cyl(D['r'] + 0.8, HUB['r_wall_in'] - (SV['r_bottom'] + SV['H']), (SV['r_bottom'] + SV['H'], 0, 0), (1, 0, 0))
    driver_up = box(SV['r_bottom'] + SV['H'], HUB['r_wall_in'], -D['r'] - 0.8, D['r'] + 0.8, 0, HUB['z_max'] + 1)
    return b.fuse([t, s, open_up, tabs_up, driver_space, driver_up]).removeSplitter()


def pin_shapes():
    p = P['pin']
    return [cyl(p['d'] / 2, p['len'], (BL['groove_r'], -p['len'] / 2, s * p['z_offset']), (0, 1, 0)) for s in (-1, 1)]


# ---------------------------------------------------------------- Nabe und Zahnkranz (lokal, Fluegelebene z = 0, Aussenseite +z)
def hub_shape():
    zmin, zmax, h = HUB['z_min'], HUB['z_max'], HUB['z_max'] - HUB['z_min']
    b = P['bearing']
    s = cyl(HUB['r_out'], h, (0, 0, zmin))
    s = s.cut(cyl(HUB['bore_mid'], h + 2, (0, 0, zmin - 1)))
    for z0 in b['z_local']:
        s = s.cut(cyl(b['D'] / 2, b['B'], (0, 0, z0)))
    tools = []
    for k in range(N):
        a = 360 * k / N
        tools.append(rotz(pocket_tool(), a))
        tools.append(rotz(cyl(BL['boss_d'] / 2 + HUB['bore_clear'], HUB['r_out'] - HUB['r_wall_in'] + 2, (HUB['r_wall_in'] - 1, 0, 0), (1, 0, 0)), a))
        tools += [rotz(pp, a) for pp in pin_shapes()]
        tools.append(rotz(cyl(HUB['screw_d'] / 2, 12, (HUB['screw_r'], 0, zmax - 11)), a + 180 / N))
        # Erleichterung: Sackbohrung von unten im Steg zwischen zwei Taschen (unterhalb der Deckelschrauben)
        tools.append(rotz(cyl(HUB['lighten_d'] / 2, HUB['lighten_depth'], (HUB['lighten_r'], 0, zmin - 1)), a + 180 / N))
    # Erleichterung: unterhalb der Servotaschen zwischen Lagersitz und Aussenring kein Material noetig
    z_pocket_min = -SV['shaft_off'] - (SV['tab_total'] - SV['L']) / 2 - HUB['pocket_clear'] - 0.6
    tools.append(cyl(HUB['r_wall_in'], z_pocket_min - zmin + 1, (0, 0, zmin - 1)).cut(cyl(P['bearing']['D'] / 2 + 3, 40, (0, 0, zmin - 2))))
    # Erleichterung: Aussenring r_wall_in+2 .. r_out nur im Band um die Fluegelzapfen
    band = HUB['rim_band']
    for z0, z1 in ((zmin - 1, -band), (band, zmax + 1)):
        tools.append(cyl(HUB['r_out'] + 1, z1 - z0, (0, 0, z0)).cut(cyl(HUB['r_wall_in'] + 2, z1 - z0 + 2, (0, 0, z0 - 1))))
    return s.cut(Part.makeCompound(tools))


def ring_gear_shape():
    g, radii = spur_gear(GR['module'], GR['z_ring'], GR['face'], GR['backlash'], GR['r_in'])
    g.translate(V(0, 0, GR['z_local']))
    holes = [rotz(cyl(HUB['screw_d'] / 2 + 0.25, GR['face'] + 2, (HUB['screw_r'], 0, GR['z_local'] - 1)), 360 * k / N + 180 / N) for k in range(N)]
    heads = [rotz(cyl(2.6, 2.2, (HUB['screw_r'], 0, GR['z_local'] + GR['face'] - 2.2)), 360 * k / N + 180 / N) for k in range(N)]
    windows = [rotz(cyl(GR['window_d'] / 2, GR['face'] + 2, (GR['window_r'], 0, GR['z_local'] - 1)), 45 + 90 * k) for k in range(4)]
    return g.cut(Part.makeCompound(holes + heads + windows)), radii


def electronics_parts():
    E = P['electronics']; z0 = GR['z_local'] + GR['face'] + 0.5; rc = E['r_center']; out = []
    def item(dims, ang, ident, mass):
        L, Wd, H = dims; s = box(rc - Wd / 2, rc + Wd / 2, -L / 2, L / 2, z0, z0 + H); out.append((rotz(s, ang), ident, mass))
    item(E['cell'], 90, 'ROT-ZELLE-1S', E['cell_mass_g']); item(E['cell'], 270, 'ROT-ZELLE-1S', E['cell_mass_g'])
    item(E['esp'], 0, 'ROT-ESP32C3', E['esp_mass_g']); item(E['switch'], 180, 'ROT-SCHALTER', E['switch_mass_g'])
    return out


def rotor_local(pitch_local):
    """Teile eines Rotors im lokalen Rahmen: (shape, id, art, masse_g oder None, dichte, fuellgrad)."""
    parts = []
    d = P['print']['density']; f = P['print']['fill']
    parts.append((hub_shape(), 'TM-NABE', 'Druck', None, d['PA-CF'], f['hub']))
    gear, _ = ring_gear_shape(); parts.append((gear, 'TM-ZAHNKRANZ-91', 'Druck', None, d['PA-CF'], f['gear']))
    blade = pitched(blade_shape(), pitch_local); serv = servo_shape(); drv = driver_shape()
    for k in range(N):
        a = 360 * k / N
        parts.append((rotz(blade, a), 'TM-FLUEGEL', 'Druck', None, d['PA-CF'], f['blade']))
        parts.append((rotz(serv, a), 'SERVO-PLATZHALTER', 'Kauf', SV['mass_g'], None, None))
        parts.append((rotz(drv, a), 'TM-MITNEHMER', 'Druck', None, d['PA-CF'], f['driver']))
        for pp in pin_shapes(): parts.append((rotz(pp, a), 'STIFT-D2x20', 'Kauf', None, 7850, 1.0))
    b = P['bearing']
    for z0 in b['z_local']:
        ring = cyl(b['D'] / 2, b['B'], (0, 0, z0)).cut(cyl(b['d'] / 2, b['B'] + 2, (0, 0, z0 - 1)))
        parts.append((ring, 'LAGER-6806', 'Kauf', b['mass_g'], None, None))
    for s, ident, m in electronics_parts(): parts.append((s, ident, 'Kauf', m, None, None))
    return parts


def place_rotor(parts, level, angle):
    out = []
    for s, *rest in parts:
        t = s.copy()
        if level < 0: t.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        t.translate(V(0, 0, level)); t.rotate(V(0, 0, 0), V(0, 0, 1), angle if level > 0 else -angle)
        out.append((t, *rest))
    return out


# ---------------------------------------------------------------- Feststehende Teile
def motor_stack(level, ang_deg, gear_angle):
    """Motor, Ritzel und Halteplatte. Lokale Hoehen: Ritzel z_local..+face, Welle darunter 1 mm Ueberstand."""
    sgn = 1 if level > 0 else -1
    a = math.radians(ang_deg); cdist = GR['module'] * (GR['z_ring'] + GR['z_pinion']) / 2 + GR['center_extra']
    cx, cy = cdist * math.cos(a), cdist * math.sin(a)
    # Ritzel 0,5 mm ueber der Nabenoberseite (kein Schleifen), Welle endet buendig mit dem Ritzel
    z_p0 = GR['z_local'] + 0.5; z_shaft0 = z_p0; z_body0 = z_shaft0 + MO['shaft_h']; z_face = z_body0 + MO['body_h']
    def w(z): return level + sgn * z     # lokal -> Welt
    def zc(z0, h): return (w(z0), h * sgn) if sgn > 0 else (w(z0) - h, h)
    parts = []
    z, h = zc(z_body0, MO['body_h']); parts.append((cyl(MO['d'] / 2, h, (cx, cy, z)), 'MOTOR-ECO2-2306', 'Kauf', MO['mass_g'], None, None))
    z, h = zc(z_shaft0, MO['shaft_h']); parts.append((cyl(MO['shaft_d'] / 2, h, (cx, cy, z)), 'MOTORWELLE-M5', 'Teil Motor', 0, None, None))
    # Ritzelphase: Luecke bzw. Zahn zur Zahnkranzmitte, synchron zur Zahnkranzdrehung
    ratio = GR['z_ring'] / GR['z_pinion']
    gap_face = 180 / GR['z_pinion'] if level > 0 else 0.0
    pin, _ = spur_gear(GR['module'], GR['z_pinion'], GR['face'], GR['backlash'], GR['pinion_bore'] / 2, gap_face)
    pin.rotate(V(0, 0, 0), V(0, 0, 1), -gear_angle * ratio if level > 0 else gear_angle * ratio)
    z, h = zc(z_p0, GR['face']); pin.translate(V(cx, cy, z)); parts.append((pin, 'RITZEL-M1-Z14', 'Kauf', P['purchased_mass_g']['pinion'], None, None))
    # Halteplatte (identisch oben/unten): Rohrschelle, Arm zum Motor, Gegenarm fuer Stack/Pruefstand
    pz, ph = zc(z_face, PL['t'])
    plate = local_plate()
    plate.rotate(V(0, 0, 0), V(0, 0, 1), ang_deg)
    if sgn < 0: plate.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    plate.translate(V(0, 0, pz if sgn > 0 else pz + ph))
    parts.append((plate, 'TM-HALTEPLATTE', 'Druck', None, P['print']['density']['PETG'], P['print']['fill']['plate']))
    return parts, (cx, cy)


def local_plate():
    """Halteplatte im Druckrahmen: Unterseite z = 0, Motor auf +x, Gegenarm auf -x."""
    t, cd = PL['t'], GR['module'] * (GR['z_ring'] + GR['z_pinion']) / 2 + GR['center_extra']
    rt = P['tube']['d'] / 2
    s = cyl(rt + PL['collar_wall'] + 4, t)
    s = s.fuse(box(0, cd, -PL['arm_w'] / 2, PL['arm_w'] / 2, 0, t)).fuse(cyl(PL['pad_d'] / 2, t, (cd, 0, 0)))
    s = s.fuse(box(-PL['counter_len'], 0, -PL['arm_w'] / 2, PL['arm_w'] / 2, 0, t))
    s = s.fuse(cyl(rt + PL['collar_wall'], t + PL['collar_h'])).removeSplitter()
    holes = [cyl(rt + 0.15, t + PL['collar_h'] + 2, (0, 0, -1)), cyl(MO['boss_d'] / 2 + 0.3, t + 2, (cd, 0, -1))]
    holes += [cyl(MO['mount_screw'] / 2 + 0.2, t + 2, (cd + MO['mount_pcd'] / 2 * math.cos(q), MO['mount_pcd'] / 2 * math.sin(q), -1))
              for q in (math.pi / 4 + i * math.pi / 2 for i in range(4))]
    sh = PL['stack_hole'] / 2; xc = -PL['counter_len'] + 22
    holes += [cyl(1.7, t + 2, (xc + dx, dy, -1)) for dx in (-sh, sh) for dy in (-sh, sh)]   # Stack 30,5 x 30,5
    holes += [cyl(2.6, t + 2, (xc + dx, 0, -1)) for dx in (-PL['stand_hole_pitch'] / 2, PL['stand_hole_pitch'] / 2)]  # M5 fuer 2020-Profil
    holes.append(box(-rt - PL['collar_wall'] - 1, -rt + 1, -0.6, 0.6, t, t + PL['collar_h'] + 1))   # Klemmschlitz
    holes.append(cyl(1.6, 2 * (rt + PL['collar_wall']) + 4, (-rt - PL['collar_wall'] - 2, 3.5, t + PL['collar_h'] / 2), (1, 0, 0)).cut(cyl(rt + 0.2, 40, (0, 0, 0))))
    return s.cut(Part.makeCompound(holes))


def static_parts(gear_angle=0.0):
    out = []
    rt = P['tube']; hl = rt['half_len']
    tube = cyl(rt['d'] / 2, 2 * hl, (0, 0, -hl)).cut(cyl(rt['d'] / 2 - rt['wall'], 2 * hl + 2, (0, 0, -hl - 1)))
    out.append((tube, 'MITTELROHR-AL-D30x1', 'Kauf', None, 2700, 1.0))
    b = P['bearing']; ri = b['inner_ring_od'] / 2
    up_in = (P['levels_z'][0] + b['z_local'][0], P['levels_z'][0] + b['z_local'][1] + b['B'])     # Lagerbereich oben (Welt)
    face_up = P['levels_z'][0] + GR['z_local'] + 0.5 + MO['shaft_h'] + MO['body_h']
    sl_mid = cyl(ri, 2 * up_in[0], (0, 0, -up_in[0])).cut(cyl(rt['d'] / 2 + 0.15, 2 * up_in[0] + 2, (0, 0, -up_in[0] - 1)))
    out.append((sl_mid, 'TM-HUELSE-MITTE', 'Druck', None, P['print']['density']['PETG'], P['print']['fill']['sleeve']))
    for s in (1, -1):
        z0, z1 = up_in[1], face_up
        sl = cyl(ri, z1 - z0, (0, 0, z0)).cut(cyl(rt['d'] / 2 + 0.15, z1 - z0 + 2, (0, 0, z0 - 1)))
        if s < 0: sl.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        out.append((sl, 'TM-HUELSE-AUSSEN', 'Druck', None, P['print']['density']['PETG'], P['print']['fill']['sleeve']))
    for level, ang in zip(P['levels_z'], MO['angle_deg']):
        parts, _ = motor_stack(level, ang, gear_angle); out += parts
    return out


# ---------------------------------------------------------------- Pruefungen
def mass_g(item):
    s, ident, kind, m, rho, fill = item
    if m is not None: return m
    return s.Volume * 1e-9 * rho * fill * 1000


def fits_bed(shape):
    bb = shape.BoundBox; d = sorted([bb.XLength, bb.YLength, bb.ZLength]); bed = sorted(P['print']['bed'])
    return all(a <= b for a, b in zip(d, bed)), [round(x, 1) for x in (bb.XLength, bb.YLength, bb.ZLength)]


def collisions(group_a, group_b, tol=1e-3):
    hits = []
    for sa, ida, *_ in group_a:
        for sb, idb, *_ in group_b:
            if not sa.BoundBox.intersect(sb.BoundBox): continue
            v = sa.common(sb).Volume
            if v > tol: hits.append((ida, idb, round(v, 3)))
    return hits


def min_dist(group_a, group_b):
    best = (1e9, None, None)
    for sa, ida, *_ in group_a:
        for sb, idb, *_ in group_b:
            d = sa.distToShape(sb)[0]
            if d < best[0]: best = (d, ida, idb)
    return best


def main():
    pu, pl = P['pitch_hover_deg']
    upper_local = rotor_local(pu); lower_local = rotor_local(-pl)   # unten gekippt: lokaler Pitch negativ
    report = {'status': P['status'], 'servo': SV['name'], 'pitch_hover_deg': [pu, pl]}

    # Kollisionen ueber mehrere Rotorwinkel (oben +a, unten -a; Ritzel synchron)
    col, gearmesh, dists = {}, [], []
    for a in P['check_angles_deg']:
        up = place_rotor(upper_local, P['levels_z'][0], a); lo = place_rotor(lower_local, P['levels_z'][1], a)
        st = static_parts(a)
        pin_items = [x for x in st if x[1] == 'RITZEL-M1-Z14']; st_nopin = [x for x in st if x[1] != 'RITZEL-M1-Z14']
        gears_up = [x for x in up if x[1] == 'TM-ZAHNKRANZ-91']; gears_lo = [x for x in lo if x[1] == 'TM-ZAHNKRANZ-91']
        c = collisions(up, st_nopin) + collisions(lo, st_nopin) + collisions(up, lo)
        c += collisions([x for x in up if x[1] != 'TM-ZAHNKRANZ-91'], pin_items) + collisions([x for x in lo if x[1] != 'TM-ZAHNKRANZ-91'], pin_items)
        col[str(a)] = c
        for g, p_ in ((gears_up[0], pin_items[0]), (gears_lo[0], pin_items[1])):
            v = g[0].common(p_[0]).Volume; d = g[0].distToShape(p_[0])[0]
            gearmesh.append({'winkel_deg': a, 'ueberdeckung_mm3': round(v, 4), 'min_abstand_mm': round(d, 3)})
        if a == 0:
            blades_up = [x for x in up if x[1] == 'TM-FLUEGEL']; blades_lo = [x for x in lo if x[1] == 'TM-FLUEGEL']
            motors = [x for x in st if x[1] in ('MOTOR-ECO2-2306', 'TM-HALTEPLATTE')]
            for name, ga, gb in (('Fluegel oben - Motor/Platte', blades_up, motors), ('Fluegel unten - Motor/Platte', blades_lo, motors),
                                 ('Fluegel oben - Fluegel unten', blades_up, blades_lo),
                                 ('Rotorelektronik - Motor', [x for x in up + lo if x[1].startswith('ROT-')], [x for x in st if x[1] == 'MOTOR-ECO2-2306']),
                                 ('Nabe oben - Nabe unten', [x for x in up if x[1] == 'TM-NABE'], [x for x in lo if x[1] == 'TM-NABE'])):
                d, ia, ib = min_dist(ga, gb); dists.append({'paar': name, 'min_abstand_mm': round(d, 2)})
    report['kollisionen_je_winkel'] = col
    report['kollisionsfrei'] = all(not v for v in col.values())
    report['verzahnung'] = gearmesh
    report['verzahnung_ohne_ueberdeckung'] = all(g['ueberdeckung_mm3'] < 1e-3 for g in gearmesh)
    report['mindestabstaende'] = dists

    # Pitch-Endlagen: Fluegel gegen Nabe und Nachbarfluegel
    hub = hub_shape(); ends = []
    for ang in (-2, 21):
        b0 = pitched(blade_shape(), ang); b1 = rotz(b0, 360 / N)
        ends.append({'pitch_deg': ang, 'fluegel_nabe_mm3': round(b0.common(hub).Volume, 3), 'fluegel_nachbar_mm': round(b0.distToShape(b1)[0], 2)})
    report['pitch_endlagen'] = ends

    # Masse, Schwerpunkt, Unwucht je Rotor
    up0 = place_rotor(upper_local, P['levels_z'][0], 0); lo0 = place_rotor(lower_local, P['levels_z'][1], 0); st0 = static_parts(0)
    def cg(items):
        M = 0; c = V(0, 0, 0)
        for it in items:
            m = mass_g(it); M += m; c += it[0].CenterOfMass * m if hasattr(it[0], 'CenterOfMass') and it[0].Volume > 0 else V(0, 0, 0)
        return M, c * (1 / M)
    mu, cu = cg(up0); ml, cl_ = cg(lo0)
    purchased = P['purchased_mass_g']
    extra = purchased['battery'] + purchased['fc_esc'] + purchased['receiver'] + purchased['bridge'] + purchased['wiring']
    m_static = sum(mass_g(x) for x in st0)
    report['masse_g'] = {'rotor_oben': round(mu, 1), 'rotor_unten': round(ml, 1), 'feststehend_cad': round(m_static, 1),
                         'akku_fc_empfaenger_bridge_kabel': extra, 'gesamt': round(mu + ml + m_static + extra, 0),
                         'auslegung_phase1': 1097}
    report['unwucht'] = {'rotor_oben_gmm': round(mu * math.hypot(cu.x, cu.y), 1), 'rotor_unten_gmm': round(ml * math.hypot(cl_.x, cl_.y), 1),
                         'hinweis': 'statische Unwucht aus CAD (Platzhaltermassen); Ausgleich ueber Wuchtgewicht gegenueber dem ESP32'}

    # Druckteile: einzeln in Druckorientierung exportieren, Druckbett pruefen
    blade_print = blade_shape(); blade_print.translate(V(0, 0, -blade_print.BoundBox.ZMin))
    hub_print = hub_shape(); hub_print.translate(V(0, 0, -HUB['z_min']))
    gear_print, gradii = ring_gear_shape(); gear_print.translate(V(0, 0, -GR['z_local']))
    sleeves = [x for x in st0 if x[1].startswith('TM-HUELSE')]
    prints = {'Fluegel': (blade_print, 16), 'Nabe': (hub_print, 2), 'Zahnkranz_91Z_m1': (gear_print, 2), 'Halteplatte': (local_plate(), 2),
              'Mitnehmer': (driver_shape(), 16), 'Huelse_Mitte': (sleeves[0][0], 1), 'Huelse_Aussen': (sleeves[1][0], 2)}
    report['druckteile'] = {}
    for name, (shape, count) in prints.items():
        s = shape.copy(); s.translate(V(-s.BoundBox.XMin, -s.BoundBox.YMin, -s.BoundBox.ZMin))
        mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.25, Relative=False)
        mesh.write(str(STL / f'{name}.stl'))
        ok, dims = fits_bed(s)
        report['druckteile'][name] = {'anzahl': count, 'masse_mm': dims, 'passt_aufs_bett': ok, 'gueltig': s.isValid(), 'volumen_cm3': round(s.Volume / 1000, 2)}
    report['zahnkranz'] = {'teilkreis_mm': round(2 * gradii[0], 2), 'kopfkreis_mm': round(2 * gradii[1], 2), 'fusskreis_mm': round(2 * gradii[2], 2),
                           'achsabstand_mm': GR['module'] * (GR['z_ring'] + GR['z_pinion']) / 2 + GR['center_extra']}

    # FreeCAD-Dokument
    doc = App.newDocument('R04_Testmodell_1zu4')
    info = doc.addObject('App::FeaturePython', 'Konstruktionsstatus')
    for k, v in {'Status': P['status'], 'Hinweis': P['hinweis'], 'Quelle': 'modell_r04/cad/erstellen.py + parameter.json'}.items():
        info.addProperty('App::PropertyString', k); setattr(info, k, v)
    groups = {}
    rows = []
    for label, items in (('Rotor_oben', up0), ('Rotor_unten', lo0), ('Feststehend', st0)):
        g = doc.addObject('App::DocumentObjectGroup', label)
        for i, it in enumerate(items):
            s, ident, kind, *_ = it
            o = doc.addObject('Part::Feature', f'{label}_{ident}_{i}'.replace('-', '_')); o.Shape = s; g.addObject(o)
            for k, v in (('BauteilID', ident), ('Herstellung', kind), ('Masse_g', f'{mass_g(it):.2f}')):
                o.addProperty('App::PropertyString', k); setattr(o, k, v)
            rows.append({'Gruppe': label, 'BauteilID': ident, 'Herstellung': kind, 'Masse_g': round(mass_g(it), 2)})
    doc.recompute()
    doc.saveAs(str(HERE / 'R04_Testmodell_1zu4.FCStd'))
    Part.export([o for o in doc.Objects if hasattr(o, 'BauteilID')], str(HERE / 'R04_Testmodell_1zu4.step'))
    # Grobes Vorschaunetz je Gruppe fuer vorschau.py (Farbe nach Gruppe/Art)
    for label, items in (('Rotor_oben', up0), ('Rotor_unten', lo0), ('Feststehend', st0)):
        for kind in ('Druck', 'Kauf'):
            sel = [it[0] for it in items if (it[2] == 'Druck') == (kind == 'Druck') and it[0].Volume > 0]
            if sel:
                m = MeshPart.meshFromShape(Shape=Part.makeCompound(sel), LinearDeflection=0.4, AngularDeflection=0.5, Relative=False)
                m.write(str(STL.parent / 'vorschau' / f'{label}_{kind}.stl'))
    App.closeDocument(doc.Name)
    agg = {}
    for r in rows:
        k = (r['BauteilID'], r['Herstellung']); n, m = agg.get(k, (0, 0)); agg[k] = (n + 1, m + r['Masse_g'])
    with (HERE / 'Stueckliste.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['BauteilID', 'Herstellung', 'Anzahl', 'Masse_gesamt_g'])
        for (ident, kind), (n, m) in sorted(agg.items()): w.writerow([ident, kind, n, round(m, 1)])
        for k, v in purchased.items():
            if k != 'pinion': w.writerow([k.upper(), 'Kauf', 1, v])
    (HERE / 'Pruefbericht.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k: report[k] for k in ('kollisionsfrei', 'verzahnung_ohne_ueberdeckung', 'mindestabstaende', 'pitch_endlagen', 'masse_g', 'unwucht', 'druckteile', 'zahnkranz')}, ensure_ascii=False, indent=1))
    if not report['kollisionsfrei']: print('KOLLISIONEN:', json.dumps(col, ensure_ascii=False))


if __name__ == '__main__':
    main()
