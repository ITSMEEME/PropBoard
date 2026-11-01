#!/usr/bin/env python3
import json
from pathlib import Path
from zuschnitt import plan
H=Path(__file__).resolve().parent;d=json.loads((H/'Ausgabe/CFK_Beschaffung.json').read_text());seen=[]
for b in d['bins']:
    assert b['remaining_mm']>=-1e-8
    assert b['used_mm']+2*d['end_trim_each_mm']<=d['stock_length_mm']+1e-8
    assert abs(sum(c['planned_cut_mm']+d['kerf_per_cut_mm'] for c in b['cuts'])-b['used_mm'])<1e-7
    for c in b['cuts']:
        seen.append(c['id']);assert c['planned_cut_mm']>=c['length_mm']-1e-8
        assert c['engagement_each_end_mm']==30
assert len(seen)==len(set(seen))==d['cut_count']
assert d['tube_cost_including_VAT_EUR']==round(d['purchased_stock_count']*45.02,2)
try:plan([dict(id='invalid',length_mm=1000)],1000,2,5)
except ValueError:pass
else:raise AssertionError('Overlength with trim/kerf accepted')
print('CFK cut plan: all cuts unique; stock/kerf/trim/cost and overlength rejection PASS')
