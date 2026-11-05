"""D14 Builder: Volumenkoerper, Kollisionspruefung, Massen, Viewerdaten, FCStd/STEP.

Aufruf mit dem FreeCAD-Python (AppImage):
  FC=~/Programme/squashfs-root/usr
  LD_LIBRARY_PATH=$FC/lib $FC/bin/python multirotor_d14/bauen.py            # alle 120
  ... bauen.py --konfig QUAD_HEP_S_42_16_V3 --nativ                          # einzeln + FCStd/STEP
"""
from pathlib import Path
import sys, os, json, math, time, hashlib, base64, array, argparse

H = Path(__file__).resolve().parent
FC = os.environ.get('FREECAD_USR', str(Path.home() / 'Programme/squashfs-root/usr'))
sys.path += [FC + '/lib', FC + '/Mod']
sys.path.insert(0, str(H))
import FreeCAD as A
import Part
import auslegung as AU
import knoten as K
import ausruestung_bau as AB

V = A.Vector
O = H / 'Ausgabe'; VO = O / 'viewer'; NO = O / 'nativ'; CA = H / 'Cache'
for d in (O, VO, NO, CA): d.mkdir(parents=True, exist_ok=True)
P = AU.P
ALU = P['werkstoffe']['alu_dichte_kg_m3'] * 1e-9
CFK = P['werkstoffe']['cfk_dichte_kg_m3'] * 1e-9
STAHL = P['werkstoffe']['stahl_dichte_kg_m3'] * 1e-9
TOL = 1e-3   # mm3 erlaubte numerische Ueberdeckung
SIG = hashlib.sha256(b''.join((H / f).read_bytes() for f in ('knoten.py', 'auslegung.py', 'ausruestung.py', 'ausruestung_bau.py', 'parameter.json'))).hexdigest()[:16]


# ---------------------------------------------------------------- Helfer
def rot(s, deg):
    c = s.copy(); c.rotate(V(0, 0, 0), V(0, 0, 1), deg); return c


def comp(lst):
    return Part.makeCompound(lst)


def ueberdeckung(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


def cache_shape(name, builder):
    f = CA / f'{name}_{SIG}.brep'
    if f.exists():
        s = Part.Shape(); s.read(str(f)); return s, True
    s = builder(); s.exportBrep(str(f)); return s, False


def mesh(shape, tol=0.3, winkel=0.5):
    import MeshPart
    mm = MeshPart.meshFromShape(Shape=shape, LinearDeflection=tol, AngularDeflection=winkel, Relative=False)
    v, t = mm.Topology
    if not v:
        return None
    xs = [p.x for p in v]; ys = [p.y for p in v]; zs = [p.z for p in v]
    c = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2]
    q = array.array('h', [int(round((p[i] - c[i]) / 0.05)) for p in [(p.x, p.y, p.z) for p in v] for i in range(3)])
    idx = array.array('I' if len(v) > 65535 else 'H', [i for tri in t for i in tri])
    return dict(c=[round(x, 3) for x in c], s=0.05, v=base64.b64encode(q.tobytes()).decode(),
                i=base64.b64encode(idx.tobytes()).decode(), i32=len(v) > 65535, n=len(t))


# ------------------------------------------------------------- Geometrie
def rahmenrohre(cfg):
    """Ringrohre und Pfosten global (alle Seiten)."""
    rf = cfg['rahmen']; ra = P['rahmen']; lv = ra['ebene_z_mm']; an = ra['eckknoten_rohranschlag_mm']
    ecken = cfg['rahmenecken']; out = []
    for i, a in enumerate(ecken):
        b = ecken[(i + 1) % len(ecken)]
        d = V(b[0] - a[0], b[1] - a[1], 0); L = d.Length; d.normalize()
        for z in (lv, -lv):
            pa = V(a[0], a[1], z) + d * (an + 0.25); pb = V(b[0], b[1], z) - d * (an + 0.25)
            out.append(('Ring', K.rohr([pa.x, pa.y, pa.z], [pb.x, pb.y, pb.z], ra['rohr_od_mm'], ra['rohr_id_mm']), (pa, pb)))
        pa = V(a[0], a[1], lv - an - 0.25); pb = V(a[0], a[1], -lv + an + 0.25)
        out.append(('Pfosten', K.rohr([pa.x, pa.y, pa.z], [pb.x, pb.y, pb.z], ra['rohr_od_mm'], ra['rohr_id_mm']), (pa, pb)))
    return out


def armrohre_links(cfg):
    """Rohre mit 0,25 mm Stirnspalt je Ende (Zuschnitt = Systemabstand - 0,5 mm)."""
    hu = cfg['arm']['huelse']; out = []
    for t in cfg['arm']['rohre']:
        a = V(*t['T']); b = V(*t['Q']); d = b - a; d.normalize()
        a = a + d * 0.25; b = b - d * 0.25
        out.append(K.rohr([a.x, a.y, a.z], [b.x, b.y, b.z], hu['od'], hu['id']))
    return out


