#!/usr/bin/env python3
"""Export der nativen P10-Oberflächen für die WebGL-Ansicht des Flugsimulators.

* Jede Bauteiloberfläche wird im lokalen Rahmen ihres Bewegungsschlüssels (P09_Rahmen)
  gespeichert; der Simulator setzt die Rahmen live aus der Physik (kinematik_p10.js).
* Gleiche Bauteile teilen Puffer, wenn Topologie, Volumen und Eckpunkte übereinstimmen.
* Referenzrahmen aus FreeCAD für den Node-Abgleich: simulation/kinematik_p10_referenz.json.
"""
import array
import base64
import hashlib
import json
import math
import os
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path[:0] = [os.environ.get('FREECAD_LIB', str(ROOT / '.cfd-tools/freecad/usr/lib')), str(H)]
import FreeCAD as A  # noqa: E402
import p10_runtime as RT  # noqa: E402

SIM = H.parent / 'simulation'
SRC = H / 'Ausgabe/P10_Gesamtbaugruppe.FCStd'
d = A.openDocument(str(SRC))
parts = [o for o in d.Objects if hasattr(o, 'P09_Rahmen') and not getattr(o, 'BauteilID', '').startswith('KEEP_')]
RT.apply(d, [0] * 6, [0, 0])


def category(o):
    i = o.BauteilID
    key = o.P09_Rahmen
    if i.startswith('P10-KABEL'):
        return 'cable'
    if i in ('TM-FLUEGEL',):
        return 'blade'
    if i in ('TM-NABE', 'TM-DECKEL-HOHLRAD-130'):
        return 'cover'
    if i == 'SERVO-SAVOX-SB2270SGP':
        return 'servo_case'
    if key.startswith('planet:') or i in ('RITZEL-M1-Z20', 'P10-STUETZPLANET-Z20', 'MR85ZZ', 'P10-PLANETENBOLZEN-D5', 'P10-PLANETENBOLZENTRAEGER', 'P10-DISTANZSCHEIBE-5'):
        return 'gear'
    if i.startswith(('P10-FAHRWERK', 'P10-STREBE', 'P10-KUFE')):
        return 'landing'
    if i.startswith(('P10-REF', 'P10-SERVOVERTEILER', 'REF_', 'P10-DISTANZ-VERTEILER')):
        return 'electronics'
    if key.startswith(('link:', 'p08:', 'output:', 'swash', 'sleeve', 'pin:')) or i.startswith('P09_'):
        return 'linkage'
    if i.startswith(('ISO', 'M3', 'M2', 'P10-GEWINDE')):
        return 'fastener'
    return 'structure'


def color(o, cat):
    if hasattr(o, 'P10_Farbe') and len(o.P10_Farbe) == 3:
        return list(o.P10_Farbe)
    i = o.BauteilID
    if cat == 'blade':
        return [.20, .65, .78] if int(getattr(o, 'Rotor', 0)) == 0 else [.85, .48, .25]
    if cat == 'servo_case':
        return [.16, .17, .19]
    if cat == 'gear':
        return [.78, .70, .45] if 'TRAEGER' not in i and 'BOLZEN' not in i else [.70, .72, .76]
    if cat == 'landing':
        return [.12, .12, .13] if 'CFK' in i else [.35, .37, .40]
    if cat == 'linkage':
        return [.30, .65, .64] if ('body' in i or 'horn' in i) else [.72, .74, .78]
    if cat == 'fastener':
        return [.62, .63, .66]
    if i == 'P10-SERVOHALTER' or i == 'P10-MOTORBRUECKE':
        return [.28, .30, .34]
    if i == 'TM-HALTEPLATTE':
        return [.62, .66, .70]
    if i == 'MOTOR-ECO2-2306':
        return [.25, .25, .28]
    if i == 'REF_AKKU':
        return [.33, .41, .60]
    if cat == 'cover':
        return [.50, .55, .62]
    return [.63, .68, .73]


def tol(shape, cat):
    diag = shape.BoundBox.DiagonalLength
    if cat == 'cable':
        return 0.6, 0.6
    if cat == 'servo_case':
        return 0.35, 0.5
    return (0.12, 0.45) if diag < 12 else (0.25, 0.45) if diag < 40 else (0.4, 0.4)


def canonical(o):
    """Geometry without its placement plus the placement relative to the frame key (neutral state)."""
    shape = o.Shape
    T = o.Placement
    if shape.ShapeType == 'Compound' and len(shape.SubShapes) == 1:
        sub = shape.SubShapes[0]
        T = T.multiply(sub.Placement)
        geo = sub.copy()
        geo.Placement = A.Placement()
    else:
        geo = shape.copy()
        geo.Placement = A.Placement()
    rel = T if o.P09_Rahmen == 'fixed' else o.P09_Neutralrahmen.inverse().multiply(T)
    return geo, rel


