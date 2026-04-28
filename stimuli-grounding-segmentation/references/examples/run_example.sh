#!/usr/bin/env bash
# 一键执行 grounding segmentation 示例
# 用法: bash run_example.sh [WORKSPACE]
#   例:  cd examples && bash run_example.sh demo_workspace
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SAM3_REPO="${SAM3_REPO:-/path/to/sam3}"
SAM3_CKPT="${SAM3_CKPT:-/path/to/sam3/ckpt/sam3.1_multiplex.pt}"

# 支持相对路径；默认用脚本同目录下的 demo_workspace
if [[ -n "${1:-}" ]]; then
  WORKSPACE="$(cd "${1}" && pwd)"
else
  WORKSPACE="${SCRIPT_DIR}/demo_workspace"
fi

REQUESTS="${WORKSPACE}/paper/grounding/grounding_requests.json"
OUTPUT="${WORKSPACE}/paper/grounding"

if [[ ! -f "${REQUESTS}" ]]; then
  echo "ERROR: requests file not found: ${REQUESTS}"
  echo "Usage: bash run_example.sh /path/to/workspace"
  exit 1
fi

echo "=========================================="
echo " Grounding Segmentation Example"
echo "=========================================="
echo " WORKSPACE : ${WORKSPACE}"
echo " REQUESTS  : ${REQUESTS}"
echo " OUTPUT    : ${OUTPUT}"
echo "=========================================="

echo ""
echo ">>> Step 1/3: Check SAM3.1 environment"
sam3-python "${SKILL_ROOT}/scripts/check_sam31_env.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda

echo ""
echo ">>> Step 2/3: Verify model loading (smoke test)"
# 用合成图 (红色矩形 + 蓝色椭圆) 做 smoke test，prompt 已知可检测
sam3-python "${SKILL_ROOT}/scripts/verify_sam31_setup.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --output-dir "${WORKSPACE}/tmp/sam31_verify" \
  --prompt "red rectangle" \
  --confidence-threshold 0.05 \
  --require-mask
echo "Verify artifacts:"
echo "  ${WORKSPACE}/tmp/sam31_verify/verify_overlay.png"
echo "  ${WORKSPACE}/tmp/sam31_verify/verify_top1_crop.png"
echo "  ${WORKSPACE}/tmp/sam31_verify/verify_summary.json"

echo ""
echo ">>> Step 3/3: Run grounding segmentation"
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${REQUESTS}" \
  --output-root "${OUTPUT}" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --max-masks-per-family 3 \
  --retry-sweep

echo ""
echo "=========================================="
echo " Results"
echo "=========================================="
echo "Index: ${OUTPUT}/grounding_index.json"
echo ""
echo "Generated files:"
find "${OUTPUT}" -name '*.png' 2>/dev/null | sort | head -20
echo ""
echo "Index content:"
python3 -m json.tool "${OUTPUT}/grounding_index.json"
