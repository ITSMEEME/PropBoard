#!/usr/bin/env python3
"""R04-Taumelmodell 1:4 – parametrisches FreeCAD-Modell, Fertigungsentwurf F01. Millimeter.

Steuerung ueber je eine Taumelscheibe pro Rotor (kollektiv + zyklisch) statt eines Servos je Fluegel.
Lokaler Rotorrahmen: Fluegelebene z = 0, Aussenseite (Zahnkranz, Taumelscheibe, Motor, Platte) +z.
Oberer Aufbau = lokaler Aufbau + 30 mm; unterer = um x gekippt, um z 180 Grad gedreht, -30 mm (gleiche Teile).

Je Pruefzustand (Kollektiv, Zyklik, Rotorwinkel) wird die Lage der Taumelscheibe so bestimmt, dass alle
8 Steuerstangen ihre Nennlaenge haben (Gauss-Newton); der Restfehler wird ausgewiesen.

    FREECAD_LIB=.cfd-tools/freecad/usr/lib .cfd-tools/freecad/usr/bin/python modell_r04_taumel/cad/erstellen.py
"""
import csv, json, math, os, sys
import functools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.extend([p for p in (os.environ.get('FREECAD_LIB'), '/usr/lib/freecad/lib') if p])
import FreeCAD as App
import Part, MeshPart

P = json.loads((HERE / 'parameter.json').read_text())
V = App.Vector
BL, HUB, HO, LID, GR, SW, MO, PL = P['blade'], P['hub'], P['horn'], P['lid'], P['gear'], P['swash'], P['motor'], P['plate']
N = BL['count']; D = P['print']['density']; F = P['print']['fill']
STL = HERE / 'stl'; STL.mkdir(exist_ok=True); (HERE / 'vorschau').mkdir(exist_ok=True)
CDIST = GR['module'] * (GR['z_ring'] + GR['z_pinion']) / 2 + GR['center_extra']


def cached_geometry(fn):
    """Reuse expensive local BReps, returning independent copies for placement.

    Include every input parameter in the key so spreadsheet edits cannot reuse
    stale geometry in the manufacturing features.
    """
    @functools.lru_cache(maxsize=32)
    def cached(parameter_signature, args, kwargs):
        return fn(*args, **dict(kwargs))
    def clone(value):
        if isinstance(value, Part.Shape): return value.copy()
        if isinstance(value, list): return [clone(v) for v in value]
        if isinstance(value, tuple): return tuple(clone(v) for v in value)
        return value
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        return clone(cached(json.dumps(P, sort_keys=True), args, tuple(sorted(kwargs.items()))))
    return wrapped


def cyl(r, h, base=(0, 0, 0), axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*base), V(*axis))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def ring(r0, r1, z0, h):
    return cyl(r1, h, (0, 0, z0)).cut(cyl(r0, h + 2, (0, 0, z0 - 1)))


def rotz(s, deg):
    s = s.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), deg); return s


def rotx(s, deg):
    s = s.copy(); s.rotate(V(0, 0, 0), V(1, 0, 0), deg); return s


def placed(s, pl):
    s = s.copy(); s.Placement = pl.multiply(s.Placement); return s


def poly_face(pts, plane='xy', offset=0.0):
    vs = [V(x, y, offset) for x, y in pts] if plane == 'xy' else [V(offset, y, z) for y, z in pts]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


# ---------------------------------------------------------------- Verzahnung (Evolvente)
def gear_points(m, z, alpha_deg, backlash, n=10):
    a = math.radians(alpha_deg); r = m * z / 2; rb = r * math.cos(a); ra = r + m; rf = r - 1.25 * m
    inv = lambda x: math.tan(x) - x
    half = math.pi / (2 * z) - backlash / (2 * r)
    theta = lambda rr: half + inv(a) - inv(math.acos(min(1.0, rb / rr)))
    rs = max(rf, rb); radii = [rs + (ra - rs) * i / n for i in range(n + 1)]; pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        pts += ([(rf, c - theta(rs))] if rf < rs else []) + [(rr, c - theta(rr)) for rr in radii] + \
               [(rr, c + theta(rr)) for rr in reversed(radii)] + ([(rf, c + theta(rs))] if rf < rs else [])
        a0, a1 = c + theta(rs), c + 2 * math.pi / z - theta(rs)
        pts += [(rf, a0 + (a1 - a0) * t) for t in (0.25, 0.5, 0.75)]
    return [(rr * math.cos(t), rr * math.sin(t)) for rr, t in pts], (r, ra, rf)


def spur(z, face, bore_r, phase=0.0):
    pts, radii = gear_points(GR['module'], z, GR['pressure_angle'], GR['backlash'])
    return rotz(poly_face(pts).extrude(V(0, 0, face)).cut(cyl(bore_r, face + 2, (0, 0, -1))), phase), radii


# ---------------------------------------------------------------- Fluegel mit Zapfen und Vierkant (x radial, y Nase +)
def naca_half(q):
    q = min(max(q, 0.0), 1.0); tc = BL['tc']
    return 5 * tc * (0.2969 * math.sqrt(q) - 0.126 * q - 0.3516 * q * q + 0.2843 * q ** 3 - 0.1036 * q ** 4) * BL['chord'] + BL['te_mm'] / 2 * q ** 10


