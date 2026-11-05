"""D14 Volumenkoerper: Dreiecksverbinder, Eckknoten, Motortraeger (Anhang 4), Schrauben.

Alle Teile werden im Paarsystem des Paares 0 erzeugt (Paar schaut nach +x, linker
Ausleger bei +y). Rechter Ausleger und gegenueberliegende Ecken sind Spiegelbilder.
Huelsen: starrer Teil am Rohrende (angebunden), Klemmteil an der Huelsenmuendung mit
Schlitz, Klemmnase und zwei M4-Schrauben; Isolierhuelse im radialen Passspalt.
"""
import math
import FreeCAD as A
import Part
from auslegung import P

V = A.Vector
Z = V(0, 0, 1)


def vec(p):
    return V(*[float(x) for x in p])


def cyl(r, a, b):
    d = b - a
    return Part.makeCylinder(r, d.Length, a, d)


def basis(adir, pref):
    a = V(adir); a.normalize()
    n = pref - a * pref.dot(a); n.normalize()
    b = a.cross(n); b.normalize()
    return a, n, b


def lbox(o, a, n, b, a0, a1, n0, n1, b0, b1):
    pts = [o + a * a0 + n * n0 + b * b0, o + a * a1 + n * n0 + b * b0,
           o + a * a1 + n * n1 + b * b0, o + a * a0 + n * n1 + b * b0]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(b * (b1 - b0))


def platte(points, z0, dicke, rand, loch_rand=None):
    """Ebene Platte aus Polygon (Draufsicht), gerundet um 'rand' vergroessert."""
    pts = [V(p[0], p[1], z0) for p in points]
    f = Part.Face(Part.makePolygon(pts + [pts[0]]))
    outer = f.makeOffset2D(rand, join=0)
    s = outer.extrude(V(0, 0, dicke))
    if loch_rand is not None:
        try:
            inner = f.makeOffset2D(-loch_rand, join=0)
            if inner.Area > 600:
                s = s.cut(inner.extrude(V(0, 0, dicke)).translated(V(0, 0, 0)))
        except Exception:
            pass
    return s


def schraube(p, d, shank_d, shank_len, head_d, head_h):
    d = V(d); d.normalize()
    return cyl(head_d / 2, p - d * head_h, p).fuse(cyl(shank_d / 2, p, p + d * shank_len))


def huelse(E, into, pref, hu, kammer=0.0, fenster=True, L=None, L_starr=None, start_bei=None, kopf_unten=False):
    """Huelse mit Rohrende E, Achse 'into' zeigt ins Rohr (zur Muendung).

    Liefert (koerper, schnitte, schrauben, isolierhuelse)."""
    h = P['huelse']
    L = hu['L'] if L is None else L
    L_starr = hu['L_starr'] if L_starr is None else L_starr
    a, n, b = basis(into, pref)
    if kopf_unten:
        b = -b
    rb, rs, rk = hu['r_bohr'], hu['r_aussen'], hu['r_kammer']
    nase = h['klemmnase_ueberstand_mm']
    # Nasenhoehe so, dass der Schraubenkopf nicht auf der Huelsenwoelbung aufsitzt
    hn = max(h['klemmnase_hoehe_mm'], 2 * math.sqrt(max(0.0, rs ** 2 - (rb + 2.0) ** 2)) + 1.5)
    anfang = E - a * (kammer + (6.0 if kammer > 0 else 0.0)) if start_bei is None else start_bei
    body = [cyl(rs, anfang, E + a * L),
            lbox(E, a, n, b, L_starr + 1, L - 1, rb + 1, rb + nase, -hn / 2, hn / 2)]
    cuts = [cyl(rb, E, E + a * (L + 1))]
    if kammer > 0:
        cuts.append(cyl(rk, E - a * (kammer + 0.5), E + a * 0.5))
        if fenster:
            cuts.append(lbox(E, a, n, b, -kammer + 3, -3, 0, rs + 2, -rk * 0.85, rk * 0.85))
    cuts.append(lbox(E, a, n, b, L_starr, L + 1, 0, rb + nase + 1, -h['klemmschlitz_mm'] / 2, h['klemmschlitz_mm'] / 2))
    bolts = []
    for t in (L_starr + (L - L_starr) / 3, L_starr + 2 * (L - L_starr) / 3):
        p = E + a * t + n * (rb + 5.5)
        cuts.append(cyl(2.25, p - b * (hn / 2 + 1), p + b * (hn / 2 + 1)))
        bolts.append(schraube(p + b * (hn / 2), -b, 3.8, hn - 2, 7.0, 4.0))
    iso_r_in = hu['od'] / 2 + 0.02
    iso = cyl(iso_r_in + h['isolierhuelse_mm'], E, E + a * L).cut(cyl(iso_r_in, E - a, E + a * (L + 1)))
    return body, cuts, bolts, iso


