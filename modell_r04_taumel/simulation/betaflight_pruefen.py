"""Integration test against the RUNNING REAL Betaflight server (no firmware mocks)."""
import json,math,subprocess,time,urllib.request
from pathlib import Path
BASE='http://127.0.0.1:8765'
HERE=Path(__file__).resolve().parent
def get():return json.load(urllib.request.urlopen(BASE+'/api/betaflight/status',timeout=3))
body={'state':{'dt':.0025,'q':[1,0,0,0],'w':[0,0,0],'p':[0,0,1],'v':[0,0,0],'specificForce':[0,0,9.80665]},'sticks':{'roll':0,'pitch':0,'yaw':0,'throttle':-1},'armed':False,'angle':True}
def frame():
    req=urllib.request.Request(BASE+'/api/betaflight/frame',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    out=json.load(urllib.request.urlopen(req,timeout=3));assert out['motorCount']==2 and len(out['servoRad'])==6 and out['ageMs']<150
    return out
def hold(n=180):
    for _ in range(n):out=frame()
    return out
metadata=get();assert metadata['realFirmware'] and metadata['mspVersion']==[4,5,2]
node="const F=require('./flugphysik.js'),S=require('./szenarien.js');const s=new F.Flight({...S.cases.find(c=>c.name==='Savox_7_4V_Manoever').options,massModel:'P11',drive:'P11_DIRECT',noise:false});console.log(JSON.stringify(s.B));"
B=json.loads(subprocess.check_output(['node','-e',node],cwd=HERE,text=True))
evidence={'firmware':metadata['firmware'],'axes':[]}
try:
    neutral=hold()['servoRad']
    for axis in range(2):
        q=[math.cos(math.radians(5)/2),0,0,0];q[axis+1]=math.sin(math.radians(5)/2);body['state']['q']=q
        out=hold(220);att=get()['attitudeDeg'];expected=5 if axis==0 else -5
        assert abs(att[axis]-expected)<.2,(axis,att)
        restoring=sum(v*(a-b) for v,a,b in zip(B[axis+1],out['servoRad'],neutral))
        assert restoring<0,('Wrong restoring sign',axis,restoring)
        evidence['axes'].append({'kind':'angle','axis':axis,'firmware_angle_deg':att[axis],'linearized_restoring_moment_Nm':restoring})
        body['state']['q']=[1,0,0,0];hold(100)
    body['angle']=False
    neutral=hold()['servoRad']
    for axis in range(3):
        body['state']['w'][axis]=.2;out=hold(220)
        damping=sum(v*(a-b) for v,a,b in zip(B[axis+1],out['servoRad'],neutral))
        assert damping<0,('Wrong damping sign',axis,damping)
        evidence['axes'].append({'kind':'rate','axis':axis,'linearized_damping_moment_Nm':damping})
        body['state']['w'][axis]=0;hold(100)
    body['angle']=True;hold(150);body['armed']=True
    for _ in range(800):
        out=frame()
        if out['armed']:break
    assert out['armed'],out
    body['sticks']['throttle']=0;gas=hold(220);assert gas['armed'] and min(gas['duty'])>.2,gas
    body['sticks']['roll']=.5;roll=hold(220);assert max(roll['servoRad'])-min(roll['servoRad'])>.05,roll
    evidence['gas_duty']=gas['duty'];evidence['roll_servo_rad']=roll['servoRad']
    time.sleep(.65);assert not get()['armed'],'Idle watchdog must disarm'
    evidence['idle_watchdog_disarmed']=True;evidence['status']='PASS'
finally:
    body['armed']=False;body['sticks']={k:0 for k in body['sticks']};body['sticks']['throttle']=-1;body['state']['q']=[1,0,0,0];body['state']['w']=[0,0,0];hold(80)
Path('/tmp/PropBoard-Betaflight-Pruefung.json').write_text(json.dumps(evidence,indent=2))
print(json.dumps(evidence,indent=2))
