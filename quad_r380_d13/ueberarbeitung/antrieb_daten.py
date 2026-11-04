"""Generic static coefficient estimate, NS52 reference only, never HEP-S OEM map."""
from pathlib import Path
import json,csv,statistics,math,hashlib
H=Path(__file__).resolve().parents[1];R=H.parent;f=R/'quad_r380_d05/Quellen/MN1330/MN1330_NS52x20_Nutzertabelle.csv';rows=list(csv.DictReader(f.open()));rho=1.225;d=52*.0254
ct=[];cp=[];eta=[]
for r in rows:
 n=float(r['rpm'])/60;shaft=float(r['torque_Nm'])*2*math.pi*n
 ct.append(float(r['thrust_g'])/1000*9.80665/(rho*n*n*d**4));cp.append(shaft/(rho*n**3*d**5));eta.append(shaft/float(r['input_power_W']))
data=dict(method='Generic static CT/CP model, reference NS52x20 coefficients transferred with assumed pitch-ratio scaling; NOT measured HEP-S performance.',rho_kg_m3=rho,g_m_s2=9.80665,reference_diameter_in=52,reference_pitch_in=20,reference_CT=statistics.median(ct),reference_CP=statistics.median(cp),assumed_drive_efficiency=statistics.median(eta),CT_sensitivity_fraction=.25,CP_sensitivity_fraction=.35,uncertainty_kind='illustrative coefficient sensitivity,not statistical confidence or guaranteed bound',motor_KV=40,motor_measured_max_torque_Nm=max(float(r['torque_Nm']) for r in rows),motor_measured_max_rpm=max(float(r['rpm']) for r in rows),motor_thermal_continuous_verified=False,ESC_output_continuous_A=100,ESC_phase_definition_verified=False,battery_cells=24,default_voltage_V=92,default_rpm=2500,default_all_up_mass_kg=160,default_payload_reference_kg=100,rotor_count=4,reference_source=str(f.relative_to(R)),reference_source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),HEPS_manufacturer_map_available=False,production_ready=False)
power=json.loads((R/'quad_r380_d05/Ausgabe/MN1330_Betriebsgrenzen.json').read_text());data.update(motor_reference_power_W=3400,motor_reference_power_duration_s=power['motor_power_3400W_duration_s'],motor_reference_power_side_unknown=power['motor_power_3400W_side_unknown'])
(H/'Ausgabe/Antrieb_Annahmen.json').write_text(json.dumps(data,indent=2));(H/'Ausgabe/antrieb_daten.js').write_text('globalThis.QD_DRIVE='+json.dumps(data,separators=(',',':'))+';\n');print(data['reference_CT'],data['reference_CP'],data['assumed_drive_efficiency'])
