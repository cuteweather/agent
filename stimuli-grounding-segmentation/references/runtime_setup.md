# Runtime Setup

## 上游要求
- `facebookresearch/sam3` README 当前写明的安装前提是：
  - Python `3.12+`
  - PyTorch `2.7+`
  - CUDA `12.6+`
- README 同时给出示例安装命令：
  - `pip install torch==2.10.0 torchvision --index-url https://download.pytorch.org/whl/cu128`
  - `pip install -e .`

## 本仓库当前状态
- `Dockerfile` 已提供：
  - Python 3.12 基础镜像
  - `git` / `git-lfs`
  - 编译工具链
  - Mesa / EGL / OSMesa / Xvfb
- 当前根项目依赖里没有预装：
  - `torch`
  - `torchvision`
  - `sam3`
  - `timm`
  - `ftfy`
  - `iopath`
  - `huggingface_hub`
  - `modelscope`

## 建议安装策略
- 不要把 SAM3.1 直接并进当前根项目的 `pyproject.toml`。
- 建议在 Docker 内单独建一个 venv，例如 `/workspace/.venv-sam3`。
- 优先直接使用当前环境里已经准备好的本地 SAM3 repo 与 checkpoint。
- 不要在 launch 执行阶段再次下载 `torch`、`modelscope` 或 checkpoint。
- Docker image 内的 `sam3-python` 包装器默认位于：
  - `/home/developer/.local/bin/sam3-python`
- 使用本技能的脚本：
  - `scripts/clone_sam3_repo.sh`
  - `scripts/download_sam31_checkpoint.sh`
  - `scripts/install_sam31_runtime.sh`
  - `scripts/check_sam31_env.py`
  - `scripts/verify_sam31_setup.py`

## 推荐执行顺序（当前仓库已含本地 repo/ckpt 时）
```bash
SKILL_ROOT="./stimuli-grounding-segmentation"

sam3-python "${SKILL_ROOT}/scripts/check_sam31_env.py" \
  --repo-dir /path/to/sam3 \
  --checkpoint /path/to/sam3/ckpt/sam3.1_multiplex.pt \
  --device cuda
```

## 通用回退路径（仅当本地 repo / ckpt 缺失时）
- 若本地 repo 或 checkpoint 缺失，再使用 clone / download 脚本补齐。
- 该回退路径不应作为当前仓库的默认执行路径。

## 关于 checkpoint 适配
- 本技能默认 checkpoint 名称为 `sam3.1_multiplex.pt`。
- `segment_with_sam31.py` 通过 `build_sam3_image_model(checkpoint_path=..., load_from_HF=False)` 加载本地 checkpoint。
- 这里依赖的是上游 `sam3/model_builder.py` 的 checkpoint remap 逻辑：脚本层只取 detector 权重来构造 image grounding 路径。
- 这是基于源码行为的适配，不改变 skill 契约名称 `facebook/sam3.1`。
