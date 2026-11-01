"""要点列表：一页里的"三条结论"。

竖排、左对齐、行距一致，是教学视频里信息密度最高的元件。列表项的标记统一用
一个小圆点 + 可选的状态色，避免每页自己发明符号。
"""

from __future__ import annotations

from typing import Sequence

from manim import DOWN, LEFT, RIGHT, UP, Circle, VGroup

from .. import typography as T
from ..theme.palette import INK, INK_DIM

__all__ = ["Bullets"]


class Bullets(VGroup):
    """竖排要点列表。

    Examples
    --------
    ```python
    b = Bullets(
        ["只有 3 个自由度", "9 个数必须互相约束", "插值会离开合法集合"],
        marker_color=BAD,
        number=True,
    )
    ```

    Parameters
    ----------
    items
        每条要点；超过 24 字建议手动换行，或让 :meth:`fit` 统一缩放。
    marker_color
        标记点颜色；传 ``None`` 则使用默认弱化色。
    number
        为真时标记点改用序号（1、2、3…），更适合"步骤"。
    """

    def __init__(
        self,
        items: Sequence[str],
        *,
        marker_color: str | None = None,
        number: bool = False,
        text_color: str = INK,
        buff: float = 0.46,
        gap: float = 0.28,
    ) -> None:
        super().__init__()
        self.rows: list[VGroup] = []

        for i, text in enumerate(items, start=1):
            if number:
                marker: VGroup = VGroup(T.small(str(i), marker_color or INK, weight="BOLD"))
            else:
                dot = Circle(radius=0.055)
                dot.set_fill(marker_color or INK_DIM, opacity=0.85).set_stroke(width=0)
                marker = VGroup(dot)

            label = T.body(text, text_color)
            row = VGroup(marker, label)
            row.arrange(RIGHT, buff=gap, aligned_edge=UP)
            # 标记点与首行文字的视觉中线对齐（文字首行比整块矮）
            marker.set_y(label.get_top()[1] - T.HEIGHT_BODY * 0.62)
            self.rows.append(row)

        self.add(*self.rows)
        self.arrange(DOWN, buff=buff, aligned_edge=LEFT)

    def fit(self, max_width: float) -> "Bullets":
        """整列超宽时等比缩小（不换行），用于避免撑破安全区。"""
        if self.width > max_width:
            self.scale_to_fit_width(max_width)
        return self

    def with_checkmarks(self, good_color: str, bad_color: str) -> "Bullets":
        """把奇数/偶数标记改色，用于"对照"型列表。

        约定：第 1 条用绿（对的），第 2 条用红（错的），依次交替。
        """
        for i, row in enumerate(self.rows):
            row[0].set_color(good_color if i % 2 == 0 else bad_color)
        return self
