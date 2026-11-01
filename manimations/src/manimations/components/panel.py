"""卡片、公式面板：正文里最常出现的"承装容器"。

设计原则：**内容自己决定大小，容器最后包住它**——先排内容，再画框，
不做手工猜宽高。这样换文案、换字号都不会撑破版式。
"""

from __future__ import annotations

from typing import Sequence

from manim import DOWN, LEFT, UP, MathTex, RoundedRectangle, VGroup

from .. import typography as T
from ..theme.palette import BG_ALT, INK_DIM, INK_FAINT, WARM

__all__ = ["Card", "Equation", "fit_card", "formula_panel"]


def fit_card(
    content: VGroup,
    *,
    color: str = INK_FAINT,
    fill: str = BG_ALT,
    fill_opacity: float = 0.55,
    stroke_width: float = 1.2,
    padding: float = 0.34,
    corner_radius: float = 0.16,
) -> VGroup:
    """给一组内容包一个圆角卡片，返回 ``VGroup(框, 内容)``。

    卡片用极低透明度的填充 + 细描边：既划分区域，又不抢内容。
    """
    box = RoundedRectangle(
        width=content.width + 2 * padding,
        height=content.height + 2 * padding,
        corner_radius=corner_radius,
    )
    box.set_fill(fill, opacity=fill_opacity).set_stroke(color, width=stroke_width, opacity=0.55)
    box.move_to(content)
    return VGroup(box, content)


class Card(VGroup):
    """带可选标题的卡片。

    固定宽高时（``width/height`` 给定）适合做左右对比布局；
    不给宽高则退化为"按内容自适应"，之后再 :meth:`resize` 统一尺寸。
    """

    def __init__(
        self,
        *,
        title: str | None = None,
        color: str = INK_FAINT,
        width: float | None = None,
        height: float | None = None,
        fill: str = BG_ALT,
        title_color: str = INK_DIM,
        **kwargs,
    ) -> None:
        super().__init__()
        self._box = RoundedRectangle(
            width=width or 4.0,
            height=height or 2.0,
            corner_radius=0.16,
        )
        self._box.set_fill(fill, opacity=0.55).set_stroke(color, width=1.2, opacity=0.55)
        self.add(self._box)

        self._title: VGroup | None = None
        if title:
            label = T.small(title, title_color, weight="MEDIUM")
            self._title = VGroup(label)
            self._title.next_to(self._box.get_top(), DOWN, buff=0.24)
            self.add(self._title)

        self._content: VGroup | None = None

    def set_content(self, content: VGroup, *, buff: float = 0.32) -> "Card":
        """把内容放进卡片，并在放不下时自动缩到安全宽度。"""
        self._content = content
        if self._title is not None:
            content.next_to(self._title, DOWN, buff=buff)
        else:
            content.move_to(self._box.get_center())
        max_w = self._box.width - 2 * buff
        if content.width > max_w:
            content.scale_to_fit_width(max_w)
        self.add(content)
        return self

    def resize(self, *, width: float | None = None, height: float | None = None) -> "Card":
        """调整卡片外框，内容保持居中。用于把一组卡片统一成同一尺寸。"""
        if width is not None:
            self._box.width = width
        if height is not None:
            self._box.height = height
        self._box.move_to(self._box.get_center())
        if self._title is not None:
            self._title.next_to(self._box.get_top(), DOWN, buff=0.24)
        if self._content is not None:
            if self._title is not None:
                self._content.next_to(self._title, DOWN, buff=0.32)
            else:
                self._content.move_to(self._box.get_center())
        return self


class Equation(VGroup):
    """公式块：主公式（LaTeX）+ 可选的中文注释。

    注释用 Pango 排版的 ``Text`` 而不是塞进 LaTeX 的 ``\\text{}``：
    中文由系统字体排版更好看，也避免 MiKTeX 缺字体时整个公式渲染失败。
    """

    def __init__(
        self,
        tex: str,
        *,
        color: str = WARM,
        note: str | None = None,
        buff: float = 0.30,
        height: float = T.HEIGHT_EQ,
    ) -> None:
        super().__init__()
        self.formula = MathTex(tex, color=color)
        if self.formula.height > 0:
            self.formula.scale_to_fit_height(height)
        self.add(self.formula)
        self.note_mob = None
        if note:
            self.note_mob = T.small(note, INK_DIM)
            self.note_mob.next_to(self.formula, DOWN, buff=buff)
            self.add(self.note_mob)


def formula_panel(
    equations: Sequence[str | Equation],
    *,
    title: str | None = None,
    width: float | None = None,
    color: str = WARM,
    fill_opacity: float = 0.5,
    buff: float = 0.5,
) -> VGroup:
    """一列公式 + 卡片组成的面板，适合放在正文一侧做"理论区"。

    Parameters
    ----------
    equations
        字符串按 LaTeX 直接渲染；也可传已构造好的 :class:`Equation`。
    width
        给定时会把整块缩放到该宽度，用于配合左右分栏。
    """
    items: list[Equation] = []
    for e in equations:
        items.append(e if isinstance(e, Equation) else Equation(e, color=color))
    col = VGroup(*items).arrange(DOWN, buff=buff, aligned_edge=LEFT)

    if title:
        head = T.small(title, INK_DIM, weight="MEDIUM")
        head.next_to(col, UP, buff=0.32, aligned_edge=LEFT)
        group = VGroup(head, col)
    else:
        group = VGroup(col)

    card = fit_card(group, fill_opacity=fill_opacity)
    if width is not None and card.width > width:
        card.scale_to_fit_width(width)
    return card