@cached_geometry
def blade_shape():
    c = BL['chord']; qs = [(1 - math.cos(math.pi * i / 60)) / 2 for i in range(61)]
    pts = [((0.5 - q) * c, naca_half(q)) for q in qs] + [((0.5 - q) * c, -naca_half(q)) for q in reversed(qs[1:])]
    foil = poly_face(pts, 'yz', BL['r_airfoil_start']).extrude(V(BL['r_tip'] - BL['r_airfoil_start'], 0, 0))
    rb = BL['boss_d'] / 2; sq = BL['square'] / 2; r0 = BL['boss_r_in']
    boss = cyl(rb, BL['r_airfoil_start'] - r0 - BL['square_len'] + 0.5, (r0 + BL['square_len'], 0, 0), (1, 0, 0))
    square = box(r0, r0 + BL['square_len'] + 0.01, -sq, sq, -sq, sq)
    groove = cyl(rb + 1, BL['groove_w'], (BL['groove_r'] - BL['groove_w'] / 2, 0, 0), (1, 0, 0)).cut(
        cyl(rb - BL['groove_depth'], BL['groove_w'] + 2, (BL['groove_r'] - BL['groove_w'] / 2 - 1, 0, 0), (1, 0, 0)))
    return foil.fuse([boss, square]).removeSplitter().cut(groove)


@cached_geometry
def pins():
    p = P['pin']; return [cyl(p['d'] / 2, p['len'], (BL['groove_r'], -p['len'] / 2, s * p['z_offset']), (0, 1, 0)) for s in (-1, 1)]


@cached_geometry
def horn_shape(d):
    """Pitchhebel auf dem Vierkant, Arm in Richtung d*y (oben +y, unten -y, gleiches Teil gewendet)."""
    r0 = BL['boss_r_in']; sq = BL['square'] / 2 + 0.1; y1 = HO['arm'] + 2.0
    body = box(r0 - 0.5, r0 + BL['square_len'] - 0.2, -sq - 2.5, y1, -HO['w'] / 2, HO['w'] / 2)
    body = body.cut(box(r0 - 1, r0 + BL['square_len'] + 1, -sq, sq, -sq, sq))
    return body if d > 0 else rotx(body, 180)


def horn_ball_local(d):
    return V(HO['r_center'], d * HO['arm'], HO['ball_z'])


# ---------------------------------------------------------------- Nabe (Topf) und Deckel/Zahnkranz
@cached_geometry
def hub_shape():
    zmin, zmax, h = HUB['z_min'], HUB['z_max'], HUB['z_max'] - HUB['z_min']; b = P['bearing']
    s = ring(b['D'] / 2, HUB['r_inner_ring'], zmin, h)                                        # Innenring mit Lagersitzen
    s = s.fuse(ring(b['D'] / 2 - 0.5, HUB['r_out'], zmin, HUB['floor_t']))                   # Boden
    s = s.fuse(ring(HUB['r_wall_in'], HUB['r_out'], zmin, h)).removeSplitter()              # Aussenwand
    s = s.cut(cyl(b['d'] / 2 + 1.5, h + 2, (0, 0, zmin - 1)))
    for z0 in b['z_local']: s = s.cut(cyl(b['D'] / 2, b['B'], (0, 0, z0)))
    # Lagerschulter: zwischen den Lagern Bohrung kleiner als Lageraussen-D
    s = s.fuse(ring(b['D'] / 2 - 2, b['D'] / 2 + 0.01, b['z_local'][0] + b['B'], b['z_local'][1] - b['z_local'][0] - b['B'])).removeSplitter()
    tools = []
    for k in range(N):
        a = 360 * k / N
        tools.append(rotz(cyl(BL['boss_d'] / 2 + HUB['bore_clear'], HUB['r_out'] - HUB['r_wall_in'] + 2, (HUB['r_wall_in'] - 1, 0, 0), (1, 0, 0)), a))
        tools += [rotz(p, a) for p in pins()]
        tools.append(rotz(cyl(HUB['screw_d'] / 2, 8, (HUB['screw_r'], 0, zmax - 7.9)), a + 180 / N))
    return s.cut(Part.makeCompound(tools))


@cached_geometry
def lid_shape(d=1, teeth=True):
    if teeth: g, radii = spur(GR['z_ring'], GR['face'], LID['r_in'])
    else: radii = (0, GR['module'] * (GR['z_ring'] / 2 + 1), 0); g = ring(LID['r_in'], radii[1], 0, GR['face'])   # Ersatzkoerper fuer Kollisionen
    g.translate(V(0, 0, LID['z0']))
    g = g.cut(cyl(LID['rim_r_in'], GR['face'] + 2, (0, 0, LID['z0'] + LID['disk_t']))).fuse(ring(LID['r_in'], LID['rim_r_in'] + 0.5, LID['z0'], LID['disk_t'])).removeSplitter()
    tools = []
    sx, sy = LID['slot']
    for k in range(N):
        a = 360 * k / N
        y0, y1 = sorted((d * LID['slot_y0'], d * (LID['slot_y0'] + sy)))   # Langloch nur auf der Hebelseite
        tools.append(rotz(box(HO['r_center'] - sx / 2, HO['r_center'] + sx / 2, y0, y1, LID['z0'] - 1, LID['z0'] + GR['face'] + 1), a))
        tools.append(rotz(cyl(HUB['screw_d'] / 2 + 0.25, LID['disk_t'] + 2, (HUB['screw_r'], 0, LID['z0'] - 1)), a + 180 / N))
        tools.append(rotz(cyl(LID['window_d'] / 2, LID['disk_t'] + 2, (LID['window_r'], 0, LID['z0'] - 1)), a))
    # Dedicated support for the drive pin, opposite the blade-link windows.
    tools.append(rotz(cyl(LID.get('driver_pin_bore_d',3.1)/2,
                           LID['disk_t']+2,(LID['driver_pin_r'],0,LID['z0']-1)),
                      -d*LID['driver_angle']))
    return g.cut(Part.makeCompound(tools)), radii


