# 模型与配置对齐（config.py + stimuli_config.toml）

## 核心目标
- `config.py` 与 `stimuli_config.toml` **一一对应**
- 参数来源仅来自 exp_design.md 的 Parameter Registry
- 所有字段显式配置，**不依赖默认值**
- 本文档受 `SKILL.md` 约束：静态导出主流程面向 PsychoPy + headless，图片格式统一为 `jpg`

## config.py 规则
- 所有模型继承 `StrictModel`（`extra="forbid"`）
- Enum 使用 `StrEnum` / `IntEnum`，禁止 magic number/string
- 视觉参数必须是 `VisualAngle` / `Pixel`（不是 raw float）
- `SceneConfig` 仅包含**调度最小字段**（`trial_data`、`phase`、`seed` 等），禁止几何数值

### 正例（模型）
```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Phase(StrEnum):
    MEMORY = "Memory"
    CUE = "Cue"

class Exp1Config(StrictModel):
    cue_radius: VisualAngle = Field(description="Cue ring radius")
    cue_line_width: VisualAngle = Field(description="Cue ring line width")

class Exp1TrialData(StrictModel):
    subject: int
    conditions: Exp1Condition

class SceneConfig(StrictModel):
    phase: Phase
    trial_data: Exp1TrialData
    seed: int
```

## stimuli_config.toml 规则
- `[canvas]` / `[render]` / `[expN]` 必选 section
- `[canvas]` 必须包含 `CanvasConfig` 全字段
- 颜色、尺寸、线宽等必须有明确单位与来源注释

### 正例（配置）
```toml
[canvas]
bg_color = "white"
screen_distance = 50.0
screen_size = 17.0
screen_resolution = [1024, 768]

[render]
seed = 42
output_format = "jpg"
phases = ["Memory", "Cue"]
max_trials = 0

[exp1]
cue_radius = 1.0
cue_line_width = 0.1
```

## 反例（禁止）
```python
# ❌ raw float + 默认值
class Exp1Config(StrictModel):
    cue_radius: float = 1.0
```

```toml
# ❌ 缺少 canvas 必需字段
[canvas]
screen_size = 17.0
```
