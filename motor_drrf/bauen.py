"""DRRF-K01: Konzept-CAD des Dual-Rotor-Radialfluss-Motors (Ringwicklung) aus Ausgabe/Auslegung.json.

Aufruf (FreeCAD-AppImage):
  FC=~/Programme/squashfs-root/usr; LD_LIBRARY_PATH=$FC/lib $FC/bin/python motor_drrf/bauen.py
Erzeugt Ausgabe/DRRF_K01.FCStd, Ausgabe/DRRF_K01.step, Ausgabe/viewer.js (Netze fuer Projekt.html) und Ausgabe/Pruefung.json.
Koordinaten: z nach oben, z = 0 ist die Auflageflaeche auf dem D14-Motortraegerflansch (dort z = 88 mm im Fahrzeug).
"""
from pathlib import Path
import sys, os, json, math, base64, array
H = Path(__file__).resolve().parent
FC = os.path.expanduser('~/Programme/squashfs-root/usr')
sys.path += [FC + '/lib', FC + '/Mod']
import FreeCAD as A
import Part, MeshPart

V = A.Vector
P = json.loads((H / 'parameter.json').read_text())
AUS = json.loads((H / 'Ausgabe' / 'Auslegung.json').read_text())
D = AUS['topologien'][AUS['gewaehlt']]
GF, MA = P['geometrie_fest'], P['material']
R = D['radien_mm']
NS, NP = GF['nuten'], GF['pole']
L = D['aktive_laenge_mm']; WK = GF['wickelkopf_mm']

# ------------------------------------------------------------- Hoehen
z_boden = GF['boden_mm']                                   # Statortraeger-Boden 0..6
z_rotor_u = z_boden + GF['spalt_boden_mm']                 # Unterkante Rotor
z_akt0 = z_rotor_u + 1.0 + WK                              # aktive Zone
z_akt1 = z_akt0 + L
z_deckel0 = z_akt1 + WK + 1.0                              # Rotordeckel
z_deckel1 = z_deckel0 + GF['deckel_mm']
z_top = z_deckel1 + GF['nabe_aufbau_mm']
z_mag0, z_mag1 = z_akt0 - GF['magnet_ueberstand_mm'], z_akt1 + GF['magnet_ueberstand_mm']


def ring(ri, ro, z0, z1):
    return Part.makeCylinder(ro, z1 - z0, V(0, 0, z0)).cut(Part.makeCylinder(ri, z1 - z0 + 2, V(0, 0, z0 - 1)))


def sektor(ri, ro, z0, z1, mitte_grad, breite_grad):
    s = ring(ri, ro, z0, z1)
    a0 = math.radians(mitte_grad - breite_grad / 2); a1 = math.radians(mitte_grad + breite_grad / 2)
    big = ro * 3
    keil = Part.makePolygon([V(0, 0, z0 - 1), V(big * math.cos(a0), big * math.sin(a0), z0 - 1),
                             V(big * math.cos((a0 + a1) / 2) * 1.5, big * math.sin((a0 + a1) / 2) * 1.5, z0 - 1),
                             V(big * math.cos(a1), big * math.sin(a1), z0 - 1), V(0, 0, z0 - 1)])
    keil = Part.Face(keil).extrude(V(0, 0, z1 - z0 + 2))
    return s.common(keil)


def kasten(r0, r1, b, z0, z1, winkel_grad):
    """Quader radial r0..r1, tangential +-b/2, axial z0..z1, um z gedreht."""
    k = Part.makeBox(r1 - r0, b, z1 - z0, V(r0, -b / 2, z0))
    k.rotate(V(0, 0, 0), V(0, 0, 1), winkel_grad)
    return k


def vereinige(teile):
    s = teile[0]
    if len(teile) > 1:
        s = s.fuse(teile[1:])
    try:
        s = s.removeSplitter()
    except Exception:
        pass
    return s