def _bool(body, cuts, tol=None):
    s = body[0].fuse(body[1:], tol) if (len(body) > 1 and tol) else (body[0].fuse(body[1:]) if len(body) > 1 else body[0])
    if cuts:
        s = s.cut(cuts, tol) if tol else s.cut(cuts)
    return s


def _sequenziell(body, cuts):
    s = body[0]
    for b in body[1:]:
        s = s.fuse(b)
    for c in cuts:
        s = s.cut(c)
    return s


def fertig(body, cuts, name):
    """Boolesche Verknuepfung mit Rueckfallstrategien (OCC-Booleans sind nicht immer reproduzierbar)."""
    versuche = [lambda: _bool(body, cuts), lambda: _bool(body, cuts, 1e-4), lambda: _bool(body, cuts, 1e-3),
                lambda: _sequenziell(body, cuts)]
    letzte = None
    for v in versuche:
        try:
            s = v()
        except Exception as e:
            letzte = e; continue
        if not s.isValid():
            f = s.copy()
            try:
                f.fix(1e-4, 1e-5, 1e-3)
            except Exception:
                pass
            s = f
        if not s.isValid():
            continue
        # kein removeSplitter: veraendert in FreeCAD 1.0 teils den Ausgangskoerper
        big = []
        for x in s.Solids:
            if x.Volume < 0:          # umgekehrt orientierter Koerper aus dem Boolean
                x = x.copy(); x.reverse()
            if x.Volume > 1.0:
                big.append(x)
        if len(big) == 1 and big[0].isValid() and big[0].Volume > 0:
            return big[0]
        letzte = AssertionError((name, [round(x.Volume, 2) for x in s.Solids]))
    raise AssertionError(name + ' ungueltig: ' + str(letzte))


def links_normal(u):
    return V(-u.y, u.x, 0)


def spiegel_y(s):
    return s.mirror(V(0, 0, 0), V(0, 1, 0))


def spiegel_z(s):
    return s.mirror(V(0, 0, 0), V(0, 0, 1))



def steg_mit_fenstern(o, a, n, s0, s1, t2, zr, cfg):
    """Senkrechter Steg; zwischen Huelsen- und Plattenebenen ausgespart."""
    dv = P['dreiecksverbinder']; lv = P['rahmen']['ebene_z_mm']
    rs = cfg['arm']['huelse']['r_aussen']
    anker = [(z, rs + 6) for z in P['varianten'][cfg['variante']]['wurzel_z_mm']]
    hp = dv['platte_abstand_ebene_mm'] + dv['platte_dicke_mm'] + 4
    anker += [(lv, hp), (-lv, hp)]
    anker.sort()
    s = lbox(o, a, n, Z, s0, s1, -t2, t2, -zr, zr)
    fenster = []
    for (z0, h0), (z1, h1) in zip(anker, anker[1:]):
        lo, hi = z0 + h0 + 4, z1 - h1 - 4
        if hi - lo > 12 and s1 - s0 > 22:
            fenster.append(lbox(o, a, n, Z, s0 + 8, s1 - 8, -t2 - 1, t2 + 1, lo, hi))
    return s.cut(fenster) if fenster else s


