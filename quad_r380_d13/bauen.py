"""Replace legacy35mm2/OD12+OD4 placeholder routes with selected standard cable envelopes.
Unchanged CFK/Al load path;no inventedOEM pins,ports or purchased connector shells.
"""
from pathlib import Path
import sys,json,math,hashlib
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(R/'quad_r380_d07'))
import FreeCAD as A,Part,PartDesign
from geometrie import frame,placed
sys.path.append(str(H));from planung import layout,axis_geometry
P=json.loads((H/'parameter.json').read_text());VARS=json.loads((R/'quad_r380_d10/Varianten.json').read_text());CONFIGS=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());source=R/'quad_r380_d12/Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd';source_sha=hashlib.sha256(source.read_bytes()).hexdigest();D=A.openDocument(str(source));lib=D.getObject('Bauteilbibliothek');asm=D.getObject('Montage');control=D.getObject('Variantensteuerung');old=json.loads((R/'quad_r380_d10/Ausgabe/Kabel_Instanzen.json').read_text());masters=set()
# Protect the exact pre-existing structural shapes in the same document process.
protected={}
for o in D.Objects:
 if o.TypeId=='Part::Feature' and (o.Name.startswith('LAND_') and any(s in o.Name for s in ['_Carrier','_FootBase','_Leg']) or o.Name.startswith('P') and any(o.Name.endswith(s) for s in ['_Root','_Motor','_Tube0','_Tube1','_Tube2','_Tube3'])):
  protected[o.Name]=hashlib.sha256(o.Shape.exportBrepToString().encode()).hexdigest()
for row in old:
 o=D.getObject(row['instance']);assert o is not None;masters.add(o.LinkedObject.Name);D.removeObject(o.Name)
for name in masters:
 assert name.startswith('P') and D.getObject(name).TypeId=='Part::Feature';D.removeObject(name)
records=[];nets=[];parts=[];models=[]

def cable(L,net,od):
 ro=od/2
 if net.startswith('DC_'):
  area=P['DC']['conductor_mm2'];core=Part.makeCylinder(math.sqrt(area/math.pi),L);outside=Part.makeCylinder(ro,L);return core,outside.cut(core),area
 count={'CAN':4,'PWM':3,'SERVICE_5C':5}[net];rr=math.sqrt(.25/math.pi);sleeve_r=.55;shield_ro=ro-.4;shield_ri=shield_ro-.05
 if net=='CAN':positions=[(-1.05,-.6),(-1.05,.6),(1.05,-.6),(1.05,.6)]
 else:positions=[(1.15*math.cos(2*math.pi*i/count),1.15*math.sin(2*math.pi*i/count)) for i in range(count)]
 # Parallel core geometry resolves radial packing/material volumes;twist and braid are not meshed.
 copper=[Part.makeCylinder(rr,L,A.Vector(x,y,0)) for x,y in positions];copper.append(Part.makeCylinder(shield_ro,L).cut(Part.makeCylinder(shield_ri,L)))
 ins=Part.makeCylinder(ro,L)
 for c in copper:ins=ins.cut(c)
 return Part.Compound(copper),ins,.25*count

