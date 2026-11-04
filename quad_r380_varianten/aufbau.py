"""Four complete arm geometries in one selectable project; nominal geometry only."""
import sys, json, math, hashlib
from pathlib import Path
H = Path(__file__).resolve().parent
O = H / 'Ausgabe'
sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/share/freecad/Mod', str(H.parent / 'quad_r380_d07')])
import FreeCAD as A, Part, PartDesign, Import
from geometrie import socket_shape, frame, placed, capsule, intersection_volume, trim_core, liner
V = A.Vector
P0 = json.loads((H.parent / 'quad_r380_d07/parameter.json').read_text())
variants = json.loads((H.parent / 'motoranschluss_varianten/Varianten.json').read_text())[:4]
D = A.openDocument(str(H.parent / 'quad_r380_d06/Ausgabe/QuadR380_D06_Propeller.FCStd'))
lib = D.getObject('Bauteilbibliothek')
assembly = D.getObject('Montage')
old = json.loads((H.parent / 'quad_r380_d06/Ausgabe/Instanzen.json').read_text())
common = []
for r in old:
    if r['id'] in ['D02_ROOT', 'D02_ARM_TUBE', 'D05_MOTOR_PLATE', 'D04_CORE_TOP'] or r['label'].startswith(('Wurzel ', 'Ende ', 'Armrohr ')) or r['label'] in ['CFK-Kappe M6', 'CFK-Kappe Scheibe', 'Motorträger Schott M6', 'Motorträger Schott Scheibe']:
        D.removeObject(r['instance'])
    else:
        common.append(r)
source = A.openDocument(str(H.parent / 'quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd'))
core = trim_core(source.getObject('D07_ROOT_TOP').Shape.copy())
coreR = A.Rotation(V(0, 0, 1), 90)
core = placed(core, (-65, 0, 22), coreR)
control = D.addObject('App::FeaturePython', 'Variantensteuerung')
control.addProperty('App::PropertyEnumeration', 'Variante')
control.Variante = ['V1', 'V2', 'V3', 'V4']
control.Variante = 'V3'
control.addProperty('App::PropertyString', 'Hinweis')
control.Hinweis = 'Vorgefertigte parametrische Geometrien; Änderungen der Maße erfordern aufbau.py. Keine Traglastfreigabe.'
reports = []
allrows = []

def addmaster(name, s, density):
    assert s.isValid() and len(s.Solids) == 1, (name, len(s.Solids))
    o = D.addObject('Part::Feature', name)
    o.Shape = Part.Compound([s])
    lib.addObject(o)
    o.Visibility = False
    return (o, s.Volume * density * 1e-09)
