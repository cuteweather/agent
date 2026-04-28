---
name: data-preview
description: 当需要查看/预览各种数据尤其是非纯文本数据(pdf等)时使用此技能，可将任何非md格式转换为md格式。例如：txt,xlsx,docx,pptx,pdf,mat,zip,rar。
---


## 纯文本数据查看

请直接调用内置工具读取文本文件，注意请不要一次性全部读取占用上下文，请限制行数，例如先只读前20行。

## 非纯文本数据查看

#### pdf（默认使用 marker）

`pdf`默认使用`marker`，不要优先用`markitdown`。

`marker` 使用 OCR/Layout 模型，默认走 GPU（CUDA）推理；无 GPU 时可运行但速度会明显下降。

要求使用命令：
```bash
marker_single paper.pdf --output_format markdown --output_dir .
```

一定要带上output_dir参数，输出回paper目录，方便再次查看。

说明：
- `marker` 的 markdown 输出会包含图片引用，并将图片保存到输出目录。
- 如需仅文本可另行简化，但默认流程应保留图片。

#### xlsx,docx,pptx（使用 markitdown）

系统已经安装了`markitdown`命令行工具，用于预览xlsx,docx,pptx等数据，请务必将结果添加md后缀保存，方便以后再次阅读。
例如：
```bash
markitdown data.xlsx -o data.xlsx.md
```
转换后，使用文件读取工具查看`data.xlsx.md`。

## 压缩包

**禁止**使用markitdown直接处理zip等压缩文件，这回导致缓慢的处理速度。任何压缩包请解压缩后处理。

## mat

系统已经安装了`mat_preview`命令行工具，用于预览mat文件（该工具及其生成结果仅用于可复现性检验阶段），生成的结果是有截断的。
例如：
```bash
mat_preview ./data.mat --max-entries 10 --sample-k 20 -o ./data.mat.preview.json
```
