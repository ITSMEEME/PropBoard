"""P10 – Rahmenanbindung der Servos, Landegestell, Elektronik-Bauräume. Millimeter.

Alle Maße sind Konstruktionsentwurf, keine Fertigungsfreigabe.

Koordinaten
-----------
* Lokaler Rotorrahmen wie in P09 (``bewegung_runtime.local_world``): Flügelebene z = 0,
  Halteplatte z = 43…47, Servo-Abtriebsachse bei x = 58,3 / z = 60 tangential (y).
* Servo-STEP (Quelle) → lokal: (X, Y, Z) → (X + 58,3, Y − 22,3, Z + 60), danach Drehung um z
  mit dem Servo-Azimut 60/180/300° und Abbildung auf Welt über ``local_world(sign)``.
* Aus der gelieferten STEP vermessen: Laschenunterseite Y = 0 (lokal y = −22,3), Laschendicke
  2,2 mm, Laschenbohrungen X = −14,15 / 33,85, Z = ±5 (48,0 × 10,0 mm, Ø4,68 mit
  Randschlitz 3 mm), Gehäuse X −10,3…30,0, Z ±10,05, Y −25,9…7,77.
"""
import math
import FreeCAD as A
import Part

V = A.Vector
SERVO_AZ = (60, 180, 300)

# ----------------------------------------------------------------------------- Servo-Bezug
SERVO_OFFSET = (58.3, -22.3, 60.0)
TAB_UNDERSIDE_Y = -22.3          # Laschen-Anlagefläche (Quelle Y = 0)
TAB_TOP_Y = -20.1                # Laschenoberseite (Quelle Y = 2,2)
TAB_HOLES_XZ = [(-14.15 + 58.3, z + 60.0) for z in (-5.0, 5.0)] + [(33.85 + 58.3, z + 60.0) for z in (-5.0, 5.0)]
SERVO_BODY = dict(x=(-10.3 + 58.3, 30.0 + 58.3), y=(-25.9 - 22.3, 7.77 - 22.3), z=(-10.05 + 60, 10.05 + 60))
SERVO_CABLE_EXIT = (29.2 + 58.3, -22.5 - 22.3, 60.0)   # Annahme: Kabelaustritt Stirnseite unten; STEP enthält kein Kabel

# ----------------------------------------------------------------------------- Servohalter
WEB_Y = (-26.3, -22.3)           # 4-mm-Steg hinter der Laschenanlage
WEB_X = (38.5, 98.5)
WEB_Z_TOP = 69.5                 # unterhalb H04 (unten, Welt −100) und H01 (oben)
WINDOW_X = (47.2, 89.1)          # Gehäusedurchtritt, ≥0,7 mm Luft zum Gehäuse
FOOT_Z = (47.0, 49.4)            # Fußflansch auf der Halteplatte, 0,55 mm unter Servoboden
FOOT_Y = (-38.5, -12.0)
FOOT_IN_X = (32.0, 47.2)
FOOT_OUT_X = (89.1, 104.5)
FOOT_BOLTS_XY = [(35.2, -35.5), (35.2, -25.5), (101.5, -35.5), (101.5, -17.0)]
PLATE_EXT = dict(x=(29.5, 107.0), y=(-40.5, -9.5), z=(43.0, 47.0))

M3 = dict(d=3.0, head_d=5.5, head_k=3.0, socket=2.5, nut_s=5.5, nut_m=2.4, washer_d=7.0, washer_t=0.5, clear=3.4)


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, h, p=(0, 0, 0), axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*axis))


def hex_prism(af, h):
    r = af / math.sqrt(3)
    pts = [V(r * math.cos(math.radians(30 + 60 * i)), r * math.sin(math.radians(30 + 60 * i)), 0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, h))


def orient(shape, origin, axis, spin=0.0):
    """Place a +z-oriented local shape at ``origin`` with local +z along ``axis``."""
    s = shape.copy()
    if spin:
        s.rotate(V(), V(0, 0, 1), spin)
    rot = A.Rotation(V(0, 0, 1), V(*axis))
    s.Placement = A.Placement(V(*origin), rot).multiply(s.Placement)
    return s


def tri_prism_x(x0, x1, pts_yz):
    """Prism between x0 and x1 with polygon given in (y, z)."""
    vs = [V(x0, y, z) for y, z in pts_yz]
    return Part.Face(Part.makePolygon(vs + [vs[0]])).extrude(V(x1 - x0, 0, 0))


