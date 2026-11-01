"""CBU20171005TG frame: straight stock, conical motor stays and explicit split sockets.
Connector dimensions are engineering assumptions awaiting load/laminate qualification.
"""
import math,json
import FreeCAD as A,Part
from spiegeln import reflected, X, Y, Z
from geometrie import V,box,cyl,ring,pcd,holes,shift

def apply(p,q,parts,scene):
    removed={'P12-006','P12-007','P12-008','P12-009','P12-021','P12-023','P12-024','P12-025','P12-026','P12-027'}
    scene[:]=[r for r in scene if r['id'] not in removed]
    for id in removed:parts.pop(id,None)
    nodes={};edges=[];cuts=[]
    def part(id,name,shape,material,process,features,open_items='Klemm-, Schrauben- und CFK-Festigkeitsnachweis offen'):
        s=shape.removeSplitter()
        if not s.isValid() or len(s.Solids)!=1:raise ValueError(id+': ungültiger CFK-Rahmenkörper')
        parts[id]=dict(id=id,name=name,shape=s,material=material,process=process,features=features,open=open_items,reference=False)
    def put(id,name,point=V(),rotation=None,variant='NOMINAL',shape=None):
        local=shape or parts[id]['shape'];s=local.copy();s.Placement=A.Placement(point,rotation or A.Rotation()).multiply(s.Placement)
        scene.append(dict(id=id,name=name,shape=s,context=False,variant=variant,manufacturing_shape=local.copy()))
    def node(name,point,base=None):nodes[name]=dict(pos=V(*point),ports=[],base=base);return name
    def connect(a,b):
        # Add an intermediate connector only when1000mm stock cannot cover the cut length.
        d=nodes[b]['pos']-nodes[a]['pos'];usable=p['cfk_stock_length']-2*p['cfk_end_trim'];n=max(1,math.ceil(d.Length/(usable-p['cfk_saw_kerf']+2*q['cfk_tube_inset'])))
        chain=[a]
        for i in range(1,n):chain.append(node(f'Stoß_{a}_{b}_{i}',tuple(nodes[a]['pos']+d*(i/n))))
        chain.append(b)
        for aa,bb in zip(chain,chain[1:]):edges.append((aa,bb))
    # Stable rings have short polygon sides. No straight tube is bent into a circle.
    postangles=[math.degrees(math.atan2(y,x))%360 for x in [-q['post_x'],q['post_x']] for y in [-p['frame_beam_y'],p['frame_beam_y']]]
    angles=sorted(postangles+[v%360 for v in q['guide_angles']]);expanded=[]
    for i,a in enumerate(angles):
        b=angles[(i+1)%len(angles)]+(360 if i==len(angles)-1 else 0);n=max(1,math.ceil((b-a)/p['cfk_max_panel_angle']))
        expanded.extend((a+(b-a)*j/n)%360 for j in range(n))
    angles=sorted(expanded);radius=math.hypot(q['post_x'],p['frame_beam_y']);ringnodes={}
    for li,z in enumerate([-q['cfk_rim_z'],0,q['cfk_rim_z']]):
        for i,a in enumerate(angles):
            isguide=any(abs((a-v+180)%360-180)<1e-7 for v in q['guide_angles']);r=q['cfk_guide_radius'] if isguide else radius
            ringnodes[li,i]=node(f'Ring{li}_{i}',(r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),z))
        for i in range(len(angles)):connect(ringnodes[li,i],ringnodes[li,(i+1)%len(angles)])
    for i in range(len(angles)):
        for li in [0,1]:connect(ringnodes[li,i],ringnodes[li+1,i])
    # Motor plate support: four inclined struts per motor, no1.84m bending beam.
    adapter_z=q['beam_z']+p['cfk_node_core_r']
    for sign,label,li in [(1,'Oben',2),(-1,'Unten',0)]:
        for xsign in [-1,1]:
            for ysign in [-1,1]:
                x=xsign*p['motor_mount_bolt_x'];y=ysign*p['frame_beam_y'];a=math.degrees(math.atan2(y,xsign*q['post_x']))%360
                idx=min(range(len(angles)),key=lambda i:abs((angles[i]-a+180)%360-180))
                name=node(f'{label}_Motorstütze_{xsign}_{ysign}',(x,y,sign*adapter_z),('motor',sign));connect(name,ringnodes[li,idx])
    # Localized metal bridge remains under the central bearing pedestal.
    for xs in [-1,1]:
        for ys in [-1,1]:
            x=xs*(p['cfk_bridge_length']/2+p['cfk_bridge_end_t']+p['cfk_node_core_r']);y=ys*p['foot_pitch_y']/2
            a=math.degrees(math.atan2(ys*p['frame_beam_y'],xs*q['post_x']))%360;idx=min(range(len(angles)),key=lambda i:abs((angles[i]-a+180)%360-180))
            name=node(f'Mittelstütze_{xs}_{ys}',(x,y,0),('bridge',xs));connect(name,ringnodes[1,idx])
    for a,b in edges:
        d=nodes[b]['pos']-nodes[a]['pos'];d.normalize();nodes[a]['ports'].append(d);nodes[b]['ports'].append(-d)
    # Standard split socket, M4 flange fixing and transverse M4 pinch screws.
    face=p['cfk_node_face'];ft=p['cfk_socket_flange_t'];sl=p['cfk_socket_length'];bore=p['cfk_socket_bore']/2;fr=p['cfk_socket_flange_r'];br=p['cfk_socket_body_r'];cg=p['cfk_clamp_gap'];total=ft+sl
    flangeholes=pcd(4,15,45)
    socket=cyl(fr,ft).fuse(cyl(br,sl,z=ft))
    for y in [-18,18]:socket=socket.fuse(box(16,12,10,-8,y-6,ft+sl/2-5))
    socket=socket.cut(cyl(bore,total+2,z=-1));socket=holes(socket,flangeholes,4.5,-1,total+2);socket=holes(socket,flangeholes,7.5,ft-4,5)
    for side in [-1,1]:
        s=socket.common(box(100,100,total+2,-100 if side<0 else cg/2,-50,-1)) if side<0 else socket.common(box(100,100,total+2,cg/2,-50,-1))
        # Negative half must end at-cg/2, not at0.
        if side<0:s=socket.common(box(100-cg/2,100,total+2,-100,-50,-1))
        for y in [-18,18]:s=s.cut(Part.makeCylinder((3.3 if side<0 else 4.5)/2,20,V(-10,y,ft+sl/2),V(1,0,0)))
        part('CFK-KLEMM-'+('A' if side<0 else 'B'),'Rohrklemmhälfte',s,'EN AW-7075 T6','Drehen/Fräsen/Kernbohren',f'BoreØ{2*bore}; Klemmlänge{sl}; M4-Flansch/Queranzug; Halbschnitt{cg}','Klemmdruck und M4-Vorspannung fehlen; keine Rohrquerbohrung')
    liner=ring(p['cfk_actual_od']/2,bore,0,sl).cut(box(fr, cg,sl+2,0,-cg/2,-1))
    part('CFK-ZWISCHENLAGE','Isolierzwischenlage',liner,'GFK-/Isolierfilm, Auswahl offen','Schneiden/Anpassen',f't{q["cfk_liner_t"]}; Länge{sl}','Auf gemessenen Rohr-OD anpassen; PU-Reibwert und Kriechen nicht nachgewiesen')
    # Each multi-port central body has real flange seats and symbolic M4 core holes.
    min_angle=180
    for ni,(name,n) in enumerate(nodes.items()):
        dirs=n['ports']
        for i,u in enumerate(dirs):
            for v in dirs[i+1:]:min_angle=min(min_angle,math.degrees(math.acos(max(-1,min(1,u.dot(v))))))
        s=Part.makeSphere(p['cfk_node_core_r'])
        for u in dirs:
            boss=Part.makeCone(14,fr,face);boss.Placement=A.Placement(V(),A.Rotation(V(0,0,1),u));s=s.fuse(boss)
        if n['base']:
            kind,sign=n['base'];core=p['cfk_node_core_r']
            if kind=='motor':
                base=box(50,50,12,-25,-25,-core) if sign>0 else box(50,50,12,-25,-25,core-12)
                s=s.fuse(base);start=V(0,0,-core-1 if sign>0 else core+1);axis=V(0,0,sign);s=s.cut(Part.makeCylinder(3.4,11,start,axis))
            else:
                base=box(12,50,50,-core,-25,-25) if sign>0 else box(12,50,50,core-12,-25,-25)
                s=s.fuse(base);s=s.cut(Part.makeCylinder(3.4,11,V(-core-1 if sign>0 else core+1,0,0),V(sign,0,0)))
        # Flange holes, two in each split half. Eight-mm symbolic thread depth.
        for u in dirs:
            rot=A.Rotation(V(0,0,1),u)
            for x,y in flangeholes:
                start=rot.multVec(V(x,y,face-8));s=s.cut(Part.makeCylinder(1.65,9,start,u))
        id=f'CFK-KNOTEN-{ni:03d}';part(id,'Mehrport_Rahmenknoten',s,'EN AW-7075 T6','5-Achs-Fräsen/Bohren/Gewinde','PortflanscheØ42; M4-KernØ3.3×8; lokale Achsen='+json.dumps([[v.x,v.y,v.z] for v in dirs]),'Knotensteifigkeit, Schrauben und Fertigungstoleranzen nicht freigegeben');put(id,name,n['pos'])
        for pi,u in enumerate(dirs):
            rot=A.Rotation(V(0,0,1),u);point=n['pos']+u*face
            for half in ['A','B']:put('CFK-KLEMM-'+half,f'{name}_Port{pi}_{half}',point,rot)
            put('CFK-ZWISCHENLAGE',f'{name}_Port{pi}_Isolierung',point+u*ft,rot)
    threshold=math.degrees(2*math.atan(fr/face))+2
    if min_angle<threshold:raise ValueError(f'CFK-Ports zu dicht: {min_angle:.2f}° <{threshold:.2f}°; Rahmenwinkel/Knoten ändern')
    # Tubes carry no mounting holes. Length is measured shoulder-to-shoulder,30mm engagement per end.
    for i,(a,b) in enumerate(edges):
        delta=nodes[b]['pos']-nodes[a]['pos'];distance=delta.Length;u=delta/distance;length=distance-2*q['cfk_tube_inset'];free=distance-2*q['cfk_port_reach']
        if length<=0 or free<2:raise ValueError(f'CFK-Anschlüsse kollidieren: {a}/{b}, freie Rohrlänge{free:.2f}')
        if length>p['cfk_stock_length']-2*p['cfk_end_trim']+1e-8:raise ValueError('Zuschnitt über1000mm')
        id=f'CFK-ROHR-{i:03d}';shape=ring(p['cfk_id']/2,p['cfk_actual_od']/2,0,length)
        part(id,'CFK_Rohrzuschnitt',shape,'CFK CBU 2017 1005 TG','Trennschleifen/Sägen; Kanten versiegeln',f'Ø{p["cfk_actual_od"]}/Ø{p["cfk_id"]}×{length:.3f}; keine Querbohrung','Längentoleranz, Klemmdruck und CFK-Lastnachweis offen')
        put(id,f'CFK_Rohr_{i:03d}',nodes[a]['pos']+u*q['cfk_tube_inset'],A.Rotation(V(0,0,1),u));cuts.append(dict(id=id,length_mm=length,from_node=a,to_node=b,engagement_each_end_mm=sl,free_span_mm=free))
    # End plates on the short central bridge.
    ex=p['cfk_bridge_end_t'];ey=p['middle_width']+30;ez=p['middle_height']+20
    ep=box(ex,ey,ez,0,-ey/2,-ez/2)
    for y in [-p['foot_pitch_y']/2,p['foot_pitch_y']/2]:ep=ep.cut(Part.makeCylinder(p['frame_hole_d']/2,ex+2,V(-1,y,0),V(1,0,0)))
    part('CFK-BRUECKE-END','Mittelbrücken_Endplatte',ep,'EN AW-6082 T6','Fräsen/Bohren; Schweißanschluss',f'{ex}×{ey}×{ez}; 2×Ø{p["frame_hole_d"]}','Schweißnaht und Wärmeeinflusszone offen')
    put('CFK-BRUECKE-END','Mittelbrücke_Ende_Pos',V(p['cfk_bridge_length']/2,0,0));em=reflected(ep,X);put('CFK-BRUECKE-END','Mittelbrücke_Ende_Neg',V(-p['cfk_bridge_length']/2,0,0),variant='MX',shape=em)
    # Through-post guide saddles; fitting liners accommodate the supplier's OD tolerance.
    depth=p['cfk_guide_saddle_depth'];height=32;wide=44
    for half in ['A','B']:
        s=box(depth-cg/2 if half=='A' else 22-cg/2,wide,height,-depth if half=='A' else cg/2,-wide/2,-height/2)
        s=s.cut(cyl(bore,height+2,z=-height/2-1))
        for y in [-17,17]:s=s.cut(Part.makeCylinder((4.2 if half=='A' else 5.5)/2,depth+24,V(-depth-1,y,0),V(1,0,0)))
        if half=='A':
            for z in [-p['web_bolt_z'],p['web_bolt_z']]:s=s.cut(Part.makeCylinder(2.5,10,V(-depth-1,0,z),V(1,0,0)))
        part('CFK-GUIDE-'+half,'Guide_Rohrklemmhälfte',s,'EN AW-7075 T6','Fräsen/Bohren/Gewinde','Ø20.6-Durchgang, M5-Klemmung, frontseitig2×M6-Kernloch9tief' if half=='A' else 'Ø20.6, M5-Durchgänge','Keine Bohrung durch CFK; Zwischenlage auf Rohr-Istmaß anpassen')
    gl=ring(p['cfk_actual_od']/2,bore,-height/2,height).cut(box(fr,cg,height+2,0,-cg/2,-height/2-1));part('CFK-GUIDE-FILM','Guide_Isolierlage',gl,'GFK-/Isolierfilm, Auswahl offen','Schneiden/Anpassen',f't{q["cfk_liner_t"]}; Länge{height}')
    for sign,label in [(1,'Oben'),(-1,'Unten')]:
        for i,a in enumerate(q['guide_angles']):
            rot=A.Rotation(V(0,0,1),a);r=q['cfk_guide_radius'];point=V(r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),sign*q['level_z'])
            for half in ['A','B']:put('CFK-GUIDE-'+half,f'{label}_Guideklemmung{i}_{half}',point,rot)
            put('CFK-GUIDE-FILM',f'{label}_Guideklemmung{i}_Film',point,rot)
    q['cfk_cut_list']=cuts;q['cfk_node_count']=len(nodes);q['cfk_tube_count']=len(cuts);q['cfk_ring_vertices']=len(angles);q['cfk_min_port_angle_deg']=min_angle;q['cfk_nominal_area_mm2']=math.pi/4*(p['cfk_od']**2-p['cfk_id']**2);q['cfk_nominal_I_mm4']=math.pi/64*(p['cfk_od']**4-p['cfk_id']**4)
    bounds=Part.Compound([r['shape'] for r in scene]).BoundBox
    q['frame_envelope_x']=bounds.XLength;q['frame_envelope_y']=bounds.YLength;q['height']=bounds.ZLength;q['guide_ring_outer']=max(bounds.XLength,bounds.YLength)/2
    q['cfk_nodes']=[dict(name=name,position_mm=[n['pos'].x,n['pos'].y,n['pos'].z],port_axes=[[v.x,v.y,v.z] for v in n['ports']]) for name,n in nodes.items()]
    return parts,scene,q
