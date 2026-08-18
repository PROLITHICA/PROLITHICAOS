#!/usr/bin/env bash
# Run the Prolithica OS API and app together.
set -euo pipefail
cd "$(dirname "$0")"
export PATH=/opt/homebrew/bin:$PATH

PY=backend_venv/bin/python

"$PY" backend/manage.py migrate --noinput
"$PY" backend/manage.py seed

"$PY" backend/manage.py runserver 8000 &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

cd frontend
[ -d node_modules ] || npm install
npm start
