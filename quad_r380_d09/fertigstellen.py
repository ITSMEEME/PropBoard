"""Fit clamp hardware and variant-sized cable routes; verify both native selectors."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import frame
V=A.Vector;native=O/'Quad_HEPS_Parametrisch.FCStd';D=A.openDocument(str(native));lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');control=D.getObject('Variantensteuerung');configs=json.loads((H/'Konfigurationen.json').read_text());variants=json.loads((R/'motoranschluss_varianten/Varianten.json').read_text())[:4];rows=json.loads((O/'Instanzen.json').read_text());common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());sized=json.loads((O/'Groessen_Instanzen.json').read_text());geometry=json.loads((O/'Geometrie_Pruefung.json').read_text());assert len(geometry['configurations'])==40 and all(c['local_geometry_passed'] for c in geometry['configurations']);hardware=[];cables=[];nets=[];cache={}
# Identical root-side geometry uses one master across all10 sizes.
for r in rows:
 if r['part']=='Root' or r['part'].endswith('_root'):
  obj=D.getObject(r['instance']);key=(r['variant'],r['part']);cache.setdefault(key,obj.LinkedObject);obj.setLink(cache[key])
norms={k:D.getObject('Klemmung_'+k) for k in ['Bolt','Nut','Washer']};assert all(norms.values());mass={k:o.Shape.Volume*7850e-9 for k,o in norms.items()};w=norms['Washer'].Shape.BoundBox.ZLength;maxL=configs[-1]['motor_half_spacing_mm']*math.sqrt(2)-210-36
for pidx,cfg in enumerate(configs):
 L=cfg['motor_half_spacing_mm']*math.sqrt(2)-210-36
 for vidx,v in enumerate(variants):
  ro=(v['od']+8)/2;ear=v['od']/2+6;starts=[V(*x) for x in v['start']];ends=[a+(V(maxL,b[1],min(b[2],-(ro+8)))-a)*(L/maxL) for a,b in zip(starts,v['end'])]
  for angle in [45,135,225,315]:
   a=math.radians(angle);u=V(math.cos(a),math.sin(a),0);gr=A.Rotation(u,V(-u.y,u.x,0),V(0,0,1),'ZXY');origin=u*210+V(0,0,88)
   for j,(start,end) in enumerate(zip(starts,ends)):
    axis=end-start;axis.normalize();sr=frame(axis);hr=sr.multiply(A.Rotation(V(1,0,0),-90))
    for side,base in [('root',start),('motor',end-axis*35)]:
     for sign in [-1,1]:
      for kind,y,rr in [('Washer',10.5,hr),('Washer',-10.5-w,hr),('Bolt',10.5+w,hr),('Nut',-10.5-w,hr.multiply(A.Rotation(V(0,0,1),34)).multiply(A.Rotation(V(0,1,0),180)))]:
       pos=origin+gr.multVec(base+sr.multVec(V(sign*ear,y,17.5)));rotation=gr.multiply(rr);o=D.addObject('App::Link',f'P{pidx}_{v["id"]}_Hardware');o.setLink(norms[kind]);o.LinkPlacement=A.Placement(pos,rotation);assembly.addObject(o);o.Visibility=True;o.setExpression('Visibility',f'Variantensteuerung.Variante == {vidx} ? (Variantensteuerung.Propeller == {pidx} ? 1 : 0) : 0');hardware.append(dict(instance=o.Name,variant=v['id'],propeller_index=pidx,part=kind,mass_kg=mass[kind],placement_mm=list(pos),placement_quaternion=list(rotation.Q)))
 print('Hardware',cfg['label'],flush=True)
# Cache local cable shapes; rotate them into all four corners.
wirecache={}
def cable(name,points,area,od,circuit,pidx,angle,from_port,to_port):
 key=(tuple(tuple(p) for p in points),area,od);rotation=A.Rotation(V(0,0,1),angle)
 if key not in wirecache:
  curve=Part.BSplineCurve();curve.interpolate([V(*p) for p in points]);edge=curve.toShape();wire=Part.Wire([edge]);t=curve.tangent(curve.FirstParameter)[0];start=V(*points[0]);outer=wire.makePipeShell([Part.Wire([Part.makeCircle(od/2,start,t)])],True,False);core=wire.makePipeShell([Part.Wire([Part.makeCircle(math.sqrt(area/math.pi),start,t)])],True,False);ins=outer.cut(core);assert all(s.isValid() and len(s.Solids)==1 for s in [core,ins]);masters=[]
  for suffix,s,density in [('Cu',core,8960),('Isolation',ins,1400)]:
   m=D.addObject('Part::Feature','Kabel_'+str(len(wirecache))+'_'+suffix);m.Shape=Part.Compound([s]);lib.addObject(m);m.Visibility=False;masters.append((m,s.Volume*density*1e-9,suffix))
  radii=[1/curve.curvature(t) for t in [curve.FirstParameter+(curve.LastParameter-curve.FirstParameter)*i/200 for i in range(201)] if curve.curvature(t)>1e-10];wirecache[key]=(masters,edge.Length,min(radii) if radii else None)
 masters,length,radius=wirecache[key]
 for master,mass,suffix in masters:
  obj=D.addObject('App::Link',f'P{pidx}_{name}_{suffix}');obj.setLink(master);obj.LinkPlacement=A.Placement(V(),rotation);assembly.addObject(obj);obj.Visibility=True;obj.setExpression('Visibility',f'Variantensteuerung.Propeller == {pidx} ? 1 : 0');cables.append(dict(instance=obj.Name,id=master.Name,label=name+' '+suffix,group='Kabelplanung',propeller_index=pidx,mass_kg=mass,placement_mm=[0,0,0],placement_quaternion=list(rotation.Q)))
 nets.append(dict(net=name,propeller_index=pidx,circuit=circuit,from_port=from_port,to_port=to_port,conductor_mm2=area,assumed_outer_diameter_mm=od,length_mm=length,minimum_sampled_bend_radius_mm=radius,terminations_verified=False,ampacity_verified=False))
for pidx,cfg in enumerate(configs):
 motorR=cfg['motor_half_spacing_mm']*math.sqrt(2)
 for i,angle in enumerate([45,135,225,315],1):
  for sign,name in [(-1,'DC_minus'),(1,'DC_plus')]:cable(f'R{i}_{name}',[[100,sign*18,-180],[200,sign*18,-180],[300,sign*18,-180]],35,12,'DC branch',pidx,angle,'Verteiler_Planport',f'ESC{i}_{name}_Planport')
  for j,phase in enumerate(['U','V','W']):
   dy=(j-1)*18;points=[[320,dy,-150],[320+.3*(motorR-320),dy,-130],[320+.65*(motorR-320),dy,-100],[motorR,dy,-35]];cable(f'R{i}_{phase}',points,25,10,'motor phase',pidx,angle,f'ESC{i}_{phase}_Planport',f'MN1330_{i}_{phase}_OEM_Kabelende_offen')
  cable(f'R{i}_Signal',[[100,48,-200],[200,48,-200],[300,48,-200]],.5,5,'control harness envelope',pidx,angle,'Flightcontroller_Planport',f'ESC{i}_Signal_Pinout_offen')
 for sign,name in [(-1,'minus'),(1,'plus')]:cable('Haupt_DC_'+name,[[sign*35,-260,-230],[sign*35,-160,-230],[sign*35,-60,-230]],95,18,'main DC',pidx,0,'Akku_Schutzkette_Planport','Verteiler_Planport')
 print('Cables',cfg['label'],flush=True)
checks=[]
for pidx,cfg in enumerate(configs):
 control.Propeller=cfg['label']
 for v in variants:
  control.Variante=v['id'];D.recompute();visible=[r for r in rows+hardware+sized+cables if D.getObject(r['instance']).Visibility];assert all(r['propeller_index']==pidx and r.get('variant',v['id'])==v['id'] for r in visible);assert sum(r.get('part','').startswith('Tube') for r in visible)==4*v['count'];assert sum(r.get('part')=='Motor' for r in visible)==4;assert sum(r.get('part')=='Bolt' for r in visible)==16*v['count'];checks.append(dict(propeller_index=pidx,propeller=cfg['label'],variant=v['id'],visible_config_instances=len(visible),arm_tubes=4*v['count'],mass_modeled_excluding_propellers_kg=sum(r['mass_kg'] for r in common+visible),passed=True))
 for row in [r for r in sized if r['propeller_index']==pidx and r.get('id')=='D05_MN1330_LEGACY_REF']:
  pos=D.getObject(row['instance']).LinkPlacement.Base
  assert abs(abs(pos.x)-cfg['motor_half_spacing_mm'])<1e-6 and abs(abs(pos.y)-cfg['motor_half_spacing_mm'])<1e-6
 print('Selector',cfg['label'],'all4 passed',flush=True)
def dimension_expression(values,selector):
 expr=str(values[-1])+' mm'
 for index in reversed(range(len(values)-1)):expr=f'{selector} == {index} ? {values[index]} mm : ({expr})'
 return expr
for name,values in [('PropellerDurchmesser',[c['diameter_mm'] for c in configs]),('PropellerSteigung',[c['pitch_mm'] for c in configs]),('MotorHalbabstand',[c['motor_half_spacing_mm'] for c in configs]),('AussenbreiteOhneSchutz',[c['unprotected_width_mm'] for c in configs])]:
 control.addProperty('App::PropertyLength',name,'Abmessungen');control.setExpression(name,dimension_expression(values,'Variantensteuerung.Propeller'));control.setEditorMode(name,1)
control.Variante='V4';control.Propeller=configs[-1]['label'];D.recompute()
# Remove unused old propellers/arms and duplicate root masters from the library.
used={o.LinkedObject.Name for o in assembly.Group if o.TypeId=='App::Link'}
for obj in list(lib.Group):
 if obj.Name not in used:
  if obj.TypeId=='PartDesign::Body':
   for child in reversed(list(obj.Group)):D.removeObject(child.Name)
  D.removeObject(obj.Name)
D.recompute();D.Label='Quad HEP-S –10 Durchmesser × V1–V4; Rotorhüllen';D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest()
for name,data in [('Hardware.json',hardware),('Kabel_Instanzen.json',cables),('Kabelbaum.json',dict(native_sha256=sha,nets=nets,closed_harness=False)),('Umschalter_Pruefung.json',dict(native_sha256=sha,checks=checks,OEM_propellers_modeled=False))]:(O/name).write_text(json.dumps(data,indent=2,ensure_ascii=False))
geometry['geometry_stage_native_sha256']=geometry['native_sha256'];geometry['native_sha256']=sha;(O/'Geometrie_Pruefung.json').write_text(json.dumps(geometry,indent=2))
print('Native finished',sha,flush=True)
