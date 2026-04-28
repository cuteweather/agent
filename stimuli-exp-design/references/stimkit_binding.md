# stimkit 绑定规范（输出如何写到“可实现”）

## 1) 表述原则

- 所有刺激描述必须能落到 stimkit 的 collections 下定义好的patch工厂函数/ matplotlib 内置的Patch
- 描述必须“可参数化”：能写成 config + trial data 驱动的渲染
- 不接受只靠自然语言的图形描述（例如“一个像吃豆人一样的形状”）；必须给几何定义（圆心、半径、缺口角度、旋转）

## 2) 坐标与角度（必须以 stimkit 为实现真值）

- 必须查证 stimkit 对：
  - angle=0 的朝向(是否与论文使用的默认方向不同)
  - 正角方向（CW/CCW）
  - (x, y) 的轴方向
  的定义来源，并写入 Global Conventions（Evidence 必须来自 stimkit 源码/文档条目）

若工作区拿不到 stimkit 的可引用定义：
- 将上述项记为 Missing，并禁止在 angle 相关内容上做推导（例如“45° left/right”映射到绝对角）。

## 3) Primitive Spec 最小字段（写在 exp_design.md 中时应具备）

每个 primitive 至少包含：
- kind: {circle, line, polygon, arc, text, group, ...}
- pos: (x_deg, y_deg)
- size: (w_deg, h_deg) 或 radius_deg
- stroke/fill: color (name 或 rgb)
- rotation_deg: (若适用)
- z_index / layering: (若遮挡或组合形状涉及顺序)

## 4) 组合刺激

- 复杂刺激（例如“二色半圆”、“闭合错觉矩形”等）必须拆成可实现的 primitive 列表，并给出：
  - 每个 primitive 的几何参数
  - 组合方式（相对位姿、对齐点、层级）
  - 哪些参数来自 data 字段，哪些来自全局常量
