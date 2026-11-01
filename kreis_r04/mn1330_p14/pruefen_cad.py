"""Audit generated artifacts independently of the builder; never grants release."""
import sys,json,hashlib,time,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part

def main():
    global O
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['step','collision'],default='collision',nargs='?');ap.add_argument('--output',type=Path,default=O);ap.add_argument('--quick',action='store_true');args=ap.parse_args();mode=args.mode;O=args.output
    sha=hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest()
    if mode=='step':
        native=A.openDocument(str(O/'P14_MN1330_Leichtbau.FCStd'));scene=json.loads((O/'Szenengraph.json').read_text());q=json.loads((O/'Abgeleitet.json').read_text())
        results=[]
        for t in json.loads((O/'Teile.json').read_text()):
            paths=list(O.glob('STEP_*/'+t['id']+'.step'))
            # A stale inactive type must not be treated as a generated active part.
            assert len(paths)==1,(t['id'],paths)
            s=Part.read(str(paths[0]));err=abs(s.Volume/t['volume_mm3']-1)
            r=dict(id=t['id'],valid=s.isValid(),solids=len(s.Solids),relative_volume_error=err)
            r['pass']=r['valid'] and r['solids']==1 and err<1e-5;r['pass_basis']='valid solid and relative volume<1e-5'
            if r['valid'] and r['solids']==1 and err>=1e-5:
                # OCC's adaptive mass integration differs on the same trimmed
                # sphere/complex cut after STEP reparameterisation. Verify the
                # actual material domains rather than weakening volume limits.
                row=next(rr for rr in scene if rr['part']==t['id']);n=native.getObject(row['native_object']).Shape.copy();m=A.Matrix()
                for ii in range(4):
                    for jj in range(4):setattr(m,'A'+str(ii+1)+str(jj+1),row['neutral_transform'][4*ii+jj])
                world=A.Placement(A.Vector(*q['unit_centres_mm'][row['unit']]),A.Rotation())
                if row['sign']<0:world=world.multiply(A.Placement(A.Vector(),A.Rotation(A.Vector(0,1,0),180)))
                world=world.multiply(A.Placement(m));n.Placement=world.inverse().multiply(n.Placement)
                a,b=n.cut(s),s.cut(n);diff=abs(a.Volume)+abs(b.Volume)
                bb=max(abs(getattr(n.BoundBox,k)-getattr(s.BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])
                r['bidirectional_cut_difference_mm3']=diff;r['bbox_max_difference_mm']=bb;r['difference_shapes_valid']=a.isValid() and b.isValid()
                r['pass']=r['difference_shapes_valid'] and diff<=.1 and bb<1e-5
                r['pass_basis']='bidirectional material difference<=0.1mm3 and bbox agreement<1e-5mm; numerical volume integration differs'
            results.append(r)
        aggregate=O/'P14_MN1330_Leichtbau.step';agg=None
        if aggregate.exists():
            s=Part.read(str(aggregate));objects=[o for o in native.Objects if hasattr(o,'Shape') and o.Shape.Solids]
            vol=sum(o.Shape.Volume for o in objects)
            agg=dict(valid=s.isValid(),solids=len(s.Solids),expected_solids=len(objects),relative_volume_error=abs(s.Volume/vol-1))
            agg['pass']=agg['valid'] and agg['solids']==len(objects) and agg['relative_volume_error']<1e-5
        assert sha==hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest(),'Native changed during check'
        out=dict(native_sha256=sha,all_active_single_parts_pass=all(r['pass'] for r in results),parts=results,aggregate=agg)
        (O/'STEP_Pruefung.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True);return
    scene=json.loads((O/'Szenengraph.json').read_text());d=A.openDocument(str(O/'P14_MN1330_Leichtbau.FCStd'))
    if args.quick:scene=[r for r in scene if r['sign']==1 and r['unit']==0 and r['blade_index'] in [-1,0] and r['servo_index'] in [-1,0]]
    objects=[(r,d.getObject(r['native_object']).Shape) for r in scene]
    failures=[];tested=0;exact=0;cache={};start=time.time()
    for i,(a,sa) in enumerate(objects):
        for b,sb in objects[i+1:]:
            if not sa.BoundBox.intersect(sb.BoundBox):continue
            tested+=1
            try:
                # Every occurrence of a part ID is the same prototype under a
                # rigid placement. Cache only an identical relative transform;
                # mirrored pods use a proper180deg rotation, not a reflection.
                m=sa.Placement.inverse().multiply(sb.Placement).toMatrix()
                key=(a['part'],b['part'],tuple(round(getattr(m,'A'+str(ii)+str(jj)),8) for ii in range(1,4) for jj in range(1,5)))
                if key in cache:v=cache[key]
                else:v=abs(sa.common(sb).Volume);cache[key]=v;exact+=1
                if v>.1:failures.append(dict(a=a['name'],b=b['name'],part_a=a['part'],part_b=b['part'],volume_mm3=v))
            except Exception as e:failures.append(dict(a=a['name'],b=b['name'],error=str(e)))
        if i%40==0:
            print('collision',i,len(objects),len(failures),flush=True)
            (O/'Kollisionen_laufend.json').write_text(json.dumps(failures,indent=2))
    assert sha==hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest(),'Native changed during check'
    out=dict(native_sha256=sha,pose='neutral only; not a swept-clearance certificate',all_bodies=len(objects),bbox_pairs_tested=tested,exact_boolean_pairs=exact,identical_rigid_pair_cache_hits=tested-exact,cache_relative_transform_rounding_mm=1e-8,threshold_mm3=.1,overlaps=failures,open_count=len(failures),seconds=time.time()-start)
    (O/('Kollisionen_Sektor.json' if args.quick else 'Kollisionen.json')).write_text(json.dumps(out,indent=2,ensure_ascii=False));print('Done',len(failures),flush=True)
if __name__=='__main__':main()
