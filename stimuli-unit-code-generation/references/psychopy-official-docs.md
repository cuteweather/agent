# PsychoPy 官方文档索引与核对说明

## 目标
- 为 `stimuli-code-generation` 提供 PsychoPy API 的官方事实来源。
- 降低凭记忆猜类名、参数、默认值、颜色空间或单位语义的风险。
- 本文件解决“官方 API 是什么”；具体在本项目里“应该怎么用”，仍以 `SKILL.md`、`references/architecture.md`、`references/psychopy-stimuli-pattern.md` 为准。

## 使用规则
- 只要代码里新增或修改了 `psychopy.visual.*`、`psychopy.monitors.*`、`visual.Window` 的参数或方法，就必须先核对对应官方页。
- 当前工作区基线是 `PsychoPy 2025.1.1`，但公开官方文档主页可能显示 `2025.2.x` 或 `2026.x`；因此官方文档用于确认 **API 名称、构造参数、默认行为、颜色/单位定义**，不能把“最新文档里出现的新能力”自动当作 `2025.1.1` 可用。
- 若 reference 已锁定图元选型或导出范式，官方文档只用于核对 API 写法，不得借此改写既定策略。
- 若官方默认行为与本项目 headless 规范冲突，必须显式覆写并遵守本项目规范：
  - `Window.getMovieFrame()` 官方默认是 `buffer='front'`；本项目静态导出必须显式写 `buffer="back"`。
  - `Window.saveMovieFrames()` 官方支持多种图片/视频格式；本项目统一输出 `jpg`。
  - `Window.units` 只是窗口默认单位，且只影响**新创建**的 stimulus；不要指望后改 `win.units` 会回溯修改已创建对象。
  - 使用 `units="deg"` 或 `units="cm"` 时，必须同步提供 `Monitor` 标定信息，而不是只写 `units`。

## 官方入口
- 最新 API 总索引：<https://docs.psychopy.org/api/index.html>
- 较接近当前基线的官方 API 总索引（`2025.1.0` devdocs，可用于版本漂移比对）：<https://devdocs.psychopy.org/api/index.html>
- visual 模块索引：<https://docs.psychopy.org/api/visual/index.html>
- 单位说明：<https://docs.psychopy.org/general/units.html>
- 颜色 API：<https://docs.psychopy.org/api/color.html>
- Monitor API：<https://docs.psychopy.org/api/monitors.html>

## code-gen 常用页面
- `visual.Window`：<https://docs.psychopy.org/api/visual/window.html>
  - 核对 `allowGUI`、`monitor`、`units`、`getMovieFrame()`、`saveMovieFrames()`。
  - 官方文档明确：`getMovieFrame(buffer='front')` 是默认值，通常在 `flip()` 后抓前缓冲；本项目 headless 导出不能沿用这条默认路径。
  - 官方文档明确：`units` 是窗口默认单位，但单个 stimulus 初始化时可覆盖；已创建 stimulus 不会因后改 `win.units` 自动更新。
- `psychopy.monitors.Monitor`：<https://docs.psychopy.org/api/monitors.html>
  - 核对 `Monitor(name, width, distance)`、`setSizePix()`。
  - `deg` / `cm` 不是“只改个字符串”的单位切换，依赖 monitor 宽度、像素尺寸、观看距离。
- 单位说明：<https://docs.psychopy.org/general/units.html>
  - 官方文档明确：所有单位下屏幕中心都是 `(0, 0)`。
  - 因此若脚本使用 `units="pix"`，禁止把 `(width/2, height/2)` 当成 PsychoPy 绘制中心。
- 颜色 API：<https://docs.psychopy.org/api/color.html>
  - 官方文档明确 `rgb`、`rgb1`、`rgb255` 是不同值域；不要混用。
  - 结合 visual stimulus 文档可知：切换 `colorSpace` 不会自动重算已有颜色值，所以必须先固定 `colorSpace`，再设置 `color` / `fillColor` / `lineColor`。

## 常用图元页面
- `visual.Circle`：<https://psychopy.org/api/visual/circle.html>
  - 用于完整圆语义。
  - 官方文档明确：若 `radius != 0.5`，不要再用 `size` 做主几何缩放，否则会有未定义行为。
- `visual.Pie`：<https://psychopy.org/api/visual/pie.html>
  - 用于缺口圆盘、Pac-Man、楔形。
  - 官方文档明确：`start` / `end` 是以度为单位的填充区域角度，并按 counter-clockwise 方向定义。
  - 官方文档同样提示：若 `radius != 0.5`，不要再依赖 `size` 做主几何缩放。
- `visual.ShapeStim`：<https://docs.psychopy.org/api/visual/shapestim.html>
  - 只在 `Circle` / `Pie` 无法表达的自定义几何里使用。
  - 官方文档明确：它支持 concave / self-crossing / multi-loop 形状，但 multi-loop 情况下 `border` / `contains()` 不可直接依赖。
- `visual.Line`：<https://docs.psychopy.org/api/visual/line.html>
  - 用于 fixation cross、指示线、简单 feedback 线段。
  - 优先用 `start` / `end` 表达线段，不要把简单直线退化成自定义 `ShapeStim`。
- `visual.ImageStim`：<https://docs.psychopy.org/api/visual/imagestim.html>
  - 仅在刺激本体就是图片资产或纹理贴图时使用。
  - 官方文档明确：`image` 可以是路径或图像数据；若只是几何刺激，不要用外部位图绕过本应可参数化的图元。
- `visual.GratingStim`：<https://docs.psychopy.org/api/visual/gratingstim.html>
  - 适合“纹理 + mask”范式，例如连续色环的 Numpy RGB 纹理配合环形 alpha mask。
  - 官方文档明确：`GratingStim` 的核心是 texture 加透明 mask；若从磁盘读纹理，理想尺寸是方形且接近 2 的幂。
- 其他 visual 类：从 visual 模块索引继续跳转核对，不要直接猜页面或猜 API：<https://docs.psychopy.org/api/visual/index.html>

## 与本项目规范的衔接说明
- 官方文档若出现 deprecated 别名（如 `RGB`、`fillRGB`、`lineColorSpace` 等），生成代码时优先使用当前 API（`color`、`colorSpace`、`fillColor`、`lineColor`）。
- 官方文档允许 `autoDraw`、`flip()` 等实时显示范式，但本项目的静态导出主流程仍锁定为 `clearBuffer()` -> `draw()` -> `getMovieFrame(buffer="back")` -> `saveMovieFrames()`。
- 若官方页没有明确证明某类、某参数或某默认行为存在，就不要在 code-gen 阶段臆造调用；先退回更简单、已核实的实现路径。
