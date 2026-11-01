"""P14 central, back-to-back MN1330 architecture. All sizes mm.

This builds an engineering revision, never a production certificate. Custom
metal structure is aluminium; bearing races and purchased OEM internals retain
their proper materials. Main motor thrust is bypassed by separate rotor bearings.
"""
import sys,math,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
from kinematik import derive,solve,D,rz
import gelenke as J
V=A.Vector
def source_hash():
    h=hashlib.sha256()
    for name in ['geometrie.py','gelenke.py','kinematik.py']:h.update(name.encode()+b'\0'+(H/name).read_bytes())
    return h.hexdigest()
def box(dx,dy,dz,x=0,y=0,z=0):return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(r,h,z=0,x=0,y=0):return Part.makeCylinder(r,h,V(x,y,z))
def ring(ri,ro,z,h):return cyl(ro,h,z).cut(cyl(ri,h+2,z-1))
def axial(r,h,x,y=0,z=0):return Part.makeCylinder(r,h,V(x,y,z),V(1,0,0))
def annx(ri,ro,x,h):return axial(ro,h,x).cut(axial(ri,h+2,x-1)) if ri>0 else axial(ro,h,x)
def hexnut_x(x,length,af,bore):
    pts=[V(x,*p) for p in xy(6,af/math.sqrt(3),30)]
    return Part.Face(Part.Wire(Part.makePolygon(pts+[pts[0]]).Edges)).extrude(V(length,0,0)).cut(axial(bore,length+2,x-1))
def xy(n,r,phase=0):return [(r*math.cos((phase+360*i/n)*D),r*math.sin((phase+360*i/n)*D)) for i in range(n)]
def holes(s,points,r,z,h):
    for x,y in points:s=s.cut(cyl(r,h,z,x,y))
    return s
def rot(s,a):s=s.copy();s.rotate(V(),V(0,0,1),a);return s
def moved(s,x=0,y=0,z=0):s=s.copy();s.translate(V(x,y,z));return s
def link(radius,p0,p1,bore=0):
    a,b=V(*p0),V(*p1);d=b-a;s=Part.makeCylinder(radius,d.Length,a,d)
    if bore:s=s.cut(Part.makeCylinder(bore,d.Length+2,a-d/d.Length,d))
    return s
def sector(ri,ro,z,h,a0,a1):return rot(Part.makeCylinder(ro,h,V(0,0,z),V(0,0,1),a1-a0).cut(cyl(ri,h+2,z-1)),a0)
def clean(s):
    candidate=s.removeSplitter()
    if candidate.isValid() and len(candidate.Solids)==len(s.Solids) and (not s.isValid() or abs(candidate.Volume-s.Volume)<max(1e-5,abs(s.Volume)*1e-7)):return candidate
    return s
def profile(g,q,r):
    start=q['blade_root_mm'];t=min(1,max(0,(r-start-75)/105))
    return max(g['root_tc_min'],35.4/g['chord_mm'])*(1-t)+g['airfoil_tc']*t
def thick(g,q,r,u):
    tc=profile(g,q,r);return 5*tc*g['chord_mm']*(.2969*math.sqrt(max(u,0))-.1260*u-.3516*u*u+.2843*u**3-.1036*u**4)
def airfoil(g,q,r,inside=0):
    # Inner contour stays inside the outer foil using a scaled radial contour;
    # web/cap sizes are subsequently called out and screened separately.
    points=[];us=[(1-math.cos(math.pi*i/48))/2 for i in range(49)]
    for sign,values in [(1,us),(-1,list(reversed(us))[1:-1])]:
        for u in values:
            y=(u-g['pitch_axis_fraction'])*g['chord_mm']
            z=sign*thick(g,q,r,u)
            if inside:
                y=(.5-g['pitch_axis_fraction'])*g['chord_mm']+(y-(.5-g['pitch_axis_fraction'])*g['chord_mm'])*.97
                z*=max(.45,1-2*inside/(g['chord_mm']*profile(g,q,r)))
            points.append(V(r,y,z))
    # Nonzero trailing edge is a deliberate manufacturable geometry proposal.
    if (points[-1]-points[0]).Length<1e-8:points.pop()
    return Part.Wire(Part.makePolygon(points+[points[0]]).Edges)
def blade(g,q):
    start,end=q['blade_root_mm'],g['rotor_radius_mm'];stations=sorted(set([start,start+2,start+70,start+75,start+120,start+180,end-3,end]))
    outer=Part.makeLoft([airfoil(g,q,r) for r in stations],True,True)
    inner=Part.makeLoft([airfoil(g,q,r,g['skin_mm']) for r in stations[1:-1]],True,True)
    shell=outer.cut(inner)
    root=inner.common(box(75,200,100,start,-80,-50))
    spar=outer.common(box(end-start-70,g['spar_width_mm'],100,start+70,-10,-50))
    cavities=[]
    for r in [start+75,start+120,start+180,end-5]:
        hh=min(2*thick(g,q,r,u) for u in [(g['pitch_axis_fraction']-10/g['chord_mm']),(g['pitch_axis_fraction']+22/g['chord_mm'])])-2*(g['skin_mm']+g['spar_wall_mm'])
        hh=max(2,hh);w=g['spar_width_mm']-2*g['spar_wall_mm'];y0=6-w/2
        p=[V(r,y0,-hh/2),V(r,y0+w,-hh/2),V(r,y0+w,hh/2),V(r,y0,hh/2)]
        cavities.append(Part.Wire(Part.makePolygon(p+[p[0]]).Edges))
    spar=spar.cut(Part.makeLoft(cavities,True,True))
    flange=annx(16.2,24,start,8)
    s=shell.fuse(root).fuse(spar).fuse(flange).cut(axial(16.2,80,start-1))
    s=s.cut(annx(16.2,39.2,start+8,4.1))
    for y,z in xy(4,32,45):s=s.cut(Part.makeCylinder(3.2,13,V(start-1,y,z),V(1,0,0)))
    for y,z in xy(4,32,45):s=s.cut(Part.makeCylinder(5.5,6.2,V(start+11.9,y,z),V(1,0,0)))
    if not s.isValid():s.fix(1e-7,1e-7,1e-5)
    return s