# ----------------------------------------------------------------------------- Normteile (nominal)
def iso4762(length, d=3.0, head_d=5.5, k=3.0, socket=2.5):
    """Zylinderschraube: Kopfauflage z = 0, Kopf +z, Schaft −z (Gewinde nominal glatt dargestellt)."""
    s = cyl(head_d / 2, k).fuse(cyl(d / 2, length, (0, 0, -length)))
    sock = hex_prism(socket, 1.6)
    sock.translate(V(0, 0, k - 1.6))
    return s.cut(sock).removeSplitter()


def iso4032(s=5.5, m=2.4, d=3.0):
    return hex_prism(s, m).cut(cyl(d / 2, m + 2, (0, 0, -1))).removeSplitter()


def iso7089(d_in=3.2, d_out=7.0, t=0.5):
    return cyl(d_out / 2, t).cut(cyl(d_in / 2, t + 2, (0, 0, -1)))


def heatset_m3(length=4.0, od=4.0):
    """Gewindeeinsatz M3 (Bauraum Ø4 in der Ø4,0-Aufnahmebohrung, Rändel nicht dargestellt)."""
    return cyl(od / 2, length).cut(cyl(1.5, length + 2, (0, 0, -1)))


# ----------------------------------------------------------------------------- Servohalter
def servo_bracket():
    web = box(WEB_X[0], WEB_X[1], WEB_Y[0], WEB_Y[1], FOOT_Z[0], WEB_Z_TOP)
    web = web.cut(box(WINDOW_X[0], WINDOW_X[1], WEB_Y[0] - 1, WEB_Y[1] + 1, FOOT_Z[1], WEB_Z_TOP + 1))
    feet = box(FOOT_IN_X[0], FOOT_IN_X[1], FOOT_Y[0], FOOT_Y[1], *FOOT_Z).fuse(
        box(FOOT_OUT_X[0], FOOT_OUT_X[1], FOOT_Y[0], FOOT_Y[1], *FOOT_Z))
    # Rippen: hinten (Gehäuseseite) und vorn (Laschenseite), außerhalb von Laschen und Muttern.
    back = [(WEB_Y[0], FOOT_Z[1]), (FOOT_Y[0] + 4.5, FOOT_Z[1]), (WEB_Y[0], 66.0)]
    front = [(WEB_Y[1], FOOT_Z[1]), (FOOT_Y[1] - 2.0, FOOT_Z[1]), (WEB_Y[1], 64.0)]
    ribs = [tri_prism_x(38.5, 41.0, back), tri_prism_x(96.0, 98.5, back),
            tri_prism_x(38.5, 40.4, front), tri_prism_x(96.6, 98.5, front)]
    s = web.fuse([feet] + ribs).removeSplitter()
    holes = [orient(cyl(M3['clear'] / 2, 12, (0, 0, -6)), (x, -24.3, z), (0, 1, 0)) for x, z in TAB_HOLES_XZ]
    holes += [cyl(M3['clear'] / 2, 6, (x, y, FOOT_Z[0] - 1)) for x, y in FOOT_BOLTS_XY]
    return s.cut(Part.makeCompound(holes)).removeSplitter()


def bracket_fasteners():
    """Liste (Rolle, Shape) aller Schrauben/Scheiben/Muttern eines Halters im lokalen Rahmen."""
    out = []
    for x, z in TAB_HOLES_XZ:
        # Servo-Lasche → Steg: Scheibe + M3x12 von der Laschenoberseite, Scheibe + Mutter auf der Stegrückseite.
        out.append(('ISO7089-M3', orient(iso7089(), (x, TAB_TOP_Y, z), (0, 1, 0))))
        out.append(('ISO4762-M3x12', orient(iso4762(12), (x, TAB_TOP_Y + 0.5, z), (0, 1, 0))))
        out.append(('ISO7089-M3', orient(iso7089(), (x, WEB_Y[0], z), (0, -1, 0))))
        out.append(('ISO4032-M3', orient(iso4032(), (x, WEB_Y[0] - 0.5, z), (0, -1, 0), spin=30)))
    for x, y in FOOT_BOLTS_XY:
        # Halterfuß → Halteplatte: M3x10 von oben, Scheibe + Mutter unter der Platte.
        out.append(('ISO4762-M3x10', orient(iso4762(10), (x, y, FOOT_Z[1]), (0, 0, 1))))
        out.append(('ISO7089-M3', orient(iso7089(), (x, y, PLATE_EXT['z'][0]), (0, 0, -1))))
        out.append(('ISO4032-M3', orient(iso4032(), (x, y, PLATE_EXT['z'][0] - 0.5), (0, 0, -1))))
    return out


