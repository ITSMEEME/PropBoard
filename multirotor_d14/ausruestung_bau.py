"""Zusammenbau und Pruefung der D14-Ausruestung (Fussschlitten, Landegestell, Reglerhalter)."""
import math
import FreeCAD as A
import Part
from auslegung import P
import knoten as K
import ausruestung as AR

V = A.Vector
ZV = V(0, 0, 1)


def rot(s, deg):
    c = s.copy(); c.rotate(V(0, 0, 0), V(0, 0, 1), deg); return c


def sx_sy(s, sx, sy):
    if sx < 0: s = s.mirror(V(0, 0, 0), V(1, 0, 0))
    if sy < 0: s = s.mirror(V(0, 0, 0), V(0, 1, 0))
    return s


def pv(p, sx, sy):
    return V(p.x * sx, p.y * sy, p.z)


def rohr(a, b, od, di, spalt=0.25):
    d = b - a; d.normalize()
    a = a + d * spalt; b = b - d * spalt
    return dict(a=[a.x, a.y, a.z], b=[b.x, b.y, b.z], od=od, id=di), K.rohr([a.x, a.y, a.z], [b.x, b.y, b.z], od, di)


def ecken_zuordnung(cfg):
    """Fuer jede Rahmenecke: (Paar j, V- ja/nein). Ecke V+ liegt bei phi_j + 180/n, V- bei phi_j - 180/n."""
    rf = cfg['rahmen']; n = rf['seiten']; out = {}
    for j, phi in enumerate(cfg['paarwinkel_grad']):
        for vm, sgn in ((False, 1), (True, -1)):
            w = math.radians(phi + sgn * 180.0 / n)
            out[(round(rf['umkreis'] * math.cos(w), 3), round(rf['umkreis'] * math.sin(w), 3))] = (j, vm)
    return out


def platziere_ecke(s, cfg, j, vm, unten):
    if unten: s = K.spiegel_z(s)
    if vm: s = K.spiegel_y(s)
    return rot(s, cfg['paarwinkel_grad'][j])


def lokal_richtung(d, cfg, j, vm, unten):
    phi = -math.radians(cfg['paarwinkel_grad'][j])
    x = d.x * math.cos(phi) - d.y * math.sin(phi); y = d.x * math.sin(phi) + d.y * math.cos(phi); z = d.z
    if vm: y = -y
    if unten: z = -z
    return V(x, y, z)


def matrix(cfg, j, vm, unten):
    c, s = math.cos(math.radians(cfg['paarwinkel_grad'][j])), math.sin(math.radians(cfg['paarwinkel_grad'][j]))
    sy = -1 if vm else 1; sz = -1 if unten else 1
    return [c, s, 0, 0, -s * sy, c * sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]