def baue(cfg):
    key = cfg['schluessel']; bw = cfg['bauweise']
    t0 = time.time()
    conn_all = {}
    def bconn():
        s, b, i = K.dreiecksverbinder(cfg); conn_all.update(b=b, i=i); return s
    conn, c1 = cache_shape(key + '_Verbinder', bconn)
    if not conn_all:
        _, b, i = (None, None, None)
    mount_all = {}
    def bmount():
        s, b, i = K.motortraeger(cfg); mount_all.update(b=b, i=i); return s
    mount, c2 = cache_shape(key + '_Motortraeger', bmount)
    eck_all = {}
    def beck():
        s, b, i, p = K.eckknoten(cfg); eck_all.update(b=b, i=i); return s
    ek = key if cfg['arm'].get('eck_rohre') else bw          # V4: Eckknoten tragen konfigurationsabhaengige Gurthuelsen
    eck, c3 = cache_shape(ek + '_Eckknoten', beck)
    eck_u_all = {}
    def becku():
        s, b, i, p = K.eckknoten(cfg, fuss=True); eck_u_all.update(b=b, i=i); return s
    eck_u, _ = cache_shape(ek + '_Eckknoten_unten', becku)
    # Schrauben/Isolierhuelsen sind einfache Koerper: bei Cache-Treffer schnell neu erzeugen
    if not conn_all:
        g = dict(cfg)
        conn_bolts, conn_iso = conn_bolt_iso(cfg)
    else:
        conn_bolts, conn_iso = conn_all['b'], conn_all['i']
    if not mount_all:
        mount_bolts, mount_iso = mount_bolt_iso(cfg)
    else:
        mount_bolts, mount_iso = mount_all['b'], mount_all['i']
    if not eck_all:
        _, eck_bolts, eck_iso, _ = K.eckknoten(cfg)
    else:
        eck_bolts, eck_iso = eck_all['b'], eck_all['i']
    if cfg['arm'].get('eck_rohre'):          # V4: unterer Knoten hat eine eigene Gurthuelse (Schrauben/Isolierung)
        if not eck_u_all:
            _, ub, ui, _ = K.eckknoten(cfg, fuss=True)
        else:
            ub, ui = eck_u_all['b'], eck_u_all['i']
    else:
        ub, ui = eck_bolts, eck_iso
    return dict(conn=conn, mount=mount, eck=eck, eck_u=eck_u, conn_bolts=comp(conn_bolts), mount_bolts=comp(mount_bolts),
                eck_bolts=comp(eck_bolts), conn_iso=comp(conn_iso), mount_iso=comp(mount_iso), eck_iso=comp(eck_iso),
                eck_u_bolts=comp(ub), eck_u_iso=comp(ui),
                cache=[c1, c2, c3], zeit_s=round(time.time() - t0, 1))


def conn_bolt_iso(cfg):
    _, b, i = K.dreiecksverbinder(cfg); return b, i


def mount_bolt_iso(cfg):
    _, b, i = K.motortraeger(cfg); return b, i


def ecken_instanzen(eck, eck_u):
    """Vier Eckknoten an der Verbinderseite von Paar 0: (V+,oben),(V-,oben),(V+,unten),(V-,unten).
    Untere Knoten tragen den Eckfuss."""
    return [eck, K.spiegel_y(eck), K.spiegel_z(eck_u), K.spiegel_z(K.spiegel_y(eck_u))]