def ebene_flaeche(points, o, a):
    """Planare Flaeche in der senkrechten Ebene durch o mit Grundrissrichtung a."""
    pts = [o + a * (p - o).dot(a) + Z * p.z for p in points]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))


def huelle_2d(points, o, a):
    """Konvexe Huelle von 3D-Punkten in der senkrechten Ebene (o, a); Rueckgabe 3D."""
    q = sorted({(round((p - o).dot(a), 6), round(p.z, 6)) for p in points})
    def cross(o_, a_, b_): return (a_[0] - o_[0]) * (b_[1] - o_[1]) - (a_[1] - o_[1]) * (b_[0] - o_[0])
    lo, hi = [], []
    for p in q:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(q):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return [o + a * s_ + Z * z_ for s_, z_ in lo[:-1] + hi[:-1]]

# ------------------------------------------------------------ Verbinder
def dreiecksverbinder(cfg):
    g = cfg['arm']; hu = g['huelse']; dv = P['dreiecksverbinder']
    lv = P['rahmen']['ebene_z_mm']
    W = vec(g['W']); u = vec(g['u']); nL = links_normal(u)
    body, cuts, bolts, iso = [], [], [], []
    halb_body, halb_cuts, halb_bolts, halb_iso = [], [], [], []
    for t in g['rohre']:
        e = vec(t['e']); T = vec(t['T']); Wz = V(W.x, W.y, t['wurzel'][2])
        kam = (T - Wz).Length
        # Kopf zur naechstgelegenen freien Seite: Untergurt mit Kopf nach unten
        b_, c_, s_, i_ = huelse(T, e, nL, hu, kammer=kam, fenster=False, kopf_unten=t['wurzel'][2] < 0)
        halb_body += b_; halb_cuts += c_; halb_bolts += s_; halb_iso.append(i_)
    # Armsteg in der Auslegerebene ueber die volle Knotenhoehe
    zr = lv + dv['platte_abstand_ebene_mm'] + dv['platte_dicke_mm']
    s1 = g['d0'] + hu['L_starr']
    t2 = dv['armsteg_dicke_mm'] / 2
    halb_body.append(steg_mit_fenstern(V(W.x, W.y, 0), u, nL, 0, s1, t2, zr, cfg))
    for lst, src in ((body, halb_body), (cuts, halb_cuts), (bolts, halb_bolts), (iso, halb_iso)):
        lst += src + [spiegel_y(x) for x in src]
    # Mittelsaeule (Symmetrieebene)
    ts = dv['saeule_dicke_mm'] / 2
    body.append(steg_mit_fenstern(V(W.x, 0, 0), V(1, 0, 0), V(0, 1, 0), -20, 10, ts, zr, cfg))
    # Dreiecksplatten: je Rahmenebene eine Platte ueber und unter dem Rahmenrohr
    Al = g['A']; Bl = g['B']
    poly = [Bl, Al, [Al[0], -Al[1]], [Bl[0], -Bl[1]]]
    d = dv['platte_dicke_mm']; ab = dv['platte_abstand_ebene_mm']
    plates = []
    for lev in (lv, -lv):
        for z0 in (lev + ab, lev - ab - d):
            plates.append(platte(poly, z0, d, dv['platte_rand_mm'], dv['platte_aussparung_rand_mm']))
            for B in (V(Bl[0], Bl[1], 0), V(Bl[0], -Bl[1], 0)):
                cuts.append(cyl(4.2, V(B.x, B.y, z0 - 1), V(B.x, B.y, z0 + d + 1)))
                if z0 > lev:   # Kopf oben, Gewinde in der Lasche darunter
                    bolts.append(schraube(V(B.x, B.y, z0 + d), V(0, 0, -1), 7.8, 16, 13, 8))
                else:
                    bolts.append(schraube(V(B.x, B.y, z0), V(0, 0, 1), 7.8, 16, 13, 8))
    body += plates
    s = fertig(body, cuts, 'Dreiecksverbinder')
    return s, bolts, iso


