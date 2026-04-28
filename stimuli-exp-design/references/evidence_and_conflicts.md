# 可核验引用与冲突处理规范

## A. 引用规则（强制）

1) 任何可影响复现实现的陈述都必须引用至少 1 个 Evidence ID。
2) 允许短引述，但必须短、可定位；正文不粘贴大段原文。
3) 每条事实只引用“支持它的最小证据集合”，避免堆砌。

推荐来源类型优先级（用于冲突时的默认裁决起点）：
1) reference code / config（**若 `<workspace>/data/` 提供源代码/参考实现：对实现逻辑与超参数，必须作为最高优先级真值**）
2) data README / 数据字典（字段语义与编码）
3) paper（方法与附录的明确文字）
4) figure（刺激几何/相对位置，尤其当 paper 文字含糊时）
5) derived（由前四者推导；必须写推导链）

> 注意：优先级是**实现真值的默认裁决顺序**。若存在源代码/参考实现，必须在 Conflict Log 中明确说明“以代码为准”的理由与影响范围。

## B. Evidence ID 命名约定

- E-P*：paper
- E-F*：figure / stimuli illustration
- E-D*：data docs / dataset schema
- E-C*：reference code
- E-K*：config (toml/yaml/json)

## C. 冲突处理（必须显式落表）

遇到不一致：
- 不允许“择一不写理由”
- 不允许“折中平均”
- 必须写 Conflict Log：冲突点、证据、决策、决策理由、对实现的影响面

典型冲突类型：
- 时序：paper 的 ms 与代码 hardcode 不同
- 几何：figure 看起来是 8 个位置但文字写 6
- 编码：data README 的列含义与 code 解析不一致

## D. 缺失项处理

- 任何缺失项必须进入 Missing Items
- 缺失项不得被“常识默认值”填充
- 若缺失阻断关键推导：停止相关推导，并在对应章节显式标注 “MISSING”
