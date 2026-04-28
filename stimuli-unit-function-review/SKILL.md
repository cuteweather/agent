---
name: stimuli-unit-function-review
description: run_unit_review 的两阶段人工审核门禁。第一次生成 gate 并暂停，人工填写后再 finalize 生成 unit_function_review.md。
---

# Unit Function Review（Manual Pause/Resume）

## 目标
`run_unit_review` 必须在同一个 action 内支持两阶段：
1. `request_manual_review`：只生成/刷新 gate，并触发 workflow pause。
2. `finalize_manual_review`：读取人工填写后的 gate，生成最终 `unit_function_review.md`，并给出 passed/fallback 结论。

禁止新增 action 名，禁止新增平行 step。

## 固定输入与输出
- gate 路径固定：`<workspace>/script/unit_function_review_gate.json`
- 最终报告路径固定：`<workspace>/unit_function_review.md`

## 阶段判定（只看 gate）
- 若 gate 不存在，或存在但未标记人工完成：进入 `request_manual_review`
- 若 gate 已标记人工完成：进入 `finalize_manual_review`

人工完成判定规则：
- `human_review_completed == true`，且
- `review_status == "finalized"`

## gate 协议（必须包含）
```json
{
  "review_status": "pending_manual_review | finalized",
  "human_review_completed": false,
  "passed": false,
  "fallback_needed": true,
  "summary": "string",
  "findings": [],
  "checks": {},
  "vlm_review": {},
  "critical_mismatches": [],
  "next_actions": []
}
```

可直接参考模板：`references/unit_function_review_gate.template.json`。

说明：
- `gate` 是唯一人工输入入口。
- request 阶段可补充 skeleton 与运行元信息，但不得伪造“已人工完成”。
- finalize 阶段不得覆盖人工已填写 verdict（尤其 `passed/fallback_needed/summary/findings`）。

## Phase A: request_manual_review
必须执行：
1. 生成或刷新 `script/unit_function_review_gate.json` skeleton。
2. 若 gate 已存在且包含人工填写字段，仅允许补充非冲突元数据，不覆盖人工 verdict。
3. 不生成 `unit_function_review.md`。

返回 JSON（必须）：
```json
{
  "status": "reviewing",
  "success": false,
  "summary": "unit manual review requested; fill gate then resume",
  "artifacts": {
    "unit_function_review_gate": "<workspace>/script/unit_function_review_gate.json"
  },
  "evidence": {
    "files_read": [],
    "files_written": ["<workspace>/script/unit_function_review_gate.json"],
    "commands_run": [],
    "subagents": []
  },
  "decision": {
    "retryable": false,
    "next_step": null,
    "terminate_workflow": false,
    "pause_workflow": true,
    "resume_step": "meta_orchestrator",
    "pause_reason": "manual_review_pending"
  },
  "error": null
}
```

## Phase B: finalize_manual_review
必须执行：
1. 读取人工 finalized gate。
2. 基于 gate 内容生成 `unit_function_review.md`（报告内容必须来自人工 gate，不得重新自动 VLM 判定覆盖）。
3. 根据 gate 的 `passed/fallback_needed` 生成最终 verdict。

finalize verdict 规则：
- `passed=true` 且 `fallback_needed=false` -> `status=succeeded`
- 其他情况 -> `status=failed_retryable`

返回 JSON（必须）：
- `artifacts` 至少包含 gate 与 `unit_function_review.md` 路径。
- 若失败，`summary/error` 需明确指出由人工 gate 判定触发 fallback。

## 明确禁止
- 禁止在本技能内等待人工输入（轮询/阻塞）。
- 禁止在 finalize 阶段重跑自动 VLM 并覆盖人工结论。
- 禁止把 pause 伪装为 failed_terminal/terminate_workflow。
- 禁止更改 gate/report 固定路径。
