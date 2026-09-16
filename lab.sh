#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$root/scripts/start.sh" "${1:-jython-vibration}"