def plate_extension():
    """Servoausleger der Halteplatte (lokal, je Servo-Azimut) mit Bohrungen für den Halterfuß."""
    e = PLATE_EXT
    pads = []
    for az in SERVO_AZ:
        pad = box(e['x'][0], e['x'][1], e['y'][0], e['y'][1], *e['z'])
        pad.rotate(V(), V(0, 0, 1), az)
        pads.append(pad)
    return pads


def plate_holes():
    z0 = PLATE_EXT['z'][0] - 1
    holes = []
    for az in SERVO_AZ:
        for x, y in FOOT_BOLTS_XY:
            h = cyl(M3['clear'] / 2, 6, (x, y, z0))
            h.rotate(V(), V(0, 0, 1), az)
            holes.append(h)
    return holes


def servo_body_relief_local(margin=1.0):
    b = SERVO_BODY
    return box(b['x'][0] - margin, b['x'][1] + margin, b['y'][0] - margin, b['y'][1] + margin, b['z'][0] - margin, b['z'][1] + margin)


# ----------------------------------------------------------------------------- Landegestell (Welt)
GROUND_Z = -220.5   # Ringboden der Kufenschellen; Kufenunterkante −218 (2,5 mm darüber)
SKID = dict(y=110.0, z=-214.0, r=4.0, r_in=3.0, flat=120.0, tip_x=158.0, tip_z=-199.0)
STRUT = dict(r=3.0, r_in=2.0)
NODE = dict(size=16.0, z=(-181.0, -169.0))
CORNERS = [(sx * 45.0, sy * 26.0) for sx in (-1, 1) for sy in (-1, 1)]
JOINT_X = 60.0


def node_point(cx, cy):
    return V(cx, cy, -176.0)


def joint_point(cx, cy):
    return V(math.copysign(JOINT_X, cx), math.copysign(SKID['y'], cy), SKID['z'])


def strut_axis(cx, cy):
    a = node_point(cx, cy)
    b = joint_point(cx, cy)
    u = b - a
    u.normalize()
    return a, b, u


def gear_node(cx, cy):
    """Fahrwerksknoten unter der Akkuwanne, geklemmt von der verlängerten M3-Akkuverschraubung."""
    h = NODE['size'] / 2
    s = box(cx - h, cx + h, cy - h, cy + h, *NODE['z'])
    a, b, u = strut_axis(cx, cy)
    boss = Part.makeCylinder(5.5, 16.0, a, u)
    s = s.fuse(boss).removeSplitter()
    s = s.cut(cyl(M3['clear'] / 2, 20, (cx, cy, NODE['z'][0] - 4)))
    s = s.cut(Part.makeCylinder(3.05, 11.0, a + u * 5.0, u))          # Rohrsteckung Ø6, 11 tief
    return s.removeSplitter()


def strut_tube(cx, cy):
    a, b, u = strut_axis(cx, cy)
    start = a + u * 5.2
    end = b - u * 6.2
    L = (end - start).Length
    return Part.makeCylinder(STRUT['r'], L, start, u).cut(Part.makeCylinder(STRUT['r_in'], L + 2, start - u, u))


def skid_path(side):
    """Gerade Kufe mit tangential aufgebogenen Enden (Biegeradius 30 mm, 40°)."""
    y, z = math.copysign(SKID['y'], side), SKID['z']
    R, ang, tip = 30.0, math.radians(40.0), 22.0
    x0 = SKID['flat']
    edges = []

    def end(sx):
        a0 = V(sx * x0, y, z)
        mid = V(sx * (x0 + R * math.sin(ang / 2)), y, z + R * (1 - math.cos(ang / 2)))
        a1 = V(sx * (x0 + R * math.sin(ang)), y, z + R * (1 - math.cos(ang)))
        t = V(sx * math.cos(ang), 0, math.sin(ang))
        return a0, mid, a1, a1 + t * tip

    l0, lm, l1, lt = end(-1)
    r0, rm, r1, rt = end(1)
    edges.append(Part.LineSegment(lt, l1).toShape())
    edges.append(Part.Arc(l1, lm, l0).toShape())
    edges.append(Part.LineSegment(l0, r0).toShape())
    edges.append(Part.Arc(r0, rm, r1).toShape())
    edges.append(Part.LineSegment(r1, rt).toShape())
    return Part.Wire(edges)


