#!/bin/bash
set -eu
: "${CFD_WORKDIR:?}"
touch "$CFD_WORKDIR/stop_requested"
for file in "$CFD_WORKDIR"/cases/K??_*/running; do
    [ -f "$file" ] || continue
    case_dir="${file%/running}"
    foamDictionary "$case_dir/system/controlDict" -entry stopAt -set writeNow >/dev/null 2>&1 || true
done
echo 'Checkpoint-Stopp angefordert. Netzaufbau kann beim nächsten Start neu beginnen.'
