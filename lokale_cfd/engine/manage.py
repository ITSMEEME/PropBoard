#!/usr/bin/env python3
"""Portable local workflow. Docker is controlled by the user's launcher, never via a mounted socket."""
import argparse,csv,hashlib,json,math,os,random,re,shutil,time,tempfile
from pathlib import Path
import erstellen as G
from netzcheck import check as mesh_check
from auswerten import measure
ROOT=Path(__file__).resolve().parents[1];W=G.H
def read(p):return json.loads(Path(p).read_text())
def finite(v):
    if isinstance(v,float) and not math.isfinite(v):return None
    if isinstance(v,dict):return {k:finite(x) for k,x in v.items()}
    if isinstance(v,list):return [finite(x) for x in v]
    return v
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=p.parent,prefix='.'+p.name,delete=False) as f:f.write(json.dumps(v,indent=2,allow_nan=False)+'\n');tmp=Path(f.name)
    tmp.replace(p)
def profile():return read(ROOT/'profiles'/f'{os.environ.get("CFD_PROFILE","fullscale")}.json')
def hardware(p):
    r={'profile':p['name'],'target_mass_kg':p['target_mass_kg'],'target_mass_status':p['target_mass_status'],'data_source':p.get('hardware_data_source'),'blockers':[],'unknowns':[]}
    if 'battery' not in p:r['unknowns']=['Kein ausgewählter Direktantriebsmotor; elektrische Machbarkeit nicht bewiesen.'];return r
    b=p['battery'];m=p['motor'];R=p['reference']['diameterMm']/2000;area=math.pi*R*R;rho=p['air']['rho'];power=b['nominal_V']*b['continuous_A'];T=p['target_mass_kg']*9.81
    cells=round(b['full_V']/4.2);upper=(power*power*2*rho*area)**(1/3)/9.81;ideal=T**1.5/math.sqrt(2*rho*area)
    r.update(inferred_battery_cells=cells,claimed_battery_cells=b['claimed_cells'],nominal_continuous_bus_power_W=power,full_charge_continuous_bus_power_W=b['full_V']*b['continuous_A'],known_components_mass_kg=b['mass_kg']+m['count']*m['mass_each_kg'],ideal_maximum_gross_thrust_kg_at_nominal_voltage=upper,ideal_required_shaft_power_W=ideal,motor_claimed_power_total_W=m['count']*m['claimed_power_W'],motor_claimed_power_duration_s=m['power_duration_s'],no_load_rpm_bounds={'cutoff':m['kv']*b['cutoff_V'],'nominal':m['kv']*b['nominal_V'],'full':m['kv']*b['full_V']},ideal_target_feasible=ideal<=power)
    if cells!=b['claimed_cells']:r['blockers'].append(f'Akkuspannung {b["nominal_V"]}/{b["full_V"]} V entspricht {cells}S, nicht {b["claimed_cells"]}S.')
    if ideal>power:r['blockers'].append('Der Zielschub überschreitet bereits die ideale Leistungsgrenze des 50-A-Akkus. Keine Flügelform kann diese Energiebilanz umgehen.')
    prop=p['manufacturer_reference_propeller'];Aprop=math.pi*(prop['diameter_mm']/2000)**2;thrust=m['claimed_thrust_kg']*9.81;lower=thrust**1.5/math.sqrt(2*rho*Aprop);r['ideal_power_for_claimed_75kg_single_reference_propeller_W']=lower
    if lower>m['claimed_power_W']:r['blockers'].append('75 kg Schub an NS52 und 3400 W sind untereinander nicht plausibel: Schon die ideale induzierte Leistung liegt darüber. Herstellerkennfeld klären.')
    r['unknowns']=['MN1330-Leistungs-/Stromkennfeld und Bedeutung der 177 A fehlen.','19,5 mΩ ist ein Interphasenwert und kein validierter Gleichstrom-Ersatzwiderstand.','24S-ESC-Betrieb am 20S-Pack, Zellkennlinie, Spannungseinbruch und Motorkühlung sind ungeklärt.','Kein axialer Motordurchgang: stationäre Führung muss außen abgestützt werden; Anschlussmaße und Freigängigkeit sind konstruktiv zu prüfen.','Isolations-/Magnettemperaturen sind keine freigegebenen Motor-Dauerbetriebstemperaturen.','NS52x20-Herstellerschub gilt nicht automatisch für die eigene koaxiale Flügelgeometrie.']
    r['note']='Ideale Obergrenze mit gemeinsamer voller Koaxial-Kreisfläche, ohne Verluste. Spitzenstrom 1–3 s und 70-A-Sicherung erhöhen die 50-A-Dauergrenze nicht.';return r
