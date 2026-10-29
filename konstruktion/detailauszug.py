#!/usr/bin/python3
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as App,Part
HERE=Path(__file__).resolve().parent
source=App.openDocument(str(HERE/'02_Fuehrung_Antrieb_Detail.FCStd'));source.recompute()
d=App.newDocument('Schlitten_Detailauszug');objects=[]
fixed=d.addObject('App::DocumentObjectGroup','Stationaerer_Stator_ausblendbar')
moving=d.addObject('App::DocumentObjectGroup','Bewegter_Schlitten')
for o in source.Objects:
    if not hasattr(o,'BauteilID') or o.Shape.BoundBox.YMin<294:continue
    n=d.addObject('Part::Feature',o.Name);n.Shape=o.Shape.copy()
    for key in ['BauteilID','Material_Annahme','Prozess_Referenz','Bemerkung','Freigabe','Referenzkoerper']:
        n.addProperty('App::PropertyString',key);setattr(n,key,getattr(o,key))
    n.addProperty('App::PropertyString','Quellobjekt');n.Quellobjekt='02_Fuehrung_Antrieb_Detail.FCStd:'+o.Name
    (fixed if o.BauteilID in ['FUEHR-C-PROBE','FUEHR-F-PROBE','LM-SPULE-REF'] else moving).addObject(n)
    objects.append(n)
axis=d.addObject('Part::Cylinder','Wellenabschnitt_REF');axis.Radius=4;axis.Height=45
axis.Placement=App.Placement(App.Vector(0,295,0),App.Rotation(App.Vector(0,0,1),App.Vector(0,1,0)))
for key,value in {'BauteilID':'PITCH-W-REF','Material_Annahme':'Welle TBD','Referenzkoerper':'JA','Freigabe':'VOR_ENTWURF',
                  'Bemerkung':'Gekuerzter Betrachtungsabschnitt, kein neuer Fertigungsstand'}.items():
    axis.addProperty('App::PropertyString',key);setattr(axis,key,value)
objects.append(axis)
moving.addObject(axis)
d.recompute();assert all(o.Shape.isValid() for o in objects)
path=HERE/'02a_Schlitten_Detail.FCStd';d.saveAs(str(path));Part.export(objects,str(HERE/'02a_Schlitten_Detail.step'))
App.closeDocument(d.Name);opened=App.openDocument(str(path));opened.recompute()
assert all(o.Shape.isValid() for o in opened.Objects if hasattr(o,'Shape'))
(HERE/'Detailauszug_Pruefung.json').write_text(json.dumps({'objects':len(objects),'saved_reopened':True,'manufacturing_release':False},indent=2))
print('Schlittenauszug:',len(objects),'Koerper')