def sweep_tube(path, r_out, r_in=None):
    """Kreisquerschnitt entlang eines tangentenstetigen Pfads (korrigiertes Frenet-Trieder)."""
    if isinstance(path, Part.Wire):
        wire = path
    elif isinstance(path, Part.Edge):
        wire = Part.Wire([path])
    else:
        wire = Part.Wire([path.toShape()])
    e0 = wire.OrderedEdges[0]
    p0 = wire.OrderedVertexes[0].Point
    t0 = e0.tangentAt(e0.FirstParameter)
    if (e0.valueAt(e0.FirstParameter) - p0).Length > 1e-6:
        t0 = -e0.tangentAt(e0.LastParameter)

    def solid(r):
        circle = Part.Wire([Part.makeCircle(r, p0, t0)])
        return wire.makePipeShell([circle], True, False)

    s = solid(r_out)
    if r_in:
        s = s.cut(solid(r_in))
    return s


def skid(side):
    return sweep_tube(skid_path(side), SKID['r'], SKID['r_in'])


def skid_clamp(cx, cy):
    """Kufenschelle mit Strebenaufnahme (geschlossener Ring, RC-üblich: der Ringboden ist der Bodenkontakt).
    Klemmlasche nach außen (weg von der Strebe) und über Bodenniveau; horizontaler Schlitz 1 mm,
    M3x8 von oben in einen Gewindeeinsatz der unteren Laschenhälfte."""
    j = joint_point(cx, cy)
    a, b, u = strut_axis(cx, cy)
    out = math.copysign(1.0, cy)
    ring = Part.makeCylinder(6.5, 16.0, j + V(-8, 0, 0), V(1, 0, 0))
    boss = Part.makeCylinder(5.5, 15.0, j, V(-u.x, -u.y, -u.z))
    y0, y1 = sorted((j.y + out * 4.0, j.y + out * 13.5))
    lug = box(j.x - 6, j.x + 6, y0, y1, j.z - 3.5, j.z + 5.5)
    s = ring.fuse([boss, lug]).removeSplitter()
    s = s.cut(Part.makeCylinder(SKID['r'] + 0.05, 20.0, j + V(-10, 0, 0), V(1, 0, 0)))
    ys0, ys1 = sorted((j.y + out * 2.0, j.y + out * 14.5))
    s = s.cut(box(j.x - 9, j.x + 9, ys0, ys1, j.z - 0.5, j.z + 0.5))                    # Klemmschlitz
    yc = j.y + out * 9.5
    s = s.cut(Part.makeCylinder(M3['clear'] / 2, 7.0, V(j.x, yc, j.z - 0.6), V(0, 0, 1)))
    s = s.cut(Part.makeCylinder(2.0, 3.2, V(j.x, yc, j.z - 3.6), V(0, 0, 1)))           # Aufnahme Gewindeeinsatz
    s = s.cut(Part.makeCylinder(3.05, 11.0, b - u * 6.5, V(-u.x, -u.y, -u.z)).fuse(
        Part.makeCylinder(3.05, 6.6, b - u * 6.5, u)))                                   # Strebensteckung
    return s.removeSplitter()


def skid_clamp_fasteners(cx, cy):
    j = joint_point(cx, cy)
    yc = j.y + math.copysign(9.5, cy)
    out = [('ISO4762-M3x8', orient(iso4762(8), (j.x, yc, j.z + 5.5), (0, 0, 1)))]
    insert = heatset_m3(3.0)
    insert.translate(V(j.x, yc, j.z - 3.5))
    out.append(('P10-GEWINDEEINSATZ-M3', insert))
    return out


def skid_end_cap(side, end):
    """Weicher Kufenstopfen (TPU) im aufgebogenen Rohrende."""
    w = skid_path(side)
    e = w.OrderedEdges[-1] if end > 0 else w.OrderedEdges[0]
    if end > 0:
        p, d = e.valueAt(e.LastParameter), e.tangentAt(e.LastParameter)
    else:
        p, d = e.valueAt(e.FirstParameter), -e.tangentAt(e.FirstParameter)
    return Part.makeCylinder(SKID['r_in'], 6.0, p - d * 5.0, d).fuse(Part.makeCylinder(SKID['r'] + 0.3, 2.0, p, d)).removeSplitter()


def gear_bolt(cx, cy):
    """M3x80 ISO 4762 von unten durch Knoten, Wanne, Distanz H06 in Gewindeeinsatz von H04."""
    return orient(iso4762(80), (cx, cy, NODE['z'][0]), (0, 0, -1))


# ----------------------------------------------------------------------------- Elektronik-Bauräume (Welt)
def ubec():
    """UBEC 7,4 V (Bauraumreferenz 22 x 15 x 5,6 mm, Annahme); frei von den M3-Köpfen unter H04."""
    return box(19.5, 41.5, -29.5, -14.5, -110.6, -105.0)


