"""Own R380 propeller proposal. Millimetres; no OEM or aerodynamic approval.

CCW is viewed from +Z toward the vehicle: LE points in +tangent, LE is
higher than TE. CW mirrors Y only, preserving the upward-facing camber.
"""
import math
import FreeCAD as A
import Part
V=A.Vector

def intersection_volume(a,b):
    """Handle OCC's empty-common exception by an independently valid subtraction."""
    aa=a.BoundBox;bb=b.BoundBox
    if any(min(getattr(aa,d+'Max'),getattr(bb,d+'Max'))-max(getattr(aa,d+'Min'),getattr(bb,d+'Min'))<=1e-7 for d in ['X','Y','Z']):return 0.0
    try:
        s=a.common(b)
        return 0.0 if s.isNull() else max(0.0,s.Volume)
    except ValueError as error:
        if 'NullShapeException' not in str(error):raise
        remainder=a.cut(b)
        assert not remainder.isNull() and remainder.isValid()
        delta=a.Volume-remainder.Volume
        assert delta>=-1e-5
        return max(0.0,delta)

def section_parameters(p,r):
    ss=p['sections_r_chord_pitch_tc_axis']
    for a,b in zip(ss,ss[1:]):
        if a[0]<=r<=b[0]:
            f=(r-a[0])/(b[0]-a[0]);return [r]+[a[i]+f*(b[i]-a[i]) for i in range(1,5)]
    raise ValueError(r)

def foil_point(p,section,u,upper=True,inset=0):
    r,c,beta,tc,axis=section;m=p['airfoil_camber_fraction'];q=p['airfoil_camber_position_fraction']
    if u<q:
        yc=m/q**2*(2*q*u-u*u);slope=2*m/q**2*(q-u)
    else:
        yc=m/(1-q)**2*((1-2*q)+2*q*u-u*u);slope=2*m/(1-q)**2*(q-u)
    yt=5*tc*(.2969*math.sqrt(u)-.126*u-.3516*u*u+.2843*u**3-.1036*u**4)+p['trailing_edge_half_mm']/c*u**8
    theta=math.atan(slope);sign=1 if upper else -1
    x=u-sign*yt*math.sin(theta);z=yc+sign*yt*math.cos(theta)-sign*inset/c
    b=math.radians(beta);y=(axis-x)*c*math.cos(b)-z*c*math.sin(b);z=(axis-x)*c*math.sin(b)+z*c*math.cos(b)
    return V(r,y,z)

def spline(points):
    c=Part.BSplineCurve();c.interpolate(points);return c.toShape()

def foil_wire(p,section):
    n=p['profile_points_per_surface']-1;us=[(1-math.cos(math.pi*i/n))/2 for i in range(n+1)]
    upper=[foil_point(p,section,u,True) for u in us];lower=[foil_point(p,section,u,False) for u in reversed(us)]
    return Part.Wire([spline(upper),Part.makeLine(upper[-1],lower[0]),spline(lower)])

def cavity_wire(p,r,limits):
    sec=section_parameters(p,r);u0,u1=limits;us=[u0+(u1-u0)*i/16 for i in range(17)];d=p['skin_chord_normal_allowance_mm']
    top=[foil_point(p,sec,u,True,d) for u in us];bottom=[foil_point(p,sec,u,False,d) for u in reversed(us)]
    # Explicitly reject a collapsed inner section rather than silently invert it.
    for u in us:
        a=foil_point(p,sec,u,True,d);b=foil_point(p,sec,u,False,d)
        assert (a-b).Length>.05,(r,u)
    return Part.Wire([spline(top),Part.makeLine(top[-1],bottom[0]),spline(bottom),Part.makeLine(bottom[-1],top[0])])

