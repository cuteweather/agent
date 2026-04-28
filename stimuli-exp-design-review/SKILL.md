---
name: stimuli-exp-design-review
description: 在 run_exp_design 与 run_codegen 之间执行阻断式 exp_design 审核，输出机器可读 gate 与人类可读报告，确保设计规格可执行、可追溯、可审计。
---

# Stimuli Exp Design Review

## Purpose
你只做一件事：审核 `<workspace>/exp_design.md` 是否达到可进入 code generation 的标准。

## Inputs (Priority)
1) `<workspace>/exp_design.md`
2) `<workspace>/paper/`
3) `<workspace>/data/`
4) `<workspace>/repro_check.md`（若存在）

## Required Outputs
- `<workspace>/exp_design_review.md`
- `<workspace>/script/exp_design_review_gate.json`

## Review Method (Blocking)
必须沿用既有 exp_design 审核思路，至少覆盖以下检查项：
1. Evidence Index 完整性：关键事实都能追溯到明确证据定位。
2. Parameter Registry 完整性：关键实现参数可落地、无明显缺项、无自相矛盾。
3. Fact Ledger 一致性：事实陈述与 paper/data/code 证据一致。
4. Phase/condition 语义一致性：phase 职责、条件分支、trial 流程可执行且无错位。
5. Data mapping 完整性：数据字段到实现参数的映射可闭环。
6. Conflict/Missing 处置：冲突有裁决，缺失有明确阻断说明。
7. 外部素材策略一致性：若实验依赖外部视觉素材，策略、追溯要求与 trial 映射完整。
8. **Grounding 产物一致性**：`<workspace>/paper/grounding/grounding_index.json` 必须存在于磁盘上（无论有无参考图）。
  - 若 paper 中存在可用于 grounding 的参考图，则 exp_design 阶段应已调用精确技能名 `stimuli-grounding-segmentation`；若产物缺失或全部回退成 text_only，应优先怀疑 `stimuli-grounding-segmentation` 没被正确调用或没有被继续重试。
   - 若文件中 `status = "no_reference_figures"` 且 `families` 为空数组：确认 paper/ 中确实无图片文件，exp_design.md 中所有 family 的 `effective_reference_basis` 均为 `text_only`。
  - 若 paper/ 中存在图片文件，且 `grounding_index.json` 中所有 family 的 `effective_reference_basis` 都是 `text_only`：必须进一步检查这些图片是否真的全是结果图/统计图。**只要任一图片中可见 stimulus exemplar、procedure panel、layout scene、response dial、search display 或 memory sample，就必须判为 issue**，因为这说明 exp_design 错误跳过了 figure grounding。
  - **“刺激可由数学参数生成”不能作为通过理由**。若 paper 中仍有可见刺激图或流程面板，review 必须要求至少保留 1 条 `figure_then_text` 的 grounding family；并且尽可能产出`crop_and_text` 的 grounding 产物，而不是直接回退到 `text_only`。
  - **有参考图就必须产图**：若任何 family 的 `reference_priority=figure_then_text`，则最终产物中必须至少存在 1 张图片产物（mask / overlay / example）。若全部为空，判定为 **critical issue**，不得以任何理由通过（包括“刺激可由文本参数指定”“无需外部资产”等）。
  - **空产物判定流程**（当所有有参考图 family 的产物均为空时）：
    1. 检查 `retry_attempts` 是否非空 → 若空，**critical issue**（未使用 `--retry-sweep`）
    2. 检查 `retry_attempts` 中是否包含 `phase=fallback_prompt` → 若无，**issue**（未写入 `fallback_prompts`）
    3. 检查是否存在 `reference_role=layout_reference` 且 `match_status=matched` 的兜底记录 → 若无，**issue**（未做 scene-level 兜底）
    4. 只有当 1-3 全部通过（即已充分重试、已写 fallback prompts、已尝试 scene-level）且仍然无产物时，才可记为 non-critical issue 并允许 codegen 基于文本参数继续
   - **严禁将"有参考图但全部分割失败"标记为 `no_reference_figures`**。若 `grounding_index.json` 中存在 family 条目（`families` 非空），则 `grounding_status` 必须为 `has_families`，不可为 `no_reference_figures`。
   - 若文件中包含 family 条目且全部 `match_status = "no_match"`（即有参考图但全部分割失败）：判定为 **issue**（非自动 pass），要求在 issues 中记录失败原因，并验证 exp_design 阶段已尝试至少一次重试或 prompt 调整。
   - **必须检查 `retry_attempts` 字段**：若 family 为 `no_match` 且 `retry_attempts` 为空数组或不存在，说明未使用 `--retry-sweep`，判定为 **critical issue**，要求重新运行 `stimuli-grounding-segmentation` 并带上 `--retry-sweep`。
   - **必须检查 `fallback_prompts` 覆盖**：若 `retry_attempts` 中没有任何 `phase=fallback_prompt` 的条目，说明未在 `grounding_requests.json` 中写入 `fallback_prompts`，判定为 **issue**，要求补充 `fallback_prompts`（至少包含 1 条 scene-level prompt）并重跑。
   - **必须检查 scene-level 兜底**：若所有 object-level family 均 `no_match`，但没有任何 `reference_role=layout_reference` 且 `match_status=matched` 的 family 记录，判定为 **issue**，要求增加 scene-level grounding 并重跑。
  - 若文件中包含 family 条目但全部 `effective_reference_basis = text_only`，同时 paper 图中又存在 stimulus/procedure/layout 画面：判定为 **issue**，要求重新运行 exp_design / grounding，并补出grounding图。
   - 若文件中包含实际 families 条目且任何 `effective_reference_basis` 为 `crop_and_text`：验证 `paper/grounding/examples/`、`paper/grounding/overlays/`、`paper/grounding/masks/` 中有实际图片文件。若声称 `crop_and_text` 但无对应图片，判定为 **critical issue**。
   - 若 `grounding_index.json` 不存在，判定为 **critical issue**（说明 exp_design 阶段未执行 grounding 扫描）。

## Gate Contract (Mandatory)
`script/exp_design_review_gate.json` 必须包含以下最小结构：

```json
{
  "passed": true,
  "summary": "string",
  "checks": {
    "executed": true,
    "evidence_index": {"passed": true, "issues": []},
    "parameter_registry": {"passed": true, "issues": []},
    "fact_ledger": {"passed": true, "issues": []},
    "phase_condition_semantics": {"passed": true, "issues": []},
    "data_mapping": {"passed": true, "issues": []},
    "conflict_missing": {"passed": true, "issues": []},
    "asset_strategy": {"required": false, "passed": true, "issues": []},
    "grounding_artifacts": {"required": true, "passed": true, "issues": [], "grounding_status": "has_families | no_reference_figures", "retry_sweep_verified": true}
  },
  "critical_issues": [],
  "next_actions": []
}
```

## Hard Rules
- `critical_issues` 只要非空，`passed` 必须为 `false`。
- 若任一关键检查未执行，`passed` 必须为 `false`。
- `exp_design_review.md` 与 gate 结论必须一致，不得一个通过一个不通过。
- 不得用“看起来差不多”替代可核验证据。

## Return Contract
按调用方要求返回结构化 JSON。
- 若 `exp_design_review_gate.json.passed = true`，可返回 `succeeded`。
- 若 `passed = false`（发现阻断问题），返回 `failed_retryable`，并在 `error`/`summary` 明确 blocker。
