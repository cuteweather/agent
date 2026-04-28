---
name: image-generate
description: 根据提示词进行文生图并保存到本地，支持比例、尺寸、数量、seed、prompt 优化和风格参数。当用户提到“文生图/生成图片/image-01/image-01-live”时使用。
---

# 文生图

## 目标
- 根据文本提示词生成图片并保存到本地目录。
- 返回生成任务信息与本地文件路径。
- 默认使用独立脚本，不在对话里拼长请求体。

## API 配置
- Endpoint: 由脚本内 `API_URL` 定义
- Header: 由脚本内鉴权逻辑自动处理
- 默认模型：`image-01`

## 关键说明
- `response_format=url` 时，接口返回临时图片 URL，脚本会立即下载到本地。
- `response_format=base64` 时，脚本会直接解码并保存为本地 PNG。

## 参数约定
1. 必须传 `prompt`。
2. 常用参数：`model`、`aspect_ratio`、`n`、`seed`、`prompt_optimizer`。
3. 如果同时传 `width/height`，需要两个都提供。
4. `n` 取值范围为 `1-9`。
5. `image-01-live` 可配合 `style_type/style_weight` 使用。

## 输出约定
- 默认输出目录由调用方给定。
- 文件名默认使用 prompt slug，加三位序号。
- 可选 `--metadata-file` 保存完整返回信息。
- 默认只打印一条汇总 JSON；如需逐张打印，显式使用 `--print-each`。

## 工具脚本（独立文件）
- 仓库内脚本路径：`image-generate/scripts/text_to_image.py`
- 环境变量：`MINIMAX_API_KEY`
- 可选环境变量：`MINIMAX_API_URL`

```bash
SCRIPT="./image-generate/scripts/text_to_image.py"
[ -f "$SCRIPT" ] || { echo "text_to_image script not found"; exit 1; }
```

## 可执行示例

### 示例 1：基础文生图
```bash
SCRIPT="./image-generate/scripts/text_to_image.py"
python "$SCRIPT" \
  --prompt "a serene mountain landscape at sunrise, photorealistic" \
  --output-dir "./assets/t2i" \
  --aspect-ratio "16:9" \
  --n 1
```

### 示例 2：固定 seed，生成 4 张
```bash
SCRIPT="./image-generate/scripts/text_to_image.py"
python "$SCRIPT" \
  --prompt "a cozy reading room with warm lamp light, cinematic interior photography" \
  --output-dir "./assets/t2i" \
  --aspect-ratio "4:3" \
  --seed 42 \
  --n 4 \
  --metadata-file "./assets/t2i/reading_room.json"
```

### 示例 3：开启 prompt 优化
```bash
SCRIPT="./image-generate/scripts/text_to_image.py"
python "$SCRIPT" \
  --prompt "futuristic city street at night with neon reflections on wet pavement" \
  --output-dir "./assets/t2i" \
  --aspect-ratio "16:9" \
  --prompt-optimizer \
  --n 2
```

### 示例 4：`image-01-live` 风格化生成
```bash
SCRIPT="./image-generate/scripts/text_to_image.py"
python "$SCRIPT" \
  --prompt "a small wizard walking through an enchanted forest" \
  --output-dir "./assets/t2i" \
  --model "image-01-live" \
  --style-type "水彩" \
  --style-weight 0.8 \
  --n 1
```

## 执行策略（给模型）
- 需要真实生成图片时优先使用本技能，不要返回占位图或仅给伪代码。
- 先确认脚本存在，再执行。
- 若返回鉴权失败、余额不足或参数错误，直接把 `status_code/status_msg` 回报给用户。
- 若用户要求稳定复现，优先设置 `seed`。
