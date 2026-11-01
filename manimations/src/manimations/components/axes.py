"""坐标系：所有几何内容的"舞台"。

两个关键决定：

* **3D 只画到 ±3**。Manim 的透视相机让 3D 内容看起来只有画面的一小半，
  配合 :class:`~manimations.scene.Slide3DScene` 的近距离焦距，
  ±3 的范围刚好撑满正文区，画到 ±6 反而会被裁掉。
* **轴标签用屏幕图层（fixed-in-frame）**，不参与 3D 旋转。这是教学视频的通行做法：
  几何体可以转，但"X / Y / Z"必须永远正对观众，否则一转就认不出来了。
"""

from __future__ import annotations

from manim import (
    BLUE,
    DOWN,
    GREEN,
    LEFT,
    RED,
    RIGHT,
    Axes,
    NumberPlane,
    RoundedRectangle,
    ThreeDAxes,
    VGroup,
)

from .. import typography as T
from ..theme.palette import INK_FAINT

__all__ = ["cg_axes", "plane2d", "axis_legend", "AXIS_COLORS"]

# 坐标轴配色约定：X 红、Y 绿、Z 蓝——和绝大多数建模软件一致，形成肌肉记忆
AXIS_COLORS: dict[str, str] = {"x": RED, "y": GREEN, "z": BLUE}


def cg_axes(
    *,
    x_range: tuple[float, float] = (-3.0, 3.0),
    y_range: tuple[float, float] = (-3.0, 3.0),
    z_range: tuple[float, float] = (-3.0, 3.0),
    color: str = INK_FAINT,
    include_numbers: bool = False,
) -> ThreeDAxes:
    """3D 坐标系。刻度线短、描边细、末端带箭头，够用而不喧宾夺主。

    ``include_numbers=False`` 是刻意的：教学视频里数字太密会挡住几何体，
    需要数值时用 :func:`axis_legend` 或旁白点名即可。
    """
    return ThreeDAxes(
        x_range=[*x_range, 1],
        y_range=[*y_range, 1],
        z_range=[*z_range, 1],
        axis_config={
            "include_tip": True,
            "tip_width": 0.22,
            "tip_height": 0.22,
            "stroke_color": color,
            "stroke_width": 2.4,
            "include_numbers": include_numbers,
            "font_size": 24,
        },
    )


def plane2d(
    *,
    x_range: tuple[float, float] = (-7.0, 7.0, 1.0),
    y_range: tuple[float, float] = (-4.0, 4.0, 1.0),
    background_line_style: dict | None = None,
) -> tuple[NumberPlane, Axes]:
    """2D 网格 + 坐标轴。返回 ``(网格, 轴)``，网格故意画得很淡。

    网格只是"暗示这是一张纸"，真正承载几何的是放在上面的向量与点。
    """
    plane = NumberPlane(
        x_range=x_range,
        y_range=y_range,
        background_line_style={
            "stroke_color": INK_FAINT,
            "stroke_width": 1.0,
            "stroke_opacity": 0.16,
        },
        axis_config={
            "stroke_color": INK_FAINT,
            "stroke_width": 2.0,
            "include_tip": True,
            "tip_width": 0.16,
            "tip_height": 0.16,
        },
    )
    axes = plane.get_axes()
    return plane, axes


def axis_legend(*, size: float = 0.30) -> VGroup:
    """X/Y/Z 颜色图例，放在角落替代会乱飘的 3D 轴标签。

    一圈彩色小方块 + 字母，比在 3D 里贴 3D 文字稳定得多。
    """
    rows = VGroup()
    for name, col in AXIS_COLORS.items():
        chip = RoundedRectangle(width=size * 0.6, height=size * 0.6, corner_radius=0.04)
        chip.set_fill(col, opacity=0.9).set_stroke(width=0)
        label = T.small(name.upper(), col, weight="BOLD")
        row = VGroup(chip, label)
        row.arrange(RIGHT, buff=0.14)
        rows.add(row)
    rows.arrange(DOWN, buff=0.18, aligned_edge=LEFT)
    return rows
