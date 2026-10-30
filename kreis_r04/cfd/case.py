#!/usr/bin/env python3
"""REKONSTRUKTION (2026-10-30): OpenFOAM-v1912-Fall fuer den 45-Grad-Sektor erzeugen.

Stationaer, inkompressibel, simpleFoam + kOmegaSST, zwei gegenlaeufige MRF-Zonen
(untere Ebene +omega, obere -omega um z), zyklische Sektorflaechen (createPatch).
Schwebefall ohne Anstroemung. Erwartet das Netz aus gmsh_mesh.py unter cases/<name>/<name>.msh.

    python case.py free_tet_c_u40 --u 40 [--iterations 3000]

UNGETESTET: In der Rekonstruktionsumgebung war kein OpenFOAM installiert. Die Dictionaries
sind nach v1912-Syntax geschrieben, aber nicht mit gmshToFoam/checkMesh/simpleFoam geprueft.
"""
import argparse, json, math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import profil

RHO, NU = 1.225, 1.5e-5
HEADER = '''FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    object      {obj};
}}
'''
WALLS = ('wing_lower', 'wing_upper', 'guides')
FAR = ('outer', 'top', 'bottom')


def write(case, rel, cls, body):
    p = case/rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HEADER.format(cls=cls, obj=p.name)+body)


def field(case, name, cls, dim, internal, bc):
    body = f'dimensions      {dim};\ninternalField   uniform {internal};\nboundaryField\n{{\n'
    for patch, spec in bc.items():body += f'    {patch}\n    {{\n        {spec}\n    }}\n'
    write(case, f'0/{name}', cls, body+'}\n')


