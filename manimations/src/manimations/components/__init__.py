"""可复用元件。

| 元件 | 用途 |
| --- | --- |
| :class:`~manimations.components.panel.Card` | 带标题的卡片容器 |
| :class:`~manimations.components.panel.Equation` | 公式 + 中文注释 |
| :func:`~manimations.components.panel.formula_panel` | 一列公式组成的理论区面板 |
| :class:`~manimations.components.bullets.Bullets` | 竖排要点列表 |
| :func:`~manimations.components.axes.cg_axes` | 3D 坐标系 |
| :func:`~manimations.components.axes.plane2d` | 2D 网格 + 坐标轴 |
| :class:`~manimations.components.compare.Compare` | 左右对照布局 |
"""

from .animate3d import GrowArrow3D
from .axes import AXIS_COLORS, axis_legend, cg_axes, plane2d
from .bullets import Bullets
from .compare import Compare
from .panel import Card, Equation, fit_card, formula_panel

__all__ = [
    "AXIS_COLORS",
    "axis_legend",
    "cg_axes",
    "plane2d",
    "Bullets",
    "Compare",
    "Card",
    "Equation",
    "fit_card",
    "formula_panel",
    "GrowArrow3D",
]