# ------------------------------------------------------------- Eckknoten
def eckknoten(cfg, extra=(), fuss=False):
    """Oberer Eckknoten an der Ecke V+ der Verbinderseite (Paarsystem).

    extra: zusaetzliche Huelsen (Richtung, Vorzugsrichtung) im selben lokalen System,
    z. B. Fussschlittenstrebe oder Landebein."""
    rf = cfg['rahmen']; g = cfg['arm']; ra = P['rahmen']; dv = P['dreiecksverbinder']
    lv = ra['ebene_z_mm']
    hu = dict(g['huelse']) if False else None
    od = ra['rohr_od_mm']
    hu = dict(od=od, id=ra['rohr_id_mm'], r_bohr=od / 2 + P['huelse']['passspalt_radial_mm'],
              r_aussen=od / 2 + P['huelse']['passspalt_radial_mm'] + P['huelse']['wand_mm'],
              r_kammer=ra['rohr_id_mm'] / 2, L=ra['eckknoten_steckhuelse_mm'], L_starr=15.0, kammer=0.0)
    V0 = V(g['Vp'][0], g['Vp'][1], lv)
    nf = rf['seiten']
    ang = math.radians(360.0 / nf)
    V2 = V(V0.x * math.cos(ang) - V0.y * math.sin(ang), V0.x * math.sin(ang) + V0.y * math.cos(ang), lv)
    d1 = V(0, -1, 0); d2 = V2 - V0; d2.normalize(); d3 = V(0, 0, -1)
    rad = V(V0.x, V0.y, 0); rad.normalize()
    an = ra['eckknoten_rohranschlag_mm']
    body = [Part.makeSphere(ra['eckknoten_kugel_r_mm'], V0)]
    cuts, bolts, iso = [], [], []
    ports = []
    for d, pref in ((d1, -rad), (d2, -rad), (d3, rad)):
        E = V0 + d * an
        b_, c_, s_, i_ = huelse(E, d, pref, hu, start_bei=V0)
        body += b_; cuts += c_; bolts += s_; iso.append(i_)
        ports.append(dict(E=[E.x, E.y, E.z], d=[d.x, d.y, d.z]))
    alle = [d1, d2, d3]
    for ex in extra:
        d, pref = ex[0], ex[1]
        hx = dict(hu, L=ex[2], L_starr=min(15.0, ex[2] * 0.4)) if len(ex) > 2 else hu
        d = V(d); d.normalize()
        an_e = an
        for o in alle:
            w = math.degrees(math.acos(max(-1.0, min(1.0, d.dot(o)))))
            if w < 89.0:
                an_e = max(an_e, (2 * hu['r_bohr'] + 2.5) / math.sin(math.radians(w)))
        alle.append(d)
        E = V0 + d * an_e
        b_, c_, s_, i_ = huelse(E, d, pref, hx, start_bei=V0)
        body += b_; cuts += c_; bolts += s_; iso.append(i_)
        ports.append(dict(E=[E.x, E.y, E.z], d=[d.x, d.y, d.z]))
    # Laschen fuer den Dreiecksverbinder (ueber und unter der Rahmenebene)
    B = V(g['B'][0], g['B'][1], 0)
    ve = vec(g['ve']); ne = links_normal(ve)
    t = dv['lasche_dicke_mm']; ab = dv['lasche_abstand_ebene_mm']
    L = dv['lasche_bohrung_abstand_ecke_mm']
    for z0 in (lv + ab, lv - ab - t):
        body.append(lbox(V(V0.x, V0.y, z0), ve, ne, Z, 0, L, -13, 13, 0, t))
        body.append(Part.makeCylinder(13, t, V(B.x, B.y, z0)))
        cuts.append(cyl(4.0, V(B.x, B.y, z0 - 1), V(B.x, B.y, z0 + t + 1)))
    if fuss:
        # Eckfuss (lokal nach +z, wird beim unteren Knoten an z = 0 gespiegelt): Stutzen, Fussplatte, M5-Gewinde
        lg = P['landegestell']; zg = cfg['ausruestung']['landegestell']['boden_z_mm']
        z_top = -(zg + lg['sohle_dicke_mm'])                 # lokale Oberkante = Fussplattenunterseite global
        z_pl = z_top - lg['fussplatte_dicke_mm']
        body.append(Part.makeCylinder(lg['stutzen_d_mm'] / 2, z_pl - V0.z + 1.0, V(V0.x, V0.y, V0.z)))
        body.append(Part.makeCylinder(lg['fussplatte_d_mm'] / 2, lg['fussplatte_dicke_mm'], V(V0.x, V0.y, z_pl)))
        th0 = math.atan2(V0.y, V0.x)
        for kk in range(4):
            w = th0 + math.radians(45 + 90 * kk)
            p = V(V0.x + 20 * math.cos(w), V0.y + 20 * math.sin(w), 0)
            cuts.append(Part.makeCylinder(2.5, 7.0, V(p.x, p.y, z_top - 6.0)))
    s = fertig(body, cuts, 'Eckknoten')
    return s, bolts, iso, ports


