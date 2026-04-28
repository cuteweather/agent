#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="facebook/sam3.1"
CHECKPOINT_NAME="sam3.1_multiplex.pt"
OUTPUT_DIR="${PWD}/external/checkpoints/sam3.1"

usage() {
  cat <<'EOF'
Usage:
  download_sam31_checkpoint.sh [--output-dir DIR] [--checkpoint-name FILE]

Requirements:
  - modelscope CLI or Python package must be installed first

Example:
  bash download_sam31_checkpoint.sh --output-dir /workspace/external/checkpoints/sam3.1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --checkpoint-name)
      CHECKPOINT_NAME="$2"
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

mkdir -p "${OUTPUT_DIR}"

if command -v modelscope >/dev/null 2>&1; then
  modelscope download \
    --model "${MODEL_ID}" \
    --local_dir "${OUTPUT_DIR}" \
    --include "${CHECKPOINT_NAME}"
else
  python - <<'PY'
import importlib.util
import sys
if importlib.util.find_spec("modelscope") is None:
    print("Neither `modelscope` CLI nor Python package is installed.", file=sys.stderr)
    print("Install it first with: python -m pip install modelscope", file=sys.stderr)
    raise SystemExit(3)
PY
  MODEL_ID="${MODEL_ID}" OUTPUT_DIR="${OUTPUT_DIR}" CHECKPOINT_NAME="${CHECKPOINT_NAME}" python - <<'PY'
import os
from modelscope.hub.snapshot_download import snapshot_download

snapshot_download(
    model_id=os.environ["MODEL_ID"],
    local_dir=os.environ["OUTPUT_DIR"],
    allow_patterns=[os.environ["CHECKPOINT_NAME"]],
)
PY
fi

if [[ ! -f "${OUTPUT_DIR}/${CHECKPOINT_NAME}" ]]; then
  echo "Checkpoint download did not produce ${OUTPUT_DIR}/${CHECKPOINT_NAME}" >&2
  exit 4
fi

printf 'checkpoint ready: %s\n' "${OUTPUT_DIR}/${CHECKPOINT_NAME}"
