# 数据字段 ↔ 实现参数映射（闭环要求）

## 1) Data Dictionary 的粒度要求

- 每列必须写：类型、取值集合/范围、语义、是否因实验而变
- 若同名列在不同实验含义不同：必须拆开写（Experiment-specific）

## 2) 映射闭环（两段式）

A. Data → Derived
| Data Field | Condition | Derived Var | Formula/Rule | Evidence |
|---|---|---|---|---|

B. Derived → Render
| Derived Var | Used Phase | stimkit target | Param Key | Evidence |
|---|---|---|---|---|

## 3) 参考实现的使用方式（实现优先级最高）

若 `<workspace>/data/` 中存在参考代码/配置：
- 把它们当成 **实现真值最高优先级**（E-C*, E-K*）
- 用来补齐 paper 未写清的实现细节（逻辑/超参数/枚举编码）
- 若与 paper 冲突：**以代码为准**并走 Conflict Log，写清楚“为何以代码为准”的依据

示例（说明这种“引用方式”为何必要）：
- 你的配置文件把 phase 列表显式写成 ["Memory","Cue","Search","Probe1","Probe2"]，这应进入 Parameter Registry，并引用其 config 证据。:contentReference[oaicite:3]{index=3}
- paper 明确描述了两个 probe display 及其 ISI/时限/按键，这属于实现关键事实，必须进 Fact Ledger。:contentReference[oaicite:4]{index=4}

## 4) 强制输出：随机化规则的“可实现形式”

随机化/约束必须写成：
- 变量名
- 取值空间
- 约束（例如“singleton_index ≠ target_index”）
- 采样单位（trial/block/subject）
- seed（若有）从哪里来

不要写成“随机分配”“均匀分布”等空话；必须可直接变成代码。
