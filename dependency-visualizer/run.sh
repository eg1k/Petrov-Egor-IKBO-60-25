#!/bin/sh
# Запуск визуализатора. Аргументы передаются программе, например: ./run.sh -c config.yaml
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$ROOT/.venv/bin/python" ]; then
    PY="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
    PY="$ROOT/.venv/Scripts/python.exe"
else
    echo "Создание виртуального окружения .venv..."
    python3 -m venv "$ROOT/.venv" || exit 1
    PY="$ROOT/.venv/bin/python"
    "$PY" -m pip install -q -r "$ROOT/requirements.txt" || exit 1
fi
export PYTHONIOENCODING=utf-8
exec "$PY" "$ROOT/src/visualizer.py" "$@"
