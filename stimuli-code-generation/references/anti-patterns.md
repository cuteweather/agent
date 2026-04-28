# 反模式清单（只列要点，细节见对应引用）

## ❌ 绕过 exp_design.md
- 未先补全 exp_design.md 就直接写实现
- 详见：`references/config-toml.md`、`references/data-loading.md`

## ❌ 忽略 `<workspace>/data/` 的源代码
- data 下存在参考实现却不优先采用其逻辑/超参数

## ❌ 调度层做渲染或单位转换
- `render_trial` 里做绘制/转换
- 详见：`references/architecture.md`、`references/unit-rules.md`

## ❌ phase 内 `flip()` + back buffer 抓帧
- 在 `render_phase_*` 内调用 `flip()`，同时在导出处使用 `getMovieFrame(buffer="back")`
- 该组合在 headless 下高概率产生黑图/空图，必须直接判错
- 详见：`references/architecture.md`

## ❌ 单位对象参与运算或布局
- 直接用 `VisualAngle/Pixel` 参与数学或布局计算
- 详见：`references/unit-rules.md`

## ❌ Thin wrapper
- 仅改名/改参顺序/转发调用的 helper
- 详见：`references/architecture.md`

## ❌ 依赖默认配置
- 未显式配置 `CanvasConfig` 必需字段
- 详见：`references/config-toml.md`

## ❌ 随机化未绑定 seed
- 使用随机数但未注入 `render.seed`
- 详见：`references/architecture.md`
