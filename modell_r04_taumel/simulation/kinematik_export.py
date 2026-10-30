#!/usr/bin/env python3
import sys,json
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'mechanik'))
import pruefen as K
out=[]
for sign,collective in [(1,14),(-1,16.7)]:
    pose,_=K.fit_pose(collective,0,0,sign)
    angles=K.servo_angles(pose,pose)
    _,J=K.actuation_matrix(pose,angles,pose,sign)
    out.append(dict(sign=sign,neutral=pose.tolist(),link_lengths_mm=[float(K.np.linalg.norm(K.servo_end(0,a)-K.stat_ball(pose,a))) for a in K.SW['servo_angles_deg']],pitch_servo_jacobian=J.tolist()))
(H/'kinematik.json').write_text(json.dumps(out,indent=2))
(H/'kinematik.js').write_text('globalThis.H01_KINEMATICS='+json.dumps(out)+';\n')

references=[]
for sign,collective,cyclic,phase in [(1,5,0,0),(1,14,4,60),(1,21,3,120),(-1,10,4,30),(-1,16.7,2,180)]:
    neutral=K.fit_pose(K.P['pitch_hover_deg'][0 if sign>0 else 1],0,0,sign)[0]
    pose,_=K.fit_pose(collective,cyclic,phase,sign)
    alpha=K.servo_angles(pose,neutral)
    for az in (0,37,123):
        pitches,error=K.forward(pose,az,sign,K.np.full(8,collective*K.DEG))
        references.append(dict(sign=sign,pose=pose.tolist(),servo_rad=alpha.tolist(),azimuth_deg=az,pitch_rad=pitches.tolist()))
(H/'kinematik_referenz.json').write_text(json.dumps(references,indent=2))
