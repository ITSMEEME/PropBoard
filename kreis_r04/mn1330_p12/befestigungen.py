"""Befestigungen an vorhandenen P12-Sitzen, ohne erfundene Kaufteil-CAD.

Gewinde als Kernkontur (mit radialem Spiel) für die BRep-Kollisionsprüfung.
Abmessungen sind Entwurfsannahmen, keine freigegebenen Bestellpositionen.
"""
import math
import FreeCAD as A
import Part

V = A.Vector


def apply(p, q, parts, scene):
    original = list(scene)
    connections = []

    def add_type(key, name, shape, detail):
        if key in parts:
            return
        shape = shape.removeSplitter()
        if not shape.isValid() or len(shape.Solids) != 1:
            raise ValueError(key + ': ungültige Befestigungsgeometrie')
        parts[key] = dict(id=key, name=name, shape=shape,
                          material='Stahl, Festigkeitsklasse/Ausführung offen',
                          process='Kaufen; konkrete Norm-/Lieferantenauswahl offen',
                          features=detail,
                          open='Entwurfsmaße; Gewinde nur Kernkontur mit Spiel; '
                               'Länge, Vorspannung, Sicherung und Lieferteil bestätigen',
                          reference=True)

    def screw(row, suffix, point, direction, nominal, length, core, head_d, head_h, socket):
        key = f'REF-SCHRAUBE-M{nominal:g}-L{length:g}-K{core:g}'
        if key not in parts:
            shaft = Part.makeCylinder(core / 2, length, V(0, 0, -length))
            head = Part.makeCylinder(head_d / 2, head_h)
            radius = socket / math.sqrt(3)
            poly = [V(radius * math.cos(i * math.pi / 3),
                      radius * math.sin(i * math.pi / 3), head_h / 2) for i in range(6)]
            pocket = Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, 0, head_h))
            add_type(key, f'Schraube M{nominal:g}×{length:g} Entwurf',
                     shaft.fuse(head).cut(pocket),
                     f'M{nominal:g}×{length:g}; Kopf Ø{head_d:g}×{head_h:g}; '
                     f'SW{socket:g}; symbolischer Gewindekern Ø{core:g}')
        place(row, suffix, key, point, direction)

    def place(row, suffix, key, point, direction):
        # Map from the original manufacturing frame into the installed frame,
        # including mirrored lower-level parts (their local Z coordinates differ).
        transform = row['shape'].Placement.multiply(row['manufacturing_shape'].Placement.inverse())
        local = A.Placement(V(*point), A.Rotation(V(0, 0, 1), V(*direction)))
        shape = parts[key]['shape'].copy()
        shape.Placement = transform.multiply(local).multiply(shape.Placement)
        name = row['name'] + '_' + suffix
        scene.append(dict(id=key, name=name, shape=shape, context=False,
                          variant='NOMINAL', manufacturing_shape=parts[key]['shape'].copy()))
        connections.append(dict(instance=name, support=row['name'], part_id=key,
                                status='ENTWURF_NICHT_BESTELLFREIGEGEBEN'))

    for row in original:
        id = row['id']
        if id == 'CFK-KLEMM-A':
            # Four recessed flange screws per complete split clamp.
            z = p['cfk_socket_flange_t'] - 4
            for i in range(4):
                a = math.radians(45 + 90 * i)
                screw(row, f'Flanschschraube{i+1}', (15*math.cos(a), 15*math.sin(a), z),
                      (0, 0, 1), 4, z + 7, 3.2, 7, 4, 3)
        if id == 'CFK-KLEMM-B':
            for i, y in enumerate([-18, 18]):
                screw(row, f'Klemmschraube{i+1}', (8, y, p['cfk_socket_flange_t'] + p['cfk_socket_length']/2),
                      (1, 0, 0), 4, 14, 3.2, 7, 4, 3)
        if id == 'CFK-GUIDE-B':
            for i, y in enumerate([-17, 17]):
                screw(row, f'Klemmschraube{i+1}', (22, y, 0), (1, 0, 0),
                      5, 60, 4.1, 8.5, 5, 4)
        if id == 'P12-016':
            # Mirrored lower-level covers occupy -t..0 in manufacturing frame.
            mirrored = row['variant'] == 'MZ'
            side = -1 if row['name'].endswith('_Deckel_B') else 1
            z = (p['cap_t'] if side > 0 else 0) * (-1 if mirrored else 1)
            direction = (0, 0, side * (-1 if mirrored else 1))
            for i in range(4):
                a = math.radians(45 + i*90)
                screw(row, f'Deckelschraube{i+1}',
                      (p['cap_hole_pcd']/2*math.cos(a), p['cap_hole_pcd']/2*math.sin(a), z),
                      direction, 3, 8, 2.4, 5.5, p['cap_head_height'], 2.5)
        if id == 'P12-018':
            nominal = p['axle_thread_d']
            height, sw = nominal * .8, nominal * 1.5
            radius = sw / math.sqrt(3)
            poly = [V(radius*math.cos(i*math.pi/3), radius*math.sin(i*math.pi/3), 0) for i in range(6)]
            nut = Part.Face(Part.makePolygon(poly+[poly[0]])).extrude(V(0,0,height))
            nut = nut.cut(Part.makeCylinder(nominal/2+.05, height+2, V(0,0,-1)))
            key = f'REF-ACHS-MUTTER-M{nominal:g}'
            add_type(key, 'Rollenachsenmutter Entwurf', nut,
                     f'Bohrung Ø{nominal+.1:g}; SW{sw:g}; Höhe{height:g}; keine Sicherungsfunktion modelliert')
            top = q['fork_inner_z'] + p['fork_t']
            mirrored = row['variant'] == 'MZ'
            place(row, 'Achsmutter', key, (0,0,-top if mirrored else top),
                  (0,0,-1 if mirrored else 1))
    q['befestigungen'] = connections
    q['befestigung_count'] = len(connections)
    return parts, scene, q
