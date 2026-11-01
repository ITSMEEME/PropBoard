#!/usr/bin/env python3
"""Run independent OpenFOAM cases in the managed local Docker daemon, bounded concurrency."""
import argparse,concurrent.futures,datetime,json,os,subprocess,time,re,shutil
from pathlib import Path
from erstellen import H,IMAGE
from netzcheck import check as check_mesh
ROOT=H.parents[1]
def one(rank,level,steps,until=500):
    case=H/'cases'/f'K{rank:02d}_{level}'
    assert (case/'case.json').exists(),f'Generate case {rank} first'
    requested_steps=steps
    if steps=='auto':
        times=sorted(float(p.name) for p in case.iterdir() if p.is_dir() and re.fullmatch(r'\d+(?:\.\d+)?',p.name) and ((p/'U').exists() or (p/'U.gz').exists()))
        latest=times[-1] if times else 0
        steps='solve' if latest>0 else 'all'
        if latest>=until:print('REUSE completed case',rank,level,latest,flush=True);check_mesh(case);return 0
        if latest>0:
            ctl=case/'system/controlDict';text=ctl.read_text();text=re.sub(r'startFrom \w+;', 'startFrom latestTime;',text);text=re.sub(r'stopAt \w+;', 'stopAt endTime;',text);target=max(until,latest+250);text=re.sub(r'endTime [\d.]+;',f'endTime {target:g};',text);text=re.sub(r'(writeControl timeStep; writeInterval )\d+;',lambda m:m[1]+f'{target-latest:g};',text,count=1);ctl.write_text(text)
            if (case/'log.simpleFoam').exists():shutil.copyfile(case/'log.simpleFoam',case/f'log.simpleFoam.before_{latest:g}')
    scripts={
      'all':'./Allrun',
      'mesh':'blockMesh > log.blockMesh 2>&1 && surfaceCheck constant/triSurface/wingUpper.stl > log.surfaceUpper 2>&1 && surfaceCheck constant/triSurface/wingLower.stl > log.surfaceLower 2>&1 && surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1 && snappyHexMesh -overwrite > log.snappyHexMesh 2>&1 && checkMesh -allGeometry -allTopology > log.checkMesh 2>&1 && topoSet > log.topoSet 2>&1',
      'solve':'topoSet > log.topoSet 2>&1 && decomposePar -latestTime -force > log.decomposePar 2>&1 && mpirun -np 2 --bind-to none simpleFoam -parallel > log.simpleFoam 2>&1 && reconstructPar -latestTime > log.reconstructPar 2>&1'}
    if steps=='solve':assert check_mesh(case)['status']=='PASS','Mesh not accepted'
    command=['docker','--host=unix:///var/run/docker.sock','run','--rm','--name',f'propboard-cfd-k{rank:02d}-{level}','--user',f'{os.getuid()}:{os.getgid()}','--cpus','2','--memory','10g','--mount',f'type=bind,src={ROOT},dst=/work','-w','/work/'+str(case.relative_to(ROOT)),'--entrypoint','/bin/bash',IMAGE,'-lc',scripts[steps]]
    env={k:v for k,v in os.environ.items() if k not in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']}
    t=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat();print('START',rank,level,steps,flush=True)
    with (case/'log.container').open('w') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env)
    report={'rank':rank,'level':level,'steps':steps,'requested_steps':requested_steps,'image':IMAGE,'started_utc':started,'duration_s':time.monotonic()-t,'exit_code':r.returncode}
    if (case/'log.checkMesh').exists() and (case/'log.snappyHexMesh').exists():check_mesh(case)
    (case/f'execution_{steps}.json').write_text(json.dumps(report,indent=2)+'\n');print('FINISH',rank,'exit',r.returncode,'seconds',round(report['duration_s']),flush=True)
    return r.returncode
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ranks',default=','.join(map(str,range(1,11))));p.add_argument('--level',default='coarse');p.add_argument('--steps',choices=['all','mesh','solve','auto'],default='auto');p.add_argument('--until',type=int,default=500);p.add_argument('--jobs',type=int,default=2);a=p.parse_args();assert 1<=a.jobs<=3
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:results=list(ex.map(lambda rank:one(rank,a.level,a.steps,a.until),map(int,a.ranks.split(','))))
    raise SystemExit(1 if any(results) else 0)
