#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"

check_file() {
  local path="$1"
  if [[ ! -e "${path}" ]]; then
    echo "[FAIL] Missing: ${path}"
    exit 1
  fi
  echo "[OK] Found: ${path}"
}

echo "== Static checks =="
check_file "app/main.py"
check_file "requirements.txt"
check_file ".env.example"
check_file "scripts/init_db.py"

if [[ -f ".env" ]]; then
  echo "[OK] Found optional .env"
else
  echo "[WARN] .env not found (optional for smoke check)"
fi

if [[ -d "data" ]]; then
  echo "[OK] Found data/"
else
  echo "[WARN] data/ not found yet"
fi

echo "== HTTP health checks =="
HEALTH_URL="${BASE_URL}/health"
OUT_FILE="$(mktemp)"
STATUS="$(curl -sS -o "${OUT_FILE}" -w '%{http_code}' "${HEALTH_URL}" || true)"
if [[ "${STATUS}" == "200" ]]; then
  echo "[OK] ${HEALTH_URL} -> 200"
else
  echo "[FAIL] ${HEALTH_URL} -> ${STATUS}"
  echo "Response:"
  cat "${OUT_FILE}" || true
  exit 1
fi

echo "Smoke check passed."
