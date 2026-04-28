---
name: stimuli-exp-design
description: 从心理学论文原文、论文中的刺激插图(<workspace>/paper/...)、实验数据与参考代码(<workspace>/data/...)中，抽取复现实验所需的全部实现信息，生成严格可追溯、可核验引用的 exp_design.md；输出必须以 stimkit 为唯一刺激实现框架来表述参数、坐标、形状与渲染逻辑，并将 trial 流程、phase 级刺激规格、grounding stimulus families / reference basis、随机化/反平衡规则、数据字段↔实现参数映射统一纳入 Per-Experiment Specification。
---

# 心理学论文 exp_design.md 生成（stimkit 绑定、可核验引用）

## Overview

**最高纲领**：阅读工作区中的论文原文与论文中图像刺激的插图(<workspace>/paper/...)，以及提供的实验数据与可能的代码(<workspace>/data/...)，提取所有与复现实现有关信息形式化的，无歧义的，有原文引用的设计文档`exp_design.md`。

以下所有原则皆派生自该最高纲领：当规则冲突或缺失时，优先保证“形式化 + 无歧义 + 可核验引用”。

**特别强调**：若 `<workspace>/data/` 中提供源代码/参考实现，则其对**实现逻辑与超参数**具有**最高优先级**（高于论文文字描述）；必须显式引用并在冲突时以代码为准。

## 输出契约（必须满足）

严格按模板输出 `<workspace>/exp_design.md`，章节、表格与字段含义遵循：
- `references/output_contract.md`

## 图像识别执行约束（硬约束）

- 凡涉及论文插图、示意图、渲染输出图、PDF 页面等视觉识别任务，优先调用 `task(subagent_type="multimodal-looker", ...)`。
- 传给子代理的图片或 PDF 路径必须是绝对路径。
- 禁止使用 `look_at` / `look-at` 作为视觉识别兜底；视觉任务必须通过 `multimodal-looker` 子代理完成。

## 工作流程（按顺序执行）

1) 建立 Evidence Index
- 扫描 `<workspace>/paper/`（正文 + 刺激插图）与 `<workspace>/data/`（数据说明 + 参考实现/配置）
- 对需目视核验的图像证据，调用 `multimodal-looker` 子代理完成识别并记录证据链
- 为每个可引用片段分配 Evidence ID，并记录定位方式（文件路径、页码/标题、代码行区间、图号）
- 写入 `exp_design.md` 的 “Evidence Index” 章节（模板见 output_contract）

2) 抽取事实并入账（Fact Ledger）
- 将所有“会影响复现代码”的信息拆成最小事实单元（参数/规则/枚举/流程/判定条件）
- 每条事实必须：唯一表述 + Evidence 引用 + 置信度/来源类型（paper/figure/data/code/derived）
- 事实台账格式见 `references/output_contract.md` 与 `references/evidence_and_conflicts.md`

3) 处理冲突与缺失（禁止拍脑袋补数）
- 当 paper、figure、data、code 的表述不一致：
  - 建立 Conflict Log（见 `references/evidence_and_conflicts.md`）
  - 给出“采用哪个来源作为实现真值”的明确决策，并引用支撑证据  
  - **若 `<workspace>/data/` 中提供了源代码/参考实现：对实现逻辑与超参数，必须以源代码为最高优先级**
- 当关键参数缺失：
  - 记录为 “缺失项（Missing）”，列出需要哪类证据才能补齐
  - 禁止虚构数值、禁止用“通常/一般/大概”替代

