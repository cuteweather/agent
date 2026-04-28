# Exp Design Review Verification Checklist

## Core Metrics
- M-01 Evidence Traceability: 关键实现事实是否都能回链到 paper/data/code。
- M-02 Parameter Registry Fidelity: 参数定义是否完整、一致、可实现。
- M-03 Fact Consistency: Fact Ledger 与证据是否冲突。
- M-04 Phase & Condition Semantics: phase 语义与条件逻辑是否正确。
- M-05 Data Mapping Closure: 数据字段到实现参数是否闭环。
- M-06 Conflict/Missing Governance: 冲突是否有裁决、缺失是否明确阻断。
- M-07 External Asset Strategy (if required): 外部素材策略与追溯要求是否完备。
- M-08 Grounding Completeness (if reference figures exist): 有参考图时 grounding 是否充分重试并产出图片产物。
  - M-08a: `grounding_index.json` 存在且结构正确
  - M-08b: 所有 `reference_priority=figure_then_text` 的 family 均已使用 `--retry-sweep`（`retry_attempts` 非空）
  - M-08c: `retry_attempts` 中包含 `phase=fallback_prompt` 条目（已写入 fallback_prompts）
  - M-08d: 至少 1 个 family 产出了实际图片产物（mask/overlay/example），或所有 family 均满足 M-08b+M-08c 后仍为空

## Pass Rule
仅当 M-01 ~ M-08（适用项）全部通过，且无 critical issue，才能 `passed=true`。
