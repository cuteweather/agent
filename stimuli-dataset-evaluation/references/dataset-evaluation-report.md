# dataset_evaluation_report.md — <PAPER_TITLE>

> **执行声明**: 本报告由自动化审计脚本 `evaluate_dataset.py` 驱动 LLM + `multimodal-looker` 多模态子 agent 高并发代理生成。
> **审计铁律**: 报告遵循“无死角可追溯”原则，所有涉及图像抽样的评测环节，必须 100% 列出被抽样的图片路径、对应的基准参数及单次推理的详细判决结果，拒绝任何模糊的“黑盒打分”。
> **术语说明**: 文中“多模态审计子 agent”统一指 `multimodal-looker`；该 agent 可能不会显示在 agent 列表界面中，但运行环境可能已显式注册。所有图片判断结论都必须来自该子 agent 对实际图片的审计输出。

## 1. Dataset Metadata (数据集元数据)

| Attribute | Value | Source / Notes |
|:---|:---|:---|
| Paper Title | <PAPER_TITLE> | `exp_design.md` |
| Total Images Generated | <int> | `output/` structure traversal |
| Total Conditions Generated | <int> / <int> (Actual/Theoretical) | Parameter Space Coverage |
| Stimulus Types | <e.g., Gabor patches, Moving Dots> | Extracted from `exp_design.md` |
| SIC Score (Complexity) | <float> | See Metric M-05 |
| Recommended Input Format | <Single-Image VQA / Multi-image Sequence> | Multi-image if SIC > 2.0 |
| Audit Environment | <`multimodal-looker` subagent with absolute image paths> | Verification of subagent availability and image-path consistency |

---

## 2. Quantitative Metrics Ledger (量化指标总台账)

> Rule: Accuracy for M-01 requires all 6 sub-dimensions to PASS. Status must be PASS / FAIL.

| Metric ID | Dimension | Metric Name | Auditing Engine | Global Score | Status |
|:---|:---|:---|:---|:---|:---|
| M-01 | Visual-Text | 视觉与文本语义对齐度 | multimodal-looker 6维特征像素级验证 | Accuracy: <float>% | <PASS/FAIL> |
| M-02 |Code-Visual | 参数注册表逐项保真度 | LLM代码审查 + multimodal-looker 视觉验证| Score: <float>% | <PASS/FAIL> |
| M-03 | Fine-Tuning | 条件视觉区分度 | multimodal-looker 跨条件盲分类抽测 | Accuracy: <float>% | <PASS/FAIL> |
| M-04 | Fine-Tuning | 交互时序复杂度 (SIC) | 规则解析 (Phases/Branching) | Score: <float> | <INFO> |
| M-05 | Trial Logic | Trial跨阶段参数连续性 | multimodal-looker + LLM Trial级审计 | Accuracy: <float>% | <PASS/FAIL> |
---

## 3. Detailed Evaluation Logs (评测详细过程与全量抽样明细)

### 3.1 M-01: 视觉与文本语义对齐度 
- **Process**: Sampled 20-30 images per condition. Sub-agent invoked `multimodal-looker` with a zero-tolerance audit prompt. Each image was checked against `exp_design.md`and `./data` for 6 dimensions: **Shape, Color, Position, Size, Count, and Spatial Integrity (Clipping/Occlusion)**.
- **Decision Rule**: An image is marked **PASS** only if all 6 dimensions are "Pass".
- **Detailed Result**: 
  - Total Samples: `<int>`
  - Overall Accuracy: `<float>%`
- **Analysis**: <Analyze which specific dimension (e.g., color precision or item count) caused failures, if any.>
- **全量抽样审计明细表**

| 抽样图片路径 (Image Path) | 所属条件 (Condition) | 形状 | 颜色 | 位置 | 尺寸比例 | 元素总数 | 遮挡/截断 | 最终结果 | 失败原因说明 (若 FAIL) |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| `output/cond1/trial_01.png` | `Target_Red_Left` | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** | - |
| `output/cond1/trial_02.png` | `Target_Red_Left` | PASS | FAIL | PASS | PASS | PASS | PASS | **FAIL** | 颜色为 `#FE0000`，不符合设计文档要求的 `#FF0000` |
| `<...循环列出所有被抽查的图片...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` |

### 3.2 M-02: 参数注册表参数保真度 (Parameter Registry Fidelity)
- **Process**: Established a "Dual-Verification Protocol" requiring absolute fidelity. The implementation was deemed an overall PASS only upon confirming that the code logic was rigorously correct and the visual output (files/sampled images) perfectly matched the design specifications.
- **Detailed Result**: 
  - Passed ：`<int>`
  - Total ：`<int>`
  - Score ：`<float>%`

- **逐项参数审计追溯表**

| Param Key | Type | Unit | Value/Range (预期) | 代码级核查结果 | 图像/文件级核查结果 | 验证依据 (抽样图片/文件路径) | 最终状态 | 失败原因 (若 FAIL) |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| `target_color` | string | RGB | `#FF0000` | PASS | PASS | `cond1/img_1.png`至`img_5.png` | **PASS** | - |
| `distractor_pos` | tuple | px | `Random (x,y)` | FAIL | FAIL | `cond2/img_1.png`至`img_5.png` | **FAIL** | 代码中未使用 random 库设定固定了坐标；抽样的 5 张图像中干扰物位置完全静止。 |
| `nback_trials` | int | count | `20+N` | PASS | PASS | `output/level_1/` 目录结构 | **PASS** | - |
| `<...列出所有参数...>` | `<...>` | `<...>`| `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` |

