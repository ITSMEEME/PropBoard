#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -f local.env ]]; then set -a; source ./local.env; set +a; fi
export LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)"
export CFD_PROFILE="${CFD_PROFILE:-fullscale}"
command="${1:-status}"; if (($#)); then shift; fi
args=()
while (($#)); do
  case "$1" in
    --profile) export CFD_PROFILE="$2"; shift 2;;
    *) args+=("$1"); shift;;
  esac
done
[[ "$CFD_PROFILE" == fullscale || "$CFD_PROFILE" == model ]] || { echo 'Profil: fullscale oder model'; exit 2; }
export CFD_REQ_SHA="$(sha256sum requirements.txt | cut -d' ' -f1)"
docker compose version >/dev/null
# Bind mounts refer to this machine; a remote daemon would use different files.
endpoint="${DOCKER_HOST:-$(docker context inspect --format '{{.Endpoints.docker.Host}}')}"
[[ "$endpoint" == unix://* ]] || { echo 'Bitte einen lokalen Docker-Kontext verwenden.'; exit 2; }
mkdir -p work
manager() { docker compose run --rm --no-deps manager "$@"; }
run_solver() { export CFD_STAGE="$1"; docker compose up -d monitor; docker compose run --rm --no-deps solver; manager report; }
case "$command" in
 build) docker compose build manager; docker compose pull solver;;
 prepare) manager prepare;;
 preflight|report|status|refine|resume) manager "$command" "${args[@]}";;
 pilot) manager pilot; run_solver pilot;;
 run) run_solver run;;
 verify) manager verify; run_solver verify;;
 optimize)
   manager prepare; run_solver run
   manager resume; run_solver run
   manager refine "${args[@]}"; run_solver run
   manager resume; run_solver run
   manager verify; run_solver verify;;
 serve) docker compose up -d viewer monitor; echo "http://127.0.0.1:${CFD_VIEW_PORT:-8766}/$CFD_PROFILE/Ausgabe/CFD_Vergleich.html";;
 stop) docker compose run --rm --no-deps --entrypoint /bin/bash solver -lc 'bash /project/bin/request_stop.sh';;
 down) docker compose down;;
 *) echo 'Befehle: build prepare preflight pilot run refine resume verify optimize report status serve stop down'; exit 2;;
esac
