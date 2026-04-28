---
name: stimuli-code-generation
description: 生成 scene composition、trial 调度与完整实验流程代码。此技能在 run_unit_codegen + run_unit_review 通过后，利用已审查通过的 primitive 函数（stimuli_primitives.py）组织成满足条件的刺激场景图片，并生成完整的 PsychoPy 复现代码。
---

# 原始刺激复现：Scene Composition 与完整实验代码生成（PsychoPy 直出版）

## 最高原则
- 本阶段是 **run_unit_codegen -> run_unit_review -> run_codegen -> run_review** 管线的 scene composition 与 trial 调度阶段。
- **前置条件**：`script/unit_function_review_gate.json` 必须 `passed=true`，`script/stimuli_primitives.py` 必须存在。
- **禁止重复实现 primitive 绘制函数**；必须 `from stimuli_primitives import ...` 复用已审查通过的 primitive 函数。
- 目标是生成**可直接运行**、**paper-specific**、**参数可追溯**的 scene composition 与 trial 复现代码。
- 对照 `paper/grounding/grounding_index.json` 中 `reference_role=layout_reference` 的布局图校正多刺激组合、相对位置与整体构型。
- 代码生成结果必须可被后续 `run_review` 消费：scene 组合层必须复用 `stimuli_primitives.py` 中已审查通过的 primitive 实现，而不是复制逻辑。
- `reproduce_stimuli.py` 中的 scene 组合、trial 调度、phase 渲染必须 import `stimuli_primitives` 模块，禁止重新定义已有 primitive 绘制函数。
- 最终 scene 图片输出到 `output/`（不是 `output_unit/`），供后续 `run_review` VLM 审计。
- **exp_design.md 是主要实现规格**；若缺失或冲突，必须先修复 exp_design，再写代码。
- **`<workspace>/data/` 中的源代码/配置/数据是上游最高优先级证据**；不得忽略。
- 若 workspace 已存在上一轮 review 产物，**`<workspace>/script/review_gate.json` 是 review -> generation 的机器可读主接口，`<workspace>/code_review.md` 只是人类可读补充说明**。- 禁止臆造参数与 trial 规则；缺失项必须显式标注并阻断对应实现。- 最终脚本必须直接调用 **PsychoPy**（少量 PsychoPy 无法覆盖的局部可用 Pygame 兜底）。
- 静态刺激导出必须面向 **headless/xvfb** 环境设计；不得假定存在可见窗口、front buffer 可读或 `flip()` 后抓帧一定有效。
- 静态刺激导出必须以“当前 phase 已绘制完成但尚未被翻转/清空”的缓冲内容为准；**禁止把 `flip()` 当作抓帧前提**。
- 颜色表示必须采用**单一约定**并在脚本中全局一致：要么统一使用 `rgb255`，要么统一使用 PsychoPy `rgb` 标准；禁止在同一脚本中混用不同颜色标度。
- 若使用 `units="pix"`，必须遵守 PsychoPy 像素坐标系约定：**屏幕中心为 `(0, 0)`**；不得将 `(width/2, height/2)` 误当作绘制中心。
- phase 语义必须按实验分支实现，不得用“视觉近似”替代条件语义。
- 在进行任何 PsychoPy 刺激实现、图元选型、phase 渲染与导出逻辑编写之前，必须先读取并**严格遵守**对应的 reference 文件（如 `references/psychopy-stimuli-pattern.md` 及同类约束文件）。任何实现不得绕过 reference 文件中已经显式锁定的渲染逻辑；尤其不得把已被 reference 指定实现方式的刺激（如连续色环、完整圆形、Pac-Man/缺口圆盘等）替换为更简化、更近似或更方便的 PsychoPy 写法。
- 涉及任何 PsychoPy 类、属性、方法、颜色空间或单位语义时，必须同步核对 `references/psychopy-official-docs.md` 中列出的官方文档；**reference 决定本项目内的实现策略，官方文档负责核对 API 名称、参数、默认行为**，不得只凭模型记忆写 PsychoPy 调用。
- 若官方文档中的默认行为与本技能的 headless 导出规范冲突，必须显式覆盖官方默认值并遵守本技能规范；典型例子包括 `getMovieFrame(buffer="back")`、统一输出 `jpg`、`allowGUI=False`、`deg/cm` 单位下显式配置 `Monitor`。

## 输入（按优先级）
0) **前置门禁产物（必须存在）**：
   - `<workspace>/script/unit_function_review_gate.json`：必须 `passed=true`，否则禁止进入本阶段。
   - `<workspace>/script/stimuli_primitives.py`：已审查通过的 primitive 绘制函数模块。
   - `<workspace>/script/unit_manifest.json`：primitive family 清单与函数映射。
   - `<workspace>/output_unit/primitive/`：已渲染的 primitive catalog 图片。