### 3.3 M-03: 条件视觉区分度 (multimodal-looker 盲测)
- **Process**: Performed a "Blind Test" using `multimodal-looker`. Images were stripped of labels and presented alongside the textual definitions of all conditions from `exp_design.md`. The model had to classify the image.
- **Detailed Result**: 
  - Classification Accuracy: `<float>%`
  - Confusion Matrix Notes: <e.g., "Condition A was often confused with Condition B due to low contrast".>
- **Analysis**: <Analyze if the experimental manipulations are visually distinct enough for a model to learn effectively. FAIL if Accuracy < 90%.>

- **盲分类全量抽测明细表与混淆分析**

| 抽样图片路径 (Blind Image Path) | 真实所属条件 (Ground Truth) | 审计 agent 预测条件 (Predicted) | 是否匹配 | 审计 agent 判决理由 (Rationale) |
|:---|:---|:---|:---|:---|
| `output/cond_A/img_08.png` | `High_Contrast` | `High_Contrast` | ✅ | 图像主体与背景对比度极高，符合高对比度条件特征。 |
| `output/cond_A/img_12.png` | `High_Contrast` | `Medium_Contrast` | ❌ | 背景颜色偏灰，主体亮度不够，视觉上更接近中等对比度定义的阈值。 |
| `<...循环列出所有盲测图片...>` | `<...>` | `<...>` | `<...>` | `<...>` |

### 3.4 M-04: 交互时序复杂度指数 (SIC)
- **Process**: Parsed the trial phases. Base 1.0 per phase. Added +2.0 for `Masking` and +3.0 for `Feedback/Branching`.
- **Detailed Result**: SIC Score = `<float>`.
- **Analysis**: < Conclusion on whether downstream fine-tuning requires single-image or multi-image sequence inputs based on the score.>

---

### 3.5 M-05: Trial跨阶段参数连续性 

- **Process**: Performed a **Trial-level continuity audit**. For each sampled Trial, the auditing agent loaded all corresponding phase images (e.g., **Stimulus Phase, Probe, Response, Feedback**) and matched them against the phase definitions and parameter mappings specified in `exp_design.md` (especially 5.x.3 Phase-by-Phase Stimulus Spec) and the original records in ./data.

The audit verified that parameters originating in the Stimulus Phase were correctly inherited by subsequent phases.

Each Trial was evaluated on four dimensions: **Target Traceability**,**Color Continuity**, **Orientation Continuity**, **Identity Binding Consistency**.

- **Decision Rule**: A Trial is marked `PASS` only if all four dimensions are `Pass`. If any dimension fails, the entire Trial is marked `FAIL`.
- **Detailed Result**:
  - Total Sampled Trials: <int>
  - Passed Trials: <int>
  - Trial Continuity Accuracy: <float>%

- **Analysis:**< Analyze whether failures were caused by parameter inheritance errors (e.g., probe color mismatch), broken identity binding (features taken from different stimuli), or incorrect phase parameter mapping. If failures exist, describe the most common error type and the phase where it occurred.>

- **全量抽样 Trial 连续性审计明细表**

| Trial ID | 涉及图片路径 (Phase Images) | 目标可追溯性 | 颜色连续性 | 方向连续性 | 身份绑定一致性 | 最终结果 | 失败原因说明 (若 FAIL) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `trial_01` | `cond1/trial01_stim.png`, `trial01_probe.png` | PASS | PASS | PASS | PASS | **PASS** | - |
| `trial_02` | `cond1/trial02_stim.png`, `trial02_response.png` | FAIL | FAIL | PASS | PASS | **FAIL** | Probe color `#0000FF` does not match any stimulus color in this trial |
| `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` | `<...>` |

---

## 4. Phase Interactions Timeline (Trial 内涉及的交互时序)

| Seq | Phase ID | Duration (ms) | Visual Content Summary | Required for Input? |
|:---|:---|:---|:---|:---|
| 1 | <e.g., Fixation> | <int> | <...> | <Yes/No> |
| 2 | <e.g., Stimulus> | <int> | <...> | <Yes/No> |

---

## 5. Model Fine-Tuning Input Schema (模型微调参数输入契约)

**Format Type**: `<Single-Image VQA / Multi-Image Sequence>`

```json
{
  "trial_metadata": {
    "condition": "<label>",
    "parameters": { "<var_1>": "<val_1>" }
  },
  "visual_inputs": [
    "<path_to_image_phase_n.jpg>"
  ],
  "user_instruction": "Based on the visual stimulus, determine the <target_property>. Response must be from: [<options>].",
  "expected_label": "<ground_truth>"
}
```

## 6. Anomalies & Action Items (异常与修复建议)

| Metric ID | Failing Target | Expected | Observed | Fix Suggestion |
|:---|:---|:---|:---|:---|
| M-01 | Condition <X> | Color #FF0000 | multimodal-looker detected #FE0000 | Adjust Renderer RGB values in script |
| M-03 | Randomization | SSIM < 0.99 | SSIM = 1.0 | Check seed implementation in render_trial |

---
