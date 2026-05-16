#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <archive_path> <target_dir>"
  echo "Example: $0 /tmp/suibi_release_20260516_103000.tar.gz /opt/suibi"
  exit 1
fi

ARCHIVE_PATH="$1"
TARGET_DIR="$2"
VENV_DIR="${TARGET_DIR}/.venv"
DB_PATH="${TARGET_DIR}/data/suibi.db"

if [[ ! -f "${ARCHIVE_PATH}" ]]; then
  echo "Error: archive not found: ${ARCHIVE_PATH}"
  exit 1
fi

mkdir -p "${TARGET_DIR}"
tar -xzf "${ARCHIVE_PATH}" -C "${TARGET_DIR}"

python -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r "${TARGET_DIR}/requirements.txt"

mkdir -p "${TARGET_DIR}/data"
mkdir -p "${TARGET_DIR}/data/imports" "${TARGET_DIR}/data/exports" "${TARGET_DIR}/data/uploads"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "Database not found, initializing: ${DB_PATH}"
  (cd "${TARGET_DIR}" && python scripts/init_db.py)
else
  echo "Database already exists, skipping init_db.py"
fi

cat <<MSG

Restore completed.

Next step: configure systemd
1) Copy service file:
   sudo cp ${TARGET_DIR}/deploy/life-tracer.service /etc/systemd/system/life-tracer.service
2) Edit /etc/systemd/system/life-tracer.service to match User/Group/WorkingDirectory if needed.
3) Reload and start:
   sudo systemctl daemon-reload
   sudo systemctl enable --now life-tracer.service
   sudo systemctl status life-tracer.service
MSG
