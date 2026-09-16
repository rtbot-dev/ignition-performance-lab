#!/bin/sh
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec ./lab.sh
