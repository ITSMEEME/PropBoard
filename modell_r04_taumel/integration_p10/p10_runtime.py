"""P10 Bewegung: P09-Kinematik (Servo → Taumelscheibe → Blatt) plus Planetenstufe.

Hohlrad Z130 dreht mit dem Rotor; die drei Planeten Z20 drehen auf festen Achsen gleichsinnig
mit 6,5-facher Rotordrehzahl. ``planet:l:0`` ist das Motorritzel (Motorwelle), ``planet:l:1/2``
die Stützplaneten. Reine Zwangskinematik, kein Kraft- oder Kontaktlöser.
"""
import math
import sys
from pathlib import Path

import FreeCAD as A

H = Path(__file__).resolve().parent
for p in (H, H.parent / 'bewegung_p09', H.parent / 'bewegung'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import voll_runtime as R  # noqa: E402

M = R.M
V = A.Vector
CENTRE = 54.8
PHI = (330.0, 115.0, 205.0)
RATIO = 6.5


def planet_spin_deg(phi, rotor_deg):
    return -(RATIO - 1.0) * phi + RATIO * rotor_deg


def planet_frame(sign, k, rotor_deg):
    phi = PHI[k]
    a = math.radians(phi)
    return M.local_world(sign).multiply(M.placement((CENTRE * math.cos(a), CENTRE * math.sin(a), 0),
                                                    M.rotz(planet_spin_deg(phi, rotor_deg))))


def state(servos, angles):
    r = R.state(servos, angles)
    for l, sign in ((0, 1), (1, -1)):
        r['frames'].pop(f'pinion:{l}', None)
        for k in range(3):
            r['frames'][f'planet:{l}:{k}'] = planet_frame(sign, k, angles[l])
    return r


def apply(doc, servos, angles, recompute=True):
    current = state(servos, angles)
    if recompute:
        ctl = doc.getObject('P09_Animation')
        if ctl is not None:
            ctl.Modus = 'Manuell'
            ctl.Servo_deg = list(servos)
            ctl.Rotor_deg = list(angles)
    for o in doc.Objects:
        if not hasattr(o, 'P09_Rahmen') or o.P09_Rahmen == 'fixed':
            continue
        o.Placement = current['frames'][o.P09_Rahmen].multiply(o.P09_Neutralrahmen.inverse())
    if recompute:
        doc.recompute()
    return current


demo = R.demo


class Controller:
    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, obj):
        if obj.Modus == 'Demo':
            servos, angles = demo(obj.Zeit_s)
        else:
            servos, angles = list(obj.Servo_deg), list(obj.Rotor_deg)
        try:
            r = apply(obj.Document, servos, angles, False)
            obj.Gelenkfehler_mm = r['max_error']
            obj.Blattpitch_deg = [x for v in r['pitches'] for x in v]
            obj.Status = 'P10: Kinematik geschlossen inkl. Planetenstufe; keine Fertigungs-/Flugfreigabe'
        except ValueError as e:
            obj.Status = 'Stellung verworfen: ' + str(e)

    def onChanged(self, obj, prop):
        pass

    def dumps(self):
        return None

    def loads(self, state):
        pass
