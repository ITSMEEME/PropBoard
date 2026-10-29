"""Einheiten m, s, rad. Geschlossene Ovalbahn in der x-z-Ebene."""
import math


def perimeter(straight, radius):
    return 2 * straight + 2 * math.pi * radius


def state(s, straight, radius, direction=1, pitch_deg=12):
    """Position, Bewegungs-Tangente und Winkel der Profilnase.

    Bahn: obere Gerade nach rechts, rechter Bogen nach unten,
    untere Gerade nach links, linker Bogen nach oben. direction=-1 kehrt
    Bewegung um. Pitch alpha = Amplitude * Tangente_x; kein Optimierungsnachweis.
    """
    s %= perimeter(straight, radius)
    half = straight / 2
    if s < straight:
        x, z, tx, tz = -half+s, radius, 1., 0.
    elif s < straight + math.pi*radius:
        a = math.pi/2 - (s-straight)/radius
        x, z = half+radius*math.cos(a), radius*math.sin(a)
        tx, tz = math.sin(a), -math.cos(a)
    elif s < 2*straight + math.pi*radius:
        x, z = half-(s-straight-math.pi*radius), -radius
        tx, tz = -1., 0.
    else:
        a = -math.pi/2 - (s-2*straight-math.pi*radius)/radius
        x, z = -half+radius*math.cos(a), radius*math.sin(a)
        tx, tz = math.sin(a), -math.cos(a)
    tx, tz = direction*tx, direction*tz
    beta = math.atan2(tz, tx) + math.radians(pitch_deg)*tx
    return x, z, tx, tz, beta


def naca_thickness(x, ratio=.12):
    """Geschlossene NACA-00xx-Kontur, x in [0,1], halbe Dicke / Sehne."""
    return 5*ratio*(.2969*math.sqrt(max(x, 0))-.126*x-.3516*x*x
                    +.2843*x**3-.1036*x**4)
