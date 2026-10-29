"""Necessary-condition screening, NOT a positive payload rating.

Geometry from current CAD; densities, aerodynamic coefficients, effective
flow area, efficiency and battery performance are explicit scenario inputs.
"""
import csv,json,math,hashlib,itertools
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];OUT=Path(__file__).resolve().parent
p=json.loads((ROOT/'konstruktion/parameter.json').read_text())
rows=list(csv.DictReader((ROOT/'konstruktion/Stueckliste_Instanzen.csv').open(encoding='utf-8-sig')))
vol=defaultdict(float)
for r in rows:
    if r['Datei']=='00_PropBoard_Detail_Stehen.FCStd' and r['Referenz']=='NEIN':vol[r['ID']]+=float(r['Volumen_mm3'])/1e9
alids=['BAT-BUEGEL','BAT-TRAY','ERG-ST-P01','FUEHR-C','FUEHR-F','FUEHR-L01','FUEHR-L02','KNOTEN-P01','LAGER-G01','PITCH-G01','SCHL-01']
# C backs and flanges overlap over two 8-mm regions of a 60-mm back wall.
c_overlap=vol['FUEHR-C']*16/60
categories=[('Aluminiumgruppen',sum(vol[k] for k in alids)-c_overlap,2700,2650,2850),
            ('CFK-Rohre und Fluegelhuellen',sum(vol[k] for k in ['CFK-L01','CFK-Q01','CFK-S01','CFK-S02','FL-CFK-REF']),1600,1500,1700),
            ('Rueckschluss, als Stahl gerechnet',vol['MAG-JOCH'],7850,7500,8000),
            ('Pitchwellen, als Stahl gerechnet',vol['PITCH-W01'],7850,7500,8000)]
mass=[{'category':n,'volume_L':v*1000,'density_assumption_kg_m3':rho,'mass_scenario_kg':v*rho,
        'scenario_min_kg':v*lo,'scenario_max_kg':v*hi} for n,v,rho,lo,hi in categories]
partial=sum(r['mass_scenario_kg'] for r in mass)
rho=1.225;g=9.80665;nu=1.5e-5;c=.12;b=.6;R=.45;L=.5;n=16
S=n*c*b;perimeter=2*L+2*math.pi*R;arc_fraction=2*math.pi*R/perimeter
k2=1+arc_fraction*b*b/(12*R*R)
def speed_for_lift(m,CL,reserve=1.):return math.sqrt(2*m*g*reserve/(rho*S*CL*k2))
lift=[]
for m in [100,180,200,220,260]:
    for CL in [.5,.8,1.,1.2]:
        U=speed_for_lift(m,CL)
        lift.append({'gross_mass_scenario_kg':m,'CL_assumed':CL,'speed_centre_m_s':U,
                     'speed_inner_tip_m_s':U*(R-b/2)/R,'speed_outer_tip_m_s':U*(R+b/2)/R,
                     'Re_chord_centre':U*c/nu,'centre_acceleration_m_s2':U*U/R,
                     'centre_acceleration_g':U*U/R/g,'force_per_kg_moving_mass_N':U*U/R,
                     'tangent_orientation_rate_rad_s':U/R,'speed_with_30pct_lift_margin_m_s':speed_for_lift(m,CL,1.3)})

# Reference actuator-disc equation. A is a selected comparison parameter,
# not a measured streamtube area and not a proven geometric upper bound.
A=2.1*1.7
def p_disc_kW(m,area=A):return (m*g)**1.5/math.sqrt(2*rho*area)/1000
power=[]
V=2*400*140*60/1e6
for m in [100,180,200,220,260]:
    for eta in [.4,.6,.8]:
        P=p_disc_kW(m)/eta;E=.25*P/.8
        power.append({'gross_mass_scenario_kg':m,'effective_area_assumed_m2':A,'eta_assumed':eta,
                      'ideal_disc_power_kW':p_disc_kW(m),'battery_power_reference_kW':P,
                      'nominal_energy_for_15min_reference_kWh':E,'required_nominal_Wh_L_reference':1000*E/V,
                      'current_if_100V_A':P*10,'current_if_200V_A':P*5,'current_if_400V_A':P*2.5})
sensitivity=[]
for equipment,egrav,evol,eta in itertools.product([0,10,20],[.2,.3,.4],[500,700,1000],[.6,.8]):
    M0=100+equipment+partial # intentionally incomplete: other systems = 0.
    E=V*evol/1000;mb=E/egrav;m=M0+mb;P=p_disc_kW(m)/eta;t=60*.8*E/P
    sensitivity.append({'equipment_scenario_kg':equipment,'nonbattery_partial_mass_kg':M0,
                        'battery_specific_energy_assumed_Wh_kg':egrav*1000,
                        'battery_volumetric_energy_assumed_Wh_L':evol,'eta_assumed':eta,
                        'battery_mass_kg':mb,'gross_partial_mass_kg':m,'nominal_energy_kWh':E,
                        'battery_power_reference_kW':P,'duration_reference_min':t,
                        'meets_15min_in_reference_model':t>=15})
