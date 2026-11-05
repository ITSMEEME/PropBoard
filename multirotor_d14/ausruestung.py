"""D14 Ausruestung: Fussschlitten (D02/D03-Teile), Landegestell, Reglerhalter.

Fussschlitten und Landegestell werden in Fahrzeugkoordinaten erzeugt (sie sind an x = 0
und y = 0 gespiegelt symmetrisch). Reglerhalter liegen im Paarsystem des linken Auslegers
wie der Motortraeger. Lastpfade gehen in die Eckknoten des Zentralrahmens.
"""
import math
from pathlib import Path
import FreeCAD as A
import Part
from auslegung import P
import knoten as K

V = A.Vector
Z = V(0, 0, 1)
H = Path(__file__).resolve().parent
QF = H / 'Quellen' / 'Fussschlitten'


def rohr_hu(od, di, L=40.0, L_starr=15.0):
    pa = P['huelse']['passspalt_radial_mm']
    return dict(od=od, id=di, r_bohr=od / 2 + pa, r_aussen=od / 2 + pa + P['huelse']['wand_mm'],
                r_kammer=di / 2, L=L, L_starr=L_starr, kammer=0.0)


def winkel(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b) / (a.Length * b.Length)))))


def anschlag(d, andere, hu, basis=18.0):
    """Rohranschlag so, dass sich Bohrungen benachbarter Huelsen nicht schneiden."""
    t = basis
    for o in andere:
        w = winkel(d, o)
        if w < 89.0:
            t = max(t, (2 * hu['r_bohr'] + 2.5) / math.sin(math.radians(w)))
    return t


def knoten_generisch(mitte, ports, hu, kugel=18.0, name='Knoten', extra_body=(), extra_cuts=()):
    """Kugelknoten mit Klemmhuelsen. ports: Liste (Richtung, Vorzugsrichtung Klemmnase).

    Liefert Koerper, Schrauben, Isolierhuelsen und die Rohranschlagpunkte."""
    body = [Part.makeSphere(kugel, mitte)] + list(extra_body)
    cuts = list(extra_cuts); bolts = []; iso = []; ends = []
    dirs = [V(d).normalize() for d, _ in ports]
    for i, (d, pref) in enumerate(ports):
        d = V(d); d.normalize()
        andere = [o for j, o in enumerate(dirs) if j != i]
        if pref is None:   # Klemmnase weg von den Nachbarhuelsen
            m = V(0, 0, 0)
            for o in andere: m = m + o
            pref = -m if m.Length > 1e-6 else V(0, 0, 1)
            if abs((pref - d * pref.dot(d)).Length) < 1e-3: pref = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
        an = anschlag(d, andere, hu)
        E = mitte + d * an
        b_, c_, s_, i_ = K.huelse(E, d, pref, hu, start_bei=mitte)
        body += b_; cuts += c_; bolts += s_; iso.append(i_); ends.append(E)
    return K.fertig(body, cuts, name), bolts, iso, ends


def lokal(G, v, punkt=True):
    """Inverse einer orthogonalen 4x4-Matrix (Liste spaltenweise) auf einen Vektor."""
    R = [[G[0], G[4], G[8]], [G[1], G[5], G[9]], [G[2], G[6], G[10]]]
    t = [G[12], G[13], G[14]] if punkt else [0, 0, 0]
    w = [v.x - t[0], v.y - t[1], v.z - t[2]]
    return V(sum(R[r][0] * w[r] for r in range(3)), sum(R[r][1] * w[r] for r in range(3)), sum(R[r][2] * w[r] for r in range(3)))


def anwenden(G, s):
    m = A.Matrix(G[0], G[4], G[8], G[12], G[1], G[5], G[9], G[13], G[2], G[6], G[10], G[14], 0, 0, 0, 1)
    return s.transformGeometry(m) if abs(m.determinant() + 1) < 1e-6 else s.transformed(m)


