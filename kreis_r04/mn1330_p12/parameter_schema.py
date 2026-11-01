"""P12 input schema and derived construction dimensions; independent of FreeCAD."""
import json,math
from pathlib import Path
# name, default, category, unit, lower bound, upper bound
ROWS=[
('rotor_radius',750,'Rotor','mm',200,2000),('blade_root',150,'Rotor','mm',40,600),('blade_chord',120,'Rotor','mm',20,400),('blade_count',8,'Rotor','int',2,24),('blade_thickness',.12,'Rotor','ratio',.06,.3),('blade_taper',1,'Rotor','ratio',.3,1.8),('blade_twist',0,'Rotor','deg',-20,20),('blade_te',.8,'Rotor','mm',.1,4),('pitch_axis',.5,'Rotor','ratio',.15,.75),('pitch_neutral',12,'Rotor','deg',-10,35),('pitch_min',-2,'Rotor','deg',-20,35),('pitch_max',21,'Rotor','deg',-10,45),('level_spacing',240,'Rotor','mm',100,1000),('upper_phase',0,'Rotor','deg',0,360),('lower_phase',0,'Rotor','deg',0,360),('blade_track_gap_min',2,'Rotor','mm',.5,30),
('motor_diameter',150,'Motor','mm',50,400),('motor_length',66,'Motor','mm',20,200),('motor_face_offset',140,'Motor','mm',70,500),('motor_rotor_pcd',40,'Motor','mm',15,180),('motor_rotor_holes',12,'Motor','int',3,24),('motor_rotor_phase',0,'Motor','deg',0,360),('motor_stator_pcd',50,'Motor','mm',20,200),('motor_stator_holes',4,'Motor','int',3,12),('motor_stator_phase',45,'Motor','deg',0,360),
('motor_plate_x',220,'Motorplatte','mm',100,600),('motor_plate_y',260,'Motorplatte','mm',100,600),('motor_plate_t',12,'Motorplatte','mm',6,40),('motor_mount_bolt_x',80,'Motorplatte','mm',30,240),('stator_hole_d',6.6,'Motorplatte','mm',3,14),('stator_head_d',11,'Motorplatte','mm',6,24),('stator_head_depth',7,'Motorplatte','mm',2,20),('frame_hole_d',8.4,'Motorplatte','mm',4,20),
('hub_flange_r',70,'Mitnehmer','mm',35,150),('hub_flange_t',10,'Mitnehmer','mm',6,30),('hub_boss_r',35,'Mitnehmer','mm',20,90),('hub_boss_length',30,'Mitnehmer','mm',10,100),('hub_rotor_hole_d',5.5,'Mitnehmer','mm',3,12),('hub_head_d',9,'Mitnehmer','mm',5,20),('hub_head_depth',5.5,'Mitnehmer','mm',2,16),('hub_membrane_pcd',100,'Mitnehmer','mm',50,260),('hub_membrane_holes',4,'Mitnehmer','int',3,12),('hub_membrane_phase',45,'Mitnehmer','deg',0,360),('drive_hole_d',6.6,'Mitnehmer','mm',3,16),('membrane_t',2,'Mitnehmer','mm',.8,8),('membrane_inner_r',36,'Mitnehmer','mm',15,90),('membrane_outer_r',72,'Mitnehmer','mm',40,160),('membrane_arm_width',20,'Mitnehmer','mm',8,60),('membrane_arm_start',60,'Mitnehmer','mm',25,120),('membrane_pad_r',12,'Mitnehmer','mm',6,30),('drive_post_radius',125,'Mitnehmer','mm',60,300),('drive_post_d',16,'Mitnehmer','mm',10,40),('carrier_inner_r',105,'Mitnehmer','mm',40,250),('carrier_outer_r',145,'Mitnehmer','mm',70,400),('carrier_height',40,'Mitnehmer','mm',20,100),
('frame_post_margin',120,'Rahmen','mm',80,300),('frame_beam_y',100,'Rahmen','mm',60,300),('post_size_x',60,'Rahmen','mm',30,120),('post_size_y',60,'Rahmen','mm',30,120),('post_wall',4,'Rahmen','mm',2,12),('beam_width',60,'Rahmen','mm',30,120),('beam_height',60,'Rahmen','mm',30,160),('beam_wall',4,'Rahmen','mm',2,12),('flange_x',100,'Rahmen','mm',60,200),('flange_y',100,'Rahmen','mm',60,200),('flange_t',8,'Rahmen','mm',4,24),('flange_pitch_x',76,'Rahmen','mm',40,160),('flange_pitch_y',76,'Rahmen','mm',40,160),('beam_sleeve_d',14,'Rahmen','mm',10,30),('middle_width',100,'Rahmen','mm',60,200),('middle_height',60,'Rahmen','mm',30,160),('middle_wall',5,'Rahmen','mm',2,12),('middle_hole_d',6.6,'Rahmen','mm',3,16),('middle_sleeve_d',12,'Rahmen','mm',8,30),
('foot_x',120,'Mittelstütze','mm',80,240),('foot_y',100,'Mittelstütze','mm',70,200),('foot_t',10,'Mittelstütze','mm',5,25),('foot_pitch_x',90,'Mittelstütze','mm',40,200),('foot_pitch_y',64,'Mittelstütze','mm',30,150),('column_d',60,'Mittelstütze','mm',30,120),('column_bore',45,'Mittelstütze','mm',15,100),('column_end_offset',60,'Mittelstütze','mm',0,180),
('track_tip_margin',20,'Führung','mm',12,80),('track_half_height',12,'Führung','mm',6,25),('groove_angle',90,'Führung','deg',60,120),('roller_root_r',21,'Führung','mm',18,50),('roller_outer_r',30,'Führung','mm',25,70),('guide_gap',.2,'Führung','mm',.05,1.5),('guide_angle_1',115,'Führung','deg',0,360),('guide_angle_2',205,'Führung','deg',0,360),('guide_angle_3',330,'Führung','deg',0,360),('bearing_bore',15,'Führung','mm',10,40),('bearing_od',35,'Führung','mm',25,80),('bearing_width',11,'Führung','mm',7,30),('bearing_gap',4,'Führung','mm',2,12),('roller_end_land',3,'Führung','mm',2,8),('roller_web_bore',20,'Führung','mm',15,50),('cap_radius',26,'Führung','mm',20,60),('cap_inner_shoulder',1.7,'Führung','mm',1,3),('cap_pocket_gap',.05,'Führung','mm',.02,.3),('cap_t',3,'Führung','mm',2,8),('cap_hole_pcd',44,'Führung','mm',32,110),('cap_hole_d',3.4,'Führung','mm',2,8),('cap_core_d',2.5,'Führung','mm',1.6,6),('cap_thread_depth',6,'Führung','mm',4,16),('cap_head_height',3,'Führung','mm',2,8),('cap_running_gap',2,'Führung','mm',1,8),('inner_spacer_d',20,'Führung','mm',15,50),('spacer_bore_gap',.1,'Führung','mm',.04,.4),('axle_head_d',22,'Führung','mm',18,60),('axle_head_h',6,'Führung','mm',4,12),('axle_thread_d',14,'Führung','mm',10,36),('axle_thread_length',16,'Führung','mm',10,30),
('fork_width',50,'Rollenhalter','mm',36,100),('fork_back_length',20,'Rollenhalter','mm',15,60),('fork_t',8,'Rollenhalter','mm',5,20),('fork_axle_gap',.5,'Rollenhalter','mm',.2,1.5),('fork_web_start',55,'Rollenhalter','mm',40,140),('fork_web_depth',20,'Rollenhalter','mm',12,40),('fork_bolt_y',16,'Rollenhalter','mm',10,36),('fork_hole_d',6.6,'Rollenhalter','mm',4,14),('fork_core_d',5,'Rollenhalter','mm',3,12),('web_bolt_z',8,'Rollenhalter','mm',5,18),('guide_post_radial',20,'Rollenhalter','mm',16,50),('guide_post_wall',4,'Rollenhalter','mm',2,8),('guide_post_end_margin',3,'Rollenhalter','mm',2,16),('guide_ring_inner_margin',190,'Rollenhalter','mm',130,500),('guide_ring_width',20,'Rollenhalter','mm',12,60),('guide_ring_t',16,'Rollenhalter','mm',8,40),
('frame_mode',1,'CFK-Rahmen','int',0,1),('cfk_od',20,'CFK-Rahmen','mm',20,20),('cfk_id',17,'CFK-Rahmen','mm',17,17),('cfk_actual_od',20,'CFK-Rahmen','mm',19.8,20.2),('cfk_stock_length',1000,'CFK-Rahmen','mm',1000,1000),('cfk_saw_kerf',2,'CFK-Rahmen','mm',.5,5),('cfk_end_trim',5,'CFK-Rahmen','mm',0,20),('cfk_price',45.02,'CFK-Rahmen','EUR',1,500),('cfk_socket_bore',20.6,'CFK-Knoten','mm',20.5,21.2),('cfk_socket_length',30,'CFK-Knoten','mm',20,60),('cfk_socket_flange_t',5,'CFK-Knoten','mm',4,10),('cfk_socket_flange_r',21,'CFK-Knoten','mm',20,30),('cfk_socket_body_r',15,'CFK-Knoten','mm',14,22),('cfk_clamp_gap',.5,'CFK-Knoten','mm',.3,1),('cfk_node_face',50,'CFK-Knoten','mm',45,80),('cfk_node_core_r',25,'CFK-Knoten','mm',22,40),('cfk_rim_offset',110,'CFK-Rahmen','mm',100,220),('cfk_max_panel_angle',40,'CFK-Rahmen','deg',25,45),('cfk_guide_saddle_depth',44,'CFK-Knoten','mm',36,65),('cfk_bridge_length',240,'CFK-Knoten','mm',200,400),('cfk_bridge_end_t',8,'CFK-Knoten','mm',6,16),
('total_mass_kg',150,'Lastszenario','kg',1,600),('rpm',850,'Lastszenario','rpm',100,5000),('load_factor',2,'Lastszenario','ratio',1,6)
]
SCHEMA={r[0]:dict(default=r[1],group=r[2],unit=r[3],minimum=r[4],maximum=r[5]) for r in ROWS}
class ParameterError(ValueError):pass

