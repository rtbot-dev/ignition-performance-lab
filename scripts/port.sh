# Sourced by start.sh after checking Docker. Never stops a service without input.
lab_port=${LAB_PORT:-$(cat runtime/port 2>/dev/null || printf 9088)}
while :; do
  case "$lab_port" in ''|*[!0-9]*) echo 'Enter a port number from 1024 to 65535.'; lab_port=0;; esac
  if [ "${#lab_port}" -gt 5 ] || [ "$lab_port" -lt 1024 ] || [ "$lab_port" -gt 65535 ]; then
    printf 'Port [9089]: '; read -r lab_port || exit 1; lab_port=${lab_port:-9089}; continue
  fi
  port_owners=$(docker ps --filter "publish=$lab_port" --format '{{.Names}} {{.Label "com.docker.compose.project"}}') || exit 1
  conflicts=$(printf '%s\n' "$port_owners" | awk 'NF && $2 != "katenaria-lab-jython-vibration" {print $1}')
  occupied=false
  if [ -z "$port_owners" ] && command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$lab_port" -sTCP:LISTEN >/dev/null 2>&1; then occupied=true; fi
  fi
  [ -n "$conflicts" ] || [ "$occupied" = true ] || break
  if [ -n "$conflicts" ]; then
    echo "Port $lab_port is used by these Docker containers:"
    printf '  %s\n' "$conflicts"
    echo '  1) Stop the listed containers (interrupts their services) and use this port'
  else
    echo "Port $lab_port is used by a local process. This launcher will not terminate it."
  fi
  echo '  2) Use another port'
  echo '  3) Cancel'
  printf 'Choose [3]: '; read -r choice || exit 1
  case "$choice" in
    1)
      [ -n "$conflicts" ] || { echo 'Choose another port or stop the local process yourself.'; continue; }
      for container in $conflicts; do docker stop "$container" || exit 1; done
      ;;
    2) printf 'New port [9089]: '; read -r lab_port || exit 1; lab_port=${lab_port:-9089};;
    ''|3) echo 'Cancelled. No additional changes made.'; exit 1;;
    *) echo 'Choose 1, 2 or 3.';;
  esac
done
export LAB_PORT="$lab_port"
mkdir -p runtime
printf '%s\n' "$LAB_PORT" > runtime/port
lab_url="http://localhost:$LAB_PORT/data/perspective/client/performance-lab"
