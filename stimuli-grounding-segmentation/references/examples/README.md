# Grounding Segmentation 示例

本示例展示如何对论文参考图的刺激物执行 grounding & segmentation。

## 目录结构

```
demo_workspace/
└── paper/
    ├── _page_1_Figure_2.jpeg          ← 论文参考图（含刺激物）
    └── grounding/
        ├── grounding_requests.json    ← 输入：每个 stimulus_family 的分割请求
        └── (产出)
            ├── grounding_index.json   ← 结果索引
            ├── masks/*.png            ← 二值 mask
            ├── overlays/*.png         ← 原图 + mask 叠加 + bbox
            └── examples/*.png         ← 裁剪后的透明背景刺激物
```

## 图示

以下面这张论文图为例（`_page_1_Figure_2.jpeg`）：

```
┌──────────────────────────────────────────────────────────────┐
│  Experiment 1                                                │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐                │
│  │  ·   │  │  ╲   │  │  ·   │  │  ⟳  dial │                │
│  │      │  │   ╲  │  │      │  │          │                 │
│  └──────┘  └──────┘  └──────┘  └──────────┘                │
│  Fixation   Sample    Delay     Report                      │
│  500ms      200ms     1300ms    until resp.                 │
│                                                              │
│  Experiment 2                                                │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐                │
│  │  ·   │  │╲  · ╱│  │  ·   │  │  ⟳ · dial│                │
│  └──────┘  └──────┘  └──────┘  └──────────┘                │
└──────────────────────────────────────────────────────────────┘
```

grounding 要做的是：从这张图中自动分割（segment）出单个刺激物的 mask、overlay 和 crop。

## grounding_requests.json 说明

每条请求对应一个 `stimulus_family`，必须包含以下关键字段：

| 字段 | 用途 | 示例 |
|------|------|------|
| `grounding_id` | 唯一标识，文件名基于它生成 | `gabor_patch_primary` |
| `stimulus_family` | 刺激家族名 | `gabor_patch` |
| `source_path` | 参考图路径 (相对或绝对)；无图时为 `null` | `../_page_1_Figure_2.jpeg` |
| `figure_locator` | 图/面板定位描述 | `Figure 1a, page 1` |
| `description` | 刺激物描述 → 用于构造 segmentation prompt | 见下 |
| `must_preserve` | 分割时必须保持的约束 | `["segment exactly one isolated item"]` |
| `reference_role` | `primary_example` (单刺激) 或 `layout_reference` (布局) | `primary_example` |

### 三种典型场景

**场景1：有参考图 + 单刺激（primary_example）**
```json
{
  "grounding_id": "gabor_patch_primary",
  "stimulus_family": "gabor_patch",
  "source_path": "../_page_1_Figure_2.jpeg",
  "description": "Single Gabor patch stimulus exemplar: a circular patch with sinusoidal luminance grating...",
  "must_preserve": [
    "segment exactly one isolated Gabor patch",
    "circular shape with soft Gaussian-blurred edge"
  ],
  "reference_role": "primary_example"
}
```

**场景2：有参考图 + 布局（layout_reference）**
```json
{
  "grounding_id": "gabor_array_layout",
  "stimulus_family": "gabor_patch",
  "source_path": "../_page_1_Figure_2.jpeg",
  "description": "Spatial layout of multiple Gabor patches arranged around a central fixation point...",
  "must_preserve": [
    "segment the group of Gabor patches as a whole layout",
    "preserve relative spatial positions"
  ],
  "reference_role": "layout_reference"
}
```

**场景3：无参考图（text_only 回退）**
```json
{
  "grounding_id": "teardrop_stimulus",
  "stimulus_family": "teardrop_bar",
  "source_path": null,
  "description": "Black teardrop-shaped stimulus with a rounded bulbous end...",
  "must_preserve": ["teardrop silhouette geometry", "solid black fill"],
  "reference_role": "primary_example"
}
```

## Bash 命令

### 0. 环境变量设置

```bash
# Skill 脚本根目录
SKILL_ROOT="./stimuli-grounding-segmentation"

# SAM3.1 仓库与 checkpoint
SAM3_REPO="/path/to/sam3"
SAM3_CKPT="/path/to/sam3/ckpt/sam3.1_multiplex.pt"

# 当前 workspace（示例）
WORKSPACE="/workspace"
```

### 1. 检查环境（Python / torch / CUDA / repo / checkpoint）

