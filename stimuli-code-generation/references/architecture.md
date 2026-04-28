# 渲染架构与职责边界（PsychoPy / headless）

## 目标
- 明确调度层、phase 渲染层、抓帧层的职责边界
- 避免 headless 导出黑图/空图
- 与 `SKILL.md` 保持一致：静态导出采用单一范式

## 架构总览（调度 vs 渲染 vs 抓帧）
```text
render_trial (调度层)
  ├─ 解析 trial 条件 / 随机状态
  ├─ for phase in phases:
  │    1) win.clearBuffer()               # 显式清缓冲
  │    2) render_phase_*()                # 只 draw，不 flip
  │    3) capture_frame()                 # 只 getMovieFrame(back)+save
  └─ 返回产物路径与审计信息
```

## 职责划分
- `render_trial`：
  - 只负责调度（phase 顺序、命名、I/O、状态复用）
  - 不在此处写具体刺激几何绘制
- `render_phase_*`：
  - 只负责绘制（`draw()`）
  - 禁止 `flip()`、禁止抓帧、禁止保存文件
- `capture_frame`：
  - 只负责抓帧和保存
  - 统一使用 `getMovieFrame(buffer="back")` + `saveMovieFrames(...)`
  - 禁止绘制刺激对象

## 强制导出范式（headless 默认）
- 每个 phase 必须执行：`clearBuffer()` -> `draw()` -> `getMovieFrame(buffer="back")` -> 保存 jpg
- phase 开始前必须显式清缓冲，不得依赖 `flip()` 充当清屏
- blank / delay / ITI 等空屏 phase 同样遵守，不得复用上一阶段残留帧

## 正例（推荐）
```python
def render_phase_memory(win, trial_state):
    # 仅绘制
    for stim in trial_state.memory_stims:
        stim.draw()

def capture_frame(win, output_path):
    # 仅抓帧与保存
    win.getMovieFrame(buffer="back")
    win.saveMovieFrames(str(output_path))

def render_trial(win, phases, trial_state, output_paths):
    for phase in phases:
        win.clearBuffer()
        render_phase_map[phase](win, trial_state)
        capture_frame(win, output_paths[phase])
```

## 反例（禁止）
```python
def render_phase_memory(win, trial_state):
    for stim in trial_state.memory_stims:
        stim.draw()
    win.flip()  # ❌ phase 内 flip

def capture_frame(win, output_path):
    win.getMovieFrame(buffer="back")  # ❌ 将抓到 flip 后空 back buffer 的高风险实现
```

## Reviewer 自检规则（必须）
- 若代码同时出现“phase 内 `flip()`”和“`getMovieFrame(buffer="back")` 抓帧”，直接判定为错误实现
- 若 `capture_frame` 包含绘制逻辑，判定为职责混淆，必须拆分后再交付