def baue(cfg):
    """Liefert dict mit globalen Teilen, Rohren, Sonderecken und Reglerhaltern (Paarsystem)."""
    aus = cfg['ausruestung']; fs = P['fussschlitten']; lg = P['landegestell']
    lv = P['rahmen']['ebene_z_mm']
    teile = []          # (name, form, gruppe)  global
    rohre = []          # (info, form) global
    # ---------------- Fussschlitten
    t = AR.fussschlitten(cfg)
    bock, bb, bi, be = t['bock']; sat, sb, si, se = t['sattel']
    f = aus['fussschlitten']; cx, cy, _ = f['ecke']
    Bk = {}; Sk = {}
    for sx in (1, -1):
        for sy in (1, -1):
            q = f'{"+" if sx > 0 else "-"}{"+" if sy > 0 else "-"}'
            teile.append((f'Schienenbock {q}', sx_sy(bock, sx, sy), 'alu'))
            teile.append((f'Schienenbock Schrauben {q}', sx_sy(Part.makeCompound(bb), sx, sy), 'schraube'))
            teile.append((f'Schienenbock Isolierung {q}', sx_sy(Part.makeCompound(bi), sx, sy), 'film'))
            teile.append((f'Schienensattel {q}', sx_sy(sat, sx, sy), 'alu'))
            teile.append((f'Schienensattel Schrauben {q}', sx_sy(Part.makeCompound(sb), sx, sy), 'schraube'))
            teile.append((f'Schienensattel Isolierung {q}', sx_sy(Part.makeCompound(si), sx, sy), 'film'))
            Bk[(sx, sy)] = [pv(e, sx, sy) for e in be]; Sk[(sx, sy)] = [pv(e, sx, sy) for e in se]
    od, di = fs['rohr_od_mm'], fs['rohr_id_mm']
    for sy in (1, -1):
        rohre.append(('Verstellschiene', *rohr(Bk[(-1, sy)][0], Bk[(1, sy)][0], od, di)))
    for sx in (1, -1):
        rohre.append(('Querrohr Fussschlitten', *rohr(Bk[(sx, -1)][1], Bk[(sx, 1)][1], od, di)))
    d12 = AR.d12_teile(cfg)
    for k, lst in d12.items():
        for i, s in enumerate(lst):
            teile.append((f'D12 {k} {i}', s, {'alu': 'alu', 'film': 'film', 'schrauben': 'schraube', 'leiste': 'alu'}[k]))
    # ---------------- Landegestell: Sohlen unter allen unteren Eckknoten (Fussstutzen sind Teil der Eckknoten)
    l = aus['landegestell']; zg = l['boden_z_mm']
    for i, (x, y, _) in enumerate(l['fuesse']):
        so = Part.makeCylinder(lg['sohle_d_mm'] / 2, lg['sohle_dicke_mm'], V(x, y, zg))
        th0 = math.atan2(y, x); bl = []
        for kk in range(4):
            w = th0 + math.radians(45 + 90 * kk)
            p = V(x + 20 * math.cos(w), y + 20 * math.sin(w), 0)
            so = so.cut(Part.makeCylinder(5.0, 3.2, V(p.x, p.y, zg - 0.1))).cut(Part.makeCylinder(2.75, lg['sohle_dicke_mm'] + 1, V(p.x, p.y, zg - 0.5)))
            bl.append(K.schraube(V(p.x, p.y, zg + 3.0), V(0, 0, 1), 4.8, lg['sohle_dicke_mm'] - 3.0 + 5.5, 8.5, 3.0))
        teile.append((f'Sohle {i + 1}', so, 'sohle'))
        teile.append((f'Sohle Schrauben {i + 1}', Part.makeCompound(bl), 'schraube'))
    # ---------------- Sonderecken (oben: Strebe + Stuetze, unten: Bein [+ Diagonale])
    zuo = ecken_zuordnung(cfg)
    sonder = []
    for unten in (False,):
        for sx in (1, -1):
            for sy in (1, -1):
                Vg = V(sx * cx, sy * cy, lv)
                key = min(zuo, key=lambda k: (k[0] - Vg.x) ** 2 + (k[1] - Vg.y) ** 2)
                j, vm = zuo[key]
                ziele = []
                ziele = [('Stuetze', Sk[(sx, sy)][0], 30.0)]
                if f['modus'] == 'Bock mit Strebe':
                    ziele.insert(0, ('Strebe', Bk[(sx, sy)][2]))
                extra = []
                for zz in ziele:
                    name, ziel = zz[0], zz[1]
                    d = ziel - Vg; d.normalize()
                    pref = d.cross(ZV)
                    if pref.Length < 1e-6: pref = V(1, 0, 0)
                    extra.append((lokal_richtung(d, cfg, j, vm, unten), lokal_richtung(pref, cfg, j, vm, unten)) + tuple(zz[2:]))
                s, b, i, ports = K.eckknoten(cfg, extra)
                sg = platziere_ecke(s, cfg, j, vm, unten)
                bg = platziere_ecke(Part.makeCompound(b), cfg, j, vm, unten)
                ig = platziere_ecke(Part.makeCompound(i), cfg, j, vm, unten)
                q = f'{"+" if sx > 0 else "-"}{"+" if sy > 0 else "-"} {"unten" if unten else "oben"}'
                sonder.append(dict(name=f'Eckknoten {q}', form=sg, schrauben=bg, iso=ig, paar=j, vminus=vm, unten=unten))
                for k_, zz in enumerate(ziele):
                    name, ziel = zz[0], zz[1]
                    Ep = ports[3 + sum(1 for p_ in ports if p_.get('gurt')) + k_]['E']
                    Eg = platziere_ecke(Part.Vertex(V(*Ep)), cfg, j, vm, unten).Point
                    od_ = od
                    rohre.append(({'Strebe': 'Fussschlittenstrebe', 'Stuetze': 'Fussschlittenstuetze', 'Bein': 'Landebein',
                                   'Diagonale': 'Landediagonale'}[name], *rohr(Eg, ziel, od_, di)))
    # ---------------- Reglerhalter (Paarsystem, linker Ausleger)
    halter, hb, regler, hi = AR.reglerhalter(cfg)
    return dict(teile=teile, rohre=rohre, sonder=sonder, halter=halter, halter_schrauben=Part.makeCompound(hb),
                regler=regler, halter_iso=Part.makeCompound(hi))


def ueberdeckung(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


def pruefe(cfg, T, AU, alt):
    """Neue Teile gegen alles Bestehende und untereinander. alt: Liste (name, form) global."""
    neu = [(n, s) for n, s, g in AU['teile']]
    neu += [(r[0] + f' {i}', r[2]) for i, r in enumerate(AU['rohre'])]
    for e in AU['sonder']:
        neu += [(e['name'], e['form']), (e['name'] + ' Schrauben', e['schrauben']), (e['name'] + ' Isolierung', e['iso'])]
    # Reglerhalter je Ausleger global
    rf = cfg['rahmen']
    for j in range(rf['paare']):
        phi = cfg['paarwinkel_grad'][j]
        for sp in (False, True):
            tf = (lambda s: rot(K.spiegel_y(s), phi)) if sp else (lambda s: rot(s, phi))
            arm = f'Paar{j + 1}{"R" if sp else "L"}'
            for name, s in AU['halter']:
                neu.append((f'{name} {arm}', tf(s)))
            neu.append((f'Reglerhalter Schrauben {arm}', tf(AU['halter_schrauben'])))
            neu.append((f'Reglerhalter Isolierung {arm}', tf(AU['halter_iso'])))
            for i, r in enumerate(AU['regler']):
                neu.append((f'Regler {i + 1} {arm}', tf(r)))
    ausnahmen = [('Regler', 'Reglerhalter Schrauben')]   # M3 greifen planmaessig ins Reglergehaeuse
    def erlaubt(a, b):
        for x, y in ausnahmen:
            if (a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)):
                if a.split()[-1] == b.split()[-1]:
                    return True
        # Die D12-Fussschlittenteile wurden in D12 als Baugruppe geprueft und bewegen sich gemeinsam
        return a.startswith('D12') and b.startswith('D12')
    tests = []
    for i, (na, sa) in enumerate(neu):
        for nb, sb in neu[i + 1:] + alt:
            if erlaubt(na, nb):
                continue
            if not sa.BoundBox.intersect(sb.BoundBox):
                continue
            v = sa.common(sb).Volume
            tests.append(dict(pruefung=f'{na} / {nb}', ueberdeckung_mm3=round(v, 4), bestanden=v <= 1e-3))
    gueltig = all(s.isValid() for n, s in neu if not n.startswith('D12'))
    return tests, gueltig, len(neu)
