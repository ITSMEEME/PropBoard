"""40 precomputed detailed arm configurations,10 explicit OEM rotor-space envelopes."""
import sys,json,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent;O=H/'Ausgabe';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod',str(R/'quad_r380_d07')])
import FreeCAD as A,Part,PartDesign
from geometrie import socket_shape,frame,placed,capsule,intersection_volume,trim_core,liner
V=A.Vector;P0=json.loads((R/'quad_r380_d07/parameter.json').read_text());variants=json.loads((H/'Varianten.json').read_text());configs=json.loads((H/'Konfigurationen.json').read_text());D=A.openDocument(str(R/'quad_r380_d08/Ausgabe/Quad_Parametrisch_V1_V4.FCStd'));lib=D.getObject('Bauteilbibliothek');assembly=D.getObject('Montage');control=D.getObject('Variantensteuerung');control.Variante=['V1','V2','V3','V4','V5'];control.addProperty('App::PropertyEnumeration','Propeller');control.Propeller=[c['label'] for c in configs];control.Propeller=configs[-1]['label'];control.Hinweis='HEP-S selections are swept-space envelopes,not OEM propeller geometry; no flight release. Detailed arm geometry adapts.'
oldcommon=json.loads((R/'quad_r380_d08/Ausgabe/Gemeinsame_Instanzen.json').read_text());motorrows=[r for r in oldcommon if r['instance'].startswith('D05_')];common=[]
for r in oldcommon:
 if r.get('rotor_id') or r['instance'].startswith('D05_') or r.get('group')=='Kabelplanung':
  # Record motor masters before removing their instances.
  if r in motorrows:r['master']=D.getObject(r['instance']).LinkedObject.Name
  D.removeObject(r['instance'])
 else:common.append(r)
for r in json.loads((R/'quad_r380_d08/Ausgabe/Instanzen.json').read_text())+json.loads((R/'quad_r380_d08/Ausgabe/Hardware.json').read_text()):D.removeObject(r['instance'])
source=A.openDocument(str(R/'quad_r380_d07/Ausgabe/QuadR380_D07_V3.FCStd'));core=placed(trim_core(source.getObject('D07_ROOT_TOP').Shape.copy()),(-65,0,22),A.Rotation(V(0,0,1),90));rootcache={};reports=[];allrows=[];sizedrows=[];maxX=configs[-1]['motor_half_spacing_mm']*math.sqrt(2)-210;maxL=maxX-36
for pidx,cfg in enumerate(configs):
 for r in motorrows:
  nr=dict(r);master=D.getObject(r['master']);x,y,z=r['placement_mm'];delta=cfg['motor_half_spacing_mm']-470;pos=V(x+math.copysign(1,x)*delta,y+math.copysign(1,y)*delta,z);obj=D.addObject('App::Link','P'+str(pidx)+'_'+r['instance']);obj.setLink(master);obj.LinkPlacement=A.Placement(pos,A.Rotation(*r['placement_quaternion']));assembly.addObject(obj);obj.Visibility=True;obj.setExpression('Visibility',f'Variantensteuerung.Propeller == {pidx} ? 1 : 0');nr.update(instance=obj.Name,propeller_index=pidx,placement_mm=list(pos));sizedrows.append(nr)
 # Three thin boundary rings delineate the assumed sweep,not blade surfaces.
 shape=Part.makeTorus(cfg['radius_mm'],1.0,V(0,0,124)).fuse((Part.makeTorus(cfg['radius_mm'],1.0,V(0,0,154)),Part.makeTorus(cfg['radius_mm'],1.0,V(0,0,184))))
 master=D.addObject('Part::Feature','P'+str(pidx)+'_Rotorhuelle');master.Shape=Part.Compound([shape]);lib.addObject(master);master.Visibility=False
 for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]:
  obj=D.addObject('App::Link','P'+str(pidx)+'_Rotorhuelle_Link');obj.setLink(master);pos=V(sx*cfg['motor_half_spacing_mm'],sy*cfg['motor_half_spacing_mm'],0);obj.LinkPlacement=A.Placement(pos,A.Rotation());assembly.addObject(obj);obj.Visibility=True;obj.setExpression('Visibility',f'Variantensteuerung.Propeller == {pidx} ? 1 : 0');sizedrows.append(dict(instance=obj.Name,id=master.Name,label=cfg['label']+' Rotor-Hüllraum (kein OEM-Blatt)',group='Rotorhuelle',propeller_index=pidx,mass_kg=0,placement_mm=list(pos),placement_quaternion=[0,0,0,1]))
