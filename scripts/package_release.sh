#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${1:-releases}"
INCLUDE_ENV="${2:-false}"
ARCHIVE_NAME="suibi_release_${TS}.tar.gz"

mkdir -p "${OUT_DIR}"

INCLUDES=(
  "app"
  "scripts"
  "requirements.txt"
  ".env.example"
  "README.md"
)

if [[ -d "data" ]]; then
  INCLUDES+=("data")
fi

if [[ "${INCLUDE_ENV}" == "true" ]]; then
  if [[ -f ".env" ]]; then
    INCLUDES+=(".env")
  else
    echo "Warning: INCLUDE_ENV=true but .env does not exist, skipping .env"
  fi
fi

for path in "${INCLUDES[@]}"; do
  if [[ ! -e "${path}" ]]; then
    echo "Error: required path '${path}' does not exist"
    exit 1
  fi
done

tar -czf "${OUT_DIR}/${ARCHIVE_NAME}" "${INCLUDES[@]}"

echo "Release package created: ${OUT_DIR}/${ARCHIVE_NAME}"
echo "Included: ${INCLUDES[*]}"
