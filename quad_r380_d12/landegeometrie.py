"""Detailed landing/ESC carrier. mm. Upper shells bond to axial CFK columns.
No landing force passes through the ESC housing or its M3 device fasteners.
"""
import math
import FreeCAD as A,Part
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'quad_r380_d07'))
from geometrie import socket_shape,frame,placed,capsule
# This module is loaded by file spec as landing_geometry to avoid the helper name collision.
V=A.Vector

def ring(ro,ri,h,z,x,y):
 return Part.makeCylinder(ro,h,V(x,y,z)).cut(Part.makeCylinder(ri,h+2,V(x,y,z-1)))

def rounded_bar(x,y,half,r,z,h):
 s=Part.makeBox(2*half,2*r,h,V(x-half,y-r,z))
 return s.fuse(Part.makeCylinder(r,h,V(x-half,y,z))).fuse(Part.makeCylinder(r,h,V(x+half,y,z))).removeSplitter()

def hex_pocket(x,y,z,h,r=3.5):
 pts=[V(x+r*math.cos(i*math.pi/3+math.radians(85)),y+r*math.sin(i*math.pi/3+math.radians(85)),z) for i in range(6)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h))

def make_parts(v,cfg,P,norms):
 maxL=P['max_arm_length_mm'];idx=min(range(v['count']),key=lambda i:(v['end'][i][2],v['start'][i][2]));a=V(*v['start'][idx]);nom=V(maxL,v['end'][idx][1],min(v['end'][idx][2],-((v['od']+8)/2+8)));end=a+(nom-a)*((cfg['motor_half_spacing_mm']*math.sqrt(2)-246)/maxL);axis=end-a;axis.normalize();sr=frame(axis)
 cx=cfg['motor_half_spacing_mm']*math.sqrt(2)-210-P['ESC_motor_radial_offset_mm'];cy=(a+(end-a)*((cx-a.x)/(end.x-a.x))).y
 zground=P['landing_ground_z_mm']-88;padtop=zground+P['sole_thickness_mm'];base_top=padtop+P['foot_base_thickness_mm'];lower_flange_top=base_top+4;lower_tube_end=lower_flange_top+P['end_isolation_mm'];half=P['clamp_centres_radial_half_spacing_mm'];B=P['bond_length_mm'];L=P['clamp_grip_mm'];ro=P['leg_od_mm']/2;ri=P['leg_id_mm']/2;spigot_r=ri-P['bond_radial_gap_mm'];bore=spigot_r-2
 p=dict(grip_length_mm=L,split_gap_mm=.5,socket_od_mm=v['od']+8,socket_bore_mm=v['od']+.6,ear_x_mm=v['od']/2+6,ear_top_mm=10.5,ear_axial_length_mm=12,end_pad_thickness_mm=.3);ear=p['ear_x_mm'];lower=socket_shape(p);upper=socket_shape(p,upper=True)
 for sign in [-1,1]:lower=lower.cut(Part.makeCylinder(2.25,45,V(sign*ear,20,L/2),V(0,-1,0)))
 plane=cy+P['ESC_mount_plane_offset_tangential_mm'];zc=P['ESC_centre_z_mm']-88;railbottom=zc-33-5;pieces=[Part.makeBox(146,2,10,V(cx-73,plane,zc+dz-5)) for dz in [-33,33]];parts=[];legs=[];clamps=[]
 # A narrow basal spine; pads carry vertical pressure directly into its end bosses.
 foot=rounded_bar(cx,cy,half,P['foot_base_radius_mm'],padtop,P['foot_base_thickness_mm'])
 for sign in [-1,1]:
  x=cx+sign*half;centre=a+(end-a)*((x-a.x)/(end.x-a.x));base=centre-axis*(L/2);clamps.append((centre,base));pieces.append(placed(lower,tuple(base),sr))
  # Normal bottom connector is concentric with the support tube, rather than offset beside the ESC.
  anchor_z=centre.z-(v['od']+8)/2+2;flange_bottom=anchor_z-12;top_tube_end=flange_bottom-P['end_isolation_mm'];length=top_tube_end-lower_tube_end;assert length>70
  plug=Part.makeCylinder(spigot_r,B,V(x,centre.y,flange_bottom-B)).fuse(Part.makeCylinder(12,4,V(x,centre.y,flange_bottom))).fuse(Part.makeCylinder(9,8.5,V(x,centre.y,flange_bottom+4)))
  plug=plug.cut(Part.makeCylinder(bore,B+11.5,V(x,centre.y,flange_bottom-B)))
  pieces.append(plug)
  # ESC rail risers are secondary members, independent of the primary CFK landing columns.
  start=base+sr.multVec(V((-12 if v['od']==20 else -math.sqrt((p['socket_od_mm']/2-.5)**2-36)),-6,L));ct=V(x,cy-22,centre.z-28);pieces.append(capsule(tuple(start),tuple(ct),2.5));height=ct.z+1-railbottom;channel=Part.makeBox(10,6,height,V(x-5,cy-25.5,railbottom));channel=channel.cut(Part.makeBox(7,5,height+2,V(x-3.5,cy-24,railbottom-1)));pieces.append(channel)
  parts.append((f'Leg{sign}',ring(ro,ri,length,lower_tube_end,x,centre.y),1600,'landing_CFK'))
  for label,z,h in [('TopBond',flange_bottom-B,B-P['end_isolation_mm']),('BottomBond',lower_tube_end,B-P['end_isolation_mm'])]:parts.append((f'{label}{sign}',ring(ri,spigot_r,h,z,x,centre.y),1200,'bond_assumption'))
  for label,z in [('TopEnd',top_tube_end),('BottomEnd',lower_flange_top)]:parts.append((f'{label}{sign}',ring(ro,spigot_r,P['end_isolation_mm'],z,x,centre.y),1900,'isolation'))
  # Lower spigot is integral with the base; its centre tracks the selected arm tube taper.
  foot=foot.fuse(Part.makeCylinder(12,4,V(x,centre.y,base_top))).fuse(Part.makeCylinder(spigot_r,B,V(x,centre.y,lower_flange_top)))
  foot=foot.cut(Part.makeCylinder(bore,P['foot_base_thickness_mm']+B,V(x,centre.y,padtop+3)))
  legs.append(dict(x=x,y=centre.y,zmin=lower_tube_end,zmax=top_tube_end,length_mm=length,upper_flange_z=flange_bottom,clamp_centre=list(centre),clamp_base=list(base)))
  parts.append((f'Cap{sign}',placed(upper,tuple(base),sr),2700,'clamp_cap'))
  sleeve=ring(v['od']/2+.3,v['od']/2,L,0,0,0).cut(Part.makeBox(v['od'],.5,L+2,V(0,-.25,-1)));parts.append((f'GFK{sign}',placed(sleeve,tuple(base),sr),1900,'isolation'))
  hr=sr.multiply(A.Rotation(V(1,0,0),-90));washer4=norms['WasherM4'].BoundBox.ZLength
  for side in [-1,1]:
   for n,y,rot in [('WasherM4',10.5,sr.multiply(A.Rotation(V(1,0,0),-90))),('WasherM4',-10.5-washer4,hr),('BoltM4',10.5+washer4,hr),('NutM4',-10.5-washer4,hr.multiply(A.Rotation(V(0,0,1),34)).multiply(A.Rotation(V(0,1,0),180)))]:
    pos=base+sr.multVec(V(side*ear,y,L/2));sh=Part.Compound([norms[n]]);sh.Placement=A.Placement(pos,rot);parts.append((n+f'_{sign}_{side}_{y}',sh,7850,'hardware'))
 # Foot pockets leave a 3-mm sole-facing floor and perimeter ribs; neither cuts a leg boss.
 for sign in [-1,1]:foot=foot.cut(Part.makeBox(24,16,P['foot_base_thickness_mm']-2,V(cx+(10 if sign>0 else -34),cy-8,padtop+3)))
 # Wide soft shoe, rounded outline, shallow transverse grooves. No damping credit is taken.
 shoe=rounded_bar(cx,cy,half,P['sole_radius_mm'],zground,P['sole_thickness_mm'])
 for dx in [-40,-10,10,40]:shoe=shoe.cut(Part.makeBox(2,40,1,V(cx+dx-1,cy-20,zground)))
 washer3=norms['WasherM3'].BoundBox.ZLength
 for sign in [-1,1]:
  x=cx+sign*25
  foot=foot.cut(Part.makeCylinder(1.7,12,V(x,cy,padtop-1))).cut(hex_pocket(x,cy,padtop+1,9))
  shoe=shoe.cut(Part.makeCylinder(1.7,P['sole_thickness_mm']+2,V(x,cy,zground-1))).cut(Part.makeCylinder(3.75,P['sole_thickness_mm']-1.5,V(x,cy,zground)))
  rot=A.Rotation(V(1,0,0),180)
  for n,z,rot1 in [('WasherM3',padtop-1.5,rot),('BoltM3',padtop-1.5-washer3,rot),('NutM3',padtop+1,A.Rotation(V(0,0,1),85))]:
   sh=Part.Compound([norms[n]]);sh.Placement=A.Placement(V(x,cy,z),rot1);parts.append((f'{n}_Sole_{sign}',sh,7850,'hardware'))
 parts.extend([('FootBase',foot.removeSplitter(),2700,'landing_base'),('WearSole',shoe.removeSplitter(),P['sole_density_assumption_kg_m3'],'wear_sole')])
 body=pieces[0].fuse(tuple(pieces[1:]),1e-5).removeSplitter()
 for x in [-63,63]:
  for dz in [-33,33]:
   body=body.cut(Part.makeCylinder(1.7,12,V(cx+x,plane-5,zc+dz),V(0,1,0)))
   rot=A.Rotation(V(1,0,0),-90)
   for n,y in [('WasherM3',plane+2),('BoltM3',plane+2+washer3)]:
    sh=Part.Compound([norms[n]]);sh.Placement=A.Placement(V(cx+x,y,zc+dz),rot);parts.append((f'{n}_Device_{x}_{dz}',sh,7850,'planned_device_bolt' if n=='BoltM3' else 'hardware'))
   pad=Part.makeCylinder(3.5,.5,V(cx+x,plane,zc+dz),V(0,-1,0)).cut(Part.makeCylinder(1.7,1,V(cx+x,plane+.2,zc+dz),V(0,-1,0)));parts.append((f'DevicePad_{x}_{dz}',pad,1900,'isolation'))
 assert body.isValid() and len(body.Solids)==1,('body',v['id'],len(body.Solids))
 foot=foot.removeSplitter()
 if not foot.isValid():foot.fix(1e-7,1e-7,1e-6)
 assert foot.isValid() and len(foot.Solids)==1,('foot',v['id'],len(foot.Solids))
 parts=[(n,foot if n=='FootBase' else sh,d,r) for n,sh,d,r in parts]
 parts.insert(0,('Carrier',body,2700,'carrier'))
 # Vertical ESC envelope, not an invented OEM body. Radial146,vertical74,tangential39.5.
 xyz=[V(cx+x,y,zc+z) for y in [plane-40,plane-.5] for x,z in [(-73,-37),(73,-37),(73,37),(-73,37)]];marks=[]
 for i,j in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:delta=xyz[j]-xyz[i];marks.append(Part.makeCylinder(.25,delta.Length,xyz[i],delta))
 parts.append(('Regler_Bauraum',Part.Compound(marks),0,'unidentified_ESC_datum'))
 for name,s,density,role in parts:assert s.isValid(),(v['id'],name)
 return parts,dict(propeller_index=cfg['index'],variant=v['id'],cx=cx,cy=cy,support_tube_index=idx,legs=legs,ground_z_world_mm=P['landing_ground_z_mm'],ESC_box_local_mm=dict(min=[cx-73,plane-40,zc-37],size=[146,39.5,74]),sole_thickness_mm=P['sole_thickness_mm'],ESC_ground_clearance_mm=88+zc-37-P['landing_ground_z_mm'],clamp_grip_mm=L)