teile = {}      # name -> (form, material, farbe, rotor?)
tp = 360.0 / NS; pp = 360.0 / NP
# ------------------------------------------------------------- Stator (feststehend)
r_si, r_so = R['stator']; r_ji, r_jo = R['joch']
w_to, w_ti = D['zahnbreite_mm'], D.get('zahnbreite_mm')
sh = GF['zahnschuh_hoehe_mm']; schlitz = GF['nutschlitz_mm']
w_ti = AUS['topologien'][AUS['gewaehlt']].get('zahnbreite_innen_mm', None) or w_to * r_si / r_so * 0.98
blech = [ring(r_ji, r_jo, z_akt0, z_akt1)]
for k in range(NS):
    w = k * tp                                               # Zahnmitten bei k*tp, Nuten bei (k+0.5)*tp
    blech.append(kasten(r_jo - 0.5, r_so - sh, w_to, z_akt0, z_akt1, w))
    blech.append(sektor(r_so - sh, r_so, z_akt0, z_akt1, w, tp - math.degrees(schlitz / r_so)))
    blech.append(kasten(r_si + sh, r_ji + 0.5, w_ti, z_akt0, z_akt1, w))
    blech.append(sektor(r_si, r_si + sh, z_akt0, z_akt1, w, tp - math.degrees(schlitz / r_si)))
teile['Statorblechpaket'] = (vereinige(blech), 'Elektroblech NO10', [0.55, 0.58, 0.62], False)
# Ringspulen um das Joch, je eine Nut aussen und innen
b_sp = min(2 * math.pi * (r_jo + 1) / NS - w_to, 2 * math.pi * (r_si + sh) / NS - w_ti) - 0.6
dick = 4.0
spulen = []
for k in range(NS):
    w = (k + 0.5) * tp
    a_ = kasten(r_jo + 0.3, r_so - sh - 0.3, b_sp, z_akt0 - dick, z_akt1 + dick, w)
    i_ = kasten(r_si + sh + 0.3, r_ji - 0.3, b_sp, z_akt0 - dick, z_akt1 + dick, w)
    o_ = kasten(r_ji - 0.3 - (r_ji - r_si - sh - 0.6), r_so - sh - 0.3, b_sp, z_akt1 + 0.3, z_akt1 + dick, w)
    u_ = kasten(r_ji - 0.3 - (r_ji - r_si - sh - 0.6), r_so - sh - 0.3, b_sp, z_akt0 - dick, z_akt0 - 0.3, w)
    spulen.append(vereinige([a_, i_, o_, u_]))
teile['Ringspulen (36)'] = (Part.makeCompound(spulen), 'Kupfer, Flachdraht, vergossen', [0.80, 0.45, 0.20], False)
# Statortraeger: Boden mit Kuehlfenstern, Tragring und Stuetzen unter dem Joch an den Zahnpositionen
r_mo = R['rueckschluss_aussen'][1]
boden = Part.makeCylinder(r_mo - 3.0, z_boden, V(0, 0, 0))
fenster = []
for k in range(12):
    w = math.radians(k * 30 + 15)
    for (ra, rb) in ((28.0, 40.0),):
        fenster.append(sektor(ra, rb, -1, z_boden + 1, k * 30 + 15, 18))
for k in range(NS):                                           # Fenster unter den Spulen (Luft durch die Nuten)
    fenster.append(sektor(r_si + 1.0, r_so - 1.0, -1, z_boden + 1, (k + 0.5) * tp, tp * 0.45))
boden = boden.cut(fenster)
r_ach = 10.0
boden = boden.cut([Part.makeCylinder(3.3, z_boden + 2, V(25 * math.cos(math.radians(45 + 90 * k)), 25 * math.sin(math.radians(45 + 90 * k)), -1)) for k in range(4)])
zentrier = Part.makeCylinder(7.9, 4.0, V(0, 0, -4.0))
stuetzen = [kasten(r_ji + 0.2, r_jo - 0.2, w_to - 1.0, z_boden - 0.1, z_akt0, k * tp) for k in range(0, NS, 3)]
traeger = vereinige([boden, zentrier] + stuetzen).cut(Part.makeCylinder(r_ach, 20, V(0, 0, -5)))   # Bohrung fuer die eingepresste Achse
teile['Statortraeger'] = (traeger, 'Alu 7075-T6', [0.72, 0.75, 0.78], False)
achse = Part.makeCylinder(r_ach, z_top - 1.0, V(0, 0, 0)).cut(Part.makeCylinder(6.0, z_top + 2, V(0, 0, -1)))
teile['Achse (feststehend)'] = (achse, 'Stahl 42CrMo4, hohl', [0.35, 0.36, 0.40], False)
# Lager 6004: 20 x 42 x 12
lager = []
z_l2 = z_deckel1 - 12.0; z_l1 = z_l2 - 14.0
for z0 in (z_l1, z_l2):
    lager.append(ring(10.0, 21.0, z0, z0 + 12.0))