# ------------------------------------------------------------ Fussschlitten
def fussschlitten(cfg):
    a = cfg['ausruestung']['fussschlitten']; fs = P['fussschlitten']
    hu = rohr_hu(fs['rohr_od_mm'], fs['rohr_id_mm'])
    L, y, z = a['bock_x_mm'], a['schiene_y_mm'], a['schiene_z_mm']
    cx, cy, cz = a['ecke']; xs = a['sattel_x_mm']
    C = V(cx, cy, cz)
    teile = {}
    # Schienenbock (+x,+y) mit Schienen-, Querrohr- und Strebenhuelse sowie Lasche fuer die Indexierleiste
    B = V(L, y, z)
    ports = [(V(-1, 0, 0), V(0, 0, -1)), (V(0, -1, 0), V(0, 0, -1))]
    if a['modus'] == 'Bock mit Strebe':
        ports.append((C - B, None))
    yl = fs['indexleiste_y_mm']; zr0, zr1 = z - 12, z + 12
    lasche = Part.makeBox(8, yl + 6 - y, zr1 - zr0, V(L - 8, y, zr0))
    loch = K.cyl(2.25, V(L - 10, yl, z), V(L + 2, yl, z))
    bock, bb, bi, be = knoten_generisch(B, ports, hu, name='Schienenbock', extra_body=[lasche], extra_cuts=[loch])
    bb.append(K.schraube(V(L, yl, z), V(-1, 0, 0), 3.8, 16, 7.0, 4.0))
    teile['bock'] = (bock, bb, bi, be)
    # Schienensattel ueber der Ecke: geteilte Klemme um die durchgehende Schiene, Stuetzenhuelse zur Ecke
    S = V(xs, y, z)
    sl = fs['sattel_halbe_laenge_mm']
    ring = K.cyl(hu['r_aussen'], S - V(sl, 0, 0), S + V(sl, 0, 0))
    d = C - S; d.normalize()
    an = hu['r_aussen'] + 4.0
    hk = dict(hu, L=30.0, L_starr=12.0)          # kurze Stuetze: verkuerzte Huelsen an beiden Enden
    E = S + d * an
    b_, c_, s_, i_ = K.huelse(E, d, V(-1, 0, 0), hk, start_bei=S)   # Klemmnase zur Rahmenmitte, weg von der Backe
    body = [ring] + b_
    cuts = [K.cyl(hu['r_bohr'], S - V(sl + 1, 0, 0), S + V(sl + 1, 0, 0))] + c_
    # Klemmschlitz zur Fahrzeugmitte (-y): oben liegt die Fussplatte, unten die Stuetzenhuelse
    rb_ = hu['r_bohr']
    cuts.append(Part.makeBox(2 * sl + 2, rb_ + 13, P['huelse']['klemmschlitz_mm'], V(xs - sl - 1, y - rb_ - 12, z - 0.5)))
    body.append(Part.makeBox(2 * sl - 2, 11, 16, V(xs - sl + 1, y - rb_ - 11, z - 8)))
    bolts = list(s_)
    for dx in (-sl / 2, sl / 2):
        p = V(xs + dx, y - rb_ - 5.5, z + 8)
        cuts.append(K.cyl(2.25, p - V(0, 0, 17), p + V(0, 0, 1)))
        bolts.append(K.schraube(p, V(0, 0, -1), 3.8, 14, 7.0, 4.0))
    sattel = K.fertig(body, cuts, 'Schienensattel')
    iso_s = K.cyl(hu['od'] / 2 + 0.27, S - V(sl, 0, 0), S + V(sl, 0, 0)).cut(K.cyl(hu['od'] / 2 + 0.02, S - V(sl + 1, 0, 0), S + V(sl + 1, 0, 0)))
    teile['sattel'] = (sattel, bolts, [i_, iso_s], [E])
    return teile


def d12_teile(cfg):
    """D02/D03-Fussschlittenteile aus D12, auf die D14-Lage verschoben (Fusslage und z-Versatz)."""
    import json
    a = cfg['ausruestung']['fussschlitten']; fs = P['fussschlitten']
    inst = json.loads((QF / 'Instanzen_D12.json').read_text())['instanzen']
    dz = fs['z_versatz_mm']; dx = a['fuss_x_mm'] - fs['fuss_nenn_x_mm']
    cache = {}
    out = {'alu': [], 'film': [], 'schrauben': [], 'leiste': []}
    behalten = ('Verstellbacke', 'Fußplatte', 'Fußschlitten', 'Scheibe Fuß', 'Sicherungsmutter Fuß', 'Isolierung Schlitten',
                'Indexierschraube', 'Indexierleiste')
    for r in inst:
        if not r['label'].startswith(behalten):
            continue
        m = r['master']
        if m not in cache:
            s = Part.Shape(); s.read(str(QF / (m + '.brep'))); cache[m] = s
        s = cache[m].copy()
        s.Placement = A.Placement(V(*r['pos']), A.Rotation(*r['quat']))
        s = Part.Shape(s).copy() if False else s
        if r['label'].startswith('Indexierleiste'):
            # Leiste auf Bockabstand kuerzen
            Lk = a['bock_x_mm'] - 8
            s = s.common(Part.makeBox(2 * Lk, 400, 400, V(-Lk, -200, 0)))
            s.translate(V(0, 0, dz))
            yl = math.copysign(fs['indexleiste_y_mm'], r['bbox'][1] + r['bbox'][4]); zl = a['schiene_z_mm']
            for sx in (-1, 1):   # M4-Gewindebohrung in der neuen Stirnseite fuer die Bockschraube
                s = s.cut(K.cyl(2.0, V(sx * (Lk + 1), yl, zl), V(sx * (Lk - 14), yl, zl)))
            out['leiste'].append(s); continue
        sx = 1 if r['bbox'][0] + r['bbox'][3] > 0 else -1
        s.translate(V(sx * dx, 0, dz))
        if m.startswith(('ISO',)):
            out['schrauben'].append(s)
        elif 'FILM' in m:
            out['film'].append(s)
        else:
            out['alu'].append(s)
    return out


