"""Exact axisymmetric BREP enclosures contain every phase of each photo propeller.
Inner radius75mm seats at154mm; outer annulus uses the native conservative z box.
"""
from pathlib import Path
import sys,json,math,hashlib
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib']);sys.path.insert(0,str(R/'quad_r380_d07'))
import FreeCAD as A,Part
from zipcad import Native
from geometrie import intersection_volume
stamp={name:hashlib.sha256((H/name).read_bytes()).hexdigest() for name in ['Ausgabe/Quad_Flachrippen_Mensch.FCStd','Ausgabe/Propeller_Aufbau.json','ueberarbeitung/zipcad.py','ueberarbeitung/propeller_pruefen.py']}
f=O/'Propeller_Pruefung.json';previous=json.loads(f.read_text()) if f.exists() else {}
if previous.get('nominal_geometry_passed') and previous.get('verification_stamp')==stamp:print('Reuse matching native propeller enclosure verification',flush=True)
else:
 V=A.Vector;n=Native(O/'Quad_Flachrippen_Mensch.FCStd');photo=json.loads((O/'Propeller_Aufbau.json').read_text());meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());data=json.loads((O/'projekt.js').read_text()[len('globalThis.QD_MODEL='):].strip().rstrip(';'));rows=data['instances'];del data;rows=[r for r in rows if r.get('group') not in ['Mensch','Bildpropeller','Rotorhuelle']]+meta['human'];shapes={};boxes={};cache={};configs=[];checks=[];hits=[]
 for c in photo['configurations']:
  i=c['propeller_index'];R0=c['R_mm'];s=n.shape(f'PHOTO_P{i}_CCW');assert s.isValid() and len(s.Solids)==1
  zmin=s.BoundBox.ZMin;zmax=s.BoundBox.ZMax;outer=Part.makeCylinder(R0,zmax-zmin,V(0,0,zmin)).cut(Part.makeCylinder(75,zmax-zmin+2,V(0,0,zmin-1)));inner=Part.makeCylinder(75,zmax-154,V(0,0,154));env=outer.fuse(inner);escaped=s.cut(env).Volume;assert escaped<.1,(i,'not contained in all-phase envelope',escaped)
  assert s.cut(Part.makeCylinder(R0+.001,200,V(0,0,80))).Volume<.1
  assert any(isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-R0)<1e-5 for f in s.Faces),('tip must meet specified radius',i)
  for r,rad in [(0,7.49)]+[(d,2.74) for d in [45,135,225,315]]:
   x=0 if r==0 else 15*math.cos(math.radians(r));y=0 if r==0 else 15*math.sin(math.radians(r));assert intersection_volume(s,Part.makeCylinder(rad,14,V(x,y,152)))<.1
  for vi in ['V1','V2','V3','V4','V5']:
   active=[r for r in rows if ('propeller_index' not in r or r['propeller_index']==i) and ('variant' not in r or r['variant']==vi)]
   for p in photo['instances']:
    if p['propeller_index']!=i:continue
    pl=n.placement(p['instance']);assert n.linked(p['instance'])==p['id'];expressions=' '.join(x.get('expression','') for x in n.expressions(p['instance']));assert f'Variantensteuerung.Propeller == {i}' in expressions
    for label,e,rmin,zlo in [('inner',inner,0,154),('outer',outer,75,zmin)]:
     E=e.copy();E.Placement=pl.multiply(E.Placement);cx=pl.Base.x;cy=pl.Base.y
     for r in active:
      key=r['instance']
      if key not in shapes:shapes[key]=n.row(r)
      t=shapes[key]
      if key not in boxes:boxes[key]=t.BoundBox
      bb=boxes[key]
      if bb.ZMax<=zlo+1e-7 or bb.ZMin>=zmax-1e-7:continue
      dx=max(bb.XMin-cx,0,cx-bb.XMax);dy=max(bb.YMin-cy,0,cy-bb.YMax)
      if math.hypot(dx,dy)>=R0-1e-7:continue
      far=math.hypot(max(abs(bb.XMin-cx),abs(bb.XMax-cx)),max(abs(bb.YMin-cy),abs(bb.YMax-cy)))
      if label=='outer' and far<=75+1e-7:continue
      k=(i,p['instance'],label,r['id'],tuple(round(x,5) for x in r['placement_mm']),tuple(round(x,5) for x in r['placement_quaternion']))
      if k not in cache:cache[k]=intersection_volume(E,t)
      vol=cache[k]
      if vol>.1:hits.append(dict(propeller_index=i,variant=vi,rotor=p['instance'],envelope=label,other=r['instance'],volume_mm3=vol));print('SWEEP HIT',hits[-1],flush=True)
   checks.append(dict(propeller_index=i,variant=vi,rotor_count=4,all_phase_envelopes_checked=True,passed=not any(h['propeller_index']==i and h['variant']==vi for h in hits)))
  # Pairwise rotor-circle separation is independent of blade angular phase.
  ps=[p for p in photo['instances'] if p['propeller_index']==i];gap=min(math.dist(p['placement_mm'][:2],q['placement_mm'][:2])-2*R0 for j,p in enumerate(ps) for q in ps[j+1:]);assert gap>0
  configs.append(dict(propeller_index=i,nominal_diameter_mm=2*R0,tip_reaches_native_cylinder_radius=True,conservative_native_z_min_mm=zmin,conservative_native_z_max_mm=zmax,enclosure_outside_volume_mm3=escaped,minimum_rotor_circle_gap_mm=gap,all_phase_clear=all(x['passed'] for x in checks if x['propeller_index']==i)));print('Photo propeller sweep',i,'clear',configs[-1]['all_phase_clear'],flush=True)
 report=dict(native_sha256=hashlib.sha256((O/'Quad_Flachrippen_Mensch.FCStd').read_bytes()).hexdigest(),configurations=configs,checks=checks,interferences=hits,nominal_geometry_passed=not hits,scope='Saved native BREP;photo blade solid contained by a rotation-invariant inner cylinder(radius75,z154up) and outer annulus(radius75toR,native bounding zrange);enclosures vs native vehicle/scale-human geometry at all4axes in all50 configurations.Rotor circles checked pairwise.Geometry is a photo-derived assumption;no blade deflection,OEM contour/PCD,manufacturing tolerance or structural clearance certification.',production_ready=False,verification_stamp=stamp)
 (O/'Propeller_Pruefung.json').write_text(json.dumps(report,indent=2));assert not hits,hits;print('All50 photo-rotor all-phase envelopes clear',flush=True)
