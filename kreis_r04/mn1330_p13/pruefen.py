#!/usr/bin/env python3
"""Check saved native geometry, interfaces, and actual volume intersections."""
import argparse,json,hashlib,sys,time
from pathlib import Path
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A
H=Path(__file__).resolve().parent

def intersections(items,progress=None,cache=None):
    shapes=[o.Shape for o in items];bounds=[s.BoundBox for s in shapes]
    cache={} if cache is None else cache
    fingerprints=[hashlib.sha256(s.exportBrepToString().encode()).hexdigest() for s in shapes]
    order=sorted(range(len(items)),key=lambda i:bounds[i].XMin);hits=[];checks=0
    for pos,i in enumerate(order):
        a=bounds[i]
        for j in order[pos+1:]:
            b=bounds[j]
            if b.XMin>=a.XMax-1e-8:break
            if b.YMin>=a.YMax-1e-8 or a.YMin>=b.YMax-1e-8 or b.ZMin>=a.ZMax-1e-8 or a.ZMin>=b.ZMax-1e-8:continue
            checks+=1
            key=':'.join(sorted((fingerprints[i],fingerprints[j])))
            if key not in cache:
                Path('/tmp/p13-current-pair.json').write_text(json.dumps(dict(a=items[i].P13Key,b=items[j].P13Key)))
                cache[key]=shapes[i].common(shapes[j]).Volume
            v=cache[key]
            if v>.01:hits.append(dict(a=items[i].P13Key,b=items[j].P13Key,volume_mm3=v))
        if progress and pos%100==0:progress(pos,len(items),checks,hits)
    return hits,checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'Ausgabe');a=ap.parse_args();out=a.output
    doc=A.openDocument(str(out/'P13_Mechanik.FCStd'));items=[o for o in doc.Objects if 'P13Key' in o.PropertiesList]
    keys=[o.P13Key for o in items];assert len(keys)==len(set(keys))
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.Volume>0 for o in items)
    boxes=[dict(name=o.P13Key,id=o.BauteilID,xmin=o.Shape.BoundBox.XMin,xmax=o.Shape.BoundBox.XMax,ymin=o.Shape.BoundBox.YMin,ymax=o.Shape.BoundBox.YMax,zmin=o.Shape.BoundBox.ZMin,zmax=o.Shape.BoundBox.ZMax) for o in items]
    extreme={k:sorted(boxes,key=lambda r:r[k],reverse=k.endswith('max'))[:4] for k in ['xmin','xmax','ymin','ymax','zmin','zmax']}
    (out/'Geometrie_Grenzen.json').write_text(json.dumps(extreme,indent=2,ensure_ascii=False)+'\n')
    print('Extremkörper: '+json.dumps({k:v[0] for k,v in extreme.items()},ensure_ascii=False),flush=True)
    byname={o.P13Key:o for o in items};mirrored=0
    for name,o in byname.items():
        if not name.startswith(('Oben_Blatt','Oben_Fachwerk')):continue
        counterpart=byname['Unten'+name[4:]];a=o.Shape.BoundBox;b=counterpart.Shape.BoundBox
        assert max(abs(a.XMin-b.XMin),abs(a.XMax-b.XMax),abs(a.YMin-b.YMin),abs(a.YMax-b.YMax),abs(a.ZMin+b.ZMax),abs(a.ZMax+b.ZMin))<1e-6,(name,'Spiegellage')
        assert abs(o.Shape.Volume-counterpart.Shape.Volume)<max(1e-5,o.Shape.Volume*1e-9),(name,'Spiegelvolumen')
        mirrored+=1
    print(f'{mirrored} Rotorbauteilpaare: Weltkoordinaten-Spiegellage und Volumen bestanden',flush=True)
    mates=json.loads((out/'Schnittstellen.json').read_text());missing=[r for r in mates if r['a'] not in keys or r['b'] not in keys]
    (out/'Schnittstellen_Fehler.json').write_text(json.dumps(missing,indent=2,ensure_ascii=False)+'\n')
    cp=Path('/tmp/p13-brep-pair-cache.json');cache=json.loads(cp.read_text()) if cp.exists() else {}
    def progress(pos,n,c,h):
        print(f'{pos}/{n}: {c} BRep-Paare, {len(h)} Überschneidungen',flush=True)
        cp.write_text(json.dumps(cache,separators=(',',':')))
        (out/'Kollisionen_Zwischenstand.json').write_text(json.dumps(h,indent=2,ensure_ascii=False)+'\n')
    hits,checks=intersections(items,progress,cache)
    cp.write_text(json.dumps(cache,separators=(',',':')))
    (out/'Kollisionen.json').write_text(json.dumps(hits,indent=2,ensure_ascii=False)+'\n')
    report=json.loads((out/'Pruefung.json').read_text());report.update(collision_status='BESTANDEN' if not hits else 'KOLLISIONEN_OFFEN',overlap_count=len(hits),interface_reference_errors=len(missing),brep_pairs_checked=checks,mirrored_rotor_pairs_checked=mirrored,checked_native_sha256=hashlib.sha256((out/'P13_Mechanik.FCStd').read_bytes()).hexdigest())
    (out/'Pruefung.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if hits or missing:raise SystemExit(1)
if __name__=='__main__':main()
