"""主题层：配色、版式、成片基类。

对外只需要从这里 import：

```python
from manimations.theme import CORE, WARM, BAD, GOOD, LAYOUT, SlideScene, Slide3DScene
```
"""

from ..scene import Slide3DScene, SlideScene
from .palette import (
    AXIS_FRONT,
    AXIS_ISOMETRIC,
    BG,
    BG_ALT,
    BAD,
    COLORS,
    COOL,
    CORE,
    GOOD,
    INK,
    INK_DIM,
    INK_FAINT,
    LAYOUT,
    QUALITY_PRESETS,
    WARM,
    Layout,
    Palette,
)

__all__ = [
    "AXIS_FRONT",
    "AXIS_ISOMETRIC",
    "BG",
    "BG_ALT",
    "BAD",
    "COLORS",
    "COOL",
    "CORE",
    "GOOD",
    "INK",
    "INK_DIM",
    "INK_FAINT",
    "LAYOUT",
    "QUALITY_PRESETS",
    "WARM",
    "Layout",
    "Palette",
    "Slide3DScene",
    "SlideScene",
]