def lower_junction():
    """Unterer Servo-Sammelpunkt (Lochraster/PCB mit 3 Servoanschlüssen, Bauraum 18 x 12,5 x 4 mm)."""
    return box(19.0, 37.0, 17.5, 30.0, -109.6, -105.6)


def top_distributor():
    """Oberer Servoverteiler (PCB 13 x 34 x 1,6 mm, Lötpads) auf zwei Distanzen, ragt 2 mm über H01."""
    pcb = box(24.0, 37.0, -17.0, 17.0, 101.5, 103.1)
    feet = cyl(1.8, 1.5, (30.5, -14.5, 100.0)).fuse(cyl(1.8, 1.5, (30.5, 14.5, 100.0)))
    return pcb, feet


def receiver():
    """ELRS-Empfänger (Bauraum 10 x 13 x 3,5 mm) auf 0,2-mm-Klebepad."""
    return box(-33.0, -23.0, 8.0, 21.0, 100.2, 103.7)


def xt60_pair():
    """XT60-Steckerpaar senkrecht im reservierten Zugang: Stecker unten (Akku), Buchse oben (Fahrzeug)."""
    male = box(49.0, 57.2, -7.9, 7.9, -155.0, -142.0)
    female = box(49.0, 57.2, -7.9, 7.9, -142.0, -129.0)
    return male, female


def jst_balancer():
    return box(-53.0, -47.0, -10.0, 10.0, -150.0, -143.0)


# ============================================================================= Planetengetriebe (lokaler Rotorrahmen)
# Innenverzahntes Hohlrad Z130 im Rotordeckel; EMAX-Ritzel Z20 = angetriebener Planet;
# zwei mitlaufende Stützplaneten Z20 auf Planetenbolzen der Halteplatte. Ohne Sonnenrad
# (Mittelrohr und Blattgestänge belegen die Achse): die Stützplaneten zentrieren das Hohlrad
# und nehmen die Radialkraft des Antriebseingriffs auf, sie übertragen kein Moment.
PLANET = dict(
    module=1.0, z_ring=130, z_planet=20, pressure_deg=20.0,
    centre=54.8,                 # 55,0 nominal − 0,2 für ≈0,15 mm Flankenspiel (Δb ≈ 2·Δa·tan20°)
    phi_drive=330.0,             # freier Sektor zwischen Servo 300° und Servohalter 60°
    phi_idlers=(115.0, 205.0),   # +145°/−125° zum Antrieb: frei von Servogestänge 180°, Führungsgabel 240° und Halter 60°
    z_gear=(15.4, 20.9),         # Ritzelstirn 5,5 mm; Wellenende bei z = 15,4
    ring_z=(13.5, 21.5), disk_z=(10.5, 13.5), ring_r_out=70.0,
    motor_lift=4.0,              # Motor-Anlagefläche von z 43 (Plattenunterseite) auf z 47 (Brücke)
)
PLANET['ratio'] = PLANET['z_ring'] / PLANET['z_planet']
BRIDGE = dict(z=(47.0, 51.0), r_disk=17.0, ear_r=20.0, ear_psi=(60.0, 130.0, 300.0), ear_w=9.0)
CARRIER = dict(flange_r=14.0, flange_z=(40.0, 43.0), pillar_r=6.0, pillar_z=(21.5, 40.0), bolt_t=10.0,
               pin_r=2.5, pin_z=(15.4, 35.0), head_r=3.5, head_z=(14.6, 15.4))
MOTOR_HOLE_R = 14.75
MOTOR_NOTCH = (13.0, 25.0, 3.5)   # radial von/bis (motorzentriert, nach außen), halbe Breite


def polar(r, deg, z=0.0):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a), z)


def planet_centre(k):
    phi = PLANET['phi_drive'] if k == 0 else PLANET['phi_idlers'][k - 1]
    return polar(PLANET['centre'], phi)[:2], phi


def planet_spin_deg(phi, rotor_deg):
    """Planetendrehwinkel (Zahnlücke der Z20-Kontur bei 0°) für Hohlrad-Drehwinkel ``rotor_deg``.

    Innenverzahnung: gleicher Drehsinn, i = 130/20 = 6,5. Phase so, dass bei einer Hohlrad-
    Zahnmitte in Richtung φ die Planetenlücke in Richtung φ zeigt: β = −5,5·φ + 6,5·a.
    """
    return -(PLANET['ratio'] - 1.0) * phi + PLANET['ratio'] * rotor_deg


