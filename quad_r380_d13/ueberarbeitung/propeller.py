"""Photo-derived two-blade reference, fixed project hub, pitch/diameter-scaled loft.
NOT manufacturer geometry. Chord/profile/thickness and hub interface are assumed.
"""
import math
import FreeCAD as A,Part
V=A.Vector

def section(r,c,beta,tc,camber,sweep,z):
 upper=[];lower=[];p=.4
 for i in range(33):
  u=(1-math.cos(math.pi*i/32))/2
  yc=camber/(p*p)*(2*p*u-u*u) if u<p else camber/((1-p)**2)*(1-2*p+2*p*u-u*u)
  slope=2*camber/(p*p)*(p-u) if u<p else 2*camber/((1-p)**2)*(p-u);theta=math.atan(slope)
  yt=5*tc*(.2969*math.sqrt(u)-.1260*u-.3516*u*u+.2843*u**3-.1015*u**4)
  for sign,pts in [(1,upper),(-1,lower)]:
   xx=u-sign*yt*math.sin(theta);zz=yc+sign*yt*math.cos(theta);y=-(xx-.5)*c;h=zz*c
   pts.append(V(r,sweep+y*math.cos(beta)-h*math.sin(beta),z+y*math.sin(beta)+h*math.cos(beta)))
 cu=Part.BSplineCurve();cu.interpolate(upper);cl=Part.BSplineCurve();cl.interpolate(list(reversed(lower)))
 return Part.Wire([cu.toShape(),Part.makeLine(upper[-1],lower[-1]),cl.toShape()])

def shape(c):
 R=c['radius_mm'];P=c['pitch_mm'];axis=158.5
 radii=[50.,60.,75.,max(95.,.23*R),max(115.,.32*R),max(135.,.50*R),.70*R,.88*R,.96*R,R+2]
 chords=[44,44,44,.16*R,.155*R,.13*R,.10*R,.075*R,.055*R,.045*R]
 assert all(b>a for a,b in zip(radii,radii[1:])),radii
 wires=[];stations=[]
 for r,chord in zip(radii,chords):
  t=max(0,min(1,(r-75)/30));blend=t*t*(3-2*t);beta=math.atan(P/(2*math.pi*r))*blend;f=max(0,min(1,(r-50)/(R-50)));tc=.18*(1-f)+.08*f;camber=.025*blend;sweep=.025*R*f*f*(3-2*f);z=axis-.004*R*f**3
  wires.append(section(r,chord,beta,tc,camber,sweep,z));stations.append(dict(radius_mm=r,chord_mm=chord,twist_deg=math.degrees(beta),thickness_ratio=tc,camber_ratio=camber,sweep_mm=sweep,axis_z_mm=z))
 root=Part.makeLoft(wires[:3],True,False);outer=Part.makeLoft(wires[2:],True,False).common(Part.makeBox(R+100,4*R,200,V(75,-2*R,80)));blade=root.fuse(outer);other=blade.copy();other.rotate(V(),V(0,0,1),180)
 e=Part.Ellipse(V(0,0,154),70,22);hub=Part.Face(Part.Wire([e.toShape()])).extrude(V(0,0,9));s=hub.fuse(blade).fuse(other)
 s=s.common(Part.makeCylinder(R,160,V(0,0,90)))
 s=s.cut(Part.makeCylinder(7.5,80,V(0,0,120)))
 for deg in [45,135,225,315]:
  t=math.radians(deg);s=s.cut(Part.makeCylinder(2.75,80,V(15*math.cos(t),15*math.sin(t),120)))
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1,(c['label'],s.isValid(),len(s.Solids));assert abs(s.Solids[0].CenterOfMass.x)<.01 and abs(s.Solids[0].CenterOfMass.y)<.01
 cw=s.mirror(V(),V(0,1,0));assert cw.isValid() and len(cw.Solids)==1
 return s,cw,stations
