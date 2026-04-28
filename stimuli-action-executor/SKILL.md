---
name: stimuli-action-executor
description: agent action 的统一执行包装器。负责执行单个 action、按需调用目标领域 skill，并强制返回结构化 JSON 结果。
---

# Stimuli Action Executor

## Purpose
你只执行一个显式 action。你不是调度器，不负责决定下一步。你的职责是：
1. 执行当前 action；
2. 若 action 指定了目标领域 skill，则必须调用它来完成核心业务；
3. 最后无论领域 skill 是否返回结构化结果，你都必须整理出统一 JSON 结果。

## Non-Negotiable Rules
- 一次只执行一个 action，不能擅自改 action。
- 对 `kind=skill` 的 action，必须调用任务中指定的 `target_skill`。
- 不能只给计划、建议或分析；必须真正执行并产出结果。
- 若目标 skill 已经完成了主要工作但没有机器可读返回，你必须根据实际执行痕迹、生成文件和调用结果自行整理 JSON。

## Required Output JSON
只返回一个 JSON 对象，不附加额外说明文字。字段至少包括：

```json
{
  "status": "succeeded | reviewing | skipped_irreproducible | failed_retryable | failed_terminal",
  "success": true,
  "summary": "short summary",
  "artifacts": {},
  "evidence": {
    "files_read": [],
    "files_written": [],
    "commands_run": [],
    "subagents": []
  },
  "decision": {},
  "error": null
}
```

当 `status=reviewing` 时，`decision` 必须包含：

```json
{
  "retryable": false,
  "next_step": null,
  "terminate_workflow": false,
  "pause_workflow": true,
  "resume_step": "当前 step",
  "pause_reason": "manual_review_pending"
}
```

## Action-Specific Notes
- `run_repro_check`
  必须调用 `stimuli-reproducibility-check`。若结论为不可复现，返回 `skipped_irreproducible`；若只是工具或执行异常，返回 `failed_retryable` 或 `failed_terminal`。
  若领域 skill 判断“论文引用公开数据集/外部图片库，但素材尚未在 workspace 中就绪”，必须保留其 `asset_requirements` / `blocking_issues` / `substitute_reproduction` 语义；禁止把它整理成“无 blocker 的 full success”。
  必须生成或刷新 `repro_check.md`（可复现性检查 markdown 报告）；若该文件缺失或为空，不得返回成功。
- `run_exp_design`
  必须调用 `stimuli-exp-design`，并基于 `exp_design.md` 是否生成/修复来汇总结果。
  若实验依赖外部视觉素材，但 `exp_design.md` 缺少对应素材策略、trial 映射、追溯要求或仍写成 `Not applicable`，不得返回成功。
- `run_exp_design_review`
  必须调用 `stimuli-exp-design-review`，并检查 `exp_design_review.md` 与 `script/exp_design_review_gate.json`。
  `script/exp_design_review_gate.json` 是 design review 对后续 codegen 的机器可读交接文件。
  若 gate 中 `passed != true`，不得整理成成功。
- `run_codegen`
  必须调用 `stimuli-code-generation`，并检查关键脚本文件是否已生成。
  codegen 前置门禁：
  - `exp_design_review.md` 与 `script/exp_design_review_gate.json` 必须存在，且 gate 中 `passed=true`。
  - `script/unit_function_review_gate.json` 必须存在，且 `passed=true`。
  - `script/stimuli_primitives.py` 必须存在。
  若任一前置门禁未满足，直接返回失败。
  `reproduce_stimuli.py` 必须 import `stimuli_primitives` 模块，禁止重复定义 primitive 函数。
  若 workspace 已存在 `script/review_gate.json`，必须把它视为 repair round 的机器可读主输入；`code_review.md` 仅作细节补充。
  若 `exp_design.md` 或上游结果声明存在未就绪的外部视觉素材，则除核心脚本外，还必须检查素材准备与追溯文件是否已生成；若只是生成 placeholder 版本代码，不得返回成功。
- `run_unit_codegen`
  必须调用 `stimuli-unit-code-generation`，只负责生成 primitive 绘制函数与渲染 unit catalog。
  必须产出并检查 `script/stimuli_primitives.py`、`script/render_unit_catalog.py`、`script/unit_manifest.json`、`script/unit_generation_gate.json`、`output_unit/primitive/`。
  `script/unit_generation_gate.json` 必须至少包含 `passed`、`primitive_units.ready`、`unit_manifest.ready`、`output_unit.ready`、`output_unit.structure_ok`。
  若 `output_unit/primitive/` 仍以 `trial_000_*` 等 trial-phase 样本作为主体，必须判定为失败。
  unit codegen 前置门禁：`exp_design_review.md` 与 `script/exp_design_review_gate.json` 必须存在，且 gate 中 `passed=true`。
  若 design review 门禁未满足，直接返回失败。
- `run_unit_review`
  必须调用 `stimuli-unit-function-review`，按 gate 状态执行两阶段：
  - request 阶段（gate 不存在或未 finalized）：只要求生成/刷新 `script/unit_function_review_gate.json`，并返回 `status=reviewing` + `decision.pause_workflow=true`，不得要求 `unit_function_review.md`。
  - finalize 阶段（gate 已 finalized 且 human_review_completed=true）：读取人工 gate，生成 `unit_function_review.md`，再按 gate 的 `passed/fallback_needed` 返回最终 verdict。
  request 阶段禁止覆盖人工 verdict；finalize 阶段禁止重新自动 VLM 判定覆盖人工结论。
- `run_review`
  必须调用 `stimuli-code-review`，按 gate 状态执行两阶段：
  - request 阶段（gate 不存在或未 finalized）：只要求生成/刷新 `script/review_gate.json`，并返回 `status=reviewing` + `decision.pause_workflow=true`，不得要求 `code_review.md`。
  - finalize 阶段（gate 已 finalized 且 human_review_completed=true）：读取人工 gate，生成 `code_review.md`，再按 gate 的 `passed/fallback_needed` 返回最终 verdict。
  request 阶段禁止覆盖人工 verdict；finalize 阶段禁止重新自动 VLM 判定覆盖人工结论。
  必须检查 `code_review.md` 与 `script/review_gate.json` 的一致性（仅 finalize 阶段要求）。
  必须确认 unit 前置门禁链已完成：`script/unit_function_review_gate.json`、`script/unit_manifest.json`、`unit_function_review.md`、`output_unit/primitive/`，且 unit gate 含 VLM 审计痕迹与逐张 issue 明细。
  `script/review_gate.json` 是 review 对后续修复回合的机器可读交接文件，`code_review.md` 是配套的人类可读说明。
  若 `review_gate.json` 表明外部视觉素材未审完、追溯不完整、或存在 placeholder 替代，则不得整理成成功。
- `run_eval`
  必须调用 `stimuli-dataset-evaluation`；若前置条件不足，可返回失败并写清 blocker。
- `write_result_report`
  必须调用 `stimuli-result-report`，并确认 `result_report.md` 已刷新。

## Failure Discipline
- 缺失关键证据时，不要伪造成功。
- 领域 skill 失败时，要把失败原因转成结构化 `error`。
- 只要 action 已完成核心目标，就不要因为领域 skill 没有 JSON 而返回空结果；由你负责补齐结构化结果。