# ------------------------------------------------------------ Landegestell
def fussknoten(cfg, diag):
    """Fussknoten (+x,+y) mit Kufen-, Querbinder-, Bein- und optional Diagonalhuelse, Fussplatte und Sohle."""
    l = cfg['ausruestung']['landegestell']; lg = P['landegestell']
    hu = rohr_hu(lg['rohr_od_mm'], lg['rohr_id_mm'])
    F = V(l['fuss_x_mm'], l['fuss_y_mm'], l['knoten_z_mm'])
    cx, cy, cz = l['ecke']
    ports = [(V(-1, 0, 0), None), (V(0, -1, 0), None), (V(cx, cy, cz) - F, None)]
    zg = l['boden_z_mm']; ts = lg['sohle_dicke_mm']; tp = lg['fussplatte_dicke_mm']
    px, py = lg['fussplatte_mm']
    platte = Part.makeBox(px, py, tp, V(F.x - px / 2, F.y - py / 2, zg + ts))
    lochpos = [V(F.x + sx * (px / 2 - 9), F.y + sy * (py / 2 - 9), 0) for sx in (-1, 1) for sy in (-1, 1)]
    cuts = [K.cyl(2.5, V(p.x, p.y, zg + ts - 1), V(p.x, p.y, zg + ts + tp - 2)) for p in lochpos]
    s, bolts, iso, ends = knoten_generisch(F, ports, hu, name='Fussknoten', extra_body=[platte], extra_cuts=cuts)
    sx_, sy_ = lg['sohle_mm']
    sohle = Part.makeBox(sx_, sy_, ts, V(F.x - sx_ / 2, F.y - sy_ / 2, zg))
    for p in lochpos:
        sohle = sohle.cut(K.cyl(5.0, V(p.x, p.y, zg - 1), V(p.x, p.y, zg + 3))).cut(K.cyl(2.75, V(p.x, p.y, zg - 1), V(p.x, p.y, zg + ts + 1)))
        bolts.append(K.schraube(V(p.x, p.y, zg + 3), V(0, 0, 1), 4.8, ts - 3 + tp - 3, 8.5, 3.0))
    return s, bolts, iso, ends, sohle


