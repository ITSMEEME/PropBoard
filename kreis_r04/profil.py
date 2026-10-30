"""REKONSTRUKTION (2026-10-30): gemeinsame Profil- und Kreisbahndefinition fuer R04-CAD und -CFD.

NACA 0012 (geschlossene Form, Koeffizient -0.1036) plus zusaetzliche halbe Dicke
0.4*q**10 mm je Seite -> endliche Hinterkantendicke 0.8 mm. Millimeter.
"""
import math

RADIUS = 450.0                 # Kreisbahn-Mittelradius
LEVELS = (-120.0, 120.0)       # Ebenen z
WINGS_PER_LEVEL = 8
CHORD = 120.0
SPAN = 600.0
R_WING = (RADIUS - SPAN/2, RADIUS + SPAN/2)   # 150 .. 750
R_GUIDE = (130.0, 770.0)       # innere/aeussere Fuehrungsbahn
PITCH_DEG = 12.0
TE_HALF_EXTRA = 0.4            # mm je Seite bei q = 1
AXIS_Q = 0.5                   # Pitchachse bei 50 % Sehne wie R02


def naca_half(q, ratio=.12):
    q = min(max(q, 0.), 1.)
    return 5*ratio*(.2969*math.sqrt(q)-.126*q-.3516*q*q+.2843*q**3-.1036*q**4)


def half_thickness_mm(q):
    return naca_half(q)*CHORD + TE_HALF_EXTRA*min(max(q, 0.), 1.)**10


def cosine_q(n):
    return [(1-math.cos(math.pi*i/n))/2 for i in range(n+1)]


def outline(n=50):
    """Geschlossene Aussenkontur (x_sehne, z) in mm, Pitchachse im Ursprung, Nase bei +x.

    Oberseite Nase->Hinterkante, dann Unterseite Hinterkante->Nase. Die Hinterkante
    ist eine gerade Kante der Dicke 0.8 mm; der Nasenpunkt kommt nur einmal vor.
    """
    qs = cosine_q(n)
    upper = [((AXIS_Q-q)*CHORD, half_thickness_mm(q)) for q in qs]
    lower = [((AXIS_Q-q)*CHORD, -half_thickness_mm(q)) for q in reversed(qs[1:])]
    return upper+lower


def inner_outline_r02(n=50):
    """Unveraenderte R02-Innenkontur der Hohlschale (skaliert, scharf); nicht neu ausgelegt."""
    xx = cosine_q(n); pts = []
    for sign, seq in ((1, xx), (-1, xx[-2:0:-1])):
        for q in seq:
            pts.append(((AXIS_Q-(.04+.92*q))*CHORD, sign*naca_half(q)*.70*CHORD))
    return pts


def polygon_area(pts):
    return abs(sum(x0*z1-x1*z0 for (x0, z0), (x1, z1) in zip(pts, pts[1:]+pts[:1])))/2


def shell_area_mm2(n=50):
    return polygon_area(outline(n))-polygon_area(inner_outline_r02(n))


def omega(u_ref):
    """Winkelgeschwindigkeit [rad/s] aus Umlaufgeschwindigkeit [m/s] bei Radius 450 mm."""
    return u_ref/(RADIUS/1000)


if __name__ == '__main__':
    print('Hinterkantendicke mm', 2*half_thickness_mm(1.0))
    print('Schalenquerschnitt mm2 (Polygon n=50)', round(shell_area_mm2(), 2))
