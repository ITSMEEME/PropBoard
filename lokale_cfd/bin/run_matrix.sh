#!/bin/bash
set -euo pipefail
: "${CFD_WORKDIR:?}"
cd "$CFD_WORKDIR"
stage="${CFD_STAGE:-run}"
case "$stage" in run|pilot|verify) ;; *) echo 'Unbekannte Rechenstufe'; exit 2;; esac
jobs="${CFD_JOBS:-1}"; ranks="${CFD_MPI_RANKS:-2}"
[[ "$jobs" =~ ^[1-8]$ && "$ranks" =~ ^[1-9][0-9]?$ ]] || exit 2
available="$(nproc)"
if [ -r /sys/fs/cgroup/cpu.max ]; then
    read -r quota period < /sys/fs/cgroup/cpu.max
    if [ "$quota" != max ]; then
        limited=$((quota/period)); [ "$limited" -ge 1 ] || limited=1
        [ "$limited" -ge "$available" ] || available="$limited"
    fi
fi
[ $((jobs*ranks)) -le "$available" ] || { echo 'MPI-Ränge × Fälle überschreiten die sichtbaren CPU-Kerne.'; exit 2; }
queue="${stage}_queue.txt"
[ -f "$queue" ] || { echo 'Zuerst prepare / pilot / verify ausführen.'; exit 2; }
rm -f stop_requested
trap 'bash /project/bin/request_stop.sh; wait || true; exit 0' TERM INT
pids=(); failed=0
while IFS= read -r name; do
    [ -n "$name" ] || continue
    [[ "$name" =~ ^K[0-9]{2}_(coarse|fine|domain|pilot)$ ]] || exit 2
    [ ! -f stop_requested ] || break
    bash /project/bin/run_case.sh "$name" & pids+=("$!")
    if [ "${#pids[@]}" -ge "$jobs" ]; then
        for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
        pids=()
    fi
done < "$queue"
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
exit "$failed"
