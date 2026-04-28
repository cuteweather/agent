---
name: stimuli-grounding-segmentation
description: 基于刺激描述，对论文参考图执行grounding & segmentation。 产出 grounding_index.json、mask、overlay 与 example crop；当分割失败时保留 no_match 记录并自动回退到 figure_and_text 或 text_only。
---

# 刺激 grounding segmentation（SAM3.1）

## 目标

- 对 `stimulus_family` 级别的参考图做 grounding，而不是对整篇论文做自由式图像理解。
- 使用 `facebook/sam3.1` 对参考图中的目标刺激做开放词汇分割。
- 固定产出：
  - `paper/grounding/grounding_index.json`
  - `paper/grounding/masks/*.png`
  - `paper/grounding/overlays/*.png`
  - `paper/grounding/examples/*.png`

## 硬约束

- segmentation prompt 必须来自刺激家族描述：至少基于 `description` 与 `must_preserve` 生成。
- 一条 `stimulus_family` 记录只能对应一种参考粒度：要么是单一刺激示意图，要么是布局图；禁止在同一条记录里混写单 item 几何与多 item layout。
- 若论文同时给出单一刺激示意图和布局图，必须拆成多条记录分别 grounding。
- 禁止直接用图注、figure title、文件名、locator 文本替代 prompt。
- `match_status=no_match` 只表示未找到可靠示例，不是 gate fail。
- 有参考图但没分到时，`effective_reference_basis` 必须回退到 `figure_and_text`。
- 没有参考图时，`effective_reference_basis` 必须是 `text_only`。
- grounding crop 永远是补充参考，不能拿 crop 子集替代条件空间。
- 单一刺激检查阶段必须优先覆盖 paper 中所有出现过的单一刺激示意图；布局图应作为独立记录保留，供后续组合/code generation 阶段参考。
- 推荐用 `reference_role=primary_example` 标记单一刺激示意图，用 `reference_role=layout_reference` 标记布局图。
- 有参考图的 family 在首轮 `no_match` 后不得直接结束；必须继续做 prompt 改写与 threshold sweep，而不是只尝试一次就判失败。
- 对有参考图的 family，只有在 `--retry-sweep` 模式 + 多次 `fallback_prompts` 均穷尽后仍无任何 mask 时，才允许把该 family 最终记为失败。
- **`--retry-sweep` 是强制标志**：凡是 workspace 中存在参考图，执行 `segment_with_sam31.py` 时必须带 `--retry-sweep`；不带此标志运行等同于违反技能硬约束。
- 若单一刺激粒度始终未命中，但 scene / panel / layout 粒度能命中，则必须至少保留 1 条 scene 级别记录并产出对应 overlay/example；把该条记录标成 `reference_role=layout_reference` 。
- scene 级别产物只能作为补充参考，不能掩盖单一刺激粒度失败这一事实；若 object-level 仍失败，仍需保留对应 `no_match` 记录。

## 输入

- 机器输入文件建议为 `paper/grounding/grounding_requests.json`。
- 请求格式与输出索引格式见：
  - `references/grounding_contract.md`
- 环境与安装要求见：
  - `references/runtime_setup.md`

## 执行顺序

1. 优先使用当前运行环境里已准备好的本地 SAM3 仓库与 checkpoint。
2. 通过 Docker image 预装好的独立运行时执行，不在 launch 时下载 `torch` 或模型。
3. 用 `scripts/check_sam31_env.py` 检查 Python / torch / CUDA / repo / checkpoint。
4. 用 `scripts/verify_sam31_setup.py` 做一次 model load + 单图前向 smoke test。
5. 用 `scripts/segment_with_sam31.py` 生成 grounding 产物。
6. 只有当本地 repo / ckpt 缺失时，才回退到 `clone_sam3_repo.sh` 与 `download_sam31_checkpoint.sh`。

## 脚本路径

