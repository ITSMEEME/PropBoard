"""Fit clamp hardware and variant-sized cable routes; verify both native selectors."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import frame
V=A.Vector;native=O/'Quad_HEPS_Innenverkabelung.FCStd';D=A.openDocument(str(native));lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');control=D.getObject('Variantensteuerung');configs=json.loads((H/'Konfigurationen.json').read_text());variants=json.loads((H/'Varianten.json').read_text());rows=json.loads((O/'Instanzen.json').read_text());common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());sized=json.loads((O/'Groessen_Instanzen.json').read_text());geometry=json.loads((O/'Geometrie_Pruefung.json').read_text());assert len(geometry['configurations'])==50 and all(c['local_geometry_passed'] for c in geometry['configurations']);hardware=[];cables=[];nets=[];cache={}
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
# Internal routing and material removal use the actual tube axes.
wirecache={};changes=[];modified={};maxL=configs[-1]['motor_half_spacing_mm']*math.sqrt(2)-210-36
for pidx,cfg in enumerate(configs):
 for vidx,v in enumerate(variants):
  L=cfg['motor_half_spacing_mm']*math.sqrt(2)-210-36;starts=[V(*x) for x in v['start']];ro=(v['od']+8)/2;ends=[a+(V(maxL,b[1],min(b[2],-(ro+8)))-a)*(L/maxL) for a,b in zip(starts,v['end'])]
  for part in ['Root','Motor']:
   r=next(r for r in rows if r['propeller_index']==pidx and r['variant']==v['id'] and r['part']==part);master=D.getObject(r['instance']).LinkedObject
   if master.Name in modified:continue
   shape=master.Shape.copy();before=shape.Volume;cutters=[]
   for start,end in zip(starts,ends):
    axis=end-start;axis.normalize();cutters.append(Part.makeCylinder(v['di']/2+.1,(end-start).Length+(34 if part=='Root' else 8),start-axis*(30 if part=='Root' else 4),axis))
   if part=='Root':
    cutters.append(Part.makeCylinder(6,60,V(-65,0,-10)))
    for start in starts:
     for sign in [-1,1]:
      a=V(-58,sign*9,29);b=V(-15,sign*max(9,abs(start.y)),29)
      for fraction in [.4,.65]:q=a+(b-a)*fraction;cutters.append(Part.makeCylinder(2.5,18,V(q.x,q.y,20)))
   else:
    motorX=cfg['motor_half_spacing_mm']*math.sqrt(2)-210
    for x,y in [(25,0),(-25,0),(0,25),(0,-25)]:cutters.append(Part.makeCylinder(5.5,9,V(motorX+x,y,-15)))
   result=shape.cut(tuple(cutters),1e-5)
   if not result.isValid():result.fix(1e-7,1e-7,1e-6)
   assert result.isValid() and len(result.Solids)==1 and 0<result.Volume<=before+.1,(pidx,v['id'],part)
   master.Shape=Part.Compound([result]);modified[master.Name]=result.Volume*2810e-9;changes.append(dict(master=master.Name,part=part,variant=v['id'],propeller_index=pidx,before_mm3=before,after_mm3=result.Volume,saved_g=(before-result.Volume)*2810e-6))
  # End pads must be annular to admit the protected cable.
  for row in [r for r in rows if r['propeller_index']==pidx and r['variant']==v['id'] and r['part'].startswith('Pad')]:
   obj=D.getObject(row['instance']).LinkedObject
   if obj.Name in modified:continue
   shape=obj.Shape.copy()
   for start,end in zip(starts,ends):
    axis=end-start;axis.normalize();shape=shape.cut(Part.makeCylinder(v['di']/2+.1,(end-start).Length+8,start-axis*4,axis))
   assert shape.isValid() and len(shape.Solids)==1;obj.Shape=Part.Compound([shape]);modified[obj.Name]=shape.Volume*1900e-9
  for angle in [45,135,225,315]:
   th=math.radians(angle);u=V(math.cos(th),math.sin(th),0);gr=A.Rotation(u,V(-u.y,u.x,0),V(0,0,1),'ZXY');origin=u*210+V(0,0,88)
   assignments=[('DC_plus',0,-7 if v['count']==1 else -2,35,12),('DC_minus',0 if v['count']==1 else 1,7 if v['count']==1 else 0,35,12),('Signal',0 if v['count']<=2 else 2,0 if v['count']==1 else (6 if v['count']==2 else 0),.5,4)]
   for name,j,offset,area,od in assignments:
    start=starts[j];end=ends[j];axis=end-start;length=axis.Length;axis.normalize();sr=frame(axis);offsetvec=sr.multVec(V(offset,10 if name=='Signal' and v['count']==1 else 0,0));base=start-axis*30+offsetvec;radius=(area/math.pi)**.5;core=Part.makeCylinder(radius,length+34,base,axis);outer=Part.makeCylinder(od/2,length+34,base,axis);ins=outer.cut(core)
    for suffix,shape,density in [('Cu',core,8960),('Isolation',ins,1400)]:
     m=D.addObject('Part::Feature',f'P{pidx}_{v["id"]}_{angle}_{name}_{suffix}');m.Shape=Part.Compound([shape]);lib.addObject(m);m.Visibility=False;link=D.addObject('App::Link',m.Name+'_Einbau');link.setLink(m);link.LinkPlacement=A.Placement(origin,gr);assembly.addObject(link);link.Visibility=True;link.setExpression('Visibility',f'Variantensteuerung.Variante == {vidx} ? (Variantensteuerung.Propeller == {pidx} ? 1 : 0) : 0');cables.append(dict(instance=link.Name,id=m.Name,label=name+' '+suffix,group='Innenverkabelung',variant=v['id'],propeller_index=pidx,part=suffix,mass_kg=shape.Volume*density*1e-9,placement_mm=list(origin),placement_quaternion=list(gr.Q)))
    nets.append(dict(net=name,variant=v['id'],propeller_index=pidx,corner_deg=angle,tube=j,conductor_mm2=area,assumed_outer_diameter_mm=od,length_mm=length+34,tube_inner_diameter_mm=v['di'],nominal_bore_only=True,tube_min_ID_verified=False,cable_OD_verified=False,nominal_bundle_liner_radial_clearance_mm=.1 if v['count']==2 else None,terminations_verified=False,ampacity_verified=False))
   for j,(start,end) in enumerate(zip(starts,ends)):
    if j not in {x[1] for x in assignments}:continue
    axis=end-start;length=axis.Length;axis.normalize();liner=Part.makeCylinder(v['di']/2-.1,length+33,start-axis*30,axis).cut(Part.makeCylinder(v['di']/2-.4,length+35,start-axis*31,axis));m=D.addObject('Part::Feature',f'P{pidx}_{v["id"]}_{angle}_Innenliner');m.Shape=Part.Compound([liner]);lib.addObject(m);m.Visibility=False;link=D.addObject('App::Link',m.Name+'_Einbau');link.setLink(m);link.LinkPlacement=A.Placement(origin,gr);assembly.addObject(link);link.Visibility=True;link.setExpression('Visibility',f'Variantensteuerung.Variante == {vidx} ? (Variantensteuerung.Propeller == {pidx} ? 1 : 0) : 0');cables.append(dict(instance=link.Name,id=m.Name,label='Innenliner, Werkstoffannahme PTFE',group='Innenverkabelung',variant=v['id'],propeller_index=pidx,part='Innenliner',mass_kg=liner.Volume*2200e-9,placement_mm=list(origin),placement_quaternion=list(gr.Q)))
 print('Internal routing',cfg['label'],flush=True)
for row in rows:
 obj=D.getObject(row['instance']).LinkedObject
 if obj.Name in modified:row['mass_kg']=modified[obj.Name]
(O/'Materialvergleich.json').write_text(json.dumps(changes,indent=2))
(O/'Instanzen.json').write_text(json.dumps(rows,indent=2))
control.addProperty('App::PropertyBool','CarbonAuslegerAnzeigen','Ansicht');control.CarbonAuslegerAnzeigen=True
for row in rows+cables:
 if row['part'].startswith('Tube') or row['part']=='Innenliner':
  obj=D.getObject(row['instance']);old=next(exp for prop,exp in obj.ExpressionEngine if prop=='Visibility');obj.setExpression('Visibility','Variantensteuerung.CarbonAuslegerAnzeigen == 1 ? ('+old+') : 0')
checks=[]
for pidx,cfg in enumerate(configs):
 control.Propeller=cfg['label']
 for v in variants:
  control.Variante=v['id'];D.recompute();visible=[r for r in rows+hardware+sized+cables if D.getObject(r['instance']).Visibility];assert all(r['propeller_index']==pidx and r.get('variant',v['id'])==v['id'] for r in visible);assert sum(r.get('part','').startswith('Tube') for r in visible)==4*v['count'];assert sum(r.get('part')=='Motor' for r in visible)==4;assert sum(r.get('part')=='Bolt' for r in visible)==16*v['count'];checks.append(dict(propeller_index=pidx,propeller=cfg['label'],variant=v['id'],visible_config_instances=len(visible),arm_tubes=4*v['count'],mass_modeled_excluding_propellers_kg=sum(r['mass_kg'] for r in common+visible),passed=True))
 for row in [r for r in sized if r['propeller_index']==pidx and r.get('id')=='D05_MN1330_LEGACY_REF']:
  pos=D.getObject(row['instance']).LinkPlacement.Base
  assert abs(abs(pos.x)-cfg['motor_half_spacing_mm'])<1e-6 and abs(abs(pos.y)-cfg['motor_half_spacing_mm'])<1e-6
 print('Selector',cfg['label'],'all5 passed',flush=True)
def dimension_expression(values,selector):
 expr=str(values[-1])+' mm'
 for index in reversed(range(len(values)-1)):expr=f'{selector} == {index} ? {values[index]} mm : ({expr})'
 return expr
for name,values in [('PropellerDurchmesser',[c['diameter_mm'] for c in configs]),('PropellerSteigung',[c['pitch_mm'] for c in configs]),('MotorHalbabstand',[c['motor_half_spacing_mm'] for c in configs]),('AussenbreiteOhneSchutz',[c['unprotected_width_mm'] for c in configs])]:
 control.addProperty('App::PropertyLength',name,'Abmessungen');control.setExpression(name,dimension_expression(values,'Variantensteuerung.Propeller'));control.setEditorMode(name,1)
control.Hinweis='DC und Signal im Auslegerrohr; Regler nahe Motor geplant. Hauptversorgung,kurze Phasen,Stecker und Zugentlastung offen. Keine Festigkeits-/Flugfreigabe.'
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
