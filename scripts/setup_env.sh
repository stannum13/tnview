#!/usr/bin/env sh
set -eu

ACTIVE_PREFIX="${VIRTUAL_ENV:-${CONDA_PREFIX:-}}"
PY_PREFIX="$(python -c 'import sys; print(sys.prefix)')"

if [ -n "$ACTIVE_PREFIX" ] && [ "$PY_PREFIX" = "$ACTIVE_PREFIX" ]; then
  python -m pip install -r requirements.txt
  echo "Installed TNView into the active Python environment."
  exit 0
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "Created/updated .venv."
echo "Run: source .venv/bin/activate"
echo "Then: tnview replay examples/tebd_run.jsonl --interactive"