teile['Lager 2 x 6004'] = (Part.makeCompound(lager), 'Waelzlager 6004-2RS', [0.62, 0.64, 0.68], False)
# ------------------------------------------------------------- Rotor (drehend)
rbo = R['rueckschluss_aussen']; rmo = R['magnet_aussen']; rmi = R['magnet_innen']; rbi = R['rueckschluss_innen']
teile['Rueckschluss aussen'] = (ring(rbo[0], rbo[1], z_mag0, z_mag1), 'Stahl 1.0503', [0.30, 0.31, 0.33], True)
teile['Rueckschluss innen'] = (ring(rbi[0], rbi[1], z_mag0, z_mag1), 'Stahl 1.0503', [0.30, 0.31, 0.33], True)
mag_a, mag_i = [], []
for k in range(NP):
    w = (k + 0.5) * pp
    mag_a.append(sektor(rmo[0], rmo[1], z_mag0, z_mag1, w, pp * GF['polbedeckung']))
    mag_i.append(sektor(rmi[0], rmi[1], z_mag0, z_mag1, w, pp * GF['polbedeckung']))
teile['Magnete aussen (42)'] = (Part.makeCompound(mag_a), 'NdFeB N52SH, segmentiert', [0.75, 0.15, 0.15], True)
teile['Magnete innen (42)'] = (Part.makeCompound(mag_i), 'NdFeB N52SH, segmentiert', [0.75, 0.15, 0.15], True)
# Rotorglocke: Deckel mit Lueftungsfenstern, Aussen- und Innenhuelse ausserhalb der Aktivzone, Nabe mit Lagersitz
hu_a = [ring(rbo[0], rbo[1], z_rotor_u, z_mag0), ring(rbo[0], rbo[1], z_mag1, z_deckel0)]
r_ih = rbi[0] - 2.0
hu_i = [ring(r_ih, rbi[0], z_rotor_u, z_deckel0), ring(rbi[0], rbi[1], z_mag1, z_deckel0)]
deckel = ring(21.0, rbo[1], z_deckel0, z_deckel1)
deckel = deckel.cut([sektor(r_si + 1.5, r_so - 1.5, z_deckel0 - 1, z_deckel1 + 1, k * 30 + 15, 20) for k in range(12)])
deckel = deckel.cut([sektor(26.0, r_ih - 2.0, z_deckel0 - 1, z_deckel1 + 1, k * 60 + 30, 30) for k in range(6)])
nabe = ring(21.0, 25.0, z_l1 - 2.0, z_deckel1)
schulter = ring(17.0, 25.0, z_l1 - 2.0, z_l1)
flansch = ring(16.5, 30.0, z_deckel1, z_top)                    # Propelleraufnahme, innen Platz fuer die Achsmutter
glocke = vereinige(hu_a + hu_i + [deckel, nabe, schulter, flansch])
loecher = [Part.makeCylinder(2.75, z_top - z_deckel0 + 2, V(22 * math.cos(math.radians(60 * k)), 22 * math.sin(math.radians(60 * k)), z_deckel0 - 1)) for k in range(6)]
glocke = glocke.cut(loecher)
teile['Rotorglocke'] = (glocke, 'Alu 7075-T6', [0.78, 0.80, 0.83], True)
mutter = ring(r_ach, 15.0, z_deckel1 + 0.5, z_top - 0.5)          # Wellenmutter M20x1 auf der Achse
teile['Achsmutter (Lager-Vorspannung)'] = (mutter, 'Stahl', [0.35, 0.36, 0.40], False)
schrauben = []
for k in range(4):
    a = math.radians(45 + 90 * k); x, y = 25 * math.cos(a), 25 * math.sin(a)
    schrauben.append(Part.makeCylinder(5.0, 4.0, V(x, y, z_boden)).fuse(Part.makeCylinder(3.0, 14.0, V(x, y, z_boden - 14.0 + 0.0))))
teile['Befestigung 4 x M6 (D14-Lochkreis 50)'] = (Part.makeCompound(schrauben), 'Stahl 12.9', [0.3, 0.3, 0.32], False)

# ------------------------------------------------------------- Pruefung: Ueberschneidungen, Luftspalte, Massen
dichte = {'Elektroblech NO10': MA['rho_blech'], 'Kupfer, Flachdraht, vergossen': MA['rho_kupfer'] * 0.62 + MA['rho_verguss'] * 0.38,   # Kupferanteil im Spulenquerschnitt (Annahme)
          'Alu 7075-T6': MA['rho_alu'], 'Stahl 42CrMo4, hohl': MA['rho_stahl'], 'Waelzlager 6004-2RS': 0.069 / (math.pi * (21 ** 2 - 10 ** 2) * 12),
          'Stahl 1.0503': MA['rho_stahl'], 'NdFeB N52SH, segmentiert': MA['rho_magnet'], 'Stahl': MA['rho_stahl'], 'Stahl 12.9': MA['rho_stahl']}
