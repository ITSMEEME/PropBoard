"""Rigid, closed-linkage animation for generated P14 native FreeCAD documents."""
import json,math,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A
from kinematik import solve,D
V=A.Vector
def T(x=0,y=0,z=0):return A.Placement(V(x,y,z),A.Rotation())
def R(axis,angle):return A.Placement(V(),A.Rotation(V(*axis),angle))
def chain(*ps):
    p=A.Placement()
    for q in ps:p=p.multiply(q)
    return p
def rod_transform(old,new):
    a,b=map(lambda p:V(*p),old);u,v=map(lambda p:V(*p),new);r=A.Rotation(b-a,v-u)
    return A.Placement(u-r.multVec(a),r)
def local_delta(row,c,pose,angle,neutral):
    g=c['geometry'];frame=row['frame'];az=row['a'];level=g['rotor_spacing_mm']/2;sz=g['swash_z_mm']
    if frame in ['fixed','shared']:return A.Placement()
    if frame=='rotor':return R([0,0,1],angle)
    if frame=='pitch':
        dp=pose['pitches_deg'][row['blade_index']]-g['neutral_pitch_deg']
        return chain(R([0,0,1],angle),T(z=level),R([math.cos(az*D),math.sin(az*D),0],dp),T(z=-level))
    if frame=='swash_slider':return T(z=pose['swash_z_mm']-sz)
    if frame in ['swash_fixed','swash_rotor']:
        tx,ty=pose['tilt_deg'];phase=angle if frame=='swash_rotor' else pose['stationary_phase_deg']
        return chain(T(z=pose['swash_z_mm']),R([1,0,0],tx),R([0,1,0],ty),R([0,0,1],phase),T(z=-sz))
    if frame in ['servo_horn','servo_shaft']:
        alpha=pose['servo_deg'][row['servo_index']]-g['servo_neutral_deg']
        return chain(R([0,0,1],az),T(g['servo_r_mm'],0,g['servo_z_mm']),R([0,1,0],alpha),T(-g['servo_r_mm'],0,-g['servo_z_mm']),R([0,0,1],-az))
    if frame=='pitch_link':
        i=row['blade_index'];rz=R([0,0,1],angle)
        old=[[v for v in rz.multVec(V(*p))] for p in neutral['pitch_points_mm'][i]]
        return rod_transform(old,pose['pitch_points_mm'][i]).multiply(rz)
    if frame=='servo_link':
        i=row['servo_index'];return rod_transform(neutral['servo_points_mm'][i],pose['servo_points_mm'][i])
    raise ValueError(frame)
class Animation:
    def __init__(self,doc,output=None):
        self.doc=doc;self.output=Path(output or H/'Ausgabe');self.c=json.loads((self.output/'Eingaben.json').read_text());self.scene=json.loads((self.output/'Szenengraph.json').read_text());self.q=json.loads((self.output/'Abgeleitet.json').read_text())
        self.base={r['native_object']:doc.getObject(r['native_object']).Shape.Placement for r in self.scene}
    def pose(self,angle=0,collective_upper=0,collective_lower=0,cyclic_x=0,cyclic_y=0):
        assert abs(collective_upper)<=3.5 and abs(collective_lower)<=3.5 and math.hypot(cyclic_x,cyclic_y)<=.500001
        poses={1:solve(self.c,-collective_upper,-cyclic_x,-cyclic_y,angle),-1:solve(self.c,collective_lower,cyclic_x,-cyclic_y,angle)}
        for row in self.scene:
            s=row['sign'];unit=T(*self.q['unit_centres_mm'][row['unit']]);pod=R([0,1,0],180) if s<0 else A.Placement();world=unit.multiply(pod)
            local=local_delta(row,self.c,poses[s],angle,self.q['neutral']);delta=chain(world,local,world.inverse())
            o=self.doc.getObject(row['native_object']);o.Placement=delta.multiply(self.base[o.Name])
        self.doc.recompute();return poses
    def reset(self):
        for name,p in self.base.items():self.doc.getObject(name).Placement=p
        self.doc.recompute()

def gui():
    import FreeCADGui as Gui
    from PySide import QtCore
    try:from PySide import QtWidgets
    except ImportError:from PySide import QtGui as QtWidgets
    doc=A.ActiveDocument
    if not doc or not any(o.Name=='Teil_0' for o in doc.Objects):doc=A.openDocument(str(H/'Ausgabe/P14_MN1330_Leichtbau.FCStd'))
    runtime=Animation(doc);dialog=QtWidgets.QDialog();dialog.setWindowTitle('P14 Mechanik – Entwicklung')
    layout=QtWidgets.QFormLayout(dialog);fields={}
    for label,limits,initial in [('Rotorwinkel',(-3600,3600),0),('Kollektiv oben',(-3.5,3.5),0),('Kollektiv unten',(-3.5,3.5),0),('Zyklisch X',(-.35,.35),0),('Zyklisch Y',(-.35,.35),0)]:
        widget=QtWidgets.QDoubleSpinBox();widget.setRange(*limits);widget.setDecimals(2);widget.setSingleStep(.1 if label!='Rotorwinkel' else 5);widget.setValue(initial);fields[label]=widget;layout.addRow(label,widget)
    def update():runtime.pose(*[w.value() for w in fields.values()]);Gui.activeDocument().activeView().redraw()
    for w in fields.values():w.valueChanged.connect(update)
    play=QtWidgets.QPushButton('Animation Start / Pause');layout.addRow(play);timer=QtCore.QTimer(dialog);timer.setInterval(50)
    timer.timeout.connect(lambda:fields['Rotorwinkel'].setValue((fields['Rotorwinkel'].value()-2)%360));play.clicked.connect(lambda:timer.stop() if timer.isActive() else timer.start())
    dialog.finished.connect(lambda _: (timer.stop(),runtime.reset()));dialog.show();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
    # Keep Qt/runtime references alive after the macro returns.
    A._P14_animation_dialog=(dialog,runtime,timer);return runtime
if __name__=='__main__':gui()