def driver_pin(d=1):
    z0 = LID['z0'] + LID['disk_t'] - LID.get('driver_pin_embed',3.0)
    return rotz(cyl(LID['driver_pin_d'] / 2, LID['driver_pin_top'] - z0, (LID['driver_pin_r'], 0, z0)), -d * LID['driver_angle'])


# ---------------------------------------------------------------- Taumelscheibe (Teile im eigenen Rahmen: Kugelmitte im Ursprung)
@cached_geometry
def swash_sleeve():
    h = SW['sleeve_half']; s = cyl(SW['sleeve_od'] / 2, 2 * h, (0, 0, -h))
    s = s.fuse(Part.makeSphere(SW['sphere_d'] / 2).common(cyl(30, 10, (0, 0, -5)))).removeSplitter()
    return s.cut(cyl(SW['sleeve_id'] / 2, 2 * h + 2, (0, 0, -h - 1)))


def swash_bearing():
    b = SW['bearing']; return ring(b['d'] / 2 + 0.02, b['D'] / 2 - 0.02, -b['B'] / 2, b['B'])


@cached_geometry
def swash_stationary():
    b = SW['bearing']; sp = SW['sphere_d'] / 2
    s = cyl(b['d'] / 2 - 0.05, b['B'], (0, 0, -b['B'] / 2)).cut(Part.makeSphere(sp + 0.05))
    s = s.fuse(ring(SW['flange_r'][0], SW['flange_r'][1], b['B'] / 2, SW['stat_flange_t']))
    z_arm0 = SW['arm_z0']; arms = []
    for ang in SW['servo_angles_deg'] + [SW['guide_angle_deg']]:
        riser = box(SW['riser_r'][0], SW['riser_r'][1], -SW['stat_arm_w'] / 2, SW['stat_arm_w'] / 2, b['B'] / 2, z_arm0 + SW['arm_t'])
        arm = box(SW['riser_r'][0], SW['stat_arm_r'], -SW['stat_arm_w'] / 2, SW['stat_arm_w'] / 2, z_arm0, z_arm0 + SW['arm_t'])
        arms.append(rotz(riser.fuse(arm), ang))
    s = s.fuse(arms).removeSplitter()
    return s


def stat_ball_local(ang, guide=False):
    """Radialer Kugelbolzen (Servo) bzw. Fuehrungsstift am Armende im Taumelscheibenrahmen."""
    zc = SW['arm_z0'] + SW['arm_t'] / 2; r = SW['stat_arm_r'] + SW['stud_len'] + (0 if guide else SW['ball_d'] / 2)
    a = math.radians(ang); return V(r * math.cos(a), r * math.sin(a), zc)


def swash_stat_hardware():
    out = []; zc = SW['arm_z0'] + SW['arm_t'] / 2
    for ang in SW['servo_angles_deg']:
        stud = cyl(1.0, SW['stud_len'], (SW['stat_arm_r'], 0, zc), (1, 0, 0)).fuse(Part.makeSphere(SW['ball_d'] / 2, stat_ball_local(0)))
        out.append((rotz(stud, ang), 'KUGELBOLZEN-M2'))
    pin = cyl(1.5, 7, (SW['stat_arm_r'], 0, zc), (1, 0, 0)); out.append((rotz(pin, SW['guide_angle_deg']), 'FUEHRUNGSSTIFT-D3'))
    return out


@cached_geometry
def swash_rotating():
    b = SW['bearing']; r0 = b['D'] / 2 + 0.05; r1 = SW['rot_ring_od'] / 2
    s = ring(r0, r1, -b['B'] / 2, b['B']).fuse(ring(b['D'] / 2 - 1.5, r0 + 0.01, b['B'] / 2 - 1, 1)).removeSplitter()   # Schulter
    slot = Part.makeCompound([rotz(box(r0 - 1, r1 + 1, -SW['slot_w'] / 2, SW['slot_w'] / 2, -10, 10), sg * LID['driver_angle']) for sg in (1, -1)])   # Mitnehmerschlitze (einer genutzt)
    holes = [rotz(cyl(1.0, 6, (HO['r_center'], d * HO['arm'], -b['B'] / 2 - 1)), 360 * k / N) for k in range(N) for d in (1, -1)]
    return s.cut(Part.makeCompound([slot] + holes))


def rot_ball_local(k, d):
    return rotz_v(V(HO['r_center'], d * HO['arm'], SW['rot_ball_z']), 360 * k / N)