def defaults():return {k:v['default'] for k,v in SCHEMA.items()}
def load(path=None,overrides=None):
    p=defaults()
    if path:
        raw=json.loads(Path(path).read_text()); given=raw.get('parameters',{})
        unknown=set(given)-set(SCHEMA)
        if unknown:raise ParameterError('Unbekannte Parameter: '+', '.join(sorted(unknown)))
        p.update(given)
    for k,v in (overrides or {}).items():
        if k not in SCHEMA:raise ParameterError('Unbekannter Parameter: '+k)
        p[k]=v
    validate(p);return p

def derive(p):
    q=dict(p);q['level_z']=p['level_spacing']/2;q['motor_face']=q['level_z']+p['motor_face_offset'];q['motor_back']=q['motor_face']+p['motor_length'];q['beam_z']=q['motor_back']+p['motor_plate_t'];q['beam_top']=q['beam_z']+p['beam_height'];q['height']=2*(q['beam_top']+p['flange_t']);q['post_x']=p['rotor_radius']+p['frame_post_margin'];q['post_half_length']=q['beam_z']-p['flange_t'];q['beam_length']=2*(q['post_x']+p['flange_x']/2);q['middle_length']=2*(q['post_x']-p['post_size_x']/2);q['side_length']=2*(p['frame_beam_y']-p['post_size_y']/2)
    q['hub_z']=q['motor_face']-p['hub_boss_length']-p['hub_flange_t'];q['membrane_z']=q['hub_z']-p['membrane_t'];q['carrier_bottom']=q['level_z']-p['carrier_height']/2;q['carrier_top']=q['level_z']+p['carrier_height']/2;q['drive_post_height']=q['membrane_z']-q['carrier_top'];q['column_base']=p['middle_height']/2+p['foot_t'];q['column_end']=q['level_z']+p['column_end_offset'];q['column_length']=q['column_end']-q['column_base']
    q['slope']=1/math.tan(math.radians(p['groove_angle']/2));q['track_tip_r']=p['rotor_radius']+p['track_tip_margin'];q['track_inner_r']=q['track_tip_r']-p['track_half_height']*q['slope'];q['roller_center']=q['track_tip_r']+p['roller_root_r']+p['guide_gap'];q['groove_half_width']=(p['roller_outer_r']-p['roller_root_r'])/q['slope'];q['bearing_edge']=p['bearing_gap']/2+p['bearing_width'];q['roller_half_height']=q['bearing_edge']+p['roller_end_land'];q['fork_inner_z']=q['roller_half_height']+p['cap_head_height']+p['cap_running_gap'];q['axle_half_length']=q['fork_inner_z']+p['fork_t'];q['fork_web_end']=p['fork_web_start']+p['fork_web_depth'];q['guide_post_inner']=q['roller_center']+q['fork_web_end'];q['guide_post_outer']=q['guide_post_inner']+p['guide_post_radial'];q['guide_post_half_length']=q['level_z']+q['axle_half_length']+p['guide_post_end_margin'];q['guide_ring_inner']=p['rotor_radius']+p['guide_ring_inner_margin'];q['guide_ring_outer']=q['guide_ring_inner']+p['guide_ring_width'];q['guide_angles']=[p[f'guide_angle_{i}'] for i in range(1,4)];q['pitch_count_angle']=360/p['blade_count'];q['cap_inner_r']=p['bearing_od']/2-p['cap_inner_shoulder'];q['membrane_clamp_r']=p['hub_membrane_pcd']/2
    chord_max=p['blade_chord']*max(1,p['blade_taper']);offset=max(p['pitch_axis'],1-p['pitch_axis'])*chord_max;q['blade_envelope_r']=math.hypot(p['rotor_radius'],offset);q['blade_vertical_bound']=chord_max*(max(abs(math.sin(math.radians(v))) for v in [p['pitch_min'],p['pitch_max']])+p['blade_thickness'])+p['blade_te']
    q['cfk_rim_z']=q['level_z']+p['cfk_rim_offset'];q['cfk_guide_radius']=q['guide_post_inner']+p['cfk_guide_saddle_depth'];q['cfk_tube_inset']=p['cfk_node_face']+p['cfk_socket_flange_t'];q['cfk_port_reach']=q['cfk_tube_inset']+p['cfk_socket_length'];q['cfk_liner_t']=(p['cfk_socket_bore']-p['cfk_actual_od'])/2
    if p['frame_mode']==1:
        q['middle_length']=p['cfk_bridge_length'];q['height']=2*(q['beam_z']+2*p['cfk_node_core_r'])
    q['design_total_thrust_N']=p['total_mass_kg']*9.81*p['load_factor'];q['nominal_total_thrust_N']=p['total_mass_kg']*9.81;q['blade_tip_speed_m_s']=2*math.pi*p['rpm']/60*p['rotor_radius']/1000
    return q

