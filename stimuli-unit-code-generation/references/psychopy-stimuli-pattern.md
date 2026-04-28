# PsychoPy 图元与渲染模式参考（2025.1.1）

## 目标
- 为 `reproduce_stimuli.py` 提供 PsychoPy 图元选型与渲染模式参考
- 减少错误 API、错误图元映射、错误导出范式导致的低保真复现
- 与 `SKILL.md` 保持一致：优先保证实验语义保真、参数可追溯、headless 导出稳定

## 使用边界
- `SKILL.md` 是最高原则；若本文件与 `SKILL.md`、`exp_design.md`、`data/` 证据冲突，以上游为准
- 本文件只约束 PsychoPy 图元选择与渲染模式，不替代 `exp_design.md`、`trial_conditions.json` 或参数追溯链路
- 缺失参数时，可以阻断精确实现；不得因此改变刺激类别或偷换成示意图
- 本文件不是 PsychoPy 教程；不要把示例规则扩展成未经证据支持的 paper-specific 推断

## 版本与 API 约束
- 目标版本固定为 `PsychoPy 2025.1.1`
- 仅使用已确认存在且适合稳定导出的基础图元与 API
- 具体官方入口与常用 API 页面见 `references/psychopy-official-docs.md`
- 禁止猜测式调用 PsychoPy 类、属性或方法
- 禁止把“新版本可能支持”的行为当作 2025.1.1 的事实
- 每次新增或修改 PsychoPy API 调用时，都要先核对官方文档中的类名、参数名、默认值，再回到本 reference 决定项目内实现策略
- 若官方默认行为与本项目导出规范冲突，必须显式覆写后再使用；典型例子是 `getMovieFrame(buffer="back")`，不能沿用官方默认的 `front`
- 若某实现路径兼容性不明确，优先选择更简单、更稳定的等价方案

## 图元选型
- 连续色环（color wheel / hue wheel）渲染方式锁定：
  - 若 `exp_design.md` / 论文 / 数据证据要求的是“颜色沿圆周连续变化”的真实色环，则必须使用 **预计算的 Numpy RGB 纹理 + 环形 alpha mask** 进行渲染，优先实现为单个 `visual.GratingStim(tex=<rgb_array>, mask=<ring_alpha_mask>)`；禁止用 `visual.RadialStim`、若干 `Pie` 扇区、离散 `ShapeStim` 色块或截图贴图来近似连续色环。
  - 色相必须按极角连续映射，环宽、外半径、内半径、起始角与旋转量应作为可追溯参数一次生成并跨 phase 复用；不得把连续色环退化为少量扇区、棋盘径向纹理、双色/多色交替纹理或单色 outline。
  - `tex` 必须为连续极角映射得到的 `H×W×3` 浮点 RGB 数组，且数值范围必须与 `colorSpace` 一致（明确为 `[-1,1]` 或 `[0,1]`，不可混用）。
  - `mask` 必须为环形 alpha / luminance mask，内外区域取值须符合 PsychoPy 对 `GratingStim` 的要求（例如环内 `1`、环外 `-1`），不得使用会导致半透明或平铺伪影的错误范围。
  - 最终渲染结果必须是**单个连续色环**；不得在包围方形区域内出现纹理平铺、棋盘格、三角重复、径向/切向重复或非环形背景着色。
- 圆形类刺激渲染方式锁定：
  - 若上游设计语义是**完整圆形**（如圆盘、圆形轮廓、probe outline、marker、placeholder），必须直接使用 `visual.Circle`；
  - 若上游设计语义是**圆形减去扇形/楔形缺口**（如 Pac-Man、Kanizsa 诱导子、缺口圆盘），必须优先使用 `visual.Pie`，通过 `radius`、`start`、`end` 明确表达缺口几何；禁止用 `visual.ShapeStim` 通过若干圆周顶点近似实现。
  - 仅当 `exp_design.md` 或数据证据明确表明目标轮廓为 `Circle` / `Pie` 都无法表达的**非标准自定义几何**时，才允许使用 `visual.ShapeStim` 自定义顶点。
  - 禁止为了“统一写法”或“方便旋转”而把本可由 `visual.Circle` / `visual.Pie` 直接表达的圆形类刺激降级为多边形近似。
