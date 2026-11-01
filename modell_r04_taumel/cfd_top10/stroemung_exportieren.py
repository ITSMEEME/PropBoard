#!/usr/bin/env python3
"""Sample actual solved fields in an isolated copy; never touch active force histories."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from erstellen import H,IMAGE,write
def prepare(rank,time,level):
    src=H/'cases'/f'K{rank:02d}_{level}';probe=H/'cases'/f'K{rank:02d}_probe_{time}_{level}';probe.mkdir(exist_ok=True)
    meta=json.loads((src/'case.json').read_text());R=meta['design']['diameterMm']/2000
    if not (probe/'constant').exists():shutil.copytree(src/'constant',probe/'constant',copy_function=os.link)
    (probe/str(time)).mkdir(exist_ok=True)
    for field in ['U','p']:
        source=src/str(time)/field
        if not source.exists():source=source.with_name(field+'.gz')
        assert source.exists(),f'Full reconstructed field missing: {source}'
        shutil.copyfile(source,probe/str(time)/source.name)
    for name in ['fvSchemes','fvSolution']:
        (probe/'system').mkdir(exist_ok=True);shutil.copyfile(src/'system'/name,probe/'system'/name)
    write(probe,'system/controlDict',f'''application postProcess; startFrom startTime; startTime {time}; stopAt endTime; endTime {time}; deltaT 1; writeControl timeStep; writeInterval 1; writeFormat ascii; runTimeModifiable false;
functions {{ profiles {{ type surfaces; libs (sampling); writeControl timeStep; writeInterval 1; surfaceFormat raw; interpolationScheme cellPoint; fields (U p);
 surfaces {{ midspan {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{point ({.7*R} 0 0); normal (1 0 0);}} interpolate true; }} }} }} }}''')
    (probe/'case.json').write_text(json.dumps(meta,indent=2)+'\n');return probe
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rank',type=int,required=True);p.add_argument('--time',type=int,required=True);p.add_argument('--level',default='coarse');a=p.parse_args();probe=prepare(a.rank,a.time,a.level);root=H.parents[1]
    env={k:v for k,v in os.environ.items() if k not in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']}
    command=['docker','--host=unix:///var/run/docker.sock','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','--cpus','1','--mount',f'type=bind,src={root},dst=/work','-w','/work/'+str(probe.relative_to(root)),'--entrypoint','/bin/bash',IMAGE,'-lc',f'postProcess -time {a.time} -fields "(U p)" > log.sample 2>&1']
    r=subprocess.run(command,env=env);print(probe);raise SystemExit(r.returncode)