def _fcgear_face(internal, z, add, ded, fillet):
    import sys
    from pathlib import Path
    pd = Path(A.getResourceDir()) / 'Mod/PartDesign'
    if str(pd) not in sys.path:
        sys.path.insert(0, str(pd))
    from fcgear import involute, fcgear
    w = fcgear.FCWireBuilder()
    if internal:
        involute.CreateInternalGear(w, PLANET['module'], z, PLANET['pressure_deg'], split=True,
                                    addCoeff=add, dedCoeff=ded, filletCoeff=fillet)
    else:
        involute.CreateExternalGear(w, PLANET['module'], z, PLANET['pressure_deg'], split=True,
                                    addCoeff=add, dedCoeff=ded, filletCoeff=fillet, shiftCoeff=0)
    return Part.Face(Part.Wire([e.toShape() for e in w.wire]))


def ring_gear():
    """Hohlrad Z130 m1: Kopfkreis innen Ø128,8 (Kopfhöhe 0,6 m), Fußkreis Ø132,5, Kranz bis Ø140."""
    z0, z1 = PLANET['ring_z']
    teeth = _fcgear_face(True, PLANET['z_ring'], 0.6, 1.25, 0.375).extrude(V(0, 0, z1 - z0 + 2))
    teeth.translate(V(0, 0, z0 - 1))
    rim = cyl(PLANET['ring_r_out'], z1 - z0, (0, 0, z0))
    return rim.cut(teeth).removeSplitter()


def lid_p10(C, sign):
    """P10-Deckel: unveränderter innerer P09-Deckel (Fenster, Schlitze, Mitnehmer, Schrauben)
    bis r = 59,5 plus geschlossene Scheibe bis r = 70 und darauf das Hohlrad."""
    z0, z1 = PLANET['disk_z']
    # Nur die Scheibe des P09-Deckels übernehmen (der frühere Zahnkranzring über z1 entfällt).
    inner = C.lid_shape(sign, teeth=False)[0].common(cyl(59.5, z1 - z0 + 2, (0, 0, z0 - 2)))
    disk = cyl(PLANET['ring_r_out'], z1 - z0, (0, 0, z0)).cut(cyl(59.0, 10, (0, 0, z0 - 1)))
    lid = inner.fuse([disk, ring_gear()]).removeSplitter()
    # Gestängeschlitze radial bis r = 24,5 verlängern: der P09-Pitchhebel-Boss berührte bei
    # Schwebepitch die Deckelunterseite (0,65/1,1 mm); frei für Pitch −6…25°.
    sy = C.LID['slot'][1]
    y0, y1 = sorted((sign * C.LID['slot_y0'], sign * (C.LID['slot_y0'] + sy)))
    relief = []
    for k in range(8):
        b = box(24.5, C.HO['r_center'], y0, y1, z0 - 1, z1 + 1)
        b.rotate(V(), V(0, 0, 1), 45 * k)
        relief.append(b)
    return lid.cut(Part.makeCompound(relief)).removeSplitter()


def planet_profile_shape(face_h, bore_r):
    s = _fcgear_face(False, PLANET['z_planet'], 1.0, 1.25, 0.38)
    probe = s.extrude(V(0, 0, 1))
    tooth_at_0 = probe.isInside(V(10, 0, 0.5), 1e-7, True)
    s = s.extrude(V(0, 0, face_h)).cut(cyl(bore_r, face_h + 2, (0, 0, -1)))
    if tooth_at_0:
        s.rotate(V(), V(0, 0, 1), 9.0)          # Zahnlücke auf 0° wie P05-Ritzel
    return s


def idler_gear():
    """Stützplanet Z20 m1 (lokal: Achse z, Lücke bei 0°), Bohrung Ø8 für 2× MR85 + Schulter Ø7."""
    h = PLANET['z_gear'][1] - PLANET['z_gear'][0]
    g = planet_profile_shape(h, 4.0)
    g = g.fuse(cyl(4.0, 0.5, (0, 0, h - 0.5)).cut(cyl(3.5, 2, (0, 0, h - 1)))).removeSplitter()
    g.translate(V(0, 0, PLANET['z_gear'][0]))
    return g


def mr85_pair():
    """Zwei Rillenkugellager MR85 (5 × 8 × 2,5 mm) als Hüllkörper."""
    z0 = PLANET['z_gear'][0]
    return [cyl(4.0, 2.5, (0, 0, z0 + 2.5 * i)).cut(cyl(2.5, 4, (0, 0, z0 + 2.5 * i - 1))) for i in range(2)]


