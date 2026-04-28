#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=""
VENV_DIR="${PWD}/.venv-sam3"
TORCH_VERSION="2.10.0"
TORCH_INDEX_URL="https://download.pytorch.org/whl/cu128"
PYTHON_BIN=""

usage() {
  cat <<'EOF'
Usage:
  install_sam31_runtime.sh --repo-dir DIR [--venv-dir DIR] [--python-bin PYTHON]

Example:
  bash install_sam31_runtime.sh \
    --repo-dir /workspace/external/sam3 \
    --venv-dir /workspace/.venv-sam3
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir)
      REPO_DIR="$2"
      shift 2
      ;;
    --venv-dir)
      VENV_DIR="$2"
      shift 2
      ;;
    --python-bin)
      PYTHON_BIN="$2"
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

if [[ -z "${REPO_DIR}" ]]; then
  echo "--repo-dir is required" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Repo directory does not exist: ${REPO_DIR}" >&2
  exit 2
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.12)"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python3.12 or python3 is required" >&2
    exit 3
  fi
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install "torch==${TORCH_VERSION}" torchvision --index-url "${TORCH_INDEX_URL}"
python -m pip install -e "${REPO_DIR}"
python -m pip install modelscope pillow numpy

python - <<'PY'
import sys
print("python", sys.version)
try:
    import torch
    print("torch", torch.__version__)
except Exception as exc:
    print("torch_import_error", repr(exc))
    raise
try:
    import sam3
    print("sam3", getattr(sam3, "__version__", "unknown"))
except Exception as exc:
    print("sam3_import_error", repr(exc))
    raise
PY

printf 'sam3 runtime ready: %s\n' "${VENV_DIR}"
