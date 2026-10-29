import csv,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=list(csv.DictReader((HERE/'Stueckliste_Instanzen.csv').open(encoding='utf-8-sig')))
groups={}
for r in rows:
    if r['Datei']!='00_PropBoard_Detail_Stehen.FCStd':continue
    key=(r['ID'],r['Material_Annahme'],r['Referenz'])
    groups[key]=groups.get(key,0)+1
with (HERE/'Stueckliste_Hauptbaugruppe_Familien.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['ID_Familie','Material_Annahme','Referenz','Instanzanzahl','Freigabe'])
    for key,n in sorted(groups.items()):w.writerow([*key,n,'VOR_ENTWURF_NICHT_BESTELLFERTIG'])
p=json.loads((HERE/'parameter.json').read_text())
with (HERE/'CFK_Zuschnitt_Referenz.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['ID','Anzahl_Hauptbaugruppe','Querschnitt_mm','Nennlaenge_mm','Bemerkung'])
    for row in [('CFK-L01',2,'40x40 Wand3',p['longeron_length_mm']),('CFK-Q01',3,'40x40 Wand3',p['crossbeam_length_mm']),
                ('CFK-S01',6,'D30/d24',400),('CFK-S02',6,'D16/d10',400)]:
        w.writerow([*row,'Laminat, Schnittzugabe, Endverstaerkung und Toleranz OFFEN'])
print('Familien und Referenzzuschnitte exportiert:',len(groups),'Familien')
