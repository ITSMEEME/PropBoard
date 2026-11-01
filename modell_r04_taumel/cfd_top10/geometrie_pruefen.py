#!/usr/bin/env python3
"""Independent manifold / orientation / source checks on the actual CFD surface files."""
import collections,hashlib,json,math,struct
from pathlib import Path
import numpy as np
from erstellen import H,SOURCE
source=json.loads(SOURCE.read_text());sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rows=[]
dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
for rank in range(1,11):
    case=H/'cases'/f'K{rank:02d}_coarse';m=json.loads((case/'case.json').read_text());assert m['source_search_sha256']==sha;assert m['design']==source['top10Aerodynamic'][rank-1]['design'];d=m['design']
    for patch,sign in [('wingUpper',1),('wingLower',-1)]:
        raw=(case/f'constant/triSurface/{patch}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0];assert len(raw)==84+50*n
        a=np.frombuffer(raw,dtype=dtype,offset=84);v=a['v'].astype(float);edges=collections.defaultdict(list)
        for i,t in enumerate(v):
            points=[tuple(q) for q in t]
            for j in range(3):
                x,y=points[j],points[(j+1)%3];key=tuple(sorted([x,y]));edges[key].append((i,1 if x<y else -1))
        assert all(len(e)==2 and e[0][1]+e[1][1]==0 for e in edges.values()),(rank,patch,'open / inconsistent surface')
        neighbors=[[] for _ in range(n)]
        for e in edges.values():i,j=e[0][0],e[1][0];neighbors[i].append(j);neighbors[j].append(i)
        unseen=set(range(n));components=0
        while unseen:
            stack=[unseen.pop()];components+=1
            while stack:
                for i in neighbors[stack.pop()]:
                    if i in unseen:unseen.remove(i);stack.append(i)
        assert components==d['blades'];assert np.max(np.abs(np.linalg.norm(a['normal'],axis=1)-1))<2e-6
        volume=float(np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2])).sum()/6);assert volume>0
        radius=np.linalg.norm(v[:,:,:2],axis=2);assert radius.max()<1.08*d['diameterMm']/2000
        zc=sign*d['spacingMm']/2000;assert np.max(abs(v[:,:,2]-zc))<min(.04,abs(zc)*.7)
        rows.append({'rank':rank,'patch':patch,'triangles':n,'closed_components':components,'oriented_volume_m3':volume,'stl_sha256':hashlib.sha256(raw).hexdigest()})
report={'status':'PASS','source_search_sha256':sha,'native_sha256':source['native_sha256'],'surfaces':rows,'checks':['exact source parameters','closed oriented manifold edges','blade component count','unit normals','positive oriented volume','fully inside intended rotating zone'],'limitations':['Surface checks do not certify CFD convergence or manufacturing geometry']}
out=H/'Ausgabe';out.mkdir(exist_ok=True);(out/'Geometriepruefung.json').write_text(json.dumps(report,indent=2)+'\n');(out/'CFD_Eingaben.json').write_bytes(SOURCE.read_bytes());print('PASS: all 20 rotor surface files, correct source and MRF containment')
