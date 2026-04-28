# Grounding Contract

## 输入文件
- 默认输入文件建议：`paper/grounding/grounding_requests.json`
- 顶层可以是数组，或对象 `{ "families": [...] }`

## 每条请求的建议字段
- `grounding_id`: 稳定唯一 ID，输出文件名会基于它生成
- `stimulus_family`: 家族名
- `source_path`: 参考图路径；可相对 `grounding_requests.json` 所在目录，也可绝对路径；没有参考图时可为 `null`
- `figure_locator`: 例如 `Figure 2A left panel`
- `experiment_ids`: 字符串数组
- `phase_ids`: 字符串数组
- `condition_scope`: 数组或对象，记录该家族覆盖的条件范围
- `description`: 家族描述。segmentation prompt 会从这里派生；必须只描述当前这条记录要对齐的那一种参考粒度
- `must_preserve`: 字符串数组。会并入 prompt 派生逻辑；必须只约束当前粒度，不能把单 item 几何与整组 layout 约束混在同一条记录里
- `allowed_variation`: 字符串数组
- `reference_role`: 例如 `primary_example` / `layout_reference` / `fallback_anchor`
- `non_exhaustive`: 布尔值
- `fallback_prompts`: 字符串数组，备用 prompt 变体。当原始 `description+must_preserve` 派生的 prompt 分割失败时，`--retry-sweep` 会逐条尝试。至少应包含 1 条 外观/几何变体 + 1 条 scene/panel 粒度 prompt。

## 最小有效请求
```json
{
  "families": [
    {
      "grounding_id": "exp1_memory_items",
      "stimulus_family": "memory items",
      "source_path": "figures/figure2a.png",
      "figure_locator": "Figure 2A left panel",
      "experiment_ids": ["exp1"],
      "phase_ids": ["study"],
      "condition_scope": ["set_size=4", "set_size=8"],
      "description": "Single colored memory item exemplar: one filled circular disk with a wedge cutout.",
      "must_preserve": [
        "segment exactly one isolated item",
        "filled disk geometry with a single wedge cutout",
        "do not include the surrounding array layout"
      ],
      "allowed_variation": [
        "exact color values may vary by condition",
        "absolute pixel size may be rescaled"
      ],
      "reference_role": "primary_example",
      "non_exhaustive": true,
      "fallback_prompts": [
        "filled circular disk with colored stripe pattern",
        "experiment panel showing memory sample stimulus"
      ]
    }
  ]
}
```

## 输出文件
- `paper/grounding/grounding_index.json`
- `paper/grounding/masks/*.png`
- `paper/grounding/overlays/*.png`
- `paper/grounding/examples/*.png`

## grounding_index.json 字段
- `grounding_id`
- `stimulus_family`
- `source_path`
- `figure_locator`
- `experiment_ids`
- `phase_ids`
- `condition_scope`
- `prompt_text`
- `description`
- `must_preserve`
- `allowed_variation`
- `reference_priority`
- `effective_reference_basis`
- `reference_role`
- `non_exhaustive`
- `match_status`
- `mask_paths`
- `example_paths`
- `overlay_paths`
- `searched_regions`
- `no_match_reason`
- `retry_attempts`: 数组，记录 `--retry-sweep` 模式下的所有重试尝试。每项包含 `phase`（`threshold_sweep` 或 `fallback_prompt`）、`prompt`、`score_threshold`、`candidates_found`、`searched_count`。未使用 `--retry-sweep` 时为空数组。

## 固定枚举
- `reference_priority`: `figure_then_text` | `text_only`
- `effective_reference_basis`: `crop_and_text` | `figure_and_text` | `text_only`
- `match_status`: `matched` | `no_match` | `ambiguous`

## 回退规则
- 有参考图且至少有 1 个保存下来的 mask：`effective_reference_basis = crop_and_text`
- 有参考图但没有可靠 mask（且已经 `--retry-sweep` 穷尽）：`effective_reference_basis = figure_and_text`
- 没有参考图：`effective_reference_basis = text_only`
- **禁止未经 `--retry-sweep` 就回退到 `figure_and_text`**；`retry_attempts` 为空的 `figure_and_text` 记录将被 review gate 判为 issue。

## 无参考图时的 grounding_index.json
即使论文中不存在任何可用参考图，`paper/grounding/grounding_index.json` 仍然**必须产出**，内容为：
```json
{
  "status": "no_reference_figures",
  "families": [],
  "scan_summary": "scanned N files in paper/, found 0 usable reference figures"
}
```
此文件的存在性是下游 review gate 的硬门禁。

## 有参考图但全部分割失败时的 grounding_index.json
若参考图存在但所有 family 均 `no_match`，文件顶层必须为数组（保留所有 family 记录与 `no_match_reason`），且**不得**写 `"status": "no_reference_figures"`。调用方应在顶层或外部 wrapper 中标记 `"status": "all_no_match"`。

## Index 合并与磁盘产物对账
- `segment_with_sam31.py` 在写入 `grounding_index.json` 前自动执行：
  1. **Merge**：读取已有 `grounding_index.json`，保留不在本次 requests 中的旧 family 记录。多次运行不会互相覆盖。
  2. **Disk reconciliation**：对 `no_match` family，扫描 `masks/`、`overlays/`、`examples/` 中以 `grounding_id` 为前缀的文件。若磁盘上有历史产物，自动升级为 `matched` / `crop_and_text`，并标记 `_disk_reconciled: true`。
- 这意味着：即使新一轮 prompt 失败，只要旧轮次的产物文件还在目录中，index 会自动引用它们，不会出现"磁盘有文件但 index 标记为 no_match"的不一致。
- `_disk_reconciled: true` 表示该 family 的 `matched` 状态来自磁盘扫描而非当前运行的模型输出。

## 粒度与阶段规则
- `prompt_text` 必须始终由 `description + must_preserve` 派生。
- 一条记录只能对应一种参考粒度：要么是 `single stimulus exemplar`，要么是 `layout exemplar`；不能在同一条记录里同时描述单一刺激物和多刺激布局。
- 若论文里同时出现单一刺激示意图与刺激布局图，必须拆成多条 `stimulus_family` 记录。
- `reference_role=primary_example` 默认用于单一刺激示意图，供刺激检查/primitive fidelity 对照。
- `reference_role=layout_reference` 用于论文中出现过的布局图，供后续组合检查与 code generation 阶段参考。
- 单一刺激检查阶段不得直接消费 `layout_reference` 去反推单个刺激物几何。

## searched_regions 约定
- 推荐记录脚本真正搜索或保留下来的区域摘要，而不是空数组。
- 每项至少包含：
  - `kind`
  - `box_xyxy`
  - `score`
  - `mask_area`

## no_match_reason 约定
- 建议使用短、稳定、机器可判读的原因：
  - `missing_source_image`
  - `missing_required_fields:description,must_preserve`
  - `model_runtime_error:<message>`
  - `no_mask_above_threshold`
  - `all_masks_filtered_by_area`