def rotz_v(v, deg):
    a = math.radians(deg); return V(v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a), v.z)


# ---------------------------------------------------------------- Kinematik
def swash_placement(c, tx, ty):
    return App.Placement(V(0, 0, c), App.Rotation(V(1, 0, 0), tx).multiply(App.Rotation(V(0, 1, 0), ty)))


def blade_pitch(theta0, cyc, a, k):
    return theta0 + cyc * math.sin(math.radians(a + 360 * k / N))


def horn_ball_world(theta, s, a, k):
    """Kugelmitte am Pitchhebel im lokalen Rotorrahmen; s = +1 oben, -1 unten (lokaler Pitch s*theta, Arm d = s)."""
    v = horn_ball_local(s); b = math.radians(s * theta)
    v = V(v.x, v.y * math.cos(b) - v.z * math.sin(b), v.y * math.sin(b) + v.z * math.cos(b))
    return rotz_v(v, a + 360 * k / N)


def solve_swash(theta0, cyc, a, s, L):
    hb = [horn_ball_world(blade_pitch(theta0, cyc, a, k), s, a, k) for k in range(N)]
    def res(x):
        pl = swash_placement(*x)
        return [(pl.multVec(rotz_v(rot_ball_local(k, s), a)) - hb[k]).Length - L for k in range(N)]
    x = [hb[0].z - SW['rot_ball_z'] + L, 0.0, 0.0]
    for _ in range(30):
        r0 = res(x); J = []
        for j in range(3):
            xe = list(x); xe[j] += 1e-4; J.append([(a1 - a0) / 1e-4 for a1, a0 in zip(res(xe), r0)])
        A = [[sum(J[i][k] * J[j][k] for k in range(N)) for j in range(3)] for i in range(3)]
        g = [sum(J[i][k] * r0[k] for k in range(N)) for i in range(3)]
        dx = solve3(A, [-v for v in g]); x = [xi + di for xi, di in zip(x, dx)]
        if max(abs(v) for v in dx) < 1e-7: break
    return x, max(abs(v) for v in res(x)), hb


def solve3(A, b):
    import copy
    M = [row[:] + [bb] for row, bb in zip(copy.deepcopy(A), b)]
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(M[r][i])); M[i], M[p] = M[p], M[i]
        for r in range(3):
            if r != i:
                f = M[r][i] / M[i][i]; M[r] = [x - f * y for x, y in zip(M[r], M[i])]
    return [M[i][3] / M[i][i] for i in range(3)]


def link_len_hover():
    return SW['c_hover_link_len']


def rod(p0, p1, r=1.25, trim=None):
    d = p1 - p0; L = d.Length; u = d * (1 / L); t = SW['ball_d'] / 2 + 0.3 if trim is None else trim
    b = p0 + u * t
    return cyl(r, L - 2 * t, (b.x, b.y, b.z), (u.x, u.y, u.z))


# ---------------------------------------------------------------- Aufbau eines Rotors mit seinen feststehenden Teilen (lokal)
def local_assembly(theta0, cyc, a, s):
    """Liefert (drehend, feststehend, info). Eintraege: (shape, id, art, masse_g|None, dichte|None, fuell|None)."""
    L = link_len_hover(); x, err, hb = solve_swash(theta0, cyc, a, s, L)
    spl = swash_placement(*x); rot_pl = spl.multiply(App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), a)))
    rot, st = [], []
    hub = rotz(hub_shape(), a); lid, _ = lid_shape(s)
    rot += [(hub, 'TM-NABE', 'Druck', None, D['PA-CF'], F['hub']), (rotz(lid, a), 'TM-DECKEL-ZAHNKRANZ-130', 'Druck', None, D['PA-CF'], F['gear']),
            (rotz(driver_pin(s), a), 'MITNEHMERSTIFT-D3', 'Kauf', None, 7850, 1.0)]
    blade0 = blade_shape(); horn0 = horn_shape(s)
    for k in range(N):
        ang = a + 360 * k / N; th = blade_pitch(theta0, cyc, a, k)
        rot.append((rotz(rotx(blade0, s * th), ang), 'TM-FLUEGEL', 'Druck', None, D['PA-CF'], F['blade']))
        rot.append((rotz(rotx(horn0, s * th), ang), 'TM-PITCHHEBEL', 'Druck', None, D['PA-CF'], F['horn']))
        hball = Part.makeSphere(SW['ball_d'] / 2, hb[k]); rot.append((hball, 'KUGELBOLZEN-M2', 'Kauf', 0.5, None, None))
        for p in pins(): rot.append((rotz(p, ang), 'STIFT-D2x18', 'Kauf', None, 7850, 1.0))
        rball = rot_pl.multVec(rot_ball_local(k, s))
        rot.append((Part.makeSphere(SW['ball_d'] / 2, rball), 'KUGELBOLZEN-M2', 'Kauf', 0.5, None, None))
        rot.append((rod(hb[k], rball), 'STEUERSTANGE', 'Kauf', P['purchased_mass_g']['link_set'], None, None))
    b = P['bearing']
    for z0 in b['z_local']: rot.append((ring(b['d'] / 2, b['D'] / 2, z0, b['B']), 'LAGER-6806', 'Kauf', b['mass_g'], None, None))
    rot.append((placed(swash_rotating(), rot_pl), 'TM-TAUMEL-DREHRING', 'Druck', None, D['PA-CF'], F['swash']))
    # Feststehend: Gleitkugel, Innenring, Lager, Arme, Servostangen, Halteplatte, Motor, Ritzel, Klemmring, Fuehrung, Servos
    sleeve_pl = App.Placement(V(0, 0, x[0]), App.Rotation())
    st.append((placed(swash_sleeve(), sleeve_pl), 'TM-TAUMEL-GLEITKUGEL', 'Druck', None, D['PA-CF'], F['swash']))
    st.append((placed(swash_stationary(), spl), 'TM-TAUMEL-INNENRING', 'Druck', None, D['PA-CF'], F['swash']))
    st.append((placed(swash_bearing(), spl), 'LAGER-6809', 'Kauf', SW['bearing']['mass_g'], None, None))
    for shp, ident in swash_stat_hardware(): st.append((placed(shp, spl), ident, 'Kauf', 0.5, None, None))
    for ang in SW['servo_angles_deg']:
        p0 = spl.multVec(rotz_v(stat_ball_local(0), ang)); top = rotz_v(V(stat_ball_local(0).x, 0, PL['rod_top_z']), ang)
        st.append((rod(p0, top, 1.0, SW['ball_d'] / 2 + 0.3), 'SERVOSTANGE', 'Kauf', 1.0, None, None))
    st += static_parts(a)
    return rot, st, {'c': x[0], 'tilt_x_deg': x[1], 'tilt_y_deg': x[2], 'stangenfehler_mm': err}


