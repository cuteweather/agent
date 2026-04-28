#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/facebookresearch/sam3.git"
TARGET_DIR="${PWD}/external/sam3"
REF="main"

usage() {
  cat <<'EOF'
Usage:
  clone_sam3_repo.sh [--target-dir DIR] [--ref REF]

Examples:
  bash clone_sam3_repo.sh --target-dir /workspace/external/sam3
  bash clone_sam3_repo.sh --target-dir /workspace/external/sam3 --ref main
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -e "${TARGET_DIR}" ]] && [[ -n "$(find "${TARGET_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Target directory is not empty: ${TARGET_DIR}" >&2
  exit 2
fi

mkdir -p "$(dirname "${TARGET_DIR}")"
git clone "${REPO_URL}" "${TARGET_DIR}"
git -C "${TARGET_DIR}" checkout "${REF}"
git -C "${TARGET_DIR}" submodule update --init --recursive

printf 'sam3 repo ready: %s\n' "${TARGET_DIR}"