# --------------------------------------------------------------- Pruefung
def pruefe(cfg, T):
    lv = P['rahmen']['ebene_z_mm']
    rl = armrohre_links(cfg); rr = [K.spiegel_y(r) for r in rl]
    rahmen = rahmenrohre(cfg)
    # nur Rahmenrohre in der Naehe von Paar 0 (Verbinderseite und Nachbarseiten)
    nah = [r for name, r, _ in rahmen if r.BoundBox.XMax > 0]
    ecken = ecken_instanzen(T['eck'], T['eck_u'])
    eck_b = [T['eck_bolts'], K.spiegel_y(T['eck_bolts']), K.spiegel_z(T['eck_u_bolts']), K.spiegel_z(K.spiegel_y(T['eck_u_bolts']))]
    eck_i = [T['eck_iso'], K.spiegel_y(T['eck_iso']), K.spiegel_z(T['eck_u_iso']), K.spiegel_z(K.spiegel_y(T['eck_u_iso']))]
    mL = T['mount']; mR = K.spiegel_y(mL)
    mbL = T['mount_bolts']; mbR = K.spiegel_y(mbL)
    miL = T['mount_iso']; miR = K.spiegel_y(miL)
    motL = K.motor_huellen(cfg); motR = [K.spiegel_y(m) for m in motL]
    propL = K.rotor_huellen(cfg); propR = [K.spiegel_y(p) for p in propL]
    # alle Auslegerrohre aller Paare (fuer Rotorfreiraum)
    rf = cfg['rahmen']; alle_rohre = []
    for j in range(rf['paare']):
        phi = j * 360.0 / rf['paare']
        alle_rohre += [rot(r, phi) for r in rl + rr]
    C = T['conn']
    tests = []
    def t(name, a, b, grenze=TOL):
        v = ueberdeckung(a, b); tests.append(dict(pruefung=name, ueberdeckung_mm3=round(v, 4), bestanden=v <= grenze))
    for k, (a, b) in enumerate(zip(rl, rr)):
        t(f'Verbinder/Rohr L{k}', C, a); t(f'Verbinder/Rohr R{k}', C, b)
        t(f'Motortraeger L/Rohr L{k}', mL, a); t(f'Motortraeger R/Rohr R{k}', mR, b)
        t(f'Isolierhuelsen Verbinder/Rohr L{k}', T['conn_iso'], a); t(f'Isolierhuelsen Motor/Rohr L{k}', miL, a)
        for j, c in enumerate(rr):
            t(f'Rohr L{k}/Rohr R{j}', a, c)
        for j, f in enumerate(nah):
            t(f'Rohr L{k}/Rahmenrohr {j}', a, f)
        for j, e in enumerate(ecken):
            t(f'Rohr L{k}/Eckknoten {j}', a, e)
    t('Verbinder/Isolierhuelsen', C, T['conn_iso'])
    t('Motortraeger/Isolierhuelsen', mL, miL)
    for j, e in enumerate(ecken):
        t(f'Verbinder/Eckknoten {j}', C, e)
        t(f'Eckknoten {j}/Isolierhuelsen', e, eck_i[j])
        t(f'Verbinderschrauben/Eckknoten {j}', T['conn_bolts'], e)
        t(f'Eckknotenschrauben {j}/Verbinder', eck_b[j], C)
        for i, f in enumerate(nah):
            t(f'Eckknoten {j}/Rahmenrohr {i}', e, f)
            t(f'Eckknotenschrauben {j}/Rahmenrohr {i}', eck_b[j], f)
    for i, f in enumerate(nah):
        t(f'Verbinder/Rahmenrohr {i}', C, f)
        t(f'Verbinderschrauben/Rahmenrohr {i}', T['conn_bolts'], f)
    t('Verbinderschrauben/Verbinder', T['conn_bolts'], C)
    t('Motortraegerschrauben/Motortraeger', mbL, mL)
    for k, a in enumerate(rl):
        t(f'Verbinderschrauben/Rohr L{k}', T['conn_bolts'], a)
        t(f'Motortraegerschrauben/Rohr L{k}', mbL, a)
    t('Verbinder/Motortraeger L', C, mL); t('Verbinder/Motortraeger R', C, mR)
    for i, m in enumerate(motL):
        t(f'Motortraeger L/Motorhuelle {i}', mL, m)
        for k, a in enumerate(rl):
            t(f'Motorhuelle {i}/Rohr L{k}', m, a)
    for i, p in enumerate(propL + propR):
        for name, s in [('Verbinder', C), ('Motortraeger L', mL), ('Motortraeger R', mR),
                        ('Verbinderschrauben', T['conn_bolts']), ('Motortraegerschrauben L', mbL), ('Motortraegerschrauben R', mbR)] + \
                       [(f'Eckknoten {j}', e) for j, e in enumerate(ecken)] + [(f'Rahmenrohr {j}', f) for j, f in enumerate(nah)]:
            t(f'Rotorhuelle {i}/{name}', p, s)
        for k, a in enumerate(alle_rohre):
            t(f'Rotorhuelle {i}/Auslegerrohr {k}', p, a)
    gueltig = dict(Verbinder=(C.isValid(), len(C.Solids)), Motortraeger=(mL.isValid(), len(mL.Solids)),
                   Eckknoten=(T['eck'].isValid(), len(T['eck'].Solids)))
    alle_ok = all(x['bestanden'] for x in tests) and all(v and n == 1 for v, n in gueltig.values())
    return tests, gueltig, alle_ok


def massen(cfg, T):
    rf = cfg['rahmen']; paare = rf['paare']; mpp = P['bauweisen'][cfg['bauweise']]['motoren_je_position']
    rl = armrohre_links(cfg)
    rahmen = rahmenrohre(cfg)
    m = dict(
        verbinder_je_stueck_kg=T['conn'].Volume * ALU, verbinder_anzahl=paare,
        motortraeger_je_stueck_kg=T['mount'].Volume * ALU, motortraeger_anzahl=2 * paare,
        eckknoten_je_stueck_kg=T['eck'].Volume * ALU, eckknoten_anzahl=2 * rf['seiten'],
        eckknoten_mit_fuss_je_stueck_kg=T['eck_u'].Volume * ALU,
        auslegerrohre_je_ausleger_kg=sum(r.Volume for r in rl) * CFK,
        rahmenrohre_gesamt_kg=sum(r.Volume for _, r, _ in rahmen) * CFK,
        schrauben_je_verbinder_kg=T['conn_bolts'].Volume * STAHL,
        schrauben_je_motortraeger_kg=T['mount_bolts'].Volume * STAHL,
        schrauben_je_eckknoten_kg=T['eck_bolts'].Volume * STAHL)
    m['struktur_gesamt_kg'] = (m['verbinder_je_stueck_kg'] + m['schrauben_je_verbinder_kg']) * paare + \
        (m['motortraeger_je_stueck_kg'] + m['schrauben_je_motortraeger_kg']) * 2 * paare + \
        (m['eckknoten_je_stueck_kg'] + m['eckknoten_mit_fuss_je_stueck_kg'] + 2 * m['schrauben_je_eckknoten_kg']) * rf['seiten'] + \
        m['auslegerrohre_je_ausleger_kg'] * 2 * paare + m['rahmenrohre_gesamt_kg']
    m['hinweis'] = 'CAD-Volumen x angenommene Dichte; ohne Motoren, Regler, Kabel, Akku, Plattform, Landefuesse'
    m['motoren_gesamt'] = 2 * paare * mpp
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}


