---
name: stimuli-result-report
description: 基于统一 manifest 与当前工作区状态刷新 result_report.md，记录执行动作、证据、剩余风险与当前结论。
---

# Stimuli Result Report

## Purpose
你的唯一任务是更新 `<workspace>/result_report.md`。输入中的 manifest 是当前流程唯一可信的调度事实来源。

## Rules
- 必须读取 manifest，并基于 manifest 中的 `decision_history`、`action_history`、`completion`、`workspace_state` 撰写结果报告。
- 必须说明：本轮执行了哪些显式 action、哪些产物已更新、哪些 blocker 已解决、哪些风险仍未解决。
- 若当前状态不可复现或仍失败，必须写清阻断证据与原因；禁止把失败写成成功。
- 不负责选择下一步 action，不负责 finish 决策。

## Required Report Content
- 当前轮次实际执行的 action 摘要
- 关键产物状态：`exp_design.md`、`script/`、`code_review.md`、`script/review_gate.json`、`result_report.md`
- 关键 blocker / risk
- 当前建议结论：可交付 / 不可复现 / 仍需修复

## Output Contract
按调用方要求返回结构化 JSON，并确保 `<workspace>/result_report.md` 已更新。
