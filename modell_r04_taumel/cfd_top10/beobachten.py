#!/usr/bin/env python3
"""Refresh the local review dashboard while solvers run; sends no external messages."""
import argparse,time
from pathlib import Path
from auswerten import main,H
from netzcheck import check
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--interval',type=int,default=30);p.add_argument('--cycles',type=int,default=360);a=p.parse_args();assert 5<=a.interval<=60
    for i in range(a.cycles):
        for case in sorted((H/'cases').glob('K??_coarse')):
            mesh=case/'log.checkMesh';snap=case/'log.snappyHexMesh'
            if mesh.exists() and snap.exists() and 'Mesh OK.' in mesh.read_text(errors='replace'):
                try:check(case)
                except (OSError,ValueError):pass
        try:main()
        except (OSError,ValueError) as e:print(type(e).__name__,str(e),flush=True)
        if i+1<a.cycles:time.sleep(a.interval)
