---
name: stimuli-reproducibility-check
description: 验证一个心理学论文的实验中使用的刺激是否可复现。在开始处理一个心理学论文原始刺激的代码复现工作时，使用这个技能来检验论文是否满足复现要求。
---

# 心理学论文实验用刺激可复现性检验

## Overview

阅读工作区中的论文原文(<workspace>/paper/...)和使用脚本检验提供的实验数据(<workspace>/data/...)来判断论文是否可以复现。

## Workflow
### 论文检查
1. 论文类型检查：仅实验型论文可以复现，综述等无实验论文无法复现
2. 刺激类型要求：仅包含**静态图像**或**文本刺激**，任何其他类型的刺激例如视频/音频/电刺激等均无法复现

### 数据检查
1. 没有提供数据的论文无法复现
2. 没有Trial级数据，仅提供统计结果的论文无法复现
3. 没有提供关键假设锁涉及数据的论文无法复现。例如：论文探究前后刺激的颜色是否改变对工作记忆的影响，如果没有记录前后颜色或者前后颜色是否改变的数据，该论文在复现中无法还原关键假设，故而无法复现。
4. 提供了关键数据，但是细节缺失的论文**可以复现**。例如：对于3中提到的工作，如果提供了前后颜色是否改变的bool数据，虽然无法精确还原原始刺激，但是可以通过随机抽取颜色来复现类似的刺激，同时满足关键数据成立，这种可以复现。
5. 如果原始刺激缺失，必须继续判断是否可通过以下方式完成：
   - 使用工作区中已有公开素材
   - 从公开可下载图片源补齐素材
   - 使用文生图生成替代刺激
6. 只有在以下情况成立时，才判定论文无法复现：
   - 缺少关键 trial 级或条件映射数据，导致刺激无法与实验条件逐 trial 对齐
   - 关键实验操纵依赖于原始刺激的特定属性，而替代刺激无法保留这些属性
   - 论文指定了第三方数据集、版权图片、联网素材，但这些素材既不在 `<workspace>/data/...` 中，也无法用公开下载或文生图方式构造出满足关键操纵的替代刺激
7. 如果原始素材缺失，但关键行为语义仍能通过替代刺激保留，则应判定为“可复现（替代刺激）”，而不是“不可复现”。
8. 若论文提到“公开数据集 / publicly available dataset / external image library”，但 `<workspace>/data/`、`<workspace>/paper/` 或已解包目录中没有实际可用的图片素材、素材清单或下载记录，**不能**把这件事视为“素材已就绪”；此时只能判定为“可复现但待补素材”。

### 素材替代判断规则
1. 先判断论文的关键假设到底依赖什么：
   - 是依赖具体某张原图本身
   - 还是依赖可抽象的语义/视觉属性，例如类别、情绪价、朝向、复杂度、场景类型、位置关系等
2. 如果关键假设只依赖这些可抽象属性，而不依赖特定原图身份，则允许替代刺激。
3. 对图片类刺激，优先使用以下素材策略：
   - `workspace_existing`：工作区已有素材
   - `public_download`：公开可下载图片或公开数据集
   - `image_generation`：文生图
   - `mixed`：混合方案
4. 若使用 `public_download` 或 `image_generation`，必须能输出至少下列追溯信息：
   - 每张图的来源类型
   - 与实验条件的映射关系
5. `public_dataset` 只是来源类型，不代表素材已经在工作区中可用。必须实际检查：
   - 是否已有图片文件；
   - 是否已有包含图片的压缩包且可明确解包使用；
   - 是否已有 `download_manifest` / `assets_manifest` / `source_trace` 一类记录。
6. 若以上检查均不满足，必须把该素材家族标记为 `resolved=false`，后续进入素材准备分支；禁止直接给出“无 blocker 的 full reproduction”。

### 短路策略

检查应该由易到难，一旦有不符合立即退出。但对“缺图片素材”不能过早短路。

推荐顺序：
1. 先看 `data/` 是否为空、是否只有空压缩包
2. 再看论文是否为实验型、刺激类型是否受支持
3. 再看是否有 trial 级数据、关键假设数据
4. 若问题只剩“原始图片/素材缺失”，必须继续判断是否能进入替代刺激分支
5. 只有确认替代刺激也无法保留关键操纵时，才判不可复现

## 结构化输出要求（强制）

- `decision.reproducibility_path` 只能使用：
  - `full_reproduction`
  - `substitute_reproduction`
  - `irreproducible`
- 只有在以下条件同时满足时，才能返回 `full_reproduction`：
  - 所有关键刺激都能仅靠文本 / 数学参数精确生成，或
  - 所有外部视觉素材已经在工作区中真实存在并可直接用于后续代码生成。
- 若论文依赖对象图片、面孔库、场景照片、公开图像数据集、第三方图片库等外部视觉素材，而这些素材当前不在工作区中，则必须返回：
  - `reproducible = true`
  - `reproducibility_path = "substitute_reproduction"`
  - `blocking_issues` 中包含素材准备相关项
  - `asset_requirements`，逐项列出待补素材家族
- `asset_requirements` 每项至少包含：
  - `stimulus_family`
  - `source_kind`
  - `required`
  - `resolved`
  - `asset_strategy`
  - `fallback_strategy`
  - `must_preserve`
  - `required_outputs`
- 若外部视觉素材未就绪，`blocking_issues` 不能为空。

## Markdown 文件输出要求（强制）

- 必须在工作区根目录生成或刷新：`<workspace>/repro_check.md`
- 该文件不能为空，且至少包含以下小节（标题可同义）：
  - 复现性结论（Reproducible / Irreproducible）
  - 复现路径（`full_reproduction` / `substitute_reproduction` / `irreproducible`）
  - 关键证据（论文与数据证据）
  - 阻断项与风险（若有）
  - 素材需求与替代策略（若有外部视觉素材）
  - 建议下一步动作（供后续 orchestration 使用）
- 结构化结论与 `repro_check.md` 的结论必须一致，不允许互相冲突。

## 附录
使用 `data-preview` 技能来进行论文提供数据的快速预览。