```bash
SKILL_ROOT="./stimuli-grounding-segmentation"
SEGMENT_SCRIPT="${SKILL_ROOT}/scripts/segment_with_sam31.py"
CHECK_SCRIPT="${SKILL_ROOT}/scripts/check_sam31_env.py"
VERIFY_SCRIPT="${SKILL_ROOT}/scripts/verify_sam31_setup.py"
```

- 若要验证当前仓库里的最新修改，优先使用上面的 repo-local 路径。
- 安装副本可能落后于当前仓库源码，调试时优先直接运行仓库内脚本。

## 典型命令

```bash
sam3-python "$CHECK_SCRIPT" \
  --repo-dir /path/to/sam3 \
  --checkpoint /path/to/sam3/ckpt/sam3.1_multiplex.pt \
  --device cuda
```

```bash
sam3-python "$VERIFY_SCRIPT" \
  --repo-dir /path/to/sam3 \
  --checkpoint /path/to/sam3/ckpt/sam3.1_multiplex.pt \
  --device cuda \
  --output-dir ./tmp/sam31_verify
```

```bash
sam3-python "$SEGMENT_SCRIPT" \
  --requests-file ./workspace/paper/grounding/grounding_requests.json \
  --output-root ./workspace/paper/grounding \
  --repo-dir /path/to/sam3 \
  --checkpoint /path/to/sam3/ckpt/sam3.1_multiplex.pt \
  --device cuda \
  --retry-sweep
```

## 内置 Example

- 仓库内置了一个可直接运行的 example：
  - `./stimuli-grounding-segmentation/references/examples/demo_workspace`
- example 内包含：
  - `paper/_page_1_Figure_2.jpeg`
  - `paper/grounding/grounding_requests.json`
  - `paper/grounding/` 下的 masks / overlays / examples 产物目录

一键运行 example：

```bash
cd ./stimuli-grounding-segmentation/references/examples
bash run_example.sh demo_workspace
```

只跑 grounding：

```bash
sam3-python "$SEGMENT_SCRIPT" \
  --requests-file ./stimuli-grounding-segmentation/references/examples/demo_workspace/paper/grounding/grounding_requests.json \
  --output-root ./stimuli-grounding-segmentation/references/examples/demo_workspace/paper/grounding \
  --repo-dir /path/to/sam3 \
  --checkpoint /path/to/sam3/ckpt/sam3.1_multiplex.pt \
  --device cuda \
  --max-masks-per-family 3 \
  --retry-sweep
```

verify 的关键产物：
- `./stimuli-grounding-segmentation/references/examples/demo_workspace/tmp/sam31_verify/verify_top1_crop.png`
- `./stimuli-grounding-segmentation/references/examples/demo_workspace/tmp/sam31_verify/verify_summary.json`

- `verify_top1_crop.png` 直接裁出最高分 box，便于快速判断模型到底选中了什么。
- smoke test 只用于验证运行时与基本检测路径，不替代最终的 grounding 结果审查。

## 重试协议

- 若首轮运行后 `match_status=no_match`、`searched_regions=[]`，或没有任何 `masks/overlays/examples` 产物，不得直接结束；必须进入重试流程。
- **必须在 `grounding_requests.json` 的每条有参考图 family 中写入 `fallback_prompts` 字段**（字符串数组）。`fallback_prompts` 至少应包含：
  - 1 条 外观/几何变体 prompt：例如 `"black filled teardrop with rounded head and pointed tail"`
  - 1 条 scene / panel / layout 粒度 prompt：例如 `"experiment panel showing fixation, sample, delay and report boxes"`
- `--retry-sweep` 标志会自动完成以下流程（不需要手动多次调用脚本）：
  1. 以 `confidence_threshold=0.0` 创建处理器（保证模型返回所有候选）
  2. 用原始 prompt 对 `score_threshold` 做 `0.2 → 0.1 → 0.05 → 0.01 → 0.0` 递减 sweep
  3. 若原始 prompt 全部 sweep 失败，逐条尝试 `fallback_prompts`，每条都做完整 threshold sweep
  4. 将所有尝试记录写入 `grounding_index.json` 的 `retry_attempts` 字段
