"""Actual D12 BREP section properties, gross fitting/ear screens and preload bounds."""
from pathlib import Path
import sys,json,zipfile,math
H=Path(__file__).resolve().parents[1];O=H/'Ausgabe/Festigkeit';sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/share/freecad/Mod'])
import FreeCAD as A,Part
M=json.loads((H/'Ausgabe/Regler_Montage.json').read_text());c=next(c for c in M['configurations'] if c['propeller_index']==9 and c['variant']=='V4');D=json.loads((O/'Verbindungen.json').read_text());j=next(c for c in D['cases'] if c['propeller_index']==9 and c['variant']=='V4');work=Path('/tmp/d12_strength_sections');work.mkdir(exist_ok=True)
with zipfile.ZipFile(H/'Ausgabe/Quad_Reglerhalter_Landefuesse.FCStd') as z:
 for name in ['FootBase','WearSole']:(work/(name+'.brp')).write_bytes(z.read('LAND_P9_V4_'+name+'.Shape.brp'))
s=Part.Shape();s.read(str(work/'FootBase.brp'));sole=Part.Shape();sole.read(str(work/'WearSole.brp'));sections=[];F=j['F_per_foot_N'];cx=c['cx']
for dx in [0,5,9.9,10.1,12,15,20,23,24,25,26,27,30,33,33.9,34.1,38]:
 wires=s.slice(A.Vector(1,0,0),cx+dx);face=Part.makeFace(wires,'Part::FaceMakerBullseye');assert face.isValid() and face.Area>0;z=sum(f.Area*f.CenterOfMass.z for f in face.Faces)/face.Area;Iy=sum(f.MatrixOfInertia.A22+f.Area*(f.CenterOfMass.z-z)**2 for f in face.Faces);Z=min(Iy/(face.BoundBox.ZMax-z),Iy/(z-face.BoundBox.ZMin));# Beam stress is only an idealized lower-dimensional screen.
 Mpoint=F/2*(50-dx) if dx<=50 else 0;Muniform=abs(F/256*(dx+64)**2-F/2*(dx+50));sections.append(dict(radial_offset_mm=dx,area_mm2=face.Area,Iy_mm4=Iy,minimum_section_modulus_mm3=Z,centre_point_ground_M_Nmm=Mpoint,uniform_ground_M_Nmm=Muniform,centre_point_nominal_bending_MPa=Mpoint/Z,uniform_ground_nominal_bending_MPa=Muniform/Z,scope='Symmetric two-end forces F/2 at+-50mm,ideal central point or uniformly distributed ground over128mm;actual FE end force asymmetry,local plug moments and pocket stress concentrations excluded.'))
contact=sum(f.Area for f in sole.Faces if isinstance(f.Surface,Part.Plane) and abs(f.BoundBox.ZMin+268)<1e-5 and abs(f.BoundBox.ZMax+268)<1e-5)
fittings=[]
for b in j['bonds']:
 wr=b['wrench_N_Nmm'];N=abs(wr[2]);V=math.hypot(wr[0],wr[1]);Mb=math.hypot(wr[3],wr[4]);T=abs(wr[5]);ro=8.3;ri=6.3;area=math.pi*(ro*ro-ri*ri);I=math.pi/4*(ro**4-ri**4);J=2*I;sig=N/area+Mb*ro/I;tau=T*ro/J+2*V/area;vm=math.sqrt(sig*sig+3*tau*tau);fittings.append(dict(leg=b['leg'],end=b['end'],force_N=N,transverse_N=V,bending_Nm=Mb/1000,nominal_combined_longitudinal_MPa=sig,von_Mises_screen_MPa=vm,required_yield_MPa_with_factor1p5=1.5*vm,conditional_margin_if_yield250_MPa=250/(1.5*vm),compressive_face_eccentricity_mm=Mb/max(N,1e-9),face_only_moment_capacity_Nmm=N*10,scope='Unnotched annulus16.6/12.6 from CAD;moment/shear at CFK end applied to plug section;no 3D bond shear redistribution,fillet,notch,stress concentration or certificate.250MPa is a hypothetical aluminium yield,not an identified material.'))
preloads=[]
for grade,Sp in [('8.8',580),('10.9',830),('12.9',970)]:
 Fp=.7*Sp*8.78
 for retention in [.5,.7,1.]:
  for mu in [.1,.2,.35,.5]:
   N=2*math.pi*Fp*retention;capacity=mu*N;preloads.append(dict(grade_assumed=grade,proof_stress_MPa=Sp,preload_each_N=Fp,retained_fraction=retention,mu_assumed=mu,uniform_ring_normal_N=N,friction_capacity_N=capacity,mean_preload_pressure_MPa=2*Fp/(20*35),worst_D12_V4_root_demand_N=max(x['resultant_slip_demand_N'] for x in j['clamps']),passes_conditional_slip_demand=capacity>=max(x['resultant_slip_demand_N'] for x in j['clamps']),scope='Uniform full-ring contact is favourable;two bolts at70% proof,withoutprying.A property class is not evidence of actual bolts.'))
# Known OD tolerance vs nominal split-liner fit.
fits=[]
for od in [19.8,20.,20.2]:fits.append(dict(actual_OD_mm=od,nominal_effective_bore_mm=20.6-2*.3,diametral_clearance_mm=20.6-2*.3-od,liner_for_zero_nominal_clearance_mm=(20.6-od)/2))
# Ear load is a section screen; effective lever and prying require contact FE or test.
ears=[]
for grade,Sp in [('8.8',580),('12.9',970)]:
 f=.7*Sp*8.78;width=12-4.5;height=10.5-.25;Z=width*height**2/6
 for lever in [2,4,6]:
  sig=f*lever/Z;tau=f/(width*height);ears.append(dict(grade_assumed=grade,lever_assumed_mm=lever,net_width_mm=width,section_height_mm=height,bending_MPa=sig,shear_MPa=tau,VM_MPa=math.sqrt(sig*sig+3*tau*tau),required_yield_factor1p5_MPa=1.5*math.sqrt(sig*sig+3*tau*tau),scope='Simple net rectangular ear cantilever,not actual ring contact/prying FE;fillets and bolt bearing excluded.'))
result=dict(native_sha256=M['native_sha256'],qualified=False,foot_sections=sections,sole_nominal_initial_contact_area_mm2=contact,sole_pressure_at_design_force_MPa=F/contact,spigots=fittings,preload_scenarios=preloads,ear_screens=ears,known_OD_fit_sensitivity=fits,formula_scope='Actual BREP section properties;idealized beam/annular stress and preload requirements.No laminate or adhesive manufacturing qualification.')
(O/'Querschnitt_Verbindung_Details.json').write_text(json.dumps(result,indent=2));print('CAD sections',len(sections),'sole area',contact);print('worst foot section point/uniform',max(x['centre_point_nominal_bending_MPa'] for x in sections),max(x['uniform_ground_nominal_bending_MPa'] for x in sections));print('upper spigot required yield factor1p5',max(x['required_yield_MPa_with_factor1p5'] for x in fittings))
