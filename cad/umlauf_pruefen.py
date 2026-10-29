"""Sampled motion audit; bounding circles enclose whole wing cross-sections."""
import json
import math
from pathlib import Path
from umlauf_kinematik import perimeter,state

HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'umlauf_parameter.json').read_text())
length=perimeter(p['straight_m'],p['radius_m'])
minimum=1e9
bounds=[1e9,-1e9,1e9,-1e9]
for k in range(360):
    for direction in (-1,1):
        positions=[]
        for j in range(p['wings_per_module']):
            x,z,*_=state(length*(j/p['wings_per_module']+direction*k/360),
                         p['straight_m'],p['radius_m'],direction,p['pitch_amplitude_deg'])
            positions.append((x,z))
            r=.5*p['chord_m']*math.sqrt(1+p['thickness_ratio']**2)
            bounds=[min(bounds[0],x-r),max(bounds[1],x+r),
                    min(bounds[2],z-r),max(bounds[3],z+r)]
        for i,a in enumerate(positions):
            for b in positions[i+1:]: minimum=min(minimum,math.dist(a,b))
clearance=minimum-p['chord_m']*math.sqrt(1+p['thickness_ratio']**2)
assert clearance>0
assert bounds[1]-bounds[0]<2.1
assert .290-bounds[2]<.6
assert bounds[3]<.250 # Wing cross sections below deck underside.
report={'sampled_phases':360,'directions':[-1,1],
        'min_wing_centre_distance_m':minimum,
        'bounding_circle_clearance_m':clearance,
        'moving_wing_xz_bounds_m':bounds,
        'note':'Sampled conservative wing clearance only; no structural, bearing or rail-clearance validation'}
(HERE/'Umlauf_Bewegungspruefung.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
