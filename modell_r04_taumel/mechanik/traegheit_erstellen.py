#!/usr/bin/env python3
"""Extract effective homogeneous CAD blade mass/inertia; not measured infill."""
import json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'cad'));sys.path.insert(0,os.environ.get('FREECAD_LIB',str(HERE.parents[1]/'.cfd-tools/freecad/usr/lib')))
import FreeCAD,erstellen as model
shape=model.blade_shape();assert len(shape.Solids)==1
s=shape.Solids[0];cg=s.CenterOfMass;J=s.MatrixOfInertia
rho=model.P['print']['density']['PA-CF']*model.P['print']['fill']['blade']/1e9
out={'volume_mm3':s.Volume,'mass_kg':s.Volume*rho,'cg_mm':[cg.x,cg.y,cg.z],
 'Iyy_cg_kgm2':J.A22*rho*1e-6,'Izz_cg_kgm2':J.A33*rho*1e-6,
 'delta_I_about_radial_pitch_axis_kgm2':(J.A33-J.A22+s.Volume*(cg.y**2-cg.z**2))*rho*1e-6,
 'Ixx_about_pitch_axis_kgm2':(J.A11+s.Volume*(cg.y**2+cg.z**2))*rho*1e-6,
 'density_kg_m3':model.P['print']['density']['PA-CF'],'effective_fill':model.P['print']['fill']['blade']}
(HERE/'Fluegel_Traegheit.json').write_text(json.dumps(out,indent=2));print('Effective CAD inertia extracted')
