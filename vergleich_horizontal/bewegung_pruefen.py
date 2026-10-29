"""Conservative rectangle footprints enclosing the projected NACA wings."""
import sys,json,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'cad'))
from umlauf_kinematik import state,perimeter
p=json.loads((HERE/'parameter.json').read_text());L=perimeter(p['straight_m'],p['radius_m'])
ambiguous=[];minimum=1e9
for phase in range(360):
    boxes=[]
    for j in range(p['wings_per_level']):
        x,y,tx,ty,_=state(L*(phase/360+j/p['wings_per_level']),p['straight_m'],p['radius_m'])
        t=np.array([tx,ty]);r=np.array([-ty,tx]);centre=np.array([x,y])
        alpha=math.radians(p['pitch_deg'])
        halfc=p['chord_m']/2*(math.cos(alpha)+.12*math.sin(alpha))
        vertices=np.array([centre+a*halfc*t+b*p['span_m']/2*r
                           for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]])
        boxes.append((vertices,t,r))
    for i,(a,t,r) in enumerate(boxes):
        for j in range(i+1,len(boxes)):
            b,tb,rb=boxes[j]
            gaps=[max((b@axis).min()-(a@axis).max(),(a@axis).min()-(b@axis).max())
                  for axis in (t,r,tb,rb)]
            sep=max(gaps);minimum=min(minimum,sep)
            if sep<=0:ambiguous.append([phase,i,j])
report={'sampled_phases':360,'footprint_overlap_candidates':ambiguous,
        'minimum_separating_axis_gap_m':minimum,
        'scope':'Conservative wing footprint test per level, both directions cover identical phases. No bearing or structural validation.'}
(HERE/'Bewegungspruefung.json').write_text(json.dumps(report,indent=2))
assert not ambiguous,ambiguous[:10]
print(json.dumps(report,indent=2))