# ------------------------------------------------------------ Reglerhalter
def reglerhalter(cfg):
    """Reglerhalter am linken Ausleger (Paarsystem). Je Seite eine Halbschale mit Platte; bei nur einer
    Seite traegt die Gegenseite einen Klemmdeckel. Liefert Halter (Liste), Schrauben, Reglerhuellen, Isolierung."""
    g = cfg['arm']; rg = P['regler']; r = cfg['ausruestung']['regler']; hu = g['huelse']
    u = K.vec(g['u']); nL = K.links_normal(u); M = K.vec(g['M'])
    s_m = r['s_mitte_mm']; zc = r['mitte'][2]
    lx, lz, ly = rg['mass_mm'][0], rg['mass_mm'][1], rg['mass_mm'][2]
    lb = list(rg['lochbild_mm'])
    if r['lage'] == 'hochkant':
        lx, lz = lz, lx; lb = lb[::-1]
    dsl = (-40.0, 40.0) if r['lage'] == 'liegend' else (-27.0, 27.0)
    tp = rg['halter_platte_mm']; cl = rg['schelle_laenge_mm']
    rb, rs = hu['r_bohr'], hu['r_aussen']
    if g.get('eck_rohre'):
        rohre = [t for t in g['rohre'] if t['anschluss'] != 'verbinder']      # V4: Schellen auf Ober- und Untergurt (Eckseite)
        # Halter parallel zur Grundrissrichtung der Gurte (Ecke -> Motorachse) statt zur Auslegerachse W -> I
        eg = K.vec(rohre[0]['e']); u = V(eg.x, eg.y, 0); u.normalize(); nL = K.links_normal(u)
    else:
        rohre = g['rohre'] if len(g['rohre']) < 3 else [g['rohre'][0], g['rohre'][-1]]
    # Reglerlagen (Seite, Grundrissabstand zur Motorachse); Schellensaetze je Abstand, Halbschale der Reglerseite mit Platte
    positionen = [tuple(p_) for p_ in r.get('positionen', [[sg, s_m] for sg in r['seiten']])]
    abstaende = sorted({round(p_[1], 3) for p_ in positionen})
    d_p = rs + 3.0
    halter = {p_: [] for p_ in positionen}; deckel = []
    schnitte = []; bolts = []; iso = []
    def auf_rohr(t, s):
        # exakt auf der modellierten Rohrachse T-Q (gerundete Richtungen genuegen fuer 0,02-mm-Spalte nicht)
        T = K.vec(t['T']); Q = K.vec(t['Q'])
        sT = math.hypot(T.x - M.x, T.y - M.y); sQ = math.hypot(Q.x - M.x, Q.y - M.y)
        e = Q - T; e.normalize()
        return Q + (T - Q) * ((s - sQ) / (sT - sQ)), e
    for s_ in abstaende:
        for t in rohre:
            for ds in dsl:
                P0, e = auf_rohr(t, s_ + ds)
                a, n, b = K.basis(-e, nL)          # n = +nL horizontal, b ~ senkrecht
                ring = K.cyl(rs, P0 - a * cl / 2, P0 + a * cl / 2)
                ohr = 9.0
                for sg in (1, -1):
                    half = ring.common(K.lbox(P0, a, n, b, -cl, cl, sg * 0.25, sg * 40, -40, 40))
                    for sb in (1, -1):
                        half = half.fuse(K.lbox(P0, a, n, b, -cl / 2, cl / 2, sg * 0.25, sg * 8.25, sb * (rb + 1), sb * (rs + ohr)))
                    pos = next((p_ for p_ in positionen if p_[0] == sg and abs(p_[1] - s_) < 1e-3), None)
                    if pos is not None:
                        half = half.fuse(K.lbox(P0, a, n, b, -cl / 2, cl / 2, sg * (rb + 1), sg * (d_p + 0.1), -8, 8))
                        halter[pos].append(half)
                    else:
                        deckel.append(half)
                for sb in (1, -1):
                    p = P0 + b * (sb * (rs + ohr / 2 + 0.5))
                    schnitte.append(K.cyl(2.25, p - n * 9, p + n * 9))
                    bolts.append(K.schraube(p - n * 8.25, n, 3.8, 15.5, 7.0, 4.0))
                iso.append(K.cyl(hu['od'] / 2 + 0.27, P0 - a * cl / 2, P0 + a * cl / 2).cut(K.cyl(hu['od'] / 2 + 0.02, P0 - a * cl, P0 + a * cl)))
    regler = []
    for pos in positionen:
        sg, s_ = pos
        o = M - u * s_ + V(0, 0, zc)
        if g.get('eck_rohre'):        # Platte seitlich an die Gurtlage (Eckseite) verschieben
            o = o + nL * (sum((auf_rohr(t, s_)[0] - o).dot(nL) for t in rohre) / len(rohre))
        n = nL * sg
        zr = [auf_rohr(t, s_)[0].z - zc for t in rohre]
        z0 = min(-lz / 2 - 6, min(zr) - 10); z1 = max(lz / 2 + 6, max(zr) + 10)
        halter[pos].append(K.lbox(o, u, n, Z, -lx / 2 - 6, lx / 2 + 6, d_p, d_p + tp, z0, z1))
        regler.append(K.lbox(o, u, n, Z, -lx / 2, lx / 2, d_p + tp, d_p + tp + ly, -lz / 2, lz / 2))
        for su in (-1, 1):
            for sz in (-1, 1):
                p = o + u * (su * lb[0] / 2) + Z * (sz * lb[1] / 2)
                schnitte.append(K.cyl(1.7, p + n * (d_p - 1), p + n * (d_p + tp + 1)))
                bolts.append(K.schraube(p + n * d_p, n, 2.8, tp + 4, 5.5, 3.0))
    teile = []
    bohr = [K.cyl(rb, *(lambda P0, e: (P0 - e * 60, P0 + e * 60))(*auf_rohr(t, s_ + ds))) for s_ in abstaende for t in rohre for ds in dsl]
    zaehler = {}
    for pos in positionen:
        name = 'Reglerhalter ' + ('aussen' if pos[0] > 0 else 'innen')
        zaehler[name] = zaehler.get(name, 0) + 1
        if sum(1 for p_ in positionen if p_[0] == pos[0]) > 1:
            name += f' {zaehler[name]}'
        teile.append((name, K.fertig(halter[pos], schnitte + bohr, 'Reglerhalter')))
    for i, hb in enumerate(deckel):         # Klemmdeckel ohne Platte: Einzelteile
        teile.append((f'Klemmdeckel {i + 1}', K.fertig([hb], schnitte + bohr, 'Klemmdeckel')))
    return teile, bolts, regler, iso
