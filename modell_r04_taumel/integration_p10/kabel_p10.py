"""P10 Kabelbaum: konkrete Leitungswege als Sweep-Körper (Weltrahmen, mm).

Architektur (Konstruktionsentwurf):
* Akku → XT60 → Hauptleitung 2 × 14 AWG durch das Mittelrohr → ESC-Batteriepads (−y-Kante).
* XT60-Buchse → UBEC (Plenum unter H04) → unterer Servo-Sammelpunkt.
* Untere Servos (3) → unterer Sammelpunkt → Stammkabel 5-adrig (S4–S6, +, −) durchs Rohr →
  oberer Servoverteiler. Obere Servos (3) → oberer Servoverteiler direkt.
* Oberer Verteiler → Signalband (6 × Signal + GND) → FC-Pads; ELRS-Empfänger → FC.
* Motor oben/unten: 3 × 20 AWG (Motorlitzen verlängert) → ESC M1 (+x-Kante) / M2 (−x-Kante).

Das Mittelrohr ist die einzige Durchführung durch beide drehenden Rotoren. Belegung des
Rohrquerschnitts (Bohrung H01 Ø16): alle Leitungen bei |y| ≥ 1 + r neben dem M2-Querbolzen.
Pad-/Steckerlagen an FC/ESC sind Annahmen auf Basis der Bauraumhüllen, keine Herstellerdaten.
"""
import math
import FreeCAD as A
import Part

V = A.Vector

AWG = {  # Außendurchmesser Silikonlitze [mm], lineare Masse [g/m] (Richtwerte, nicht gemessen)
    '14AWG': (3.4, 24.0), '20AWG': (1.6, 7.0), '22AWG': (1.3, 4.8), '28AWG': (0.9, 2.0),
    'SERVO3x22AWG': (2.6, 14.5), 'STAMM5x24AWG': (4.0, 22.0), 'BAL7x22AWG': (3.4, 30.0), 'ANT': (1.2, 1.5),
}
COLORS = {'rot': (0.85, 0.12, 0.10), 'schwarz': (0.08, 0.08, 0.08), 'gelb': (0.95, 0.80, 0.10),
          'blau': (0.15, 0.35, 0.90), 'orange': (0.95, 0.50, 0.10), 'braun': (0.45, 0.28, 0.12),
          'weiss': (0.92, 0.92, 0.92), 'grau': (0.55, 0.55, 0.58), 'gruen': (0.15, 0.65, 0.25)}

# Rohrquerschnitt (x, y) und Radius
SLOT = {'P+': (2.6, -4.6), 'P-': (-2.6, -4.6), 'ML1': (-4.0, 1.9), 'ML2': (-4.0, 3.6), 'ML3': (-4.0, 5.3),
        'STAMM': (3.6, 3.4)}
TUBE_Z = (-103.0, 101.5)

# Servoleitung im lokalen Rotorrahmen (vor Azimut-Drehung): Kabelaustritt → entlang der
# Gehäuseunterseite → innerer Halterfuß → senkrecht nach außen (lokal +z).
SERVO_LOCAL = [(87.5, -44.8, 60.0), (90.6, -44.8, 60.0), (91.8, -48.3, 60.0), (88.0, -49.9, 60.0),
               (60.0, -49.9, 60.0), (46.0, -49.9, 58.0), (39.0, -46.5, 56.0), (34.5, -43.5, 58.0), (33.0, -43.0, 66.0)]
# Motorlitzen im lokalen Rotorrahmen: Austritt am Stator, Nut in der Halteplatte, nach außen.
MOTOR_C = (47.457, -27.4)
MOTOR_DIR = math.radians(330.0)


def _motor_local(r, z, off):
    c, s = math.cos(MOTOR_DIR), math.sin(MOTOR_DIR)
    return (MOTOR_C[0] + r * c - off * s, MOTOR_C[1] + r * s + off * c, z)


