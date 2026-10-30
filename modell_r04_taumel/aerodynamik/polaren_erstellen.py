#!/usr/bin/env python3
"""Calculated XFOIL polars of actual CAD geometry. Never labelled measurements."""
import concurrent.futures,hashlib,json,math,os,subprocess,tempfile,csv
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];BIN=Path(os.environ.get('XFOIL_BIN',str(ROOT/'.cfd-tools/xfoil/xfoil')));OUT=H/'Ausgabe';OUT.mkdir(exist_ok=True)

def one(re,ncrit,panels=160,kind='cad'):
    name=f'{kind}_Re{re}_N{ncrit}_P{panels}'
    with tempfile.TemporaryDirectory(prefix='h01-xfoil-') as td:
        p=Path(td);(p/'foil.dat').write_bytes((H/'H01_CAD_Profil.dat').read_bytes())
        setup='LOAD foil.dat' if kind=='cad' else 'NACA 0012'
        commands=f'PLOP\nG\n\n{setup}\nPPAR\nN {panels}\n\n\nPANE\nOPER\nVISC {re}\nMACH 0.08\nVPAR\nN {ncrit}\n\nITER 220\nPACC\npolar.dat\n\nASEQ 0 16 1\nINIT\nASEQ -1 -6 -1\nPACC\n\nQUIT\n'
        try:r=subprocess.run([str(BIN)],input=commands,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=p,timeout=40);log=r.stdout;ret=r.returncode
        except subprocess.TimeoutExpired as e:log=str(e.stdout);ret='TIMEOUT'
        rows=[]
        if (p/'polar.dat').exists():
            raw=(p/'polar.dat').read_text();(OUT/(name+'.polar')).write_text(raw)
            for line in raw.splitlines():
                vals=line.split()
                if len(vals)<7:continue
                try:v=list(map(float,vals[:7]))
                except ValueError:continue
                if not all(map(math.isfinite,v)) or not (-6<=v[0]<=16 and 0<v[2]<2 and abs(v[1])<3):continue
                rows.append(dict(alpha=v[0],cl=v[1],cd=v[2],cdp=v[3],cm=v[4],xtr_upper=v[5],xtr_lower=v[6]))
        (OUT/(name+'.log')).write_text(log)
        return dict(re=re,ncrit=ncrit,panels=panels,kind=kind,exit_code=ret,rows=sorted(rows,key=lambda r:r['alpha']),missing_alpha_deg=[a for a in range(-6,17) if a not in [r['alpha'] for r in rows]],convergence_failure_messages=log.count('Convergence failed'))

if __name__=='__main__':
    jobs=[(re,n) for re in (20000,40000,60000,80000,100000,140000,180000) for n in (4,9)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:tables=list(pool.map(lambda p:one(*p),jobs))
    reference=one(100000,9,160,'naca');dense=one(100000,4,240)
    def at(t,a):return next((r for r in t['rows'] if r['alpha']==a),None)
    nom=next(t for t in tables if t['re']==100000 and t['ncrit']==4);a=at(nom,4);b=at(dense,4);z=at(reference,0)
    checks={'naca_zero_lift_symmetry_pass':z is not None and abs(z['cl'])<.005,'cad_panel_refinement_alpha4_pass':a is not None and b is not None and abs(a['cl']-b['cl'])<.05 and abs(a['cd']-b['cd'])<.005,'cad_panel_refinement_delta_cl':None if not a or not b else a['cl']-b['cl'],'cad_panel_refinement_delta_cd':None if not a or not b else a['cd']-b['cd']}
    common=[(at(nom,a),at(dense,a)) for a in range(-4,9) if at(nom,a) and at(dense,a)]
    checks['panel_refinement_alpha_range_deg']=[-4,8]
    checks['panel_refinement_max_delta_cl']=max(abs(x['cl']-y['cl']) for x,y in common)
    checks['panel_refinement_max_delta_cd']=max(abs(x['cd']-y['cd']) for x,y in common)
    checks['output_precision_note']='CL printed to 4 decimals, CD to 5 decimals; zero delta at alpha4 is rounding, not exact accuracy'
    assert checks['naca_zero_lift_symmetry_pass'] and checks['cad_panel_refinement_alpha4_pass'],checks
    out=dict(status='COMPUTED_XFOIL_POLARS_NOT_MEASURED_OR_FULL_ROTOR_CFD',solver='XFOIL 6.99, locally built double precision release',solver_sha256=hashlib.sha256(BIN.read_bytes()).hexdigest(),source_url='https://deb.debian.org/debian/pool/main/x/xfoil/xfoil_6.99.dfsg+1.orig.tar.gz',source_sha256=hashlib.sha256((ROOT/'.cfd-tools/downloads/xfoil-source.tar.gz').read_bytes()).hexdigest(),profile=json.loads((H/'Profilherkunft.json').read_text()),mach=.08,checks=checks,tables=tables,reference=reference,panel_refinement=dense,limitations=['2D steady boundary-layer/panel calculation, not CFD of coaxial vehicle','Ncrit 4/9 are sensitivity assumptions, not measured surface roughness or turbulence','Converged points only; missing points are not zero or silently extrapolated','Printed profile/surface, transition, dynamic stall, finite rotor effects and wake still require experiments'])
    (OUT/'Polaren.json').write_text(json.dumps(out,indent=2));(OUT/'Polaren.js').write_text('globalThis.H01_POLARS='+json.dumps(out,separators=(',',':'))+';\n')
    with (OUT/'Polaren.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['re','Ncrit','alpha_deg','CL','CD','CM'])
        for t in tables:
            for r in t['rows']:w.writerow([t['re'],t['ncrit'],r['alpha'],r['cl'],r['cd'],r['cm']])
    print('XFOIL tables',len(tables),'converged points',sum(len(t['rows']) for t in tables),'of',len(jobs)*23,'checks',checks)