- 只要 `--retry-sweep` 运行完仍然 `no_match`，agent 仍须手动补充更多 `fallback_prompts` 并重跑，直到满足下述最低产出要求。
- 允许先生成一个临时探索文件，例如 `paper/grounding/grounding_requests_prompts.json`，对同一张参考图写入多条 prompt 变体进行探测；确认哪个 prompt 有效后，再回写正式 `grounding_requests.json`。
- prompt 重试至少应覆盖：
  - 外观/几何短语：例如 `black filled teardrop with rounded head and pointed tail`。
  - 场景/面板短语：例如 `experiment panel with fixation, sample, delay, report boxes`；当 object-level 一直失败时，必须至少尝试 1 条 scene-level prompt。
- threshold sweep 应按递减顺序继续尝试，直到 0 为止；推荐顺序：
  - `--score-threshold` sweep（`--retry-sweep` 自动完成）: `0.2 -> 0.1 -> 0.05 -> 0.01 -> 0.0`
  - `--confidence-threshold`：`--retry-sweep` 已固定为 `0.0`，无需手动降低
- 只要 `--retry-sweep` 还没有跑过，就不能把有参考图的 family 最终判为失败。
- `--retry-sweep` 运行后仍然 `no_match` 的 family，`retry_attempts` 字段会记录所有尝试；review gate 据此判断重试是否充分。
- 一旦某组 prompt + threshold 组合开始产出 mask，应立即检查 `masks/`、`overlays/`、`examples/`；如果 scene-level 有结果而 object-level 没结果，也必须至少保留 1 个 scene 级别示意图作为补充参考。
- 当重试流程结束时，最终产物至少应满足二者之一：
  - 成功保留 1 个或更多 object-level mask；
  - 若 object-level 始终失败，则至少保留 1 个 scene-level / panel-level 的 overlay/example 作为示意图。

### 阈值含义

- `--confidence-threshold` 是 SAM3 内部的第一道筛选阈值。它传给 `Sam3Processor(...)`，用于过滤模型刚输出的候选区域；低于该阈值的候选会在 SAM3 内部直接被丢掉，后续连 `scores`、`boxes`、`masks` 都不会返回。
- `--score-threshold` 是本技能脚本外加的第二道筛选阈值。它作用在 `segment_with_sam31.py` 的 `select_candidates(...)` 里，只过滤已经从 SAM3 返回出来的候选，决定哪些候选最终会被保存成 `mask/overlay/example`。
- 两者看的分数来源是同一套 `output["scores"]`，但生效阶段不同：
  - `confidence-threshold` 控制“候选能不能从模型里出来”；
  - `score-threshold` 控制“出来的候选要不要被保留下来”。
- 排查顺序必须按下面执行：
  - 若 `searched_regions=[]`，或 SAM3 根本没有返回任何候选，先降低 `--confidence-threshold`。
  - 若 `searched_regions` 已经非空，但 `mask_paths=[]`、`overlay_paths=[]`，或最终还是 `no_mask_above_threshold`，优先降低 `--score-threshold`。
  - 若候选很多且混入无关 panel、折线图、文字或大面积背景，优先提高 `--score-threshold`；如果连候选集合本身都过于泛滥，再提高 `--confidence-threshold`。
- 因此，“阈值降到 0 才算失败”不是只降一个阈值，而是要把这两层阈值都逐步降到 `0.0`，并完成 prompt 重试后，仍然没有任何可用 mask，才允许最终判失败。

## 最低产出要求（有参考图时）

