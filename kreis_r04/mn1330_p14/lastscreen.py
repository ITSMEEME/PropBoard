"""Demand-only linear beam / inertial pitch screen; no invented allowables."""
import json,math,sys,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'Ausgabe';sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD as A,Part
from kinematik import derive,solve,D,dist
def main():
    c=json.loads((O/'Eingaben.json').read_text());g=c['geometry'];q=derive(c);types={r['id']:r for r in json.loads((O/'Teile.json').read_text())}
    cfk=types['CFK01'];s=Part.read(str(O/'STEP_Sonderteile/CFK01.step'));start=q['blade_root_mm'];end=g['rotor_radius_mm'];sections=[];dx=.2
    for k in range(41):
        x=start+1+(end-start-2)*k/40
        cut=s.common(Part.makeBox(dx,220,100,A.Vector(x-dx/2,-80,-50)))
        solids=cut.Solids;vol=sum(t.Volume for t in solids);z=sum(t.Volume*t.CenterOfMass.z for t in solids)/vol
        I=sum(t.MatrixOfInertia.A22+t.Volume*(t.CenterOfMass.z-z)**2 for t in solids)/dx
        area=vol/dx;zmax=max(abs(cut.BoundBox.ZMax-z),abs(cut.BoundBox.ZMin-z))
        sections.append(dict(r_mm=x,area_mm2=area,I_flap_mm4=I,zmax_mm=zmax))
    mass=json.loads((O/'Pruefung.json').read_text())['mass']['total_scenario_mass_kg'];n=g['blades_per_rotor'];loadfactor=c['operating']['load_factor'];F=mass*9.81*loadfactor/(2*n*g['lift_units'])
    a=start/1000;b=end/1000;den=(b**3-a**3)/3
    def moment(x):return F/den*((b**4-x**4)/4-x*(b**3-x**3)/3)
    def M_at(x):return moment(max(a,x))+F*max(0,a-x)
    beam=[]
    for E in c['operating']['cfk_modulus_range_Pa']:
        integral=0;stress=0
        for i,t in enumerate(sections):
            x=t['r_mm']/1000;M=M_at(x);I=t['I_flap_mm4']*1e-12;stress=max(stress,M*t['zmax_mm']*1e-3/I)
            if i:
                p=sections[i-1];xp=p['r_mm']/1000
                f0=M_at(xp)*(b-xp)/(E*p['I_flap_mm4']*1e-12);f1=M*(b-x)/(E*I)
                integral+=(f0+f1)/2*(x-xp)
        beam.append(dict(E_assumed_Pa=E,tip_deflection_mm=integral*1000,max_flap_stress_MPa=stress/1e6))
    r_support=(q['root_r_mm']+42.5)*1e-3;Mb=M_at(r_support);d=.025;di=.014;area=math.pi/4*(d*d-di*di);I=math.pi/64*(d**4-di**4)
    rpmcases=[];rho=cfk['density_assumed_kg_m3'];cg=cfk['cg_mm'];J=cfk['inertia_cg_kgm2'];m=cfk['mass_kg']
    # Integral y²-z² about the radial pitch axis. The quarter-chord offset is
    # explicitly retained, rather than approximating a massless blade.
    S=(J[2][2]-J[1][1])+m*((cg[1]*1e-3)**2-(cg[2]*1e-3)**2)
    Ix=J[0][0]+m*((cg[1]*1e-3)**2+(cg[2]*1e-3)**2)
    for rpm in [850,1500,2100]:
        w=rpm*2*math.pi/60;centrifugal=m*w*w*cg[0]*1e-3
        # Add the mass of the root metal/clamps, using their CAD CGs.
        extra=sum(types[id]['mass_kg']*(types[id]['cg_mm'][0]*1e-3) for id in ['A13','A13C','A13D','A14','A14W','A14S','A16A','A18','A18B','A18S','A18T','A18W','F6_PITCH_END'])
        extra+=4*types['F6_ROOT']['mass_kg']*types['F6_ROOT']['cg_mm'][0]*1e-3
        centrifugal+=w*w*extra
        inertial_pitch=.5*w*w*S*math.sin(2*g['neutral_pitch_deg']*D)
        # A deliberately visible aerodynamic hinge-moment assumption, not an
        # OEM polar or a validated quarter-chord moment coefficient.
        cm=.05;cch=g['chord_mm']/1000;aero_hinge=.5*1.225*w*w*cch*cch*cm*(b**3-a**3)/3
        cyc_amp=.5*D*g['swash_joint_r_mm']/g['pitch_lever_mm'];pitch_acc=w*w*cyc_amp
        pitch_inertia=Ix*pitch_acc
        hinge_abs=abs(inertial_pitch)+aero_hinge+abs(pitch_inertia)
        linkforce=hinge_abs/(g['pitch_lever_mm']*1e-3*math.cos(g['neutral_pitch_deg']*D))
        # Symmetric collective virtual work: dtheta/dalpha measured from the
        # closed linkage. Three equal motors share all blade hinge torques.
        eps=.01;s0=solve(c);s1=solve(c,eps)
        dtheta=sum(s1['pitches_deg'][i]-s0['pitches_deg'][i] for i in range(n))/n
        dalpha=sum(s1['servo_deg'][i]-s0['servo_deg'][i] for i in range(3))/3
        virtual_ratio=abs(dtheta/dalpha);servo_collective=abs(inertial_pitch+aero_hinge)*n/3*virtual_ratio
        servo_conservative=hinge_abs*n/3*virtual_ratio
        clampF=(m*cg[0]*1e-3+types['A16A']['mass_kg']*types['A16A']['cg_mm'][0]*1e-3)*w*w/4
        rpmcases.append(dict(rpm=rpm,centrifugal_root_N=centrifugal,CFK_clamp_M6_nominal_force_each_N=clampF,CFK_clamp_M6_nominal_tensile_MPa=clampF/20.1,shaft_nominal_axial_MPa=centrifugal/area/1e6,shaft_flap_MPa=Mb*(d/2)/I/1e6,shaft_nominal_sum_MPa=(centrifugal/area+Mb*(d/2)/I)/1e6,cfk_inertial_pitch_torque_Nm=inertial_pitch,aero_hinge_Cm_assumed=cm,aero_hinge_torque_Nm=aero_hinge,cyclic_pitch_accel_rad_s2=pitch_acc,cfk_pitch_inertia_torque_Nm=pitch_inertia,linkforce_demand_N=linkforce,servo_virtual_ratio=virtual_ratio,servo_collective_demand_Nm=servo_collective,servo_peak_abs_sum_screen_Nm=servo_conservative,servo_stall_Nm=c['servo']['stall_torque_Nm'],servo_continuous_rating_Nm=c['servo']['continuous_torque_Nm'],servo_thermal_screen_assumption_Nm=None))
    bearing_couple=Mb/.035
    out=dict(production_ready=False,method='Isotropic uniform-E linear beam from 41 exact CAD slices; no centrifugal stiffening. Demand only, no strength/fatigue allowables.',load_case=dict(total_mass_kg=mass,load_factor=loadfactor,flap_force_per_blade_N=F,flap_root_moment_Nm=F*((b**4-a**4)/4/den-a),shaft_last_support_moment_Nm=Mb,bearing_pair_spacing_mm=35,bearing_couple_reaction_N=bearing_couple),cfk_sections=sections,beam=beam,rpm_cases=rpmcases,unresolved=['Orthotrope Laminate, Delamination und CFK-Flansch/Bohrung nicht nachgewiesen','Kerbfaktoren an D-Flach, Gewinden, hohler Welle und Klemmung fehlen','Alu-Bolzen/Vorspannung/Reibung/galvanische Trennung und Temperatur nicht nachgewiesen','Lagertragzahlen, Paarvorspannung, Lebensdauer und Gehäuseverformung fehlen','Anwendungsspezifischer Servo-Dauerbetrieb/Kühlung, dynamische Reibung und OEM-Hornanschluss offen','Wurzelstern-Verformung, Nutzlastanschluss und Motorhochlauf brauchen FE/Prüfversuche','MN1330:3.4kW beziehen sich auf180s, nicht Dauerleistung; Prüftabellen-Haltedauer unbekannt'])
    out['native_sha256']=hashlib.sha256((O/'P14_MN1330_Leichtbau.FCStd').read_bytes()).hexdigest()
    (O/'Lastscreen.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps({k:v for k,v in out.items() if k!='cfk_sections'},indent=2),flush=True)
if __name__=='__main__':main()
