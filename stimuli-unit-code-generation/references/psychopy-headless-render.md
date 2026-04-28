# PsychoPy Headless 最小可渲染示例

用于实现或修复 `review` / `render-only` 出图路径时，先拿这个最小样例验证三件事：
- PsychoPy 能在 `xvfb-run` 下建窗并真实绘制；
- 脚本会把图片保存到指定目录；
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

## 使用要求
- 默认使用 `win.getMovieFrame(buffer="back")` + `win.saveMovieFrames(...)`。
- 不要在 headless 路径依赖 `win.getMovieFrame(buffer="front")`。
- 若最终实现偏离这条默认链路，必须在实现说明或 review 记录里写明原因。
