"""3D 几何专用的补丁式动画。"""

from __future__ import annotations

from typing import Any

import numpy as np
from manim import Animation, Arrow3D

__all__ = ["GrowArrow3D"]


class GrowArrow3D(Animation):
    """3D 箭头的"生长"动画（从起点长到终点）。

    Manim 自带的 ``GrowArrow`` 内部会调 ``arrow.scale(..., scale_tips=True)``，
    而 ``Arrow3D`` 继承自 ``Line3D``、``scale`` 没有这个参数，直接用它渲染会抛
    ``TypeError: VMobject.scale() got an unexpected keyword argument 'scale_tips'``。
    这里改为让终点从起点插值出去，视觉等价，且不依赖 2D 专用逻辑。
    """

    def __init__(self, arrow: Arrow3D, **kwargs: Any) -> None:
        super().__init__(arrow, **kwargs)
        self._arrow: Arrow3D = arrow
        self._start = np.array(arrow.get_start(), dtype=np.float64)
        self._end = np.array(arrow.get_end(), dtype=np.float64)

    def interpolate(self, alpha: float) -> None:
        self._arrow.put_start_and_end_on(
            self._start, self._start + alpha * (self._end - self._start)
        )
