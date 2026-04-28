# 单位与坐标规则（PsychoPy 对齐）

## 关键结论
- 单位体系必须单一且可追溯，不得在同一脚本中混用不兼容坐标逻辑
- 若窗口使用 `units="pix"`，屏幕中心必须是 `(0, 0)`
- phase 渲染与抓帧分离：`render_phase_*()` 仅绘制，`capture_frame()` 仅抓帧保存
- 与 `SKILL.md` 对齐：headless 静态导出默认 `clearBuffer -> draw -> getMovieFrame(buffer="back")`

## 单位转换规则
- 来自 `exp_design.md` 的视觉角度参数，进入绘制前需在统一位置转换为 PsychoPy 当前单位
- 线宽、尺寸、位置的转换必须一致，禁止同一参数多处重复换算
- 同一 trial 内随机结果复用时，复用转换后的值或统一来源值，禁止每个 phase 重新派生

## 命名约定（推荐）
- 角度单位：`*_deg`
- 像素单位：`*_pix`
- 时间单位：`*_ms`
- 归一化颜色：`*_rgb` 或 `*_rgb255`（二选一，全局一致）

## 正例（推荐）
```python
def render_phase_probe(win, phase_state):
    # 只绘制，不 flip
    for stim in phase_state.stims_pix:
        stim.draw()

def capture_frame(win, output_path):
    win.getMovieFrame(buffer="back")
    win.saveMovieFrames(str(output_path))
```

## 反例（禁止）
```python
# ❌ 同一脚本混用坐标语义（pix 中心坐标 + 左上角坐标）
x = width / 2
y = height / 2

# ❌ phase 内 flip + back buffer 抓帧
def render_phase_probe(win, phase_state):
    ...
    win.flip()
```
