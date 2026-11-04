"""Complete the saved ongoing D13 build with collision-corrected open yokes and photo props."""
from pathlib import Path
import sys,json,hashlib,runpy
H=Path(__file__).resolve().parents[1];R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod']);sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(0,str(R/'quad_r380_d07'));sys.path.insert(0,str(H))
import FreeCAD as A,Part,PartDesign
from zipcad import Native
from geometrie import trim_core,placed
from knoten import make_nodes
from planung import axis_geometry
from propeller_einbauen import install
native=O/'Quad_Flachrippen_Mensch.FCStd';print('Restore saved frame',flush=True);D=A.openDocument(str(native));meta=json.loads((O/'Flachrippen_Aufbau.json').read_text());meta.setdefault('initial_flat_yoke_native_sha256',meta['native_sha256']);vs=json.loads((R/'quad_r380_d10/Varianten.json').read_text());cs=json.loads((R/'quad_r380_d10/Konfigurationen.json').read_text());p=json.loads((R/'quad_r380_d07/parameter.json').read_text());n=Native(R/'quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd');core=placed(trim_core(n.shape('D07_ROOT_TOP')),(-65,0,22),A.Rotation(A.Vector(0,0,1),90));cache=H/'Cache/OffeneBruecke';cache.mkdir(parents=True,exist_ok=True)
for v in vs:
 sig=hashlib.sha256((Path(__file__).parent/'knoten.py').read_bytes()+json.dumps([v,p],sort_keys=True).encode()).hexdigest();f=cache/(sig+'.brep')
 if f.exists():s=Part.Shape();s.read(str(f))
 else:a,b=axis_geometry(v,cs[-1]);s,_=make_nodes(v,cs[-1],a,b,core,p);s.exportBrep(str(f))
 assert s.isValid() and len(s.Solids)==1;vol=s.Volume;name=next(r['master'] for r in meta['changes'] if r['variant']==v['id'] and r['part']=='Root');D.getObject(name).Shape=s
 for r in meta['changes']:
  if r['master']==name:r.update(mass_new_per_corner_kg=vol*2810e-9,volume_mm3=vol)
 print('Corrected root',v['id'],round(vol*.00281,1),'g',flush=True)
photo=install(D,H);ctl=D.getObject('Variantensteuerung');ctl.Hinweis='D13:Offene integrierte Rahmenbrücke,flache Motorknoten,1.75m Person,2Blatt-Bildreferenz je HEP-S-Größe.Antrieb Schätzung;OEM-Nabe,Profil undFestigkeitsfreigabe offen.';D.Label='Quad D13 – offene Knoten, Mensch und Bildpropeller';D.recompute();D.saveAs(str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();meta['native_sha256']=sha;meta['root_revision']='open_bridge_outside_vertical_frame_clamp';(O/'Flachrippen_Aufbau.json').write_text(json.dumps(meta,indent=2));photo['native_sha256']=sha;(O/'Propeller_Aufbau.json').write_text(json.dumps(photo,indent=2));print('Final native saved',sha,flush=True)
runpy.run_path(str(Path(__file__).parent/'fast_pruefen.py'))
runpy.run_path(str(Path(__file__).parent/'propeller_pruefen.py'))
runpy.run_path(str(Path(__file__).parent/'viewer_export.py'),init_globals={'BUILD_DOC':D})
