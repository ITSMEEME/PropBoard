"""Conservative First-Fit-Decreasing stock plan, kerf and end trims included."""
import csv,json,math

def plan(cuts,stock,kerf,trim):
    bins=[];usable=stock-2*trim
    for cut in sorted(cuts,key=lambda x:x['length_mm'],reverse=True):
        # Rounded-up0.1mm cut length prevents an optimistic material plan.
        length=math.ceil((cut['length_mm']-1e-9)*10)/10
        if length+kerf>usable+1e-9:raise ValueError('Zuschnitt einschließlich Sägefuge überschreitet Nutzlänge')
        target=next((b for b in bins if b['used_mm']+length+kerf<=usable+1e-9),None)
        if target is None:target={'stock_id':len(bins)+1,'used_mm':0.,'cuts':[]};bins.append(target)
        target['used_mm']+=length+kerf;target['cuts'].append(cut|{'planned_cut_mm':length})
    for b in bins:b['remaining_mm']=usable-b['used_mm']
    return bins

def export_cut_plan(out,p,q):
    bins=plan(q['cfk_cut_list'],p['cfk_stock_length'],p['cfk_saw_kerf'],p['cfk_end_trim']);rows=[]
    for b in bins:
        for cut in b['cuts']:rows.append(dict(stock_id=b['stock_id'],part_id=cut['id'],cad_length_mm=cut['length_mm'],planned_cut_mm=cut['planned_cut_mm'],from_node=cut['from_node'],to_node=cut['to_node'],engagement_each_end_mm=cut['engagement_each_end_mm'],kerf_mm=p['cfk_saw_kerf']))
    with (out/'CFK_Zuschnitt.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
    data={'article':'CBU 2017 1005 TG','nominal_dimensions_mm':[20,17,1000],'OD_tolerance_mm':.2,'purchased_stock_count':len(bins),'cut_count':len(rows),'total_CAD_cut_length_mm':sum(c['length_mm'] for c in q['cfk_cut_list']),'price_per_stock_including_VAT_EUR':p['cfk_price'],'tube_cost_including_VAT_EUR':round(len(bins)*p['cfk_price'],2),'cost_excludes':['Knoten','Klemmen','Schrauben','Zwischenlagen','Bearbeitung','Versand'],'stock_length_mm':p['cfk_stock_length'],'end_trim_each_mm':p['cfk_end_trim'],'kerf_per_cut_mm':p['cfk_saw_kerf'],'algorithm':'First-fit decreasing, auf0.1mm aufgerundet, kein global minimaler Materialverbrauch bewiesen','bins':bins,'nominal_area_mm2':q['cfk_nominal_area_mm2'],'nominal_second_moment_mm4':q['cfk_nominal_I_mm4'],'laminate_properties':None,'structural_release':False}
    (out/'CFK_Beschaffung.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');(out/'CFK_Knotenanschluesse.json').write_text(json.dumps(q['cfk_nodes'],indent=2,ensure_ascii=False)+'\n')