def motor_mount_points():
    """Local motor screw centres; retain legacy PCD unless a rectangular pitch is explicit.

    A 16 mm PCD gives 11.3137 mm square pitch, not a 16 x 16 mm mounting pattern.
    Manufacturer/user source and verification belong to the selected revision.
    """
    pattern = MO.get('mount_pattern', 'pcd')
    if pattern == 'rectangular':
        dx, dy = MO['mount_pitch_mm']
        if dx <= 0 or dy <= 0: raise ValueError('Positive motor mounting pitch required')
        return [(CDIST + sx * dx / 2, sy * dy / 2) for sx in (-1, 1) for sy in (-1, 1)]
    if pattern != 'pcd': raise ValueError('Unknown motor mount pattern: ' + pattern)
    return [(CDIST + MO['mount_pcd'] / 2 * math.cos(q), MO['mount_pcd'] / 2 * math.sin(q))
            for q in (math.pi / 4 + i * math.pi / 2 for i in range(4))]


@cached_geometry
def plate_shape():
    t = PL['t']; z0 = P['gear']['pinion_z0'] + MO['shaft_h'] + MO['body_h']; rt = P['tube']['d'] / 2
    s = cyl(rt + PL['collar_wall'] + 6, t, (0, 0, z0))
    s = s.fuse(box(0, CDIST, -PL['arm_w'] / 2, PL['arm_w'] / 2, z0, z0 + t)).fuse(cyl(PL['pad_d'] / 2, t, (CDIST, 0, z0)))
    pw, pd = PL['servo_pad']
    for ang in SW['servo_angles_deg']:
        s = s.fuse(rotz(box(0, PL['servo_pad_r'] + pd / 2 + 6, -pw / 2, pw / 2, z0, z0 + t), ang))
    ga = SW['guide_angle_deg']; gr = SW['stat_arm_r'] + 6
    s = s.fuse(rotz(box(0, gr + 4, -6, 6, z0, z0 + t), ga))
    guide_w=SW.get('guide_slot_w',SW['slot_w'])
    # Open the guide fork below the lowest commanded collective position.
    # The former 1 mm floor clipped the tilted D3 guide pin at minimum pitch.
    post = box(gr - 4, gr + 4, -4, 4, z0 - 11, z0 + 0.01).cut(box(gr - 5, gr + 5, -guide_w / 2, guide_w / 2, z0 - 12, z0 - 1.5))
    s = s.fuse(rotz(post, ga)).fuse(ring(rt + 0.15, rt + PL['collar_wall'], z0 + t - 0.01, PL['collar_h'])).removeSplitter()
    holes = [cyl(rt + 0.15, t + 2, (0, 0, z0 - 1)), cyl(MO['boss_d'] / 2 + 0.3, t + 2, (CDIST, 0, z0 - 1))]
    holes += [cyl(MO['mount_screw'] / 2 + 0.2, t + 2, (x, y, z0 - 1)) for x, y in motor_mount_points()]
    for ang in SW['servo_angles_deg']:
        holes.append(rotz(cyl(PL['rod_hole_d'] / 2, t + 2, (stat_ball_local(0).x, 0, z0 - 1)), ang))
    holes.append(box(-rt - PL['collar_wall'] - 1, -rt + 1, -0.6, 0.6, z0 + t, z0 + t + PL['collar_h'] + 1))
    return s.cut(Part.makeCompound(holes)), z0


