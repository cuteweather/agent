# 数据加载规范（优先 stimkit.io）

## 核心规则
- 字段集合必须来自 exp_design.md 的 Data Dictionary
- **优先使用 `stimkit.io`**（`load_excel` / `load_mat_matrix`）
- 读取后立即清洗并转换为 Pydantic 模型
- 本文档仅约束数据读取层；渲染与导出流程以 `SKILL.md` 的 PsychoPy/headless 约束为准

## Excel（推荐）
```python
from stimkit import load_excel

def load_sheet_records(path: Path, sheet_name: str, columns: list[str]) -> list[dict[str, Any]]:
    df = load_excel(path=path, sheet=sheet_name)
    df = df[columns]
    df.columns = df.columns.map(func=str.strip)
    df = df.dropna(how="all")
    df = df.where(cond=df.notna(), other=None)
    return df.to_dict(orient="records")
```

## MATLAB .mat（推荐）
```python
from stimkit import load_mat_matrix

mat = load_mat_matrix(file_path=path, var_name="results")
```

## 类型验证
```python
exp1 = load_sheet_records(path=XLSX_PATH, sheet_name="E1", columns=[*Exp1TrialData.model_fields.keys()])
coerce_int_fields(records=exp1, fields=["subject", "conditions", "orientation", "consis"])
exp1_trials = [Exp1TrialData(**record) for record in exp1]
```

## 反例（禁止）
```python
# ❌ 绕过 exp_design 字段约束（未按字段表裁剪）
df = load_excel(path=path, sheet="E1")
# 直接使用 df（包含多余列）
```
