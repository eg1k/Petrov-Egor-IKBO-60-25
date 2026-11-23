#!/bin/sh
exec python3 -X utf8 "$(dirname "$0")/src/main.py" "$@"
