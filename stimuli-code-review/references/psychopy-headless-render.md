# PsychoPy Headless 最小可渲染示例

Review 时若需要先确认样本渲染链本身是否可用，优先用这个最小样例做基线判断。目标是验证：
- PsychoPy 能在 `xvfb-run` 下真实绘制；
- 保存逻辑确实落盘；
- 输出图片不是纯黑、纯白或单一像素值。

## 最小脚本

```python
#!/usr/bin/env python3
from pathlib import Path

from psychopy import core, visual
from psychopy.monitors import Monitor

output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

monitor = Monitor("testMonitor", width=52.0, distance=60.0)
monitor.setSizePix((1280, 1024))

win = visual.Window(
    size=(1280, 1024),
    units="deg",
    fullscr=False,
    allowGUI=False,
    monitor=monitor,
    color="gray",
)

stim = visual.TextStim(
    win=win,
    text="+",
    color="black",
    height=0.8,
    pos=(0, 0),
)
stim.draw()
win.getMovieFrame(buffer="back")
win.saveMovieFrames(str(output_dir / "sample_fixation.jpg"))

win.close()
core.quit()
```

## 运行命令

```bash
xvfb-run -a -s "-screen 0 1280x1024x24" python script/simple_render_test.py
```

## 最小像素检查

```bash
python - <<'PY'
from pathlib import Path

import numpy as np
from PIL import Image

path = Path("output/sample_fixation.jpg")
assert path.exists(), f"missing image: {path}"

img = np.array(Image.open(path))
unique_values = np.unique(img)

print("min=", int(img.min()))
print("max=", int(img.max()))
print("all_black=", bool((img == 0).all()))
print("all_white=", bool((img == 255).all()))
print("single_value=", bool(unique_values.size == 1))
PY
```

## Review 关注点
- 保存链路应为 `win.getMovieFrame(buffer="back")` + `win.saveMovieFrames(...)`。
- 若出现“文件存在但全黑”，先检查是否错误读了 `front buffer`。
- 若 workspace 脚本连这个最小样例都跑不通，再考虑环境问题。
