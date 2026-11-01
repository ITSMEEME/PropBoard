"""Rebuild all supported blade-count variants and derive true CAD mass tensors.

No empirical mass scaling with blade count. Multiple pods are subsequently
assembled with the parallel-axis theorem; their connection structure is open.
"""
import json,copy,hashlib,argparse
from geometrie import *
import MeshPart
O=H/'Ausgabe'
def mass_of(p,c):
    if p['mass_override_kg'] is not None:return p['mass_override_kg']
    mat=p['material'];rho=(2810 if '7075' in mat else 2700) if 'Aluminium' in mat else (c['operating']['cfk_density_assumed_kg_m3'] if mat=='CFK' else 2200 if mat=='PTFE' else 7850)
    return p['shape'].Volume*rho*1e-9
def case(c):
    p,scene,q=build(c);pieces=[];rotor=[0.,0.];valid=True;render=[]
    for sign in [1,-1]:
        for row in scene:
            if sign<0 and row['frame']=='shared':continue
            id=row['id'];s=row['shape'].copy()
            if sign>0 and id=='A13':
                id='A13U';s=p[id]['shape'].copy();s.rotate(V(),V(1,0,0),row['theta']);s.rotate(V(),V(0,0,1),row['a']);s.translate(V(0,0,row['z']))
            if sign>0 and id in {'A16A','CFK01','F6_ROOT'}:
                s.rotate(V(0,0,q['level_mm']),V(math.cos(row['a']*D),math.sin(row['a']*D),0),-24)
            rel=s.Placement.multiply(p[id]['shape'].Placement.inverse()).toMatrix()
            transform=[getattr(rel,'A'+str(i)+str(j)) for i in range(1,5) for j in range(1,5)]
            render.append({k:v for k,v in row.items() if k!='shape'}|dict(part=id,sign=sign,neutral_transform=transform))
            if sign<0:s.rotate(V(),V(0,1,0),180)
            solid=s.Solids[0];m=mass_of(p[id],c);cg=[v*1e-3 for v in solid.CenterOfMass];J=solid.MatrixOfInertia
            j=[[getattr(J,'A'+str(i+1)+str(k+1))*m/s.Volume*1e-6 for k in range(3)] for i in range(3)]
            pieces.append((m,cg,j));valid=valid and s.isValid() and len(s.Solids)==1
            fraction=1. if row['frame'] in ['rotor','pitch','pitch_link','swash_rotor'] else .5 if id in ['MN1330','B7212'] else 0
            if id=='B61832':fraction=.5
            rotor[0 if sign>0 else 1]+=fraction*(j[2][2]+m*(cg[0]**2+cg[1]**2))
    total=sum(m for m,_,_ in pieces);cg=[sum(m*r[i] for m,r,_ in pieces)/total for i in range(3)]
    inertia=[[0.]*3 for _ in range(3)]
    for m,r,j in pieces:
        v=[r[i]-cg[i] for i in range(3)];rr=sum(x*x for x in v)
        for i in range(3):
            for k in range(3):inertia[i][k]+=j[i][k]+m*((rr if i==k else 0)-v[i]*v[k])
    meshes={}
    for id,t in p.items():
        mm=MeshPart.meshFromShape(Shape=t['shape'],LinearDeflection=.65,AngularDeflection=.35,Relative=False);vv,ff=mm.Topology
        meshes[id]=dict(vertices_mm=[[v.x,v.y,v.z] for v in vv],triangles=ff)
    variant=dict(meshes=meshes,scene=render,derived=q,types={id:{k:v for k,v in t.items() if k not in ['shape','mass_override_kg']} for id,t in p.items()},production_ready=False,geometry_source_sha256=source_hash())
    n=c['geometry']['blades_per_rotor'];(O/f'variante_{n}.js').write_text('globalThis.P14_VARIANTS=globalThis.P14_VARIANTS||{};globalThis.P14_VARIANTS['+str(n)+']='+json.dumps(variant,separators=(',',':'),ensure_ascii=False)+';\n')
    return dict(mass_kg=total,cg_m=cg,inertia_cg_kgm2=inertia,rotor_relative_inertia_kgm2=rotor,body_count=len(pieces),all_valid=valid,derived=q)
def main():
    global O
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=H/'parameter.json');ap.add_argument('--output',type=Path,default=H/'Ausgabe');args=ap.parse_args();O=args.output;O.mkdir(parents=True,exist_ok=True)
    c=json.loads(args.config.read_text());initial_hash=source_hash();out=dict(reference_config=c,geometry_source_sha256=initial_hash,scope='CAD dry structure; density/bought masses assumed. Original motor rotating fraction and main/swash inner races assumed 50%. No multi-unit connection frame.',cases={})
    for n in [4,6,8,10,12]:
        v=copy.deepcopy(c);v['geometry']['blades_per_rotor']=n;v['geometry']['lift_units']=1
        out['cases'][str(n)]=case(v);print('mass case',n,out['cases'][str(n)]['mass_kg'],flush=True)
        assert source_hash()==initial_hash,'Geometry source changed during generation; restart all variants'
    (O/'Massenvarianten.json').write_text(json.dumps(out,indent=2));(O/'massen.js').write_text('globalThis.P14_MASS='+json.dumps(out,separators=(',',':'))+';\n')
if __name__=='__main__':main()
