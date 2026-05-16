#!/usr/bin/env bash
# Run the FastAPI app from any cwd. Uvicorn needs the backend folder on PYTHONPATH
# (equivalent to: cd backend && uvicorn app.main:app …).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="${ROOT}/backend"
if [[ -x "${BACKEND}/.venv/bin/uvicorn" ]]; then
  UV="${BACKEND}/.venv/bin/uvicorn"
else
  UV="uvicorn"
fi
exec "${UV}" app.main:app \
  --app-dir "${BACKEND}" \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --reload \
  "$@"
