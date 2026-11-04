import sys,json,math
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(Path(__file__).resolve().parents[1]/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import intersection_volume
R=Path(__file__).resolve().parents[1];D=A.openDocument(str(R/'quad_r380_varianten/Ausgabe/Quad_Parametrisch_V1_V4.FCStd'));rows=json.loads((R/'quad_r380_varianten/Ausgabe/Gemeinsame_Instanzen.json').read_text());hulls=json.loads((R/'quad_r380_d06/Ausgabe/Rotor_Pruefung.json').read_text())['continuous_sweep_hulls'];fixed=[r for r in rows if not r.get('rotor_id') and not r['instance'].startswith('D05_')];shapes={r['instance']:D.getObject(r['instance']).Shape for r in fixed};results=[]
for half in [450,460,470]:
 hits=[];candidates=0
 for h in hulls:
  source=next(r for r in rows if r['instance']==h['source_instance']);ax,ay,_=source['rotor_axis_mm'];x=math.copysign(half,ax);y=math.copysign(half,ay);outer=h['outer_radius_mm'];z=h['zmin_mm'];height=h['zmax_mm']-z;hull=None
  for r in fixed:
   s=shapes[r['instance']];b=s.BoundBox
   if b.ZMax<z or b.ZMin>z+height:continue
   dist=math.hypot(max(b.XMin-x,0,x-b.XMax),max(b.YMin-y,0,y-b.YMax))
   if dist>outer:continue
   if hull is None:
    hull=Part.makeCylinder(outer,height,A.Vector(x,y,z))
    if h['inner_radius_mm']>1e-6:hull=hull.cut(Part.makeCylinder(h['inner_radius_mm'],height+2,A.Vector(x,y,z-1)))
   candidates+=1;vol=intersection_volume(hull,s)
   if vol>.1:hits.append(dict(hull=h['id'],instance=r['instance'],volume=vol))
 result=dict(half_spacing_mm=half,overall_rotor_width_mm=2*(half+380),candidates=candidates,hits=hits);results.append(result);print(result,flush=True)
(R/'quad_r380_d08/Ausgabe/Freiraum_Suche.json').write_text(json.dumps(results,indent=2))