def static_parts(a):
    out = []; plate, z0 = plate_shape(); out.append((plate, 'TM-HALTEPLATTE', 'Druck', None, D['PETG'], F['plate']))
    zp = GR['pinion_z0']
    out.append((cyl(MO['d'] / 2, MO['body_h'], (CDIST, 0, zp + MO['shaft_h'])), 'MOTOR-ECO2-2306', 'Kauf', MO['mass_g'], None, None))
    out.append((cyl(MO['shaft_d'] / 2, MO['shaft_h'], (CDIST, 0, zp)), 'MOTORWELLE-M5', 'Teil Motor', 0, None, None))
    ratio = GR['z_ring'] / GR['z_pinion']
    pin, _ = spur(GR['z_pinion'], GR['face'] - (zp - LID['z0']), GR['pinion_bore'] / 2, 180 / GR['z_pinion'])
    pin.rotate(V(0, 0, 0), V(0, 0, 1), -a * ratio); pin.translate(V(CDIST, 0, zp))
    out.append((pin, 'RITZEL-M1-Z20', 'Kauf', P['purchased_mass_g']['pinion'], None, None))
    out.append((ring(P['tube']['d'] / 2 + 0.15, P['bearing']['inner_ring_od'] / 2, HUB['z_max'] + 0.2, 3.8), 'TM-KLEMMRING', 'Druck', None, D['PETG'], F['sleeve']))
    pw, pd = PL['servo_pad']; sv = P['servo']
    for ang in SW['servo_angles_deg']:
        r_in = stat_ball_local(0).x + PL['rod_hole_d'] / 2 - 1   # Servo radial ausserhalb der Stangendurchfuehrung
        body = box(r_in, r_in + sv['W'], -sv['L'] / 2, sv['L'] / 2, z0 + PL['t'], z0 + PL['t'] + sv['H'])
        out.append((rotz(body, ang), 'SERVO-PLATZHALTER', 'Kauf', sv['mass_g'], None, None))
    return out


def place(items, s):
    out = []
    for shp, *rest in items:
        t = shp.copy()
        if s < 0: t.rotate(V(0, 0, 0), V(1, 0, 0), 180); t.rotate(V(0, 0, 0), V(0, 0, 1), 180)
        t.translate(V(0, 0, P['levels_z'][0 if s > 0 else 1])); out.append((t, *rest))
    return out


def world_static():
    rt = P['tube']; hl = rt['half_len']; out = []
    out.append((ring(rt['d'] / 2 - rt['wall'], rt['d'] / 2, -hl, 2 * hl), 'MITTELROHR-AL-D30x1', 'Kauf', None, 2700, 1.0))
    zb = P['levels_z'][0] + P['bearing']['z_local'][0]
    out.append((ring(rt['d'] / 2 + 0.15, P['bearing']['inner_ring_od'] / 2, -zb, 2 * zb), 'TM-HUELSE-MITTE', 'Druck', None, D['PETG'], F['sleeve']))
    C = P['cap']; zc = rt['half_len']
    for s in (1, -1):
        cap = box(-C['size'] / 2, C['size'] / 2, -C['size'] / 2, C['size'] / 2, 0, C['t']).fuse(
            ring(C.get('sleeve_id',24)/2,C.get('sleeve_od',27.8)/2,
                 -C.get('sleeve_len',8),C.get('sleeve_len',8))).removeSplitter()
        h = C['stack_hole'] / 2
        cap = cap.cut(Part.makeCompound([cyl(1.7, C['t'] + 2, (dx, dy, -1)) for dx in (-h, h) for dy in (-h, h)] +
                                        [cyl(2.6, C['t'] + 2, (dx, 0, -1)) for dx in (-C['stand_hole_pitch'] / 2, C['stand_hole_pitch'] / 2)]))
        if s < 0: cap.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        cap.translate(V(0, 0, s * zc))
        out.append((cap, 'TM-KAPPE-STACK-PRUEFSTAND', 'Druck', None, D['PETG'], F['cap']))
    return out


# ---------------------------------------------------------------- Pruefungen
def mass_g(it):
    s, ident, kind, m, rho, fill = it
    return m if m is not None else s.Volume * 1e-9 * rho * fill * 1000


CONTACT = {frozenset(p) for p in [('TM-FLUEGEL', 'TM-PITCHHEBEL'), ('TM-PITCHHEBEL', 'KUGELBOLZEN-M2'), ('STEUERSTANGE', 'KUGELBOLZEN-M2'),
           ('TM-TAUMEL-DREHRING', 'KUGELBOLZEN-M2'), ('TM-TAUMEL-DREHRING', 'LAGER-6809'), ('TM-TAUMEL-INNENRING', 'LAGER-6809'),
           ('TM-TAUMEL-INNENRING', 'TM-TAUMEL-GLEITKUGEL'), ('TM-TAUMEL-INNENRING', 'KUGELBOLZEN-M2'), ('TM-TAUMEL-INNENRING', 'FUEHRUNGSSTIFT-D3'),
           ('SERVOSTANGE', 'KUGELBOLZEN-M2'), ('TM-NABE', 'STIFT-D2x18'), ('TM-NABE', 'LAGER-6806'), ('TM-FLUEGEL', 'STIFT-D2x18'),
           ('TM-DECKEL-ZAHNKRANZ-130', 'MITNEHMERSTIFT-D3'), ('TM-NABE', 'TM-DECKEL-ZAHNKRANZ-130'), ('MOTOR-ECO2-2306', 'TM-HALTEPLATTE'),
           ('MOTORWELLE-M5', 'RITZEL-M1-Z20'), ('MOTORWELLE-M5', 'MOTOR-ECO2-2306'), ('SERVO-PLATZHALTER', 'TM-HALTEPLATTE')]}


