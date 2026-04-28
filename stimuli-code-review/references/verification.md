# Review 检查清单

最小 PsychoPy headless 基线样例见：`psychopy-headless-render.md`

## 1) 代码规范性（必须逐项核对）

### 1.0 前置门禁（必须先过）
- 必须先确认 `script/unit_generation_gate.json` 存在且 `passed=true`。
- 必须确认 `script/unit_generation_gate.json` 中 `primitive_units.ready=true`、`output_unit.ready=true`、`output_unit.structure_ok=true`。
- 必须确认 `script/unit_manifest.json` 存在且可解析。
- 必须确认 `script/unit_manifest.json` 非空且 schema 基本合法（至少包含 `generated_at`、`generator_script`、`primitive_families`、`paper_mapping`、`output_structure`）。
- 必须确认 `script/unit_manifest.json` 与 gate 引用一致（`unit_manifest.path` 指向 manifest，`output_unit.path/primitive_dir` 与 manifest 一致）。
- 必须先确认 `script/unit_function_review_gate.json` 存在且 `passed=true`。
- 必须确认 `script/unit_function_review_gate.json` 中 `primitive_units.ready=true`、`output_unit.ready=true`、`output_unit.structure_ok=true`。
- 必须确认 `script/unit_function_review_gate.json` 中 `vlm_review.executed=true`。
- 必须确认 `script/unit_function_review_gate.json` 中 `vlm_review.sampled_images` 为非空列表、`vlm_review.issues` 为逐张明细列表。
- 必须确认 `script/unit_function_review_gate.json` 中 `critical_mismatches` 是空列表，且不存在 `verdict=fail` 的 VLM issue。
- 必须确认 `output_unit/` 是标准 catalog（含 `primitive/`），且有真实样本图。最终场景图片应输出到 `output/`。
- 若前置门禁未满足，review 结论必须为阻断，不得继续给出“可通过”判定。

### 1.1 规范与结构
- `exp_design.md` 的 Parameter Registry 与 `stimuli_config.toml` **完全对应**。
- `config.py` 使用 `StrictModel`，字段类型与 TOML 对齐；无未建模字段。
- `SceneConfig` 仅含调度字段；视觉参数仅存在于配置模型中。
- `render_trial` 只做调度；phase 渲染函数只负责 `draw()`，抓帧与保存由独立导出路径负责。
- **不使用位置参数**，所有函数调用使用 `xxx=yyy`。

### 1.2 依赖与 API 使用
- 视觉图形优先使用 `stimkit.collections` 工厂函数；仅在缺失时使用 matplotlib Patch。
- 禁止 thin wrapper（仅改名/改参/重排的 helper）。
- 数据加载优先 `stimkit.io` 提供的函数，且仅保留 exp_design 指定字段。
- 若脚本有 `capture_frame` / `save_frame` / 等价 helper，必须检查该保存逻辑是否被样本渲染主路径真实调用。
- 若使用 `saveMovieFrames()`，必须检查前面是否有 `getMovieFrame(buffer="back")` 或等价的安全采帧逻辑；若脚本在 headless 路径依赖 `getMovieFrame(buffer="front")`，按高风险问题处理。
- 若脚本偏离默认的纯 PsychoPy 出图链路，必须检查是否明确记录了“为什么 PsychoPy 不可行”以及回退范围；若没有，按规范性问题处理。
- 若脚本支持 `--output-dir` 或等价输出参数，必须检查保存逻辑是否真的使用该参数，而不是继续写死默认目录。
- blank/delay/ITI 等空屏阶段必须显式清屏并独立导出，禁止复用上一阶段残留帧。
- 若使用 `units="pix"`，位置坐标必须围绕 `(0, 0)` 中心定义，禁止混入左上角坐标系。
- 颜色空间必须全局一致（`rgb255` 或 PsychoPy `rgb` 二选一），禁止混用。

### 1.3 随机化与可复现性
- 随机化仅来自 exp_design 规定；`seed` 贯穿所有分支。
- 不存在隐式随机或未声明的随机化逻辑。

