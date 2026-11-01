"""P12 geometry exclusively driven by validated input and derived dimensions."""
import math,sys,json
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
from parameter_schema import validate
V=A.Vector

def box(x,y,z,px=0,py=0,pz=0):return Part.makeBox(x,y,z,V(px,py,pz))
def cyl(r,h,x=0,y=0,z=0):return Part.makeCylinder(r,h,V(x,y,z))
def ring(ri,ro,z,h):return cyl(ro,h,z=z).cut(cyl(ri,h+2,z=z-1)) if ri>0 else cyl(ro,h,z=z)
def holes(s,coords,d,z,h):
    for x,y in coords:s=s.cut(cyl(d/2,h,x,y,z))
    return s

def pcd(n,r,phase=0):return [(r*math.cos(math.radians(phase+360*i/n)),r*math.sin(math.radians(phase+360*i/n))) for i in range(int(n))]
def tube(length,w,h,t):return box(length,w,h,0,-w/2,-h/2).cut(box(length+2,w-2*t,h-2*t,-1,-w/2+t,-h/2+t))
def revolve(points):
    pts=[V(r,0,z) for r,z in points];return Part.Face(Part.makePolygon(pts+[pts[0]])).revolve(V(),V(0,0,1),360)
def shift(s,x=0,y=0,z=0):s=s.copy();s.translate(V(x,y,z));return s

