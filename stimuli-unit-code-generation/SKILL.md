---
name: stimuli-unit-code-generation
description: 生成单体刺激物（primitive）的 PsychoPy 绘制函数与 unit catalog。此技能从 exp_design.md 提取所有可能出现的刺激物形状定义，为每种刺激物类型生成独立的 PsychoPy 绘制函数（含背景图片处理），并渲染 primitive catalog 供后续 unit review 审查。
---

# 原始刺激复现：单体刺激物代码生成（Unit Codegen）

## 最高原则
- 本阶段只负责 **单体刺激物（primitive）** 的代码生成与渲染，不负责 scene 组合、trial 调度或完整实验流程。
- 每种刺激物类型实现为一个独立的 PsychoPy 绘制函数（如 `draw_pacman()`、`draw_diamond()`、`draw_gabor()` 等），可视为一个可复用的"类"。
- 刺激物函数必须覆盖该类型在实验中所有可能出现的变体（颜色、朝向、大小等参数化），通过函数参数控制变体。
- 若实验存在背景图片或外部视觉素材作为刺激物的一部分，也必须在本阶段处理（图片加载函数、预处理逻辑）。
- 对照 `paper/grounding/grounding_index.json` 中 `reference_role=primary_example` 的参考图锁定 primitive 几何、颜色与朝向。
- **exp_design.md 是主要实现规格**；若缺失或冲突，必须返回失败，并告知上层orchestrator 需要补充或修正 exp_design.md。
- **`<workspace>/data/` 中的源代码/配置/数据是上游最高优先级证据**；不得忽略。
- 禁止臆造参数；缺失项必须显式标注并阻断对应实现。
- 所有 PsychoPy 函数必须面向 **headless/xvfb** 环境设计。
- 颜色表示必须采用**单一约定**并在脚本中全局一致。
- 若使用 `units="pix"`，必须遵守 PsychoPy 像素坐标系约定：**屏幕中心为 `(0, 0)`**。
- 在进行任何 PsychoPy 刺激实现之前，必须先读取并**严格遵守**对应的 reference 文件（如 `references/psychopy-stimuli-pattern.md` 及同类约束文件）。
- 涉及任何 PsychoPy 类、属性、方法时，必须同步核对 `references/psychopy-official-docs.md`。

## 输入（按优先级）
0) 若存在 `<workspace>/script/unit_function_review_gate.json`，视为上一轮 unit review 回传（修复回合）：
   - 优先按 gate 中的 `critical_mismatches` 和 `vlm_review.issues` 修复 primitive 实现。
1) `<workspace>/exp_design.md`
2) `<workspace>/data/`（源代码/参考实现/配置）
3) `<workspace>/paper/`（论文与参考图）
4) `<workspace>/paper/grounding/grounding_index.json`：
   - 使用 `reference_role=primary_example` 的单一刺激示意图锁定 primitive 几何、颜色与朝向。

## 输出文件（最小必选集）
- `script/stimuli_primitives.py`（所有单体刺激物绘制函数）
- `script/render_unit_catalog.py`（unit 渲染入口，遍历所有 primitive 并导出）
- `script/unit_manifest.json`（primitive family 清单与映射）
- `script/unit_generation_gate.json`（机器可读门禁）
- `output_unit/primitive/`（渲染出的 primitive catalog 图片）

若 `exp_design.md` 中声明存在未就绪的外部视觉素材用于 primitive 定义，则还必须额外产出素材准备与追溯文件。

## Non-Goals
- 不生成 scene 组合逻辑、trial 调度逻辑、`reproduce_stimuli.py`。
- 不生成最终 scene 图片（scene 由后续 `run_codegen` 输出到 `output/`）。
- 不做 textual fidelity review 或 VLM 审查。
- 不生成 `unit_function_review.md` 或 `unit_function_review_gate.json`。
- 不生成 `config.py`、`stimuli_config.toml`、`trial_conditions.json`、`parameter_traceability.json`（留给 `run_codegen`）。

## `stimuli_primitives.py` 规范
- 每种刺激物类型对应一个顶层绘制函数，函数签名清晰、参数化、有 docstring。
- 函数接收 PsychoPy `Window` 对象和刺激物参数（颜色、大小、朝向、位置等），在 window 上绘制对应刺激物。
- 函数只负责 `draw()`，**不得** `flip()`、`clearBuffer()`、或保存图片。
- 函数必须可被外部脚本直接 import 调用（`from stimuli_primitives import draw_pacman`）。
- 若某类刺激物需要预加载图片/纹理，提供对应的 `load_*()` 或 `init_*()` 辅助函数。
- 必须在文件顶部统一声明颜色空间约定。
- 若存在多个实验（experiments），primitive 函数按刺激物类型组织，而非按实验组织；不同实验共享同一 primitive 函数。

## `render_unit_catalog.py` 规范
- 独立可运行的渲染入口，import `stimuli_primitives.py` 中的函数。
- 遍历每个 primitive family 的所有关键变体，渲染到 `output_unit/primitive/`。
- 命名规范：`output_unit/primitive/{family_name}_{variant_desc}.jpg`。
- 使用 headless PsychoPy 渲染：`clearBuffer()` -> `draw()` -> `getMovieFrame(buffer="back")` -> 保存 jpg。
- 必须创建 `Monitor` 并传入 `monitor=...`，`allowGUI=False`。
- 必须以 `xvfb-run` 包裹执行。
- 渲染后必须执行像素 sanity check：图片存在、非纯黑、非纯白。

## Output Directory Contract
`output_unit/primitive/` 必须是 primitive catalog，不是 trial 缓存。

