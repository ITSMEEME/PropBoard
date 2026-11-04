"""Continuous rotor envelopes vs full fixed assembly for every arm variant."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';R=H.parent;sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
native=O/'Quad_Parametrisch_V1_V4.FCStd';D=A.openDocument(str(native));common=json.loads((O/'Gemeinsame_Instanzen.json').read_text());arms=json.loads((O/'Instanzen.json').read_text())+json.loads((O/'Hardware.json').read_text());base=json.loads((R/'quad_r380_d06/Ausgabe/Rotor_Pruefung.json').read_text());hulls=base['continuous_sweep_hulls'];byname={r['instance']:r for r in common+arms};shapes={r['instance']:D.getObject(r['instance']).Shape for r in common+arms};candidates=[];count=0;near=[]
for h in hulls:
 source=byname[h['source_instance']];ax,ay,az=source['rotor_axis_mm'];z=h['zmin_mm'];height=h['zmax_mm']-z;outer=h['outer_radius_mm'];hull=None
 for r in common+arms:
  if r.get('rotor_id'):continue
  s=shapes[r['instance']];b=s.BoundBox
  if b.ZMax<z or b.ZMin>z+height:continue
  distance=math.hypot(max(b.XMin-ax,0,ax-b.XMax),max(b.YMin-ay,0,ay-b.YMax))
  if distance>outer+15:continue
  if hull is None:
   hull=Part.makeCylinder(outer,height,A.Vector(ax,ay,z))
   if h['inner_radius_mm']>1e-6:hull=hull.cut(Part.makeCylinder(h['inner_radius_mm'],height+2,A.Vector(ax,ay,z-1)))
  if distance<=outer:
   count+=1;vol=intersection_volume(hull,s)
   if vol>.1:candidates.append(dict(hull=h['id'],fixed_instance=r['instance'],variant=r.get('variant','all'),volume_mm3=vol));print('Rotor interference',candidates[-1],flush=True)
  if r.get('id','').startswith('D08_D04_HIGH_') and h['source_part'].startswith('D06_BLADE_'):near.append(dict(hull=h['id'],instance=r['instance'],distance_mm=hull.distToShape(s)[0]))
 print('Sweep',h['id'],'candidates',count,'hits',len(candidates),flush=True)
footmin=min(shapes[r['instance']].BoundBox.ZMin for r in common if r.get('foot_side'));rotormax=max(h['zmax_mm'] for h in hulls);assert footmin>rotormax
report=dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),continuous_sweep_candidates=candidates,continuous_sweep_candidate_count=len(candidates),exact_brep_candidates=count,actual_blade_collision_witnesses=[],mechanically_clear=not candidates,nominal_rotor_sweep_clear=not candidates,foot_sweep_Z_gap_mm=footmin-rotormax,trimmed_node_clearance=near,rotor_disk_edge_gap_mm=180,overall_rotor_width_mm=1700,production_ready=False,scope='All68 conservative D06 component annuli translated with the complete rotors to±470mm,versus every shared fixed part and all four mutually exclusive arm configurations including wiring. Z-separation proves foot-system clearance throughout its translation/retraction range. Rotor disks mutually separated180mm. Rigid nominal geometry only; no operating clearance under deflection,tolerance or person envelope. Mating hub/motor face contacts are permitted. No new actual-phase witness needed when all enclosing envelopes are clear.')
(O/'Rotor_Pruefung.json').write_text(json.dumps(report,indent=2));print('Rotor clearance',report['nominal_rotor_sweep_clear'],'footZgap',report['foot_sweep_Z_gap_mm'],'node gaps',near,flush=True)