# ----------------------------------------------------------- Motortraeger
def motortraeger(cfg):
    g = cfg['arm']; hu = g['huelse']; mt = P['motortraeger']
    I = vec(g['I']); M = vec(g['M']); u = vec(g['u']); nL = links_normal(u)
    n = len(g['rohre'])
    rs = (mt['strebe_d_einrohr_mm'] if n == 1 else mt['strebe_d_mm']) / 2
    body, cuts, bolts, iso = [], [], [], []
    starts = []
    for t in g['rohre']:
        e = vec(t['e']); Q = vec(t['Q'])
        pref = -nL if (n == 3 and t['index'] == 1) else nL
        b_, c_, s_, i_ = huelse(Q, -e, pref, hu, kammer=hu['kammer'])
        body += b_; cuts += c_; bolts += s_; iso.append(i_)
        S = Q + e * hu['kammer']
        starts.append(S)
        # Strebe endet innerhalb der Knotenkugel (keine gemeinsamen Endflaechen am Systempunkt)
        body.append(cyl(rs, S, I - e * 6.0))
    body.append(Part.makeSphere(rs + 6, I))
    # Knotenblech in der Auslegerebene: Huellenkontur aus Huelsen, Streben, Nabe und Flansch,
    # Erleichterungsloch im Dreieck zwischen den Gurtstreben (Formgebung wie Anhang 4).
    o = V(g['W'][0], g['W'][1], 0)
    zb_ = mt['motor_basis_z_mm']; ft_ = mt['flansch_dicke_mm']; rf_ = mt['flansch_d_mm'] / 2
    pk = []
    for t in g['rohre']:
        e = vec(t['e']); Q = vec(t['Q'])
        pk += [Q - e * hu['L_starr'], Q + e * hu['kammer']]
    pk += [I, M + u * (rf_ - 6) + Z * (zb_ - ft_), M - u * (rf_ - 6) + Z * (zb_ - ft_)]
    if cfg['rotor_unten'] is not None:
        zf = cfg['rotor_unten']['flansch_unterseite_z_mm']
        pk += [M + u * (rf_ - 6) + Z * (zf + ft_), M - u * (rf_ - 6) + Z * (zf + ft_)]
    st = mt['steg_dicke_mm']
    blech = ebene_flaeche(huelle_2d(pk, o, u), o, u).makeOffset2D(4.0, join=0)
    blech = blech.translated(-nL * (st / 2)).extrude(nL * st)
    loch_pts = [starts[0], I, starts[-1]] if n > 1 else [starts[0], I + Z * 10, M - u * (rf_ - 4) + Z * (zb_ - ft_ - 2)]
    try:
        loch = ebene_flaeche(loch_pts, o, u).makeOffset2D(-(rs + 6), join=0)
        if loch.Area > 120:
            blech = blech.cut(loch.translated(-nL * (st / 2 + 1)).extrude(nL * (st + 2)))
    except Exception:
        pass
    # Motorbauraeume (+2 mm) aus dem Knotenblech freistellen
    rmo = P['motor']['d_mm'] / 2 + 2
    blech = blech.cut(Part.makeCylinder(rmo, 120, V(M.x, M.y, zb_)))
    if cfg['rotor_unten'] is not None:
        blech = blech.cut(Part.makeCylinder(rmo, 120, V(M.x, M.y, zf - 120)))
    body.append(blech)
    # Nabe und Flansch(e)
    zb = mt['motor_basis_z_mm']; ft = mt['flansch_dicke_mm']
    unten = cfg['rotor_unten']
    z_nabe_u = I.z - rs - 4
    flansche = [(zb - ft, zb, 'oben')]
    if unten is not None:
        zf = unten['flansch_unterseite_z_mm']
        flansche.append((zf, zf + ft, 'unten'))
        z_nabe_u = zf
    body.append(Part.makeCylinder(mt['nabe_d_mm'] / 2, zb - z_nabe_u, V(M.x, M.y, z_nabe_u)))
    lk = mt['motor_lochkreis_mm'] / 2
    phi0 = math.atan2(u.y, u.x)
    for z0, z1, lage in flansche:
        body.append(Part.makeCylinder(mt['flansch_d_mm'] / 2, z1 - z0, V(M.x, M.y, z0)))
        zc0, zc1 = (z1 - 12, z1 + 1) if lage == 'oben' else (z0 - 1, z0 + 12)
        cuts.append(Part.makeCylinder(mt['motor_zentrierbohrung_mm'] / 2, zc1 - zc0, V(M.x, M.y, zc0)))
        for k in range(4):
            p = phi0 + math.radians(45 + 90 * k)
            x, y = M.x + lk * math.cos(p), M.y + lk * math.sin(p)
            cuts.append(Part.makeCylinder(3.3, z1 - z0 + 2, V(x, y, z0 - 1)))
            if lage == 'oben':
                bolts.append(schraube(V(x, y, z0), V(0, 0, 1), 5.8, 16, 10, 6))
            else:
                bolts.append(schraube(V(x, y, z1), V(0, 0, -1), 5.8, 16, 10, 6))
    s = fertig(body, cuts, 'Motortraeger')
    return s, bolts, iso