# ------------------------------------------------------- Ausruestung global
def standard_ecken(cfg, AUS):
    """Standard-Eckknoten-Instanzen (j, V-, unten) ohne die Sonderecken der Ausruestung."""
    sonder = {(e['paar'], e['vminus'], e['unten']) for e in AUS['sonder']}
    return [(j, vm, un) for j in range(cfg['rahmen']['paare']) for vm in (False, True) for un in (False, True)
            if (j, vm, un) not in sonder]


def alt_global(cfg, T, AUS):
    """Bestehende Teile (Struktur, Antrieb, Rotorhuellen) in Fahrzeugkoordinaten."""
    out = []
    rl = armrohre_links(cfg)
    motL = K.motor_huellen(cfg); propL = K.rotor_huellen(cfg)
    for j, phi in enumerate(cfg['paarwinkel_grad']):
        out += [(f'Verbinder P{j + 1}', rot(T['conn'], phi)), (f'Verbinderschrauben P{j + 1}', rot(T['conn_bolts'], phi))]
        for sp in (False, True):
            tf = (lambda x: rot(K.spiegel_y(x), phi)) if sp else (lambda x: rot(x, phi))
            a = f'P{j + 1}{"R" if sp else "L"}'
            out += [(f'Motortraeger {a}', tf(T['mount'])), (f'Motortraegerschrauben {a}', tf(T['mount_bolts']))]
            out += [(f'Auslegerrohr {a}{k}', tf(r)) for k, r in enumerate(rl)]
            out += [(f'Motorhuelle {a}{k}', tf(m)) for k, m in enumerate(motL)]
            out += [(f'Rotorhuelle {a}{k}', tf(p)) for k, p in enumerate(propL)]
    for j, vm, un in standard_ecken(cfg, AUS):
        out.append((f'Eckknoten P{j + 1}{"-" if vm else "+"}{"u" if un else "o"}', AB.platziere_ecke(T['eck_u'] if un else T['eck'], cfg, j, vm, un)))
        out.append((f'Eckknotenschrauben P{j + 1}{"-" if vm else "+"}{"u" if un else "o"}', AB.platziere_ecke(T['eck_u_bolts'] if un else T['eck_bolts'], cfg, j, vm, un)))
    out += [(f'Rahmenrohr {i}', r) for i, (_, r, _) in enumerate(rahmenrohre(cfg))]
    return out


def massen_ausruestung(cfg, AUS, eck_masse=0.0):
    rho = dict(alu=ALU, schraube=STAHL, film=1900e-9, sohle=P['landegestell']['sohle_dichte_kg_m3'] * 1e-9)
    m = dict(fussschlitten_alu_kg=0.0, landegestell_alu_kg=0.0, schrauben_kg=0.0, sohlen_kg=0.0, isolierung_kg=0.0)
    for n, s, g in AUS['teile']:
        v = s.Volume * rho[g]
        if g == 'schraube': m['schrauben_kg'] += v
        elif g == 'sohle': m['sohlen_kg'] += v
        elif g == 'film': m['isolierung_kg'] += v
        elif n.startswith(('Fussknoten',)): m['landegestell_alu_kg'] += v
        else: m['fussschlitten_alu_kg'] += v
    for e in AUS['sonder']:
        m['schrauben_kg'] += e['schrauben'].Volume * STAHL
    cf = {}
    for name, info, form in AUS['rohre']:
        cf[name] = cf.get(name, 0.0) + form.Volume * CFK
    m['cfk_rohre_kg'] = cf
    arme = 2 * cfg['rahmen']['paare']
    m['reglerhalter_je_ausleger_kg'] = sum(s.Volume for _, s in AUS['halter']) * ALU + AUS['halter_schrauben'].Volume * STAHL
    m['regler_anzahl'] = arme * len(AUS['regler'])
    m['regler_katalog_kg'] = m['regler_anzahl'] * P['regler']['masse_kg']
    m['ausruestung_gesamt_ohne_regler_kg'] = m['fussschlitten_alu_kg'] + m['landegestell_alu_kg'] + m['schrauben_kg'] + \
        m['sohlen_kg'] + m['isolierung_kg'] + sum(cf.values()) + m['reglerhalter_je_ausleger_kg'] * arme
    # Sonderecken ersetzen Standard-Eckknoten, deren Masse bereits in der Strukturmasse steckt: nur Mehrmasse zaehlen
    m['fussschlitten_alu_kg'] -= len(AUS['sonder']) * eck_masse
    m['ausruestung_gesamt_ohne_regler_kg'] -= len(AUS['sonder']) * eck_masse
    m['hinweis'] = 'Sonderecken nur mit ihrer Mehrmasse gegenueber Standard-Eckknoten; Regler separat (Katalogmasse inkl. Leitungen)'
    r = lambda v: round(v, 4) if isinstance(v, float) else ({k: round(x, 4) for k, x in v.items()} if isinstance(v, dict) else v)
    return {k: r(v) for k, v in m.items()}

PROP_CACHE = {}


def propeller_form(pid, hand):
    """D13-Bildpropeller (STEP) im lokalen Motorsystem: Achse bei x = y = 0, Nabenunterseite z = 154."""
    key = (pid, hand)
    if key not in PROP_CACHE:
        pr = [p for p in P['propeller'] if p['id'] == pid][0]
        s = Part.Shape(); s.read(str((H / pr['step_' + hand.lower()]).resolve()))
        PROP_CACHE[key] = s
    return PROP_CACHE[key]