def rounded_path(points, radius):
    """Polylinie mit G1-stetigen Ecken (quadratische Bézier-Übergänge)."""
    P = [V(*p) for p in points]
    P = [p for i, p in enumerate(P) if i == 0 or (p - P[i - 1]).Length > 1e-6]
    if len(P) == 2:
        return Part.Wire([Part.LineSegment(P[0], P[1]).toShape()])
    edges = []
    start = P[0]
    for i in range(1, len(P) - 1):
        u = P[i] - P[i - 1]
        w = P[i + 1] - P[i]
        lu, lw = u.Length, w.Length
        u.normalize()
        w.normalize()
        if u.dot(w) < -0.5:
            raise ValueError(f'Leitungsweg kehrt bei Punkt {i} um ({P[i]})')
        ang = math.acos(max(-1.0, min(1.0, u.dot(w))))
        t = min(radius * math.tan(ang / 2) if ang > 1e-6 else 0.0, 0.45 * lu, 0.45 * lw)
        if t < 1e-4:
            continue
        a = P[i] - u * t
        b = P[i] + w * t
        if (a - start).Length > 1e-6:
            edges.append(Part.LineSegment(start, a).toShape())
        bz = Part.BezierCurve()
        bz.setPoles([a, P[i], b])
        edges.append(bz.toShape())
        start = b
    if (P[-1] - start).Length > 1e-6:
        edges.append(Part.LineSegment(start, P[-1]).toShape())
    return Part.Wire(edges)


def sweep(points, d, radius=None):
    wire = rounded_path(points, radius or max(4.0, 3.0 * d))
    e0 = wire.OrderedEdges[0]
    p0 = wire.OrderedVertexes[0].Point
    t0 = e0.tangentAt(e0.FirstParameter)
    if (e0.valueAt(e0.FirstParameter) - p0).Length > 1e-6:
        t0 = -e0.tangentAt(e0.LastParameter)
    circle = Part.Wire([Part.makeCircle(d / 2, p0, t0)])
    s = wire.makePipeShell([circle], True, False)
    return s, wire.Length


def _tube_run(x, y):
    return [(x, y, TUBE_Z[0]), (x, y, TUBE_Z[1])]


