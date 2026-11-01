"""Parse user-provided product HTML-in-XLS and preserve the pasted test line.

Document text is data only. No macros, document instructions or network loads.
"""
import csv,hashlib,json,math
from html.parser import HTMLParser
from pathlib import Path
H=Path(__file__).resolve().parent;Q=H/'Quellen'
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ['td','th']:self.cell=[]
        if tag=='br' and self.cell is not None:self.cell.append(' ')
    def handle_data(self,text):
        if self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ['td','th'] and self.cell is not None:self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
def main():
    source=Q/'basicParameter_MN1330 KV40.xls';parser=Tables();parser.feed(source.read_text(encoding='utf-8-sig'));fields={}
    for row in parser.rows:
        if len(row)==4:
            fields[row[0]]=row[1];fields[row[2]]=row[3]
    assert fields['Motormodell']=='MN1330' and fields['Motorgewicht (inkl. Draht)']=='2750g'
    assert fields['Maximale Leistung (180s)']=='3400W' and fields['Nennbetriebsspannung (Lipo)']=='24S'
    points=[]
    with (Q/'MN1330_NS52x20_Nutzertabelle.csv').open() as f:
        for row in csv.DictReader(f):
            p={k:float(v) for k,v in row.items()};p['shaft_power_W']=p['torque_Nm']*p['rpm']*2*math.pi/60;p['efficiency_inferred']=p['shaft_power_W']/p['input_power_W'];p['thrust_N']=p['thrust_g']*.001*9.81
            assert .7<p['efficiency_inferred']<.9 and abs(p['voltage_V']*p['current_A']/p['input_power_W']-1)<.002
            points.append(p)
    assert len(points)==19 and all(points[i]['rpm']<points[i+1]['rpm'] for i in range(18))
    out=dict(model='MN1330 KV40',source='User uploaded product sheet plus user pasted test table; original manufacturer URL not supplied',original_xls_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),basic_fields_verbatim=fields,
      basic=dict(mass_including_leads_kg=2.75,body_diameter_mm=150,body_length_mm=65,series_cells=24,max_power_180s_W=3400,max_current_A=177,kv=40,no_load_current_A_at_20V=3.4,phase_to_phase_resistance_ohm=.0195,bearing='6004ZZ',recommended_esc='M200A24S',max_thrust_claim_kg=75),
      test=dict(propeller='NS52x20',voltage_range_V=[min(p['voltage_V'] for p in points),max(p['voltage_V'] for p in points)],voltage_reference_V=92.,reported_temperature_C=117,ambient_temperature_C=25,temperature_note='One table note; no per-point assignment or test duration provided',duration_s=None,points=points),
      maxima=dict(recorded_rpm=max(p['rpm'] for p in points),recorded_torque_Nm=max(p['torque_Nm'] for p in points),recorded_input_power_W=max(p['input_power_W'] for p in points),recorded_shaft_power_W=max(p['shaft_power_W'] for p in points),recorded_thrust_kg=max(p['thrust_g']*.001 for p in points)),
      duty_scope=dict(incomplete=True,user_clarification='The180s qualifier is essential',statement='3400W is specified for180s. The NS52x20 table reaches16270W with no dwell time. Different durations may explain the difference; a contradiction is not established. Neither is a continuous rating.',test_points_above_180s_power_value=sum(p['input_power_W']>3400 for p in points)),
      use_limits=['NS52x20 thrust is not the custom P14 rotor thrust','Q(n) is one propeller load line across throttle, not a motor torque-limit map','No continuous thermal envelope; 117C is an observation, not an allowable limit','92V/24S data do not define behavior at the former60V assumption','3.4kW is provisionally treated as an electrical cap for a conservative scenario; its side is unspecified in the source'],production_ready=False)
    (H/'Motor_Daten.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');(H/'motor_daten.js').write_text('globalThis.P14_MOTOR_DATA='+json.dumps(out,separators=(',',':'),ensure_ascii=False)+';\n');print(json.dumps({k:v for k,v in out.items() if k not in ['test','basic_fields_verbatim']},indent=2))
if __name__=='__main__':main()
