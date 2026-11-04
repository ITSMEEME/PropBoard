"""Read exact saved BREP/placements from FCStd, without restoring25000 GUI links."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,tempfile,hashlib,json
import FreeCAD as A,Part
class Native:
 def __init__(self,path):
  self.path=Path(path);self.z=zipfile.ZipFile(path);self.objects={};self.cache={};self.tmp=tempfile.TemporaryDirectory(prefix='quad-native-')
  component_file=self.path.parents[2]/'quad_r380_d12/Ausgabe/Viewer_Komponenten.json'
  self.components={r['instance']:r for r in json.loads(component_file.read_text())} if component_file.exists() else {}
  wanted={'Shape','LinkedObject','Placement','LinkPlacement','ExpressionEngine'}
  for _,e in ET.iterparse(self.z.open('Document.xml'),events=['end']):
   if e.tag=='Object':
    ps=e.find('Properties')
    if ps is not None:self.objects[e.attrib['name']]={p.attrib['name']:p for p in ps if p.attrib.get('name') in wanted}
    e.clear()
 def prop(self,name,prop):return self.objects[name].get(prop)
 def linked(self,name):return self.prop(name,'LinkedObject').find('XLink').attrib['name']
 def shape(self,name):
  if name not in self.cache:
   p=self.prop(name,'Shape')
   if p is None:return self.instance(name)
   p=p.find('Part').attrib['file'];f=Path(self.tmp.name)/(hashlib.sha256(p.encode()).hexdigest()+'.brep');f.write_bytes(self.z.read(p));s=Part.Shape();s.read(str(f));self.cache[name]=s
  return self.cache[name].copy()
 def placement(self,name):
  p=self.prop(name,'LinkPlacement');p=p if p is not None else self.prop(name,'Placement');a=p.find('PropertyPlacement').attrib
  return A.Placement(A.Vector(*(float(a['P'+x]) for x in 'xyz')),A.Rotation(*(float(a['Q'+str(i)]) for i in range(4))))
 def instance(self,name):
  s=self.shape(self.linked(name));s.Placement=self.placement(name).multiply(s.Placement);return s
 def expressions(self,name):return [e.attrib for e in self.prop(name,'ExpressionEngine').find('ExpressionEngine')]

 def row(self,r):
  if r['instance'] in self.objects:return self.instance(r['instance'])
  if r['instance'] in self.components:
   original=self.components[r['instance']];s=self.shape(original['id']);parent=r['instance'].rsplit('_',1)[0];s.Placement=self.placement(parent).multiply(s.Placement);return s
  s=self.shape(r['id']);pl=A.Placement(A.Vector(*r['placement_mm']),A.Rotation(*r['placement_quaternion']));s.Placement=pl.multiply(s.Placement);return s