def collisions(A, B, same=False, tol=1e-3):
    hits = []
    for i, (sa, ia, *_) in enumerate(A):
        for j, (sb, ib, *_) in enumerate(B):
            if same and j <= i: continue
            if frozenset((ia, ib)) in CONTACT or ia == ib: continue   # gleichartige Teile stehen fest zueinander
            if not sa.BoundBox.intersect(sb.BoundBox): continue
            v = sa.common(sb).Volume
            if v > tol: hits.append((ia, ib, round(v, 3)))
    return hits


def fits_bed(shape):
    bb = shape.BoundBox; d = sorted([bb.XLength, bb.YLength, bb.ZLength])
    return all(a <= b for a, b in zip(d, sorted(P['print']['bed']))), [round(x, 1) for x in (bb.XLength, bb.YLength, bb.ZLength)]


def main():
    hover = P['pitch_hover_deg']; report = {'status': P['status'], 'servo': P['servo']['name'], 'zustaende': []}
    all_ok = True
    for stt in P['check_states']:
        for a in stt['angles']:
            entry = {'zustand': stt['name'], 'winkel_deg': a}
            for s, idx in ((1, 0), (-1, 1)):
                th0 = hover[idx] if stt['theta0'] == 'hover' else stt['theta0']
                rot, st, info = local_assembly(th0, stt['cyclic'], a, s)
                gear = [x for x in rot if x[1].startswith('TM-DECKEL')][0]; pin = [x for x in st if x[1].startswith('RITZEL')][0]
                # Kollisionen mit zahnlosen Ersatzkoerpern; die echte Verzahnung wird nur gegen das Ritzel geprueft
                proxy = rotz(lid_shape(s, teeth=False)[0], a)
                pin_proxy = cyl(GR['module'] * (GR['z_pinion'] / 2 + 1), GR['face'], (CDIST, 0, GR['pinion_z0']))
                rot_c = [(proxy, *x[1:]) if x is gear else x for x in rot]
                st_c = [x for x in st if x is not pin]
                c = collisions(rot_c, st_c) + collisions(rot_c, rot_c, same=True)
                c += [h for h in collisions(rot_c, [(pin_proxy, *pin[1:])]) if h[0] != gear[1]]
                if a == stt['angles'][0]: c += collisions(st_c + [(pin_proxy, *pin[1:])], st_c + [(pin_proxy, *pin[1:])], same=True)
                gm = gear[0].common(pin[0]).Volume; gd = gear[0].distToShape(pin[0])[0]
                key = 'oben' if s > 0 else 'unten'
                entry[key] = {'theta0': th0, 'kollisionen': c, 'taumelscheibe': {k: round(v, 4) for k, v in info.items()},
                              'verzahnung_ueberdeckung_mm3': round(gm, 4), 'verzahnung_abstand_mm': round(gd, 3)}
                all_ok &= not c and gm < 1e-3 and info['stangenfehler_mm'] < 0.05
            report['zustaende'].append(entry); print(entry['zustand'], a, {k: (len(entry[k]['kollisionen']), entry[k]['taumelscheibe']) for k in ('oben', 'unten')}, flush=True)
            if any(entry[k]['kollisionen'] for k in ('oben','unten')):
                print('KOLLISIONEN', {k:entry[k]['kollisionen'] for k in ('oben','unten')}, flush=True)
    report['alle_pruefungen_bestanden'] = bool(all_ok)

    # Schwebestellung, Welt: Rotorabstand, Masse, Unwucht, Dokument
    ru, su, iu = local_assembly(hover[0], 0, 0, 1); rl, sl, il = local_assembly(hover[1], 0, 0, -1)
    up_r, up_s, lo_r, lo_s = place(ru, 1), place(su, 1), place(rl, -1), place(sl, -1); ws = world_static()
    report['kollisionen_oben_unten'] = collisions(up_r + up_s, lo_r + lo_s) + collisions(ws, up_r + lo_r)
    bl_up = [x for x in up_r if x[1] == 'TM-FLUEGEL']; bl_lo = [x for x in lo_r if x[1] == 'TM-FLUEGEL']
    report['abstand_fluegel_oben_unten_mm'] = round(min(a[0].distToShape(b[0])[0] for a in bl_up[:2] for b in bl_lo), 2)
    def cg(items):
        M = sum(mass_g(i) for i in items); c = V(0, 0, 0)
        for i in items:
            # Boolean operations may retain a Compound wrapper even around a
            # single Solid. OCCT exposes CenterOfMass only on the solids.
            solids = i[0].Solids
            volume = sum(s.Volume for s in solids)
            if volume > 0:
                center = V(0,0,0)
                for solid in solids: center += solid.CenterOfMass * solid.Volume
                c += center * (mass_g(i) / volume)
        return M, c * (1 / M)
    mr, cr = cg(ru); pm = P['purchased_mass_g']
    extra = pm['battery'] + pm['fc_esc'] + pm['receiver'] + pm['wiring']
    m_st = sum(mass_g(i) for i in su) * 2 + sum(mass_g(i) for i in ws)
    report['masse_g'] = {'rotor_drehend_je': round(mr, 1), 'feststehend_cad': round(m_st, 1), 'akku_fc_empfaenger_kabel': extra,
                         'gesamt': round(2 * mr + m_st + extra), 'vergleich_servo_modell_v1': 1195}
    report['unwucht_rotor_gmm'] = round(mr * math.hypot(cr.x, cr.y), 2)

    # Druckteile
    def flat(s):
        s = s.copy(); s.translate(V(-s.BoundBox.XMin, -s.BoundBox.YMin, -s.BoundBox.ZMin)); return s
    lid, radii = lid_shape(1); lid_lo, _ = lid_shape(-1); plate, _ = plate_shape(); cap = [x for x in ws if x[1].startswith('TM-KAPPE')][0][0]
    stat = swash_stationary(); stat.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    prints = {'Fluegel': (blade_shape(), 16), 'Nabe': (hub_shape(), 2), 'Deckel_Zahnkranz_130Z_m1_oben': (lid, 1), 'Deckel_Zahnkranz_130Z_m1_unten': (lid_lo, 1), 'Pitchhebel': (horn_shape(1), 16),
              'Taumel_Gleitkugel': (swash_sleeve(), 2), 'Taumel_Innenring': (stat, 2), 'Taumel_Drehring': (swash_rotating(), 2),
              'Halteplatte': (plate, 2), 'Kappe_Stack_Pruefstand': (cap, 2), 'Huelse_Mitte': ([x for x in ws if x[1] == 'TM-HUELSE-MITTE'][0][0], 1),
              'Klemmring': ([x for x in su if x[1] == 'TM-KLEMMRING'][0][0], 2)}
    report['druckteile'] = {}
    for name, (shape, n) in prints.items():
        s = flat(shape); ok, dims = fits_bed(s)
        MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.25, Relative=False).write(str(STL / f'{name}.stl'))
        report['druckteile'][name] = {'anzahl': n, 'masse_mm': dims, 'passt_aufs_bett': ok, 'gueltig': s.isValid(), 'volumen_cm3': round(s.Volume / 1000, 2)}
    report['zahnkranz'] = {'zaehne': GR['z_ring'], 'kopfkreis_mm': round(2 * radii[1], 2), 'ritzel': GR['z_pinion'], 'achsabstand_mm': CDIST,
                           'uebersetzung': round(GR['z_ring'] / GR['z_pinion'], 3)}

    doc = App.newDocument('R04_Taumelmodell_1zu4'); rows = []
    info = doc.addObject('App::FeaturePython', 'Konstruktionsstatus')
    for k, v in {'Status': P['status'], 'Hinweis': P['hinweis']}.items(): info.addProperty('App::PropertyString', k); setattr(info, k, v)
    for label, items in (('Rotor_oben', up_r), ('Oben_feststehend', up_s), ('Rotor_unten', lo_r), ('Unten_feststehend', lo_s), ('Mitte', ws)):
        g = doc.addObject('App::DocumentObjectGroup', label)
        for i, it in enumerate(items):
            o = doc.addObject('Part::Feature', f'{label}_{i}'); o.Shape = it[0]; g.addObject(o)
            for k, v in (('BauteilID', it[1]), ('Herstellung', it[2]), ('Masse_g', f'{mass_g(it):.2f}')): o.addProperty('App::PropertyString', k); setattr(o, k, v)
            rows.append((it[1], it[2], mass_g(it)))
        for kind in ('Druck', 'Kauf'):
            sel = [it[0] for it in items if (it[2] == 'Druck') == (kind == 'Druck') and it[0].Volume > 0]
            if sel: MeshPart.meshFromShape(Shape=Part.makeCompound(sel), LinearDeflection=0.4, AngularDeflection=0.5, Relative=False).write(str(HERE / 'vorschau' / f'{label}_{kind}.stl'))
    doc.recompute(); doc.saveAs(str(HERE / 'R04_Taumelmodell_1zu4.FCStd'))
    Part.export([o for o in doc.Objects if hasattr(o, 'BauteilID')], str(HERE / 'R04_Taumelmodell_1zu4.step')); App.closeDocument(doc.Name)
    agg = {}
    for ident, kind, m in rows: n, mm = agg.get((ident, kind), (0, 0)); agg[(ident, kind)] = (n + 1, mm + m)
    with (HERE / 'Stueckliste.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['BauteilID', 'Herstellung', 'Anzahl', 'Masse_gesamt_g'])
        for (ident, kind), (n, m) in sorted(agg.items()): w.writerow([ident, kind, n, round(m, 1)])
        for k in ('battery', 'fc_esc', 'receiver', 'wiring'): w.writerow([k.upper(), 'Kauf', 1, pm[k]])
    (HERE / 'Pruefbericht.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k: report[k] for k in ('alle_pruefungen_bestanden', 'kollisionen_oben_unten', 'abstand_fluegel_oben_unten_mm', 'masse_g', 'unwucht_rotor_gmm', 'zahnkranz')}, ensure_ascii=False, indent=1))
    print({k: (v['masse_mm'], v['passt_aufs_bett'], v['gueltig']) for k, v in report['druckteile'].items()})


if __name__ == '__main__':
    main()
