"""Physical conductor/insulation routing proposal, explicit open OEM terminations."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part,PartDesign
V=A.Vector;native=O/'Quad_Parametrisch_V1_V4.FCStd';D=A.openDocument(str(native));assembly=D.getObject('Montage');lib=D.getObject('Bauteilbibliothek');rows=[];nets=[]
# Replace only this generator's prior cable instances when rerun.
prior=json.loads((O/'Gemeinsame_Instanzen.json').read_text());owned=[r for r in prior if r.get('group')=='Kabelplanung']
if owned:
 oldmass=sum(r['mass_kg'] for r in owned)
 for r in owned:
  obj=D.getObject(r['instance']);master=obj.LinkedObject;D.removeObject(obj.Name);D.removeObject(master.Name)
 (O/'Gemeinsame_Instanzen.json').write_text(json.dumps([r for r in prior if r not in owned],indent=2))
 oldproof=json.loads((O/'Varianten_Pruefung.json').read_text())
 for cfg in oldproof['switch_checks']:cfg['mass_modeled_kg']-=oldmass
 (O/'Varianten_Pruefung.json').write_text(json.dumps(oldproof,indent=2))
def cable(name,points,area,od,circuit,end_a,end_b):
 pts=[V(*p) for p in points];curve=Part.BSplineCurve();curve.interpolate(pts);edge=curve.toShape();wire=Part.Wire([edge]);tangent=curve.tangent(curve.FirstParameter)[0];start=pts[0];core_r=math.sqrt(area/math.pi);outer=Part.Wire([Part.makeCircle(od/2,start,tangent)]);inner=Part.Wire([Part.makeCircle(core_r,start,tangent)]);s1=wire.makePipeShell([outer],True,False);s2=wire.makePipeShell([inner],True,False);ins=s1.cut(s2);assert s2.isValid() and ins.isValid() and len(ins.Solids)==len(s2.Solids)==1
 radii=[]
 for i in range(201):
  t=curve.FirstParameter+(curve.LastParameter-curve.FirstParameter)*i/200;k=curve.curvature(t)
  if k>1e-10:radii.append(1/k)
 for suffix,shape,density in [('Cu',s2,8960),('Isolation',ins,1400)]:
  master=D.addObject('Part::Feature',name+'_'+suffix);master.Shape=Part.Compound([shape]);lib.addObject(master);master.Visibility=False;o=D.addObject('App::Link',name+'_'+suffix+'_Einbau');o.setLink(master);assembly.addObject(o);o.Visibility=True;rows.append(dict(instance=o.Name,id=master.Name,label=name+' '+suffix,group='Kabelplanung',mass_kg=shape.Volume*density*1e-9,placement_mm=[0,0,0],placement_quaternion=[0,0,0,1]))
 nets.append(dict(net=name,circuit=circuit,from_port=end_a,to_port=end_b,conductor_mm2=area,assumed_outer_diameter_mm=od,length_mm=edge.Length,minimum_sampled_bend_radius_mm=min(radii) if radii else None,control_points_mm=points,terminations_verified=False,ampacity_verified=False))
# Finish the lower end-node stem at28mm width; retain upper flange interfaces.
common_pre=json.loads((O/'Gemeinsame_Instanzen.json').read_text());trim_mass_delta=0
for r in common_pre:
 if r['id'].startswith('D08_D04_HIGH_'):
  obj=D.getObject(r['instance']);sx=1 if '_P_' in r['id'] else -1;sy=1 if r['id'].endswith('_P') else -1;x0=385 if sx>0 else -394;yc=sy*75
  shape=obj.LinkedObject.Shape.cut((Part.makeBox(9,200,190,V(x0,yc+14,0)),Part.makeBox(9,200,190,V(x0,yc-214,0))),1e-5);assert shape.isValid() and len(shape.Solids)==1
  obj.LinkedObject.Shape=Part.Compound([shape]);newmass=shape.Volume*2810e-9;trim_mass_delta+=newmass-r['mass_kg'];r['mass_kg']=newmass
(O/'Gemeinsame_Instanzen.json').write_text(json.dumps(common_pre,indent=2))
for i,angle in enumerate([45,135,225,315],1):
 a=math.radians(angle);u=V(math.cos(a),math.sin(a),0);t=V(-u.y,u.x,0)
 def point(r,offset,z):return list(u*r+t*offset+V(0,0,z))
 for sign,name in [(-1,'DC_minus'),(1,'DC_plus')]:cable(f'R{i}_{name}',[point(100,sign*18,-180),point(200,sign*18,-180),point(300,sign*18,-180)],35,12,'DC branch',f'Verteiler_R{i}_{name}',f'ESC{i}_{name}_Planport')
 for j,phase in enumerate(['U','V','W']):cable(f'R{i}_{phase}',[point(320,(j-1)*18,-150),point(420,(j-1)*18,-130),point(540,(j-1)*18,-100),point(665,(j-1)*18,-35)],25,10,'motor phase',f'ESC{i}_{phase}_Planport',f'MN1330_{i}_{phase}_OEM_Kabelende_offen')
 cable(f'R{i}_Signal', [point(100,48,-200),point(200,48,-200),point(300,48,-200)],.5,5,'control harness envelope','Flightcontroller_Planport',f'ESC{i}_Signal_Pinout_offen')
for sign,name in [(-1,'minus'),(1,'plus')]:cable('Haupt_DC_'+name,[[sign*35,-260,-230],[sign*35,-160,-230],[sign*35,-60,-230]],95,18,'main DC','Akku_Schutzkette_Planport','Verteiler_Planport')
D.recompute();D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());common+=rows;(O/'Gemeinsame_Instanzen.json').write_text(json.dumps(common,indent=2));proof=json.loads((O/'Varianten_Pruefung.json').read_text());proof['native_sha256']=sha;mass=sum(r['mass_kg'] for r in rows)
for c in proof['switch_checks']:c['mass_modeled_kg']+=mass+trim_mass_delta
(O/'Varianten_Pruefung.json').write_text(json.dumps(proof,indent=2));(O/'Kabel_Instanzen.json').write_text(json.dumps(rows,indent=2));(O/'Kabelbaum.json').write_text(json.dumps(dict(native_sha256=sha,nets=nets,mass_kg=mass,scope='26 routed conductor/jacket pairs; signal cable is an equivalent envelope,not a real pinned twisted-pair design. All power cable copper sections and insulationODs are design assumptions. Planning ports have no fitted lugs/connectors. Mounting clips,ESC/battery placements,EMC,thermal ampacity and OEM motor lead transitions are open.',production_ready=False),indent=2));print('Cable routing saved',len(nets),mass,sha,flush=True)
