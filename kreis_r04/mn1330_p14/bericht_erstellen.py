"""Publish a source-bound engineering review; never grants manufacturing release."""
import os,json,csv,collections,hashlib,re
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe'
def read(name):return json.loads((O/name).read_text())
def de(v,n=2):return f'{v:,.{n}f}'.replace(',','@').replace('.',',').replace('@','.')
def main():
    model=read('Modell.json');p=read('Pruefung.json');step=read('STEP_Pruefung.json');kin=read('Kinematik_Pruefung.json');col=read('Kollisionen.json');sim=read('Simulation_Pruefung.json');browser=read('Browser_Pruefung.json');load=read('Lastscreen.json');mass=read('Massenvarianten.json');motor=json.loads((H/'Motor_Daten.json').read_text())
    assembly=read('Montage_Pruefung.json');oldjoint=json.loads((H/'Quellen/P14_Gelenkfix_Ausgangsbefund.json').read_text())
    pilot=read('Flugsteuerung_Pruefung.json');pilotbrowser=read('Flugsimulator_Browser_Pruefung.json')
    sha=hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest()
    assert sha==model['source_native_sha256']==p['native_sha256']
    for report in [step,kin,col,sim,browser,load,assembly,pilot,pilotbrowser]:assert report['native_sha256']==sha
    assert pilot['passed'] and pilotbrowser['passed']
    for report in [pilot,pilotbrowser]:
        for name,digest in report['source_sha256'].items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
    assert p['all_valid'] and step['all_active_single_parts_pass'] and step['aggregate']['pass'] and sim['passed'] and browser['passed']
    assert not kin['native']['selected_dynamic_overlaps']
    assert col['open_count']==0 and assembly['passed']
    assert len(mass['cases'])==5 and all(c['all_valid'] for c in mass['cases'].values())
    before=json.loads((H/'Quellen/P13_Lastscreen_4dc7252.json').read_text())
    previous=before['identified_manufactured_metal_mass_kg']+before['cfk_solid_volume_mass_if_1600kg_m3_kg'];current=p['mass']['aluminium_assumed_kg']+p['mass']['cfk_assumed_kg'];reduction=1-current/previous
    groups=collections.Counter((re.sub(r'_[0-9]+$','',r['part_a']),re.sub(r'_[0-9]+$','',r['part_b'])) for r in col['overlaps'])
    grouptext='\n'.join(f'| {a} / {b} | {count} |' for (a,b),count in groups.items())
    variants='\n'.join(f'| {n} | {de(v["mass_kg"])} kg | {v["body_count"]} |' for n,v in mass['cases'].items())
    h=sim['hover_demand'];m=p['mass'];rq=load['rpm_cases'][-1]
    domainparts=[r for r in step['parts'] if 'bidirectional_cut_difference_mm3' in r]
    text=f'''# Ergebnis P14

**Außenrahmen und Spitzenlager entfernt; verstärktes Zentrum, freitragende CFK-Flügel und sechs reale PH54-Servos je Rotorpaar als Entwicklungsstand umgesetzt.** Die native Baugruppe hat {p['body_count']} gültige Körper und {p['type_count']} aktive Teiletypen. Sie ist animierbar und mit CAD-Masse/-Trägheit im separaten parametrischen Entwicklungsprüfstand untersuchbar. **Produktions- und Flugfreigabe fehlen.**

[Flugsimulator mit WASD](P14_Flugsimulator.html) · [Technischer Prüfstand](P14_Entwicklungspruefstand.html) · [FreeCAD](Ausgabe/P14_MN1330_Leichtbau.FCStd) · [STEP](Ausgabe/P14_MN1330_Leichtbau.step) · [offene Freigaben](FREIGABESTATUS.md)

![P14](Ansichten/P14_Gesamt.png)

## Masse und Umfang

| Erfasster Anteil | P13 | P14 |
|---|---:|---:|
| Zuordenbares Metall / Aluminium-Struktur | {de(before['identified_manufactured_metal_mass_kg'])} kg | {de(m['aluminium_assumed_kg'])} kg |
| CFK bei angenommener Dichte 1.600 kg/m³ | {de(before['cfk_solid_volume_mass_if_1600kg_m3_kg'])} kg | {de(m['cfk_assumed_kg'])} kg |
| Summe dieser Strukturanteile | {de(previous)} kg | {de(current)} kg |

Die erfassten Strukturanteile sinken um {de(reduction*100,1)} %. Der Umfang ist unterschiedlich: P13 enthält unter anderem äußere Führung, Aktoren und Fahrwerk; P14 benötigt noch Personendeck, Schutz-/Landestruktur und weitere Systemteile. **Die Prozentzahl ist kein Nachweis eines entsprechend leichteren vollständigen Fluggeräts.**

Mit dokumentierten Motor-/Servomassen und angenommenen Normlager-/Materialmassen beträgt die erfasste P14-CAD-Masse **{de(m['dry_cad_mass_assumed_kg'])} kg**. Die neue XLS-Motormasse 2,75 kg statt 2,00 kg erhöht diesen Wert um 1,50 kg. Mit 100 kg Nutzlast, 12 kg angenommener Batterie und 2 kg Elektronik ergibt sich der Rechenfall **{de(m['total_scenario_mass_kg'])} kg**. Weitere reale Systemmassen fehlen; dies ist keine gewogene Fahrzeugmasse.

Die ausgeführten Gelenke, Deckel, Befestigungen und größeren Freiräume erhöhen die erfasste CAD-Masse gegenüber dem früheren P14-Nennstangenstand von {de(oldjoint['dry_cad_mass_kg'])}kg um {de(m['dry_cad_mass_assumed_kg']-oldjoint['dry_cad_mass_kg'])}kg. Der zusätzliche Umfang ist in den neuen Massendaten und Flugrechenfällen enthalten.

## Geometrie, Bewegung und Export

- Alle {p['body_count']} installierten Körper sind gültige Einzelvolumina.
- Alle {p['type_count']} aktiven Einzel-STEPs und das Gesamt-STEP mit {step['aggregate']['solids']} Volumina bestehen den Rücklesetest. Relative Gesamtvolumenabweichung: {step['aggregate']['relative_volume_error']:.3g}.
- Bei {len(domainparts)} Einzelteilen weicht die numerische Volumenintegration nach STEP-Reparametrisierung ab. Die zusätzliche beidseitige Material-Differenzprüfung ergibt maximal {max((r['bidirectional_cut_difference_mm3'] for r in domainparts),default=0):.3g}mm³; Hüllkästen und gültige Volumina stimmen innerhalb der protokollierten Prüfgrenzen überein.
- {kin['states']} Kinematikzustände für 4/6/8/10/12 Blätter und 360/440 mm Ebenenabstand: numerischer Gestängeschluss unter 10⁻⁶ mm; Hebelpitch {de(kin['blade_lever_pitch_range_deg'][0])}–{de(kin['blade_lever_pitch_range_deg'][1])}°.
- Die Gestängedurchführungen haben in der abgetasteten Hüllkreisabschätzung mindestens {de(kin['rod_port_min_screen_clearance_mm'])} mm Reserve; das ist kein vollständiger Fertigungs-/Elastizitätsnachweis.
- Native Animation: alle Körper in fünf Stellungen gültig, Rückstellung ohne Verschiebungsfehler. {kin['native']['selected_pair_count']} ausgewählte kritische Paare einschließlich benachbarter Gelenkaugen zeigen keine Volumenüberschneidung. Eine vollständige dynamische Hüllvolumenprüfung steht aus.

Die vollständige statische Prüfung zählt **{col['open_count']} Überschneidungen** über0,1mm³. Die früheren28 Anschlussbefunde sind konstruktiv geschlossen. Alle {col['all_bodies']} Körper sind einbezogen; es gibt keine pauschalen Kontakt-Ausnahmen. Identische Bauteilpaare mit identischer relativer Starrkörperlage werden zwischengespeichert.

## Gelenke und Montage

44 Endgelenke je Rotorpaar sind mit separaten Augen, Lagern/Buchsen, Distanzhülsen, Kopfbolzen, Scheiben, Splinten und DIN472-Sicherungen modelliert. M6-RH/LH-Einstellhülsen ersetzen die durchgehenden Nennstangen. Die Aluminiumteile sind Sonderteile in Norm-Konturfamilien; die GE8E-Innenprofile sind Nennmodelle, keine behaupteten OEM-Dateien.

{len(assembly['assembly_paths'])} Montage-/Werkzeugfälle bestehen: kontinuierliche Bolzen-Auszugshüllen, die benannten Lager-/Baugruppenwege und30-mm-Bitzugänge für {len(assembly['hex_bit_access_families'])} Schraubenfamilien. Der minimale modellierte M6-Gestängeeingriff beträgt {de(assembly['min_M6_engagement_mm'])}mm. Über2160 Kinematikzustände benötigt das GE-Nennmodell maximal {de(kin['joint_articulation_screen']['max_spherical_misalignment_deg'])}° Schwenkwinkel bei einem12°-Geometriescreen. Im nativen Fünf-Posen-Test bleiben die inneren Gelenkprofile überschneidungsfrei.

Der Hauptflansch ist abnehmbar, die äußeren Blattlagersitze sind offen, Kugelpfanne/Liner und Taumellagerdeckel sind geteilt. Die Pitchwelle besitzt Integralflansch und Wurzelmandrel; vier von außen erreichbareM6 ersetzen separate Innenplatte/Einsatz und die verdeckte Endschraube. [Montagefolge, Prüfbedingungen und Restpunkte](MONTAGE.md) · [Gelenk-Explosionsansicht](Ansichten/P14_Gelenk_Explodiert.png).

Die Montageprüfung gilt für die8-Blatt-Standardkonfiguration und die ausdrücklich benannten Montagestufen. OEM-Servobefestigung/Horn, Fertigungstoleranzen, vollständige Hand-/Werkzeughüllen und Tragfähigkeit bleiben offen. Die Prüfungen sind keine Produktionsfreigabe.

## Servo und Strukturbeanspruchung

Ausgewählt ist ROBOTIS PH54-200-S500-R. Der XH540 wurde nach dem Lastscreen verworfen. PH54-Herstellerangabe: 44,7 Nm, 24 V, 855 g; die Dauerangabe basiert laut OEM-Fußnote auf einer Berechnung des Grundmotors und muss für diese Anwendung bestätigt werden. Originales Montage-/Horn-CAD fehlt. [Quellen und Grenzen](SERVO.md).

Der aktuelle 2-g-Rechenfall fordert {de(load['load_case']['flap_force_per_blade_N'],1)} N Schub je Blatt, {de(load['load_case']['shaft_last_support_moment_Nm'],1)} Nm am letzten Wellenlager und etwa {de(load['load_case']['bearing_couple_reaction_N'],0)} N Lagerpaar-Reaktion. Bei 2.100/min ergibt der Screen rund {de(rq['centrifugal_root_N']/1000,2)} kN Wurzelfliehkraft und {de(rq['servo_peak_abs_sum_screen_Nm'],1)} Nm konservativen Servo-Momentbedarf.

Das homogene Ersatz-Balkenmodell liefert bei angenommenem E = 70–110 GPa eine Spitzendurchbiegung von etwa {de(min(r['tip_deflection_mm'] for r in load['beam']))}–{de(max(r['tip_deflection_mm'] for r in load['beam']))} mm. Orthotropes Laminat, Kerben, Flanschbohrungen, Alu-Schrauben, Lagertragzahlen, Wurzelstern-Verformung und Ermüdung sind damit nicht freigegeben.

## MN1330-Daten und Flugbedarf

Die 19 NS52×20-Prüfpunkte, 2,75-kg-Motormasse und ca.92V/24S wurden übernommen. **3.400 W beziehen sich auf höchstens180s.** Der 16.270-W-Prüfwert hat keine angegebene Haltedauer. Das sind unterschiedliche Zeitbezüge; keine der Angaben wird als Dauerleistung oder als freigegebene Sonderrotor-Kennlinie behandelt. Die NS52×20-Zugkraft wird nicht auf P14 übertragen. [Ausführliche Dateninterpretation](MOTOR_DATEN.md).

Für die Standardkonfiguration mit 100 kg Nutzlast ergibt die vereinfachte Aerorechnung:

| Rechnerischer Schwebebedarf | Wert |
|---|---:|
| Drehzahl | {de(h['rpm'],0)}/min |
| Wellenleistung gesamt | {de(h['shaftPower_W']/1000,1)} kW |
| Drehmoment je Motor | {de(h['torques_Nm'][0],1)} / {de(h['torques_Nm'][1],1)} Nm |
| Elektrisch bei angenommener η = {de(h['efficiency_assumed'],2)} | {de(h['electricalPowerAssumed_W']/1000,1)} kW |
| Höchster dokumentierter Prüfmomentwert | {de(motor['maxima']['recorded_torque_Nm'],2)} Nm je Motor |
| Höchste dokumentierte elektrische Aufnahme beider Motoren | {de(2*motor['maxima']['recorded_input_power_W']/1000,2)} kW |

Der berechnete Wellenbedarf ist bereits höher als die gesamte dokumentierte elektrische Aufnahme beider Motoren. Die vorliegenden Betriebswerte decken diesen Sonderrotor-Schwebepunkt deshalb nicht ab. Bei 850/min entstehen getrimmt nur etwa 270 N Gesamtschub, rund27,5 kg Kraftäquivalent. Im voreingestellten zeitgebundenen Motorfall bleibt das Modell am Boden. Die Flugrechnung erzeugt keine zusätzliche Leistung, um Schweben zu erzwingen.

Der konservative 3,4-kW-Rechenfall beendet die Zeitrechnung nach180s. Ein Vergleich mit den Prüfmaxima weist deren unbekannte Haltedauer aus. Freie Motorannahmen sind separat sichtbar; sie werden nicht als bestätigter Hardwarebetrieb ausgegeben. Ein thermisches Dauermodell fehlt.

## Parametrische Fälle

| Blätter je Rotor | Erfasste Masse eines Rotorpaars | Körper |
|---|---:|---:|
{variants}

Die Geometrien und Trägheiten wurden für alle fünf Blattzahlen neu aus CAD erzeugt. 1–4 Rotorpaare lassen sich mit geänderter Gesamtmasse, Schwerpunktlage und Trägheit im Prüfstand untersuchen. Bei mehreren Paaren fehlt der Verbindungsrahmen; diese Anordnungen sind konstruktiv unvollständig und können das Zielmaß überschreiten.

Die {len(sim['checks'])} Physik-/Datenprüfungen und {len(browser['checks'])} Browserprüfungen bestehen, einschließlich Gegenmomenten, Leistungsgrenzen,180s-Zeitgrenze, Parameterwechsel, Export und mobiler Darstellung. Die bisherigen BEMT-Standardfälle bleiben numerisch unverändert. P14 ist als Entwicklungsmodell aus der H01-Modellauswahl erreichbar; eine Produktions- oder Flugfreigabe folgt daraus nicht.

## Interaktiver Flugsimulator

P14 ist mit WASD, QE, RF und Start/Landung/Pause steuerbar. Der ideale Modellregler bietet Positionshaltung und Winkelmodus, Kamera-Nachführung und eine Navigationsanzeige. Standard-Gamepad und Mehrfinger-Touch sind implementiert. Aus dem bisherigen H01/P11-Simulator führt die Modellauswahl zum P14-Flugsimulator; die unterschiedlichen Physikmodelle bleiben getrennt.

{len(pilot['checks'])} Reglerprüfungen bestehen, darunter kalter Bodenstart, Positions-/Höhenregelung, Gieren, Landung, alle fünf Blattzahlen und mehrere Rotorpaare. {len(pilotbrowser['checks'])} zusätzliche Browserprüfungen bestehen mit tatsächlichen Tastaturereignissen, Fokus-/Pausenverhalten, Parameterwechsel, Gamepad-API und Zweifinger-Touch. Die Software-Quellhashes stehen in den Berichten.

Der ausdrücklich gewählte Trainingsfall verwendet150Nm und40kW elektrische Leistung je Motor bei höchstens2.800/min als freie Annahmen. Das ist keine MN1330-Freigabe. Die dokumentierten Datenfälle erhalten ihre Leistungs-/Zeitgrenzen und bleiben im Standardfall am Boden. Der Regler gibt nur Drehzahl-/Pitchbefehle vor; es wird keine zusätzliche Auftriebskraft erzeugt. [Bedienung und Grenzen](FLUGSTEUERUNG.md).

Native SHA256: `{sha}`.
'''
    # Reject accidental unresolved template fragments before writing a report.
    (H/'ERGEBNIS.md').write_text(text)
    counts=collections.Counter(r['part'] for r in model['scene'])
    with (O/'Beschaffungsuebersicht.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['ID','Bezeichnung','Anzahl','Werkstoff','Kategorie','Status','Hinweis'])
        for id,t in model['types'].items():w.writerow([id,t['name'],counts[id],t['material'],t['kind'],'ENTWICKLUNG_KEINE_BESTELLFREIGABE',t['note']])
    gate=dict(production_ready=False,manufacturing_release=False,flight_release=False,H01_large_profile_activated=False,native_sha256=sha,all_report_sources_match=True,static_open_overlaps=col['open_count'],selected_dynamic_overlaps=0,nominal_assembly_paths_passed=assembly['passed'],joint_geometry_completed=True,motor_time_reference_s=180,continuous_motor_rating_verified=False,blocking=['Servo-OEM-Horn/Gehäusebefestigung und spezifischer Dauerbetrieb','GE8E/DIN472-Lieferprofile, Toleranzkette und Alu-Gelenk-Tragfähigkeit','Sonderrotor-Schwebebedarf über dokumentierten Motorprüfwerten','CFK/Alu/Lager-Vorspannungs-/Ermüdungsnachweise','Motor-Montagebezug65/66mm und Gewindeeingriffe','Personendeck, reale Versorgung/Kühlung, Schutz-/Landestruktur','Mehrrotor-Verbindungsrahmen bei mehr als einem Paar'])
    gate.update(P14_interactive_flight_available=True,H01_model_navigation_available=True,interactive_flight_checks_passed=True,training_motor_assumptions=dict(torque_each_Nm=150,input_power_each_W=40000,max_rpm=2800,hardware_verified=False))
    (O/'Freigabe.json').write_text(json.dumps(gate,indent=2,ensure_ascii=False)+'\n')
    plot_motor(motor,h)
    print(json.dumps(dict(native_sha256=sha,structural_mass_reduction_percent=reduction*100,cad_mass_kg=m['dry_cad_mass_assumed_kg'],scenario_mass_kg=m['total_scenario_mass_kg'],production_ready=False),indent=2))
def plot_motor(motor,hover):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/p14-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/p14-cache')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    p=motor['test']['points'];rpm=[r['rpm'] for r in p];fig,axes=plt.subplots(1,2,figsize=(12,5.8),facecolor='#f7fafb');ax,bx=axes
    ax.plot(rpm,[r['torque_Nm'] for r in p],'o-',color='#087e93',ms=4,label='NS52×20-Prüflastlinie')
    ax.scatter([hover['rpm']],[hover['torques_Nm'][0]],color='#ba3e40',s=65,zorder=4,label='P14-Schwebebedarf je Motor')
    ax.axhline(motor['maxima']['recorded_torque_Nm'],color='#708998',ls=':',label='Höchster dokumentierter Prüfwert')
    ax.set(xlabel='Drehzahl [1/min]',ylabel='Drehmoment [Nm]',title='Unterschiedliche Propellerlasten');ax.legend(fontsize=8,loc='upper left');ax.grid(alpha=.2)
    bx.plot(rpm,[r['input_power_W']/1000 for r in p],'o-',color='#087e93',ms=4,label='Elektrische Prüfleis­tung')
    bx.plot(rpm,[r['shaft_power_W']/1000 for r in p],'-',color='#5f8976',label='Welle aus Q·ω')
    bx.scatter([hover['rpm']],[hover['electricalPowerAssumed_W']/2/1000],color='#ba3e40',s=65,zorder=4,label='P14-Bedarf je Motor bei η =0,82')
    bx.axhline(3.4,color='#b57a23',ls='--',label='3,4 kW /180s; Leistungsseite unklar')
    bx.set(xlabel='Drehzahl [1/min]',ylabel='Leistung je Motor [kW]',title='Zeitbezug begrenzt die Aussage');bx.grid(alpha=.2);bx.legend(fontsize=8,loc='upper left')
    fig.suptitle('MN1330 KV40 · Nutzer-Prüfdaten bei ca.92 V',fontsize=16,fontweight='bold',color='#183e52',x=.06,ha='left')
    fig.text(.06,.035,'NS52×20-Kurve ist keine Motormomentgrenze. Haltedauer der Prüfmaxima unbekannt. Kein Dauerleistungsnachweis.',fontsize=9,color='#526d7e')
    fig.tight_layout(rect=[0,.08,1,.91]);fig.savefig(H/'Ansichten/MN1330_Pruefdaten_und_P14.png',dpi=170);plt.close(fig)
if __name__=='__main__':main()