# ----------------------------------------------------- Rohre und Referenzen
def rohr(a, b, od, di):
    a = vec(a); b = vec(b)
    return cyl(od / 2, a, b).cut(cyl(di / 2, a - (b - a) * 0.01, b + (b - a) * 0.01))


def motor_huellen(cfg):
    mo = P['motor']; mt = P['motortraeger']
    M = vec(cfg['arm']['M'])
    out = [Part.makeCylinder(mo['d_mm'] / 2, mo['h_mm'], V(M.x, M.y, mt['motor_basis_z_mm']))]
    if cfg['rotor_unten'] is not None:
        zf = cfg['rotor_unten']['flansch_unterseite_z_mm']
        out.append(Part.makeCylinder(mo['d_mm'] / 2, mo['h_mm'], V(M.x, M.y, zf - mo['h_mm'])))
    return out


def rotor_huellen(cfg):
    M = vec(cfg['arm']['M']); r = cfg['rotor_d_mm'] / 2; hh = cfg['rotor_huelle_halb_mm']
    out = [Part.makeCylinder(r, 2 * hh, V(M.x, M.y, cfg['rotor_oben_z_mm'] - hh))]
    if cfg['rotor_unten'] is not None:
        out.append(Part.makeCylinder(r, 2 * hh, V(M.x, M.y, cfg['rotor_unten']['rotorebene_z_mm'] - hh)))
    return out
