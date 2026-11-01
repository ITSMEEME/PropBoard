#!/usr/bin/env python3
"""Independent 3D coaxial-rotor OpenFOAM cases from the saved eleven-parameter finalists.
Full 360 degrees, frozen relative blade position, two counter-rotating MRF zones.
No hardware, transition or time-resolved blade-passage claim.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
SOURCE=H.parent/'simulation/Ergebnisse/P11/Kandidatensuche.json'
IMAGE='opencfd/openfoam-default@sha256:1ba02114b1c025c370f2e269a07677c16c9bea8d990fcd75ac8378aff9d41b50'

def header(name,cls='dictionary'):
    return f'FoamFile\n{{ version 2.0; format ascii; class {cls}; object {name}; }}\n'
def write(case,rel,body,cls='dictionary'):
    p=case/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(header(p.name,cls)+body+'\n')
def profile(q,tc):return 5*tc*(.2969*np.sqrt(q)-.126*q-.3516*q*q+.2843*q**3-.1015*q**4)

def blade_triangles(d,level,direction):
    q=(1-np.cos(np.linspace(0,np.pi,49)))/2
    contour=np.r_[q,q[-1:0:-1]];z=np.r_[profile(q,d['thickness']),-profile(q[-1:0:-1],d['thickness'])]
    loops=[]
    for f in np.linspace(0,1,13):
        r=(d['rootRadiusMm']+(d['diameterMm']/2-d['rootRadiusMm'])*f)/1000
        chord=d['chordMm']/1000*(1+(d['taper']-1)*f)
        theta=math.radians(d['pitchUpperDeg' if level==0 else 'pitchLowerDeg']+d['twistDeg']*f)
        x=(contour-.25)*chord;thick=z*chord
        loops.append(np.column_stack([np.full(len(x),r),-direction*(x*np.cos(theta)+thick*np.sin(theta)),(1 if level==0 else -1)*d['spacingMm']/2000-x*np.sin(theta)+thick*np.cos(theta)]))
    triangles=[];n=len(contour)
    for a,b in zip(loops[:-1],loops[1:]):
        for j in range(n):
            k=(j+1)%n;triangles.extend([[a[j],b[j],b[k]],[a[j],b[k],a[k]]])
    for ring,reverse in [(loops[0],False),(loops[-1],True)]:
        center=ring.mean(axis=0)
        for j in range(n):
            t=[center,ring[j],ring[(j+1)%n]];triangles.append(t[::-1] if reverse else t)
    triangles=np.array(triangles)
    volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
    if volume<0:triangles=triangles[:,::-1]
    assert abs(volume)>1e-10
    all_tri=[]
    for j in range(d['blades']):
        a=2*np.pi*j/d['blades'];rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        all_tri.append(triangles@rot.T)
    return np.concatenate(all_tri)
def stl(path,triangles):
    with path.open('wb') as f:
        f.write(b'P11 sampled NACA symmetric foil; finite trailing edge'.ljust(80,b' '));f.write(struct.pack('<I',len(triangles)))
        for t in triangles:
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=np.linalg.norm(n)
            f.write(struct.pack('<12fH',*n,*t.flatten(),0))

def build(rank,level='coarse',iterations=1000):
    source=json.loads(SOURCE.read_text());row=source['top10Aerodynamic'][rank-1];d=row['design'];R=d['diameterMm']/2000
    case=H/'cases'/f'K{rank:02d}_{level}'
    if (case/'constant/polyMesh').exists():
        raise RuntimeError(f'{case}: computed mesh already exists. Archive this generated case before regenerating inputs; never overwrite an active solver case.')
    (case/'constant/triSurface').mkdir(parents=True,exist_ok=True)
    for l,(name,sign) in enumerate([('wingUpper',1),('wingLower',-1)]):stl(case/f'constant/triSurface/{name}.stl',blade_triangles(d,l,sign))
    span=3*R;cells=24 if level=='coarse' else 32;layers=6 if level=='coarse' else 10;expansion=1.8 if level=='coarse' else 1.2;feature_angle=60 if level=='coarse' else 150
    vertices='\n'.join(f'({x*span} {y*span} {z*span})' for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
    write(case,'system/blockMeshDict',f'''scale 1;
vertices ({vertices});
blocks (hex (0 1 2 3 4 5 6 7) ({cells} {cells} {cells}) simpleGrading (1 1 1));
edges ();
boundary (far {{ type patch; faces ((0 3 2 1)(4 5 6 7)(0 1 5 4)(1 2 6 5)(2 3 7 6)(3 0 4 7)); }});
mergePatchPairs ();''')
    z=d['spacingMm']/2000;dz=min(.04,z*.7)
    write(case,'system/surfaceFeatureExtractDict','\n'.join(f'{n}.stl {{ extractionMethod extractFromSurface; extractFromSurfaceCoeffs {{ includedAngle 150; }} writeObj no; }}' for n in ['wingUpper','wingLower']))
    geometries='\n'.join(f'{n}.stl {{ type triSurfaceMesh; name {n}; }}' for n in ['wingUpper','wingLower'])
    geometries+=f'\nrotors {{type searchableBox; min ({-1.1*R} {-1.1*R} {-z-dz}); max ({1.1*R} {1.1*R} {z+dz});}}'
    surfaces='\n'.join(f'{n} {{ level (5 6); patchInfo {{ type wall; }} }}' for n in ['wingUpper','wingLower'])
    write(case,'system/snappyHexMeshDict',f'''castellatedMesh true; snap true; addLayers true;
geometry {{ {geometries} }}
castellatedMeshControls {{
 maxLocalCells 1500000; maxGlobalCells 2000000; minRefinementCells 0; maxLoadUnbalance 0.1; nCellsBetweenLevels 3;
 features ({{file "wingUpper.eMesh"; level 6;}}{{file "wingLower.eMesh"; level 6;}});
 refinementSurfaces {{ {surfaces} }}
 resolveFeatureAngle 30;
 refinementRegions {{ rotors {{ mode inside; levels ((1e15 2)); }} }}
 locationInMesh (0 0 {span*.9}); allowFreeStandingZoneFaces true;
}}
snapControls {{ nSmoothPatch 3; tolerance 2; nSolveIter 30; nRelaxIter 5; nFeatureSnapIter 10; implicitFeatureSnap false; explicitFeatureSnap true; multiRegionFeatureSnap false; }}
addLayersControls {{ relativeSizes false; layers {{ "wing.*" {{ nSurfaceLayers {layers}; }} }}
 expansionRatio {expansion}; firstLayerThickness 0.00001; minThickness 0.000005;
 nGrow 0; featureAngle {feature_angle}; slipFeatureAngle 30; nRelaxIter 5; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10;
 maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50;
}}
meshQualityControls {{
 maxNonOrtho 65; maxBoundarySkewness 4; maxInternalSkewness 4; maxConcave 80;
 minVol 1e-15; minTetQuality 1e-15; minArea -1; minTwist 0.02; minDeterminant 1e-8; minFaceWeight 0.001; minVolRatio 0.001; minTriangleTwist -1;
 nSmoothScale 4; errorReduction 0.75;
}}
writeFlags (scalarLevels layerSets layerFields); mergeTolerance 1e-6;''')
    actions=[];mrf=[]
    for name,zc,sign in [('upper',z,1),('lower',-z,-1)]:
        actions.append(f'{{name {name}Set; type cellSet; action new; source cylinderToCell; sourceInfo {{p1 (0 0 {zc-dz}); p2 (0 0 {zc+dz}); radius {1.08*R};}}}}')
        actions.append(f'{{name {name}Zone; type cellZoneSet; action new; source setToCellZone; sourceInfo {{set {name}Set;}}}}')
        mrf.append(f'{name} {{ cellZone {name}Zone; active yes; nonRotatingPatches (); origin (0 0 {zc}); axis (0 0 1); omega {sign*d["rpm"]*math.pi/30}; }}')
    write(case,'system/topoSetDict','actions ('+'\n'.join(actions)+');')
    write(case,'constant/MRFProperties','\n'.join(mrf))
    write(case,'constant/transportProperties','transportModel Newtonian; nu 1.5e-5;')
    write(case,'constant/turbulenceProperties','simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }')
    for name,cls,dim,value,wall,far in [
        ('U','volVectorField','0 1 -1 0 0 0 0','(0 0 0)','type fixedValue; value uniform (0 0 0);','type pressureInletOutletVelocity; value uniform (0 0 0);'),
        ('p','volScalarField','0 2 -2 0 0 0 0','0','type zeroGradient;','type totalPressure; p0 uniform 0; value uniform 0;'),
        ('k','volScalarField','0 2 -2 0 0 0 0','0.01','type kqRWallFunction; value uniform 0.01;','type inletOutlet; inletValue uniform 0.01; value uniform 0.01;'),
        ('omega','volScalarField','0 0 -1 0 0 0 0','10','type omegaWallFunction; value uniform 10;','type inletOutlet; inletValue uniform 10; value uniform 10;'),
        ('nut','volScalarField','0 2 -1 0 0 0 0','0','type nutUSpaldingWallFunction; value uniform 0;','type calculated; value uniform 0;')]:
        write(case,'0/'+name,f'dimensions [{dim}]; internalField uniform {value}; boundaryField {{ far {{ {far} }} "wing.*" {{ {wall} }} }}',cls)
    functions='\n'.join(f'forces_{n} {{ type forces; libs (forces); writeControl timeStep; writeInterval 1; patches ({n}); rho rhoInf; rhoInf 1.225; CofR (0 0 0); }}' for n in ['wingUpper','wingLower'])
    functions+='\nyPlus { type yPlus; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 50; }\n'
    functions+='\nfarFlux {type surfaceFieldValue; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name far; operation sum; fields (phi); writeFields false;}\n'
    functions+='\nfarAbsFlux {type surfaceFieldValue; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name far; operation sumMag; fields (phi); writeFields false;}\n'
    write(case,'system/controlDict',f'''application simpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {iterations}; deltaT 1;
writeControl timeStep; writeInterval {iterations}; purgeWrite 2; writeFormat binary; writePrecision 8; writeCompression on; timeFormat general; timePrecision 6; runTimeModifiable true;
functions {{ {functions} }}''')
    write(case,'system/decomposeParDict','numberOfSubdomains 2; method scotch;')
    write(case,'system/fvSchemes','''ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }''')
    write(case,'system/fvSolution','''solvers {
 p { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.05; }
 "(U|k|omega)" {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.1;}
}
SIMPLE {nNonOrthogonalCorrectors 0; consistent yes; residualControl {p 1e-5; U 1e-6; "(k|omega)" 1e-6;} }
relaxationFactors {fields {p 0.3;} equations {U 0.5; "(k|omega)" 0.5;}}''')
    run='''#!/bin/bash
set -euo pipefail
cd "${0%/*}"
rm -rf constant/polyMesh
blockMesh > log.blockMesh 2>&1
surfaceCheck constant/triSurface/wingUpper.stl > log.surfaceUpper 2>&1
surfaceCheck constant/triSurface/wingLower.stl > log.surfaceLower 2>&1
surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
checkMesh -allTopology > log.checkMesh 2>&1
checkMesh -allGeometry -allTopology > log.checkMeshExtended 2>&1
grep -q 'Mesh OK.' log.checkMesh
awk '/Extruding [0-9]+ out of/ {p=$7; gsub(/[^0-9.]/,"",p)} END {exit !(p+0>=70)}' log.snappyHexMesh
topoSet > log.topoSet 2>&1
decomposePar -force > log.decomposePar 2>&1
mpirun -np 2 --bind-to none simpleFoam -parallel > log.simpleFoam 2>&1
reconstructPar -latestTime > log.reconstructPar 2>&1
'''
    (case/'Allrun').write_text(run);(case/'Allrun').chmod(0o755)
    meta={'candidate_rank':rank,'level':level,'design':d,'source_search_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'native_sha256':source['native_sha256'],'image':IMAGE,'solver':'OpenFOAM 2412 simpleFoam kOmegaSST MRF','rho_kg_m3':1.225,'nu_m2_s':1.5e-5,'tipMach':row['tipMach'],'massKg':source['massKg'],'screeningThrustN':row['thrustN'],'screeningPowerW':row['mechanicalPowerW'],'domain_half_width_m':span,'iterations_requested':iterations,'mesh_setup':{'base_cells_per_axis':cells,'layers':layers,'expansion':expansion,'layer_feature_angle':feature_angle,'first_layer_m':1e-5},'limitations':['Stationary frozen-rotor MRF, no transient blade passages','Fully turbulent SST, no low-Re transition validation','Incompressible; tip Mach approaching 0.3 needs compressibility sensitivity','No hub, motor, supports or guide rings','Nominal symmetric NACA thickness family, no camber optimization','No structural, thermal, acoustic or measured validation']}
    (case/'case.json').write_text(json.dumps(meta,indent=2)+'\n');return case
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--rank',type=int);a.add_argument('--level',choices=['coarse','fine'],default='coarse');a.add_argument('--iterations',type=int,default=1000);args=a.parse_args()
    for rank in ([args.rank] if args.rank else range(1,11)):print(build(rank,args.level,args.iterations))
