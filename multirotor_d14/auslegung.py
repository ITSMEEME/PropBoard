"""D14 Auslegung: Bauweisen QUAD/HEXA/OKTO/KOAX, Paarausleger mit Dreiecksverbinder.

Reine Python-Geometrie (kein FreeCAD). Liefert fuer jede Kombination aus Bauweise,
Propeller und Rohrvariante alle Systemlinien, Huelsenlagen, Freiraeume und ein
Stabwerks-Screening. bauen.py erzeugt daraus die Volumenkoerper.

Koordinaten: x vorne, z oben, Ursprung Rahmenmitte. "Paarsystem": das betrachtete
Auslegerpaar liegt symmetrisch zur +x-Achse; der linke Ausleger (Motor bei +delta)
ist Master, der rechte ist sein Spiegelbild an y = 0.
"""
from pathlib import Path
import json
import math

H = Path(__file__).resolve().parent
P = json.loads((H / 'parameter.json').read_text())


# ----------------------------------------------------------------- Vektoren
def add(a, b): return [x + y for x, y in zip(a, b)]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def mul(a, k): return [x * k for x in a]
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def norm(a): return math.sqrt(dot(a, a))
def unit(a):
    n = norm(a)
    return [x / n for x in a]
def rotz(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [c * p[0] - s * p[1], s * p[0] + c * p[1]] + list(p[2:])
def mirror_y(p): return [p[0], -p[1]] + list(p[2:])
def r3(p): return [round(x, 4) for x in p]


def seg_point_dist2d(p, a, b):
    ab = sub(b[:2], a[:2]); ap = sub(p[:2], a[:2])
    t = max(0.0, min(1.0, dot(ap, ab) / dot(ab, ab)))
    return norm(sub(ap, mul(ab, t)))


# ------------------------------------------------------------ Grundgroessen
def overrides(bw, prop=None, vid=None):
    """Konfigurationsspezifische Abweichungen (parameter.json 'konfig_overrides', Schluessel BW_PROP_VARIANTE)."""
    if prop is None or vid is None:
        return {}
    pid = prop['id'] if isinstance(prop, dict) else prop
    return P.get('konfig_overrides', {}).get(f'{bw}_{pid}_{vid}', {})


def variante(bw, prop, vid):
    """Rohrvariante inkl. Overrides (Rohrgroesse, E-Modul)."""
    v = dict(P['varianten'][vid]); o = overrides(bw, prop, vid)
    for k in ('rohr_od_mm', 'rohr_id_mm', 'cfk_e_modul_mpa', 'rohr_material'):
        if k in o: v[k] = o[k]
    v.setdefault('cfk_e_modul_mpa', P['lasten']['cfk_e_modul_mpa'])
    return v


def rahmen(bw, prop=None, vid=None):
    b = P['bauweisen'][bw]
    paare = b['rotorpositionen'] // 2
    nf = 2 * paare
    s = overrides(bw, prop, vid).get('rahmen_seitenlaenge_mm', P['rahmen']['seitenlaenge_mm'])
    a = s / (2 * math.tan(math.pi / nf))
    rho = s / (2 * math.sin(math.pi / nf))
    return dict(paare=paare, seiten=nf, seitenlaenge=s, apothem=a, umkreis=rho,
                ebene=P['rahmen']['ebene_z_mm'])


def huelse(v):
    """Socket-Masse fuer eine Rohrvariante."""
    hu = P['huelse']
    od = v['rohr_od_mm']; di = v['rohr_id_mm']
    bohr = od + 2 * hu['passspalt_radial_mm']
    return dict(od=od, id=di, r_bohr=bohr / 2, r_aussen=bohr / 2 + hu['wand_mm'],
                r_kammer=di / 2, L=hu['laenge_mm'], L_starr=hu['starrer_teil_mm'],
                kammer=hu['kabelkammer_mm'])


def eckpunkte(rf):
    """Rahmenecken im Paarsystem (Paar 0 schaut nach +x)."""
    out = []
    for i in range(rf['seiten']):
        ang = 180.0 / rf['seiten'] + i * 360.0 / rf['seiten']
        out.append([rf['umkreis'] * math.cos(math.radians(ang)), rf['umkreis'] * math.sin(math.radians(ang))])
    return out


# ------------------------------------------------------------ Armgeometrie
def arm(bw, prop, vid, R):
    """Systemlinien und Knotenpunkte des linken Auslegers im Paarsystem."""
    rf = rahmen(bw, prop, vid)
    v = variante(bw, prop, vid) if vid in P['varianten'] else P['varianten'][vid]
    hu = huelse(v)
    dv = P['dreiecksverbinder']; mt = P['motortraeger']
    npos = P['bauweisen'][bw]['rotorpositionen']
    delta = 180.0 / npos
    W = [rf['apothem'] + dv['arbeitspunkt_abstand_aussen_mm'], 0.0, 0.0]
    M = [R * math.cos(math.radians(delta)), R * math.sin(math.radians(delta)), 0.0]
    u = unit([M[0] - W[0], M[1] - W[1], 0.0])
    Lr = norm(sub(M[:2], W[:2]))
    gamma = math.degrees(math.atan2(u[1], u[0]))
    zI = mt['systempunkt_z_mm']
    I = [M[0], M[1], zI]
    Vp = [rf['apothem'], rf['seitenlaenge'] / 2, 0.0]
    eck_z = v.get('eck_z_mm', [])
    roots = [[W[0], W[1], z] for z in v['wurzel_z_mm']]
    n = len(roots) + len(eck_z)
    # Wurzelabstand: Bohrungen links/rechts duerfen sich nicht schneiden.
    d0 = max(dv['min_wurzel_abstand_mm'], (hu['r_bohr'] + 2.0) / math.sin(math.radians(gamma)))
    # Motorseitiger Kragabstand c_e: benachbarte Huelsen brauchen den Mittenabstand.
    if n == 1:
        ce = mt['einrohr_kragabstand_mm']
    elif not eck_z:
        dz = abs(v['wurzel_z_mm'][0] - v['wurzel_z_mm'][1])
        th = max(abs(math.atan2(zI - z, Lr)) for z in v['wurzel_z_mm'])
        ce = math.ceil(mt['huelsen_mittenabstand_mm'] * Lr / (dz * math.cos(th)))
    else:
        # Raumfachwerk: Achsabstand zweier Rohre im Grundrissabstand s vor I waechst mit s * |r_i/L_i - r_j/L_j|
        alle = roots + [[Vp[0], Vp[1], z] for z in eck_z]
        rel = [mul(sub(r, I), 1.0 / math.hypot(r[0] - I[0], r[1] - I[1])) for r in alle]
        kmin = min(norm(sub(a, b)) for i, a in enumerate(rel) for b in rel[i + 1:])
        ce = math.ceil(mt['huelsen_mittenabstand_mm'] / kmin)
    ce = max(ce, hu['kammer'] + 20.0)

    def at(k, s):
        return add(roots[k], mul(sub(I, roots[k]), s / Lr))
    rohre = []
    for k in range(len(roots)):
        e = unit(sub(I, roots[k]))
        T = at(k, d0); Q = at(k, Lr - ce)
        Lsys = norm(sub(I, roots[k]))
        rohre.append(dict(index=k, wurzel=r3(roots[k]), systempunkt=r3(I), e=r3(e), T=r3(T), Q=r3(Q), anschluss='verbinder',
                          laenge_mm=round(norm(sub(Q, T)), 2), systemlaenge_mm=round(Lsys, 2),
                          neigung_grad=round(math.degrees(math.asin(e[2])), 3)))
    # Gurte zum benachbarten Rahmeneckknoten (V4): Huelse im Eckknoten, Anschlag nach der Eckknoten-Regel
    eck_rohre = {}
    if eck_z:
        ra = P['rahmen']; an0 = ra['eckknoten_rohranschlag_mm']
        r_bohr_r = ra['rohr_od_mm'] / 2 + P['huelse']['passspalt_radial_mm']
        nf = rf['seiten']; ang = math.radians(360.0 / nf)
        V2 = [Vp[0] * math.cos(ang) - Vp[1] * math.sin(ang), Vp[0] * math.sin(ang) + Vp[1] * math.cos(ang), 0.0]
        rahmen_dirs = [[0.0, -1.0, 0.0], unit(sub(V2, Vp)), [0.0, 0.0, -1.0]]   # lokales System des oberen Eckknotens
        for z in eck_z:
            root = [Vp[0], Vp[1], z]; e = unit(sub(I, root)); k = len(rohre)
            d_lok = [e[0], e[1], e[2] if z > 0 else -e[2]]          # unterer Knoten wird lokal oben gebaut und gespiegelt
            an = an0
            for o in rahmen_dirs:
                w = math.degrees(math.acos(max(-1.0, min(1.0, dot(d_lok, o)))))
                if w < 89.0:
                    an = max(an, (r_bohr_r + hu['r_bohr'] + 2.5) / math.sin(math.radians(w)))
            T = add(root, mul(e, an))
            Lp = math.hypot(root[0] - I[0], root[1] - I[1])
            Q = add(I, mul(sub(root, I), ce / Lp))
            lage = 'ecke_oben' if z > 0 else 'ecke_unten'
            eck_rohre[lage] = dict(d_lokal=r3(d_lok), anschlag_mm=round(an, 3))
            rohre.append(dict(index=k, wurzel=r3(root), systempunkt=r3(I), e=r3(e), T=r3(T), Q=r3(Q), anschluss=lage,
                              laenge_mm=round(norm(sub(Q, T)), 2), systemlaenge_mm=round(norm(sub(I, root)), 2),
                              neigung_grad=round(math.degrees(math.asin(e[2])), 3)))
    # Dreiecksplatten: Eckpunkte (Laschenbohrungen B) und Huelsenenden (A)
    ve = unit([W[0] - Vp[0], W[1] - Vp[1], 0.0])
    B = add(Vp, mul(ve, dv['lasche_bohrung_abstand_ecke_mm']))
    A = add(W, mul(u, d0 + hu['L_starr']))
    return dict(W=r3(W), M=r3(M), u=r3(u), Lr=round(Lr, 3), gamma_grad=round(gamma, 3), I=r3(I),
                d0=round(d0, 3), ce=round(ce, 3), rohre=rohre, eck_rohre=eck_rohre, A=r3(A), B=r3(B), Vp=r3(Vp), ve=r3(ve),
                huelse=hu, delta_grad=delta, e_modul=v.get('cfk_e_modul_mpa', P['lasten']['cfk_e_modul_mpa']),
                rohr_material=v.get('rohr_material', 'CFK gewickelt (E 50 GPa, Annahme D14)'))


def motorradius(bw, prop):
    b = P['bauweisen'][bw]
    if bw in ('QUAD', 'KOAX'):
        return prop['quad_half_spacing_mm'] * math.sqrt(2.0), 'D10/D13-Quadabstand'
    rt = P['rotor']
    npos = b['rotorpositionen']
    D = prop['d_mm']
    R = D * (1 + rt['min_spitzenabstand_anteil_d']) / (2 * math.sin(math.pi / npos))
    R = math.ceil(R / 5.0) * 5.0
    quelle = 'Blattspitzenabstand'
    while min(grundriss_freiraum(bw, prop, v, R) for v in P['varianten']) < rt['min_freiraum_grundriss_mm']:
        R += 5.0; quelle = 'Rahmen-/Verbinderfreiraum'
    return R, quelle


def struktur_grundriss(bw, prop, vid, R):
    """Punkte/Radien der Rahmen- und Verbinderstruktur aller Paare (global)."""
    rf = rahmen(bw, prop, vid); g = arm(bw, prop, vid, R)
    pts = []
    paarwinkel = [j * 360.0 / rf['paare'] for j in range(rf['paare'])]
    for V in eckpunkte(rf):
        pts.append((V, P['rahmen']['eckknoten_kugel_r_mm'] + P['rahmen']['eckknoten_rohranschlag_mm'] + 10))
    for phi in paarwinkel:
        for spiegel in (False, True):
            for q, r in [(g['W'], 30.0), (g['A'], g['huelse']['r_aussen'] + 12), (g['B'], 26.0)]:
                p = mirror_y(q) if spiegel else q
                pts.append((rotz(p, phi), r))
    return pts


def grundriss_freiraum(bw, prop, vid, R):
    rf = rahmen(bw, prop, vid)
    npos = P['bauweisen'][bw]['rotorpositionen']
    pts = struktur_grundriss(bw, prop, vid, R)
    best = 1e9
    for i in range(npos):
        ang = 180.0 / npos + i * 360.0 / npos
        m = [R * math.cos(math.radians(ang)), R * math.sin(math.radians(ang))]
        for p, r in pts:
            best = min(best, norm(sub(p[:2], m)) - r - prop['d_mm'] / 2)
    return best


def alle_rohre_global(bw, g):
    rf = rahmen(bw); out = []
    for j in range(rf['paare']):
        phi = j * 360.0 / rf['paare']
        for spiegel in (False, True):
            for t in g['rohre']:
                a, b = t['T'], t['Q']
                if spiegel: a, b = mirror_y(a), mirror_y(b)
                out.append((rotz(a, phi), rotz(b, phi)))
    return out


def motoren_global(bw, R):
    npos = P['bauweisen'][bw]['rotorpositionen']
    out = []
    for i in range(npos):
        # M1 = rechter Motor von Paar 0 (Winkel -delta), danach gegen den Uhrzeigersinn
        ang = -180.0 / npos + i * 360.0 / npos
        out.append(dict(nr=i + 1, winkel_grad=round(ang % 360, 3), drehrichtung='CCW' if i % 2 == 0 else 'CW',
                        xy=[round(R * math.cos(math.radians(ang)), 3), round(R * math.sin(math.radians(ang)), 3)],
                        paar=(i // 2) + 1 if True else None))
    # Paare: (M1,M2) Paar 0, (M3,M4) Paar 1, ...
    return out


def z_min_im_kreis(rohre, center, radius, r_aussen, samples=200):
    zmin = 1e9; zmax = -1e9
    for a, b in rohre:
        for i in range(samples + 1):
            p = add(a, mul(sub(b, a), i / samples))
            if norm(sub(p[:2], center)) <= radius:
                zmin = min(zmin, p[2] - r_aussen); zmax = max(zmax, p[2] + r_aussen)
    return zmin, zmax


# ---------------------------------------------------------------- Statik
def stabwerk(bw, g, vid):
    la = P['lasten']; v = P['varianten'][vid]
    npos = P['bauweisen'][bw]['rotorpositionen']
    Fz = la['gesamtmasse_kg'] * la['g_m_s2'] * la['lastfaktor'] / npos
    od, di = g['huelse']['od'], g['huelse']['id']
    A = math.pi / 4 * (od ** 2 - di ** 2)
    Iq = math.pi / 64 * (od ** 4 - di ** 4)
    E = g.get('e_modul', la['cfk_e_modul_mpa'])
    res = dict(schub_je_ausleger_N=round(Fz, 1), lastfall='Schweben x Lastfaktor, Schub vertikal in der Motorachse')
    mt = P['motortraeger']
    if g.get('eck_rohre'):
        return stabwerk_raum(g, Fz, res, A, Iq, E, la, mt, v)
    if len(g['rohre']) == 1:
        M = Fz * g['Lr']
        Wb = math.pi * (od ** 4 - di ** 4) / (32 * od)
        s = M / Wb
        res.update(modell='Kragarm (Biegung)', wurzelmoment_Nm=round(M / 1000, 1), biegespannung_MPa=round(s, 1),
                   ausnutzung=round(s / la['cfk_zulaessig_mpa'], 3))
        res['bestanden'] = res['ausnutzung'] <= 1.0
        return res
    # 2D-Stabwerk in der Auslegerebene (s, z), Knoten I, Gelenkstaebe zu den Wurzeln
    K = [[0.0, 0.0], [0.0, 0.0]]
    stabs = []
    for t in g['rohre']:
        d3 = sub(t['wurzel'], t['systempunkt'])
        L = norm(d3)
        d = [math.hypot(d3[0], d3[1]) * (-1.0), d3[2]]  # s-Achse zeigt zur Motorachse
        d = [d[0] / L, d[1] / L]
        k = E * A / L
        for i in range(2):
            for j in range(2): K[i][j] += k * d[i] * d[j]
        stabs.append((t, d, k, L))
    det = K[0][0] * K[1][1] - K[0][1] * K[1][0]
    F = [0.0, Fz]
    u = [(K[1][1] * F[0] - K[0][1] * F[1]) / det, (-K[1][0] * F[0] + K[0][0] * F[1]) / det]
    rows = []
    ok = True
    hu = g['huelse']
    for t, d, k, L in stabs:
        N = -k * (d[0] * u[0] + d[1] * u[1])  # Zug positiv
        sig = N / A
        Lfrei = t['laenge_mm'] - 2 * hu['L']
        Pcr = math.pi ** 2 * E * Iq / (la['knickfaktor_k'] * Lfrei) ** 2
        Ls = norm(sub(t['systempunkt'], t['Q'])) - hu['kammer']
        ds = mt['strebe_d_mm']
        As = math.pi / 4 * ds ** 2; Is = math.pi * ds ** 4 / 64
        Pcr_s = math.pi ** 2 * la['alu_e_modul_mpa'] * Is / Ls ** 2
        r = dict(rohr=t['index'], wurzel_z_mm=t['wurzel'][2], stabkraft_N=round(N, 1),
                 cfk_spannung_MPa=round(sig, 1), cfk_ausnutzung=round(abs(sig) / la['cfk_zulaessig_mpa'], 3),
                 freie_knicklaenge_mm=round(Lfrei, 1), euler_knicklast_N=round(Pcr, 1),
                 knick_ausnutzung=round(max(0.0, -N) / Pcr, 3),
                 alu_strebe_laenge_mm=round(Ls, 1), alu_strebe_spannung_MPa=round(N / As, 1),
                 alu_strebe_knick_ausnutzung=round(max(0.0, -N) / Pcr_s, 3))
        r['bestanden'] = r['cfk_ausnutzung'] <= 1 and r['knick_ausnutzung'] <= 1 and \
            abs(N / As) <= la['alu_zulaessig_mpa'] and r['alu_strebe_knick_ausnutzung'] <= 1
        ok = ok and r['bestanden']
        rows.append(r)
    res.update(modell='zentrisches Gelenkstabwerk (Systemlinien schneiden sich auf der Motorachse)',
               verschiebung_systempunkt_mm=[round(x, 3) for x in u], staebe=rows, bestanden=ok)
    # Kraefte, die ein Ausleger am Dreiecksverbinder abgibt (Paarsystem, linker Arm)
    res['wurzelkraefte_N'] = []
    for (t, d, k, L), r in zip(stabs, rows):
        e = unit(sub(t['systempunkt'], t['wurzel']))
        res['wurzelkraefte_N'].append(r3(mul(e, r['stabkraft_N'])))
    return res


def _k_rohr(t, E, A, Iq):
    """Steifigkeit eines Rohrs am Systempunkt: axial EA/L, quer 3EI/L^3 (eingespannt-frei)."""
    d = sub(t['wurzel'], t['systempunkt']); L = norm(d); e = [x / L for x in d]
    ka = E * A / L; kq = 3 * E * Iq / L ** 3
    return [[ka * e[i] * e[j] + kq * ((1.0 if i == j else 0.0) - e[i] * e[j]) for j in range(3)] for i in range(3)], e, L


def _loese3(K, F):
    import numpy as np
    return [float(x) for x in np.linalg.solve(np.array(K), np.array(F))]


def stabwerk_raum(g, Fz, res, A, Iq, E, la, mt, v):
    """Raumfachwerk (V4): Balkenmodell aller Rohre am gemeinsamen Systempunkt I."""
    K = [[0.0] * 3 for _ in range(3)]; st = []
    for t in g['rohre']:
        k, e, L = _k_rohr(t, E, A, Iq)
        for i in range(3):
            for j in range(3): K[i][j] += k[i][j]
        st.append((t, e, L))
    u = _loese3(K, [0.0, 0.0, Fz])
    rows = []; ok = True; hu = g['huelse']
    for t, e, L in st:
        N = -E * A / L * dot(e, u)                           # Zug positiv
        sig = N / A
        Lfrei = t['laenge_mm'] - 2 * hu['L']
        Pcr = math.pi ** 2 * E * Iq / (la['knickfaktor_k'] * Lfrei) ** 2
        Ls = norm(sub(t['systempunkt'], t['Q'])) - hu['kammer']
        ds = mt['strebe_d_mm']; As = math.pi / 4 * ds ** 2; Is = math.pi * ds ** 4 / 64
        Pcr_s = math.pi ** 2 * la['alu_e_modul_mpa'] * Is / Ls ** 2
        r = dict(rohr=t['index'], anschluss=t['anschluss'], wurzel_z_mm=t['wurzel'][2], stabkraft_N=round(N, 1),
                 cfk_spannung_MPa=round(sig, 1), cfk_ausnutzung=round(abs(sig) / la['cfk_zulaessig_mpa'], 3),
                 freie_knicklaenge_mm=round(Lfrei, 1), euler_knicklast_N=round(Pcr, 1), knick_ausnutzung=round(max(0.0, -N) / Pcr, 3),
                 alu_strebe_laenge_mm=round(Ls, 1), alu_strebe_spannung_MPa=round(N / As, 1),
                 alu_strebe_knick_ausnutzung=round(max(0.0, -N) / Pcr_s, 3))
        r['bestanden'] = r['cfk_ausnutzung'] <= 1 and r['knick_ausnutzung'] <= 1 and abs(N / As) <= la['alu_zulaessig_mpa'] and r['alu_strebe_knick_ausnutzung'] <= 1
        ok = ok and r['bestanden']; rows.append(r)
    res.update(modell='Raumfachwerk (Balkenmodell, Systemlinien schneiden sich auf der Motorachse)',
               verschiebung_systempunkt_mm=[round(x, 3) for x in u], staebe=rows, bestanden=ok)
    res['wurzelkraefte_N'] = [r3(mul(unit(sub(t['systempunkt'], t['wurzel'])), r['stabkraft_N'])) for (t, e, L), r in zip(st, rows)]
    return res


def dynamik(bw, prop, g, vid):
    """Erste Eigenfrequenzen des Auslegers (Ein-Massen-Schwinger am Systempunkt, Balkenmodell aller Rohre)."""
    import numpy as np
    la = P['lasten']
    od, di = g['huelse']['od'], g['huelse']['id']; A = math.pi / 4 * (od ** 2 - di ** 2); Iq = math.pi / 64 * (od ** 4 - di ** 4); E = g.get('e_modul', la['cfk_e_modul_mpa'])
    K = np.zeros((3, 3)); m_rohre = 0.0
    for t in g['rohre']:
        k, e, L = _k_rohr(t, E, A, Iq); K += np.array(k); m_rohre += A * L * 1.55e-6
    koax = P['bauweisen'][bw]['motoren_je_position'] == 2
    m = (2 if koax else 1) * (2.75 + 0.56 * (prop['d_mm'] / 1066.8) ** 2.5) + (1.0 if koax else 0.6) + 0.3 + 0.24 * m_rohre
    Ki = np.linalg.inv(K); u = np.array(g['u']); lat = np.cross([0, 0, 1.0], u)
    f = lambda k: math.sqrt(max(k, 0) * 1000 / m) / (2 * math.pi)
    return dict(f_vertikal_Hz=round(f(1 / Ki[2, 2]), 1), f_seitlich_Hz=round(f(1 / float(lat @ Ki @ lat)), 1),
                f_min_Hz=round(f(float(np.linalg.eigvalsh(K)[0])), 1), endmasse_kg=round(m, 2),
                modell='Balkenmodell (axial EA/L, quer 3EI/L^3) am Systempunkt, Endmasse Motor+Propeller+Motortraeger+Regleranteil; Anhalt, keine FE-Modalanalyse')


# ------------------------------------------------------- Ausruestung
def _abstand_polygon(p, poly):
    """Grundrissabstand Punkt-Polygon (0, wenn innen)."""
    inn = False; best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            inn = not inn
        best = min(best, seg_point_dist2d(p, a, b))
    return 0.0 if inn else best


def ausruestungsecken(rf, fuer='landung'):
    """Vier Ecken (+-cx, +-cy). Landung: groesstes |y| (breite Spur); Fussschlitten: kleinstes |y|
    (Ecke nahe der Schiene, Stuetzen kreuzen die Indexierleisten nicht)."""
    cand = [v for v in eckpunkte(rf) if v[1] > 1e-6 and abs(v[0]) > 1e-6]
    yw = max(v[1] for v in cand) if fuer == 'landung' else min(v[1] for v in cand)
    cx = min(abs(v[0]) for v in cand if abs(v[1] - yw) < 1e-6)
    return round(cx, 6), round(yw, 6)


def sattel_x(rf, g, cx, cy):
    """Grundrisslage des Schienensattels: ueber der Ecke; bei grossen Rahmen nach innen versetzt, bis die Stuetze
    (Eckknoten -> Sattel) im Hoehenbereich der Dreiecksverbinderplatten mindestens Plattenrand + Huelsenradius + 3 mm
    Abstand zur Plattenkontur hat."""
    dv = P['dreiecksverbinder']; lv = P['rahmen']['ebene_z_mm']; fs = P['fussschlitten']
    A_, B_ = g['A'], g['B']; poly0 = [B_[:2], A_[:2], [A_[0], -A_[1]], [B_[0], -B_[1]]]
    polys = [[rotz(q + [0.0], j * 360.0 / rf['paare'])[:2] for q in poly0] for j in range(rf['paare'])]
    r_h = P['rahmen']['rohr_od_mm'] / 2 + P['huelse']['passspalt_radial_mm'] + P['huelse']['wand_mm']
    grenze = dv['platte_rand_mm'] + r_h + 3.0
    z_lo, z_hi = lv - 5.0, lv + dv['platte_abstand_ebene_mm'] + dv['platte_dicke_mm'] + r_h
    zs = fs['schiene_z_d13_mm'] + fs['z_versatz_mm'] - 30.0; y = fs['schiene_y_mm']
    def frei(xs):
        a, b = [cx, cy, lv], [xs, y, zs]
        for i in range(41):
            p = add(a, mul(sub(b, a), i / 40))
            if z_lo <= p[2] <= z_hi and min(_abstand_polygon(p[:2], pl) for pl in polys) < grenze:
                return False
        return True
    xs = cx
    while not frei(xs) and xs > cx - 200:
        xs -= 5.0
    return xs


def strecke_im_rotor(a, b, motoren, r_frei, z_grenze=None, n=60):
    """Kleinster Grundrissabstand Strecke a-b zu den Rotorkreisen (nur Punkte unter z_grenze)."""
    best = 1e9
    for i in range(n + 1):
        p = add(a, mul(sub(b, a), i / n))
        if z_grenze is not None and p[2] >= z_grenze:
            continue
        for m in motoren:
            best = min(best, norm(sub(p[:2], m['xy'])) - r_frei)
    return best


def ausruestung(bw, prop, vid, R, g, rotor_oben, unten, hh):
    rf = rahmen(bw, prop, vid); fs = P['fussschlitten']; lg = P['landegestell']; rg = P['regler']; rt = P['rotor']
    hu = g['huelse']; mt = P['motortraeger']
    lv = P['rahmen']['ebene_z_mm']; an = P['rahmen']['eckknoten_rohranschlag_mm']
    motoren = motoren_global(bw, R)
    D = prop['d_mm']
    cx, cy = ausruestungsecken(rf, 'fussschlitten')
    xs = sattel_x(rf, g, cx, cy)
    cxl, cyl = ausruestungsecken(rf, 'fussschlitten')   # gleiche Ecken: Beine laufen von den Verbindern weg
    frei = rt['min_freiraum_struktur_mm']
    env_oben_unterkante = rotor_oben - hh
    # --- Fussschlitten: groesstes L <= max, Bock und Strebe ausserhalb der Rotorkreise
    zr = fs['schiene_z_d13_mm'] + fs['z_versatz_mm']
    schiene_frei_z = zr - fs['rohr_od_mm'] / 2 - (rotor_oben + hh)
    L = fs['schienenbock_max_x_mm']
    while True:
        bock = [L, fs['schiene_y_mm'], zr]
        ecke = [cx, cy, lv]
        d_bock = min(norm(sub(bock[:2], m['xy'])) for m in motoren) - D / 2 - 30.0
        d_str = strecke_im_rotor(ecke, bock, motoren, D / 2 + 15.0, z_grenze=rotor_oben + hh + frei)
        if (d_bock >= frei and d_str >= frei) or L <= cx + 40:
            break
        L -= 5.0
    xf_min = xs + fs['sattel_halbe_laenge_mm'] + fs['sattel_freiraum_mm'] + fs['backe_halbe_laenge_mm']
    L_noetig = xf_min + fs['backe_halbe_laenge_mm'] + fs['bock_freiraum_x_mm']
    if L >= L_noetig:
        modus = 'Bock mit Strebe'
    else:
        # Rotoren zu nah: kurze Schiene, Endbock ohne Strebe; Schiene kragt ueber den Schienensattel aus
        modus = 'Endbock ohne Strebe'; L = L_noetig
        d_bock = min(norm(sub([L, fs['schiene_y_mm']], m['xy'])) for m in motoren) - D / 2 - 30.0
    xf_max = L - fs['bock_freiraum_x_mm'] - fs['backe_halbe_laenge_mm']
    xf = max(xf_min, min(fs['fuss_nenn_x_mm'], xf_max))
    fussschlitten = dict(schiene_z_mm=zr, schiene_y_mm=fs['schiene_y_mm'], bock_x_mm=L, fuss_x_mm=round(xf, 1),
                         fuss_x_max_mm=round(xf_max, 1), fuss_x_min_mm=round(xf_min, 1), sattel_x_mm=xs,
                         verstellbereich_ok=xf_max >= xf_min, ecke=[cx, cy, lv], modus=modus,
                         bock_ueber_rotor_vertikal_mm=round(zr - 18.0 - (rotor_oben + hh), 1),
                         bock_rotor_ok=(d_bock >= frei) or (zr - 18.0 - (rotor_oben + hh) >= frei),
                         schiene_ueber_rotorhuelle_mm=round(schiene_frei_z, 1),
                         nennstand_200mm_moeglich=xf_min - 1e-6 <= fs['fuss_nenn_x_mm'] <= xf_max + 1e-6,
                         bock_rotorabstand_mm=round(d_bock + 30.0, 1))
    # --- Landegestell: Eckfuesse unter allen unteren Eckknoten, Boden knapp unter der Rahmenunterkante
    dv = P['dreiecksverbinder']
    z_rahmen_unten = -(lv + dv['platte_abstand_ebene_mm'] + dv['platte_dicke_mm'] + 8.0)   # Plattenschraubenkopf M8
    zg = z_rahmen_unten - lg['boden_freiraum_mm']
    fuesse = [[round(v[0], 3), round(v[1], 3), zg] for v in eckpunkte(rf)]
    kipp = min(seg_point_dist2d([0, 0], fuesse[i], fuesse[(i + 1) % len(fuesse)]) for i in range(len(fuesse)))
    boden_rotor = None
    if unten is not None:
        boden_rotor = round(unten['rotorebene_z_mm'] - hh - zg, 2)
    landegestell = dict(bauart='Eckfuesse', boden_z_mm=round(zg, 2), rahmen_unterkante_z_mm=round(z_rahmen_unten, 2),
                        fuesse=fuesse, anzahl=len(fuesse), kippkante_mm=round(kipp, 1),
                        standflaeche_mm=[round(2 * max(abs(f[0]) for f in fuesse), 1), round(2 * max(abs(f[1]) for f in fuesse), 1)],
                        unterer_rotor_ueber_boden_mm=boden_rotor,
                        unterer_rotor_boden_ok=(boden_rotor is None) or boden_rotor >= frei)
    # --- Regler: Lage im Paarsystem (linker Ausleger), Abstand vor der Motortraeger-Huelse
    # Platz zwischen Motortraeger-Huelse und Verbinder-Huelse entlang des Auslegers (Grundriss)
    frei_von = g['ce'] + hu['L'] + rg['abstand_hinter_huelse_mm']
    frei_bis = g['Lr'] - g['d0'] - hu['L'] - rg['abstand_hinter_huelse_mm']
    if g.get('eck_rohre'):
        # V4: Halter sitzt auf den Gurten zur Rahmenecke; Platz endet vor der Gurthuelse im Eckknoten
        ec = g['rohre'][-1]; ehor = math.hypot(ec['e'][0], ec['e'][1])
        d_ecke = math.hypot(g['M'][0] - g['Vp'][0], g['M'][1] - g['Vp'][1])
        an_max = max(v_['anschlag_mm'] for v_ in g['eck_rohre'].values())
        frei_bis = min(frei_bis, d_ecke - (an_max + P['rahmen']['eckknoten_steckhuelse_mm']) * ehor - rg['abstand_hinter_huelse_mm'])
    platz = frei_bis - frei_von
    n_hinter = 2 if (unten is not None and g.get('eck_rohre')) else 1      # V4-Koax: zwei Regler hintereinander
    if platz >= n_hinter * (rg['mass_mm'][0] + 12):
        lage, laenge = 'liegend', rg['mass_mm'][0]
    else:
        lage, laenge = 'hochkant', rg['mass_mm'][1]
    if n_hinter == 2 and platz < 2 * (laenge + 12):
        n_hinter = 1                                                       # zweiter Regler passt nicht an den Ausleger
    s_mitte = frei_von + laenge / 2 + 6                                     # Grundrissabstand zur Motorachse
    u = g['u']; M = g['M']
    pz = []
    for t in g['rohre']:
        e = t['e']; I = t['systempunkt']
        k = s_mitte / math.hypot(e[0], e[1])
        pz.append(I[2] - e[2] * k)
    zc = (max(pz) + min(pz)) / 2
    mitte = [M[0] - u[0] * s_mitte, M[1] - u[1] * s_mitte, zc]
    dz = (rg['mass_mm'][1] if lage == 'liegend' else rg['mass_mm'][0]) / 2
    # Lage der Regler (Seite, Grundrissabstand zur Motorachse). V4-Koax: beide aussen hintereinander, weil innen das Mittelrohr liegt
    if unten is None:
        positionen = [[1, s_mitte]]
    elif g.get('eck_rohre'):
        positionen = [[1, s_mitte], [1, s_mitte + laenge + 12]] if n_hinter == 2 else [[1, s_mitte]]
    else:
        positionen = [[1, s_mitte], [-1, s_mitte]]
    s_fern = max(p_[1] for p_ in positionen)
    passt = frei_bis - frei_von >= (s_fern - s_mitte) + laenge + 12 and len(positionen) == (2 if unten is not None else 1)
    regler = dict(mitte=r3(mitte), s_mitte_mm=round(s_mitte, 2), seiten=sorted({p_[0] for p_ in positionen}, reverse=True),
                  positionen=[[p_[0], round(p_[1], 2)] for p_ in positionen],
                  z_bereich_mm=[round(zc - dz, 2), round(zc + dz, 2)],
                  freiraum_oben_mm=round(env_oben_unterkante - (zc + dz), 2),
                  freiraum_unten_mm=None if unten is None else round(zc - dz - (unten['rotorebene_z_mm'] + hh), 2),
                  lage=lage, platz_entlang_ausleger_mm=round(platz, 1), passt=passt,
                  abstand_reglerende_motorachse_mm=round(s_fern - laenge / 2, 1),
                  phasenkabel_reicht=s_fern - laenge / 2 <= rg['phasenkabel_mm'],
                  rohr_z_mm=[round(z, 2) for z in pz])
    return dict(fussschlitten=fussschlitten, landegestell=landegestell, regler=regler)


def statik_ausruestung(bw, a):
    la = P['lasten']; fs = P['fussschlitten']
    g0 = la['g_m_s2']; LF = la['lastfaktor']
    od, di = fs['rohr_od_mm'], fs['rohr_id_mm']
    A = math.pi / 4 * (od ** 2 - di ** 2); Iq = math.pi / 64 * (od ** 4 - di ** 4); Wb = Iq / (od / 2); E = la['cfk_e_modul_mpa']
    f = a['fussschlitten']; l = a['landegestell']
    # Fussschlitten: Person auf zwei Fussplatten, je Platte zwei Schienen
    F = fs['personenmasse_kg'] * g0 * LF / 4
    L = f['bock_x_mm']; xf = f['fuss_x_mm']; xs = f['sattel_x_mm']
    sp = max(L - xs, 1.0); a_ = xf - xs; b_ = L - xf
    if f['modus'] == 'Bock mit Strebe':
        M = F * a_ * b_ / sp               # Einfeldtraeger Sattel-Bock (konservativ, ohne Durchlauf)
        R_s, R_b = F * b_ / sp, F * a_ / sp
    else:
        M = F * a_                         # Kragarm ab Schienensattel
        R_s, R_b = F, 0.0
    ecke = f['ecke']; z = f['schiene_z_mm']; y = f['schiene_y_mm']
    def strebe(ziel, R):
        d = sub(ziel, ecke); Ls = norm(d)
        N = R / (d[2] / Ls)
        return N, N / (math.pi ** 2 * E * Iq / max(Ls - 2 * 58, 50) ** 2)
    N_str, k_str = strebe([L, y, z], R_b)
    N_st, k_st = strebe([xs, y, z], R_s)
    fussschlitten = dict(last_je_schiene_und_fuss_N=round(F, 1), schienenmoment_Nm=round(M / 1000, 1),
                         schienenspannung_MPa=round(M / Wb, 1), schienen_ausnutzung=round(M / Wb / la['cfk_zulaessig_mpa'], 3),
                         strebe_druck_N=round(N_str, 1), strebe_knick_ausnutzung=round(k_str, 3),
                         stuetze_druck_N=round(N_st, 1), stuetze_knick_ausnutzung=round(k_st, 3))
    fussschlitten['bestanden'] = fussschlitten['schienen_ausnutzung'] <= 1 and k_str <= 1 and k_st <= 1
    # Landung: 3 g auf zwei Fuessen, senkrecht ueber Fussstutzen in den Rahmenpfosten
    Fv = la['gesamtmasse_kg'] * g0 * 3.0 / 2
    Lp = 2 * P['rahmen']['ebene_z_mm'] - 2 * P['rahmen']['eckknoten_rohranschlag_mm'] - 2 * 40.0
    Pcr_p = math.pi ** 2 * E * Iq / Lp ** 2
    landung = dict(fusslast_N=round(Fv, 1), pfosten_druck_N=round(Fv, 1), pfosten_spannung_MPa=round(Fv / A, 1),
                   pfosten_knick_ausnutzung=round(Fv / Pcr_p, 3), kippkante_mm=l['kippkante_mm'],
                   hinweis='Kippstabilitaet nicht nachgewiesen: Standbreite nur Rahmenbreite')
    landung['bestanden'] = Fv / A <= la['cfk_zulaessig_mpa'] and Fv / Pcr_p <= 1
    return dict(fussschlitten=fussschlitten, landung=landung,
                modell='Gelenkstab-Screening; Schiene als Einfeldtraeger zwischen den Boecken; Bein zentrisch belastet')


# --------------------------------------------------------- Konfiguration
def konfiguration(bw, prop, vid):
    rt = P['rotor']; mt = P['motortraeger']; mo = P['motor']
    R, quelle = motorradius(bw, prop)
    g = arm(bw, prop, vid, R)
    rf = rahmen(bw, prop, vid)
    npos = P['bauweisen'][bw]['rotorpositionen']
    D = prop['d_mm']
    spitze = 2 * R * math.sin(math.pi / npos) - D
    rohre = alle_rohre_global(bw, g)
    motoren = motoren_global(bw, R)
    hu = g['huelse']
    # Rotorhuelle aus der realen D13-Propellergeometrie: Nabe auf der Motoroberseite
    z_nabe = mt['motor_basis_z_mm'] + mo['h_mm']
    c_rel = (prop['z_min_ueber_nabe_mm'] + prop['z_max_ueber_nabe_mm']) / 2
    hh = (prop['z_max_ueber_nabe_mm'] - prop['z_min_ueber_nabe_mm']) / 2
    z_oben = z_nabe + c_rel                       # Mitte der oberen Rotorhuelle
    zmin_all, zmax_all = 1e9, -1e9
    for m in motoren:
        zmin, zmax = z_min_im_kreis(rohre, m['xy'], D / 2, hu['r_aussen'])
        zmin_all = min(zmin_all, zmin); zmax_all = max(zmax_all, zmax)
    frei_oben = z_oben - hh - zmax_all
    unten = None
    if P['bauweisen'][bw]['motoren_je_position'] == 2:
        # unterer Propeller: an der Motorunterseite gespiegelt, Huellenmitte = Motorunterseite - c_rel
        z_unten = zmin_all - rt['min_freiraum_struktur_mm'] - hh
        fl_unten = z_unten + c_rel + mo['h_mm']     # Unterseite des unteren Flansches = Motoroberseite
        fl_unten = min(fl_unten, mt['systempunkt_z_mm'] - 45.0 - mt['flansch_dicke_mm'])
        z_unten = fl_unten - mo['h_mm'] - c_rel
        unten = dict(rotorebene_z_mm=round(z_unten, 2), flansch_unterseite_z_mm=round(fl_unten, 2),
                     nabe_z_mm=round(fl_unten - mo['h_mm'], 2),
                     freiraum_struktur_mm=round(zmin_all - (z_unten + hh), 2),
                     huelle_unterkante_z_mm=round(z_unten - hh, 2))
    plan = grundriss_freiraum(bw, prop, vid, R)
    stat = stabwerk(bw, g, vid)
    stat['dynamik'] = dynamik(bw, prop, g, vid)
    aus = ausruestung(bw, prop, vid, R, g, z_oben, unten, hh)
    stat_aus = statik_ausruestung(bw, aus)
    # Zuschnitt
    s = rf['seitenlaenge']; an = P['rahmen']['eckknoten_rohranschlag_mm']
    zus = [dict(teil='Auslegerrohr', variante=vid, od=hu['od'], id=hu['id'], index=t['index'],
                laenge_mm=round(t['laenge_mm'] - 0.5, 1), anzahl=2 * rf['paare']) for t in g['rohre']]
    zus.append(dict(teil='Rahmenring', od=20, id=17, laenge_mm=round(s - 2 * an - 0.5, 1), anzahl=2 * rf['seiten']))
    zus.append(dict(teil='Rahmenpfosten', od=20, id=17, laenge_mm=round(2 * rf['ebene'] - 2 * an - 0.5, 1), anzahl=rf['seiten']))
    checks = dict(
        spitzenabstand_mm=round(spitze, 1),
        spitzenabstand_ok=spitze >= rt['min_spitzenabstand_anteil_d'] * D - 1e-6 or bw in ('QUAD', 'KOAX'),
        grundriss_freiraum_mm=round(plan, 1),
        grundriss_ok=plan >= rt['min_freiraum_grundriss_mm'] - 1e-6,
        oberer_rotor_freiraum_mm=round(frei_oben, 1),
        oberer_rotor_ok=frei_oben >= rt['min_freiraum_struktur_mm'] - 1e-6,
        unterer_rotor_ok=(unten is None) or unten['freiraum_struktur_mm'] >= rt['min_freiraum_struktur_mm'] - 1e-6,
        systemlinien_zentrisch=len(g['rohre']) > 1,
        seitensteifigkeit_ok=stat['dynamik']['f_min_Hz'] >= 15.0,
        stabwerk_screening_ok=stat['bestanden'],
        fussschlitten_nennstand_ok=aus['fussschlitten']['nennstand_200mm_moeglich'],
        fussschlitten_verstellbereich_ok=aus['fussschlitten']['verstellbereich_ok'],
        fussschlitten_bock_rotor_ok=aus['fussschlitten']['bock_rotor_ok'],
        regler_rotorfreiraum_ok=aus['regler']['freiraum_oben_mm'] >= rt['min_freiraum_struktur_mm'] and
            (aus['regler']['freiraum_unten_mm'] is None or aus['regler']['freiraum_unten_mm'] >= rt['min_freiraum_struktur_mm']),
        fussschlitten_screening_ok=stat_aus['fussschlitten']['bestanden'],
        regler_phasenkabel_ok=aus['regler']['phasenkabel_reicht'],
        regler_platz_ok=aus['regler']['passt'],
        landung_screening_ok=stat_aus['landung']['bestanden'],
        unterer_rotor_boden_ok=aus['landegestell']['unterer_rotor_boden_ok'])
    return dict(bauweise=bw, propeller=prop['id'], propeller_label=prop['label'], variante=vid,
                schluessel=f"{bw}_{prop['id']}_{vid}", motorradius_mm=round(R, 2), motorradius_quelle=quelle,
                rahmen={k: (round(v, 3) if isinstance(v, float) else v) for k, v in rf.items()},
                rahmenecken=[r3(x) for x in eckpunkte(rf)], paarwinkel_grad=[j * 360.0 / rf['paare'] for j in range(rf['paare'])],
                motoren=motoren, arm=g, rotor_oben_z_mm=round(z_oben, 3), rotor_huelle_halb_mm=round(hh, 3), rotor_nabe_z_mm=z_nabe,
                rotor_unten=unten, rotor_d_mm=D,
                statik=stat, statik_ausruestung=stat_aus, ausruestung=aus, pruefungen=checks, zuschnitt=zus)


def alle():
    out = []
    for bw in P['bauweisen']:
        for prop in P['propeller']:
            for vid in P['varianten']:
                out.append(konfiguration(bw, prop, vid))
    return out


if __name__ == '__main__':
    A = H / 'Ausgabe'; A.mkdir(exist_ok=True)
    cfgs = alle()
    (A / 'Auslegung.json').write_text(json.dumps(dict(revision=P['revision'], anzahl=len(cfgs), konfigurationen=cfgs,
                                                      produktionsfreigabe=False), indent=1, ensure_ascii=False))
    for c in cfgs:
        pr = c['pruefungen']
        flags = [k for k, v in pr.items() if v is False]
        print(f"{c['schluessel']:28s} R={c['motorradius_mm']:7.1f} Lr={c['arm']['Lr']:6.1f} gamma={c['arm']['gamma_grad']:5.1f} "
              f"d0={c['arm']['d0']:5.1f} ce={c['arm']['ce']:5.1f} plan={pr['grundriss_freiraum_mm']:6.1f} "
              f"oben={pr['oberer_rotor_freiraum_mm']:6.1f} {'' if not flags else 'OFFEN:' + ','.join(flags)}")