禁止把以下 trial-phase 命名作为 unit 主体：
- `trial_000_fixation.jpg`、`trial_000_memory.jpg`、`trial_000_probe.jpg`
- 任意 `trial_###_*` 目录/文件

## 强制工作流
0) 若这是修复回合（workspace 中已存在 `script/unit_function_review_gate.json` 且 `passed=false`），必须先读取 review 回传并列出待修问题；优先按 gate 的 `critical_mismatches` 和 `vlm_review.issues` 修复。
1) 从 `exp_design.md` 提取所有 primitive 刺激物定义：类型、几何参数、颜色集合、朝向、大小等。
2) 从 `<workspace>/data/` 读取 paper-specific 参考实现（若有），提取 primitive 绘制逻辑。
3) 若存在 `paper/grounding/grounding_index.json`，读取 `reference_role=primary_example` 的参考图，核对 primitive 几何与颜色。
4) 生成 `script/stimuli_primitives.py`：每种 primitive 一个绘制函数，参数化覆盖所有变体。
5) 生成 `script/render_unit_catalog.py`：遍历 primitive family 渲染 catalog。
6) 使用 `xvfb-run -a -s "-screen 0 1280x1024x24" python script/render_unit_catalog.py` 执行渲染。
7) 检查 `output_unit/primitive/` 目录：图片存在、非空、非纯黑/纯白。
8) 生成 `script/unit_manifest.json`，记录 primitive family 清单。
9) 生成 `script/unit_generation_gate.json`，输出门禁结论。

## unit_manifest.json 最小字段
```json
{
  "generated_at": "ISO timestamp",
  "generator_script": "script/render_unit_catalog.py",
  "primitives_module": "script/stimuli_primitives.py",
  "primitive_families": [
    {
      "family_name": "string",
      "function_name": "draw_xxx",
      "variants": ["variant_desc"],
      "samples": ["output_unit/primitive/xxx.jpg"],
      "exp_design_ref": "exp_design.md#section"
    }
  ],
  "paper_mapping": "与实验刺激物类型的映射说明"
}
```

## unit_generation_gate.json 最小字段
```json
{
  "passed": true,
  "summary": "string",
  "primitive_units": {
    "ready": true,
    "missing": [],
    "families": []
  },
  "unit_manifest": {
    "ready": true,
    "path": "script/unit_manifest.json"
  },
  "output_unit": {
    "ready": true,
    "structure_ok": true,
    "path": "output_unit",
    "primitive_dir": "output_unit/primitive",
    "image_count": 0
  },
  "critical_issues": []
}
```

## Hard Gate Rules
- `critical_issues` 非空时，`passed` 必须为 `false`。
- `primitive_units.ready != true` 时，`passed=false`。
- `unit_manifest.ready != true` 时，`passed=false`。
- `output_unit.ready != true` 或 `output_unit.structure_ok != true` 时，`passed=false`。
- 若发现 trial 样本伪装为 unit 主体，必须 `passed=false` 并写入 `critical_issues`。
- 渲染后图片全黑/全白/纯背景色，必须 `passed=false`。

## 渲染可执行性验证（必须）
- 渲染命令必须使用 `xvfb-run` 包裹。
- 默认命令：`xvfb-run -a -s "-screen 0 1280x1024x24" python script/render_unit_catalog.py`
- 验证连续通过 3 个硬门槛：
  1. `xvfb-run` 命令执行成功；
  2. `output_unit/primitive/` 中实际存在图片文件；
  3. 至少 1 张图片通过 `PIL + numpy` 像素检查，不是纯黑、不是纯白。
- 任一门槛失败，视为代码生成未完成，必须继续修复。
- 禁止在本技能中不使用 `xvfb-run` 直跑命令。

## PsychoPy 出图硬规则
- headless/xvfb 环境默认采帧方案：`win.getMovieFrame(buffer="back")` + `saveMovieFrames()`。
- phase 渲染函数只 `draw()`，不 `flip()`。
- 创建 `visual.Window()` 时必须 `allowGUI=False`，并创建 `Monitor` 后传入。
- 输出图片格式统一 `jpg`。
- 颜色空间全局一致，不混用。
- 禁止依赖 `getMovieFrame(buffer="front")`。

## 必读参考
- PsychoPy headless 最小出图模板：`references/psychopy-headless-render.md`
- PsychoPy 官方文档索引：`references/psychopy-official-docs.md`
- PsychoPy 刺激模式约束：`references/psychopy-stimuli-pattern.md`

## 与下游的交接契约
- `script/stimuli_primitives.py` 是 `run_unit_review` 审查的 textual 对齐对象。
- `script/unit_manifest.json` 和 `script/unit_generation_gate.json` 是 `run_unit_review` 的前置门禁产物。
- `output_unit/primitive/` 是 `run_unit_review` 的 VLM 审计图片来源。
- `script/stimuli_primitives.py` 也是后续 `run_codegen`（scene composition）的 import 依赖。

## Return Contract
按调用方要求返回结构化 JSON。
- 当 `unit_generation_gate.passed=true` 时可返回 `succeeded`。
- 否则返回 `failed_retryable`，并在 `summary` / `error` 中给出 blocker。

## 外部视觉素材处理
若实验刺激依赖外部视觉素材（背景图、对象图片等）作为 primitive 的一部分：
- 先检查 `exp_design.md` 中的 `External Visual Asset Strategy`；
- 若 `asset_strategy = workspace_existing`，验证素材存在；
- 若指向公开数据集，按 `public_download` 路径准备；
- 若只有语义类别，使用 `image-search` 技能检索；
- 若仍不满足，使用 `image-generate` 技能文生图；
- 必须同步生成素材追溯文件。
- 素材未就绪时不得宣告成功。