def setup(name, u_ref, iterations, patches):
    case = HERE/'cases'/name; om = profil.omega(u_ref)
    k0 = 1.5*(.01*u_ref)**2; w0 = math.sqrt(k0)/(.09**.25*.01)
    cyc = {'cyclic_0': 'type cyclic;', 'cyclic_45': 'type cyclic;'}
    inner = {'inner': 'type slip;'}
    present = lambda d: {k: v for k, v in d.items() if k in patches}
    wall = lambda spec: present({p: spec for p in WALLS})
    far = lambda spec: present({p: spec for p in FAR})
    field(case, 'U', 'volVectorField', '[0 1 -1 0 0 0 0]', '(0 0 0)',
          {**wall('type noSlip;'), **far('type pressureInletOutletVelocity; value uniform (0 0 0);'), **inner, **cyc})
    field(case, 'p', 'volScalarField', '[0 2 -2 0 0 0 0]', '0',
          {**wall('type zeroGradient;'), **far('type totalPressure; p0 uniform 0; value uniform 0;'), 'inner': 'type zeroGradient;', **cyc})
    for f, val, wf in (('k', k0, 'kqRWallFunction'), ('omega', w0, 'omegaWallFunction')):
        field(case, f, 'volScalarField', '[0 2 -2 0 0 0 0]' if f == 'k' else '[0 0 -1 0 0 0 0]', f'{val:.6g}',
              {**wall(f'type {wf}; value uniform {val:.6g};'), **far(f'type inletOutlet; inletValue uniform {val:.6g}; value uniform {val:.6g};'),
               'inner': 'type zeroGradient;', **cyc})
    field(case, 'nut', 'volScalarField', '[0 2 -1 0 0 0 0]', '0',
          {**wall('type nutkWallFunction; value uniform 0;'), **far('type calculated; value uniform 0;'), 'inner': 'type calculated; value uniform 0;', **cyc})
    write(case, 'constant/transportProperties', 'dictionary', f'transportModel  Newtonian;\nnu              {NU};\n')
    write(case, 'constant/turbulenceProperties', 'dictionary', 'simulationType RAS;\nRAS\n{\n    RASModel kOmegaSST;\n    turbulence on;\n    printCoeffs on;\n}\n')
    mrf = ''
    for zone, sign in (('MRF_lower', 1), ('MRF_upper', -1)):
        nonrot = ' guides' if 'guides' in patches else ''
        mrf += (f'{zone}\n{{\n    cellZone    {zone};\n    active      yes;\n    nonRotatingPatches ({nonrot.strip()});\n'
                f'    origin      (0 0 0);\n    axis        (0 0 1);\n    omega       {sign*om:.8g};\n}}\n')
    write(case, 'constant/MRFProperties', 'dictionary', mrf)
    write(case, 'system/createPatchDict', 'dictionary', '''pointSync false;
patches
(
    { name cyclic_0;  patchInfo { type cyclic; neighbourPatch cyclic_45; transform rotational;
      rotationAxis (0 0 1); rotationCentre (0 0 0); } constructFrom patches; patches (cyclic_0); }
    { name cyclic_45; patchInfo { type cyclic; neighbourPatch cyclic_0;  transform rotational;
      rotationAxis (0 0 1); rotationCentre (0 0 0); } constructFrom patches; patches (cyclic_45); }
);
''')
    fos = ''
    for p in ('wing_lower', 'wing_upper'):
        fos += (f'    forces_{p}\n    {{\n        type forces; libs ("libforces.so"); writeControl timeStep; writeInterval 1;\n'
                f'        patches ({p}); rho rhoInf; rhoInf {RHO}; CofR (0 0 0);\n    }}\n')
    for p in [q for q in FAR+('inner',) if q in patches]:
        fos += (f'    flux_{p}\n    {{\n        type surfaceFieldValue; libs ("libfieldFunctionObjects.so"); writeControl timeStep; writeInterval 1;\n'
                f'        regionType patch; name {p}; operation sum; fields (phi); writeFields false;\n    }}\n')
    write(case, 'system/controlDict', 'dictionary', f'''application simpleFoam;
startFrom latestTime; startTime 0; stopAt endTime; endTime {iterations}; deltaT 1;
writeControl timeStep; writeInterval 500; purgeWrite 2; writeFormat binary; writePrecision 8;
runTimeModifiable true;
functions
{{
{fos}}}
''')
    write(case, 'system/fvSchemes', 'dictionary', '''ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes
{
    default none;
    div(phi,U) bounded Gauss linearUpwindV grad(U);
    div(phi,k) bounded Gauss upwind;
    div(phi,omega) bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''')
    write(case, 'system/fvSolution', 'dictionary', '''solvers
{
    p { solver GAMG; smoother GaussSeidel; tolerance 1e-8; relTol 0.05; }
    "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0.1; }
}
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent yes;
    residualControl { p 1e-6; U 1e-7; "(k|omega)" 1e-7; }
}
relaxationFactors { equations { U 0.5; "(k|omega)" 0.5; } fields { p 0.3; } }
''')
    run = f'''#!/bin/sh
# REKONSTRUKTION, ungetestet. OpenFOAM v1912 Umgebung vorausgesetzt.
cd "${{0%/*}}" || exit 1
set -e
gmshToFoam {name}.msh > log.gmshToFoam 2>&1
createPatch -overwrite > log.createPatch 2>&1
checkMesh -allGeometry -allTopology > log.checkMesh 2>&1 || true
simpleFoam > log.simpleFoam 2>&1
'''
    (case/'Allrun').write_text(run); (case/'Allrun').chmod(0o755)
    meta = {'fall': name, 'status': 'REKONSTRUKTION_FALLDEFINITION_UNGETESTET', 'U_ref_m_s': u_ref, 'omega_rad_s': om,
            'rho': RHO, 'nu': NU, 'turbulenzmodell': 'kOmegaSST', 'mrf': {'MRF_lower': om, 'MRF_upper': -om},
            'sektor_deg': 45, 'iterationen': iterations, 'patches': sorted(patches)}
    (case/'case.json').write_text(json.dumps(meta, indent=2))
    return case


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--u', type=float, required=True)
    ap.add_argument('--iterations', type=int, default=3000); a = ap.parse_args()
    rep = json.loads((HERE/'results'/f'Netzpruefung_{a.name}.json').read_text())
    if not rep.get('netzpruefung_bestanden'):
        sys.exit(f'{a.name}: Netzpruefung nicht bestanden, kein Fall erzeugt')
    print(setup(a.name, a.u, a.iterations, [k for k, v in rep['Randflaechen'].items() if v]))


if __name__ == '__main__':
    main()
