"""D12 native assembly: integrated lightweight landing feet and vertical ESC mounts."""
from pathlib import Path
import sys,json,math,hashlib,importlib.util,os
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
mod=importlib.util.spec_from_file_location('landing_geometry',H/'landegeometrie.py');G=importlib.util.module_from_spec(mod);mod.loader.exec_module(G)
catalog=json.loads((H/'Quellen/Regler/V200A24S.json').read_text());P=json.loads((H/'parameter.json').read_text());cfgs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());variants=json.loads((R/'quad_r380_d10/Varianten.json').read_text());P['max_arm_length_mm']=cfgs[-1]['motor_half_spacing_mm']*math.sqrt(2)-246
D=A.openDocument(str(R/'quad_r380_d10/Ausgabe/Quad_HEPS_Innenverkabelung.FCStd'));lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');norms={};std={}
for key,path in [('BoltM4',None),('NutM4',None),('WasherM4',None),('BoltM3',R/'quad_r380_d11/Quellen/Normteile/ISO4762_M3x6.brep'),('WasherM3',R/'quad_r380_d01/Quellen/Normteile/ISO7089_M3.brep'),('NutM3',R/'quad_r380_d01/Quellen/Normteile/ISO4032_M3.brep')]:
 if path is None:s=D.getObject({'BoltM4':'Klemmung_Bolt','NutM4':'Klemmung_Nut','WasherM4':'Klemmung_Washer'}[key]).Shape.copy()
 else:s=Part.Shape();s.read(str(path))
 norms[key]=s;o=D.addObject('Part::Feature','Landing_Standard_'+key);o.Shape=s;lib.addObject(o);o.Visibility=False;std[key]=o
modules=[];records=[];specs=[]
for i,c in enumerate(cfgs):
 if os.environ.get('D12_PROTOTYPE') and i!=0:continue
 for vi,v in enumerate(variants):
  cfg={**c,'index':i};parts,info=G.make_parts(v,cfg,P,norms);local=[]
  for name,shape,density,role in parts:
   key=f'LAND_P{i}_{v["id"]}_{name}'.replace('-','m').replace('.','p');tag=next((k for k in std if name.startswith(k+'_')),None)
   if tag:o=D.addObject('App::Link',key);o.setLink(std[tag]);o.LinkPlacement=shape.Placement
   else:o=D.addObject('Part::Feature',key);o.Shape=Part.Compound([shape])
   lib.addObject(o);o.Visibility=False;local.append(dict(master=o.Name,part=name,role=role,mass_kg=shape.Volume*density*1e-9))
  master=D.addObject('Part::Feature',f'LAND_Modul_P{i}_{v["id"]}');master.Shape=Part.Compound([p[1] for p in parts]);lib.addObject(master);master.Visibility=False
  for angle in [45,135,225,315]:
   rad=math.radians(angle);u=A.Vector(math.cos(rad),math.sin(rad),0);rot=A.Rotation(u,A.Vector(-u.y,u.x,0),A.Vector(0,0,1),'ZXY');origin=u*210+A.Vector(0,0,88);o=D.addObject('App::Link',master.Name+'_Einbau');o.setLink(master);o.LinkPlacement=A.Placement(origin,rot);assembly.addObject(o);o.setExpression('Visibility',f'Variantensteuerung.Variante == {vi} ? (Variantensteuerung.Propeller == {i} ? 1 : 0) : 0');modules.append(dict(instance=o.Name,propeller_index=i,variant=v['id'],corner_deg=angle,placement_mm=list(origin),placement_quaternion=list(rot.Q),parts=local));records.extend(dict(instance=o.Name+'_'+str(k),id=r['master'],label=r['part'],role=r['role'],propeller_index=i,variant=v['id'],mass_kg=r['mass_kg'],placement_mm=list(origin),placement_quaternion=list(rot.Q)) for k,r in enumerate(local))
  info.update(carrier_mass_each_kg=sum(r['mass_kg'] for r in local),ESC_identity_verified=True,ESC_model=catalog['model'],ESC_body_geometry_verified=False,ESC_catalog_mass_including_wires_kg=catalog['mass_including_wires_kg']);specs.append(info);print('D12 built',i,v['id'],round(info['carrier_mass_each_kg']*1000,1),'g',flush=True)
D.recompute();D.Label='Quad D12 – kombinierte Reglerhalter und CFK-Landefuesse; Nachweise offen';native=O/('Prototyp.FCStd' if os.environ.get('D12_PROTOTYPE') else 'Quad_Reglerhalter_Landefuesse.FCStd');D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest()
(O/'Reglerhalter_Instanzen.json').write_text(json.dumps(modules,indent=2));(O/'Viewer_Komponenten.json').write_text(json.dumps(records,indent=2));(O/'Regler_Montage.json').write_text(json.dumps(dict(native_sha256=sha,configurations=specs,production_ready=False,landing_strength_qualified=False,ESC_identity_verified=True,ESC_model=catalog['model'],ESC_identity_verification_basis='User confirmed drawing/model assignment',OEM_original_document_verified=False,ESC_catalog=catalog,ESC_catalog_mass_per_unit_including_wires_kg=.748,ESC_quad_catalog_mass_including_wires_kg=2.992,ESC_body_geometry_verified=False,ESC_orientation='Vertical;mount146 radial x66 hole height;OEM orientation unconfirmed',load_path='Sole -> pocketed Al base -> bonded lower inserts -> 2 axial CFK20/17 columns -> isolated upper inserts integral with32mm clamp shells -> lowest arm tube.ESC rails and housing carry no design landing force.',parameters=P),indent=2));print('D12 saved',sha,flush=True)
