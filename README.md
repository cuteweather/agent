# Agent Skills Repository

[![Repo Check](https://github.com/cuteweather/agent/actions/workflows/repo-check.yml/badge.svg)](https://github.com/cuteweather/agent/actions/workflows/repo-check.yml)

这个目录现在被整理成一个可分发的 skills 集合仓库，包含 16 个独立 skill。每个 skill 保持自己的目录边界，根目录补充了仓库说明、机器可读索引和批量安装脚本，方便直接 clone、审阅和安装。

## 发布前状态

这个仓库已经补齐公开发布常见的基础配套：

- 根目录说明文档
- 机器可读 skills 索引
- 批量安装脚本
- 仓库校验脚本
- GitHub issue / PR 模板
- GitHub Actions 基础校验工作流

仍需仓库维护者自行决定的一项是许可证类型，因为这涉及明确的授权边界和法律后果。

## 目录约定

- 每个 skill 目录至少包含一个 `SKILL.md`
- 可选子目录：
  - `scripts/`
  - `references/`
  - `assets/`
- 根目录附带：
  - `skills.json`：机器可读的 skill 索引
  - `scripts/generate_skill_index.py`：重新生成索引
  - `scripts/install_skills.py`：将本仓库中的 skill 复制到目标 skills 目录

## Skill Catalog

### Utility

- `data-preview`: 预览文本与非纯文本数据，支持 pdf/xlsx/docx/pptx/mat/压缩包等场景。
- `function-shell-executor`: 通用函数壳执行器，按函数描述自主规划并落盘结构化结果。
- `image-generate`: 根据提示词调用文生图接口并保存图片到本地。
- `image-search`: 从 Pexels 检索并下载真实图片素材。

### Stimuli Pipeline

- `stimuli-action-executor`: 单个 workflow action 的统一执行包装器。
- `stimuli-code-generation`: 生成 scene composition、trial 调度与完整实验复现代码。
- `stimuli-code-review`: `run_review` 的两阶段人工审核门禁。
- `stimuli-dataset-evaluation`: 心理学刺激数据集的量化测评与微调价值分析。
- `stimuli-exp-design`: 从论文、插图、实验数据与参考代码中提取可执行设计规格。
- `stimuli-exp-design-review`: `run_exp_design` 与 `run_codegen` 之间的阻断式设计审核。
- `stimuli-grounding-segmentation`: 基于刺激描述对论文参考图做 grounding 与 segmentation。
- `stimuli-meta-orchestrator`: 顶层论文处理 meta orchestrator，只负责选择下一条 action。
- `stimuli-reproducibility-check`: 检查论文刺激是否满足复现条件。
- `stimuli-result-report`: 基于 manifest 和工作区状态刷新 `result_report.md`。
- `stimuli-unit-code-generation`: 生成 primitive 级别的 PsychoPy 绘制函数与 unit catalog。
- `stimuli-unit-function-review`: `run_unit_review` 的两阶段人工审核门禁。

## 安装

默认会安装到 `~/.codex/skills`。如果你想安装到别的目录，显式传 `--target` 即可。

Windows PowerShell:

```powershell
python .\scripts\install_skills.py
```

安装指定 skill：

```powershell
python .\scripts\install_skills.py image-search image-generate
```

安装到自定义目录并覆盖已有版本：

```powershell
python .\scripts\install_skills.py --target C:\path\to\skills --force
```

## 索引刷新

当你新增、删除或修改 skill frontmatter 后，运行：

```powershell
python .\scripts\generate_skill_index.py
```

脚本会重新生成根目录下的 `skills.json`。

## 仓库校验

发布前或提交前建议运行：

```powershell
python .\scripts\check_repo.py
```

它会检查：

- `SKILL.md` frontmatter 是否完整
- `skills.json` 是否过期
- 是否出现常见明文密钥模式

## 环境变量

部分脚本依赖外部 API，仓库中已去除明文密钥，运行前请设置：

- `PEXELS_API_KEY`
- `MINIMAX_API_KEY`
- 可选：`MINIMAX_API_URL`

## 说明

- 当前机器环境里没有可用的 `git` 命令，所以这次整理的是“标准仓库结构”，但没有实际执行 `git init`。
- 仓库中的示例与参考文件保留原有内容，仅修复了影响复用的路径、frontmatter 与安全问题。
- 如果你要公开发布到 GitHub，建议再补一个你明确选择的 `LICENSE` 文件。