for pi,c in enumerate(CONFIGS):
 for vi,v in enumerate(VARS):
  starts,ends=axis_geometry(v,c);local=[];used=set()
  for net,t,x,y,od in layout(v):
   a=A.Vector(*starts[t]);b=A.Vector(*ends[t]);axis=b-a;L=axis.Length;axis.normalize();rot=frame(axis);base=a-axis*30+rot.multVec(A.Vector(x,y,0));cu,ins,area=cable(L+34,net,od)
   for suffix,s,density in [('Cu',cu,8960),('Isolation',ins,1400)]:
    s=placed(s,tuple(base),rot);assert s.isValid(),(pi,v['id'],net,suffix);name=f'H13_P{pi}_{v["id"]}_{net}_{suffix}';m=D.addObject('Part::Feature',name);m.Shape=Part.Compound([s]);lib.addObject(m);m.Visibility=False;mass=s.Volume*density*1e-9;local.append(dict(id=m.Name,net=net,part=suffix,mass_kg=mass,tube=t,OD_design_max_mm=od));parts.append(dict(master=m.Name,propeller_index=pi,variant=v['id'],net=net,part=suffix,tube=t,offset_xy_mm=[x,y],area_conductor_mm2=area,OD_design_max_mm=od,geometry_scope='Cable design-envelope/core-area model;twist and braid not resolved;notOEM-validated cable CAD.'))
   nets.append(dict(propeller_index=pi,variant=v['id'],net=net,tube=t,axis_start_local_mm=list(a),axis_end_local_mm=list(b),centre_offset_xy_mm=[x,y],OD_design_max_mm=od,straight_route_length_mm=L+34,planned_stock_or_extension_length_mm=1200));used.add(t)
  for t in sorted(used):
   a=A.Vector(*starts[t]);b=A.Vector(*ends[t]);axis=b-a;L=axis.Length;axis.normalize();shape=Part.makeCylinder(v['di']/2-.1,L+33,a-axis*30,axis).cut(Part.makeCylinder(v['di']/2-.4,L+35,a-axis*31,axis));name=f'H13_P{pi}_{v["id"]}_Liner{t}';m=D.addObject('Part::Feature',name);m.Shape=Part.Compound([shape]);lib.addObject(m);m.Visibility=False;local.append(dict(id=m.Name,net='Liner',part='Innenliner',mass_kg=shape.Volume*2200e-9,tube=t))
  for angle in [45,135,225,315]:
   th=math.radians(angle);u=A.Vector(math.cos(th),math.sin(th),0);gr=A.Rotation(u,A.Vector(-u.y,u.x,0),A.Vector(0,0,1),'ZXY');origin=u*210+A.Vector(0,0,88)
   for r in local:
    m=D.getObject(r['id']);o=D.addObject('App::Link',r['id']+'_'+str(angle));o.setLink(m);o.LinkPlacement=A.Placement(origin,gr);asm.addObject(o);expr=f'Variantensteuerung.Variante == {vi} ? (Variantensteuerung.Propeller == {pi} ? 1 : 0) : 0'
    if r['part']=='Innenliner':expr='Variantensteuerung.CarbonAuslegerAnzeigen == 1 ? ('+expr+') : 0'
    o.setExpression('Visibility',expr);records.append(dict(instance=o.Name,propeller_index=pi,variant=v['id'],id=m.Name,label=r['net']+' '+r['part'],part=r['part'],group='Innenverkabelung',mass_kg=r['mass_kg'],tube=r['tube'],placement_mm=list(origin),placement_quaternion=list(gr.Q),OD_design_max_mm=r.get('OD_design_max_mm')))
  print('H13',pi,v['id'],'routed',len(local),'parts',flush=True)
control.Variante='V4';control.Propeller=CONFIGS[-1]['label'];control.Hinweis='D13:Standardkabel-Entwurf,DC-Paar imRohr;Projektstecker definiert.OEM-JP/M6-Adapterbelegung,Ports,Biegungen,Thermik und Antriebsfreigabe offen.Strukturbefunde D12 bleiben bestehen.';D.recompute()
for name,sig in protected.items():assert hashlib.sha256(D.getObject(name).Shape.exportBrepToString().encode()).hexdigest()==sig,name
native=O/'Quad_Standardkabelbaum.FCStd';D.Label='Quad D13 – Standard-Innenkabelbaum; OEM-Adapter und Freigaben offen';D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();(O/'Kabel_Instanzen.json').write_text(json.dumps(records,indent=2));(O/'Kabel_Bauteile.json').write_text(json.dumps(parts,indent=2));(O/'Kabel_Netze.json').write_text(json.dumps(nets,indent=2));(O/'Aufbau.json').write_text(json.dumps(dict(native_sha256=sha,source_D12_native_sha256=source_sha,structural_shapes_unchanged=True,protected_BREP_count=len(protected),protected_structural_BREP_sha256=protected,OEM_ports_and_adapter_mapping_verified=False,connector_body_CAD_verified=False,closed_harness=False,production_ready=False),indent=2));print('D13 native saved',sha,flush=True)
