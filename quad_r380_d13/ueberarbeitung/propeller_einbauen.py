from pathlib import Path
import math,json,hashlib
import FreeCAD as A,Part
from propeller import shape

def install(D,H):
 O=H/'Ausgabe';R=H.parent;cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());lib=D.getObject('Bauteilbibliothek');asm=D.getObject('Montage');ctl=D.getObject('Variantensteuerung');rows=[];configs=[]
 for prop,val in [('BildpropellerAnzeigen',True),('RotorhuelleAnzeigen',False)]:
  if not hasattr(ctl,prop):ctl.addProperty('App::PropertyBool',prop,'Ansicht')
  setattr(ctl,prop,val)
 cache=H/'Cache/Bildpropeller';cache.mkdir(parents=True,exist_ok=True);steps=O/'Propeller_STEP';steps.mkdir(exist_ok=True)
 for i,c in enumerate(cs):
  key=hashlib.sha256((Path(__file__).parent/'propeller.py').read_bytes()+json.dumps(c,sort_keys=True).encode()).hexdigest();f=cache/(key+'.brep');j=cache/(key+'.json')
  if f.exists() and j.exists():
   cc=Part.Shape();cc.read(str(f));cw=cc.mirror(A.Vector(),A.Vector(0,1,0));stations=json.loads(j.read_text())
  else:cc,cw,stations=shape(c);cc.exportBrep(str(f));j.write_text(json.dumps(stations))
  for hand,s in [('CCW',cc),('CW',cw)]:
   name=f'PHOTO_P{i}_{hand}';m=D.getObject(name) or D.addObject('Part::Feature',name);m.Shape=s;m.Label=c['label']+' '+hand+' – Bildreferenz';lib.addObject(m);m.Visibility=False;s.exportStep(str(steps/(c['id']+'_'+hand+'.step')))
  for angle in [45,135,225,315]:
   rad=math.radians(angle);h=c['motor_half_spacing_mm'];xy=[math.copysign(h,math.cos(rad)),math.copysign(h,math.sin(rad))];hand='CW' if angle in [45,225] else 'CCW';m=D.getObject(f'PHOTO_P{i}_{hand}');name=f'PHOTO_P{i}_Einbau_{angle}';o=D.getObject(name) or D.addObject('App::Link',name);o.setLink(m);pl=A.Placement(A.Vector(*xy,0),A.Rotation(A.Vector(0,0,1),angle));o.LinkPlacement=pl;asm.addObject(o);o.setExpression('Visibility',f'Variantensteuerung.BildpropellerAnzeigen == 1 ? (Variantensteuerung.Propeller == {i} ? 1 : 0) : 0')
   rows.append(dict(instance=name,id=m.Name,label=c['label']+' '+hand+' (Bildreferenz)',group='Bildpropeller',role='photo_propeller',propeller_index=i,rotor_id=f'Foto_{angle}',rotor_hand=hand,rotor_axis_mm=[*xy,154],mass_kg=0,placement_mm=list(pl.Base),placement_quaternion=list(pl.Rotation.Q),reference_only=True))
  zmin=cc.BoundBox.ZMin;zmax=cc.BoundBox.ZMax;ring=D.getObject(f'P{i}_Rotorhuelle');ring.Shape=Part.Compound([Part.makeTorus(c['radius_mm'],.7,A.Vector(0,0,z)) for z in [zmin,(zmin+zmax)/2,zmax]])
  for o in asm.Group:
   if o.TypeId=='App::Link' and o.LinkedObject==ring:o.setExpression('Visibility',f'Variantensteuerung.RotorhuelleAnzeigen == 1 ? (Variantensteuerung.Propeller == {i} ? 1 : 0) : 0')
  configs.append(dict(propeller_index=i,label=c['label'],diameter_mm=c['diameter_mm'],pitch_mm=c['pitch_mm'],R_mm=c['radius_mm'],native_BB_z_min_mm=zmin,native_BB_z_max_mm=zmax,hub_bottom_z_mm=154,hub_thickness_mm=9,hub_half_length_mm=70,hub_half_width_mm=22,hub_centre_bore_mm=15,hub_assumed_bolt_PCD_mm=30,hub_assumed_clearance_mm=5.5,hub_bolt_count=4,hub_dimensions_verified=False,stations=stations));print('Photo propeller',i,c['label'],'z',round(zmin,2),round(zmax,2),flush=True)
 return dict(instances=rows,configurations=configs,photo_based=True,OEM_CAD=False,OEM_airfoil=False,blade_count=2,hub_fixed_across_sizes=True,profile_assumption='NACA-like camber2.5percent,18to8percent thickness;not identified from photograph',handedness_convention='viewed from above,CW negative angular velocity;CCW mirror keeps positive camber',performance_validated=False,production_ready=False)
