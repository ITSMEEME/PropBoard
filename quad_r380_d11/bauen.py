"""Motor-near, independent ESC carriers; unidentified ESC drawing remains a datum."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign,MeshPart
from geometrie import socket_shape,frame,placed,capsule
V=A.Vector;D=A.openDocument(str(R/'quad_r380_d10/Ausgabe/Quad_HEPS_Innenverkabelung.FCStd'));lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');control=D.getObject('Variantensteuerung');cfgs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());variants=json.loads((R/'quad_r380_d10/Varianten.json').read_text());maxL=cfgs[-1]['motor_half_spacing_mm']*math.sqrt(2)-246;rows=[];modules=[];parts_data=[];norms={}
for key,path in [('BoltM4',None),('NutM4',None),('WasherM4',None),('BoltM3',H/'Quellen/Normteile/ISO4762_M3x6.brep'),('WasherM3',R/'quad_r380_d01/Quellen/Normteile/ISO7089_M3.brep')]:
 if path is None:norms[key]=D.getObject({'BoltM4':'Klemmung_Bolt','NutM4':'Klemmung_Nut','WasherM4':'Klemmung_Washer'}[key]).Shape.copy()
 else:s=Part.Shape();s.read(str(path));norms[key]=s
 assert norms[key].isValid()
print('M3 bounds',norms['BoltM3'].BoundBox,flush=True)
washer4=norms['WasherM4'].BoundBox.ZLength;washer3=norms['WasherM3'].BoundBox.ZLength;assert abs(washer3-.5)<.001
prototype_parts={};component_records=[];bbox_records=[];std_objects={}
for name,shape in norms.items():
 o=D.addObject('Part::Feature','ESC_Standard_'+name);o.Shape=shape;lib.addObject(o);o.Visibility=False;std_objects[name]=o
def place_norm(name,pos,rot):
 shape=Part.Compound([norms[name]]);shape.Placement=A.Placement(V(*pos),rot);return shape

def store_part(key,shape,density,role):
 assert shape.isValid(),key
 if key not in prototype_parts:
  std=next((n for n,tag in [('BoltM4','_BoltM4_'),('NutM4','_NutM4_'),('WasherM4','_WasherM4_'),('BoltM3','_M3bolt'),('WasherM3','_M3washer')] if tag in key),None)
  if std:
   o=D.addObject('App::Link',key);o.setLink(std_objects[std]);o.LinkPlacement=shape.Placement
  else:
   o=D.addObject('Part::Feature',key);o.Shape=Part.Compound([shape])
  lib.addObject(o);o.Visibility=False;prototype_parts[key]=o
 return prototype_parts[key],shape.Volume*density*1e-9
for pidx,cfg in enumerate(cfgs):
 for vidx,v in enumerate(variants):
  a=V(*v['start'][0]);end=a+(V(maxL,v['end'][0][1],min(v['end'][0][2],-((v['od']+8)/2+8)))-a)*((cfg['motor_half_spacing_mm']*math.sqrt(2)-246)/maxL);axis=end-a;axis.normalize();sr=frame(axis);cx=cfg['motor_half_spacing_mm']*math.sqrt(2)-210-140;cy=(a+(end-a)*((cx-a.x)/(end.x-a.x))).y;plate=-138;p=dict(grip_length_mm=16,split_gap_mm=.5,socket_od_mm=v['od']+8,socket_bore_mm=v['od']+.6,ear_x_mm=v['od']/2+6,ear_top_mm=10.5,ear_axial_length_mm=12,end_pad_thickness_mm=.3);ear=p['ear_x_mm'];lower=socket_shape(p);upper=socket_shape(p,upper=True)
  for sign in [-1,1]:lower=lower.cut(Part.makeCylinder(2.25,45,V(sign*ear,20,8),V(0,-1,0)))
  pieces=[Part.makeBox(146,10,2,V(cx-73,cy+y-5,plate-2)) for y in [-33,33]];positions=[]
  for side in [-1,1]:
   x=cx+side*55-8;centre=a+(end-a)*((x-a.x)/(end.x-a.x));base=centre-axis*8;positions.append((centre,base));pieces.append(placed(lower,tuple(base),sr));start=base+sr.multVec(V((-12 if v['od']==20 else -math.sqrt((p['socket_od_mm']/2-.5)**2-36)),-6,16));finish=base+sr.multVec(V(-21,-22,16));channel_centre=base+sr.multVec(V(-19,-22,16));pieces.append(capsule(tuple(start),tuple(finish),2.5));height=channel_centre.z+1-(plate-2);channel=Part.makeBox(12,6,height,V(channel_centre.x-6,channel_centre.y-3,plate-2));channel=channel.cut(Part.makeBox(8,5,height+2,V(channel_centre.x-4,channel_centre.y-1,plate-3)));pieces.append(channel);pieces.append(Part.makeBox(10,76,2,V(channel_centre.x-5,cy-38,plate-2)))
  body=pieces[0].fuse(tuple(pieces[1:]),1e-5).removeSplitter()
  for x in [-63,63]:
   for y in [-33,33]:body=body.cut(Part.makeCylinder(1.7,6,V(cx+x,cy+y,plate-4)))
  if not body.isValid():body.fix(1e-7,1e-7,1e-6)
  assert body.isValid() and len(body.Solids)==1,(pidx,v['id'],'carrier',len(body.Solids))
  components=[('Carrier',body,2700,'carrier')]
  for j,(centre,base) in enumerate(positions):
   components.append((f'Cap{j}',placed(upper,tuple(base),sr),2700,'clamp_cap'))
   sleeve=Part.makeCylinder(v['od']/2+.3,16).cut(Part.makeCylinder(v['od']/2,18,V(0,0,-1))).cut(Part.makeBox(v['od'],.5,18,V(0,-.25,-1)));components.append((f'GFK{j}',placed(sleeve,tuple(base),sr),1900,'isolation'))
   hr=sr.multiply(A.Rotation(V(1,0,0),-90))
   for sign in [-1,1]:
    for n,y,rot in [('WasherM4',10.5,sr.multiply(A.Rotation(V(1,0,0),-90))),('WasherM4',-10.5-washer4,hr),('BoltM4',10.5+washer4,hr),('NutM4',-10.5-washer4,hr.multiply(A.Rotation(V(0,0,1),34)).multiply(A.Rotation(V(0,1,0),180)))]:
     pos=base+sr.multVec(V(sign*ear,y,8));components.append((n+'_'+str(j)+'_'+str(sign)+'_'+str(y),place_norm(n,tuple(pos),rot),7850,'hardware'))
  for x in [-63,63]:
   for y in [-33,33]:
    pos=V(cx+x,cy+y,plate);components.append((f'M3washer{x}_{y}',place_norm('WasherM3',tuple(pos),A.Rotation()),7850,'hardware'));components.append((f'M3bolt{x}_{y}',place_norm('BoltM3',tuple(pos+V(0,0,washer3)),A.Rotation()),7850,'planned_device_bolt'));pad=Part.makeCylinder(3.5,.5,V(pos.x,pos.y,plate-2.5)).cut(Part.makeCylinder(1.7,1,V(pos.x,pos.y,plate-2.75)));components.append((f'M3pad{x}_{y}',pad,1900,'isolation'))
  # Visual construction boundary only, explicitly not an OEM controller solid.
  points=[V(cx+x,cy+y,z) for z in [-180,-140.5] for x,y in [(-73,-37),(73,-37),(73,37),(-73,37)]];marks=[]
  for i,j in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
   delta=points[j]-points[i];marks.append(Part.makeCylinder(.25,delta.Length,points[i],delta))
  components.append(('Regler_Bauraum',Part.Compound(marks),0,'unidentified_ESC_datum'));local_records=[]
  for name,shape,density,role in components:
   key=f'ESC_P{pidx}_{v["id"]}_{name}'.replace('-','m').replace('.','p');master,mass=store_part(key,shape,density,role);local_records.append(dict(master=master.Name,part=name,role=role,mass_kg=mass))
  master=D.addObject('Part::Feature',f'ESC_Modul_P{pidx}_{v["id"]}');master.Shape=Part.Compound([s for _,s,_,_ in components]);lib.addObject(master);master.Visibility=False
  for angle in [45,135,225,315]:
   theta=math.radians(angle);u=V(math.cos(theta),math.sin(theta),0);rotation=A.Rotation(u,V(-u.y,u.x,0),V(0,0,1),'ZXY');origin=u*210+V(0,0,88);obj=D.addObject('App::Link',master.Name+'_Einbau');obj.setLink(master);obj.LinkPlacement=A.Placement(origin,rotation);assembly.addObject(obj);obj.Visibility=True;obj.setExpression('Visibility',f'Variantensteuerung.Variante == {vidx} ? (Variantensteuerung.Propeller == {pidx} ? 1 : 0) : 0');modules.append(dict(instance=obj.Name,propeller_index=pidx,variant=v['id'],corner_deg=angle,placement_mm=list(origin),placement_quaternion=list(rotation.Q),parts=local_records));component_records.extend(dict(instance=obj.Name+'_'+str(k),id=r['master'],label=r['part'],role=r['role'],propeller_index=pidx,variant=v['id'],mass_kg=r['mass_kg'],placement_mm=list(origin),placement_quaternion=list(rotation.Q)) for k,r in enumerate(local_records))
  bbox_records.append(dict(propeller_index=pidx,variant=v['id'],cx=cx,cy=cy,zmin=-180,zmax=-140.5,case_width_mm=74,case_length_mm=146,case_height_mm=39.5,motor_axis_radial_mm=cfg['motor_half_spacing_mm']*math.sqrt(2),local_origin_radial_mm=210,ESC_center_radial_mm=cx+210,motor_ESC_radial_offset_mm=140,carrier_mass_each_kg=sum(r['mass_kg'] for r in local_records),ESC_identity_verified=False))
  print('ESC carrier',cfg['label'],v['id'],round(sum(r['mass_kg'] for r in local_records)*1000,1),'g',flush=True)
D.recompute();D.Label='Quad D11 – motornahe Reglerhalter; Kaufteilzuordnung offen';native=O/'Quad_Motornahe_Reglerhalter.FCStd';D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Reglerhalter_Instanzen.json').write_text(json.dumps(modules,indent=2));(O/'Viewer_Komponenten.json').write_text(json.dumps(component_records,indent=2));(O/'Regler_Montage.json').write_text(json.dumps(dict(native_sha256=sha,carrier_revision=2,configurations=bbox_records,ESC_candidate='T-Motor M200A24S recommendation,unconfirmed drawing identity',screw_stack=dict(M3_length_mm=6,rail_mm=2,washer_mm=washer3,isolation_pad_mm=.5,nominal_thread_engagement_mm=6-2-washer3-.5,drawing_thread_depth_mm=4,CAD_thread_tip_intrusion_mm=-norms['BoltM3'].BoundBox.ZMin-2-washer3-.5,CAD_blind_depth_margin_mm=4-(-norms['BoltM3'].BoundBox.ZMin-2-washer3-.5)),device_geometry='Construction boundary from user74x146x39.5 drawing,not a regulator CAD model',electrical_ports_verified=False,ESC_mass_verified=False,production_ready=False),indent=2));print('Native ESC carrier project saved',sha,flush=True)
