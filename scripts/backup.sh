#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${1:-backups}"
ARCHIVE_NAME="suibi_backup_${TS}.tar.gz"

mkdir -p "${OUT_DIR}"

tar -czf "${OUT_DIR}/${ARCHIVE_NAME}" \
  app/ \
  scripts/ \
  requirements.txt \
  .env \
  data/

echo "Backup created: ${OUT_DIR}/${ARCHIVE_NAME}"