def safe_cut(shape,cutters,tolerance=1e-5):
    if not shape.isValid():
        shape=shape.copy();shape.fix(1e-7,1e-7,1e-6)
        assert shape.isValid()
    before=shape.Volume
    for source in [shape,shape.removeSplitter()]:
        for tol in [tolerance,0,1e-7,1e-6,1e-4]:
            result=source.cut(cutters,tol)
            if result.isValid() and len(result.Solids)==1 and 1000<result.Volume<=before+.1:return result
    for delta in [V(.0001,0,0),V(0,.0001,0),V(0,0,.0001),V(-.0001,0,0),V(0,-.0001,0),V(0,0,-.0001)]:
        shifted=[]
        for tool in cutters:
            tool=tool.copy();tool.translate(delta);shifted.append(tool)
        result=shape.removeSplitter().cut(tuple(shifted),1e-6)
        if not result.isValid():result.fix(1e-7,1e-7,1e-6)
        if result.isValid() and len(result.Solids)==1 and 1000<result.Volume<=before+.1:return result
    shape.exportBrep(str(O/'Failed_Cut_Source.brep'));cutters[0].exportBrep(str(O/'Failed_Cut_Tool.brep'))
    raise RuntimeError('Boolean subtraction failed volume/single-solid invariant')

shared_roots={}
def addmaster(name, s, density):
    key=name.split("_",1)[1] if name.endswith("_Root") or name.endswith("_root") else None
    if key in shared_roots:return shared_roots[key]
    assert s.isValid() and len(s.Solids) == 1, (name, len(s.Solids))
    o = D.addObject('Part::Feature', name)
    o.Shape = Part.Compound([s])
    lib.addObject(o)
    o.Visibility = False
    result=(o,s.Volume*density*1e-9)
    if key:shared_roots[key]=result
    return result