def validate(p):
    errors=[]
    for k,s in SCHEMA.items():
        v=p.get(k)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):errors.append(k+': endliche Zahl erforderlich');continue
        if not s['minimum']<=v<=s['maximum']:errors.append(f'{k}: Bereich {s["minimum"]}..{s["maximum"]}')
        if s['unit']=='int' and int(v)!=v:errors.append(k+': ganze Zahl erforderlich')
    if errors:raise ParameterError('\n'.join(errors))
    q=derive(p)
    def need(test,msg):
        if not test:errors.append(msg)
    need(p['pitch_min']<=p['pitch_neutral']<=p['pitch_max'],'Neutralpitch außerhalb der Pitchgrenzen')
    need(p['pitch_min']<=p['pitch_neutral']+p['blade_twist']<=p['pitch_max'],'Verwindung führt die Blattspitze außerhalb der Pitchgrenzen')
    need(p['blade_root']<p['rotor_radius'],'Flügelwurzel muss innerhalb der Spitze liegen')
    need(p['blade_root']>p['carrier_outer_r']+2,'Flügelwurzel benötigt Abstand zum Innenring')
    need(p['blade_chord']*max(1,p['blade_taper'])<2*p['blade_root']*math.tan(math.pi/p['blade_count']),'Blätter überdecken sich konservativ an der Wurzel')
    need(q['track_inner_r']>q['blade_envelope_r']+p['blade_track_gap_min'],'V-Laufbahn liegt im Flügelhüllraum')
    need(2*q['blade_vertical_bound']+p['middle_height']+10<p['level_spacing'],'Ebenenabstand zu klein für Flügel-/Mittelträgerhüllraum')
    need(q['drive_post_height']>10,'Motor-/Nabenposition lässt keinen Platz für Distanzsäulen')
    need(q['column_length']>20 and q['column_end']+10<q['membrane_z'],'Mittelstütze kollidiert mit Mitnehmer oder hat negative Länge')
    need(p['column_bore']<p['column_d']-6,'Mittelstützen-Wandstärke zu klein')
    need(p['column_d']/2+3<min(p['foot_x'],p['foot_y'])/2,'Mittelrohr passt nicht auf Fußplatte')
    for w,h,t,name in [(p['post_size_x'],p['post_size_y'],p['post_wall'],'Pfosten'),(p['beam_width'],p['beam_height'],p['beam_wall'],'Motorträger'),(p['middle_width'],p['middle_height'],p['middle_wall'],'Mittelträger'),(p['guide_post_radial'],p['fork_width'],p['guide_post_wall'],'Guidepfosten')]:need(2*t<min(w,h),name+': ungültige Rohrwand')
    need(p['motor_plate_x']/2>p['motor_mount_bolt_x']+p['frame_hole_d'],'Motorplatte zu schmal für Rahmenbohrungen')
    need(p['motor_plate_y']/2>=p['frame_beam_y']+p['beam_width']/2,'Motorplatte erreicht Querträger nicht vollflächig')
    need(p['stator_head_depth']<p['motor_plate_t']-2,'Kopfsenkung durchbricht Motorplatte')
    need(p['stator_head_d']>p['stator_hole_d'],'Statorsenkung kleiner als Durchgang')
    need(p['hub_head_depth']<p['hub_flange_t']-2,'Nabensenkung durchbricht Flansch')
    need(p['hub_head_d']>p['hub_rotor_hole_d'],'Nabensenkung kleiner als Durchgang')
    need(p['motor_rotor_pcd']/2+p['hub_head_d']/2+2<p['hub_boss_r'],'Rotor-Lochbild passt nicht in Nabenboss')
    need(p['motor_stator_pcd']/2+p['stator_head_d']/2<min(p['motor_plate_x'],p['motor_plate_y'])/2,'Stator-Lochbild außerhalb Tragplatte')
    need(p['motor_diameter']/2<min(p['motor_plate_x'],p['motor_plate_y'])/2,'Motorgehäuse größer als Tragplatte')
    need(2*(p['motor_rotor_pcd']/2)*math.sin(math.pi/p['motor_rotor_holes'])>p['hub_head_d']+1,'Nabensenkungen überschneiden sich')
    need(p['hub_boss_r']<p['membrane_inner_r']<q['membrane_clamp_r']-p['drive_hole_d'],'Membran-/Nabenradien passen nicht zusammen')
    need(q['membrane_clamp_r']+p['drive_hole_d']<min(p['hub_flange_r'],p['membrane_outer_r']),'Membran-Anschluss außerhalb der Flansche')
    need(p['membrane_arm_start']<p['membrane_outer_r']-2,'Membranarme nicht mit Innenring verbunden')
    need(p['membrane_arm_start']<p['drive_post_radius'],'Membranarm hat negative Länge')
    need(p['drive_post_radius']-p['drive_post_d']/2>p['carrier_inner_r'] and p['drive_post_radius']+p['drive_post_d']/2<p['carrier_outer_r'],'Distanzsäulen passen nicht auf Innenring')
    need(p['drive_post_d']>p['drive_hole_d']+4,'Distanzsäule hat zu wenig Wandstärke')
    need(p['beam_sleeve_d']>p['frame_hole_d']+2,'M8-Druckhülse zu dünn')
    need(p['middle_sleeve_d']>p['middle_hole_d']+2,'Mittelträger-Druckhülse zu dünn')
    need(p['foot_pitch_x']/2+p['middle_hole_d']<p['foot_x']/2 and p['foot_pitch_y']/2+p['middle_hole_d']<p['foot_y']/2,'Fußbohrungen zu dicht am Rand')
    need(p['foot_pitch_y']/2+p['middle_sleeve_d']/2<p['middle_width']/2-p['middle_wall'],'Druckhülsen passen nicht in Mittelträger')
    need(p['flange_pitch_x']/2+p['frame_hole_d']<p['flange_x']/2 and p['flange_pitch_y']/2+p['frame_hole_d']<p['flange_y']/2,'Flanschbohrungen zu dicht am Rand')
    need(p['flange_pitch_y']/2-p['frame_hole_d']/2>p['beam_width']/2+1,'Klemmbolzen treffen den Querträger statt seitlich vorbeizulaufen')
    need(p['bearing_bore']<p['bearing_od']-8,'Lagerabmessungen unplausibel')
    need(p['roller_root_r']>p['bearing_od']/2+2,'Nut unterschreitet erforderliche Lagersitzwand')
    need(p['roller_outer_r']>p['roller_root_r'],'Rollennut besitzt keine Tiefe')
    need(q['groove_half_width']<q['roller_half_height']-2,'Rollennut durchbricht Stirnseiten')
    need(p['track_half_height']>=q['groove_half_width']+1,'Laufbahnflanken sind kürzer als Rollennut')
    need(p['cap_t']==p['roller_end_land'],'Deckeldicke und Stirnland müssen in dieser Topologie gleich sein')
    need(p['bearing_od']/2+2<p['cap_hole_pcd']/2-p['cap_hole_d']/2,'Deckelschrauben schneiden den Lagersitz')
    need(p['cap_hole_pcd']/2+p['cap_hole_d']/2+1<p['cap_radius'],'Deckelschrauben zu dicht am Außenrand')
    need(p['cap_radius']+p['cap_pocket_gap']<p['roller_outer_r']-1,'Deckeltasche durchbricht Rollenaußenfläche')
    need(p['bearing_bore']<p['inner_spacer_d']<p['roller_web_bore']+.01,'Innenringdistanz kollidiert mit Rollensteg')
    need(p['bearing_bore']<p['axle_head_d'] and p['axle_thread_d']<p['bearing_bore'],'Rollenachse: Kopf/Gewinde passen nicht')
    need(p['fork_web_start']>p['roller_outer_r']+3,'Gabelsteg liegt im Rollenhüllraum')
    need(p['fork_width']/2>p['fork_bolt_y']+p['fork_hole_d']/2+2,'Gabelbohrung zu dicht am Rand')
    need(p['fork_back_length']>p['bearing_bore']/2+4,'Achse zu dicht an Gabelkante')
    need(p['fork_web_depth']>p['fork_hole_d']+4,'Gabelsteg zu dünn für Bohrung')
    need(p['web_bolt_z']+p['fork_hole_d']<q['fork_inner_z'],'Querbohrung außerhalb Gabelsteg')
    need(q['guide_ring_inner']>q['guide_post_outer']+10,'Stationärer Rahmen liegt im Guidepfosten')
    need(q['guide_ring_inner']>math.hypot(q['post_x']+p['post_size_x']/2,p['frame_beam_y']+p['post_size_y']/2)+2,'Stationärer Rahmen überschneidet Hauptpfosten')
    need(q['guide_ring_inner']>q['post_x']+p['post_size_x']/2+2,'Anschlusslaschen haben keine Länge')
    angles=sorted(a%360 for a in q['guide_angles']);gaps=[(angles[(i+1)%3]-angles[i])%360 for i in range(3)]
    need(min(gaps)>15 and max(gaps)<180,'Drei Führungsrollen müssen verschieden sein und den Ring umschließen (größte Winkellücke <180°)')
    need(q['side_length']>30,'Seitenriegel zu kurz')
    if p['frame_mode']==1:
        need(p['cfk_actual_od']>p['cfk_id']+2,'CFK-Rohrwand unplausibel')
        need(q['level_z']-16>q['cfk_port_reach']+3,'Ebenenabstand lässt keinen Platz für CFK-Guideklemmung')
        need(p['cfk_rim_offset']-16>q['cfk_port_reach']+3,'CFK-Rim-Abstand lässt keinen Platz für Guideklemmung')
        need(q['cfk_liner_t']>=.15,'Isolierzwischenlage zu dünn für OD-Toleranz')
        need(p['cfk_socket_length']>=25,'CFK-Klemmlänge unter vorläufigem Mindestwert25')
    if errors:raise ParameterError('\n'.join(errors))
    return q