0) 若存在 `<workspace>/script/exp_design_review_gate.json` 与/或 `<workspace>/exp_design_review.md`，视为 exp_design review 回传。
0) 若存在 `<workspace>/script/review_gate.json` 与/或 `<workspace>/code_review.md`，视为上一轮 scene review 回传：
   - `script/review_gate.json`：权威的机器可读待修问题、通过状态与阻断项。
   - `code_review.md`：对问题证据、上下文与修复建议的展开说明。
1) `<workspace>/exp_design.md`
2) `<workspace>/data/`
3) `<workspace>/paper/`（仅作证据补充，不可绕开 exp_design 直接推断）
4) 若存在 `<workspace>/paper/grounding/grounding_index.json`，必须使用 `reference_role=layout_reference` 的布局图校正多刺激组合、相对位置与整体构型。
   - 单一刺激物保真度已由 `run_unit_review` 阶段确认，本阶段只关注组合布局。

## 输出文件（最小必选集）
- `script/config.py`
- `script/stimuli_config.toml`
- `script/trial_conditions.json`
- `script/parameter_traceability.json`
- `script/reproduce_stimuli.py`（最终可运行 PsychoPy 版本，必须 import `stimuli_primitives`）
- `output/`（最终 scene 图片输出目录）

若 `exp_design.md` 中声明存在未就绪的外部视觉素材，则还必须额外产出对应素材准备与追溯文件，至少包括以下之一或组合：
- `script/prepare_assets.py`（或等价素材准备脚本）
- `script/source_trace.json`
- `data/download_manifest.jsonl`
- `data/generated_manifest.jsonl`
- `script/image_prompts.jsonl`（仅当实际使用文生图）

为兼容后续 `run_review` 门禁，必须同时满足：
- `reproduce_stimuli.py` 必须 import `stimuli_primitives` 模块，不得重新定义已有 primitive 绘制函数。
- scene 组合函数（如 `compose_scene_*`、`build_display_*`）应调用 primitive 函数组装场景。
- 必须生成 `output/` 目录，包含每种 scene configuration 的样本图片。
- 提供最小可调用路径（函数或 CLI）以便在 `output/` 导出 scene catalog，无需完整 trial 全流程。

## 强制工作流
0) **前置门禁检查**（必须）：
   - 确认 `script/unit_function_review_gate.json` 存在且 `passed=true`；
   - 确认 `script/stimuli_primitives.py` 存在且可 import；
   - 确认 `script/unit_manifest.json` 存在且可解析；
   - 确认 `output_unit/primitive/` 存在且含真实图片。
   - 若任一不满足，直接失败并返回 blocker。
0) 若这是修复回合（workspace 中已存在 `script/review_gate.json` 或 `code_review.md`），必须先读取 review 回传并列出待修问题。
1) 从 `exp_design.md` 提取阶段流程、参数注册表、数据字段映射、条件逻辑。  
2) 从 `<workspace>/data/` 读取并规范化 paper-specific trial 条件，落地 `trial_conditions.json`。  
3) 将可追溯参数写入 `stimuli_config.toml`，并在 `parameter_traceability.json` 记录来源。  
4) 若实验刺激依赖任何外部视觉素材（背景图、对象图片、面孔库、场景照片、纹理图、公开图像数据集等）：
   - 先检查 `exp_design.md` 中的 `External Visual Asset Strategy`（或等价章节）；
   - 若 `asset_strategy = workspace_existing`，先验证工作区素材真实存在且可直接使用；
   - 若论文或 `exp_design.md` 指向具体公开数据集/公开图片库，优先按 `public_download` 路径准备素材；**`public_dataset` 不等于素材已就绪**；
   - 若只有语义类别、没有指定数据集，再使用 `image-search` 技能检索真实图片素材；
   - 若下载/检索结果在语义、构图、尺寸比例、许可可用性上仍不满足实验要求，再使用 `image-generate` 技能文生图；
   - 必须同步生成素材追溯文件（manifest / `source_trace` / prompt 记录）；
   - 若素材准备未完成，`run_codegen` 不能宣告成功，禁止跳过并直接进入 placeholder 版本代码。
