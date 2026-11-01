"""Native FreeCAD FeaturePython proxy. Load using P12_oeffnen.FCMacro."""
import json,hashlib,re
from parameter_schema import SCHEMA,defaults,validate
from geometrie import build
COLORS={'frame':(.56,.62,.67),'motor':(.92,.68,.34),'drive':(.36,.77,.8),'upper':(.15,.57,.8),'lower':(.86,.51,.27),'column':(.59,.77,.47)}
def fingerprint(p):return hashlib.sha256(('P12_GEOMETRIE_2026_11_01_BEFESTIGUNGEN_1\n'+json.dumps(p,sort_keys=True)).encode()).hexdigest()
def current(obj):
    return {k:int(round(getattr(obj,'p_'+k))) if s['unit']=='int' and float(getattr(obj,'p_'+k)).is_integer() else float(getattr(obj,'p_'+k)) for k,s in SCHEMA.items()}

def color(id,name):
    if id=='REF-FLUEGEL':return COLORS['upper' if name.startswith('Oben') else 'lower']
    if id=='REF-MN1330':return COLORS['motor']
    if id.startswith('CFK-ROHR'):return (.12,.15,.18)
    if id in ['P12-002','P12-003','P12-004','P12-005']:return COLORS['drive']
    if id in ['P12-010','P12-011']:return COLORS['column']
    return COLORS['frame']
class Model:
    def __init__(self,obj):obj.Proxy=self;self._building=False
    def dumps(self):return None
    def loads(self,state):self._building=False
    def onDocumentRestored(self,obj):self._building=False
    def execute(self,obj):
        if getattr(self,'_building',False):return
        self._building=True
        try:
            p=current(obj);h=fingerprint(p)
            if obj.LastValidHash==h and any('P12Key' in o.PropertiesList for o in obj.Document.Objects) and all('Fertigungsvariante' in o.PropertiesList for o in obj.Document.Objects if 'P12Key' in o.PropertiesList):
                obj.Error='';obj.P12Status='GEOMETRIE_AKTUELL_NICHT_FREIGEGEBEN';return
            # Construct first: failed validation leaves last valid model untouched and clearly marked.
            materials=json.loads(obj.MaterialsJSON);parts,scene,q=build(p,materials)
            doc=obj.Document;existing={o.P12Key:o for o in doc.Objects if 'P12Key' in o.PropertiesList};keys=set()
            for row in scene:
                key=row['name'];keys.add(key);part=parts[row['id']];o=existing.get(key)
                if o is None:o=doc.addObject('Part::Feature','P12_'+re.sub('[^A-Za-z0-9_]','_',key))
                o.Label=key.replace('_',' ');o.Shape=row['shape']
                fields={'P12Key':key,'BauteilID':row['id'],'Fertigungsvariante':row['variant'],'Werkstoff':part['material'],'Fertigung':part['process'],'Fertigungsmerkmale':part['features'],'Offene_Punkte':part['open'],'Status':'PROFILREFERENZ' if row['context'] else ('KAUFTEILKONTUR' if part['reference'] else 'FERTIGUNGSENTWURF'),'Freigabe':'NICHT_FREIGEGEBEN'}
                for k,v in fields.items():
                    if k not in o.PropertiesList:o.addProperty('App::PropertyString',k,'P12')
                    setattr(o,k,v);o.setEditorMode(k,1)
                if 'Parameterquelle' not in o.PropertiesList:o.addProperty('App::PropertyLink','Parameterquelle','P12')
                o.Parameterquelle=obj;o.setEditorMode('Parameterquelle',1)
                group=doc.getObject('Geometriekontext' if row['context'] else ('Kaufteilkonturen' if part['reference'] else 'Fertigungsteile'));group.addObject(o)
                if o.ViewObject:o.ViewObject.ShapeColor=color(row['id'],key)
            for key,o in existing.items():
                if key not in keys:doc.removeObject(o.Name)
            obj.LastValidHash=h;obj.LastValidParameters=json.dumps(p,sort_keys=True);obj.DerivedJSON=json.dumps(q,ensure_ascii=False);obj.P12Status='GEOMETRIE_AKTUELL_NICHT_FREIGEGEBEN';obj.Error='';obj.InstanceCount=len(scene)
            derived=doc.getObject('Abgeleitet');derived.clearAll();derived.set('A1','Abgeleitete Größe');derived.set('B1','Wert (mm sofern nicht benannt)')
            for i,(k,v) in enumerate(((k,v) for k,v in q.items() if k not in p),2):
                derived.set('A'+str(i),k);derived.set('B'+str(i),str(v) if isinstance(v,(int,float)) else ("'"+str(len(v))+' Datensätze; siehe Export' if isinstance(v,list) and v and isinstance(v[0],dict) else "'"+str(v)))
            self.parts=parts;self.scene=scene
        except Exception as e:
            obj.P12Status='UNGUELTIG_LETZTE_GUELTIGE_GEOMETRIE_ANGEZEIGT';obj.Error=str(e)
            raise
        finally:self._building=False

def create(doc,p,materials):
    sheet=doc.addObject('Spreadsheet::Sheet','Parameter');sheet.Label='Parameter — hier ändern';sheet.set('A1','Parameter');sheet.set('B1','Wert');sheet.set('C1','Einheit');sheet.set('D1','Gruppe');sheet.set('E1','Zulässiger Einzelbereich')
    sheet.setColumnWidth('A',245);sheet.setColumnWidth('B',110);sheet.setColumnWidth('C',70);sheet.setColumnWidth('D',145);sheet.setColumnWidth('E',145)
    for i,(key,s) in enumerate(SCHEMA.items(),2):
        sheet.set('A'+str(i),key);sheet.set('B'+str(i),str(p[key]));sheet.setAlias('B'+str(i),key);sheet.set('C'+str(i),s['unit']);sheet.set('D'+str(i),s['group']);sheet.set('E'+str(i),"'"+str(s['minimum'])+' bis '+str(s['maximum']))
        sheet.setBackground('B'+str(i),(1.,.96,.75))
    for key in ['Fertigungsteile','Kaufteilkonturen','Geometriekontext']:doc.addObject('App::DocumentObjectGroup',key)
    doc.addObject('Spreadsheet::Sheet','Abgeleitet')
    model=doc.addObject('App::FeaturePython','P12_Modell');model.Label='P12 Parametrisches Modell — Status prüfen';Model(model)
    for k,s in SCHEMA.items():
        model.addProperty('App::PropertyFloat','p_'+k,s['group'],f"Quelle: Parameter.{k}; {s['unit']}");model.setExpression('p_'+k,'Parameter.'+k);model.setEditorMode('p_'+k,1)
    for key in ['LastValidHash','LastValidParameters','DerivedJSON','P12Status','Error','MaterialsJSON']:model.addProperty('App::PropertyString',key,'Modellstatus')
    model.addProperty('App::PropertyInteger','InstanceCount','Modellstatus');model.MaterialsJSON=json.dumps(materials);model.setEditorMode('MaterialsJSON',1)
    return model

def set_values(doc,values):
    for key,value in values.items():
        if key not in SCHEMA:raise ValueError('Unbekannter Parameter: '+key)
        doc.getObject('Parameter').set(key,str(value))
    doc.recompute()
    model=doc.getObject('P12_Modell')
    if model.Error:raise ValueError(model.Error)
    return json.loads(model.LastValidParameters)
