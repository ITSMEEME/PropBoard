#!/usr/bin/env python3
"""Reject unusable CFD meshes before spending solver time. No acceptance by solver exit code alone."""
import json,re,sys,struct
from pathlib import Path
def check(case):
    mesh=(case/'log.checkMesh').read_text();snap=(case/'log.snappyHexMesh').read_text()
    ex=re.findall(r'Extruding\s+\d+\s+out of\s+\d+\s+faces\s+\(([\d.]+)%\)',snap)
    coverage=float(ex[-1]) if ex else 0
    checks={'basic_topology_geometry':'Mesh OK.' in mesh,'layer_coverage_at_least_70_percent':coverage>=70}
    meta=json.loads((case/'case.json').read_text());solid=0
    for patch in ['wingUpper','wingLower']:
        raw=(case/f'constant/triSurface/{patch}.stl').read_bytes()
        for v in struct.iter_unpack('<12fH',raw[84:]):
            a,b,c=v[3:6],v[6:9],v[9:12]
            solid+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    found=re.search(r'Total volume = ([\deE+.\-]+)',mesh)
    captured=(2*meta['domain_half_width_m'])**3-float(found[1].rstrip('.')) if found else None
    volume_error=abs(captured/solid-1) if captured is not None and solid>0 else None
    checks['solid_volume_capture_within_5_percent']=volume_error is not None and volume_error<.05
    for name in ['Upper','Lower']:
        surface=(case/f'log.surface{name}').read_text();checks[f'closed_surface_{name}']='Surface is closed.' in surface and 'Surface has no illegal triangles.' in surface
    report={'status':'PASS' if all(checks.values()) else 'FAIL_MESH','layer_face_coverage_percent':coverage,'input_solid_volume_m3':solid,'captured_solid_volume_m3':captured,'relative_solid_volume_error':volume_error,'checks':checks,'limitations':['Extended allGeometry concave-cell diagnostics retained separately','Layer coverage is face count, not proof of wall-y+ or grid independence']}
    (case/'Netzcheck.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    r=check(Path(sys.argv[1]));print(json.dumps(r,indent=2));raise SystemExit(0 if r['status']=='PASS' else 1)
