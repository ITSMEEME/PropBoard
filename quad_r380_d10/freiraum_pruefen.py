"""Native continuous rotor-space clearance for every diameter and arm configuration."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
V=A.Vector;native=O/'Quad_HEPS_Innenverkabelung.FCStd';D=A.openDocument(str(native));configs=json.loads((H/'Konfigurationen.json').read_text());read=lambda n:json.loads((O/n).read_text());common=read('Gemeinsame_Instanzen.json');sized=read('Groessen_Instanzen.json');arms=read('Instanzen.json')+read('Hardware.json');cables=read('Kabel_Instanzen.json');objects={r['instance']:D.getObject(r['instance']) for r in common+sized+arms+cables};bounds={n:o.Shape.BoundBox for n,o in objects.items()};results=[];cache={}
for pidx,cfg in enumerate(configs):
 hits=[];candidates=0;half=cfg['motor_half_spacing_mm'];radius=cfg['radius_mm'];active=common+[r for r in sized+arms+cables if r['propeller_index']==pidx and r.get('group')!='Rotorhuelle'];gap=2*half-2*radius
 for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
  centre=V(sx*half,sy*half,124);hull=None
  for r in active:
   b=bounds[r['instance']]
   if b.ZMax<124 or b.ZMin>184:continue
   nearest=math.hypot(max(b.XMin-centre.x,0,centre.x-b.XMax),max(b.YMin-centre.y,0,centre.y-b.YMax))
   if nearest>radius:continue
   obj=objects[r['instance']];pl=obj.LinkPlacement;relative=pl.Base-centre;key=(obj.LinkedObject.Name,tuple(round(x,5) for x in relative),tuple(round(x,6) for x in pl.Rotation.Q),radius)
   if key not in cache:
    if hull is None:hull=Part.makeCylinder(radius,60,centre).cut(Part.makeCylinder(80,62,centre-V(0,0,1)))
    cache[key]=intersection_volume(hull,obj.Shape)
   candidates+=1;volume=cache[key]
   if volume>.1:hits.append(dict(instance=r['instance'],variant=r.get('variant','all'),rotor_signs=[sx,sy],volume_mm3=volume));print('HULL CONFLICT',cfg['label'],hits[-1],flush=True)
 footmin=min(bounds[r['instance']].ZMin for r in common if r.get('foot_side'));assert gap>=20-1e-6 and footmin>184
 results.append(dict(propeller_index=pidx,propeller=cfg['label'],nominal_rotor_space_clear=not hits,findings=hits,candidates=candidates,rotor_edge_gap_mm=gap,foot_translation_Z_gap_mm=footmin-184,arm_variants_checked=['V1','V2','V3','V4','V5'],unprotected_width_mm=cfg['unprotected_width_mm']));print('Sweep',cfg['label'],'clear',not hits,'candidates',candidates,flush=True)
(O/'Freiraum_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),configurations=results,all_nominal_rotor_spaces_clear=all(r['nominal_rotor_space_clear'] for r in results),envelope=dict(inner_radius_mm=80,zmin_mm=124,zmax_mm=184,outer_radius='selected diameter/2'),scope='Continuous annular planning envelope vs actual fixed CAD,each size and all four alternative arms including cable routes. All combinations are checked; actual HEP-S inner root/hub contours and vertical blade envelope are unknown. Rotor marks are visual bounds,not physical blades. Foot sweep uses invariant Z-separation throughout permitted translation/retraction.20mm nominal frame/neighbor planning reserve is not a deflection guarantee. No flight/production release.',loaded_clearance_guaranteed=False,OEM_envelope_verified=False),indent=2,ensure_ascii=False));print('Rotor space report saved',flush=True)