def valid(d,p):
    try:
        if not all(math.isfinite(float(v)) for v in d.values()):return False
        if d['diameterMm']<=2*d['rootRadiusMm'] or d['chordMm']<=0 or d['blades']<2 or int(d['blades'])!=d['blades']:return False
        # Conservative symmetric half-chord angular envelope, including projected profile thickness.
        if d['chordMm']>2*d['rootRadiusMm']*math.tan(math.pi/d['blades']):return False
        for key,(lo,hi) in p['limits'].items():
            if d[key]<lo-1e-9 or d[key]>hi+1e-9:return False
        margin=p['cyclic_margin_deg']
        for k in ['pitchUpperDeg','pitchLowerDeg']:
            if min(d[k],d[k]+d['twistDeg'])< -2+margin-1e-9 or max(d[k],d[k]+d['twistDeg'])>21-margin+1e-9:return False
        return True
    except (KeyError,ValueError,TypeError):return False
def seeds(p):
    original=read(ROOT/'inputs/model_top10.json');rows=[]
    for row in original['top10Aerodynamic']:
        d=dict(row['design']);changes={}
        if p['seed_mode']=='transfer_shape_only':
            for k in ['diameterMm','rootRadiusMm','spacingMm']:changes[k]=[d[k],p['reference'][k]];d[k]=p['reference'][k]
            changes['chordMm']=[d['chordMm'],d['chordMm']*p['chord_scale_from_model']];d['chordMm']*=p['chord_scale_from_model'];d['chordMm']=max(p['limits']['chordMm'][0],min(p['limits']['chordMm'][1],d['chordMm']));d['rpm']=p['reference_rpm'];d['pitchAxisFraction']=p['reference']['pitchAxisFraction']
            if not p['preserve_seed_blade_counts']:d['blades']=p['reference']['blades']
            lo=-2+p['cyclic_margin_deg']-min(0,d['twistDeg']);hi=21-p['cyclic_margin_deg']-max(0,d['twistDeg'])
            for k in ['pitchUpperDeg','pitchLowerDeg']:
                old=d[k];d[k]=max(lo,min(hi,old))
                if d[k]!=old:changes[k]=[old,d[k]]
        else:d['pitchAxisFraction']=p['reference']['pitchAxisFraction']
        assert valid(d,p),('Invalid transferred geometry',d)
        rows.append({'design':d,'thrustN':row['thrustN'] if not changes else None,'mechanicalPowerW':row['mechanicalPowerW'] if not changes else None,'tipMach':d['rpm']*math.pi/30*d['diameterMm']/2000/340,'seed_changes':changes,'generation':0,'parent':None})
    return {'native_sha256':original['native_sha256'] if p['name']=='model' else None,'reference_model_native_sha256':original['native_sha256'],'massKg':p['target_mass_kg'],'top10Aerodynamic':rows}
def set_source():G.SOURCE=W/'input.json'
def case_env(case,p):
    net=json.loads((case/'case.json').read_text());solid=0
    import struct
    for name in ['wingUpper','wingLower']:
        for v in struct.iter_unpack('<12fH',(case/f'constant/triSurface/{name}.stl').read_bytes()[84:]):
            a,b,c=v[3:6],v[6:9],v[9:12];solid+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    target=net['iterations_requested'];(case/'runtime.env').write_text(f'MINIMUM_ITERATIONS={target}\nEXPECTED_SOLID_VOLUME={solid:.15g}\nDOMAIN_VOLUME={(2*net["domain_half_width_m"])**3:.15g}\n')
    R=net['design']['diameterMm']/2000
    G.write(case,'system/flowControlDict',f'''application postProcess; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT 1; writeControl timeStep; writeInterval 1; writeFormat ascii; runTimeModifiable false;
functions {{ profiles {{ type surfaces; libs (sampling); surfaceFormat raw; interpolationScheme cellPoint; fields (U p); surfaces {{ midspan {{type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{point ({.7*R} 0 0);normal (1 0 0);}} interpolate true;}} }} }} }}''')
def generate(ids,level='coarse',iterations=None):
    p=profile();set_source();rows=read(G.SOURCE)['top10Aerodynamic'];queue=[]
    for i in ids:
        case=W/'cases'/f'K{i:02d}_{level}'
        if not (case/'case.json').exists():G.build(i,level,iterations or (300 if level in ['fine','domain'] else p['iterations']))
        else:
            assert read(case/'case.json')['design']==rows[i-1]['design'],'Existing case uses another geometry; archive it first.'
        case_env(case,p);save(case/'input_entry.json',rows[i-1]);queue.append(case.name)
    return queue