- **硬性规则**：只要 exp_design 阶段认定 paper 中存在参考图（`reference_priority=figure_then_text`），grounding 就 **必须** 产出至少 1 张图片产物（mask / overlay / example），不允许以空产物结束。
- 若 object-level prompt 穷尽仍失败，必须使用 scene / panel / layout 粒度 prompt 来兜底：
  - 用 `fallback_prompts` 中的 scene-level prompt 运行 `--retry-sweep`
  - 保留至少 1 条 `reference_role=layout_reference` 的记录并产出对应产物
- 只有在以下条件 **全部** 满足时，才允许把某 family 最终记为 `no_match`：
  1. 已使用 `--retry-sweep` 运行（`retry_attempts` 非空）
  2. `fallback_prompts` 至少包含 1 条 scene-level prompt
  3. 所有 `retry_attempts` 的 `candidates_found` 均为 0
- 若 object-level 全部失败但 scene-level 成功，在 grounding_index.json 中必须同时保留：
  - object-level 的 `no_match` 记录（含完整 `retry_attempts`）
  - scene-level 的 `matched` 记录（`reference_role=layout_reference`）

## 结果检查

- **磁盘产物自动合并**：`segment_with_sam31.py` 在写入 `grounding_index.json` 前会自动执行两步：
  1. **Merge**：读取已有 `grounding_index.json`，保留不在本次 requests 中的旧 family 记录（不会丢失旧运行结果）。
  2. **Disk reconciliation**：对仍然 `no_match` 的 family，扫描 `masks/`、`overlays/`、`examples/` 目录中以该 `grounding_id` 为前缀的文件。若发现磁盘上有历史产物，自动升级为 `matched` / `crop_and_text`，并在记录中标记 `_disk_reconciled: true`。
- 因此，多次运行使用不同 prompt / grounding_id 后缀（如 `_v1`、`_v2`、`_scene`）不会互相覆盖：旧文件保留在目录中，新运行的 index 会自动发现并引用它们。
- 若 `mask_count=0`、`match_status=no_match`，或 `verify_summary.json` 里没有可靠输出，先检查 `description` 与 `must_preserve` 是否真的在描述当前这条记录的目标粒度。
- 没有 mask 时，优先逐步调低 threshold：先降低 `--confidence-threshold`，必要时再降低 `--score-threshold`；必须一直试到 `0.0`，而不是停在中间阈值。
- 没有 mask 时，也要考虑更换 prompt 来源：直接修改 `grounding_requests.json` 中的 `description` 与 `must_preserve`，把目标写得更具体，并显式排除非目标元素（如 axis、line plot、labels、caption、response dial）。
- 若 object-level prompt 一直失败，必须追加至少 1 条 scene / panel / layout 粒度的 prompt，确保有机会产出一个 scene 级别示意图。
- 只有在 prompt 重试已经覆盖 object-level 与 scene-level，且 `--confidence-threshold=0.0` 与 `--score-threshold=0.0` 仍然没有任何 mask 时，才允许最终保留 `no_match`，并按契约回退到 `figure_and_text` 或 `text_only`。
- 若产出的 mask 很多，不能默认全收；必须检查 `masks/`、`overlays/`、`examples/`，确认每个产物都是当前任务真正需要的目标。多余产物删除。
- 若 mask 很多且混入了折线图、坐标轴、文字标签、无关 panel 或大面积背景，应提高 threshold、收紧 prompt，或减小 `--max-masks-per-family`。
- `--max-masks-per-family` 只是数量控制，不等于质量控制；即使数量已经被限制，也仍然要确认保留下来的每个产物都必要且正确。

## 调用策略

- `stimuli-exp-design` 在已经抽出 `stimulus_family`、`must_preserve`、`allowed_variation` 且存在参考图时，应调用本技能。
- 若请求记录缺 `description` / `must_preserve` / `figure_locator` 等关键字段，本技能仍应保留记录，但要把问题写入 `no_match_reason`，供后续 design review 判定。
