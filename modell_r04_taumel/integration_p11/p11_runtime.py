"""P11: original closed servo/blade links + 1:1 motor rotor + rolling guides. mm/deg."""
import json,math,sys
from pathlib import Path
import FreeCAD as A
H=Path(__file__).resolve().parent
sys.path[:0]=[str(H.parent/'bewegung_p09'),str(H.parent/'bewegung')]
import voll_runtime as R
M=R.M;V=A.Vector
P=json.loads((H/'parameter.json').read_text())
CENTRE=math.hypot(P['roller_journal_radial_mm'],P['roller_journal_tangent_mm'])
RATIO=P['guide_track_inner_radius_mm']/P['roller_radius_mm']
def roller_frame(sign,k,angle):
    phi=P['roller_azimuths_deg'][k];a=math.radians(phi);r=P['roller_journal_radial_mm'];t=P['roller_journal_tangent_mm']
    return M.local_world(sign).multiply(M.placement((r*math.cos(a)-t*math.sin(a),r*math.sin(a)+t*math.cos(a),0),M.rotz(RATIO*angle)))
def state(servos,angles):
    s=R.state(servos,angles)
    for l,sign in [(0,1),(1,-1)]:
        s['frames'].pop(f'pinion:{l}',None)
        s['frames'][f'motor:{l}']=s['frames'][f'rotor:{l}']
        for k in range(2):s['frames'][f'roller:{l}:{k}']=roller_frame(sign,k,angles[l])
    return s
def apply(doc,servos,angles,recompute=True):
    s=state(servos,angles)
    if recompute:
        ctl=doc.getObject('P09_Animation');ctl.Modus='Manuell';ctl.Servo_deg=list(servos);ctl.Rotor_deg=list(angles)
    for o in doc.Objects:
        key=getattr(o,'P09_Rahmen','fixed')
        if key!='fixed':o.Placement=s['frames'][key].multiply(o.P09_Neutralrahmen.inverse())
    if recompute:doc.recompute()
    return s
demo=R.demo
class Controller:
    def __init__(self,o):o.Proxy=self
    def execute(self,o):
        servos,angles=demo(o.Zeit_s) if o.Modus=='Demo' else (list(o.Servo_deg),list(o.Rotor_deg))
        try:
            s=apply(o.Document,servos,angles,False);o.Gelenkfehler_mm=s['max_error'];o.Blattpitch_deg=[p for row in s['pitches'] for p in row];o.Status='P11: Direktantrieb 1:1, Fuehrungsrollen; Motor noch auszuwaehlen, keine Freigabe'
        except ValueError as e:o.Status=str(e)
    def onChanged(self,o,p):pass
    def dumps(self):return None
    def loads(self,s):pass