### 1.4 exp_design 事实级核对（必须执行）
- 必须从 `exp_design.md` 抽取关键事实（phase 语义、condition 逻辑、scene 定义、关键参数）形成逐条核对清单。
- 必须明确区分“参数一致”与“语义一致”；两者任一不满足即判定不通过。
- 每条关键事实都必须有实现证据（代码路径或输出证据），不能只给结论。

### 1.5 trial / condition 逻辑核对（必须执行）
- 必须核对 trial scheduler、condition generator、block/interleaving/between-subject 结构与 `exp_design.md` 一致。
- 禁止仅凭样本图像判断逻辑正确，必须审查代码中的调度与条件分配实现。
- 出现 between-subject 因子误实现为 within-trial 交替（或反向错误）时，直接判定关键失败。

## 2) 输出图像与 scene 审查（必须目视）

### 2.1 覆盖抽样策略
- 至少覆盖每个实验/组别各 1 例；若条件分支较多，补充关键边界条件。
- 若 `<workspace>/data/` 提供参考输出或源代码生成图，优先与其对比。
- 图片核验优先使用 `multimodal-looker`，并确保传入绝对路径。

### 2.2 视觉一致性
- 结构与布局与参考图一致：位置、间距、对齐关系、对称性。
- 颜色、线宽、形状、大小与条件对应一致。
- 不同阶段（Phase）的差异与 exp_design 的描述一致。

### 2.3 scene 对象清单检查（必须执行）
- 对每个关键 phase 核对“必须出现对象”与“禁止出现对象”。
- 必须识别并记录多画、漏画、错 phase 复用、跨 phase 对象残留。
- 对 neutral/invalid/probe 等关键条件，必须逐项验证 scene 对象是否符合语义定义。

### 2.4 negative checks（反向检查）
- invalid 条件下是否错误省略 cue。
- probe phase 是否错误保留 memory array 或其他不该出现对象。
- neutral 条件是否被错误泛化为其他条件模板。
- 条件切换时是否错误沿用上一个 trial 的 scene 状态。

### 2.5 边界与裁剪检查
- 画布边界内无越界绘制、无裁剪痕迹。
- 边缘元素不应被边框或裁剪截断。
- 若存在边界相关规则（如留白/安全边距），必须符合。

### 2.6 样本出图真实性检查
- 不只检查图片文件是否存在；必须记录至少 1 张样本图的像素统计，如 `min/max`、`unique 值数量` 或 `all_black`。
- 若图片全黑、全白或单一像素值，先检查采帧实现与保存路径，再考虑环境问题。
- 若出现“`back` 正常、`front` 全黑”，优先判定为 front-buffer readback 不兼容；应修成 `back buffer` / `screenshot()` 路径，而不是宣布渲染失败。
- 若实现使用了非默认回退路径，但缺少 PsychoPy 不可行的证据与说明，应判为实现说明不充分。
- sample render 命令必须与脚本 `parse_args()` / `--help` 一致；使用未声明参数属于 review 命令错误，不得据此下环境结论。
- 若容器基础 PsychoPy smoke test 未跑，不得直接把当前失败定性为环境 blocker。

## 3) 结论输出格式
- `review_gate.json` 必须包含 `exp_design_checks`、`scene_inventory_checks`、`condition_logic_checks`、`critical_mismatches`。
- `critical_mismatches` 只要非空，`passed` 必须为 `false`。
- “能渲染 + 非黑图 + 大致像”不得作为通过依据；必须同时满足参数、phase 语义、scene 对象、trial/condition 逻辑四项一致性。
- **问题清单**：文件名、条件、期望、观察、影响。
- **建议修复点**：对应 `config.py`、`stimuli_config.toml`、`reproduce_stimuli.py` 或 exp_design 的具体位置。
- **归因结论**：明确区分“脚本实现问题”“review 命令问题”“环境问题”；禁止把脚本缺陷误写成环境故障。