def planet_pin():
    c = CARRIER
    return cyl(c['head_r'], c['head_z'][1] - c['head_z'][0], (0, 0, c['head_z'][0])).fuse(
        cyl(c['pin_r'], c['pin_z'][1] - c['pin_z'][0], (0, 0, c['pin_z'][0]))).removeSplitter()


def planet_spacer():
    z = PLANET['z_gear'][0] + 5.0
    return cyl(3.4, CARRIER['pillar_z'][0] - z, (0, 0, z)).cut(cyl(2.6, 5, (0, 0, z - 1)))


def planet_carrier(phi):
    """Planetenbolzenträger (Alu-Fräs-/Drehteil, Vorschlag EN AW-6082): Flansch unter der
    Halteplatte, Säule bis über das Zahnrad, Presssitz für den Ø5-Bolzen. Lokale Achse z."""
    c = CARRIER
    s = cyl(c['flange_r'], c['flange_z'][1] - c['flange_z'][0], (0, 0, c['flange_z'][0])).fuse(
        cyl(c['pillar_r'], c['pillar_z'][1] - c['pillar_z'][0], (0, 0, c['pillar_z'][0]))).removeSplitter()
    s = s.cut(cyl(c['pin_r'], c['pin_z'][1] - c['pillar_z'][0] + 0.01, (0, 0, c['pillar_z'][0] - 0.01)))
    for sgn in (-1, 1):
        x, y = _carrier_bolt_local(phi, sgn)
        s = s.cut(cyl(M3['clear'] / 2, 10, (x, y, c['flange_z'][0] - 1)))
    return s.removeSplitter()


def _carrier_bolt_local(phi, sgn):
    a = math.radians(phi)
    return (-sgn * CARRIER['bolt_t'] * math.sin(a), sgn * CARRIER['bolt_t'] * math.cos(a))


def at_xy(shape, xy, spin=0.0):
    s = shape.copy()
    if spin:
        s.rotate(V(), V(0, 0, 1), spin)
    s.translate(V(xy[0], xy[1], 0))
    return s


def carrier_fasteners(phi):
    cx, cy = polar(PLANET['centre'], phi)[:2]
    out = []
    for sgn in (-1, 1):
        dx, dy = _carrier_bolt_local(phi, sgn)
        x, y = cx + dx, cy + dy
        out.append(('ISO7089-M3', orient(iso7089(), (x, y, 47.0), (0, 0, 1))))
        out.append(('ISO4762-M3x12', orient(iso4762(12), (x, y, 47.5), (0, 0, 1))))
        out.append(('ISO7089-M3', orient(iso7089(), (x, y, CARRIER['flange_z'][0]), (0, 0, -1))))
        out.append(('ISO4032-M3', orient(iso4032(), (x, y, CARRIER['flange_z'][0] - 0.5), (0, 0, -1), spin=30)))
    return out


def motor_centre():
    return polar(PLANET['centre'], PLANET['phi_drive'])[:2]


def motor_bridge():
    """Motorbrücke (PA-CF): Motor hängt mit Anlagefläche z = 47 durch die Halteplatte."""
    b = BRIDGE
    s = cyl(b['r_disk'], b['z'][1] - b['z'][0], (0, 0, b['z'][0]))
    for psi in b['ear_psi']:
        ear = box(0, b['ear_r'], -b['ear_w'] / 2, b['ear_w'] / 2, *b['z']).fuse(cyl(b['ear_w'] / 2, 4, (b['ear_r'], 0, b['z'][0])))
        ear.rotate(V(), V(0, 0, 1), psi)
        s = s.fuse(ear)
    s = s.removeSplitter()
    holes = [cyl(3.8, 6, (0, 0, b['z'][0] - 1))]
    holes += [cyl(M3['clear'] / 2, 6, (8 * math.cos(math.radians(q)), 8 * math.sin(math.radians(q)), b['z'][0] - 1)) for q in (45, 135, 225, 315)]
    holes += [cyl(M3['clear'] / 2, 6, (b['ear_r'] * math.cos(math.radians(p)), b['ear_r'] * math.sin(math.radians(p)), b['z'][0] - 1)) for p in b['ear_psi']]
    s = s.cut(Part.makeCompound(holes)).removeSplitter()
    s.rotate(V(), V(0, 0, 1), PLANET['phi_drive'])
    s.translate(V(*motor_centre(), 0))
    return s


