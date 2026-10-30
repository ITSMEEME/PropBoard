#!/usr/bin/env python3
"""Offline WebGL viewer of actual native P09 meshes and closed FreeCAD transforms."""
import sys,os,json,math,base64,struct,hashlib,array
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')),str(H)]
import FreeCAD as A
import voll_runtime as R
src=H/'Ausgabe/P09_Servo_bis_Rotorblatt_Bewegung.FCStd';d=A.openDocument(str(src))
parts=[o for o in d.Objects if hasattr(o,'P09_Rahmen') and not o.BauteilID.startswith('KEEP_')]
static_cases={}
for o in parts:
    if o.BauteilID=='SERVO-SAVOX-SB2270SGP':
        l,j=int(o.Rotor),int(o.MotionIndex)
        static_cases[f'case:{l}:{j}']=R.M.local_world(1 if l==0 else -1).multiply(R.M.placement(rotation=R.M.rotz((60,180,300)[j])))
keys=sorted(set(o.P09_Rahmen for o in parts)|set(static_cases));refs={o.P09_Rahmen:o.P09_Neutralrahmen for o in parts};blob=bytearray();meta=[];first=0;mesh_cache={}
for o in parts:
    is_case=o.BauteilID=='SERVO-SAVOX-SB2270SGP'
    renderkey=f'case:{int(o.Rotor)}:{int(o.MotionIndex)}' if is_case else o.P09_Rahmen
    shape=o.Shape.copy()
    if is_case:shape.Placement=static_cases[renderkey].inverse().multiply(shape.Placement)
    elif renderkey!='fixed':shape.Placement=o.P09_Neutralrahmen.inverse().multiply(shape.Placement)
    # Repeated authored components share preview mesh buffers only after a
    # canonical-coordinate topology/integral/vertex signature agrees.
    cachekey=None
    if renderkey!='fixed':
        vertices=tuple(sorted((round(v.Point.x,3),round(v.Point.y,3),round(v.Point.z,3)) for v in shape.Vertexes))
        cachekey=(o.BauteilID,len(shape.Faces),len(shape.Edges),round(shape.Volume,3),round(shape.Area,3),vertices)
    if cachekey is not None and cachekey in mesh_cache:
        start,count=mesh_cache[cachekey]
    else:
        vs,fs=shape.tessellate(.35);start=first
        for f in fs:
            p,q,r=[vs[i] for i in f];normal=(q-p).cross(r-p)
            if normal.Length<1e-12:continue
            normal.normalize();ns=[max(-127,min(127,round(v*127))) for v in (normal.x,normal.y,normal.z)]
            for point in (p,q,r):blob.extend(struct.pack('<hhhbbbx',*[round(v*100) for v in (point.x,point.y,point.z)],*ns));first+=1
        count=first-start
        if cachekey is not None:mesh_cache[cachekey]=(start,count)
    ident=o.BauteilID;role=o.P09_Rahmen
    color=[.63,.68,.73]
    if ident=='TM-FLUEGEL':color=[.20,.65,.78] if o.Rotor==0 else [.85,.48,.25]
    elif 'cap' in ident or 'Haltekappe' in ident:color=[.77,.59,.28]
    elif role.startswith('link:') or role.startswith('p08:'):color=[.30,.65,.64] if 'body' in ident or 'horn' in ident else [.70,.73,.77]
    elif role.startswith('output:'):color=[.89,.65,.28]
    meta.append(dict(name=o.Name,first=start,count=count,key=keys.index(renderkey),color=color,cover=ident in ('TM-NABE','TM-DECKEL-ZAHNKRANZ-130','SERVO-SAVOX-SB2270SGP')))
    if len(meta)%50==0:print('Meshes',len(meta),'of',len(parts),flush=True)
frames=array.array('f');max_error=0
for i in range(161):
    servos,angles=R.demo(0 if i==160 else i*.05);state=R.state(servos,angles);max_error=max(max_error,state['max_error'])
    for key in keys:
        matrix=(A.Placement() if key=='fixed' else static_cases[key] if key in static_cases else state['frames'][key]).toMatrix().A
        frames.extend(matrix[r*4+c] for c in range(4) for r in range(4))
assert max_error<1e-6
payload=dict(parts=meta,keys=len(keys),mesh=base64.b64encode(blob).decode(),transforms=base64.b64encode(frames.tobytes()).decode())
page=(H/'browser_vorlage.html').read_text().replace('/*__DATA__*/','const P09_DATA='+json.dumps(payload,separators=(',',':'))+';')
out=H/'Ausgabe/P09_Durchgaengige_Animation.html';out.write_text(page)
report=dict(source_native_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),html_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),mesh_parts=len(parts),unique_mesh_triangles=first//3,rendered_triangles=sum(p['count'] for p in meta)//3,shared_servo_case_mesh=True,frames=161,max_closure_error_mm=max_error,render_position_quantization_mm=.01,tessellation_deflection_mm=.35,geometry_source='Actual native FreeCAD shapes, including known invalid servo case reference',browser_test_status='PENDING')
(H/'Ausgabe/Browserexport_P09.json').write_text(json.dumps(report,indent=2)+'\n');A.closeDocument(d.Name);print(json.dumps(report,indent=2))