def cable_list(servo_world):
    """``servo_world(sign, j, local_point)`` bildet lokale Rotorpunkte in die Welt ab."""
    C = []

    def add(ident, von, nach, typ, farbe, pts, adern=1, bend=None):
        C.append(dict(id=ident, von=von, nach=nach, typ=typ, farbe=farbe, punkte=pts, adern=adern, biegeradius=bend))

    # ---------------------------------------------------------------- Hauptstrom
    add('P+', 'XT60-Buchse +', 'ESC Batteriepad +', '14AWG', 'rot',
        [(53.0, 3.6, -128.0), (50.0, 1.0, -118.0), (42.0, -4.6, -109.4), (8.0, -4.6, -109.4), (2.6, -4.6, -106.0)]
        + _tube_run(*SLOT['P+']) + [(3.0, -12.0, 103.0), (3.0, -25.5, 103.0), (3.0, -26.5, 108.0), (3.0, -25.0, 114.6), (3.0, -21.4, 115.3)])
    add('P-', 'XT60-Buchse −', 'ESC Batteriepad −', '14AWG', 'schwarz',
        [(53.0, -3.6, -128.0), (50.0, -6.0, -118.0), (42.0, -9.0, -109.4), (0.0, -9.0, -109.4), (-2.6, -7.5, -107.5), (-2.6, -4.6, -105.0)]
        + _tube_run(*SLOT['P-']) + [(-3.0, -12.0, 103.0), (-3.0, -25.5, 103.0), (-3.0, -26.5, 108.0), (-3.0, -25.0, 114.6), (-3.0, -21.4, 115.3)])
    add('AKKU+', 'Akku', 'XT60-Stecker +', '14AWG', 'rot', [(39.0, 3.6, -150.0), (44.0, 3.6, -156.0), (50.0, 3.6, -158.2), (53.0, 3.6, -156.8)])
    add('AKKU-', 'Akku', 'XT60-Stecker −', '14AWG', 'schwarz', [(39.0, -3.6, -150.0), (44.0, -3.6, -156.0), (50.0, -3.6, -158.2), (53.0, -3.6, -156.8)])
    add('BAL', 'Akku', 'JST-XH Balancer', 'BAL7x22AWG', 'weiss', [(-39.0, 0.0, -150.0), (-44.0, 0.0, -153.5), (-50.0, 0.0, -152.0), (-50.0, 0.0, -151.8)])
    # ---------------------------------------------------------------- UBEC
    add('UBEC_IN+', 'XT60-Buchse +', 'UBEC Eingang +', '20AWG', 'rot',
        [(50.0, 3.6, -128.2), (46.0, 6.0, -112.0), (40.0, 2.0, -106.2), (40.0, -11.5, -106.2), (40.0, -13.7, -107.4)])
    add('UBEC_IN-', 'XT60-Buchse −', 'UBEC Eingang −', '20AWG', 'schwarz',
        [(50.0, -3.6, -128.2), (45.0, -10.0, -120.0), (41.0, -12.5, -110.5), (37.5, -13.7, -108.2)])
    add('UBEC_OUT+', 'UBEC Ausgang +', 'Servo-Sammelpunkt +', '20AWG', 'rot',
        [(33.0, -13.7, -106.6), (33.0, -6.0, -106.2), (33.0, 12.0, -106.2), (33.0, 16.7, -107.6)])
    add('UBEC_OUT-', 'UBEC Ausgang −', 'Servo-Sammelpunkt −', '20AWG', 'schwarz',
        [(35.4, -13.7, -106.6), (35.4, -6.0, -106.2), (35.4, 12.0, -106.2), (35.4, 16.7, -107.6)])
    # ---------------------------------------------------------------- Stammkabel untere Servos
    add('STAMM', 'Servo-Sammelpunkt unten', 'Servoverteiler oben', 'STAMM5x24AWG', 'grau',
        [(23.0, 15.5, -109.6), (14.0, 9.0, -109.6), (6.0, 5.5, -109.4), (3.6, 3.4, -106.5)] + _tube_run(*SLOT['STAMM'])
        + [(8.0, 4.0, 103.0), (19.0, 4.0, 103.0), (21.5, 4.0, 103.8), (23.5, 4.0, 105.1), (25.5, 4.0, 105.1)])
    # ---------------------------------------------------------------- Motoren
    for sign in (1, -1):
        name = 'M1_oben' if sign > 0 else 'M2_unten'
        for k, (off, col) in enumerate(((-1.8, 'schwarz'), (0.0, 'rot'), (1.8, 'gelb'))):
            local = [_motor_local(13.5, 45.2, off), _motor_local(26.0, 45.2, off), _motor_local(28.5, 49.5, off)]
            start = [servo_world(sign, None, p) for p in local]
            if sign > 0:
                pad = (-2.2, 0.0, 2.2)[k]
                n1, n2 = (0.6 * off, 0.8 * off), (0.77 * off, 0.64 * off)
                rest = [(66.0 + n1[0], -36.0 + n1[1], 95.0), (50.0 + n1[0], -24.0 + n1[1], 114.0), (36.0 + n2[0], -14.0 + n2[1], 123.0),
                        (26.0 + 0.47 * off, -2.0 + 0.99 * off, 121.0), (22.0, pad, 114.4), (19.8, pad, 114.4)]
            else:
                ml = ('ML1', 'ML2', 'ML3')[k]
                sx, sy = SLOT[ml]
                pad = (1.0, 3.2, 5.4)[k]
                rest = [(-72.0 - 0.94 * off, -42.0 + 0.33 * off, -100.0), (-60.0 - 0.76 * off, -8.0 + 0.84 * off, -106.0), (-40.0, -3.0 + off, -109.4),
                        (-9.0, sy, -109.4), (sx, sy, -106.0)] + _tube_run(sx, sy) + [
                        (-10.0, pad, 102.0), (-23.5, pad, 102.6), (-23.5, pad, 112.5), (-21.6, pad, 114.4), (-19.8, pad, 114.4)]
            add(f'{name}_{k + 1}', f'Motor {name}', f'ESC {name[:2]}-Pad {k + 1}', '20AWG', col, start + rest)
    # ---------------------------------------------------------------- Servos
    ends_top = {0: [(44.0, 0.0, 102.5), (36.0, -5.0, 104.4), (30.0, -5.0, 104.4)],
                1: [(-20.0, 35.0, 102.5), (5.0, 30.0, 103.0), (31.5, 24.0, 103.6), (31.5, 12.0, 104.4), (30.0, 11.0, 104.4)],
                2: [(0.0, -42.0, 101.6), (20.0, -30.0, 103.5), (31.5, -24.0, 104.4), (31.5, -9.0, 104.4), (30.0, -9.0, 104.4)]}
    ends_low = {0: [(-54.5, 8.0, -102.0), (-52.0, 10.0, -105.6), (-35.0, 24.0, -105.6), (10.0, 27.0, -105.6), (17.7, 27.0, -107.6)],
                1: [(34.0, 40.0, -104.0), (33.0, 34.0, -105.6), (33.0, 31.3, -107.6)],
                2: [(20.0, -48.0, -104.0), (8.0, -34.0, -105.6), (10.0, -12.0, -105.6), (10.0, 8.0, -105.6), (10.0, 19.0, -105.6), (17.7, 22.0, -107.6)]}
    for sign in (1, -1):
        for j in range(3):
            pts = [servo_world(sign, j, p) for p in SERVO_LOCAL]
            pts += ends_top[j] if sign > 0 else ends_low[j]
            lvl = 'oben' if sign > 0 else 'unten'
            add(f'SERVO_{lvl}_{j + 1}', f'Servo {lvl} {(60, 180, 300)[j]}°',
                'Servoverteiler oben' if sign > 0 else 'Servo-Sammelpunkt unten', 'SERVO3x22AWG', 'braun', pts, adern=3)
    # ---------------------------------------------------------------- Signal und Empfänger
    for k, y in enumerate((7.8, 9.07, 10.34, 11.61, -7.8, -9.07, -10.34)):
        col = 'schwarz' if k == 3 else 'orange'
        add(f'SIG_{k + 1}', 'Servoverteiler oben', 'FC-Pad' + (' GND' if k == 3 else f' Servo {k + 1 if k < 3 else k}'), '28AWG', col,
            [(36.0, y, 103.55), (36.0, y, 108.0), (22.0, y, 126.0), (20.4, y, 130.1), (19.0, y, 130.1)])
    for k, (y, col) in enumerate(((9.0, 'schwarz'), (10.2, 'rot'), (11.4, 'gelb'), (12.6, 'weiss'))):
        add(f'RX_{k + 1}', 'ELRS-Empfänger', 'FC UART', '28AWG', col,
            [(-23.0, y, 102.0), (-21.6, y, 106.0), (-21.6, y, 128.0), (-20.5, y, 130.5), (-19.0, y, 130.5)])
    add('ANT', 'ELRS-Empfänger', 'Antenne', 'ANT', 'schwarz', [(-28.0, 18.0, 103.7), (-33.0, 24.0, 120.0), (-38.0, 28.0, 140.0)])
    return C


def build(cable):
    d, rho = AWG[cable['typ']]
    shape, length = sweep(cable['punkte'], d, cable['biegeradius'])
    return shape, length, length / 1000.0 * rho