def build(p,materials=None):
    q=validate(p);parts={};scene=[];m=materials or {}
    def define(id,name,s,mat,process,detail,open_items='',ref=False):
        s=s.removeSplitter()
        if not s.isValid() or len(s.Solids)!=1:raise ValueError(f'{id}: ungültiger Körper oder nicht zusammenhängend')
        parts[id]=dict(id=id,name=name,shape=s,material=m.get(mat,mat),process=process,features=detail,open=open_items,reference=ref)
    def put(id,name,pos=(0,0,0),angle=0,mirror=False,context=False,variant=None):
        s=parts[id]['shape'].copy()
        if mirror:s=s.mirror(V(),V(0,0,1))
        production=s.copy();s.rotate(V(),V(0,0,1),angle);s.translate(V(*pos));scene.append(dict(id=id,name=name,shape=s,context=context,variant=variant or ('MZ' if mirror else 'NOMINAL'),manufacturing_shape=production))
    mh=pcd(p['motor_stator_holes'],p['motor_stator_pcd']/2,p['motor_stator_phase'])
    s=box(p['motor_plate_x'],p['motor_plate_y'],p['motor_plate_t'],-p['motor_plate_x']/2,-p['motor_plate_y']/2)
    s=holes(s,mh,p['stator_hole_d'],-1,p['motor_plate_t']+2);s=holes(s,mh,p['stator_head_d'],p['motor_plate_t']-p['stator_head_depth'],p['stator_head_depth']+1)
    s=holes(s,[(x,y) for x in [-p['motor_mount_bolt_x'],p['motor_mount_bolt_x']] for y in [-p['frame_beam_y'],p['frame_beam_y']]],p['frame_hole_d'],-1,p['motor_plate_t']+2)
    define('P12-001','Statortragplatte',s,'motor_plate','Fräsen, Bohren, Zylindersenken',f"{p['motor_plate_x']}×{p['motor_plate_y']}×{p['motor_plate_t']}; {p['motor_stator_holes']}×Ø{p['stator_hole_d']}/PCD{p['motor_stator_pcd']}; SenkungØ{p['stator_head_d']}×{p['stator_head_depth']}",'Motor-Lochbildphase und Gewindetiefen bestätigen')
    hubholes=pcd(p['motor_rotor_holes'],p['motor_rotor_pcd']/2,p['motor_rotor_phase']);memholes=pcd(p['hub_membrane_holes'],q['membrane_clamp_r'],p['hub_membrane_phase'])
    s=cyl(p['hub_flange_r'],p['hub_flange_t']).fuse(cyl(p['hub_boss_r'],p['hub_boss_length'],z=p['hub_flange_t']))
    s=holes(s,hubholes,p['hub_rotor_hole_d'],-1,p['hub_flange_t']+p['hub_boss_length']+2);s=holes(s,hubholes,p['hub_head_d'],-1,p['hub_head_depth']+1);s=holes(s,memholes,p['drive_hole_d'],-1,p['hub_flange_t']+2)
    define('P12-002','Motornabe',s,'drive_hub','Drehen/Fräsen/Bohren',f"FlanschØ{2*p['hub_flange_r']}×{p['hub_flange_t']}; BossØ{2*p['hub_boss_r']}×{p['hub_boss_length']}; Rotor-PCD{p['motor_rotor_pcd']}",'Zentrierung und Motor-Gewindeeingriff offen')
    s=ring(p['membrane_inner_r'],p['membrane_outer_r'],0,p['membrane_t']);posts=pcd(p['blade_count'],p['drive_post_radius'])
    for a in range(int(p['blade_count'])):
        arm=box(p['drive_post_radius']-p['membrane_arm_start'],p['membrane_arm_width'],p['membrane_t'],p['membrane_arm_start'],-p['membrane_arm_width']/2).fuse(cyl(p['membrane_pad_r'],p['membrane_t'],p['drive_post_radius']))
        arm.rotate(V(),V(0,0,1),a*q['pitch_count_angle']);s=s.fuse(arm)
    s=holes(s,memholes+posts,p['drive_hole_d'],-1,p['membrane_t']+2)
    define('P12-003','Drehmomentmembran',s,'drive_membrane','Feinschneiden/Fräsen/Entgraten',f"t{p['membrane_t']}; {p['blade_count']} Arme; Anschluss-PCD{2*p['drive_post_radius']}",'Axial-/Torsionssteifigkeit und Dauerfestigkeit nicht nachgewiesen')
    define('P12-004','Distanzsäule',ring(p['drive_hole_d']/2,p['drive_post_d']/2,0,q['drive_post_height']),'frame','Drehen/Bohren',f"Ø{p['drive_post_d']}/Ø{p['drive_hole_d']}×{q['drive_post_height']}",'Planparallelität und Schraubenlänge auslegen')
    s=holes(ring(p['carrier_inner_r'],p['carrier_outer_r'],0,p['carrier_height']),posts,p['drive_hole_d'],-1,p['carrier_height']+2)
    define('P12-005','Innenring_Rohanschluss',s,'drive_hub','Drehen/Bohren',f"Ø{2*p['carrier_outer_r']}/Ø{2*p['carrier_inner_r']}×{p['carrier_height']}",'Pitchlageranschlüsse noch nicht modelliert')
    s=tube(2*q['post_half_length'],p['post_size_y'],p['post_size_x'],p['post_wall']);s.rotate(V(),V(0,1,0),90)
    b=s.BoundBox;s.translate(V(-(b.XMin+b.XMax)/2,-(b.YMin+b.YMax)/2,-b.ZMin))
    define('P12-006','Rahmenpfosten',s,'frame','Rohrzuschnitt/Planen',f"RHS{p['post_size_x']}×{p['post_size_y']}×{p['post_wall']}; L{2*q['post_half_length']}",'Schweißnaht und Wärmeeinflusszone offen')
    flangeholes=[(x,y) for x in [-p['flange_pitch_x']/2,p['flange_pitch_x']/2] for y in [-p['flange_pitch_y']/2,p['flange_pitch_y']/2]]
    s=holes(box(p['flange_x'],p['flange_y'],p['flange_t'],-p['flange_x']/2,-p['flange_y']/2),flangeholes,p['frame_hole_d'],-1,p['flange_t']+2)
    define('P12-007','Pfosten_Endflansch',s,'frame','Fräsen/Bohren/Schweißen',f"{p['flange_x']}×{p['flange_y']}×{p['flange_t']}; Lochraster{p['flange_pitch_x']}×{p['flange_pitch_y']}",'Nahtbemessung offen')
    s=shift(tube(q['beam_length'],p['beam_width'],p['beam_height'],p['beam_wall']),x=-q['beam_length']/2,z=p['beam_height']/2)
    s=holes(s,[(-p['motor_mount_bolt_x'],0),(p['motor_mount_bolt_x'],0)],p['frame_hole_d'],-1,p['beam_height']+2)
    define('P12-008','Motorquerträger',s,'frame','Rohrzuschnitt/Bohren',f"RHS{p['beam_width']}×{p['beam_height']}×{p['beam_wall']}; L{q['beam_length']}",'Klemmsattel-Reibschluss und Formschluss noch auslegen')
    define('P12-009','Druckhülse_Motorträger',ring(p['frame_hole_d']/2,p['beam_sleeve_d']/2,0,p['beam_height']-2*p['beam_wall']),'frame','Drehen',f"Ø{p['beam_sleeve_d']}/Ø{p['frame_hole_d']}; L{p['beam_height']-2*p['beam_wall']}",'Auf reale Rohrwand abstimmen')
    footholes=[(x,y) for x in [-p['foot_pitch_x']/2,p['foot_pitch_x']/2] for y in [-p['foot_pitch_y']/2,p['foot_pitch_y']/2]]
    s=holes(box(p['foot_x'],p['foot_y'],p['foot_t'],-p['foot_x']/2,-p['foot_y']/2),footholes,p['middle_hole_d'],-1,p['foot_t']+2)
    define('P12-010','Mittelstützen_Fuß',s,'frame','Fräsen/Bohren',f"{p['foot_x']}×{p['foot_y']}×{p['foot_t']}; Raster{p['foot_pitch_x']}×{p['foot_pitch_y']}",'Führungsbuchse und Schweißanschluss offen')
    define('P12-011','Mittelstützen_Rohr',ring(p['column_bore']/2,p['column_d']/2,0,q['column_length']),'frame','Rohrzuschnitt/Planen',f"Ø{p['column_d']}/Ø{p['column_bore']}×{q['column_length']}",'Keine Taumelscheiben-Gleitpassung auf unbearbeitetem Rohr')
    s=shift(tube(q['middle_length'],p['middle_width'],p['middle_height'],p['middle_wall']),x=-q['middle_length']/2)
    s=holes(s,footholes,p['middle_hole_d'],-p['middle_height']/2-1,p['middle_height']+2)
    define('P12-012','Mittelquerträger',s,'frame','Rohrzuschnitt/Bohren',f"RHS{p['middle_width']}×{p['middle_height']}×{p['middle_wall']}; L{q['middle_length']}",'Lastpfad und Endnähte offen')
    define('P12-013','Druckhülse_Mittelträger',ring(p['middle_hole_d']/2,p['middle_sleeve_d']/2,0,p['middle_height']-2*p['middle_wall']),'frame','Drehen',f"Ø{p['middle_sleeve_d']}/Ø{p['middle_hole_d']}; L{p['middle_height']-2*p['middle_wall']}",'Auf reale Rohrwand abstimmen')
    define('P12-014','V_Laufbahn',revolve([(q['track_inner_r'],-p['track_half_height']),(q['track_tip_r'],0),(q['track_inner_r'],p['track_half_height'])]),'guide_track','Drehen/Härten/Profilschleifen',f"SpitzenØ{2*q['track_tip_r']}; InnenØ{2*q['track_inner_r']}; V{p['groove_angle']}°",'Verbindung zu Pitchlagerträgern, Härte und Rundlauf offen')
    rh=q['roller_half_height'];bw=p['bearing_width'];bg=p['bearing_gap'];be=q['bearing_edge'];cr=p['cap_radius'];ch=pcd(4,p['cap_hole_pcd']/2,45)
    s=revolve([(0,-rh),(p['roller_outer_r'],-rh),(p['roller_outer_r'],-q['groove_half_width']),(p['roller_root_r'],0),(p['roller_outer_r'],q['groove_half_width']),(p['roller_outer_r'],rh),(0,rh)])
    s=s.cut(cyl(p['roller_web_bore']/2,2*rh+2,z=-rh-1)).cut(cyl(p['bearing_od']/2,bw,z=-be)).cut(cyl(p['bearing_od']/2,bw,z=bg/2))
    s=s.cut(cyl(cr+p['cap_pocket_gap'],p['cap_t']+1,z=be)).cut(cyl(cr+p['cap_pocket_gap'],p['cap_t']+1,z=-rh-1))
    s=holes(s,ch,p['cap_core_d'],be-p['cap_thread_depth'],p['cap_thread_depth']+p['cap_t']+1);s=holes(s,ch,p['cap_core_d'],-rh-1,p['cap_thread_depth']+p['cap_t']+1)
    define('P12-015','V_Führungsrolle',s,'guide_roller','Drehen/Kernbohren/Härten/Schleifen',f"Ø{2*p['roller_outer_r']}×{2*rh}; Nut{p['groove_angle']}°; LagersitzeØ{p['bearing_od']}×{bw}",'Passung, DB-Vorspannung und Tragzahlen offen; Gewindekernkonturen symbolisch')
    s=holes(ring(q['cap_inner_r'],cr,0,p['cap_t']),ch,p['cap_hole_d'],-1,p['cap_t']+2)
    define('P12-016','Lagerdeckel',s,'axle','Drehen/Bohren',f"Ø{2*cr}/Ø{2*q['cap_inner_r']}×{p['cap_t']}; 4×Ø{p['cap_hole_d']}/PCD{p['cap_hole_pcd']}",'Tatsächliche Kaufteil-Schultermaße bestätigen')
    define('P12-017','Innenring_Distanz',ring((p['bearing_bore']+p['spacer_bore_gap'])/2,p['inner_spacer_d']/2,0,bg),'axle','Drehen/Stirnschleifen',f"Ø{p['inner_spacer_d']}×{bg}",'DB-Klemmkette abzustimmen')
    ah=q['axle_half_length'];s=cyl(p['bearing_bore']/2,2*ah,z=-ah).fuse(cyl(p['axle_head_d']/2,p['axle_head_h'],z=-ah-p['axle_head_h'])).fuse(cyl(p['axle_thread_d']/2,p['axle_thread_length'],z=ah))
    define('P12-018','Rollenachse',s,'axle','Drehen/Schleifen/Gewindeschneiden',f"SitzØ{p['bearing_bore']}×{2*ah}; Gewinde-Nenndurchmesser{p['axle_thread_d']}×{p['axle_thread_length']}",'Gewindesteigung, Freistich und Sicherung fehlen; Mutter noch nicht modelliert')
    wx=p['fork_web_start']+p['fork_web_depth']/2
    s=box(q['fork_web_end']+p['fork_back_length'],p['fork_width'],p['fork_t'],-p['fork_back_length'],-p['fork_width']/2)
    s=holes(s,[(0,0)],p['bearing_bore']+p['fork_axle_gap'],-1,p['fork_t']+2);s=holes(s,[(wx,-p['fork_bolt_y']),(wx,p['fork_bolt_y'])],p['fork_hole_d'],-1,p['fork_t']+2)
    define('P12-019','Rollen_Gabelplatte',s,'drive_hub','Fräsen/Bohren',f"{q['fork_web_end']+p['fork_back_length']}×{p['fork_width']}×{p['fork_t']}; AchsbohrungØ{p['bearing_bore']+p['fork_axle_gap']}",'Feste Einbaulage, Distanzblech-Justage noch auszulegen')
    fz=q['fork_inner_z'];s=holes(box(p['fork_web_depth'],p['fork_width'],2*fz,p['fork_web_start'],-p['fork_width']/2,-fz),[(wx,-p['fork_bolt_y']),(wx,p['fork_bolt_y'])],p['fork_core_d'],-fz-1,2*fz+2)
    for z in [-p['web_bolt_z'],p['web_bolt_z']]:s=s.cut(Part.makeCylinder(p['fork_hole_d']/2,p['fork_web_depth']+2,V(p['fork_web_start']-1,0,z),V(1,0,0)))
    define('P12-020','Rollen_Gabelsteg',s,'drive_hub','Fräsen/Kernbohren/Gewinde',f"{p['fork_web_depth']}×{p['fork_width']}×{2*fz}; QuerbohrungenØ{p['fork_hole_d']}",'Schraubenlängen und Distanzblech-Justage offen')
    define('P12-021','Rahmen_Klemmsattel',parts['P12-007']['shape'].copy(),'frame','Fräsen/Bohren',parts['P12-007']['features'],'Klemmkraft und Formschluss offen')
    define('P12-022','Rollen_Anlaufdistanz',ring((p['bearing_bore']+2*p['spacer_bore_gap'])/2,p['inner_spacer_d']/2,0,fz-be),'axle','Drehen/Stirnschleifen',f"Ø{p['inner_spacer_d']}×{fz-be}",'Innenring-Klemmkette noch abstimmen')
    s=tube(q['side_length'],p['post_size_x'],p['middle_height'],p['post_wall']);s.rotate(V(),V(0,0,1),90);s.translate(V(0,-q['side_length']/2,0))
    define('P12-023','Rahmen_Seitenriegel',s,'frame','Rohrzuschnitt/Schweißen',f"L{q['side_length']}; Breite{p['post_size_x']}; Höhe{p['middle_height']}",'Schweißnahtnachweis offen')
    ri=q['guide_ring_inner'];rt=p['guide_ring_t'];define('P12-024','Stationärer_Guiderahmen',ring(ri,q['guide_ring_outer'],-rt/2,rt),'frame','Fräsen/Schweißen',f"Ø{2*q['guide_ring_outer']}/Ø{2*ri}×{rt}",'Baugröße und Rahmensteifigkeit überprüfen')
    s=box(ri-q['guide_post_outer']+1,p['fork_width'],rt,q['guide_post_outer'],-p['fork_width']/2,-rt/2).common(cyl(ri,rt+2,z=-rt/2-1))
    define('P12-025','Guide_Radialsteg',s,'frame','Fräsen/Schweißen',f"Radial{q['guide_post_outer']}..{ri}; t{rt}",'Schweißanschluss und Ausrichtung offen')
    s=tube(2*q['guide_post_half_length'],p['fork_width'],p['guide_post_radial'],p['guide_post_wall']);s.rotate(V(),V(0,1,0),90);b=s.BoundBox;s.translate(V(q['guide_post_inner']+p['guide_post_radial']/2-(b.XMin+b.XMax)/2,-(b.YMin+b.YMax)/2,-(b.ZMin+b.ZMax)/2))
    for l in [-q['level_z'],q['level_z']]:
        for z in [-p['web_bolt_z'],p['web_bolt_z']]:s=s.cut(Part.makeCylinder(p['fork_hole_d']/2,p['guide_post_radial']+2,V(q['guide_post_inner']-1,0,l+z),V(1,0,0)))
    define('P12-026','Guide_Außenpfosten',s,'frame','Rohrzuschnitt/Querbohren',f"RHS{p['guide_post_radial']}×{p['fork_width']}×{p['guide_post_wall']}; L{2*q['guide_post_half_length']}",'Schraubenauflagen und radiale Justage offen')
    start=q['post_x']+p['post_size_x']/2;s=box(ri-start+1,p['post_size_y'],rt,start,p['frame_beam_y']-p['post_size_y']/2,-rt/2).common(cyl(ri,rt+2,z=-rt/2-1))
    define('P12-027','Guiderahmen_Anschlusslasche',s,'frame','Fräsen/Schweißen',f"x{start}..Radius{ri}; t{rt}",'Nahtbemessung offen')
    define('REF-7202B','Lager_Nennkontur',ring(p['bearing_bore']/2,p['bearing_od']/2,0,bw),'Kaufteil','Kaufen',f"{p['bearing_bore']}×{p['bearing_od']}×{bw}; DB-Anordnung",'Geänderte Abmessungen erfordern ein neu ausgewähltes reales Lager; keine internen Kugeln modelliert',True)
    define('REF-MN1330','Motor_Nennhülle',cyl(p['motor_diameter']/2,p['motor_length']),'Kaufteil','Kaufen',f"Ø{p['motor_diameter']}×{p['motor_length']}; KEIN Durchgang",'Abweichungen vonØ150×66 sind nur ein anderer Bauraum, keine MN1330-Variante',True)
    # Actual parametric profile, lofted for taper/twist; solid aerodynamic reference only.
    wires=[]
    for f in [i/8 for i in range(9)]:
        chord=p['blade_chord']*(1+(p['blade_taper']-1)*f);r=p['blade_root']+(p['rotor_radius']-p['blade_root'])*f;pts=[]
        qs=[(1-math.cos(math.pi*i/48))/2 for i in range(49)]
        for sign,seq in [(1,qs),(-1,list(reversed(qs[1:])) )]:
            for a in seq:
                t=5*p['blade_thickness']*(.2969*math.sqrt(a)-.126*a-.3516*a*a+.2843*a**3-.1036*a**4)*chord+p['blade_te']/2*a**10
                y=(p['pitch_axis']-a)*chord;z=sign*t;ang=math.radians(p['pitch_neutral']+p['blade_twist']*f);pts.append(V(r,y*math.cos(ang)-z*math.sin(ang),y*math.sin(ang)+z*math.cos(ang)))
        wires.append(Part.makePolygon(pts+[pts[0]]))
    wing=Part.makeLoft(wires,True,False)
    define('REF-FLUEGEL','Flügel_Profilreferenz',wing,'Profilreferenz','Nicht fertigen',f"R{p['blade_root']}..{p['rotor_radius']}; Sehne{p['blade_chord']}; Dicke{p['blade_thickness']}; Taper{p['blade_taper']}; Twist{p['blade_twist']}°",'Kein Laminat, keine Pitchwelle/-lager und keine finalisierte aerodynamische Auslegung',True)
    for sign,level in [(1,'Oben'),(-1,'Unten')]:
        mir=sign<0
        def at(id,name,pos=(0,0,0),angle=0):
            x,y,z=pos
            if id in ['P12-002','P12-003','P12-004','P12-005','P12-014']:
                phase=p['upper_phase' if sign>0 else 'lower_phase'];a=math.radians(phase);x,y=x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a);angle+=phase
            put(id,level+'_'+name,(x,y,sign*z),angle,mir)
        at('P12-001','Statorplatte',(0,0,q['motor_back']));at('REF-MN1330','Motor',(0,0,q['motor_face']));at('P12-002','Nabe',(0,0,q['hub_z']));at('P12-003','Membran',(0,0,q['membrane_z']))
        for i,(x,y) in enumerate(posts):at('P12-004',f'Distanz_{i+1}',(x,y,q['carrier_top']))
        at('P12-005','Innenring',(0,0,q['carrier_bottom']));at('P12-014','Laufbahn',(0,0,q['level_z']))
        for y in [-p['frame_beam_y'],p['frame_beam_y']]:at('P12-008',f'Quertraeger_{y:g}',(0,y,q['beam_z']))
        for x in [-p['motor_mount_bolt_x'],p['motor_mount_bolt_x']]:
            for y in [-p['frame_beam_y'],p['frame_beam_y']]:at('P12-009',f'Druckhuelse_{x:g}_{y:g}',(x,y,q['beam_z']+p['beam_wall']))
        at('P12-010','Mittelstuetze_Fuss',(0,0,p['middle_height']/2));at('P12-011','Mittelstuetze_Rohr',(0,0,q['column_base']))
        for i,a in enumerate(q['guide_angles']):
            rc=q['roller_center'];x=rc*math.cos(math.radians(a));y=rc*math.sin(math.radians(a));pre=f'Rolle_{i+1}';l=q['level_z']
            at('P12-015',pre,(x,y,l),a);at('P12-016',pre+'_Deckel_A',(x,y,l+be),a);at('P12-016',pre+'_Deckel_B',(x,y,l-rh),a)
            at('REF-7202B',pre+'_Lager_A',(x,y,l+bg/2),a);at('REF-7202B',pre+'_Lager_B',(x,y,l-be),a);at('P12-017',pre+'_Distanz',(x,y,l-bg/2),a)
            at('P12-018',pre+'_Achse',(x,y,l),a);at('P12-022',pre+'_Anlauf_A',(x,y,l+be),a);at('P12-022',pre+'_Anlauf_B',(x,y,l-fz),a)
            at('P12-019',pre+'_Gabel_A',(x,y,l+fz),a);at('P12-019',pre+'_Gabel_B',(x,y,l-fz-p['fork_t']),a);at('P12-020',pre+'_Steg',(x,y,l),a)
        for i in range(int(p['blade_count'])):put('REF-FLUEGEL',level+f'_Fluegel_{i+1}',(0,0,sign*q['level_z']),i*q['pitch_count_angle']+p['upper_phase' if sign>0 else 'lower_phase'],mir,True)
    for x in [-q['post_x'],q['post_x']]:
        for y in [-p['frame_beam_y'],p['frame_beam_y']]:
            put('P12-006',f'Pfosten_{x:g}_{y:g}',(x,y,-q['post_half_length']))
            put('P12-007',f'Pfosten_Flansch_A_{x:g}_{y:g}',(x,y,q['post_half_length']));put('P12-007',f'Pfosten_Flansch_B_{x:g}_{y:g}',(x,y,-q['beam_z']))
            put('P12-021',f'Pfosten_Sattel_A_{x:g}_{y:g}',(x,y,q['beam_top']));put('P12-021',f'Pfosten_Sattel_B_{x:g}_{y:g}',(x,y,-q['beam_top']-p['flange_t']))
    put('P12-012','Mittelquertraeger')
    for x in [-q['post_x'],q['post_x']]:put('P12-023',f'Seitenriegel_{x:g}',(x,0,0))
    put('P12-024','Guiderahmen')
    for i,a in enumerate(q['guide_angles']):put('P12-025',f'Guide_Radialsteg_{i}',angle=a);put('P12-026',f'Guide_Aussenpfosten_{i}',angle=a)
    orig=parts['P12-027']['shape']
    for xs in [-1,1]:
        for ys in [-1,1]:
            s=orig.copy()
            if xs<0:s=s.mirror(V(),V(1,0,0))
            if ys<0:s=s.mirror(V(),V(0,1,0))
            parts['P12-027']['shape']=s;put('P12-027',f'Guiderahmen_Anschluss_{xs}_{ys}',variant=f'X{xs}_Y{ys}')
    parts['P12-027']['shape']=orig
    for x,y in footholes:put('P12-013',f'Mitteltraeger_Huelse_{x:g}_{y:g}',(x,y,-p['middle_height']/2+p['middle_wall']))
    if p.get('frame_mode',0)==1:
        from cfk_rahmen import apply
        return apply(p,q,parts,scene)
    return parts,scene,q