4) 写 Per-Experiment Specification
- 对每个实验分别输出：
  - Design Summary：研究问题与操纵变量（只写与实现相关的那部分）
  - Trial 状态机 / Mermaid 流程图（带时长、输入、输出、分支条件）
  - 每个 Phase 的刺激几何定义（可在脑中复现，不依赖看图）
  - Grounding Stimulus Families & Reference Basis：
    - 先把将要进入后续实现的刺激按 `stimulus_family` 级别形式化，不能直接拿 figure caption 代替家族定义。
    - 每个家族都必须显式写出 `description`、`must_preserve`、`allowed_variation`、`figure_locator`（若存在参考图）。
    - 一条 family 只允许一种参考粒度：单一刺激示意图或布局图。若论文同时包含两者，必须拆成多条 family 记录，不能把单 item 与 layout 混在一条描述里。
    - 单一刺激示意图必须先覆盖 paper 中出现过的所有单 item 形式，供刺激检查使用；布局图作为独立 family 保留，供后续组合/code generation 参考。
    - **必须主动扫描 `<workspace>/paper/` 中所有图片文件（含 PDF 中插图），查找可用于 grounding 的参考图**；绝不可仅凭"没看到 grounding 目录"就跳过此步骤。
    - **可用于 grounding 的参考图一般是多个子图组合在一起的流程图**：只要图中可见 stimulus exemplar、trial screen、procedure panel、layout scene、response dial、search display、memory sample、comparison display 等任何能补充几何/颜色/布局/界面构型的信息，就算可用参考图；**不能**因为刺激“可以程序化生成”就把这类图排除掉。
    - **“程序化可生成”不是跳过 grounding 的理由**。即便论文已给出精确数学参数，只要 paper 中存在可见刺激图或流程面板，仍然必须进行grounding步骤。
    - 若论文里没有干净的单 item 示意图，但存在 procedure panel / scene / layout 图，仍然必须为该图建立至少 1 条 `layout_reference` 或 `fallback_anchor` 记录，供后续 scene/code review 使用。
    - 对有参考图的家族，**必须调用 `stimuli-grounding-segmentation` 技能**，生成 `paper/grounding/grounding_index.json` 与相应 crop/overlay/mask；此步骤不可跳过或延迟。
    - **必须实际执行 segmentation 脚本并验证产物落盘**：`paper/grounding/grounding_index.json` 文件必须真实存在于磁盘上，`paper/grounding/examples/`、`paper/grounding/overlays/`、`paper/grounding/masks/` 目录中必须有实际图片文件。禁止仅在 exp_design.md 表格中填写路径而不实际调用技能生成文件。
    - 若 grounding 成功，在 `exp_design.md` 中把该家族的 `effective_reference_basis` 记为 `crop_and_text`。
    - 若 grounding 失败，不得忽略；必须保留 `no_match` 记录，并把后续主要参考明确写为 `figure_and_text`。
    - **若所有 family 均返回 `no_match`（即有参考图但全部分割失败）**：这不等于"没有参考图"。必须排查原因（prompt 不准确、图片质量差、模型阈值过高等），尝试调整 prompt 或降低阈值重新执行至少一次。若重试后仍全部失败，必须在 `grounding_index.json` 中记录 `"status": "all_no_match"` 且保留所有 `no_match_reason`，并在 exp_design.md 中显式标注此情况。禁止将"有参考图但全部分割失败"伪装为 `no_reference_figures`。
    - 只有在主动扫描后确认 paper 中所有图片都只是结果图、统计图、表格截图、纯注释图，且**没有任何**可见 stimulus exemplar / procedure panel / layout scene 时，才允许把该家族标为 `text_only`，并要求文字约束足够具体。
    - **无论是否找到参考图，`paper/grounding/grounding_index.json` 都必须产出**。若确认无参考图，写入 `{"status":"no_reference_figures","families":[],"scan_summary":"scanned N files in paper/, found 0 usable reference figures"}` 并确保文件落盘。
  - Randomization & Counterbalancing：随机化/反平衡/试次数量/Block 结构
- 如果不同组（如 integrated vs separate）刺激结构不同：明确分叉并分别定义

5) 数据字段 ↔ 实现参数闭环
- 构建 Data Dictionary：每列类型、取值范围、语义
- 构建 Mapping：数据字段 → 派生变量 → stimkit 参数/primitive
- 若参考代码存在：以“可核验引用”的方式记录其实现细节，并**以其作为实现真值优先级最高的来源**
- 细则见 `references/data_mapping.md`