def propeller_mesh(pid):
    f = VO / f'Propeller_{pid}.js'
    if f.exists():
        return
    f.write_text('D14_PROPELLER(' + json.dumps(dict(id=pid, cw=mesh(propeller_form(pid, 'CW'), 0.5, 0.35),
                 ccw=mesh(propeller_form(pid, 'CCW'), 0.5, 0.35)), separators=(',', ':')) + ');\n')


def propeller_instanzen(cfg):
    """Globale Propellerkoerper: oben an jeder Motorachse, Koax unten gespiegelt (Gegenlauf)."""
    out = []
    for m in cfg['motoren']:
        s = propeller_form(cfg['propeller'], m['drehrichtung'])
        o = s.copy(); o.rotate(V(0, 0, 0), V(0, 0, 1), m['winkel_grad']); o.translate(V(m['xy'][0], m['xy'][1], 0))
        out.append((f"Propeller M{m['nr']} {m['drehrichtung']}", o))
        if cfg['rotor_unten']:
            zn = cfg['rotor_unten']['nabe_z_mm']
            u = s.mirror(V(0, 0, cfg['rotor_nabe_z_mm']), V(0, 0, 1))
            u.translate(V(0, 0, zn - cfg['rotor_nabe_z_mm']))
            u.rotate(V(0, 0, 0), V(0, 0, 1), m['winkel_grad']); u.translate(V(m['xy'][0], m['xy'][1], 0))
            out.append((f"Propeller M{m['nr']} unten (gegenlaeufig)", u))
    return out



def d12_gemeinsam(cfg):
    """D12-Backen, Fussplatten und Normteile in Nennlage (Fussmitte +-200 mm), getrennt nach Seite."""
    f = VO / 'Fussschlitten_D12.js'
    if f.exists():
        return
    import copy, ausruestung as AR
    c = copy.deepcopy(cfg); c['ausruestung']['fussschlitten']['fuss_x_mm'] = P['fussschlitten']['fuss_nenn_x_mm']
    t = AR.d12_teile(c)
    out = {}
    for seite, sx in (('plus', 1), ('minus', -1)):
        alu = [s for s in t['alu'] if s.BoundBox.Center.x * sx > 0]
        sch = [s for s in t['schrauben'] if s.BoundBox.Center.x * sx > 0]
        out[seite] = dict(alu=mesh(comp(alu), 0.4, 0.6), schrauben=mesh(comp(sch), 0.8, 1.0))
    f.write_text('D14_D12(' + json.dumps(out, separators=(',', ':')) + ');\n')


# ----------------------------------------------------------------- Viewer
def viewerdaten(cfg, T, pruef, AUS=None):
    g = cfg['arm']; hu = g['huelse']; ra = P['rahmen']
    meshes = dict(verbinder=mesh(T['conn']), verbinder_schrauben=mesh(T['conn_bolts'], 0.6, 0.8),
                  motortraeger=mesh(T['mount']), motortraeger_schrauben=mesh(T['mount_bolts'], 0.6, 0.8))
    ef = VO / f"Eckknoten_{cfg['bauweise']}.js"
    eigene_ecken = bool(g.get('eck_rohre'))
    if not eigene_ecken and (not ef.exists() or ef.stat().st_mtime < (CA / f"{cfg['bauweise']}_Eckknoten_{SIG}.brep").stat().st_mtime):
        ef.write_text('D14_ECKE(' + json.dumps(dict(bauweise=cfg['bauweise'], eckknoten=mesh(T['eck']), eckknoten_unten=mesh(T['eck_u']),
                      eckknoten_schrauben=mesh(T['eck_bolts'], 0.6, 0.8)), separators=(',', ':')) + ');\n')
    rohre = [dict(a=t['T'], b=t['Q'], od=hu['od'], id=hu['id']) for t in g['rohre']]
    rahmen = [dict(a=[p[0].x, p[0].y, p[0].z], b=[p[1].x, p[1].y, p[1].z], od=ra['rohr_od_mm'], id=ra['rohr_id_mm'])
              for _, _, p in rahmenrohre(cfg)]
    mo = P['motor']; mt = P['motortraeger']
    motoren = [dict(z0=mt['motor_basis_z_mm'], h=mo['h_mm'])]
    rotoren = [dict(z=cfg['rotor_oben_z_mm'])]
    if cfg['rotor_unten']:
        motoren.append(dict(z0=cfg['rotor_unten']['flansch_unterseite_z_mm'] - mo['h_mm'], h=mo['h_mm']))
        rotoren.append(dict(z=cfg['rotor_unten']['rotorebene_z_mm']))
    d = dict(schluessel=cfg['schluessel'], paarwinkel=cfg['paarwinkel_grad'], meshes=meshes, rohre=rohre, rahmen=rahmen,
             motor=dict(xy=g['M'][:2], d=mo['d_mm'], lagen=motoren), rotor=dict(d=cfg['rotor_d_mm'], halb=cfg['rotor_huelle_halb_mm'], lagen=rotoren),
             systemlinien=[[t['wurzel'], t['systempunkt']] for t in g['rohre']],
             W=g['W'], I=g['I'], motoren=cfg['motoren'])
    if eigene_ecken:
        d['eck_meshes'] = dict(eckknoten=mesh(T['eck']), eckknoten_unten=mesh(T['eck_u']), eckknoten_schrauben=mesh(T['eck_bolts'], 0.6, 0.8),
                               eckknoten_schrauben_unten=mesh(T['eck_u_bolts'], 0.6, 0.8))
    if AUS is not None:
        d['ecken'] = [dict(m=AB.matrix(cfg, j, vm, un), u=un) for j, vm, un in standard_ecken(cfg, AUS)]
        grp = {'alu': [], 'schraube': [], 'sohle': []}
        for n, sh, gr in AUS['teile']:
            if n.startswith('D12') and not n.startswith('D12 leiste'):
                continue          # gemeinsame D12-Fussschlittenteile: eigene Datei, im Viewer verschoben
            if gr in grp: grp[gr].append(sh)
        d12_gemeinsam(cfg)
        d['d12_versatz_x'] = cfg['ausruestung']['fussschlitten']['fuss_x_mm'] - P['fussschlitten']['fuss_nenn_x_mm']
        for e in AUS['sonder']:
            grp['alu'].append(e['form']); grp['schraube'].append(e['schrauben'])
        d['aus_meshes'] = dict(alu=mesh(comp(grp['alu']), 0.4, 0.6), schrauben=mesh(comp(grp['schraube']), 0.8, 1.0),
                               sohle=mesh(comp(grp['sohle']), 0.5, 0.6))
        d['aus_rohre'] = [dict(info) for _, info, _ in AUS['rohre']]
        d['regler_meshes'] = dict(halter=mesh(comp([x for _, x in AUS['halter']])), schrauben=mesh(AUS['halter_schrauben'], 0.6, 0.8),
                                  regler=mesh(comp(AUS['regler']), 0.5, 0.6))
        d['ausruestung'] = cfg['ausruestung']
    d['propeller'] = dict(id=cfg['propeller'], nabe_z=cfg['rotor_nabe_z_mm'],
                          nabe_unten_z=cfg['rotor_unten']['nabe_z_mm'] if cfg['rotor_unten'] else None)
    propeller_mesh(cfg['propeller'])
    f = VO / (cfg['schluessel'] + '.js')
    f.write_text('D14_DATEN(' + json.dumps(d, separators=(',', ':')) + ');\n')
    return f.stat().st_size