def write_queue(names,stage='run'):(W/f'{stage}_queue.txt').write_text('\n'.join(names)+'\n')
def archive_input():
    raw=(W/'input.json').read_bytes();dest=W/'inputs_archive'/(hashlib.sha256(raw).hexdigest()+'.json');dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
def prepare():
    p=profile();W.mkdir(parents=True,exist_ok=True);out=W/'Ausgabe';out.mkdir(exist_ok=True)
    frozen=W/'profile.json'
    if frozen.exists() and read(frozen)!=p:raise ValueError('Profil geändert: bisherigen Arbeitsordner archivieren oder neues Profil verwenden. Berechnete Netze werden nicht überschrieben.')
    save(frozen,p);save(out/'Hardware_Preflight.json',hardware(p))
    if not (W/'input.json').exists():save(W/'input.json',seeds(p))
    archive_input()
    ids=list(range(1,len(read(W/'input.json')['top10Aerodynamic'])+1));write_queue(generate(ids));report();print('PREPARED',len(ids),'cases',W)
def pilot():
    W.mkdir(parents=True,exist_ok=True);old=G.SOURCE;G.SOURCE=ROOT/'inputs/model_top10.json';case=W/'cases/K01_pilot'
    if not (case/'case.json').exists():G.build(1,'pilot',50)
    case_env(case,profile());G.SOURCE=old;write_queue([case.name],'pilot');print('Known model diagnostic only; not part of full-scale ranking.')
def evaluate(case):
    if (case/'log.checkMesh').exists() and (case/'log.snappyHexMesh').exists():
        try:mesh_check(case)
        except (OSError,ValueError):pass
    r=measure(case);r['case']=case.name
    if not (case/'log.simpleFoam').exists() and (case/'failed').exists():r['status']='FAILED_PREPROCESSING'
    if r.get('accepted'):
        r['aero_score']=r['mechanicalPowerW']/r['thrustN']**1.5
    else:r['aero_score']=None
    return r