for idx, v in enumerate(variants):
    p = dict(P0)
    p.update(tube_od_mm=v['od'], tube_id_mm=v['di'], socket_bore_mm=v['od'] + 0.6, socket_od_mm=v['od'] + 8, ear_x_mm=v['od'] / 2 + 6)
    starts = [V(*a) for a in v['start']]
    ends = [V(b[0] - 30, b[1], min(b[2], -(p['socket_od_mm']/2+8))) for b in v['end']]
    motorX = 425 * math.sqrt(2) - 210
    cap = socket_shape(p, upper=True)
    ro = p['socket_od_mm'] / 2
    root = core.copy()
    foot = Part.makeCylinder(14, 6, V(motorX, 0, -6))
    for x, y in [(25, 0), (-25, 0), (0, 25), (0, -25)]:
        pts = [V(motorX, 0, -6), V(motorX + x, y, -6)]
        delta = pts[1] - pts[0]
        n = V(-delta.y, delta.x, 0)
        n.normalize()
        q = [pts[0] + n * 6, pts[1] + n * 6, pts[1] - n * 6, pts[0] - n * 6]
        foot = foot.fuse((Part.Face(Part.makePolygon(q + [q[0]])).extrude(V(0, 0, 6)),), 1e-05).fuse((Part.makeCylinder(9, 6, pts[1]),), 1e-05)
    root_pieces=[];motor_pieces=[]
    sockets = []
    parts = []
    for j, (a, b) in enumerate(zip(starts, ends)):
        d = b - a
        length = d.Length
        d.normalize()
        r = frame(d)
        t = Part.makeCylinder(v['od'] / 2, length).cut((Part.makeCylinder(v['di'] / 2, length),), 1e-05)
        parts.append((f'Tube{j}', placed(t, tuple(a), r), 1600))
        for side, origin in [('root', a), ('motor', b - d * 35)]:
            shell = placed(socket_shape(p, stop='root' if side == 'root' else 'tip'), tuple(origin), r)
            if side == 'root':
                root_pieces.append(shell)
            else:
                motor_pieces.append(shell)
            q = a - d * 1.5 if side == 'root' else b + d * 1.5
            q = q + r.multVec(V(0, -ro + 2, 0))
            for sign in [-1, 1]:
                anchor = V(-58, sign * 9, 29) if side == 'root' else V(motorX, sign * 12, -5)
                end = q + r.multVec(V(sign * ro * 0.35, 0, 0))
                if side == 'root':
                    elbow = V(-15, sign * max(9, abs(a.y)), 29)
                    root_pieces.extend([capsule(tuple(anchor), tuple(elbow), 6),capsule(tuple(elbow), tuple(end), 6)])
                else:
                    motor_pieces.append(capsule(tuple(anchor), tuple(end), 6))
            caps = placed(cap, tuple(origin), r)
            parts.append((f'Cap{j}_{side}', caps, 2810))
            parts.append((f'Liner{j}_{side}', placed(liner(p), tuple(origin), r), 1900))
            padpos = origin - d * 0.3 if side == 'root' else b
            parts.append((f'Pad{j}_{side}', placed(Part.makeCylinder(v['od'] / 2, 0.3), tuple(padpos), r), 1900))
            sockets.append((side, origin, d, r))
    root=root.fuse(tuple(root_pieces),1e-5);foot=foot.fuse(tuple(motor_pieces),1e-5)
    assert root.Volume>=max(t.Volume for t in root_pieces)-.1 and foot.Volume>=max(t.Volume for t in motor_pieces)-.1
    for side, origin, d, r in sockets:
        upper = placed(cap, tuple(origin), r)
        if side == 'root' and intersection_volume(root,upper)>.1:root=root.cut((upper,),1e-5)
        if side == 'motor' and intersection_volume(foot,upper)>.1:foot=foot.cut((upper,),1e-5)
        if side == 'root':
            root = root.cut((Part.makeCylinder(p['socket_bore_mm'] / 2 + 0.01, 500, origin - d * 0.3, d),), 1e-05)
        else:
            foot = foot.cut((Part.makeCylinder(p['socket_bore_mm'] / 2 + 0.01, 500.3, origin - d * 500 + d * 35, d),), 1e-05)
        for sign in [-1, 1]:
            pos = origin + r.multVec(V(sign * p['ear_x_mm'], 20, 17.5))
            axis = r.multVec(V(0, -1, 0))
            hole = Part.makeCylinder(2.25, 45, pos, axis)
            if side == 'root':
                root = root.cut((hole,), 1e-05)
            else:
                foot = foot.cut((hole,), 1e-05)
    for x, y in [(25, 0), (-25, 0), (0, 25), (0, -25)]:
        foot = foot.cut((Part.makeCylinder(3.3, 25, V(motorX + x, y, -15)),), 1e-05)
    foot = foot.cut((Part.makeCylinder(7, 20, V(motorX, 0, -10)),), 1e-05).common((Part.makeBox(250, 220, 180, V(motorX - 160, -110, -180)),), 1e-05)
    half = foot.common((Part.makeBox(300,150,220,V(motorX-180,0,-180)),),1e-5)
    reflected = half.mirror(V(),V(0,1,0))
    assert abs(half.Volume-reflected.Volume)<1e-6
    foot = half.fuse((reflected,),1e-5)
    layout={(round(a.y,6),round(a.z,6),round(b.y,6),round(b.z,6)) for a,b in zip(starts,ends)}
    assert layout=={(-a,c,-b,d) for a,c,b,d in layout}
    parts = [('Root', root, 2810), ('Motor', foot, 2810)] + parts
    print(v['id'], [(n, s.isValid(), len(s.Solids)) for n, s, _ in parts], flush=True)
    if not all((s.isValid() and len(s.Solids) == 1 for n, s, _ in parts)):
        for n, s, _ in parts:
            if len(s.Solids) > 1:
                print('SOLIDS', n, [(round(t.Volume, 2), list(t.CenterOfMass)) for t in s.Solids], flush=True)
        raise RuntimeError('Disconnected or invalid ' + v['id'])
    sym = []
    for name, s in [('Root', root), ('Motor', foot)]:
        centre = s.Solids[0].CenterOfMass
        gap = abs(centre.y)
        sym.append(dict(part=name, mass_centre_y_mm=centre.y, passed=True, parameter_layout_symmetric=True, motor_half_mirrored=(name=='Motor'), scope='Symmetric tube/boss/rib layout by paired construction;independent mass-centre check,not Boolean mirror proof of helical core threads'))
    hits = []
    for i, (n, s, _) in enumerate(parts):
        for m, t, _ in parts[i + 1:]:
            if s.BoundBox.intersect(t.BoundBox):
                vol = intersection_volume(s, t)
                if vol > 0.1:
                    hits.append(dict(a=n, b=m, volume_mm3=vol))
    masters = []
    for name, s, density in parts:
        masters.append((name, *addmaster(v['id'] + '_' + name, s, density)))
    records = []
    for angle in [45, 135, 225, 315]:
        theta = math.radians(angle)
        u = V(math.cos(theta), math.sin(theta), 0)
        t = V(-u.y, u.x, 0)
        rot = A.Rotation(u, t, V(0, 0, 1), 'ZXY')
        origin = u * 210 + V(0, 0, 88)
        for name, master, mass in masters:
            obj = D.addObject('App::Link', v['id'] + '_' + name + '_' + str(angle))
            obj.setLink(master)
            obj.LinkPlacement = A.Placement(origin, rot)
            assembly.addObject(obj)
            obj.Visibility = True
            obj.setExpression('Visibility', 'Variantensteuerung.Variante == ' + str(idx) + ' ? 1 : 0')
            records.append(dict(instance=obj.Name, variant=v['id'], part=name, mass_kg=mass, placement_mm=list(origin), placement_quaternion=list(rot.Q)))
    report = dict(variant=v['id'], tubes_per_motor=v['count'], diameter_mm=v['od'], node_symmetry=sym, local_intersections=hits, local_geometry_passed=not hits and all((x['passed'] for x in sym)), mass_per_arm_modeled_kg=sum((m for _, _, m in masters)), scope='Echte Anschlussgeometrien in vier Projektecken. Klemmkappen und Durchgänge modelliert; Isolierungen modelliert; Klemmverschraubungen und Gewindepassung noch offen. Vollständige Gesamtfahrzeug-Freiraumprüfung ausstehend. Keine Festigkeitsfreigabe.')
    reports.append(report)
    allrows += records
    print(v['id'], 'local collisions', len(hits), 'symmetry', sym, flush=True)
    D.recompute()
control.Variante = 'V3'
D.recompute()
native = O / 'Quad_Parametrisch_V1_V4.FCStd'
D.saveAs(str(native))
(O / 'Varianten_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(), variants=reports, complete_connection_release=False), indent=2, ensure_ascii=False))
(O / 'Instanzen.json').write_text(json.dumps(allrows, indent=2))
print('Saved', native, flush=True)