# ----------------------------------------------------------------- Nativ
def nativ(cfg, T, AUS=None):
    import Import
    key = cfg['schluessel']
    D = A.newDocument('D14_' + key)
    lib = D.addObject('App::DocumentObjectGroup', 'Bauteile')
    asm = D.addObject('App::DocumentObjectGroup', 'Montage')
    def master(name, label, shape, farbe=None):
        o = D.addObject('Part::Feature', name); o.Label = label; o.Shape = shape; lib.addObject(o); o.Visibility = False
        return o
    def inst(m, name, pl):
        l = D.addObject('App::Link', name); l.setLink(m); l.Placement = pl; asm.addObject(l); return l
    eck = T['eck']
    mm = dict(
        V=master('Dreiecksverbinder', 'Dreiecksverbinder ' + key, T['conn']),
        VS=master('Verbinder_Schrauben', 'Verbinder Schrauben', T['conn_bolts']),
        VI=master('Verbinder_Isolierhuelsen', 'Verbinder Isolierhuelsen', T['conn_iso']),
        ML=master('Motortraeger_L', 'Motortraeger links', T['mount']),
        MR=master('Motortraeger_R', 'Motortraeger rechts (Spiegel)', K.spiegel_y(T['mount'])),
        MSL=master('Motortraeger_Schrauben_L', 'Motortraeger Schrauben L', T['mount_bolts']),
        MSR=master('Motortraeger_Schrauben_R', 'Motortraeger Schrauben R', K.spiegel_y(T['mount_bolts'])),
        MIL=master('Motortraeger_Iso_L', 'Motortraeger Isolierhuelsen L', T['mount_iso']),
        MIR=master('Motortraeger_Iso_R', 'Motortraeger Isolierhuelsen R', K.spiegel_y(T['mount_iso'])))
    ecken = ecken_instanzen(eck, T['eck_u'])
    for i, (s, b, iso) in enumerate(zip(ecken,
                                        [T['eck_bolts'], K.spiegel_y(T['eck_bolts']), K.spiegel_z(T['eck_u_bolts']), K.spiegel_z(K.spiegel_y(T['eck_u_bolts']))],
                                        [T['eck_iso'], K.spiegel_y(T['eck_iso']), K.spiegel_z(T['eck_u_iso']), K.spiegel_z(K.spiegel_y(T['eck_u_iso']))])):
        mm[f'E{i}'] = master(f'Eckknoten_{i}', f'Eckknoten {["V+ oben", "V- oben", "V+ unten", "V- unten"][i]}', s)
        mm[f'ES{i}'] = master(f'Eckknoten_Schrauben_{i}', f'Eckknoten Schrauben {i}', b)
        mm[f'EI{i}'] = master(f'Eckknoten_Iso_{i}', f'Eckknoten Isolierhuelsen {i}', iso)
    rl = armrohre_links(cfg)
    for k, r in enumerate(rl):
        mm[f'RL{k}'] = master(f'Auslegerrohr_L{k}', f'CFK-Auslegerrohr L{k}', r)
        mm[f'RR{k}'] = master(f'Auslegerrohr_R{k}', f'CFK-Auslegerrohr R{k}', K.spiegel_y(r))
    for i, m in enumerate(K.motor_huellen(cfg)):
        mm[f'ML{i}'] = master(f'Motorhuelle_L{i}', 'Motor-Bauraumreferenz MN1330', m)
        mm[f'MR{i}'] = master(f'Motorhuelle_R{i}', 'Motor-Bauraumreferenz MN1330', K.spiegel_y(m))
    for i, p in enumerate(K.rotor_huellen(cfg)):
        mm[f'PL{i}'] = master(f'Rotorhuelle_L{i}', 'Rotor-Umlaufhuelle', p)
        mm[f'PR{i}'] = master(f'Rotorhuelle_R{i}', 'Rotor-Umlaufhuelle', K.spiegel_y(p))
    rf = cfg['rahmen']
    for j in range(rf['paare']):
        phi = j * 360.0 / rf['paare']
        pl = A.Placement(V(0, 0, 0), A.Rotation(V(0, 0, 1), phi))
        for k, m in mm.items():
            inst(m, f'Paar{j + 1}_{m.Name}', pl)
    if AUS is not None:
        # Standard-Eckknoten an den Sonderecken entfernen (dort sitzen die Ecken mit Zusatzhuelsen)
        sonder = {(e['paar'], e['vminus'], e['unten']) for e in AUS['sonder']}
        for o in list(asm.Group):
            if o.TypeId == 'App::Link' and o.LinkedObject.Name.startswith('Eckknoten_'):
                j = int(o.Name.split('_')[0][4:]) - 1
                i = int(o.LinkedObject.Name.split('_')[-1])
                vm, un = i in (1, 3), i in (2, 3)
                if (j, vm, un) in sonder:
                    D.removeObject(o.Name)
        aus = D.addObject('App::DocumentObjectGroup', 'Ausruestung')
        def feat(name, label, shape):
            o = D.addObject('Part::Feature', name); o.Label = label; o.Shape = shape; aus.addObject(o)
        for k, (n, sh, g) in enumerate(AUS['teile']):
            feat(f'AUS_{k}', n, sh)
        for k, e in enumerate(AUS['sonder']):
            feat(f'AUS_Ecke_{k}', e['name'], e['form']); feat(f'AUS_Ecke_S_{k}', e['name'] + ' Schrauben', e['schrauben'])
            feat(f'AUS_Ecke_I_{k}', e['name'] + ' Isolierung', e['iso'])
        for k, (n, info, sh) in enumerate(AUS['rohre']):
            feat(f'AUS_Rohr_{k}', 'CFK ' + n, sh)
        rh = []
        for n, sh in AUS['halter']:
            rh.append(master(f'RH_{len(rh)}', n, sh))
        rh.append(master('RH_Schrauben', 'Reglerhalter Schrauben', AUS['halter_schrauben']))
        rh.append(master('RH_Iso', 'Reglerhalter Isolierung', AUS['halter_iso']))
        for i, rr in enumerate(AUS['regler']):
            rh.append(master(f'Regler_{i}', 'Regler-Bauraum V200A 24S 146x74x39,5', rr))
        for j in range(rf['paare']):
            phi = j * 360.0 / rf['paare']
            for m in rh:
                inst(m, f'Paar{j + 1}_L_{m.Name}', A.Placement(V(0, 0, 0), A.Rotation(V(0, 0, 1), phi)))
                mr = master(f'{m.Name}_R{j}', m.Label + ' (rechts)', K.spiegel_y(m.Shape)) if j == 0 else D.getObject(f'{m.Name}_R0')
                inst(mr, f'Paar{j + 1}_R_{m.Name}', A.Placement(V(0, 0, 0), A.Rotation(V(0, 0, 1), phi)))
    for i, (name, s, _) in enumerate(rahmenrohre(cfg)):
        o = D.addObject('Part::Feature', f'Rahmen_{name}_{i}'); o.Shape = s; asm.addObject(o)
    pg = D.addObject('App::DocumentObjectGroup', 'Propeller_D13_Bildreferenz')
    for i, (n, sh) in enumerate(propeller_instanzen(cfg)):
        o = D.addObject('Part::Feature', f'Propeller_{i}'); o.Label = n; o.Shape = sh; pg.addObject(o)
    D.recompute()
    fc = NO / f'{key}.FCStd'; D.saveAs(str(fc))
    objs = [o for o in asm.Group] + ([o for o in D.getObject('Ausruestung').Group] if AUS is not None else [])
    shapes = [o.Shape.copy() for o in objs if 'Rotorhuelle' not in o.Name]
    comp(shapes).exportStep(str(NO / f'{key}.step'))
    A.closeDocument(D.Name)
    return fc


