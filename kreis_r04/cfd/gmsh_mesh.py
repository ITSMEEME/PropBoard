#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): koerperangepasstes Gmsh-Tetraedernetz des 45-Grad-Sektors.

Je Ebene ein Fluegel (aussere Kontur, interpolierende Splines, 0.8 mm Hinterkante),
vereinfachte stationaere C-Fuehrungsprofile (innen; mit Aussenring zusaetzlich aussen),
zwei MRF-Zellzonen, periodische Sektorflaechen bei 0 und 45 Grad. Meter.

    python gmsh_mesh.py free_tet_c_u40 --variant free [--offset 0] [--level c]

Die Netzpruefung hier nutzt Gmsh-Qualitaetsmasse (minSICN, Volumen > 0, periodische
Knotenzuordnung); sie ersetzt OpenFOAM checkMesh nicht.
"""
import argparse, json, math, sys, time
from pathlib import Path
import gmsh
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import profil

SECTOR = math.pi/4
R_IN, R_OUT, Z_HALF = .03, 1.5, 1.2
ZONE_R, ZONE_DZ, ZONE_GAP = (.06, .95), .08, .04
LEVELS = {'h': (.0015, .0004, .045), 'c': (.004, .0006, .09), 'm': (.0028, .00045, .07), 'f': (.002, .0003, .05)}  # Fluegel, Hinterkante, Fernfeld


def wing(level_z, direction, theta, n=120):
    """Volumen eines Fluegels; direction +1 = Umlauf in +theta (untere Ebene), -1 = obere Ebene."""
    occ = gmsh.model.occ
    pts = profil.outline(n)
    # outline(): oben Nase->HK, unten HK->Nase; Spline HK_oben -> Nase -> HK_unten.
    upper = pts[:n+1]; lower = pts[n+1:]
    seq = list(reversed(upper))+list(reversed(lower))
    tags = [occ.addPoint(profil.R_WING[0]/1000, direction*x/1000, z/1000) for x, z in seq]
    spline = occ.addSpline(tags)
    te = occ.addLine(tags[-1], tags[0])
    face = occ.addPlaneSurface([occ.addCurveLoop([spline, te])])
    vol = occ.extrude([(2, face)], profil.SPAN/1000, 0, 0)
    vol = [v for v in vol if v[0] == 3]
    occ.rotate(vol, 0, 0, 0, 1, 0, 0, direction*math.radians(profil.PITCH_DEG))   # Nase nach oben
    occ.translate(vol, 0, 0, level_z)
    occ.rotate(vol, 0, 0, 0, 0, 0, 1, theta)
    return vol


def guide(level_z, outer):
    """Vereinfachtes C-Profil (Rueckwand 6 mm, zwei 8-mm-Flansche, Hoehe 60 mm) als um 45 Grad revolvierter Querschnitt."""
    occ = gmsh.model.occ; r = (profil.R_GUIDE[1] if outer else profil.R_GUIDE[0])/1000; s = 1 if outer else -1
    z0, z1, f = level_z-.03, level_z+.03, .008
    # Querschnitt in der x-z-Ebene, Oeffnung zur Fluegelseite
    rs = [r-s*.012, r+s*.016, r+s*.016, r-s*.012, r-s*.012, r+s*.010, r+s*.010, r-s*.012]
    zs = [z0, z0, z1, z1, z1-f, z1-f, z0+f, z0+f]
    pts = [occ.addPoint(x, 0, z) for x, z in zip(rs, zs)]
    loop = occ.addCurveLoop([occ.addLine(pts[i], pts[(i+1) % 8]) for i in range(8)])
    out = occ.revolve([(2, occ.addPlaneSurface([loop]))], 0, 0, 0, 0, 0, 1, SECTOR)
    return [v for v in out if v[0] == 3]


def build(name, variant, offset_deg, level, out_dir):
    h_wing, h_te, h_far = LEVELS[level]
    gmsh.model.add(name); occ = gmsh.model.occ
    dom = occ.cut([(3, occ.addCylinder(0, 0, -Z_HALF, 0, 0, 2*Z_HALF, R_OUT, angle=SECTOR))],
                  [(3, occ.addCylinder(0, 0, -Z_HALF, 0, 0, 2*Z_HALF, R_IN, angle=SECTOR))])[0]
    zones = []
    for z, sgn in ((profil.LEVELS[0]/1000, -1), (profil.LEVELS[1]/1000, 1)):
        z0, z1 = (z-ZONE_DZ, -ZONE_GAP) if sgn < 0 else (ZONE_GAP, z+ZONE_DZ)
        zones.append(occ.cut([(3, occ.addCylinder(0, 0, z0, 0, 0, z1-z0, ZONE_R[1], angle=SECTOR))],
                             [(3, occ.addCylinder(0, 0, z0, 0, 0, z1-z0, ZONE_R[0], angle=SECTOR))])[0])
    centre = SECTOR/2
    th_lo, th_up = (centre, centre) if offset_deg == 0 else (centre-math.radians(offset_deg)/2, centre+math.radians(offset_deg)/2)
    wings = {'wing_lower': wing(profil.LEVELS[0]/1000, 1, th_lo), 'wing_upper': wing(profil.LEVELS[1]/1000, -1, th_up)}
    guides = []
    for z in profil.LEVELS:
        guides += guide(z/1000, False)
        if variant == 'ring':guides += guide(z/1000, True)
    # An der Wurzel liegen die Sehnenecken nur ~1 Grad innerhalb der Sektorgrenze (bei Winkelversatz
    # darueber hinaus). Nachbarfluegel (+-45 Grad) werden mitgeschnitten, damit die Geometrie periodisch bleibt.
    for k in list(wings):
        for sgn in (-1, 1):
            cp = occ.copy(wings[k]); occ.rotate(cp, 0, 0, 0, 0, 0, 1, sgn*SECTOR); wings[k] = wings[k]+cp
    solids = [t for v in wings.values() for t in v]+guides
    occ.synchronize()
    wing_bb = {k: [gmsh.model.getBoundingBox(*t) for t in v] for k, v in wings.items()}
    guide_bb = [gmsh.model.getBoundingBox(*g) for g in guides]
    fluid = occ.cut(dom, solids, removeTool=False)[0]
    zone_cut = [occ.cut(zz, solids, removeTool=False)[0] for zz in zones]
    occ.remove(solids, recursive=True)
    frag, fmap = occ.fragment(fluid, [t for zc in zone_cut for t in zc])
    occ.synchronize()
    zone_vols = [[t[1] for t in fmap[len(fluid)+i]] for i in range(len(zone_cut))]
    zone_vols = [sorted(set(v)) for v in zone_vols]
    all_vols = [t for d, t in gmsh.model.getEntities(3)]
    stator = [v for v in all_vols if v not in zone_vols[0]+zone_vols[1]]
    # Flaechen zuordnen: Koerperflaechen ueber die vorab gespeicherten Koerper-Hüllquader,
    # Domaenenraender ueber Lage. Toleranzen beruecksichtigen die OCC-Huellquadervergroesserung.
    groups = {k: [] for k in ('wing_lower', 'wing_upper', 'guides', 'cyclic_0', 'cyclic_45', 'outer', 'inner', 'top', 'bottom')}
    tol = 1e-5
    boundary = {t for d, t in gmsh.model.getBoundary([(3, v) for v in all_vols], oriented=False, combined=True)}
    inside = lambda bb, box: all(box[i]-1e-4 <= bb[i] for i in range(3)) and all(bb[i] <= box[i]+1e-4 for i in range(3, 6))
    for s in boundary:
        bb = gmsh.model.getBoundingBox(2, s); x0, y0, z0, x1, y1, z1 = bb
        if abs(z0-z1) < tol and abs(z0-Z_HALF) < tol:groups['top'].append(s)
        elif abs(z0-z1) < tol and abs(z0+Z_HALF) < tol:groups['bottom'].append(s)
        elif abs(y0) < tol and abs(y1) < tol:groups['cyclic_0'].append(s)
        elif _planar_at(s, SECTOR):groups['cyclic_45'].append(s)
        elif abs(x1-R_OUT) < tol and abs(z0+Z_HALF) < tol and abs(z1-Z_HALF) < tol:groups['outer'].append(s)
        elif x1 < R_IN+tol:groups['inner'].append(s)
        elif any(inside(bb, w) for w in wing_bb['wing_lower']):groups['wing_lower'].append(s)
        elif any(inside(bb, w) for w in wing_bb['wing_upper']):groups['wing_upper'].append(s)
        elif any(inside(bb, g) for g in guide_bb):groups['guides'].append(s)
        else:raise RuntimeError(f'Flaeche {s} nicht zuordenbar: {bb}')
    # Periodizitaet: 45-Grad-Seite ist Abbild der 0-Grad-Seite
    ca, sa = math.cos(SECTOR), math.sin(SECTOR)
    affine = [ca, -sa, 0, 0, sa, ca, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    key = lambda t: (round(gmsh.model.getBoundingBox(2, t)[2], 4), round(gmsh.model.occ.getMass(2, t), 6))
    for k in ('cyclic_0', 'cyclic_45'):groups[k].sort(key=key)
    gmsh.model.mesh.setPeriodic(2, groups['cyclic_45'], groups['cyclic_0'], affine)
    for k, v in groups.items():
        if v:gmsh.model.addPhysicalGroup(2, v, name=k)
    gmsh.model.addPhysicalGroup(3, stator, name='stator')
    gmsh.model.addPhysicalGroup(3, zone_vols[0], name='MRF_lower')
    gmsh.model.addPhysicalGroup(3, zone_vols[1], name='MRF_upper')
    # Groessenfelder: Abstand zu Fluegeln und Hinterkanten
    wing_surf = groups['wing_lower']+groups['wing_upper']
    te_curves = [c for s in wing_surf for c in _te_curves(s)]
    f = gmsh.model.mesh.field
    d1 = f.add('Distance'); f.setNumbers(d1, 'SurfacesList', wing_surf+groups['guides']); f.setNumber(d1, 'Sampling', 60)
    t1 = f.add('Threshold'); f.setNumber(t1, 'InField', d1)
    for k, v in (('SizeMin', h_wing), ('SizeMax', h_far), ('DistMin', .004), ('DistMax', .45)):f.setNumber(t1, k, v)
    fields = [t1]
    if te_curves:
        d2 = f.add('Distance'); f.setNumbers(d2, 'CurvesList', te_curves); f.setNumber(d2, 'Sampling', 400)
        t2 = f.add('Threshold'); f.setNumber(t2, 'InField', d2)
        for k, v in (('SizeMin', h_te), ('SizeMax', h_far), ('DistMin', .0015), ('DistMax', .08)):f.setNumber(t2, k, v)
        fields.append(t2)
    mn = f.add('Min'); f.setNumbers(mn, 'FieldsList', fields); f.setAsBackgroundMesh(mn)
    for k, v in (('Mesh.MeshSizeExtendFromBoundary', 0), ('Mesh.MeshSizeFromPoints', 0), ('Mesh.MeshSizeFromCurvature', 24),
                 ('Mesh.MeshSizeMin', h_te*.5), ('Mesh.MeshSizeMax', h_far), ('Mesh.Algorithm', 6), ('Mesh.Algorithm3D', 10),
                 ('Mesh.Optimize', 1), ('Mesh.OptimizeNetgen', 0), ('Mesh.MshFileVersion', 2.2), ('Mesh.Binary', 0)):
        gmsh.option.setNumber(k, v)
    t0 = time.time(); gmsh.model.mesh.generate(3); t_mesh = time.time()-t0
    return groups, report(name, variant, offset_deg, level, groups, t_mesh, out_dir)


def _planar_at(s, angle):
    """Ebene Flaeche, deren Punkte alle in der Ebene theta = angle liegen."""
    if gmsh.model.getType(2, s) != 'Plane':return False
    u = gmsh.model.getParametrizationBounds(2, s)
    pts = gmsh.model.getValue(2, s, [u[0][0], u[0][1], u[1][0], u[1][1], (u[0][0]+u[1][0])/2, (u[0][1]+u[1][1])/2])
    return all(abs(-math.sin(angle)*pts[i]+math.cos(angle)*pts[i+1]) < 1e-5 for i in range(0, len(pts), 3))


def _te_curves(s):
    """Kurze gerade Kanten an Fluegelflaechen (Hinterkante, 0.8 mm) und lange Spannweitenkanten der HK-Flaeche."""
    out = []
    for d, c in gmsh.model.getBoundary([(2, s)], oriented=False):
        x0, y0, z0, x1, y1, z1 = gmsh.model.getBoundingBox(1, abs(c))
        if math.dist((x0, y0, z0), (x1, y1, z1)) > .5 and gmsh.model.getType(1, abs(c)) == 'Line':out.append(abs(c))
    return out


def report(name, variant, offset_deg, level, groups, t_mesh, out_dir):
    types, tags, _ = gmsh.model.mesh.getElements(3)
    n_tet = sum(len(t) for ty, t in zip(types, tags) if ty == 4)
    other = sum(len(t) for ty, t in zip(types, tags) if ty != 4)
    all_tags = [int(t) for ty, tg in zip(types, tags) if ty == 4 for t in tg]
    sicn = gmsh.model.mesh.getElementQualities(all_tags, 'minSICN')
    vol = gmsh.model.mesh.getElementQualities(all_tags, 'volume')
    srt = sorted(sicn)
    nodes_0 = len(gmsh.model.mesh.getNodes(2, -1)[0])
    per_ok = True
    try:
        for s in groups['cyclic_45']:
            tm, nt, nm, aff = gmsh.model.mesh.getPeriodicNodes(2, s, includeHighOrderNodes=False)
            per_ok &= len(nt) > 0 and len(nt) == len(nm)
    except Exception:
        per_ok = False
    checks = {'nur_Tetraeder': other == 0, 'alle_Volumen_positiv': min(vol) > 0, 'minSICN_groesser_0': srt[0] > 0,
              'minSICN_ueber_0_05': srt[0] > .05, 'periodische_Knoten_zugeordnet': bool(per_ok),
              'alle_Randgruppen_vorhanden': all(groups[k] for k in ('wing_lower', 'wing_upper', 'guides', 'cyclic_0', 'cyclic_45', 'outer', 'top', 'bottom'))}
    checks = {k: bool(v) for k, v in checks.items()}
    srt = [float(x) for x in (srt[0], srt[len(srt)//1000], srt[len(srt)//2])]
    rep = {'fall': name, 'status': 'REKONSTRUKTION_NETZ', 'variante': variant, 'winkelversatz_deg': offset_deg, 'stufe': level,
           'gmsh': gmsh.option.getString('General.Version'), 'tetraeder': n_tet, 'andere_3D_Elemente': other,
           'minSICN': srt[0], 'minSICN_p01': srt[1], 'minSICN_median': srt[2],
           'Randflaechen': {k: len(v) for k, v in groups.items()}, 'pruefungen': checks,
           'netzpruefung_bestanden': all(checks.values()), 'vernetzungsdauer_s': round(t_mesh, 1),
           'hinweis': 'Gmsh-Qualitaetspruefung; OpenFOAM checkMesh wurde in dieser Umgebung NICHT ausgefuehrt (OpenFOAM fehlt).'}
    out_dir.mkdir(parents=True, exist_ok=True)
    gmsh.write(str(out_dir/f'{name}.msh'))
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name'); ap.add_argument('--variant', choices=('free', 'ring'), required=True)
    ap.add_argument('--offset', type=float, default=0.); ap.add_argument('--level', choices=tuple(LEVELS), default='c')
    ap.add_argument('--threads', type=int, default=0); ap.add_argument('--log', action='store_true')
    a = ap.parse_args()
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 1)
    gmsh.option.setNumber('General.NumThreads', a.threads); gmsh.option.setNumber('Mesh.MaxNumThreads3D', a.threads)
    if a.log:gmsh.logger.start()
    case_dir = HERE/'cases'/a.name; res = HERE/'results'; res.mkdir(exist_ok=True)
    try:
        _, rep = build(a.name, a.variant, a.offset, a.level, case_dir)
    except Exception as exc:
        rep = {'fall': a.name, 'status': 'REKONSTRUKTION_NETZ', 'variante': a.variant, 'winkelversatz_deg': a.offset, 'stufe': a.level,
               'gmsh': gmsh.option.getString('General.Version'), 'netzpruefung_bestanden': False,
               'fehler': f'{type(exc).__name__}: {exc}'}
    if a.log:
        (case_dir/'gmsh.log').parent.mkdir(parents=True, exist_ok=True)
        (case_dir/'gmsh.log').write_text('\n'.join(gmsh.logger.get())); gmsh.logger.stop()
    gmsh.finalize()
    (res/f'Netzpruefung_{a.name}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
