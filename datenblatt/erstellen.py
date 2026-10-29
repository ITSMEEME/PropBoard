"""Create a traceable design data sheet, never substitute unknown ratings."""
from pathlib import Path
import json,subprocess,hashlib,csv
from collections import Counter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
p=json.loads((ROOT/'konstruktion/parameter.json').read_text())
r=json.loads((ROOT/'konstruktion/Pruefbericht.json').read_text())['00_PropBoard_Detail_Stehen']
rows=list(csv.DictReader((ROOT/'konstruktion/Stueckliste_Instanzen.csv').open(encoding='utf-8-sig')))
counts=Counter(v['ID'] for v in rows if v['Datei']=='00_PropBoard_Detail_Stehen.FCStd')
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
sources=['konstruktion/parameter.json','konstruktion/Pruefbericht.json','konstruktion/Stueckliste_Instanzen.csv',
         'konstruktion/00_PropBoard_Detail_Stehen.FCStd','vergleich_horizontal/parameter.json','begegnung/results/Laufbericht.json']
data={
  'document_id':'PB-HZ-STEH-DS-001','revision':'0.1','type':'Entwicklungsdatenblatt, keine freigegebene Produktspezifikation',
  'baseline_commit':sha,
  'variant':'Zwei horizontale gegenlaeufige Fluegelumlaeufe; Hauptvariante Stehen',
  'null_meaning':'Nicht festgelegt oder nicht nachgewiesen; NICHT null Leistung oder null Tragfaehigkeit',
  'targets':{'pilot_mass_kg':100,'additional_equipment_mass_kg':None,'endurance_min_min':15,
             'speed_km_h_approx':80,'maximum_vehicle_dimensions_mm':[2100,1700,600]},
  'cad':{'vehicle_dimensions_mm':r['vehicle_bounds_mm'],'pilot_excluded_from_dimensions':True,
         'complete_protection_included':False,'wings':counts['FL-CFK-REF'],'end_carriages':counts['SCHL-01'],
         'pitch_motor_envelopes':counts['PITCH-MOT-REF'],'wing_chord_mm':p['wing_chord_mm'],
         'wing_span_mm':p['wing_span_mm'],'summed_geometric_wing_area_m2':counts['FL-CFK-REF']*p['wing_chord_mm']*p['wing_span_mm']/1e6,
         'levels_z_mm':p['levels_z_mm'],'level_gap_mm':p['levels_z_mm'][1]-p['levels_z_mm'][0],
         'pitch_snapshot_deg':p['pitch_deg'],'mean_curve_radius_mm':p['radius_mm'],
         'straight_section_length_mm':p['straight_mm'],'deck_top_z_mm':p['deck_top_z_mm'],
         'standing_surface_z_mm':358,'vehicle_bottom_z_mm':p['vehicle_bottom_z_mm']},
  'battery_envelopes':{'count':counts['BAT-MOD-REF'],'each_dimensions_mm':p['battery_module_envelope_mm'],
                       'each_volume_L':p['battery_module_envelope_mm'][0]*p['battery_module_envelope_mm'][1]*p['battery_module_envelope_mm'][2]/1e6,
                       'cell_or_pack_selected':False},
  'unverified_ratings':{'allowable_pilot_mass_kg':None,'allowable_total_payload_kg':None,
                        'empty_mass_kg':None,'battery_mass_kg':None,'takeoff_mass_kg':None,
                        'continuous_thrust_N':None,'peak_thrust_N':None,
                        'battery_nominal_voltage_V':None,'battery_capacity_Ah':None,
                        'battery_nominal_energy_kWh':None,'battery_usable_energy_kWh':None,
                        'battery_continuous_current_A':None,'battery_peak_current_A':None,
                        'hover_electrical_power_kW':None,'peak_electrical_power_kW':None,
                        'hover_battery_current_A':None,'mission_energy_kWh':None,
                        'verified_endurance_min':None,'verified_speed_km_h':None,'range_km':None},
  'manufacturing_release':False,'flight_validation':False,'real_scale_3d_CFD':False,
  'sources_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}}
(HERE/'Technisches_Datenblatt.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
assert data['cad']['wings']==16 and data['cad']['end_carriages']==32
assert all(v is None for v in data['unverified_ratings'].values())
assert data['battery_envelopes']['each_volume_L']==3.36
print('Datenblatt-Daten aus CAD-Stand',sha[:7],'erstellt; unbekannte Leistungswerte explizit null.')