# ------------------------------------------------------------------ Lauf
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--konfig', action='append')
    ap.add_argument('--nativ', action='store_true')
    ap.add_argument('--standard-nativ', action='store_true', help='FCStd/STEP fuer alle Bauweisen x Varianten am Standardpropeller')
    ap.add_argument('--ohne-viewer', action='store_true')
    ap.add_argument('--nur-viewer', action='store_true', help='nur Viewerdaten neu schreiben (Pruefung bleibt unveraendert)')
    args = ap.parse_args()
    cfgs = AU.alle()
    std = P['standard']['propeller']
    if args.konfig:
        cfgs = [c for c in cfgs if c['schluessel'] in args.konfig]
    berichte = []
    alt = {}
    pf = O / 'Pruefung.json'
    if pf.exists() and args.konfig:
        alt = {r['schluessel']: r for r in json.loads(pf.read_text())['konfigurationen']}
    for c in cfgs:
        t0 = time.time()
        try:
            T = baue(c)
        except Exception as e:
            r = dict(schluessel=c['schluessel'], bauweise=c['bauweise'], propeller=c['propeller'], variante=c['variante'],
                     geometrie_signatur=SIG, fehler=str(e)[:400], kollisionsfrei=False, kollisionspruefungen=0)
            berichte.append(r); alt[c['schluessel']] = r
            print(f"{c['schluessel']:28s} FEHLER {e}", flush=True)
            continue
        if args.nur_viewer:
            viewerdaten(c, T, [], AB.baue(c)); print(c['schluessel'], 'Viewer', flush=True); continue
        tests, gueltig, ok = pruefe(c, T)
        try:
            AUS = AB.baue(c)
            tests_a, gueltig_a, n_neu = AB.pruefe(c, T, AUS, alt_global(c, T, AUS))
        except Exception as e:
            AUS = None; tests_a = [dict(pruefung='Ausruestung Aufbau', ueberdeckung_mm3=-1, bestanden=False, fehler=str(e)[:300])]
            gueltig_a = False; n_neu = 0
            print('   Ausruestung FEHLER', e, flush=True)
        tests = tests + tests_a
        ok = ok and gueltig_a and all(x['bestanden'] for x in tests_a)
        gueltig['Ausruestung'] = (gueltig_a, n_neu)
        m = massen(c, T)
        if AUS: m['ausruestung'] = massen_ausruestung(c, AUS, T['eck'].Volume * ALU)
        size = None if args.ohne_viewer else viewerdaten(c, T, tests, AUS)
        fc = None
        if args.nativ or (args.standard_nativ and c['propeller'] == std):
            fc = str(nativ(c, T, AUS).relative_to(H))
        fehl = [x for x in tests if not x['bestanden']]
        r = dict(schluessel=c['schluessel'], bauweise=c['bauweise'], propeller=c['propeller'], variante=c['variante'],
                 geometrie_signatur=SIG, volumenkoerper=gueltig, kollisionspruefungen=len(tests),
                 kollisionen=fehl, kollisionsfrei=ok, min_ueberdeckung_info=max([x['ueberdeckung_mm3'] for x in tests] + [0]),
                 auslegung_pruefungen=c['pruefungen'], statik=c['statik'], statik_ausruestung=c['statik_ausruestung'], massen=m, viewer_bytes=size, nativ=fc,
                 cache=T['cache'], zeit_s=round(time.time() - t0, 1))
        berichte.append(r); alt[c['schluessel']] = r
        print(f"{c['schluessel']:28s} kollisionsfrei={ok} tests={len(tests)} fehl={len(fehl)} "
              f"V={m['verbinder_je_stueck_kg']:.3f} M={m['motortraeger_je_stueck_kg']:.3f} kg  {r['zeit_s']}s", flush=True)
        for x in fehl[:6]:
            print('   ', x, flush=True)
    if args.nur_viewer:
        return
    alle = list(alt.values()) if args.konfig else berichte
    alle.sort(key=lambda r: r['schluessel'])
    pf.write_text(json.dumps(dict(revision=P['revision'], geometrie_signatur=SIG, anzahl=len(alle),
                                  alle_kollisionsfrei=all(r['kollisionsfrei'] for r in alle),
                                  toleranz_mm3=TOL, konfigurationen=alle, produktionsfreigabe=False),
                             indent=1, ensure_ascii=False))
    # Index fuer den Viewer
    idx = dict(bauweisen={k: v['label'] for k, v in P['bauweisen'].items()},
               propeller=[dict(id=p['id'], label=p['label']) for p in P['propeller']],
               varianten={k: v['titel'] for k, v in P['varianten'].items()}, standard=P['standard'],
               konfigurationen={})
    aus = {c['schluessel']: c for c in AU.alle()}
    for r in alle:
        if 'fehler' in r:
            continue
        c = aus[r['schluessel']]
        idx['konfigurationen'][r['schluessel']] = dict(
            R=c['motorradius_mm'], R_quelle=c['motorradius_quelle'], Lr=c['arm']['Lr'], ce=c['arm']['ce'],
            gamma=c['arm']['gamma_grad'], pruef=c['pruefungen'], kollisionsfrei=r['kollisionsfrei'],
            tests=r['kollisionspruefungen'], massen=r['massen'], statik=c['statik'], rotor_unten=c['rotor_unten'],
            zuschnitt=c['zuschnitt'], rotor_oben_z=c['rotor_oben_z_mm'], ausruestung=c['ausruestung'],
            statik_ausruestung=c['statik_ausruestung'])
    (VO / 'index.js').write_text('D14_INDEX(' + json.dumps(idx, separators=(',', ':'), ensure_ascii=False) + ');\n')


if __name__ == '__main__':
    main()