def mat12(pl):
    m = pl.toMatrix()
    return [round(v, 7) for v in (m.A11, m.A21, m.A31, m.A12, m.A22, m.A32, m.A13, m.A23, m.A33, m.A14, m.A24, m.A34)]


import MeshPart  # noqa: E402

pos = array.array('h')
nrm = array.array('b')
idx = array.array('I')
keys = []
meta = []
cache = {}
for n, o in enumerate(parts):
    key = o.P09_Rahmen
    if key not in keys:
        keys.append(key)
    geo, rel = canonical(o)
    cat = category(o)
    verts = sorted((round(v.Point.x, 2), round(v.Point.y, 2), round(v.Point.z, 2)) for v in geo.Vertexes)
    sig = (o.BauteilID, len(geo.Faces), round(geo.Volume, 2), hashlib.sha1(repr(verts).encode()).hexdigest())
    if sig in cache:
        vo, vc, io, ic = cache[sig]
    else:
        vo, io = len(pos) // 3, len(idx)
        lin, ang = tol(geo, cat)
        for f in geo.Faces:
            try:
                mesh = MeshPart.meshFromShape(Shape=f, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
            except Exception:
                continue
            pts, tris = mesh.Topology
            if not tris:
                continue
            base = len(pos) // 3
            acc = [[0.0, 0.0, 0.0] for _ in pts]
            for a, b2, c in tris:
                nn = (pts[b2] - pts[a]).cross(pts[c] - pts[a])
                for k in (a, b2, c):
                    acc[k][0] += nn.x
                    acc[k][1] += nn.y
                    acc[k][2] += nn.z
            for p, v in zip(pts, acc):
                L = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
                pos.extend([round(p.x * 100), round(p.y * 100), round(p.z * 100)])
                nrm.extend([max(-127, min(127, round(127 * v[0] / L))), max(-127, min(127, round(127 * v[1] / L))), max(-127, min(127, round(127 * v[2] / L)))])
            for a, b2, c in tris:
                idx.extend([base + a, base + b2, base + c])
        vc, ic = len(pos) // 3 - vo, len(idx) - io
        cache[sig] = (vo, vc, io, ic)
    bb = geo.BoundBox
    meta.append(dict(n=o.Name, k=keys.index(key), vo=vo, vc=vc, io=io, ic=ic, c=[round(x, 3) for x in color(o, cat)], g=cat,
                     s=[round(bb.Center.x, 2), round(bb.Center.y, 2), round(bb.Center.z, 2), round(bb.DiagonalLength / 2, 2)], m=mat12(rel)))
    if n % 100 == 0:
        print('tessellated', n, '/', len(parts), 'triangles', len(idx) // 3, flush=True)
assert max(abs(v) for v in pos) < 32767
payload = dict(revision='P10', source_native_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(), keys=keys, parts=meta,
               pos=base64.b64encode(pos.tobytes()).decode(), nrm=base64.b64encode(nrm.tobytes()).decode(),
               idx=base64.b64encode(idx.tobytes()).decode(), quantization_mm=0.01)
js = 'globalThis.H01_P10_MESH=' + json.dumps(payload, separators=(',', ':')) + ';\n'
(SIM / 'p10_mesh.js').write_text(js)

# Referenzrahmen für den JavaScript-Abgleich
states = [([0] * 6, [0, 0]), ([2, -1, 0.5, 0, 1.5, -2], [17.0, 33.0]), ([-3, 3, 1, 2.5, -2.5, 0.5], [123.4, -77.7])]
for t in (1.35, 3.1, 5.65):
    s, a = RT.demo(t)
    states.append((list(s), list(a)))
ref = []
for servos, angles in states:
    r = RT.state(servos, angles)
    fr = {}
    for k, pl in r['frames'].items():
        m = pl.toMatrix()
        fr[k] = [m.A11, m.A12, m.A13, m.A21, m.A22, m.A23, m.A31, m.A32, m.A33, pl.Base.x, pl.Base.y, pl.Base.z]
    ref.append(dict(servos=servos, angles=angles, frames=fr, pitches=r['pitches']))
(SIM / 'kinematik_p10_referenz.json').write_text(json.dumps(ref) + '\n')
mass = (H / 'Ausgabe/Massen_P10.json').read_text()
(SIM / 'p10_massen.js').write_text('globalThis.H01_P10_MASSEN=' + json.dumps(json.loads(mass), separators=(',', ':')) + ';\n')
report = dict(source_native_sha256=payload['source_native_sha256'], parts=len(meta), unique_vertices=len(pos) // 3, unique_triangles=len(idx) // 3,
              rendered_triangles=sum(p['ic'] for p in meta) // 3, keys=len(keys), mesh_js_bytes=len(js), reference_states=len(ref),
              geometry_source='Native FreeCAD shapes of P10 assembly, including known invalid servo case reference')
(H / 'Ausgabe/Browserexport_P10.json').write_text(json.dumps(report, indent=2) + '\n')
A.closeDocument(d.Name)
print(json.dumps(report, indent=2))