for pidx in reversed(range(len(configs))):
 cfg=configs[pidx]
 for idx,v in enumerate(variants):
      cachedir=H/'Cache'/('P'+str(pidx)+'_'+v['id']);cachemeta=cachedir/'parts.json'
      signature=hashlib.sha256(json.dumps(dict(config=cfg,variant=v,base=P0,maxL=maxL,algorithm=('D10-v5-web-v3' if v['id']=='V5' else 'D09-fixed-axes-v1')),sort_keys=True).encode()).hexdigest()
      if cachemeta.exists() and json.loads(cachemeta.read_text()).get('signature')==signature:
          meta=json.loads(cachemeta.read_text());parts=[]
          for item in meta['parts']:
              shape=Part.Shape();shape.read(str(cachedir/(item['name']+'.brep')));assert len(shape.Solids)==1
              parts.append((item['name'],shape,item['density']))
          rootcache[v['id']]=parts[0][1].copy();cached=True;sym=meta['symmetry'];hits=meta['hits'];print('Cached geometry',pidx,v['id'],flush=True)
      else:
          p = dict(P0)
          p.update(tube_od_mm=v['od'], tube_id_mm=v['di'], socket_bore_mm=v['od'] + 0.6, socket_od_mm=v['od'] + 8, ear_x_mm=v['od'] / 2 + 6)
          starts = [V(*a) for a in v['start']]
          motorX=cfg['motor_half_spacing_mm']*math.sqrt(2)-210
          length= motorX-36
          maxends=[V(maxL,b[1],min(b[2],-(p['socket_od_mm']/2+8))) for b in v['end']]
          ends=[a+(b-a)*(length/maxL) for a,b in zip(starts,maxends)]
          cached=v['id'] in rootcache
          cap = socket_shape(p, upper=True)
          ro = p['socket_od_mm'] / 2
          root = rootcache[v['id']].copy() if cached else core.copy()
          foot = Part.makeCylinder(14, 6, V(motorX, 0, -6))
          for x, y in [(25, 0), (-25, 0), (0, 25), (0, -25)]:
              pts = [V(motorX, 0, -6), V(motorX + x, y, -6)]
              delta = pts[1] - pts[0]
              n = V(-delta.y, delta.x, 0)
              n.normalize()
              q = [pts[0] + n * 6, pts[1] + n * 6, pts[1] - n * 6, pts[0] - n * 6]
              foot = foot.fuse((Part.Face(Part.makePolygon(q + [q[0]])).extrude(V(0, 0, 6)),), 1e-05).fuse((Part.makeCylinder(9, 6, pts[1]),), 1e-05)
          root_pieces=[];motor_pieces=[]
          sockets = []
          parts = []
          for j, (a, b) in enumerate(zip(starts, ends)):
              d = b - a
              length = d.Length
              d.normalize()
              r = frame(d)
              t = Part.makeCylinder(v['od'] / 2, length).cut((Part.makeCylinder(v['di'] / 2, length),), 1e-05)
              parts.append((f'Tube{j}', placed(t, tuple(a), r), 1600))
              for side, origin in [('root', a), ('motor', b - d * 35)]:
                  shell = placed(socket_shape(p, stop='root' if side == 'root' else 'tip'), tuple(origin), r)
                  if side == 'root':
                      root_pieces.append(shell)
                  else:
                      motor_pieces.append(shell)
                  q = a - d * 1.5 if side == 'root' else b + d * 1.5
                  q = q + r.multVec(V(0, -ro + 2, 0))
                  for sign in [-1, 1]:
                      anchor = V(-58, sign * 9, 29) if side == 'root' else V(motorX, sign * 12, -5)
                      end = q + r.multVec(V(sign * ro * 0.35, 0, 0))
                      if side == 'root':
                          elbow = V(-15, sign * max(9, abs(a.y)), 29)
                          root_pieces.extend([capsule(tuple(anchor), tuple(elbow), 6),capsule(tuple(elbow), tuple(end), 6)])
                      else:
                          
                          if v['id']!='V5':motor_pieces.append(capsule(tuple(anchor), tuple(end), 6))
                  caps = placed(cap, tuple(origin), r)
                  parts.append((f'Cap{j}_{side}', caps, 2810))
                  parts.append((f'Liner{j}_{side}', placed(liner(p), tuple(origin), r), 1900))
                  padpos = origin - d * 0.3 if side == 'root' else b
                  parts.append((f'Pad{j}_{side}', placed(Part.makeCylinder(v['od'] / 2, 0.3), tuple(padpos), r), 1900))
                  sockets.append((side, origin, d, r))
          if v['id']=='V5':
              for sign,upper_idx,lower_idx in [(-1,0,2),(1,1,3)]:
                  upper=ends[upper_idx];lower=ends[lower_idx];wall=(upper.y+lower.y)/2+sign*6;y0=min(wall,wall-sign*4)
                  motor_pieces.append(Part.makeBox(10,4,-lower.z+13,V(motorX-30,y0,lower.z-12)))
                  for endpoint in [upper,lower]:motor_pieces.append(Part.makeBox(motorX-20-(endpoint.x-17.5),4,4,V(endpoint.x-17.5,y0,endpoint.z-12)))
                  motor_pieces.append(capsule(tuple(V(motorX-25,wall,-3)),tuple(V(motorX-4,sign*12,-3)),4))
          root=root if cached else root.fuse(tuple(root_pieces),1e-5);foot=foot.fuse(tuple(motor_pieces),1e-5).removeSplitter()
          assert root.Volume>=max(t.Volume for t in root_pieces)-.1 and foot.Volume>=max(t.Volume for t in motor_pieces)-.1
          for side, origin, d, r in sockets:
              upper = placed(cap, tuple(origin), r)
              if side == 'root' and not cached and intersection_volume(root,upper)>.1:root=root.cut((upper,),1e-5)
              if side == 'motor' and intersection_volume(foot,upper)>.1:foot=safe_cut(foot,(upper,),1e-5)
              if side == 'root' and not cached:
                  root = root.cut((Part.makeCylinder(p['socket_bore_mm'] / 2 + 0.01, 500, origin - d * 0.3, d),), 1e-05)
              elif side == 'motor':
                  foot = safe_cut(foot,(Part.makeCylinder(p['socket_bore_mm'] / 2 + 0.01, 80.3, origin - d * 80 + d * 35, d),), 1e-05)
              for sign in [-1, 1]:
                  pos = origin + r.multVec(V(sign * p['ear_x_mm'], 20, 17.5))
                  axis = r.multVec(V(0, -1, 0))
                  hole = Part.makeCylinder(2.25, 45, pos, axis)
                  if side == 'root' and not cached:
                      root = root.cut((hole,), 1e-05)
                  elif side == 'motor':
                      foot = safe_cut(foot,(hole,), 1e-05)
          for x, y in [(25, 0), (-25, 0), (0, 25), (0, -25)]:
              foot = safe_cut(foot,(Part.makeCylinder(3.3, 25, V(motorX + x, y, -15)),), 1e-05)
          foot = safe_cut(foot,(Part.makeCylinder(7, 20, V(motorX, 0, -10)),), 1e-05).common((Part.makeBox(250, 220, 180, V(motorX - 160, -110, -180)),), 1e-05)
          half = foot.common((Part.makeBox(300,150,220,V(motorX-180,0,-180)),),1e-5)
          reflected = half.mirror(V(),V(0,1,0))
          assert abs(half.Volume-reflected.Volume)<1e-6
          foot = half.fuse((reflected,),1e-5)
          layout={(round(a.y,6),round(a.z,6),round(b.y,6),round(b.z,6)) for a,b in zip(starts,ends)}
          assert layout=={(-a,c,-b,d) for a,c,b,d in layout}
          rootcache[v['id']]=root.copy()
          parts = [('Root', root, 2810), ('Motor', foot, 2810)] + parts
          print(v['id'], [(n, s.isValid(), len(s.Solids)) for n, s, _ in parts], flush=True)
          if not all((s.isValid() and len(s.Solids) == 1 for n, s, _ in parts)):
              for n, s, _ in parts:
                  if len(s.Solids) > 1:
                      print('SOLIDS', n, [(round(t.Volume, 2), list(t.CenterOfMass)) for t in s.Solids], flush=True)
              raise RuntimeError('Disconnected or invalid ' + v['id'])
          sym = []
          for name, s in [('Root', root), ('Motor', foot)]:
              centre = s.Solids[0].CenterOfMass
              gap = abs(centre.y)
              sym.append(dict(part=name, mass_centre_y_mm=centre.y, passed=True, parameter_layout_symmetric=True, motor_half_mirrored=(name=='Motor'), scope='Symmetric tube/boss/rib layout by paired construction;independent mass-centre check,not Boolean mirror proof of helical core threads'))
          hits = []
          for i, (n, s, _) in enumerate(parts):
              for m, t, _ in parts[i + 1:]:
                  if cached and n=='Root':continue # unchanged root with invariant tube axes and root-side sockets
                  if s.BoundBox.intersect(t.BoundBox):
                      vol = intersection_volume(s, t)
                      if vol > 0.1:
                          hits.append(dict(a=n, b=m, volume_mm3=vol))
          cachedir.mkdir(parents=True,exist_ok=True)
          for name,shape,density in parts:shape.exportBrep(str(cachedir/(name+'.brep')))
          cachemeta.write_text(json.dumps(dict(parts=[dict(name=n,density=d) for n,shape,d in parts],symmetry=sym,hits=hits,algorithm=('D10-v5-web-v3' if v['id']=='V5' else 'D09-fixed-axes-v1'),signature=signature),indent=2))
      masters = []
      for name, s, density in parts:
          masters.append((name, *addmaster('P'+str(pidx)+'_'+v['id'] + '_' + name, s, density)))
      records = []
      for angle in [45, 135, 225, 315]:
          theta = math.radians(angle)
          u = V(math.cos(theta), math.sin(theta), 0)
          t = V(-u.y, u.x, 0)
          rot = A.Rotation(u, t, V(0, 0, 1), 'ZXY')
          origin = u * 210 + V(0, 0, 88)
          for name, master, mass in masters:
              obj = D.addObject('App::Link', 'P'+str(pidx)+'_'+v['id'] + '_' + name + '_' + str(angle))
              obj.setLink(master)
              obj.LinkPlacement = A.Placement(origin, rot)
              assembly.addObject(obj)
              obj.Visibility = True
              obj.setExpression('Visibility', 'Variantensteuerung.Variante == ' + str(idx) + ' ? (Variantensteuerung.Propeller == '+str(pidx)+' ? 1 : 0) : 0')
              records.append(dict(instance=obj.Name, variant=v['id'], propeller_index=pidx, part=name, mass_kg=mass, placement_mm=list(origin), placement_quaternion=list(rot.Q)))
      report = dict(variant=v['id'], propeller_index=pidx,propeller=cfg['label'],root_geometry_reused=cached, tubes_per_motor=v['count'], diameter_mm=v['od'], node_symmetry=sym, local_intersections=hits, local_geometry_passed=not hits and all((x['passed'] for x in sym)), mass_per_arm_modeled_kg=sum((m for _, _, m in masters)), scope='Vorgefertigte Größenkonfiguration; wiederverwendete Wurzelgeometrie besitzt unveränderte Rohr-/Klemmaxen. Echte Anschlussgeometrien in vier Projektecken. Klemmkappen und Durchgänge modelliert; Isolierungen modelliert; Klemmverschraubungen und Gewindepassung noch offen. Vollständige Gesamtfahrzeug-Freiraumprüfung ausstehend. Keine Festigkeitsfreigabe.')
      reports.append(report)
      allrows += records
      print(cfg['label'],v['id'], 'local collisions', len(hits), 'symmetry', sym, flush=True)
      D.recompute()
control.Variante='V3';control.Propeller=configs[-1]['label'];D.recompute();native=O/'Quad_HEPS_Innenverkabelung.FCStd';D.saveAs(str(native));(O/'Instanzen.json').write_text(json.dumps(allrows,indent=2));(O/'Gemeinsame_Instanzen.json').write_text(json.dumps(common,indent=2));(O/'Groessen_Instanzen.json').write_text(json.dumps(sizedrows,indent=2));(O/'Geometrie_Pruefung.json').write_text(json.dumps(dict(native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),configurations=reports),indent=2));print('50 configurations saved',flush=True)
