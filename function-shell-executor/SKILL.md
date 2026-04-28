---
name: function-shell-executor
description: 通用函数壳执行器。根据输入的函数壳(name+description)自主规划与执行任务，每个任务你都需要优先查找是否存在可用的skills/tools，若存在则调用，并输出机器可读结果文件。
---

# Function Shell Executor

## Purpose
执行“函数壳”任务：输入只包含函数名称和描述，不预设具体实现路径。

## Rules
1. 你可以自主决定执行策略，并按需调用其他可用 skills / tools。
2. 不得编造不存在的证据、数据或文件。
3. 所有产物应落在当前 workspace 内。
4. 若 prompt 明确提供 `function_result_path`，只能写这个路径，不能自行改写为默认 `function_result.json`。
5. 严禁写入或覆盖调用方保留的 workflow 机器状态文件；尤其不要主动创建或修改 step 目录下的 `function_result.json`，除非 prompt 明确要求该精确路径。

## Output Contract
若调用方 prompt 已提供结果文件路径和JSON字段要求，必须严格遵守。
至少保证：
- `success` 为布尔值
- `summary` 为字符串
- `artifacts` 为对象
- 失败时给出 `error`

## Failure Handling
当信息不足或约束冲突导致无法继续时：
- 明确标记 `success=false`
- 在 `summary` 和 `error` 中说明阻断原因
- 在 `artifacts` 中记录已产出文件（若有）
