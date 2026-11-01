#!/usr/bin/env python3
"""Consolidate split bearing CAD bodies into complete purchasing families."""
import collections,csv,json
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
def main():
    types=json.loads((O/'Teile.json').read_text());rows=[]
    byid={t['id']:t for t in types};used=set()
    for size in ['6','20','60']:
        ids=['STD-GE'+size+'-INNEN','STD-GE'+size+'-AUSSEN']
        present=[byid[i] for i in ids if i in byid]
        if not present:continue
        assert len(present)==2 and present[0]['count']==present[1]['count']
        used.update(ids)
        rows.append(dict(familie='GE'+size+('E' if size=='6' else 'ES'),menge=present[0]['count'],einheit='komplettes Gelenklager',cad_ids=', '.join(ids),anforderung=present[0]['features'],status='Lieferzeichnung, Tragzahlen und Freigabe offen'))
    for family,ids in [('Gelenkkopf M6/Ø6',['STD-GELENKKOPF6','STD-GELENKKUGEL6']),('Gelenkkopf M8/Ø8',['STD-M8-ZUGSTANGENKOPF','STD-M8-GELENKKUGEL'])]:
        present=[byid[i] for i in ids if i in byid]
        assert len(present)==2 and present[0]['count']==present[1]['count']
        used.update(ids)
        rows.append(dict(familie=family,menge=present[0]['count'],einheit='kompletter Gelenkkopf inklusive Kugel',cad_ids=', '.join(ids),anforderung=present[0]['features'],status='RH/LH-Ausführung, Lieferkontur und Tragzahlen prüfen'))
    # Other references retain their actual complete-body quantities.
    for t in types:
        if t['id'] in used or not t['reference']:continue
        rows.append(dict(familie=t['name'],menge=t['count'],einheit='CAD-Referenz; Umfang prüfen',cad_ids=t['id'],anforderung=t['features'],status='KEINE BESTELLLISTE: Baugruppenzugehörigkeit und konkretes Lieferprodukt prüfen'))
    target=O/'Beschaffungsfamilien.csv'
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
    with (O/'Stueckliste.csv').open(encoding='utf-8-sig') as f:bom=list(csv.DictReader(f,delimiter=';'))
    variants=collections.Counter((r['id'],r['step']) for r in bom if not byid[r['id']]['reference'])
    with (O/'RFQ_Fertigungsvarianten.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','step','menge','werkstoff','verfahren','status'],delimiter=';');w.writeheader()
        for (id,step),count in sorted(variants.items()):w.writerow(dict(id=id,step=step,menge=count,werkstoff=byid[id]['material'],verfahren=byid[id]['process'],status='RFQ; keine Fertigungsfreigabe'))
    print(f'{len(rows)} Beschaffungsreferenzen; GE-Lagerringe zu kompletten Lagern zusammengeführt')
if __name__=='__main__':main()
