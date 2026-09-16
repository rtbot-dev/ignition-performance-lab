#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
benchmark=${1:-jython-vibration}
case "$benchmark" in *[!a-z0-9-]*|"") echo "Invalid benchmark name"; exit 1;; esac
[ -f "$repo/benchmarks/$benchmark/benchmark.json" ] || { echo "Unknown benchmark: $benchmark"; exit 1; }
cd "$repo/benchmarks/$benchmark"
command -v docker >/dev/null || { echo 'Install and start Docker Desktop, then run this launcher again.'; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Start Docker Desktop, then run this launcher again.'; exit 1; }
. "$repo/scripts/port.sh"
if [ ! -f .env ]; then
  echo 'This starts a local Ignition trial and a bounded CPU load test.'
  echo 'License: https://inductiveautomation.com/ignition/license'
  printf 'Have you read and accepted the Ignition software license? [yes/no] '
  read -r consent
  [ "$consent" = yes ] || exit 1
  umask 077
  password=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
  printf 'ACCEPT_IGNITION_EULA=Y\nBENCH_PASSWORD=%s\nBENCH_CPUS=3\n' "$password" > .env
fi
mkdir -p results runtime
[ -f runtime/plan.json ] || cp plan.json runtime/plan.json
docker compose build prepare
docker compose up -d --no-build --remove-orphans
if command -v curl >/dev/null; then
  attempts=0
  until curl -fsS "$lab_url" >/dev/null 2>&1; do
    attempts=$((attempts + 1)); [ "$attempts" -lt 60 ] || { echo "Gateway is not ready. Inspect: docker compose logs gateway"; exit 1; }
    sleep 2
  done
fi
printf '\nOpen %s to control the benchmark.\nStop all services with: docker compose stop\n' "$lab_url"
if command -v open >/dev/null; then open "$lab_url"
elif command -v xdg-open >/dev/null; then xdg-open "$lab_url" >/dev/null 2>&1 || true
fi
printf '\nIgnition Designer connection\nGateway: http://localhost:%s\nUsername: benchmark\n' "$LAB_PORT"
configured_password=${BENCH_PASSWORD:-$(sed -n 's/^BENCH_PASSWORD=//p' .env | tail -n 1)}
printf 'Password: %s\nProject: performance-lab\n' "$configured_password"
printf 'These are the initial-setup credentials stored in this lab configuration.\nAn existing gateway volume retains its original password; this launcher does not reset it.\nKeep this terminal output private.\n'
