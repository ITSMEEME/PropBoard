import sys,json,os
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,os.environ.get('FREECAD_LIB',str(ROOT/'.cfd-tools/freecad/usr/lib')))
import FreeCAD as A
h=H;d=A.openDocument(str(h/'Ausgabe/P09_Servo_bis_Rotorblatt_Bewegung.FCStd'))
servo=[];blades=[]
for l in range(2):
 stationary=next(o.Name for o in d.Objects if getattr(o,'P09_Rahmen','')==f'p08:{l}:-1:swash')
 bearing=next(o.Name for o in d.Objects if getattr(o,'P09_Rahmen','')==f'swashrot:{l}' and o.BauteilID=='LAGER-6809')
 rotating=next(o.Name for o in d.Objects if getattr(o,'P09_Rahmen','')==f'swashrot:{l}' and o.BauteilID=='TM-TAUMEL-DREHRING')
 for i in range(3):
  path=[f'P09_Servoabtrieb_R{l}_S{i}',f'P08_R{l}_S{i}_horn',f'P08_R{l}_S{i}_ball_high',f'P08_R{l}_S{i}_body_high',f'P08_R{l}_S{i}_rod',f'P08_R{l}_S{i}_body_low',f'P08_R{l}_S{i}_ball_low',stationary,bearing,rotating,f'P09_Blattgelenktraeger_R{l}']
  assert all(d.getObject(n) for n in path);servo.append(dict(rotor=l,servo=i,native_path=path,upper_joint_cap=f'P08_R{l}_S{i}_cap_high',lower_joint_cap=f'P08_R{l}_S{i}_cap_low'))
 for j in range(8):
  pitch=next(o.Name for o in d.Objects if getattr(o,'P09_Rahmen','')==f'blade:{l}:{j}' and getattr(o,'MotionRole','')=='pitch_horn')
  blade=next(o.Name for o in d.Objects if getattr(o,'P09_Rahmen','')==f'blade:{l}:{j}' and getattr(o,'MotionRole','')=='blade')
  path=[f'P09_Blattgelenktraeger_R{l}',f'P09_R{l}_B{j}_stud_high',f'P09_R{l}_B{j}_body_high',f'P09_R{l}_B{j}_rod',f'P09_R{l}_B{j}_body_low',f'P09_R{l}_B{j}_stud_low',pitch,blade]
  assert all(d.getObject(n) for n in path);blades.append(dict(rotor=l,blade=j,native_path=path,caps=[f'P09_R{l}_B{j}_cap_high',f'P09_R{l}_B{j}_cap_low'],root_retention=[f'P09_R{l}_B{j}_{role}' for role in ('Axialschraube','Axialscheibe','Gewindeeinsatz','Klebefuge')]))
(h/'Ausgabe/Verbindungskette_P09.json').write_text(json.dumps(dict(description='Native object references for every servo-to-swash and swash-to-blade branch; kinematic coupling, not a strength certificate',servo_branches=servo,blade_branches=blades,manufacturing_release=False),indent=2)+'\n');print('6 servo paths and16 blade paths reference actual native objects')
