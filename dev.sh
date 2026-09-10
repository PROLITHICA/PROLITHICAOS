#!/usr/bin/env bash
# Run Prolithica OS and expose it on the local network.
#
#   ./dev.sh          API on :8000, app on :4200, reachable from any device on this network
#
# Other devices only need port 4200 — the app proxies /api to the API itself,
# so phones and tablets never talk to :8000 directly.
set -euo pipefail
cd "$(dirname "$0")"
export PATH=/opt/homebrew/bin:$PATH

PY=backend_venv/bin/python
PORT_API=${PORT_API:-8000}
PORT_APP=${PORT_APP:-4200}

LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
[ -z "$LAN_IP" ] && LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LAN_IP" ] && LAN_IP="127.0.0.1"

export PROLITHICA_TRUSTED_ORIGINS="http://${LAN_IP}:${PORT_APP},http://localhost:${PORT_APP}"

"$PY" backend/manage.py migrate --noinput
"$PY" backend/manage.py seed

"$PY" backend/manage.py runserver "0.0.0.0:${PORT_API}" &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT

cd frontend
[ -d node_modules ] || npm install

cat <<BANNER

  Prolithica OS is starting.

    On this machine   http://localhost:${PORT_APP}
    On this network   http://${LAN_IP}:${PORT_APP}

  Sign in as the director: newtvnbrian@gmail.com / 12428newton
  Anyone on the same Wi-Fi can reach the second address.

BANNER

npx ng serve --host 0.0.0.0 --port "${PORT_APP}"
