"""1.75m anthropometric standing reference; not a component or body-load simulation."""
import FreeCAD as A,Part,math
V=A.Vector

def ellipsoid(centre,radii):
 m=A.Matrix();m.A11=radii[0];m.A22=radii[1];m.A33=radii[2]
 s=Part.makeSphere(1).transformGeometry(m);s.translate(V(*centre));return s

def limb(a,b,r1,r2):
 a=V(*a);b=V(*b);v=b-a
 return Part.makeCone(r1,r2,v.Length,a,v).fuse(Part.makeSphere(r1,a)).fuse(Part.makeSphere(r2,b))

def human(base=244):
 parts=[]
 def add(name,shape,col):
  assert shape.isValid(),name
  parts.append((name,shape,col))
 skin=[.73,.48,.32];shirt=[.18,.42,.68];pants=[.16,.20,.25];shoe=[.14,.16,.18]
 # Nominal 1750mm from sole to head top; foot centres match the default slides.
 for sign in [-1,1]:
  add('Schuh_'+str(sign),ellipsoid((sign*200,-5,base+32.5),(48,130,32.5)),shoe)
  add('Unterschenkel_'+str(sign),limb((sign*190,0,base+80),(sign*140,0,base+490),43,57),pants)
  add('Oberschenkel_'+str(sign),limb((sign*140,0,base+490),(sign*88,0,base+890),58,75),pants)
  add('Oberarm_'+str(sign),limb((sign*203,0,base+1410),(sign*253,-12,base+1160),57,42),shirt)
  add('Unterarm_'+str(sign),limb((sign*253,-12,base+1160),(sign*275,-32,base+955),39,28),skin)
  add('Hand_'+str(sign),ellipsoid((sign*277,-35,base+900),(32,38,70)),skin)
 add('Becken',ellipsoid((0,0,base+900),(155,105,120)),pants)
 # Elliptical loft gives a shaped waist and shoulder, without schematic boxes.
 wires=[]
 for z,rx,ry in [(980,142,100),(1120,140,105),(1330,202,116),(1440,200,102),(1490,105,80)]:
  e=Part.Ellipse(V(0,0,base+z),rx,ry);wires.append(Part.Wire([e.toShape()]))
 add('Oberkoerper',Part.makeLoft(wires,True,False),shirt)
 add('Hals',limb((0,0,base+1460),(0,0,base+1560),48,44),skin)
 add('Kopf',ellipsoid((0,-4,base+1635),(84,95,115)),skin)
 add('Nase',ellipsoid((0,-93,base+1625),(18,22,22)),skin)
 for x in [-31,31]:add('Auge_'+str(x),ellipsoid((x,-89,base+1660),(7,7,6)),[.13,.14,.15])
 return parts