- `visual.Window`：
  - 作为唯一渲染根，统一 `units`、`colorSpace`、背景与抓帧语义
- `visual.ShapeStim`：
  - 用于自定义顶点几何、多边形、非标准轮廓
  - 不要用单个单色 `ShapeStim` 伪造本应由多个颜色段组成的复合刺激
- `visual.Line`：
  - 用于 fixation cross、minus feedback、pointer、简单指示线
- `visual.RadialStim`：
  - 仅用于真正的径向纹理或径向图样
  - 不要把所有 color wheel 默认实现成 `RadialStim`
- `visual.ImageStim`：
  - 仅当刺激本来就是图片、纹理，或上游证据明确依赖真实图像资产时使用
  - 不要用图片贴图掩盖本应由几何图元直接表达的刺激逻辑

## 渲染与导出约束
- 一份脚本只能有一套明确的导出范式；与 `references/architecture.md` 保持一致
- headless 默认流程必须是：`clearBuffer()` -> `render_phase_*()` 仅 `draw()` -> `capture_frame()` 使用 `getMovieFrame(buffer="back")` -> 保存 `jpg`
- `render_phase_*()` 只负责绘制当前 phase，不得在内部 `flip()`、抓帧、保存文件或重新随机
- `capture_frame()` 只负责抓帧与保存，不得包含刺激绘制逻辑
- blank / delay / ITI 等空屏 phase 也必须显式清缓冲，禁止复用上一阶段残留帧
- 当 back-buffer 抓帧作为主流程时，phase 内出现 `flip()` 直接视为错误实现
- 本项目中的 PsychoPy 脚本首先是刺激导出器，其次才是交互式实验脚本；两者冲突时优先满足 xvfb/headless 稳定导出

## Trial 状态复用
- 所有跨 phase 生效的随机结果必须在 trial 开始时一次生成，并在后续 phase 复用
- 典型复用项包括：位置、颜色分配、朝向分配、grouping 结构、probe index、probe 真值、feedback 目标、color wheel 旋转
- 禁止在 `render_phase_*()` 内重新 `shuffle`、重新抽 probe、重新推导正确答案
- 禁止原地修改共享配置对象，避免污染后续 trial

## 颜色与坐标
- 同一脚本必须统一颜色约定：要么全局 `rgb255`，要么全局 PsychoPy `rgb`
- 必须先固定 `colorSpace`，再设置 `color` / `fillColor` / `lineColor`；不要先写颜色、后切换颜色空间
- 背景、填充、描边必须使用同一套 `colorSpace` 与转换逻辑，禁止隐式混用 `rgb255`、`rgb`、`0~1` 浮点色值
- 若窗口使用 `units="pix"`，则 `(0, 0)` 必须是屏幕中心；禁止把 `(width/2, height/2)` 当作绘制中心
- 不要依赖运行中修改 `win.units` 去影响已经创建好的 stimulus；若单位不同，必须在创建对象时明确声明
- 同一实验中的圆周布局、probe 位置映射、orientation 参考系必须跨 phase 保持一致
- 若设计文件要求连续色轮，必须保留“颜色沿圆周连续变化”的刺激类别；不得退化为少量色块、单色环或 outline 占位环

## 常见反模式
- 绕过 `exp_design.md` 或 `data/`，仅凭视觉印象猜刺激结构
- 用 placeholder 代替论文要求的真实 probe/stimulus
- 用单个单色图元伪造多颜色复合刺激
- phase 内 `flip()`，同时又使用 `getMovieFrame(buffer="back")`
- 同一脚本混用中心坐标、左上角坐标、不同颜色标度
- 因缺少少量参数就把连续刺激、真实刺激降级成示意图
- 使用未经确认兼容 `2025.1.1` 的 PsychoPy API

## 生成前自检
- 我是否依据 `exp_design.md` 和 `data/` 先确认了刺激类别，而不是先挑图元？
- 我选择的 PsychoPy 图元，是否表达了论文要求的真实刺激语义？
- 我使用的 API，是否可在 `2025.1.1` 中稳定工作？
- 渲染与导出逻辑，是否严格遵守单一 headless 范式？
- trial 内跨 phase 的随机状态，是否只生成一次并全程复用？
- 若存在缺失参数，我是否阻断了精确实现，而不是偷偷降级刺激类别？
