"""左右对照布局：视频里最常用的"这样是对的 / 这样是错的"。

固定规则：两张卡片等宽、等高、间距一致，上方各有一个着色小标题。
宽度由安全区反推，避免手调。
"""

from __future__ import annotations

from manim import DOWN, UP, VGroup

from .. import typography as T
from ..theme.palette import BAD, GOOD, INK, LAYOUT

__all__ = ["Compare"]


class Compare(VGroup):
    """左右两张卡片 + 标题。

    Examples
    --------
    ```python
    left = Card(title="直接插值矩阵")
    left.set_content(...)
    right = Card(title="经四元数插值")
    right.set_content(...)
    cmp = Compare(left, right, left_title="错误示范", right_title="正确做法")
    ```
    """

    def __init__(
        self,
        left: VGroup,
        right: VGroup,
        *,
        left_title: str = "",
        right_title: str = "",
        gap: float = 0.7,
        width: float | None = None,
        height: float = 2.9,
        left_color: str = BAD,
        right_color: str = GOOD,
    ) -> None:
        super().__init__()
        total_w = width if width is not None else LAYOUT.content_width
        card_w = (total_w - gap) / 2.0

        for card in (left, right):
            if hasattr(card, "resize"):
                card.resize(width=card_w, height=height)  # type: ignore[attr-defined]

        left.move_to([-total_w / 2 + card_w / 2, 0, 0])
        right.move_to([total_w / 2 - card_w / 2, 0, 0])

        headers = VGroup()
        if left_title:
            lt = T.small(left_title, left_color, weight="BOLD").move_to(
                [left.get_center()[0], 0, 0]
            )
            lt.next_to(left, UP, buff=0.26)
            headers.add(lt)
        if right_title:
            rt = T.small(right_title, right_color, weight="BOLD").move_to(
                [right.get_center()[0], 0, 0]
            )
            rt.next_to(right, UP, buff=0.26)
            headers.add(rt)

        self.left = left
        self.right = right
        self.add(headers, left, right)

    def place(self, center_y: float = 0.0) -> "Compare":
        """整体垂直居中到指定 y。``Compare`` 构造后高度不定，用这个统一对位。"""
        self.move_to([0, center_y, 0])
        return self
