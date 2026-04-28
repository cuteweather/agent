# CLI 与 limit 设计（stimuli-code-generation 运行约定）

## CLI 约束
- 必须支持 `--exp`、`--full`、`--max-trials`、`--workers`
- `--exp` 默认 `all`（运行所有实验）
- `--full` 必须忽略所有 limit
- `--workers` 默认值必须为 `1`（headless 稳定优先）
- 与 `SKILL.md` 对齐：不新增与核心流程无关的 CLI 参数

## 默认运行目标
- 默认运行应在 **1–2 分钟内**完成
- 默认仍需覆盖所有实验条件与阶段分支
- 通过 `render.max_trials` 实现“快速但有覆盖”

## limit 设计（分层可选）
当条件来自多层级（实验/任务/被试）时，允许定义分层 limit：
```toml
[render]
max_trials = 1

[render.limits]
max_subjects = 2
max_trials_per_subject = 5

[render.limits.by_task]
compare = 5
ignore = 3
remember = 4
```

### 规则
- 若启用 `render.limits`，必须在 `RenderConfig` 中显式建模（strict）
- `--full` 忽略所有 limit（包含 `render.max_trials` 与 `render.limits.*`）
- `--max-trials` 可覆盖 `render.max_trials` 的默认值

### 调整优先级
- 覆盖不足时优先提高 trial 级 limit（`max_trials` / `max_trials_per_subject`）
- 仅当条件来源分层时才调整上层 limit（如 `max_subjects` / `by_task`）

## 覆盖度分析（必须包含）
目标：在小样本 limit 下仍能**覆盖所有组别与关键条件**，并能判断“覆盖不足”的具体原因。

### 1) 明确覆盖维度（来自 exp_design.md）
必须先从 exp_design.md 抽取覆盖维度，例如：
- 实验维度：`ExperimentName`（如 Exp1A/Exp1B/Exp2A/Exp2B）
- 组别维度：`TaskType`（compare/ignore/remember）
- 刺激维度：`StimulusType`（color/shape）
- trial 条件维度：`trial.test` × `probe_index != None` 等

### 2) 组别识别（gallery/5 复杂案例）
当组别**混在同一实验文件夹**中（如 `Exp1A` 下既有 ignore 又有 compare），必须通过**文件名解析**识别组别：
`Exp1A/inter_color_ignore_data_03.mat` → task=ignore, stimulus=color

示例（与 gallery/5 结构一致）：
```python
def infer_task_type(file_name: str) -> TaskType:
    if "ignore" in file_name:
        return TaskType.IGNORE
    if "recog" in file_name:
        return TaskType.COMPARE
    if "recall" in file_name:
        return TaskType.REMEMBER
    raise ValueError(f"Unrecognized task type: {file_name}")

def infer_stimulus_type(file_name: str) -> StimulusType:
    if "color" in file_name:
        return StimulusType.COLOR
    if "shape" in file_name:
        return StimulusType.SHAPE
    raise ValueError(f"Unrecognized stimulus type: {file_name}")
```

### 3) 组别覆盖统计（文件级）
必须确认每个 `(experiment, task_type, stimulus_type)` 至少被采样到一个文件：
```python
from collections import Counter

group_counts = Counter()
for file_path in selected_files:
    file_name = file_path.stem
    experiment_name = file_path.parent.name
    task_type = infer_task_type(file_name=file_name)
    stimulus_type = infer_stimulus_type(file_name=file_name)
    group_counts.update(iterable=[(experiment_name, task_type, stimulus_type)])

# group_covered_count = number of unique group keys in group_counts
group_covered_count = ...
expected_group_count = ...
logger.log(level="INFO", message=f"group coverage {group_covered_count}/{expected_group_count}")
```

### 4) 条件覆盖统计（trial 级）
必须确认每个组内关键条件组合被覆盖（示例使用 trial.test × probe 是否存在）：
```python
condition_counts = Counter()
for trial in filtered_trials:
    condition_counts.update(iterable=[(trial.test, trial.probe_index is not None)])

# condition_covered_count = number of unique condition keys in condition_counts
condition_covered_count = ...
expected_condition_count = ...
logger.log(level="INFO", message=f"trial coverage {condition_covered_count}/{expected_condition_count}")
```

### 5) limit 选择策略（避免“只覆盖一个组别”）
当文件夹内混合多个组别时，**不能直接截断前 N 个文件**：
- 先按组别分桶：`(experiment, task_type, stimulus_type)` → list(files)
- 再按组别轮询采样，直到达到 `max_files_per_exp`

示意：
```python
def pick_files_round_robin(*, files_by_group: dict[tuple, list[Path]], max_files: int | None) -> list[Path]:
    if max_files is None:
        return [p for group in files_by_group.values() for p in group]
    selected: list[Path] = []
    selected_count = 0
    buckets = [[*v] for v in files_by_group.values()]
    while buckets and (max_files is None or selected_count < max_files):
        next_buckets: list[list[Path]] = []
        for bucket in buckets:
            if not bucket:
                continue
            selected = selected + [bucket[0]]
            selected_count = selected_count + 1
            if max_files is not None and selected_count >= max_files:
                break
            next_buckets = next_buckets + [bucket[1:]]
        buckets = next_buckets
    return selected
```

## CLI 示例
```bash
# 快速测试（默认）
xvfb-run -a -s "-screen 0 1280x1024x24" python script/reproduce_stimuli.py --exp E1 --max-trials 20

# 完整生成
xvfb-run -a -s "-screen 0 1280x1024x24" python script/reproduce_stimuli.py --exp all --full --workers 1
```
