"""Anordnungsstudie: mehr Seitensteifigkeit nur durch andere Lage der vorhandenen Rohre?

Fuer 2 bzw. 3 Rohre (Material wie V2 bzw. V3) werden alle Zuordnungen der Rohrwurzeln zu den vorhandenen
Anschlusspunkten bewertet:
  W+  Dreiecksverbinder oben (z +110)   W0  Dreiecksverbinder Mitte (z 0)   W-  Dreiecksverbinder unten (z -110)
  E+  benachbarter Rahmeneckknoten oben  E-  Rahmeneckknoten unten
Alle Rohre enden wie in D14 im Systempunkt I auf der Motorachse. Jedes Rohr ist ein Balken: axial EA/L, quer 3EI/L^3
(eingespannt-frei). Daraus 3x3-Steifigkeit am Auslegerende, Eigenfrequenzen (Ein-Massen-Schwinger), Stabkraefte im
Lastfall 3 g, Knicken (Abminderung 1,5) und Abstand zum Nachbarausleger. Ergebnis: Ausgabe/Rohrstudie/Anordnung.json
"""
import json, math, itertools
from pathlib import Path
import numpy as np
import auslegung as AL
import rohrstudie as RS

H = Path(__file__).resolve().parent
P = AL.P
PUNKTE = ['W+', 'W0', 'W-', 'E+', 'E-']


def punkte(g):
    W = np.array(g['W']); Vp = np.array(g['Vp']); z = P['rahmen']['ebene_z_mm']
    return {'W+': W + [0, 0, z], 'W0': W.copy(), 'W-': W - [0, 0, z], 'E+': Vp + [0, 0, z], 'E-': Vp - [0, 0, z]}


def seg_abstand(a, b, c, d, n=40, t0=0.12):
    """Abstand zweier Rohrachsen ausserhalb des Wurzelbereichs (gemeinsamer Verbinderpunkt W ist gewollt)."""
    best = 1e9
    for i in range(n + 1):
        p = a + (b - a) * (t0 + (1 - t0) * i / n)
        t = np.clip(np.dot(p - c, d - c) / np.dot(d - c, d - c), t0, 1); best = min(best, np.linalg.norm(p - (c + (d - c) * t)))
    return best