def build(c):
    g=c['geometry'];q=derive(c);r=q['root_r_mm'];br=q['blade_root_mm'];level=q['level_mm'];sz=g['swash_z_mm'];n=g['blades_per_rotor'];neutral=solve(c)
    parts={};rows=[];q['neutral']=neutral
    def define(id,name,s,mat,kind='Sonderteil',mass=None,note='Festigkeit, Passungen und Freigabe offen'):
        zs=g['servo_z_mm']
        sockets={
            'F5_MOTOR':([0,0,91],[0,0,1],4,2.5),
            'F6_STATOR':([0,0,2],[0,0,-1],5,3),
            'F6_HUB':([0,0,level+18],[0,0,1],5,3),
            'F4_CRADLE':([0,0,zs-22.2],[0,0,1],3,2),
            'F6_SUPPORT':([0,0,zs-23.4],[0,0,1],5,3),
            'F4_HOUSING':([0,0,86],[0,0,-1],3,2),
            'F3_CAP':([0,0,153],[0,0,1],2.5,1.5),
            'F3_ROOT_CAP':([r-7,0,0],[-1,0,0],2.5,1.5),
            'F6_ROOT_OUT':([r+67.6,0,0],[1,0,0],5,3),
            'F6_PITCH_END':([r-32,0,0],[-1,0,0],5,3),
            'F6_ROOT':([br+18,0,0],[1,0,0],5,3),
            'F8_END':([br+82,0,0],[1,0,0],6,4),
            'A18B':([r-16,-16,23],[0,0,1],3,2)}
        sockets['F3_TAUMEL']=([0,0,sz+22],[0,0,1],2.5,1.5)
        sockets['F3_CUP']=([0,0,sz+19],[0,0,1],2.5,1.5)
        socket=None
        if id in sockets:
            p,b,af,depth=sockets[id];out=V(*b)
            cutter=J.hex_x(0,depth+.05,af,0)
            cutter.Placement=A.Placement(V(*p)+out*.05,A.Rotation(V(1,0,0),-out))
            s=s.cut(cutter);socket=dict(face_mm=p,access_axis=b,af_mm=af,depth_mm=depth)
        if not s.isValid():s=clean(s)
        if s.Volume<0:s.reverse()
        if not s.isValid() or len(s.Solids)!=1 or s.Volume<=0:raise ValueError((id,s.isValid(),len(s.Solids),s.Volume,[(t.Volume,list(t.CenterOfMass)) for t in s.Solids]))
        parts[id]=dict(id=id,name=name,shape=s,material=mat,kind=kind,mass_override_kg=mass,note=note,socket=socket)
    def put(id,name,shape=None,frame='fixed',a=0,z=0,theta=0,blade_index=-1,servo_index=-1,absolute=False,**meta):
        s=(shape or parts[id]['shape']).copy()
        if not absolute:
            if servo_index>=0 and id in ['SERVO','A25','KUPP','B6002','A26','A26K','A26S','A26N','A27','F4_CRADLE','W4']:s.translate(V(g['servo_r_mm']-200,0,0))
            if theta:s.rotate(V(),V(1,0,0),theta)
            s=rot(s,a);s.translate(V(0,0,z))
        rows.append(dict(id=id,name=name,shape=s,frame=frame,a=a,z=z,theta=theta,blade_index=blade_index,servo_index=servo_index)|meta)
    # Frame plates and columns stay in the centre, wholly below the upper rotor.
    plate=ring(10,76,6,8)
    for a in [45,135,225,315]:
        plate=plate.fuse(rot(box(42,24,8,70,-12,6),a))
    plate=holes(plate,xy(4,25),3.2,5,10)
    for x,y in xy(4,25):plate=plate.cut(cyl(5.5,2,6,x,y))
    plate=holes(plate,xy(4,95,45),3.3,5,10)
    define('A01','Zentrale Statorplatte',plate,'Aluminium7075-T6',note='8mm; 4×M6/PCD50;2mm Kopfsenkung; M6×12 ->6mm Motoreingriff angenommen')
    define('A02','Zentralkaefig-Druckhuelse76',ring(5.1,8,14,76),'Aluminium6082-T6',note='16×10.2 Rohr; vier Stützen statt Perimeterrahmen')
    bridge=ring(47,67,90,6)
    for a in [45,135,225,315]:bridge=bridge.fuse(rot(box(53,22,6,58,-11,90),a))
    bridge=holes(bridge,xy(4,95,45),3.3,89,8)
    bridge=bridge.fuse(ring(47,63,96,2))
    bridge=holes(bridge,xy(4,59),2.2,89,10)
    define('A03','Zentrales Hauptlagerjoch',bridge,'Aluminium7075-T6')
    motor=holes(cyl(75,66,14),xy(4,25),3.15,13,7);motor=holes(motor,xy(12,20),2.65,76,5)
    define('MN1330','T-Motor MN1330 – Zeichnungsreferenz',motor,'Kaufteil','Motor',c['operating'].get('motor_mass_each_kg',c['operating'].get('motor_mass_each_assumed_kg',2.0)),'Ø150×66 nach Nutzerzeichnung, XLS nennt65mm;2.75kg inkl Kabel nach XLS;3400W für180s, NS52x20-Prüfwerte bis16270W mit unbekannter Haltedauer; keine Dauerdaten')
    shaft=ring(25.2,30,86,level-91).fuse(cyl(44,6,80)).fuse(ring(25.2,40,94,4))
    shaft=holes(shaft,xy(12,20),2.75,79,8)
    shaft=shaft.cut(box(5,70,level-148,28.5,-35,148)).cut(box(5,70,level-148,-33.5,-35,148))
    shaft=shaft.cut(box(3.5,3,level-147,-1.75,28.7,148))
    define('A04','Haupt-Hohlwelle mit abnehmbarem Rotorflansch',shaft,'Aluminium7075-T6',note='60/50.4; oberer Flansch separat montierbar; durchgehender unterbrochener M60x1.5-Bereich148..175 mit D57;12×M5/PCD40')
    hole=cyl(30.05,16,level-25).cut(box(5,70,16,28.55,-35,level-25)).cut(box(5,70,16,-33.55,-35,level-25))
    flange=cyl(55,12,level-24).cut(hole).fuse(ring(35.5,40,level-12,2))
    flange=holes(flange,xy(6,48),2.55,level-25,14)
    define('A04F','Abnehmbarer D57-Rotorflansch',flange,'Aluminium7075-T6',note='D57-Sitz,80mm Zentrierbund; sechs M6/PCD96 von oben direkt in12mm Alu-Gewinde; beide7212 montierbar')
    bh=ring(41,63,98,50).cut(cyl(55.05,22,98)).cut(cyl(55.05,22,126))
    bh=holes(bh,xy(4,59),1.65,97,11);bh=holes(bh,xy(4,59),1.25,140,9)
    define('A05','Hauptlagerpatrone',bh,'Aluminium7075-T6',note='Zwei7212B in DB-Anordnung; Innenringdistanz6mm; Montage-/Thermalspiel zu qualifizieren')
    define('B7212','Hauptlager7212B',ring(30.02,55,0,22),'Wälzlagerstahl','Normlager',.65,'60×110×22;0.65kg Masseannahme, reale Lieferdaten/Schulterradien offen')
    define('A06O','Verschraubter Hauptlager-Aussendeckel',holes(ring(47,63,148,2),xy(4,59),1.7,147,4),'Aluminium7075-T6')
    define('A07','Hauptlager-Innendistanz',ring(30.05,39.5,120,6),'Aluminium7075-T6')
    def lockwasher(ri,ro,z):
        s=ring(ri,ro,z,1).fuse(box(3,2,1,-1.5,28.85,z))
        return s.fuse(box(1.2,3,5,ro-1.5,-1.5,z+1))
    def locknut(ri,ro,z):return ring(ri,ro,z,6).cut(box(4,3.5,8,ro-3,-1.75,z-1))
    define('A08W','Hauptlager-Sicherungsblech',lockwasher(30.05,40,148),'Aluminium1050',note='Innennase in durchgehender Wellennut; Aussentab in Mutternut umlegen, nach Demontage ersetzen')
    define('A08','Hauptlager-Klemmmutter M60',locknut(30.05,40,149),'Aluminium7075-T6',note='M60x1.5, mit Formschluss-Sicherungsblech; konkrete Lagervorspannung nach Lieferteil')
    define('A04W','Flansch-Sicherungsblech',lockwasher(30.05,35,level-12),'Aluminium1050')
    define('A04N','Flansch-Haltemutter M60',locknut(30.05,35,level-11),'Aluminium7075-T6',note='M60x1.5, D-Flansch formschluessig; keyed tab washer retains nut')
    # Root-only support: annular backbone, individual radial bearing cartridges.
    # Radial cartridge bores intersect the hub at the pitch plane, independent of spacing.
    # Integral radial bearing seats remove the separate housing-to-hub joints.
    gap=180/n+q['pitch_joint_delta_deg'];pr=q['phase_pin_r_mm']
    hub=ring(40.05,76,level-12,24).fuse(ring(64,80,level-35,23))
    # Continuous central load plate bypasses the lever openings and bearing
    # caps circumferentially. It replaces thin isolated cantilever webs.
    # Its outer radius follows the root seats, not the free blade tips.
    hub=hub.fuse(ring(64,r+50,level-35,8))
    for i in range(n):
        branch=box(r+56-55,62,24,55,-31,-12).fuse(axial(31,56,r))
        for y0,z0 in xy(3,30,90):branch=branch.fuse(axial(4.5,10,r,y0,z0))
        for y0,z0 in xy(6,32):branch=branch.fuse(axial(6,16,r+40,y0,z0))
        hub=hub.fuse(rot(branch,360*i/n).translated(V(0,0,level)))
    arm=rot(box(pr-110+6,8,8,110,-4,level-49),gap).fuse(cyl(8,8,level-49,*xy(1,pr,gap)[0]))
    arm=arm.fuse(rot(box(20,12,22,110,-6,level-49),gap))
    arm=arm.cut(cyl(3.1,10,level-50,*xy(1,pr,gap)[0]))
    hub=hub.fuse(arm).fuse(rot(arm,180))
    for i in range(n):
        cut=axial(21.2,17,r-26).fuse(axial(19.2,11,r-11)).fuse(axial(18.05,58,r-1)).fuse(axial(26.05,15,r)).fuse(axial(26.05,22,r+35))
        # Full inner opening: no disconnected pocket lips beside the lever.
        # The lower web is the continuous load path around this opening.
        cut=cut.fuse(box(26.35,85,47,r-26.25,-37,-20))
        # The bearing cap replaces this thin annulus; no cap embedded in the star.
        cut=cut.fuse(axial(31.1,4.1,r-4.1))
        hub=hub.cut(rot(cut,360*i/n).translated(V(0,0,level)))
        # Access for the positive axial lever retainer and the complete clevis.
        clear=axial(7,r-38,40)
        pc=V(r-20,g['pitch_lever_mm'],0);axis=V(*q['pitch_pin_axis_local'])
        a0,b0=neutral['pitch_points_mm'][0];away=V(*(b0[j]-a0[j] for j in range(3)))
        away=A.Rotation(V(1,0,0),-g['neutral_pitch_deg']).multVec(away);away=away/away.Length
        for theta0 in g['pitch_limits_deg']+[g['neutral_pitch_deg']]:
            envelope=Part.makeSphere(14,pc)
            envelope=envelope.fuse(Part.makeCylinder(8.8,40,pc-axis*19,axis))
            bp=pc+away*21;envelope=envelope.fuse(Part.makeCylinder(8,26,bp-axis*13,axis))
            envelope.rotate(V(),V(1,0,0),theta0);clear=clear.fuse(envelope)
        hub=hub.cut(rot(clear,360*i/n).translated(V(0,0,level)))
        for y0,z0 in xy(3,30,90):
            drill=Part.makeCylinder(1.25,9,V(r,y0,z0),V(1,0,0));hub=hub.cut(rot(drill,360*i/n).translated(V(0,0,level)))
        for y0,z0 in xy(6,32):
            drill=Part.makeCylinder(2.55,15,V(r+41,y0,z0),V(1,0,0));hub=hub.cut(rot(drill,360*i/n).translated(V(0,0,level)))
        lower,upper=neutral['pitch_points_mm'][i];t=(level-31-lower[2])/(upper[2]-lower[2])
        x=lower[0]+t*(upper[0]-lower[0]);y=lower[1]+t*(upper[1]-lower[1])
        hub=hub.cut(cyl(g['pitch_rod_port_radius_mm'],12,level-37,x,y))
    hub=holes(hub,xy(6,48),3.3,level-13,26)
    define('A09','Monolithischer Wurzelstern mit integralen Lagersitzen',hub,'Aluminium7075-T6',note='Ein CNC-Teil statt Stern plus8 verschraubten Patronen; geschlossene Lager-/Fliehkraftpfade im Zentrum')
    housing=annx(18.05,31,r,56).cut(axial(26.05,15,r)).cut(axial(26.05,15,r+35))
    define('A10','Radiale Blattlagerpatrone',housing,'Aluminium7075-T6',note='2×7205B25×52×15 in DB; radial beidseitig abstützen; kein Außen-/Spitzenlager')
    define('B7205','Pitchlager7205B',annx(12.52,26,0,15),'Wälzlagerstahl','Normlager',.12,'25×52×15; Paarabstimmung, Tragzahlen und Massendaten nach Lieferteil')
    cap=annx(22,31,r-4,4)
    for y0,z0 in xy(3,30,90):
        cap=cap.fuse(axial(4.5,4,r-4,y0,z0));cap=cap.cut(axial(1.7,6,r-5,y0,z0))
    define('A11','Verschraubter Pitchlager-Deckel',cap,'Aluminium7075-T6')
    outcap=annx(22.2,26,r+50,6).fuse(annx(22.2,31,r+56,4))
    for y0,z0 in xy(6,32):
        outcap=outcap.fuse(axial(6,4,r+56,y0,z0));outcap=outcap.cut(axial(3.3,6,r+55,y0,z0))
    define('A11O','Abnehmbarer Aussenlagerdeckel',outcap,'Aluminium7075-T6',note='Offenes Aussenlager-Montagefenster52.1mm; sechs M6/PCD64,14.4mm Eingriff')
    define('A12','Pitchlager-Innendistanz',annx(12.55,18,r+15,20),'Aluminium7075-T6')
    ps=axial(12.5,br+70-(r-25),r-25).fuse(annx(12.5,16,br,70)).fuse(axial(39,12,br-12))
    ps=ps.cut(axial(7,br+79-(r-8),r-8)).cut(box(14,30,8,r-25,-15,10.5))
    ps=ps.cut(axial(2.55,15,r-25)).cut(box(12,3,2,r-11,-1.5,11.4))
    for id,index in [('A13',0),('A13U',-24)]:
        shaft=ps.copy()
        for y,z in xy(4,32,45+index):shaft=shaft.cut(Part.makeCylinder(2.55,14,V(br-13,y,z),V(1,0,0)))
        define(id,'Pitchwelle25 mit Integralflansch und Wurzelmandrel'+(' oben' if index else ' unten'),shaft,'Aluminium7075-T6',note='Ein CNC-Teil statt Welle/Innenplatte/Einsatz/Endschraube;12mm Integralflansch,4xM6/PCD64; obere Bohrungen-24Grad indexiert; Ermuedung/Flankenpressung offen')
    define('A13C','Abnehmbare Pitchlager-Schulter',annx(12.55,18,r+50,4),'Aluminium7075-T6',note='Separater Ring statt unmontierbarem Integralbund')
    define('A13D','Pitchlager-Aussendistanz',annx(12.55,18,r+54,br-12-(r+54)),'Aluminium7075-T6')
    n25=annx(12.55,19,r-10,7).cut(box(9,4,3.2,r-11,16.8,-1.6))
    define('A14','Pitchlager-Klemmmutter25',n25,'Aluminium7075-T6',note='M25x1.5; Sicherungsblech mit Innennase und Aussentab')
    w25=annx(12.55,19,r-3,1).fuse(box(1,2.4,1.4,r-3,-1.2,11.6)).fuse(box(4,1.2,2.4,r-7,17.4,-1.2))
    define('A14W','Pitchlager-Sicherungsblech',w25,'Aluminium1050')
    define('A14S','Pitchlager-Anlagedistanz2',annx(12.55,18,r-2,2),'Aluminium7075-T6')
    define('A18S','Pitchhebel-Vorderdistanz5',annx(12.55,18,r-25,5),'Aluminium7075-T6')
    define('A18T','Pitchhebel-Hinterdistanz2',annx(12.55,18,r-12,2),'Aluminium7075-T6')
    define('A18W','Axiale Pitchhebel-Scheibe',annx(3.2,18,r-26,1),'Aluminium7075-T6')
    define('F6_PITCH_END','Pitchhebel-AxialschraubeM6x14',axial(2.45,14,r-26).fuse(axial(5,6,r-32)),'Aluminium7075-T6',note='Positiver Endanschlag;13mm Gewindeeingriff; Sicherungskleber und Kontrollmarke, Anzug qualifizieren')
    grip=annx(16.2,39,br+8,4)
    for y,z in xy(4,32,45):grip=grip.cut(Part.makeCylinder(3.2,6,V(br+7,y,z),V(1,0,0)))
    define('A16A','Aeussere CFK-Wurzelklemmplatte',grip,'Aluminium7075-T6',note='Vier M6/PCD64 von aussen in12mm Integralflansch; CFK-Klemmdruck und Ermuedung qualifizieren')
    # Upper foil is indexed -24 degrees relative to its pitch lever. With
    # counter-rotation and the lower pod turned over, both foils then have the
    # leading edge above the trailing edge. The upper inner plate compensates
    # the D-key by +24 degrees; the shaft and pitch lever keep their own datum.
    define('F6_ROOT','CFK-Klemmung M6x25 von aussen',axial(2.45,25,br-13).fuse(axial(5,6,br+12)),'Aluminium7075-T6',note='SW5 von aussen;12mm Gewindeeingriff im Integralflansch; Alu-Verbindung und CFK-Lip qualifizieren')
    print('CFK-Flügel aufbauen',flush=True)
    define('CFK01','Freitragender CFK-Fluegel mit Kastenspar',blade(g,q),'CFK',note='Kontinuierliche Innenanbindung; 1.2mm nominale Vertikalschale; interner geschlossener Kastenspar und Wurzelaufdickung; Laminatnachweis offen')
    pc=V(r-20,g['pitch_lever_mm'],0);axis=V(*q['pitch_pin_axis_local'])
    a0,b0=neutral['pitch_points_mm'][0];away=A.Rotation(V(1,0,0),-g['neutral_pitch_deg']).multVec(V(*(b0[j]-a0[j] for j in range(3))));away=away/away.Length
    lev=axial(20,8,r-20).fuse(box(8,17,8,r-20,0,-4)).fuse(J.fork(pc,axis,away))
    bp=pc+away*21;anchor=V(r-16,14,8);lev=lev.fuse(Part.makeCylinder(4,(bp-anchor).Length,anchor,bp-anchor))
    lev=lev.fuse(cyl(4.5,15,4,r-16,-16))
    d_hole=axial(12.6,10,r-21).cut(box(10,30,8,r-21,-15,10.6))
    lev=lev.cut(d_hole).cut(box(12,22,1,r-22,-22,-.5))
    lev=lev.cut(cyl(2.2,20,0,r-16,-16)).cut(cyl(1.65,13,-13,r-16,-16))
    lev=lev.cut(axial(18.1,5,r-25)).cut(axial(18.1,2,r-12))
    define('A18','Pitchhebel42 mit D-Flach und Klemmung',lev,'Aluminium7075-T6',note='D-Flach10.5/10.6mm zur Welle; M4×30-Klemmung axial sichern; Füge-/Ermüdungsnachweis offen')
    define('A18B','Pitchhebel-KlemmschraubeM4x30',cyl(1.6,30,-11,r-16,-16).fuse(cyl(3.5,4,19,r-16,-16)),'Aluminium7075-T6',note='ISO4762-Konturfamilie, keine übertragene Stahl8.8-Festigkeit; Anzug/Alu-Schraube qualifizieren')
    # Lightweight spherical slider instead of a huge GE140 steel bearing.
    ball=Part.makeSphere(70,V(0,0,sz)).common(box(150,150,36,-75,-75,sz-18)).cut(cyl(63.3,40,sz-20))
    define('A19','Sphaerischer Schiebekragen',ball,'Aluminium7075-T6',note='Eigenkonstruktion, nicht als Norm-Gelenklager ausgegeben; verschleißarme Auskleidung und Spiel prüfen')
    define('POM01','Gleitfolien-Buchse',ring(63.05,63.25,sz-18,36),'PTFE','Verschleissteil',note='0.2mm nominale Folie; realen Verbund, Kriechen und Reibung qualifizieren')
    cup=ring(63.4,80,sz-16,32).cut(Part.makeSphere(71,V(0,0,sz)))
    cup=cup.fuse(ring(71.05,80,sz+4,4))
    sy=g['servo_joint_y_mm']
    sx=g['servo_swash_x_mm']
    for a in [0,120,240]:
        web=box(36,16,6,64,sy-8,sz-18).fuse(box(sx-114,16,6,95,sy-8,sz-23))
        web=web.fuse(J.fork(V(sx,sy,sz-20),V(0,1,0),V(-1,0,0)))
        cup=cup.fuse(rot(web,a))
    lower_cup=cup.common(box(600,600,sz,-300,-300,0))
    upper_cup=cup.common(box(600,600,50,-300,-300,sz))
    lower_cup=holes(lower_cup,xy(4,76,45),1.25,sz-7,8)
    upper_cup=holes(upper_cup,xy(4,76,45),1.7,sz-1,18)
    define('A20','Stationaerer Taumeltraeger Unterhaelfte',lower_cup,'Aluminium7075-T6',note='Geteilte Kugelpfanne: Ball und PTFE montierbar; Phase durch eine gefuehrte RRS-Anlenkung')
    define('A20C','Stationaere Kugelpfanne Oberhaelfte',upper_cup,'Aluminium7075-T6',note='Vier M3/PCD152,6mm Eingriff, vor Montage des Rotationslagers schliessen')
    liner=Part.makeSphere(70.95,V(0,0,sz)).cut(Part.makeSphere(70.05,V(0,0,sz))).common(box(150,150,32,-75,-75,sz-16))
    define('POM02','Sphaerische Gleitpfanne unten',liner.common(box(200,200,sz,-100,-100,0)),'PTFE','Verschleissteil')
    define('POM02U','Sphaerische Gleitpfanne oben',liner.common(box(200,200,50,-100,-100,sz)),'PTFE','Verschleissteil')
    define('B61832','Rotationslager61832',ring(80.02,100,sz-4,20),'Wälzlagerstahl','Normlager',.90,'160×200×20; Massendatum0.90kg angenommen, Lieferdaten prüfen')
    outer=ring(100.05,107,sz-4,20).fuse(ring(95,107,sz-8,4))
    outer=holes(outer,xy(4,103,45),1.25,sz+10,7)
    define('A21C','Abnehmbarer Rotationslagerdeckel',holes(ring(95,107,sz+16,3),xy(4,103,45),1.7,sz+15,5),'Aluminium7075-T6',note='Vier M3/PCD206;61832 von oben montierbar')
    for i in range(n):
        a=q['pitch_joint_delta_deg']+i*360/n
        jr=g['swash_joint_r_mm']
        loweraxis=V(*q['pitch_lower_pin_axis'])
        tab=box(jr+7-103,12,8,103,15,sz-4).fuse(J.fork(V(jr,0,sz),loweraxis,V(0,1,0)))
        tab=tab.cut(Part.makeCylinder(4.1,28,V(jr,0,sz)-loweraxis*14,loweraxis))
        outer=outer.fuse(rot(tab,a))
    ear=rot(box(pr-103+7,14,6,103,-7,sz-4),gap)
    slot=box(12,8.3,10,pr-6,-4.15,sz-6);ear=ear.cut(rot(slot,gap));outer=outer.fuse(ear).fuse(rot(ear,180))
    define('A21','Rotierender Taumelring',outer,'Aluminium7075-T6')
    define('A22','Taumellager-Klemmmutter160',ring(80.05,85,sz+16,4),'Aluminium7075-T6')
    ph=cyl(4,level-49-(sz-12),sz-12,*xy(1,pr,gap)[0]).fuse(cyl(2.6,10,level-49,*xy(1,pr,gap)[0]))
    define('A24','Phasen-Gleitstift8',ph,'Aluminium7075-T6',note='D8-Schulter/M6-Anker; harteloxiert; tangentiale Spielführung mit wechselbarer Gleitbuchse, keine Schubführung')
    # Real selected servo, manufacturer dimensions; source STEP retrieval blocked.
    zs=g['servo_z_mm'];sh=g['servo_horn_mm']
    case=box(54,122,54,173,4,zs-27).fuse(Part.makeCylinder(27,4,V(200,0,zs),V(0,1,0)))
    define('SERVO','DYNAMIXEL PH54-200-S500-R',case,'Kaufteil','Servo',c['servo']['mass_kg'],'Herstellernennmaße54×126×54;0.855kg;44.7Nm continuous@24V; OEM-STEP/Horn-/Montagebezug offen')
    baseplate=box(64,200,4,168,-70,zs-31).cut(box(50,100,6,175,12,zs-32))
    baseplate=baseplate.cut(box(34,20,6,162,-50,zs-32))
    for xx in [178,188,198,208]:baseplate=baseplate.cut(cyl(2.2,6,zs-32,xx,-6))
    cradle=baseplate.fuse(box(3,132,60,168,-2,zs-27)).fuse(box(3,132,60,229,-2,zs-27))
    cradle=cradle.fuse(box(64,132,3,168,-2,zs+30))
    # Separate externally supported bellcrank keeps >40N pushrod loads off servo bearings.
    for yy in [-66,-24]:
        boss=Part.makeCylinder(20,9,V(200,yy,zs),V(0,1,0)).cut(Part.makeCylinder(16.05,11,V(200,yy-1,zs),V(0,1,0)))
        cradle=cradle.fuse(boss).fuse(box(12,9,27,194,yy,zs-27))
        cradle=cradle.cut(Part.makeCylinder(16.05,11,V(200,yy-1,zs),V(0,1,0)))
    define('A25','Servo-Sattel und Umlenk-Lagerbock',cradle,'Aluminium7075-T6',note='Klemmhalter ist Vorentwurf; OEM-Montage-/Kühlfreigaben fehlen')
    define('B6002','Umlenkungslager6002',Part.makeCylinder(16,9,V(),V(0,1,0)).cut(Part.makeCylinder(7.52,11,V(0,-1,0),V(0,1,0))),'Wälzlagerstahl','Normlager',.03,'15×32×9; externe Lager tragen Gestängelast; Liefermasse angenommen')
    shaft=Part.makeCylinder(7.5,68,V(200,-70,zs),V(0,1,0)).fuse(Part.makeCylinder(10,13,V(200,-57,zs),V(0,1,0)))
    shaft=shaft.cut(box(20,6,5,190,-8,zs+6.4)).cut(box(5,8,5,197.5,-44,zs+5.5))
    define('A26','Umlenkwelle15 mit Passfeder und Schulter',shaft,'Aluminium7075-T6',note='Runde Lagerzapfen; DIN6885-Familie5x5x8 am Hebel, D-Flach an OEM-Kupplungsreserve; zwei M15x1-Sondermuttern; Kerbfestigkeit/Preload offen')
    define('A26K','Passfeder5x5x8 Alu',box(4.98,8,4.98,197.51,-44,zs+5.51),'Aluminium7075-T6',note='DIN6885-Konturfamilie, Alu-Sonderteil; Flankenpressung und Lastwechsel qualifizieren')
    spacer=Part.makeCylinder(10,12,V(200,-36,zs),V(0,1,0)).cut(Part.makeCylinder(7.55,14,V(200,-37,zs),V(0,1,0)))
    define('A26S','Umlenkwellen-Distanzring',spacer,'Aluminium7075-T6')
    nut15=hexnut_x(0,4,19,7.55);nut15.rotate(V(),V(0,0,1),90);nut15.translate(V(200,-70,zs))
    define('A26N','Umlenkwellenmutter M15x1',nut15,'Aluminium7075-T6',note='Sondermutter mit19mm SW; Gewinde und Verliersicherung nominal/offen')
    horn=Part.makeCylinder(14,8,V(200,sy-4,zs),V(0,1,0)).fuse(J.fork(V(200-sh,sy,zs),V(0,1,0),J.unit([1,0,-.5]),24))
    hole=Part.makeCylinder(7.55,28,V(200,sy-14,zs),V(0,1,0)).fuse(box(5.1,8.2,5.1,197.45,sy-4.1,zs+5.45))
    horn=horn.cut(hole)
    for yy,hh in [(sy-14,10),(sy+4,10)]:horn=horn.cut(Part.makeCylinder(10.1,hh,V(200,yy,zs),V(0,1,0)))
    define('A27','Umlenk-Gabelhebel28',horn,'Aluminium7075-T6')
    hole=Part.makeCylinder(7.6,10,V(200,-9,zs),V(0,1,0)).cut(box(20,10,5,190,-9,zs+6.5))
    define('KUPP','Drehmomentkupplung zum OEM-Horn',Part.makeCylinder(12,8,V(200,-8,zs),V(0,1,0)).cut(hole),'Kaufteil','Anschlussreserve',.03,'D-Flach6.5 zur eigenen Welle; OEM-Horn/Flanschanschluss noch offen; keine erfundene Verzahnung')
    shift=g['servo_r_mm']-200
    support=box(130+shift,20,8,85,-10,zs-39).fuse(box(42,30,zs-31-6,78,-15,6)).fuse(box(45,28,8,170+shift,-14,zs-39))
    # Common carrier clears all four diagonal stator-plate arms at each of the
    # three servo azimuths. Bolt lands remain directly on the central block.
    for servo_az in [0,120,240]:
        for arm_az in [45,135,225,315]:
            support=support.cut(rot(box(42.6,24.6,8.2,69.7,-12.3,5.9),arm_az-servo_az))
    for xx in [87,111]:
        for yy in [-6.5,6.5]:support=support.cut(cyl(3.3,zs,5,xx,yy))
    for xx in [178,188,198,208]:support=support.cut(cyl(1.65,10,zs-40,xx+shift,-6))
    define('A28','Servotraeger-Ausleger',support,'Aluminium7075-T6',note='Vier M6 direkt auf Zentralblock; Fussausnehmungen mit0.3mm Abstand zu diagonalen Statorarmen')
    mid=ring(40,110,-6,12)
    for angle in [45,135,225,315]:mid=mid.fuse(rot(box(35,26,12,95,-13,-6),angle))
    for angle in range(0,360,60):mid=mid.fuse(rot(box(27,30,12,95,-15,-6),angle))
    mid=holes(mid,xy(4,122,45),4.3,-7,14)
    mid=holes(mid,xy(4,95,45),3.3,-7,14)
    for angle in range(0,360,60):
        for xx in [87,111]:
            for yy in [-6.5,6.5]:
                x0,y0,_=rz([xx,yy,0],angle*D);mid=mid.cut(cyl(2.55,14,-7,x0,y0))
    define('A29','Gemeinsamer Zentralblock und Nutzlastanschluss',mid,'Aluminium7075-T6',note='Ein Mittelblock für beide Motoren;4×M8-Anschluss im Zentrum, noch kein freigegebenes Personendeck')
    define('F5_MOTOR','Motorrotor M5x10',cyl(2.0,10,76).fuse(cyl(4.25,5,86)),'Aluminium7075-T6',note='Kern-/Kopfkontur;12×M5;4mm Motoreingriff Annahme')
    define('F6_STATOR','Motorstator M6x12',cyl(2.5,12,8).fuse(cyl(5,6,2)),'Aluminium7075-T6',note='Kern-/Kopfkontur;4×M6;6mm Motoreingriff Annahme')
    define('TIE6','Durchgehender Zentralanker M6',cyl(2.5,192,-96),'Aluminium7075-T6',note='Vier gemeinsame Zuganker statt doppelter Schrauben; Vorspannung/Ermüdung offen')
    nut=hexnut_x(0,5,10,2.6);nut.rotate(V(),V(0,1,0),-90)
    define('N6','Alu-Mutter M6',nut,'Aluminium7075-T6',note='ISO4032-Konturfamilie, Gewinde nominal; keine übertragene Stahlklassifizierung')
    define('F6_HUB','Hohlwellenflansch M6x40 von oben',cyl(2.5,40,level-28).fuse(cyl(5,6,level+12)),'Aluminium7075-T6',note='6xM6/PCD96, SW5 von oben;12mm Gewindeeingriff direkt im Rotorflansch')
    define('W6','Scheibe ISO7089-M6',ring(3.2,6,0,1.6),'Aluminium7075-T6','Normteil')
    define('W4','Scheibe ISO7089-M4',ring(2.15,4.5,0,.8),'Aluminium7075-T6','Normteil')
    define('F4_CRADLE','Servosattel M4x16',cyl(1.6,16,zs-42.2).fuse(cyl(3.5,4,zs-26.2)),'Aluminium7075-T6',note='Vier M4 von oben, vor Montage der Umlenkwelle;8mm Gewinde im Ausleger')
    define('F6_SUPPORT','Zentralanschluss M6x60',cyl(2.5,60,zs-89.4).fuse(cyl(5,6,zs-29.4)),'Aluminium7075-T6',note='Vier M6 je Servotraeger,12mm Eingriff im Zentralblock, Scheibe1.6mm')
    define('F4_HOUSING','Hauptlagerpatrone M4x16',cyl(1.6,16,90).fuse(cyl(3.5,4,86)),'Aluminium7075-T6',note='Vier M4, von unten vor Montage ueber Motor zugaenglich;8mm Eingriff')
    define('F3_CAP','Hauptlagerdeckel M3x8',cyl(1.2,8,142).fuse(cyl(2.75,3,150)),'Aluminium7075-T6',note='Vier M3 von oben;6mm Eingriff')
    define('F3_TAUMEL','Rotationslagerdeckel M3x8',cyl(1.2,8,sz+11).fuse(cyl(2.75,3,sz+19)),'Aluminium7075-T6',note='Vier M3,5mm Gewindeeingriff')
    define('F3_CUP','Kugelpfannenverbindung M3x22',cyl(1.2,22,sz-6).fuse(cyl(2.75,3,sz+16)),'Aluminium7075-T6',note='Vier M3,6mm Gewindeeingriff')
    define('F3_ROOT_CAP','Pitchlagerdeckel M3x10',axial(1.2,10,r-4).fuse(axial(2.75,3,r-7)),'Aluminium7075-T6',note='Drei M3 auf PCD60;6mm Eingriff')
    define('F6_ROOT_OUT','Aussenlagerdeckel M6x20',axial(2.5,20,r+41.6).fuse(axial(5,6,r+61.6)),'Aluminium7075-T6',note='M6x20 unter Kopf, von aussen nach innen;14.4mm Gewindeeingriff')
    define('W6_ROOT_OUT','Aussenlagerdeckel-ScheibeM6',annx(3.2,6,r+60,1.6),'Aluminium7075-T6','Normteil')
    put('A29','Zentralblock',frame='shared')
    for x,y in xy(4,95,45):
        put('TIE6',f'Zentralanker_{x:g}_{y:g}',shape=moved(parts['TIE6']['shape'],x=x,y=y),frame='shared')
        for zz in [-101,96]:put('N6',f'Zentralankermutter_{x:g}_{y:g}_{zz}',shape=moved(nut,x=x,y=y,z=zz),frame='shared')
    # Frame objects in local upper half; mirrored pods share the central payload interface.
    for id in ['A01','A03','MN1330','A05','A06O']:
        put(id,id)
    for xx,yy in xy(4,59):
        put('F4_HOUSING',f'Hauptlagerbefestigung_{xx:g}_{yy:g}',shape=moved(parts['F4_HOUSING']['shape'],x=xx,y=yy))
        put('F3_CAP',f'Hauptlagerdeckelbolzen_{xx:g}_{yy:g}',shape=moved(parts['F3_CAP']['shape'],x=xx,y=yy))
    for x,y in xy(4,95,45):put('A02',f'A02_{x:g}_{y:g}',shape=moved(parts['A02']['shape'],x=x,y=y))
    for x,y in xy(4,25):put('F6_STATOR',f'Statormotorbolzen_{x:g}_{y:g}',shape=moved(parts['F6_STATOR']['shape'],x=x,y=y))
    for x,y in xy(12,20):put('F5_MOTOR',f'Rotormotorbolzen_{x:g}_{y:g}',shape=moved(parts['F5_MOTOR']['shape'],x=x,y=y),frame='rotor')
    for x,y in xy(6,48):
        put('F6_HUB',f'Rotornabenbolzen_{x:g}_{y:g}',shape=moved(parts['F6_HUB']['shape'],x=x,y=y),frame='rotor')
    for z in [98,126]:put('B7212','Hauptlager'+str(z),shape=moved(parts['B7212']['shape'],z=z))
    for id in ['A04','A04F','A04W','A04N','A07','A08W','A08','A09','A24']:put(id,id,frame='rotor')
    put('A24','A24_Gegenseite',shape=rot(parts['A24']['shape'],180),frame='rotor')
    for id in ['A19','POM01']:put(id,id,frame='swash_slider')
    for id in ['A20','A20C','POM02','POM02U','A22']:put(id,id,frame='swash_fixed')
    for id in ['B61832','A21','A21C']:put(id,id,frame='swash_rotor')
    for x,y in xy(4,76,45):put('F3_CUP',f'Kugelpfannenbolzen_{x:g}_{y:g}',shape=moved(parts['F3_CUP']['shape'],x=x,y=y),frame='swash_fixed')
    for x,y in xy(4,103,45):put('F3_TAUMEL',f'Taumeldeckelbolzen_{x:g}_{y:g}',shape=moved(parts['F3_TAUMEL']['shape'],x=x,y=y),frame='swash_rotor')
    for i in range(n):
        a=360*i/n;pre='Blatt'+str(i+1)+'_'
        for id in ['A11','A11O','B7205','A12']:
            if id=='B7205':
                for x in [r,r+35]:put(id,pre+id+str(x),shape=moved(parts[id]['shape'],x=x),frame='rotor',a=a,z=level,blade_index=i)
            else:put(id,pre+id,frame='rotor',a=a,z=level,blade_index=i)
        for id in ['A13','A13C','A13D','A14','A14W','A14S','A16A','CFK01','A18','A18B','A18S','A18T','A18W','F6_PITCH_END']:put(id,pre+id,frame='pitch',a=a,z=level,theta=g['neutral_pitch_deg'],blade_index=i)
        for j,(yy,zz) in enumerate(xy(3,30,90)):
            put('F3_ROOT_CAP',pre+'Lagerdeckelbolzen'+str(j),shape=moved(parts['F3_ROOT_CAP']['shape'],y=yy,z=zz),frame='rotor',a=a,z=level,blade_index=i)
        for j,(yy,zz) in enumerate(xy(6,32)):
            for id in ['F6_ROOT_OUT','W6_ROOT_OUT']:put(id,pre+id+str(j),shape=moved(parts[id]['shape'],y=yy,z=zz),frame='rotor',a=a,z=level,blade_index=i)
        for j,(y,z) in enumerate(xy(4,32,45)):
            put('F6_ROOT',pre+'F6_ROOT'+str(j),shape=moved(parts['F6_ROOT']['shape'],y=y,z=z),frame='pitch',a=a,z=level,theta=g['neutral_pitch_deg'],blade_index=i)
    for i,a in enumerate([0,120,240]):
        for id in ['SERVO','A25','A28']:put(id,'Servo'+str(i+1)+'_'+id,a=a,servo_index=i)
        for yy in [-66,-24]:put('B6002','Servo'+str(i+1)+'_Lager'+str(yy),shape=moved(parts['B6002']['shape'],x=200,y=yy,z=zs),a=a,servo_index=i)
        for id in ['A26','A26K','A26S','KUPP']:
            ss=parts[id]['shape'].copy();ss.rotate(V(200,0,zs),V(0,1,0),g['servo_neutral_deg'])
            put(id,'Servo'+str(i+1)+'_'+id,shape=ss,a=a,frame='servo_shaft',servo_index=i)
        for dy in [0,55]:
            ss=moved(nut15,y=dy);ss.rotate(V(200,0,zs),V(0,1,0),g['servo_neutral_deg'])
            put('A26N','Servo'+str(i+1)+'_Mutter'+str(dy),shape=ss,a=a,frame='servo_shaft',servo_index=i)
        ho=parts['A27']['shape'].copy();ho.rotate(V(200,0,zs),V(0,1,0),g['servo_neutral_deg'])
        put('A27','Servo'+str(i+1)+'_Hebel',shape=ho,a=a,frame='servo_horn',servo_index=i)
        for xx in [178,188,198,208]:
            put('F4_CRADLE','Servo'+str(i+1)+'_Sattelbolzen'+str(xx),shape=moved(parts['F4_CRADLE']['shape'],x=xx,y=-6),a=a,servo_index=i)
            put('W4','Servo'+str(i+1)+'_Sattelscheibe'+str(xx),shape=moved(parts['W4']['shape'],x=xx,y=-6,z=zs-27),a=a,servo_index=i)
        for xx in [87,111]:
            for yy in [-6.5,6.5]:
                put('F6_SUPPORT','Servo'+str(i+1)+'_Traegerbolzen'+str(xx)+'_'+str(yy),shape=moved(parts['F6_SUPPORT']['shape'],x=xx,y=yy),a=a,servo_index=i)
                put('W6','Servo'+str(i+1)+'_Traegerscheibe'+str(xx)+'_'+str(yy),shape=moved(parts['W6']['shape'],x=xx,y=yy,z=zs-31),a=a,servo_index=i)
    J.install(c,q,define,put,parts)
    q['neutral']=neutral
    active={row['id'] for row in rows}|{'A13U'};parts={id:p for id,p in parts.items() if id in active}
    return parts,rows,q
