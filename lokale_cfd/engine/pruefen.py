#!/usr/bin/env python3
"""No solver run: verify transferred geometry and hardware constraints."""
import os,tempfile
os.environ['CFD_WORKDIR']=tempfile.mkdtemp(prefix='propboard-check-')
import manage as m
for name in ['fullscale','model']:
    os.environ['CFD_PROFILE']=name
    p=m.profile();rows=m.seeds(p)['top10Aerodynamic']
    assert len(rows)==10 and all(m.valid(r['design'],p) for r in rows)
    if name=='fullscale':
        h=m.hardware(p)
        assert h['inferred_battery_cells']==20 and not h['ideal_target_feasible']
        assert p['motor']['through_bore'] is False and p['motor']['free_axial_bore_mm']==0
        assert all(r['thrustN'] is None and r['mechanicalPowerW'] is None for r in rows)
        assert all(r['design']['diameterMm']==1500 for r in rows)
        bad=dict(rows[0]['design']);bad['chordMm']=1000
        assert not m.valid(bad,p)
    print(name,': PASS — 10 valid seeds, physical limits and provenance')
