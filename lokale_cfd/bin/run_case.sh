#!/bin/bash
set -euo pipefail
name="${1:?}"; [[ "$name" =~ ^K[0-9]{2}_(coarse|fine|domain|pilot)$ ]] || exit 2
cd "${CFD_WORKDIR:?}/cases/$name"
[ ! -f done ] || { echo "[$name] gespeicherten Lauf wiederverwenden"; exit 0; }
source runtime.env
touch running; rm -f failed
trap 'rc=$?; rm -f running; if [ "$rc" -ne 0 ]; then echo "$rc" > failed; echo "['"$name"'] FEHLER: Protokolle und Bericht prüfen."; fi' EXIT
if [ ! -f mesh_ready ]; then
    echo "[$name] Netzaufbau"
    rm -rf constant/polyMesh
    blockMesh > log.blockMesh 2>&1
    for side in Upper Lower; do surfaceCheck "constant/triSurface/wing${side}.stl" > "log.surface${side}" 2>&1; grep -q 'Surface is closed.' "log.surface${side}"; grep -q 'Surface has no illegal triangles.' "log.surface${side}"; done
    surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
    snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
    checkMesh -allTopology > log.checkMesh 2>&1
    checkMesh -allGeometry -allTopology > log.checkMeshExtended 2>&1
    grep -q 'Mesh OK.' log.checkMesh
    awk '/Extruding [0-9]+ out of/ {p=$7;gsub(/[^0-9.]/,"",p)} END{exit !(p+0>=70)}' log.snappyHexMesh
    awk -v d="$DOMAIN_VOLUME" -v s="$EXPECTED_SOLID_VOLUME" 'function abs(x){return x<0?-x:x} /Total volume =/{match($0,/Total volume = [eE0-9+.-]+/);v=substr($0,RSTART,RLENGTH);sub(/.*= /,"",v);sub(/[.]$/,"",v);err=abs((d-v)/s-1);found=1} END{exit !(found && err<0.05)}' log.checkMesh
    topoSet > log.topoSet 2>&1
    sha256sum constant/triSurface/wing*.stl system/blockMeshDict system/snappyHexMeshDict system/fvSchemes system/fvSolution constant/MRFProperties constant/transportProperties constant/turbulenceProperties > mesh_inputs.sha256
    touch mesh_ready
else
    sha256sum -c mesh_inputs.sha256 > log.inputCheck 2>&1 || { echo 'Eingaben eines berechneten Falls verändert: Fall zuerst archivieren.'; exit 41; }
fi
[ ! -f "$CFD_WORKDIR/stop_requested" ] || exit 0
latest_full() { find "${1:-.}" -maxdepth 2 -type f \( -name U -o -name U.gz \) | awk -F/ '{v=$(NF-1);if(v ~ /^[0-9]+([.][0-9]+)?$/ && v+0>m)m=v+0}END{print m+0}'; }
if [ -f "$CFD_WORKDIR/stop_requested" ]; then echo "[$name] Stopp vor Solverstart"; exit 0; fi
latest="$(latest_full .)"
if [ "$latest" = 0 ] && [ -f warm_start.txt ]; then
    parent="$(cat warm_start.txt)"; [[ "$parent" =~ ^K[0-9]{2}_(coarse|fine)$ ]] || exit 2
    source_case="$CFD_WORKDIR/cases/$parent"; source_time="$(latest_full "$source_case")"
    [ "$source_time" != 0 ] || { echo 'Vollständiges Elternfeld fehlt'; exit 42; }
    mapFields "$source_case" -sourceTime "$source_time" -consistent > log.mapFields 2>&1
fi
# Align the restart interval to 50 steps, guaranteeing a full final checkpoint.
floor=200; [[ "$name" != *_pilot ]] || floor=50
target="$(awk -v minimum="$floor" -v a="$latest" -v b="$MINIMUM_ITERATIONS" 'BEGIN{n=b-a;if(n<minimum)n=minimum;n=50*int((n+49)/50);print a+n}')"
foamDictionary system/controlDict -entry startFrom -set startTime >/dev/null
foamDictionary system/controlDict -entry startTime -set "$latest" >/dev/null
foamDictionary system/controlDict -entry stopAt -set endTime >/dev/null
foamDictionary system/controlDict -entry endTime -set "$target" >/dev/null
foamDictionary system/controlDict -entry writeInterval -set 50 >/dev/null
foamDictionary system/decomposeParDict -entry numberOfSubdomains -set "${CFD_MPI_RANKS:-2}" >/dev/null
[ ! -f log.simpleFoam ] || cp log.simpleFoam "log.simpleFoam.before_${latest}"
decomposePar -time "$latest" -force > log.decomposePar 2>&1
echo "[$name] CFD: $latest → $target, ${CFD_MPI_RANKS:-2} MPI-Prozesse"
mpirun -np "${CFD_MPI_RANKS:-2}" --bind-to none simpleFoam -parallel > log.simpleFoam 2>&1 & solver_pid=$!
while kill -0 "$solver_pid" 2>/dev/null; do
    iteration="$(awk '/^Time =/{t=$3}END{print t}' log.simpleFoam)"
    echo "[$name] Iteration ${iteration:-Start} / $target"
    sleep 30
done
wait "$solver_pid"
reconstructPar -latestTime > log.reconstructPar 2>&1
latest="$(latest_full .)"
if [ -f "$CFD_WORKDIR/stop_requested" ]; then echo "[$name] Checkpoint $latest gespeichert"; exit 0; fi
# Isolated postprocessing: never overwrite force histories with a one-point export.
id="${name%%_*}"; level="${name#*_}"; probe="$CFD_WORKDIR/cases/${id}_probe_${latest}_${level}"
mkdir -p "$probe/system" "$probe/$latest"
if [ ! -d "$probe/constant" ]; then cp -al constant "$probe/constant" 2>/dev/null || cp -a constant "$probe/constant"; fi
cp system/flowControlDict "$probe/system/controlDict"; cp system/fvSchemes system/fvSolution "$probe/system/"
for f in U p; do cp "$latest/$f" "$probe/$latest/$f"; done
cp case.json "$probe/case.json"
(cd "$probe" && postProcess -time "$latest" -fields '(U p)' > log.sample 2>&1)
touch done
echo "[$name] abgeschlossen; numerische Auswertung entscheidet über Zulässigkeit"
