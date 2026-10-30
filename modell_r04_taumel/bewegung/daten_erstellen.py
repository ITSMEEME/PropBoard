#!/usr/bin/env python3
"""Generate slow mechanism demo and lossless flight-log replay channels."""
import json,math,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'mechanik'))
import pruefen as K
kine=json.loads((H.parent/'simulation/kinematik.json').read_text());data={}
frames=[]
for i in range(161):
    t=i*.05;u=2*math.pi*t/8;servo=[]
    for l,sign in enumerate((1,-1)):
        pose,_=K.fit_pose((14 if l==0 else 16.7)+3*math.sin(u),3*math.sin(u/2),t*45,sign)
        servo.extend((K.servo_angles(pose,K.np.array(kine[l]['neutral']))/K.DEG).tolist())
    frames.append(dict(t=t,servoDeg=servo,angles=[t*45,t*45],p=[0,0,0],euler=[0,0,0]))
data['Kinematik_Demo']=dict(cg_m=[0,0,0],frames=frames,description='Slowed 7.5 rpm motion demo; not a flight operating point')
# Same CAD-position mass correction as flight engine, for exact CG coordinate replay.
M=json.loads((H.parent/'simulation/modell_h01.json').read_text());servos=[x for x in M['components'] if x.get('part_id')=='SERVO-PLATZHALTER'];dm=.011
cg=[(M['mass_kg']*M['cg_m'][i]+dm*sum(x['cg_m'][i] for x in servos))/(M['mass_kg']+6*dm) for i in range(3)]
profile=json.loads((H.parent/'simulation/servo_profiles.json').read_text())['Savox_SB2271SG_USER']
cg=[(M['mass_kg']*M['cg_m'][i]-.009*sum(x['cg_m'][i] for x in servos)+sum(x['mass_kg']*x['cg_m'][i] for x in profile['components']))/(M['mass_kg']+6*.060) for i in range(3)]
for name in ('Savox_7_4V_Manoever','Savox_6_0V_Boee','Savox_7_4V_Reibung_0_20'):
    rows=json.loads((H.parent/'simulation/Ergebnisse'/(name+'.json')).read_text());frames=[];angles=[0,0]
    for j,r in enumerate(rows):
        if j:
            dt=r['t']-rows[j-1]['t'];angles=[angles[l]+.5*(r['rpm'][l]+rows[j-1]['rpm'][l])*6*dt for l in range(2)]
        frames.append({k:r[k] for k in ('t','servoDeg','p','euler')}|{'angles':angles[:]})
    data[name]=dict(cg_m=cg,frames=frames,description='Savox 69 g, user supplied torque/speed limits; unvalidated flight-model replay; no new force solution inside FreeCAD')
(H/'Bewegungsdaten.json').write_text(json.dumps(data,separators=(',',':')))
print('Saved',sum(len(x['frames']) for x in data.values()),'frames in',len(data),'channels')