def bridge_fasteners():
    c = motor_centre()
    out = []
    for psi in BRIDGE['ear_psi']:
        a = math.radians(PLANET['phi_drive'] + psi)
        x, y = c[0] + BRIDGE['ear_r'] * math.cos(a), c[1] + BRIDGE['ear_r'] * math.sin(a)
        out.append(('ISO7089-M3', orient(iso7089(), (x, y, BRIDGE['z'][1]), (0, 0, 1))))
        out.append(('ISO4762-M3x12', orient(iso4762(12), (x, y, BRIDGE['z'][1] + 0.5), (0, 0, 1))))
        out.append(('ISO7089-M3', orient(iso7089(), (x, y, 43.0), (0, 0, -1))))
        out.append(('ISO4032-M3', orient(iso4032(), (x, y, 42.5), (0, 0, -1), spin=30)))
    return out


def plate_p10(C):
    """Halteplatte P10: P09-Kontur ohne alten Motorarm, Motor-/Planetenarme, Servoausleger."""
    PL, SW, MO = C.PL, C.SW, C.MO
    t = PL['t']
    z0 = C.P['gear']['pinion_z0'] + MO['shaft_h'] + MO['body_h']
    rt = C.P['tube']['d'] / 2
    s = cyl(rt + PL['collar_wall'] + 6, t, (0, 0, z0))
    mc = motor_centre()
    arm = box(0, PLANET['centre'], -PL['arm_w'] / 2, PL['arm_w'] / 2, z0, z0 + t)
    arm.rotate(V(), V(0, 0, 1), PLANET['phi_drive'])
    parts = [arm, cyl(24.0, t, (mc[0], mc[1], z0))]
    pw, pd = PL['servo_pad']
    for ang in SW['servo_angles_deg']:
        parts.append(C.rotz(C.box(0, PL['servo_pad_r'] + pd / 2 + 6, -pw / 2, pw / 2, z0, z0 + t), ang))
    ga = SW['guide_angle_deg']
    gr = SW['stat_arm_r'] + 6
    parts.append(C.rotz(C.box(0, gr + 4, -6, 6, z0, z0 + t), ga))
    guide_w = SW.get('guide_slot_w', SW['slot_w'])
    post = C.box(gr - 4, gr + 4, -4, 4, z0 - 11, z0 + 0.01).cut(C.box(gr - 5, gr + 5, -guide_w / 2, guide_w / 2, z0 - 12, z0 - 1.5))
    parts.append(C.rotz(post, ga))
    for phi in PLANET['phi_idlers']:
        a = box(0, PLANET['centre'], -9, 9, z0, z0 + t)
        a.rotate(V(), V(0, 0, 1), phi)
        x, y = polar(PLANET['centre'], phi)[:2]
        parts += [a, cyl(CARRIER['flange_r'] + 1.0, t, (x, y, z0))]
    parts += plate_extension()
    parts.append(C.ring(rt + 0.15, rt + PL['collar_wall'], z0 + t - 0.01, PL['collar_h']))
    s = s.fuse(parts).removeSplitter()
    holes = [cyl(rt + 0.15, t + 2, (0, 0, z0 - 1)), cyl(MOTOR_HOLE_R, t + 2, (mc[0], mc[1], z0 - 1))]
    r0, r1, hw = MOTOR_NOTCH
    notch = box(r0, r1, -hw, hw, z0 - 1, z0 + t + 1)
    notch.rotate(V(), V(0, 0, 1), PLANET['phi_drive'])
    notch.translate(V(mc[0], mc[1], 0))
    holes.append(notch)
    for psi in BRIDGE['ear_psi']:
        a = math.radians(PLANET['phi_drive'] + psi)
        holes.append(cyl(M3['clear'] / 2, t + 2, (mc[0] + BRIDGE['ear_r'] * math.cos(a), mc[1] + BRIDGE['ear_r'] * math.sin(a), z0 - 1)))
    for ang in SW['servo_angles_deg']:
        holes.append(C.rotz(cyl(PL['rod_hole_d'] / 2, t + 2, (C.stat_ball_local(0).x, 0, z0 - 1)), ang))
    for phi in PLANET['phi_idlers']:
        cx, cy = polar(PLANET['centre'], phi)[:2]
        for sgn in (-1, 1):
            dx, dy = _carrier_bolt_local(phi, sgn)
            holes.append(cyl(M3['clear'] / 2, t + 2, (cx + dx, cy + dy, z0 - 1)))
    holes.append(C.box(-rt - PL['collar_wall'] - 1, -rt + 1, -0.6, 0.6, z0 + t, z0 + t + PL['collar_h'] + 1))
    holes += plate_holes()
    return s.cut(Part.makeCompound(holes)).removeSplitter()