```bash
sam3-python "${SKILL_ROOT}/scripts/check_sam31_env.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda
```

### 2. 端到端 smoke test（加载模型 + 单图前向推理）

```bash
sam3-python "${SKILL_ROOT}/scripts/verify_sam31_setup.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --output-dir "${WORKSPACE}/tmp/sam31_verify"
```

### 3. 运行 grounding segmentation

```bash
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${WORKSPACE}/paper/grounding/grounding_requests.json" \
  --output-root "${WORKSPACE}/paper/grounding" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --retry-sweep
```

预期输出：
```json
{"grounding_index": "/workspace/paper/grounding/grounding_index.json", "families": 3}
```

### 4. 查看产出

```bash
# 查看索引
cat "${WORKSPACE}/paper/grounding/grounding_index.json" | python3 -m json.tool

# 查看生成的文件
find "${WORKSPACE}/paper/grounding" -name '*.png' | sort
```

预期文件树：
```
paper/grounding/
├── grounding_index.json
├── grounding_requests.json
├── masks/
│   ├── gabor_patch_primary__01.png
│   └── gabor_patch_primary__02.png
├── overlays/
│   ├── gabor_patch_primary__01.png    ← 原图 + 红色半透明 mask + 黄色 bbox
│   └── gabor_patch_primary__02.png
└── examples/
    ├── gabor_patch_primary__01.png    ← 裁剪后透明背景刺激物
    └── gabor_patch_primary__02.png
```

### 5. 可选参数调优

```bash
# 降低置信度阈值（获取更多候选区域，但可能引入噪声）
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${WORKSPACE}/paper/grounding/grounding_requests.json" \
  --output-root "${WORKSPACE}/paper/grounding" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --confidence-threshold 0.1 \
  --score-threshold 0.1

# 增大最小 mask 面积（过滤掉碎片 mask）
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${WORKSPACE}/paper/grounding/grounding_requests.json" \
  --output-root "${WORKSPACE}/paper/grounding" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --min-mask-area 1024

# 限制每个 family 最多保留的 mask 数
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${WORKSPACE}/paper/grounding/grounding_requests.json" \
  --output-root "${WORKSPACE}/paper/grounding" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --max-masks-per-family 3
```

## grounding_index.json 输出说明

每条记录的关键输出字段：

| 字段 | 说明 |
|------|------|
| `match_status` | `matched` / `no_match` / `ambiguous` |
| `effective_reference_basis` | `crop_and_text` (有 mask) / `figure_and_text` (有图无 mask) / `text_only` (无图) |
| `mask_paths` | 保存的 mask 文件路径列表 |
| `overlay_paths` | overlay 可视化路径列表 |
| `example_paths` | 裁剪示例路径列表 |
| `prompt_text` | 由 description + must_preserve 自动拼接的 prompt |
| `no_match_reason` | 失败原因（仅当 `no_match` 时） |
| `searched_regions` | 模型搜索到的所有候选区域，含 score/bbox/area |

### 三种结果的 effective_reference_basis 回退规则

```
有参考图 + 至少 1 个 mask  →  crop_and_text   (最优)
有参考图 + 0 个 mask       →  figure_and_text  (回退)
无参考图                    →  text_only         (回退)
```

## 完整一键执行脚本

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="./stimuli-grounding-segmentation"
SAM3_REPO="/path/to/sam3"
SAM3_CKPT="/path/to/sam3/ckpt/sam3.1_multiplex.pt"
WORKSPACE="/workspace"

echo "=== Step 1: Check environment ==="
sam3-python "${SKILL_ROOT}/scripts/check_sam31_env.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda

echo "=== Step 2: Verify model loading ==="
sam3-python "${SKILL_ROOT}/scripts/verify_sam31_setup.py" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --output-dir "${WORKSPACE}/tmp/sam31_verify"

echo "=== Step 3: Run grounding segmentation ==="
sam3-python "${SKILL_ROOT}/scripts/segment_with_sam31.py" \
  --requests-file "${WORKSPACE}/paper/grounding/grounding_requests.json" \
  --output-root "${WORKSPACE}/paper/grounding" \
  --repo-dir "${SAM3_REPO}" \
  --checkpoint "${SAM3_CKPT}" \
  --device cuda \
  --retry-sweep

echo "=== Step 4: Summary ==="
cat "${WORKSPACE}/paper/grounding/grounding_index.json" | python3 -m json.tool
echo "Done. Check paper/grounding/ for masks, overlays, and examples."
```