def report():
    if not (W/'input.json').exists():print('Noch nicht vorbereitet.');return {'cases':[],'ranking':[]}
    p=profile();rows=[evaluate(c) for c in sorted((W/'cases').glob('K??_coarse')) if (c/'case.json').exists()];ranking=sorted([r for r in rows if r.get('accepted')],key=lambda r:r['aero_score']);out=W/'Ausgabe';out.mkdir(exist_ok=True)
    # Render only completed physical results, once per actual checkpoint.
    for row in rows:
        c=W/'cases'/row['case']
        if not (c/'done').exists():continue
        stamp=str(row.get('lastIteration',0)); marker=c/'plots_checkpoint'
        if marker.exists() and marker.read_text()==stamp:continue
        try:
            import plotten
            plotten.forces(row['candidate_rank'])
            for probe in sorted((W/'cases').glob(f"K{row['candidate_rank']:02d}_probe_*_coarse")):
                t=probe.name.split('_')[2]
                if (probe/f'postProcessing/profiles/{t}/p_midspan.raw').exists():plotten.flow(row['candidate_rank'],t)
            marker.write_text(stamp)
        except (OSError,ValueError,AssertionError) as e:row['plot_warning']=str(e)
    hw=hardware(p);result={'profile':p,'hardware':hw,'cases':rows,'ranking':[r['candidate_rank'] for r in ranking],'best_tested':ranking[0]['candidate_rank'] if ranking else None,'unique_global_optimum_proven':False,'note':'Rangfolge nur numerisch gültiger CFD-Punkte nach P/T^(3/2); kein ungeprüfter Ersatzkandidat. Vollmaß-Saaten sind neu gerechnet, keine skalierten Modellkräfte.'}
    verifications=[]
    for r in ranking[:3]:
        item={'candidate':r['candidate_rank'],'coarse':r['aero_score'],'fine':None,'domain':None}
        for level in ['fine','domain']:
            c=W/'cases'/f'K{r["candidate_rank"]:02d}_{level}'
            if (c/'case.json').exists():
                v=evaluate(c)
                if v.get('accepted'):item[level]=v['aero_score']
        item['confirmed']=item['fine'] is not None and item['domain'] is not None and abs(item['fine']/item['coarse']-1)<.05 and abs(item['domain']/item['fine']-1)<.03;verifications.append(item)
    result['verification']=verifications
    result=finite(result)
    save(out/'results.json',result);(out/'results.js').write_text('globalThis.LOCAL_CFD_RESULTS='+json.dumps(result,allow_nan=False).replace('</','<\\/')+';\n')
    with (out/'Vergleich.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['candidate_rank','status','rpm','thrustEquivalentKg','mechanicalPowerW','figureOfMerit','aero_score'];writer=csv.writer(stream,delimiter=';');writer.writerow(fields+list(read(W/'input.json')['top10Aerodynamic'][0]['design']))
        for r in rows:writer.writerow([r.get(k) for k in fields]+list(r['design'].values()))
    shutil.copyfile(ROOT/'templates/CFD_Vergleich.html',out/'CFD_Vergleich.html')
    return result
def refine(count):
    r=report();p=profile();assert r['ranking'],'Keine numerisch gültigen Eltern. Zuerst Prüfgründe beheben; kein Scheinoptimum.'
    data=read(W/'input.json');current=data['top10Aerodynamic'];assert len(current)+count<=min(99,p['max_candidates']),'Fallbudget erreicht'
    parents=[v for v in r['cases'] if v['candidate_rank'] in r['ranking'][:3]];rng=random.Random(20261031+len(current));seen={json.dumps(v['design'],sort_keys=True) for v in current};ids=[];generation=max(v.get('generation',0) for v in current)+1
    for _ in range(2000):
        parent=parents[len(ids)%len(parents)];d=dict(parent['design']);step=.12*.6**(generation-1)
        for key,(lo,hi) in p['limits'].items():
            if key in p['fixed']:continue
            d[key]=max(lo,min(hi,d[key]+rng.gauss(0,step)*(hi-lo)))
        key=json.dumps(d,sort_keys=True)
        if not valid(d,p) or key in seen:continue
        seen.add(key);current.append({'design':d,'thrustN':None,'mechanicalPowerW':None,'tipMach':d['rpm']*math.pi/30*d['diameterMm']/2000/340,'generation':generation,'parent':parent['candidate_rank']});ids.append(len(current))
        if len(ids)==count:break
    assert len(ids)==count,'Zu wenige gültige neue Geometrien';save(W/'input.json',data);archive_input();write_queue(generate(ids));print('REFINEMENT',ids)
def verify():
    r=report();assert r['ranking'],'Keine gültigen Kandidaten für Feinprüfung';ids=r['ranking'][:3];names=generate(ids,'fine',300);names+=generate(ids[:1],'domain',300)
    for name in names:
        case=W/'cases'/name;parent=name.split('_')[0]+'_coarse';(case/'warm_start.txt').write_text(parent+'\n')
    write_queue(names,'verify');print('VERIFY',names)
def resume():
    r=report();p=profile();names=[]
    numeric={'at_least_200_iterations','force_std_below_3_percent','force_drift_below_2_percent','power_std_below_3_percent','power_drift_below_2_percent','velocity_residual_below_1e4','pressure_residual_below_1e4','mass_imbalance_below_1_percent'}
    for v in r['cases']:
        failed={k for k,x in v.get('checks',{}).items() if not x}
        if v.get('accepted') or not failed or not failed<=numeric:continue
        if v.get('lastIteration',0)>=p['max_iterations']:continue
        c=W/'cases'/v['case'];target=min(p['max_iterations'],int(v['lastIteration'])+250);env=c/'runtime.env';s=re.sub(r'MINIMUM_ITERATIONS=\d+',f'MINIMUM_ITERATIONS={target}',env.read_text());env.write_text(s);(c/'done').unlink(missing_ok=True);names.append(c.name)
    write_queue(names);print('NUMERICAL CONTINUATIONS',names)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','pilot','report','status','refine','verify','resume','preflight','watch']);parser.add_argument('--count',type=int,default=6);a=parser.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='preflight':print(json.dumps(hardware(profile()),indent=2))
    elif a.command=='pilot':pilot()
    elif a.command in ['report','status']:r=report();print(json.dumps({'profile':profile()['name'],'ranking':r.get('ranking',[]),'cases':[{k:v.get(k) for k in ['candidate_rank','status','lastIteration']} for v in r['cases']]},indent=2))
    elif a.command=='refine':refine(a.count)
    elif a.command=='verify':verify()
    elif a.command=='resume':resume()
    elif a.command=='watch':
        while True:
            try:report()
            except (OSError,ValueError) as e:print(type(e).__name__,str(e),flush=True)
            time.sleep(15)
if __name__=='__main__':main()
