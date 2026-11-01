"""manimations —— 计算机图形学教学动画库。

三层结构：``theme``（视觉语言）→ ``components``（可复用元件）→ 成片脚本。
对外 API 只需要三个入口：

```python
from manimations import SlideScene, Slide3DScene, typography as T
from manimations.components import Card, Equation, Compare, Bullets, cg_axes
from manimations.theme import CORE, WARM, BAD, GOOD, INK, LAYOUT
```
"""

from . import theme, typography
from .scene import Slide3DScene, SlideScene

__all__ = ["SlideScene", "Slide3DScene", "theme", "typography"]
