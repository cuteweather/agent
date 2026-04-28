---
name: image-search
description: 按类别检索并下载真实图片素材（如风景图、城市图、人物图）。当需要使用真实图片素材时，使用此技能。
---

# Pexels 图片检索与下载

## 目标
- 按关键词从 Pexels 检索真实图片并下载到本地目录。
- 输出图片来源追溯信息：`id`、`photographer`、`url`。
- 严禁返回或使用任何 placeholder/dummy 图片链接。

## API 配置
- Base URL: `https://api.pexels.com/v1/search`
- 环境变量：`PEXELS_API_KEY`

## 检索规范
1. 必须传 `query`（如 `landscape`、`nature mountain`）。
2. 可选参数优先按需求设置：`--per-page`、`orientation`、`size`、`color`、`locale`。
3. `--per-page` 取值范围为 `1-80`，默认 `80`。
4. 脚本会自动翻页直到达到 `limit` 或无更多结果，不需要手工传 `page`。
5. 收到结果后，优先使用 `photos[].src.large2x`，若不存在再用 `photos[].src.original`。
6. 如果 `photos` 为空，直接返回“无可用真实图片”，并建议更换 query 或过滤参数。

## 禁止占位符规则（硬约束）
- 禁止输出或下载任何占位图链接，包括但不限于：
  - `placeholder`
  - `dummy image`
  - `via.placeholder.com`
  - `placehold.co`
- 当无结果时，只能返回失败原因与改进建议，不能自动替换为占位图。

## 输出约定
- 默认输出目录由调用方给定（例如 `./assets/pexels`）。
- 命名建议：`<query_slug>_<index>_<pexels_id>.jpg`
- 结果说明中包含：
  - 下载文件路径
  - Pexels `id`
  - `photographer`
  - 原始页面 `url`

## 工具脚本（独立文件）
- 仓库内脚本路径：`image-search/scripts/pexels_search_download.py`
- 作用：检索 + 过滤占位符链接 + 下载 + 输出来源信息（JSON 行）

```bash
SCRIPT="./image-search/scripts/pexels_search_download.py"
[ -f "$SCRIPT" ] || { echo "pexels_search_download.py not found"; exit 1; }
```

## 可执行示例（调用独立脚本）

### 示例 1：检索 landscape 并下载第一张
```bash
SCRIPT="./image-search/scripts/pexels_search_download.py"
python "$SCRIPT" \
  --query "landscape" \
  --output-dir "./assets/pexels" \
  --limit 1
```

### 示例 2：带过滤条件检索并下载（横图 + 大图）
```bash
SCRIPT="./image-search/scripts/pexels_search_download.py"
python "$SCRIPT" \
  --query "nature" \
  --output-dir "./assets/pexels" \
  --orientation landscape \
  --size large \
  --limit 1
```

### 示例 3：批量下载 5 张并按序号命名（去重）
```bash
SCRIPT="./image-search/scripts/pexels_search_download.py"
python "$SCRIPT" \
  --query "city skyline" \
  --output-dir "./assets/pexels" \
  --per-page 15 \
  --limit 5 \
  --metadata-file "./assets/pexels/city_skyline.metadata.jsonl"
```

### 示例 4：下载 100 张（自动翻页，默认只打印汇总）
```bash
SCRIPT="./image-search/scripts/pexels_search_download.py"
python "$SCRIPT" \
  --query "landscape" \
  --output-dir "./assets/pexels" \
  --per-page 15 \
  --limit 100 \
  --metadata-file "./assets/pexels/landscape.metadata.jsonl"
```

## 执行策略（给模型）
- 用户要求“找某类图片”时，优先执行本技能，不要返回示例 URL 或占位符。
- 失败时提供可执行修正建议（换 query、调 `orientation/size/color`、翻页）。