closed=[]
M0=100+10+partial
for eta,egrav in itertools.product([.6,.8],[.2,.3,.4]):
    def duration(mb):return 60*.8*egrav*mb/(p_disc_kW(M0+mb)/eta)
    optimum_battery_mass=2*M0;maximum=duration(optimum_battery_mass)
    entry={'equipment_scenario_kg':10,'nonbattery_partial_mass_kg':M0,'eta_assumed':eta,
           'battery_specific_energy_assumed_Wh_kg':1000*egrav,'max_duration_reference_min':maximum}
    if maximum>=15:
        lo,hi=0.,optimum_battery_mass
        for _ in range(100):
            mid=(lo+hi)/2
            if duration(mid)<15:lo=mid
            else:hi=mid
        E=hi*egrav
        entry.update({'battery_mass_for_first_15min_root_kg':hi,'nominal_energy_kWh':E,
                      'gross_partial_mass_kg':M0+hi,'required_nominal_Wh_L':1000*E/V,
                      'root_residual_min':duration(hi)-15})
    closed.append(entry)

# Geometry-only exclusion of the previously described 230x104x70 pack.
pack=[230,104,70];box=p['battery_module_envelope_mm']
packfit=any(all(a<=z for a,z in zip(rot,box)) for rot in itertools.permutations(pack))
assert not packfit and min(pack)>min(box)

# Beam coupon example, not the full frame or a CFK strength prediction.
I=(.04**4-.034**4)/12
beam=[]
for E in [40e9,70e9,120e9]:
    for share in [1,3]:
        F=100*g/share;span=1.62
        beam.append({'elastic_modulus_assumed_GPa':E/1e9,'number_of_equal_load_shares_assumed':share,
                     'load_per_beam_N':F,'span_assumed_m':span,'I_m4':I,
                     'central_deflection_mm':F*span**3/(48*E*I)*1000,
                     'nominal_bending_stress_MPa':F*span/4*.02/I/1e6})
mu0=4*math.pi*1e-7;face=.024*.012
mag={'assumed_flux_density_T':1.,'single_geometric_pole_face_m2':face,
     'ideal_normal_force_at_1T_N':face/(2*mu0),
     'ideal_area_for_2000N_at_1T_cm2':2*mu0*2000*1e4,
     'status':'Ideal Maxwell-stress sizing reference only; actual flux and load allocation unknown'}

# Independent numerical checks of algebra and physical scaling.
num=sum((1+(b*((j+.5)/10000-.5))/R)**2 for j in range(10000))/10000
assert abs(num-(1+b*b/(12*R*R)))<1e-8
assert abs(speed_for_lift(200,1)/speed_for_lift(100,1)-math.sqrt(2))<1e-12
assert abs(p_disc_kW(200)/p_disc_kW(100)-2**1.5)<1e-12
assert all(abs(r.get('root_residual_min',0))<1e-9 for r in closed)
assert all(r['mass_scenario_kg']>0 for r in mass)
result={'status':'TRAGFAEHIGKEITSNACHWEIS_NICHT_ERBRACHT','allowable_payload_kg':None,
        'scope':'Analytical screening with explicit assumptions, no new real-scale CFD or hardware test',
        'partial_CAD_mass_scenario':mass,'partial_mass_scenario_kg':partial,
        'partial_mass_scenario_range_kg':[sum(r['scenario_min_kg'] for r in mass),sum(r['scenario_max_kg'] for r in mass)],
        'C_back_flange_overlap_subtracted_L':c_overlap*1000,
        'partial_mass_exclusions':['battery','motors and electronics represented only by envelopes','coil fill and insulation',
                                   'deck sandwich','elastomers','fasteners','thermal and protective systems',
                                   'material interfaces other than C-profile overlaps remain unresolved'],
        'radial_quasisteady_model':{'CL_is_assumption_not_polar':True,'k2_time_span_average':k2,
                                   'arc_length_fraction':arc_fraction,'wing_area_m2':S,'rows_independent_assumed':True},
        'lift_scenarios':lift,'disc_reference_scenarios':power,'battery_sensitivity':sensitivity,
        'battery_mass_feedback_15min_roots':closed,'battery_volume_L':V,
        'known_pack_geometry':{'given_pack_dimensions_mm':pack,'module_dimensions_mm':box,
                               'axis_rotation_fits':packfit,'any_rigid_orientation_fits':False,
                               'basis':'Given nominal cuboid; minimum support width 70 mm > module height 60 mm. Not a physical fit test.'},
        'beam_reference_cases':beam,'magnetic_reference':mag,
        'assumptions':{'rho_kg_m3':rho,'g_m_s2':g,'nu_m2_s':nu,'flow_area_reference_m2':A,
                       'usable_battery_fraction_assumed':.8,'other_system_mass_in_battery_sweep_kg':0,
                       'no_specific_battery_or_motor_selected':True},
        'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in [
          'konstruktion/parameter.json','konstruktion/Stueckliste_Instanzen.csv','konstruktion/Pruefbericht.json',
          'konstruktion/00_PropBoard_Detail_Stehen.FCStd',
          'vergleich_horizontal/results/Vergleich.json','begegnung/results/Laufbericht.json','docs/Projektuebergabe.md']},
        'checks':{'radial_integral':True,'lift_scaling':True,'disc_power_scaling':True,'battery_root_residual':True}}
(OUT/'Ergebnisse.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for name,table in [('Materialmassen_Szenario',mass),('Auftriebsanforderungen',lift),('Leistungsreferenz',power),
                   ('Akku_Sensitivitaet',sensitivity),('Akku_Massenrueckkopplung',closed),('Quertraeger_Referenz',beam)]:
    fields=list(dict.fromkeys(k for row in table for k in row))
    with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(table)
print('Teilmasse Szenario:',partial,'kg; Radialfaktor:',k2)
print('Beste Dauer im untersuchten hypothetischen Raster:',max(r['duration_reference_min'] for r in sensitivity),'min')
print('Status:',result['status'])