5) 生成 `reproduce_stimuli.py`，要求：
   - **必须** `from stimuli_primitives import ...` 复用已有 primitive 函数；
   - 禁止重新定义与 `stimuli_primitives.py` 中同名或等价的绘制函数；
   - scene 组合函数调用 primitive 函数组装场景；
   - 使用 PsychoPy 渲染阶段刺激；
   - 按 trial 条件逐条渲染；
   - 输出图片格式必须统一为 `jpg`；
   - **禁止输出/依赖 SVG 主流程**；
   - 静态图片导出必须使用单一范式：`clearBuffer()` -> `draw()` -> `getMovieFrame(buffer="back")` -> 保存 jpg；
   - 若使用 `getMovieFrame(buffer="back")`，各 `render_phase_*()` 只允许 `draw()`，**不得在 phase 渲染函数内部 `flip()`**；
   - 每个 phase 开始前必须显式清空缓冲，不能依赖 `flip()` 充当清屏；对 blank/delay/ITI 等空屏阶段同样适用；
   - `capture_frame()` 与 `render_phase_*()` 职责必须严格分离：前者负责抓帧保存，后者负责绘制；
   - 若脚本支持并行渲染，`--workers` 默认值必须为 `1`，单进程验证通过后才允许提高并行度；
   - trial 内会影响后续 phase 的随机结果（颜色分配、位置映射、probe 索引等）必须显式保存并跨 phase 复用。
6) 生成后自检并修复：
   - 每个 phase 均有对应渲染分支；
   - 每个关键 trial 字段有明确使用路径；
   - 参数来源可追溯，不存在硬编码 magic 值。
   - 不得存在重复分支、不可达分支或遗漏关键刺激的 phase 渲染。
   - 不得原地修改共享配置对象（如直接 `shuffle` 配置列表、直接覆写全局参数列表），避免污染后续 trial。
   - 静态导出逻辑必须确认不会跨 phase 累积旧帧、旧 buffer 或旧随机状态。
   - 若代码同时出现“phase 内 `flip()`”与“`getMovieFrame(buffer=\"back\")` 抓帧”，必须判定为错误实现并修复后再交付。
   - 若当前是 repair round，需逐条回收 `review_gate.json` 中的 blocker / issue。
   - 必须确认 scene 组合函数与 `exp_design.md` 的 phase/对象定义可一一对应。
   - 必须确认 `reproduce_stimuli.py` import 了 `stimuli_primitives` 且未重复定义 primitive 函数。

6.5) scene 渲染与输出（必须）：
   - 最终 scene 图片输出到 `output/`（而非 `output_unit/`）。
   - 每种 scene configuration（如 grouped/ungrouped/partial 等）至少 1 张样本。
   - 可作为 `reproduce_stimuli.py --render-scenes-only` 或独立脚本实现。
   - 使用 `xvfb-run` 渲染，确保图片真实存在且非纯黑/纯白。

7) 渲染可执行性验证（必须）：
   - 渲染验证命令必须使用 `xvfb-run` 包裹的 PsychoPy 实际渲染命令。
   - 默认基线命令：
     - `xvfb-run -a -s "-screen 0 1280x1024x24" python script/reproduce_stimuli.py --max-trials 20`
   - 若实验主流程包含鼠标/键盘交互，必须让脚本支持 **仅渲染样本图片后退出** 的 review 模式；验证命令只能追加脚本 **已实现** 的参数，如 `--render-only`、`--review-mode`、`--auto-quit-after-render` 或等价参数。
   - 验证目标是 **实际生成图片**，不是完成受试者响应收集。
   - 上述验证必须以单进程单窗口方式完成；若脚本支持 `--workers`，未显式传参时仍应以单 worker 运行。
   - 验证必须连续通过 3 个硬门槛：
     1. `xvfb-run` 命令执行成功；
     2. 输出目录中实际存在图片文件；
     3. 至少 1 张期望非纯色图片通过 `PIL + numpy` 像素检查，不是纯黑、不是纯白。
   - 必须执行基础渲染质量检查：检测输出图片是否接近纯黑、纯背景或近零方差；若出现黑图/空图，判定为失败。
   - 若发现 headless 导出异常，优先修复静态导出流程（buffer/清屏/抓帧时机），不得仅通过增加 `flip()`、延时或重跑次数掩盖问题。
   - 任一门槛失败，都视为代码生成未完成，必须继续修复。
   - 禁止在本技能中使用 `python script/reproduce_stimuli.py ...` 直跑命令（即使 `DISPLAY` 可用）。