namen = list(teile)
tests = []
for i, a in enumerate(namen):
    for b in namen[i + 1:]:
        sa, sb = teile[a][0], teile[b][0]
        if not sa.BoundBox.intersect(sb.BoundBox):
            continue
        if {a, b} <= {'Befestigung 4 x M6 (D14-Lochkreis 50)', 'Statortraeger'}:
            continue                                    # Schraubenkopf liegt auf, Schaft ragt in den D14-Flansch
        v = sa.common(sb).Volume
        tests.append(dict(paar=f'{a} / {b}', ueberdeckung_mm3=round(v, 3), bestanden=v <= 1e-3))
# minimaler Abstand drehend <-> feststehend
rot = Part.makeCompound([teile[n][0] for n in namen if teile[n][3] and 'Magnet' not in n] + [teile[n][0] for n in namen if 'Magnet' in n])
fest = [n for n in namen if not teile[n][3] and not n.startswith('Lager') and not n.startswith('Befestigung')]
spalte = {}
for n in fest:
    if n == 'Achse (feststehend)':
        continue
    spalte[n] = round(rot.distToShape(teile[n][0])[0], 3)
massen = {n: round(teile[n][0].Volume * dichte[teile[n][1]], 4) for n in namen}
gueltig = {n: teile[n][0].isValid() for n in namen}
pruef = dict(revision=P['revision'], topologie=AUS['gewaehlt'], kollisionsfrei=all(t['bestanden'] for t in tests), tests=tests,
             min_spalt_rotor_stator_mm=spalte, massen_cad_kg=massen, masse_cad_gesamt_kg=round(sum(massen.values()), 3),
             masse_auslegung_kg=D['masse_kg'], gueltig=gueltig,
             hoehen_mm=dict(boden=z_boden, rotor_unterkante=z_rotor_u, aktiv=[z_akt0, z_akt1], deckel=[z_deckel0, z_deckel1], oberkante=z_top),
             hinweis='Spulen als Kupfer-Verguss-Mischdichte; Lager mit Katalogmasse 69 g')
(H / 'Ausgabe' / 'Pruefung.json').write_text(json.dumps(pruef, indent=1, ensure_ascii=False))
print('kollisionsfrei', pruef['kollisionsfrei'], 'Masse CAD', pruef['masse_cad_gesamt_kg'], 'kg; Auslegung', D['masse_kg'])
print('Spalte', spalte)
for t in tests:
    if not t['bestanden']: print('  ', t)

# ------------------------------------------------------------- Native Datei, STEP, Viewernetze
doc = A.newDocument('DRRF_K01')
objs = []
for n, (s, mat, farbe, dreh) in teile.items():
    o = doc.addObject('Part::Feature', ''.join(c if c.isalnum() else '_' for c in n)[:40]); o.Label = n; o.Shape = s
    objs.append(o)
doc.recompute()
doc.saveAs(str(H / 'Ausgabe' / 'DRRF_K01.FCStd'))
import Import
Import.export(objs, str(H / 'Ausgabe' / 'DRRF_K01.step'))


def netz(s, lin=0.15, ang=0.35):
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=lin, AngularDeflection=ang)
    pts = [p for f in m.Facets for p in f.Points]
    v = array.array('f', [c for p in pts for c in p])
    return base64.b64encode(v.tobytes()).decode()


vd = dict(revision=P['revision'], topologie=AUS['gewaehlt'], hoehen=pruef['hoehen_mm'],
          teile=[dict(name=n, material=mat, farbe=farbe, rotor=dreh, masse_kg=massen[n], netz=netz(s)) for n, (s, mat, farbe, dreh) in teile.items()],
          auslegung=D, pruefung=dict(kollisionsfrei=pruef['kollisionsfrei'], spalte=spalte, masse=pruef['masse_cad_gesamt_kg']))
(H / 'Ausgabe' / 'viewer.js').write_text('DRRF_DATEN(' + json.dumps(vd, separators=(',', ':'), ensure_ascii=False) + ');\n')
print('geschrieben:', ', '.join(p.name for p in (H / 'Ausgabe').iterdir()))