def rounded_plate(x0,x1,width,z,h,r):
    # Constant-radius XY outline, planar mounting faces.
    y0=-width/2;y1=width/2
    edges=[]
    for a,b in [((x0+r,y0),(x1-r,y0)),((x1,y0+r),(x1,y1-r)),((x1-r,y1),(x0+r,y1)),((x0,y1-r),(x0,y0+r))]:
        edges.append(Part.makeLine(V(*a,z),V(*b,z)))
    for x,y,ang in [(x1-r,y0+r,-90),(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180)]:
        edges.append(Part.ArcOfCircle(Part.Circle(V(x,y,z),V(0,0,1),r),math.radians(ang),math.radians(ang+90)).toShape())
    return Part.Face(Part.Wire(Part.__sortEdges__(edges))).extrude(V(0,0,h))

def rotated(s,deg):
    s=s.copy();s.rotate(V(),V(0,0,1),deg);return s

def bore(s,x,y,r,z,h):return s.cut(Part.makeCylinder(r,h,V(x,y,z)))

def blade(p):
    outer=Part.makeLoft([foil_wire(p,s) for s in p['sections_r_chord_pitch_tc_axis']],True,False)
    # Cylindrical clipping guarantees a real R380 swept radius, including chord.
    outer=outer.common(Part.makeCylinder(p['rotor_radius_mm'],200,V(0,0,-100)))
    assert outer.isValid() and len(outer.Solids)==1
    root=rounded_plate(p['root_start_mm'],p['root_end_mm'],p['root_width_mm'],-4,8,4)
    full=outer.fuse(root).removeSplitter()
    # Defined flat bearing faces in the reinforced root, continuing2mm beyond
    # the clamp plates. The airfoil loft is relieved here; it must not penetrate
    # the hub or clamp plate as it begins to twist. This is a root machining/
    # tooling contour, not a claimed constant-thickness airfoil at the clamp.
    end=p['flat_transition_end_mm'];start=p['root_start_mm']-1
    for z in [4,-100]:
        height=100 if z==4 else 96
        full=full.cut(Part.makeBox(end-start,200,height,V(start,-100,z)))
    full=full.removeSplitter();assert full.isValid() and len(full.Solids)==1
    cores=[]
    for limits in p['cavity_u_ranges']:
        core=Part.makeLoft([cavity_wire(p,r,limits) for r in p['cavity_stations_mm']],True,False).common(outer)
        assert core.isValid() and len(core.Solids)==1
        cores.append(core)
    skin=full
    for core in cores:skin=skin.cut(core)
    for r in p['root_bolt_radii_mm']:skin=bore(skin,r,0,p['root_bore_mm']/2,-6,12)
    skin=skin.removeSplitter();assert skin.isValid() and len(skin.Solids)==1
    return full,skin,cores

def hub(p):
    h=p['hub_thickness_mm'];s=Part.makeCylinder(40,h)
    for a in [0,120,240]:s=s.fuse(rotated(rounded_plate(25,p['hub_arm_end_mm'],44,0,h,6),a))
    s=s.removeSplitter();s=bore(s,0,0,6,-1,h+2)
    for i in range(p['hub_motor_holes']):
        a=2*math.pi*i/p['hub_motor_holes']+math.radians(p['hub_motor_hole_phase_deg']);r=p['hub_motor_pcd_mm']/2;s=bore(s,r*math.cos(a),r*math.sin(a),p['hub_motor_clearance_mm']/2,-1,h+2)
    for a in [0,120,240]:
        for r in p['root_bolt_radii_mm']:s=bore(s,r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),2.75,-1,h+2)
    assert s.isValid() and len(s.Solids)==1;return s

def cap(p):
    s=rounded_plate(p['root_start_mm'],p['root_end_mm'],p['cap_width_mm'],0,p['cap_thickness_mm'],4)
    for r in p['root_bolt_radii_mm']:s=bore(s,r,0,2.75,-1,p['cap_thickness_mm']+2)
    return s

def mirrored(s):
    # OCC rigid mirror preserves analytical surfaces and volume. transformGeometry
    # unnecessarily approximates some trimmed surfaces and changes mass slightly.
    out=s.mirror(V(),V(0,1,0))
    assert out.isValid() and len(out.Solids)==1
    assert abs(out.Volume-s.Volume)<1e-7
    return out