## PsychoPy 出图硬规则
- 交互实验必须提供非交互样本渲染路径；`review` / `render-only` 模式下必须至少输出 1 张真实图片，且优先按 phase 或 trial 命名。
- review/render-only 路径必须真的执行采帧与保存；禁止只 `flip()` 或只等待计时而不落盘。
- headless / `xvfb-run` 环境的默认采帧方案是 `win.getMovieFrame(buffer="back")` + `saveMovieFrames()`；最小模板见 `references/psychopy-headless-render.md`。
- 若要偏离这条纯 PsychoPy 出图链路，必须先确认 PsychoPy 无法满足目标需求，并把原因记录到实现说明或 review 记录中，再做最小范围回退。
- 在确认纯 PsychoPy 链路不可行时，才允许结合 `win.screenshot()` 或其他工具补齐保存步骤；回退范围必须最小化，且仍以 PsychoPy 负责实际绘制。
- 禁止在 headless / review 路径依赖 `win.getMovieFrame(buffer="front")`；该路径在 `xvfb + llvmpipe/GLX` 下可能生成纯黑图。
- 如果脚本封装了 `save_frame()` / `capture_frame()` / 等价 helper，样本渲染路径必须实际调用它；禁止存在未接入主流程的死保存函数。
- `--output-dir` 或等价输出参数必须贯穿到所有保存调用；禁止 CLI 接收了输出目录，但内部继续写死 `OUTPUT_DIR` 或 `/workspace/...`。
- headless/review 路径创建 `visual.Window()` 时必须显式 `allowGUI=False`，并创建 `Monitor` 后传入 `monitor=...`。
- 样本渲染完成后必须立即做图片 sanity check：`image_count > 0`，且至少 1 张图的像素统计不是纯黑、纯白或单一像素值。
- 若出现“`back` 正常、`front` 全黑”，必须判定为 front-buffer readback 兼容性问题，并改回 `back buffer` 或 `screenshot()`；不得把它误判成刺激绘制失败。
- 若纯 PsychoPy 的默认链路失败，禁止无记录地静默切换到其他库；只能在明确写出“为什么 PsychoPy 不可行”后再回退。
- 禁止臆造 CLI 参数；只能使用 `parse_args()` / `--help` 中已实现的参数。若验证需要新参数，先在脚本中补齐，再写入 skill 运行命令。

## 必读参考
- PsychoPy headless 最小出图模板与像素检查：`references/psychopy-headless-render.md`
- PsychoPy 官方文档索引与核对规则：`references/psychopy-official-docs.md`

## 必须遵守
- 不允许把核心参数写死在 `reproduce_stimuli.py`。
- `stimuli_config.toml` 必须包含 `render.phases` 且 `render.output_format = "jpg"`。
- `trial_conditions.json` 必须是 paper-specific 数据，不可使用虚构 trial。
- `parameter_traceability.json` 必须能定位参数来源（exp_design/data/code）。
- 外部视觉素材策略必须遵守 `workspace_existing/public_download -> image-search -> image-generate` 的优先级；禁止在未尝试下载/检索时直接文生图。
- 若 `exp_design.md` 中存在未就绪的外部视觉素材要求，必须先完成素材准备并写出追溯文件；仅生成 5 个核心脚本不足以视为 `run_codegen` 完成。
- 严禁使用 placeholder circle / rectangle / dummy label / 随机几何图形去代替本应存在的真实外部图片素材。
- 若由于网络、权限、账号或源站限制导致素材无法准备完成，必须显式返回 blocker；禁止静默降级为 placeholder 版本并继续交付。
- 最终 `reproduce_stimuli.py` 中必须存在 PsychoPy 导入与可运行入口。
- `reproduce_stimuli.py` 不得依赖 front-buffer/可见窗口导出模式作为主流程；静态图片导出必须采用 headless 友好的 back-buffer 抓帧逻辑。
- `reproduce_stimuli.py` 必须包含最小渲染自检逻辑；若输出图像为黑图、空图或近似纯背景图，应返回非成功状态或明确报错。
- 注意环境中可用的 psychopy 版本信息（当前基线为 2025.1.1），确保生成代码兼容，不包含已废弃功能或函数。
- 示例执行命令与文档/日志记录中，必须使用 `xvfb-run` 版本命令。
- 若实验包含交互响应，必须在脚本或 CLI 中显式提供无交互样本渲染能力，不能让 review 卡死在等待鼠标/键盘输入。
- 未通过图片存在性与像素 sanity check 的脚本，不得交付给 `stimuli-code-review`。
- `reproduce_stimuli.py` 的静态导出主流程**不得**在抓帧前调用 `flip()`；初始化性 `flip()` 必须与实际 phase 导出流程严格分离。
- 若静态导出采用 `getMovieFrame(buffer="back")`，phase 渲染函数内出现 `flip()` 视为实现错误（必须改为仅 `draw()`，由独立 `capture_frame()` 抓帧保存）。
- `reproduce_stimuli.py` 必须在一个明确位置统一声明并使用颜色空间约定；禁止窗口、背景、刺激分别采用不同颜色标度。
- 若窗口使用 `units="pix"`，则所有位置计算必须以 `(0, 0)` 为中心；禁止混用 PsychoPy 中心坐标与图像左上角坐标逻辑。

## 交付门槛
- 代码生成完成后，必须可被 `stimuli-code-review` 审核通过。
- 若 `exp_design.md` 记录了外部视觉素材需求，则只有在素材准备、追溯文件与渲染代码三者都齐全时，才能进入 `stimuli-code-review`。
- 若发现与 exp_design/data 不一致，先修正再交付，不得带病进入下一步。