def bewerte(bw, prop, wurzeln, od=20, di=17):
    vbas = 'V3' if len(wurzeln) == 3 else 'V2'
    key = f'{bw}_{prop["id"]}_{vbas}'; c = RS.AUS[key]; sim = RS.SIM[key]
    g = RS.arm_fuer(bw, prop, vbas, c['motorradius_mm'], od, di)
    pk = punkte(g); I_ = np.array(g['I']); u = np.array(g['u']); lat = np.cross([0, 0, 1.0], u)
    A, Iq, Wb = RS.querschnitt(od, di); E = RS.E_CFK; hu = g['huelse']
    K = np.zeros((3, 3)); st = []
    for w in wurzeln:
        d = pk[w] - I_; L = np.linalg.norm(d); e = d / L
        K += E * A / L * np.outer(e, e) + 3 * E * Iq / L ** 3 * (np.eye(3) - np.outer(e, e)); st.append((w, e, L))
    npos = P['bauweisen'][bw]['rotorpositionen']; koax = bw == 'KOAX'
    masse = max(RS.LA['gesamtmasse_kg'], sim['masse_kg']); F = masse * RS.G0 * RS.LF / npos
    Kinv = np.linalg.inv(K); uF = Kinv @ np.array([0, 0, F])
    sig = 0.0; knick = 0.0; m_rohre = 0.0
    for w, e, L in st:
        N = -E * A / L * float(e @ uF); sig = max(sig, abs(N) / A); m_rohre += A * L * RS.RHO_CFK
        Lf = L - g['d0'] - g['ce'] - 2 * hu['L']; Pcr = math.pi ** 2 * E * Iq / Lf ** 2; knick = max(knick, max(0.0, -N) * RS.GAMMA_KNICK / Pcr)
    m_spitze = (2 if koax else 1) * (RS.M_MOTOR + 0.56 * (prop['d_mm'] / 1066.8) ** 2.5) + RS.PRU[key]['massen']['motortraeger_je_stueck_kg'] + 0.3
    m = (m_spitze + 0.24 * m_rohre) / 1000.0                     # kg -> fuer N/mm: f = sqrt(k[N/mm]*1000/m[kg])
    ev, vecs = np.linalg.eigh(K)
    fr = [math.sqrt(max(x, 0) / m) / (2 * math.pi) for x in ev]
    f_vert = math.sqrt(1.0 / Kinv[2, 2] / m) / (2 * math.pi); f_lat = math.sqrt(1.0 / float(lat @ Kinv @ lat) / m) / (2 * math.pi)
    # Abstand zum gespiegelten Nachbarausleger (rechter Arm desselben Paars) und Rotor-/Rahmenkonflikte grob
    spiegel = lambda p: p * [1, -1, 1]
    abst = min(seg_abstand(pk[a], I_, spiegel(pk[b]), spiegel(I_)) for a in wurzeln for b in wurzeln)
    sig_lat = (RS.Q_MOTOR_MAX * 1000) / (len(wurzeln) * Wb)
    frei = None
    if sim['schwebefaehig']:
        n_max = sim['schwebe_rpm'] * math.sqrt(max(sim['schub_gewicht'], 1.0)); n_lo = 0.85 * sim['schwebe_rpm']
        baender = [(n_lo / 60, n_max / 60), (2 * n_lo / 60, 2 * n_max / 60)]
        frei = not any(b[0] * 0.85 <= f <= b[1] * 1.15 for f in (f_vert, f_lat) for b in baender)
    return dict(bauweise=bw, propeller=prop['id'], rohr=f'{od}/{di}', anordnung='+'.join(wurzeln), rohre=len(wurzeln),
                f_min_Hz=round(fr[0], 1), f_vertikal_Hz=round(f_vert, 1), f_seitlich_Hz=round(f_lat, 1),
                ausnutzung=round((sig + sig_lat) / RS.SIG_ZUL, 3), knick_ausnutzung=round(knick, 3),
                masse_rohre_kg=round(m_rohre, 3), abstand_nachbararm_mm=round(abst - od, 1), resonanzfrei=frei, schwebefaehig=sim['schwebefaehig'],
                ok=bool(fr[0] >= RS.F_MIN and knick <= 1 and (sig + sig_lat) <= RS.SIG_ZUL and abst - od > 10 and frei is not False))


def main():
    props = [p for p in P['propeller'] if p['id'] in ('HEP_S_34_11p5', 'HEP_S_36_12', 'HEP_S_42_16')]
    rows = []
    for bw in P['bauweisen']:
        for prop in props:
            for n in (2, 3):
                for comb in itertools.combinations(PUNKTE, n):
                    rows.append(bewerte(bw, prop, list(comb)))
    (H / 'Ausgabe/Rohrstudie/Anordnung.json').write_text(json.dumps(dict(
        annahmen='Rohr 20/17, Balkenmodell je Rohr (axial + Querbiegung eingespannt-frei), Ein-Massen-Schwinger am Auslegerende, Lastfall 3 g, Knicken mit Abminderung 1,5, Mindestfrequenz 15 Hz',
        ergebnisse=rows), ensure_ascii=False, indent=1))
    return rows


if __name__ == '__main__':
    rows = main()
    for bw in P['bauweisen']:
        print('\n' + bw + ' 42″ / 36″')
        for p in ('HEP_S_42_16', 'HEP_S_36_12'):
            rs = sorted([r for r in rows if r['bauweise'] == bw and r['propeller'] == p], key=lambda r: -r['f_min_Hz'])
            zwei = [r for r in rs if r['rohre'] == 2][:1]
            for r in rs[:3] + zwei + [r for r in rs if r['anordnung'] in ('W+_W-'.replace('_', '+'), 'W+_W0_W-'.replace('_', '+'))]:
                print(f"  {p[6:]:6} {r['anordnung']:10} fmin {r['f_min_Hz']:5} fv {r['f_vertikal_Hz']:5} fl {r['f_seitlich_Hz']:5} sig {r['ausnutzung']:.2f} knick {r['knick_ausnutzung']:.2f} m {r['masse_rohre_kg']:.2f} abst {r['abstand_nachbararm_mm']:6} res {r['resonanzfrei']} {'OK' if r['ok'] else ''}")
