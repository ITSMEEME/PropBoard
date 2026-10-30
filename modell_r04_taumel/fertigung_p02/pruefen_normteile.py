#!/usr/bin/env python3
import os,sys,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as A,Part,MeshPart
manifest=json.loads((H/'Quellen/Quellenmanifest.json').read_text());d=A.newDocument('P02_Normteile');rows=[]
for i,source in enumerate(manifest['assets']):
    p=H/'Quellen'/source['filename'];assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256'];s=Part.read(str(p));assert s.isValid() and len(s.Solids)==1
    b=s.BoundBox;mesh=MeshPart.meshFromShape(Shape=s.copy().cleaned(),LinearDeflection=.02,AngularDeflection=.1,Relative=False);vs,_=mesh.Topology
    rmax=max(math.hypot(v.x,v.y) for v in vs)
    if 'Mutter' in source['id']:
        assert abs(b.ZLength-2.4)<.002
        sides=[abs(f.Surface.Position.dot(f.Surface.Axis)) for f in s.Faces if isinstance(f.Surface,Part.Plane) and abs(f.Surface.Axis.z)<1e-8]
        assert len(sides)>=6 and max(abs(x-2.75) for x in sides)<1e-4,sides
        dims=dict(thread_nominal='M3',height_mm=b.ZLength,across_flats_mm=5.5,physical_max_radius_mm=rmax)
    else:
        L=int(source['id'].split('x')[-1]);head=[f.Surface.Radius for f in s.Faces if isinstance(f.Surface,Part.Cylinder) and f.Surface.Radius>2]
        assert head and max(abs(v-2.75) for v in head)<1e-5
        assert abs(b.ZMin+L)<.002 and abs(b.ZMax-3)<.002
        assert abs(rmax-2.75)<.01,rmax
        dims=dict(thread_nominal='M3',length_under_head_mm=L,head_height_mm=3,head_diameter_mm=5.5,physical_max_radius_mm=rmax)
    o=d.addObject('Part::Feature',source['id']);o.Shape=s;o.Placement.Base.x=i*15
    for name,value in [('Quelle',source['source_url']),('Quell_SHA256',source['sha256']),('Status','MASSGEPRUEFTE_NORMTEILREFERENZ_KEINE_LIEFERANTENFREIGABE')]:o.addProperty('App::PropertyString',name);setattr(o,name,value)
    rows.append(dict(id=source['id'],valid=True,solids=1,volume_mm3=s.Volume,source_sha256=source['sha256'],dimensions=dims,occt_conservative_bbox_mm=[b.XLength,b.YLength,b.ZLength]))
d.saveAs(str(H/'Ausgabe/P02_Normteilkatalog.FCStd'));A.closeDocument(d.Name)
d=A.openDocument(str(H/'Ausgabe/P02_Normteilkatalog.FCStd'));assert len([o for o in d.Objects if hasattr(o,'Shape') and o.Shape.isValid()])==4;A.closeDocument(d.Name)
(H/'Ausgabe/Normteilpruefung.json').write_text(json.dumps(dict(status='IMPORTED_STANDARD_INTERFACES_DIMENSIONALLY_CHECKED_NOT_COMPLETE_ASSEMBLY_APPROVAL',assets=rows,native_reopen_pass=True,notes='STEP bounding boxes are conservative on some trimmed chamfer surfaces; head diameter was checked on cylindrical surfaces and refined mesh. Threads are nominal, not verified 3D flanks.'),indent=2));print('PASS four imported standard-part solids and dimensions; native reopen')