6) 外部视觉素材策略建模（当实验依赖任何外部图片素材时必须执行）
- 适用范围不仅包含背景图，还包含对象图片、面孔库、场景照片、纹理图、图标集、公开图片数据集等一切**不是纯文本或纯数学参数就能直接生成**的视觉素材。
- 必须先检查 `<workspace>/data/` 与其他已提供目录中是否已有可直接使用的素材；若没有，而论文/数据又引用了公开数据集或公开图片库，**禁止**把该情况写成 “Not applicable”。
- 在 `exp_design.md` 中必须单列 `External Visual Asset Strategy`（或等价标题）章节，并为每个素材家族逐项写明：
  - `exact` 还是 `substitute`
  - `asset_strategy`：`workspace_existing` / `public_download` / `image_generation` / `mixed`
  - 若是公开数据集或已知图片库：具体来源、下载入口或数据集名称
  - 若是检索替代：检索关键词、筛选约束、许可约束
  - 若需要文生图回退：允许回退的前提与必须保留的语义/视觉约束
  - 与实验条件的 trial 级映射方式
  - 后续 `run_codegen` 必须产出的追溯文件（如 `source_trace`、manifest、prompt 记录）
- 资源获取顺序固定为：
  1. 先用 `workspace_existing` 或明确的 `public_download` 路径补齐论文指定的公开素材；
  2. 若只有语义类别而无指定素材库，再用 `image-search` 技能检索真实素材；
  3. 若下载/检索结果仍不满足要求（语义/构图/比例/许可），再用 `image-generate` 技能文生图。
- 禁止把论文中“public dataset”这类字样直接等同于“素材已就绪”。
- 禁止用 placeholder/dummy 图形替代本应准备的外部图片素材并把它写成完成态。

## stimkit 绑定（强制）

- 所有几何/颜色/渲染必须能直接落到 stimkit 的坐标与 primitive 表述
- 坐标系、角度零点、旋转正方向等约定：以 stimkit 源码/文档为实现真值；若找不到，写入缺失项并阻断相关推导
- 细则见 `references/stimkit_binding.md`

## 最小自检（写完后必须过一遍）

- 每个数值参数都出现在 Fact Ledger 或 Parameter Registry，且至少有 1 个 Evidence 引用
- 每条流程分支（条件→呈现→响应→记录）都能在 Mermaid 图中找到对应节点
- 每个 trial-level 随机变量都有：取值空间、约束、随机化单位（trial/block/subject）、是否需要固定 seed
- 每个数据字段都在 Data Dictionary 出现；每个被代码使用的字段都能映射到具体视觉参数或判定逻辑
- 只要 paper 中存在可用参考图，必须确认已经实际调用过精确技能名 `stimuli-grounding-segmentation`，而不是只在文档里提到 grounding。
- 若存在任何外部视觉素材家族，`exp_design.md` 中必须出现对应的素材策略、追溯要求与 trial 映射；不能仅在 Missing Items 中轻描淡写带过- **Grounding 产物验证**：若 exp_design.md 中任何 `effective_reference_basis` 写了 `crop_and_text`，则必须确认 `paper/grounding/grounding_index.json` 真实存在于磁盘上，且对应的 examples/overlays/masks 目录中确实有图片文件；若文件不存在，说明 `stimuli-grounding-segmentation` 技能未被实际执行，必须立即补执行后再交付。- `exp_design.md` 中不得出现“等等/类似/大概/通常”这类不可核验表述

## 注意：
在生成 exp_design.md 时，必须优先刻画“刺激的真实实验属性与保真边界”，而不仅是给出一个可画出来的近似示意。

对于论文中的关键刺激，exp_design.md 必须首先回答：
1. 该刺激在实验中属于哪一类对象（如标准连续色轮、离散配置刺激、占位提示物、反馈标记等）；
2. 该刺激的哪些属性是实验本质属性，不能被替换、简化或降级；
3. 哪些信息缺失只会阻断精确参数实现，哪些缺失绝不允许改变刺激类别本身；
4. 若存在实现不确定性，必须显式限定“允许的实现空间”和“禁止的降级实现”，避免后续代码生成把高保真刺激退化为低保真近似物。
