#!/usr/bin/env python3
"""Summarize actual positive BRep intersections without suppressing them."""
import argparse,collections,csv,json
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');a=ap.parse_args();o=a.output
    with (o/'Stueckliste.csv').open(encoding='utf-8-sig') as f:ids={r['instance']:r['id'] for r in csv.DictReader(f,delimiter=';')}
    hits=json.loads((o/'Kollisionen.json').read_text());groups=collections.defaultdict(list)
    for hit in hits:groups[tuple(sorted((ids[hit['a']],ids[hit['b']])))].append(hit)
    result=[dict(ids=list(key),count=len(values),maximum_volume_mm3=max(v['volume_mm3'] for v in values),example=values[0]) for key,values in groups.items()]
    result.sort(key=lambda r:(-r['count'],-r['maximum_volume_mm3']))
    (o/'Kollisionsgruppen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    for r in result:print(r['count'],round(r['maximum_volume_mm3'],3),' / '.join(r['ids']),r['example']['a'],r['example']['b'],sep=' | ')
if __name__=='__main__':main()
