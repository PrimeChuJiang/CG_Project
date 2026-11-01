"""文字工厂：所有文字都从这里产出，保证字号 / 字重 / 字体一致。

为什么要有这一层？因为同一个项目里混用了两种文字系统：

* 中文正文 → :class:`~manim.scene.scene.Text`（Pango 排版，走系统字体）
* 数学公式 → ``MathTex``（LaTeX + dvisvgm 排版，走 MiKTeX）

两者字号体系完全不同（前者按像素，后者按 ``\\small``/``\\normalsize`` 比例），
混排时必须统一到同一个"视觉高度"，否则公式会突然比正文大一截。
本模块用 ``HEIGHT_*`` 常量按实测高度对齐，改字号只需要改一处。
"""

from __future__ import annotations

from typing import Iterable

from manim import DOWN, RIGHT, Text, VGroup

from .theme.palette import BAD, CORE, GOOD, INK, INK_DIM, INK_FAINT, WARM

# 字体栈：优先 Noto Sans SC（几何感强、投影友好），缺失时退回 Windows 自带雅黑
CJK_FONT = "Noto Sans SC"
CJK_FALLBACK = "Microsoft YaHei"
MONO_FONT = "Cascadia Mono"

# 视觉高度（Manim 坐标单位）。16:9 画幅高 8.4，正文单行约 0.42 视觉上最舒服。
HEIGHT_TITLE = 0.60
HEIGHT_EYEBROW = 0.26
HEIGHT_BODY = 0.42
HEIGHT_CAPTION = 0.34
HEIGHT_SMALL = 0.28
HEIGHT_EQ = 0.58  # 公式面板里的主公式


def _text(
    content: str,
    height: float,
    color: str = INK,
    *,
    font: str = CJK_FONT,
    weight: str = "NORMAL",
    line_spacing: float = 0.45,
    t2c: dict[str, str] | None = None,
) -> Text:
    """内部构造器：按"视觉高度"而不是"字号"指定大小。

    ``Text(font_size=…)`` 的像素含义会随 Pango 字体度量变化，跨字体不稳定；
    统一用 ``height`` 缩放能让不同字体、不同语言的行高看起来一致。
    """
    t = Text(
        content,
        font=font,
        weight=weight,
        color=color,
        font_size=48,
        line_spacing=line_spacing,
        should_center=True,
        t2c=t2c,
    )
    if t.height > 0:
        t.scale_to_fit_height(height)
    return t


# --------------------------------------------------------------------------
# 正文类
# --------------------------------------------------------------------------
def heading(content: str, color: str = INK) -> Text:
    """页面主标题，一页只允许一个。"""
    return _text(content, HEIGHT_TITLE, color, weight="BOLD")


def eyebrow(content: str, color: str = INK_DIM) -> Text:
    """主标题上方的小字：章 / 节 / 议题编号，英文大写或中文短词均可。"""
    return _text(content, HEIGHT_EYEBROW, color, weight="MEDIUM")


def body(content: str, color: str = INK) -> Text:
    """正文段落，支持 ``\\n`` 手动换行。"""
    return _text(content, HEIGHT_BODY, color)


def caption(
    content: str,
    color: str = INK_DIM,
    *,
    t2c: dict[str, str] | None = None,
) -> Text:
    """旁白字幕，只出现在画面底部带。``t2c`` 用于按子串着色强调。"""
    return _text(content, HEIGHT_CAPTION, color, t2c=t2c)


def small(content: str, color: str = INK_DIM, *, weight: str = "NORMAL") -> Text:
    """脚注、坐标标签、单位说明等次要信息。"""
    return _text(content, HEIGHT_SMALL, color, weight=weight)


def code(content: str, color: str = WARM) -> Text:
    """等宽代码片段，用来把画面和 ``code/`` 里的函数名对应起来。"""
    return _text(content, HEIGHT_SMALL, color, font=MONO_FONT)


def key_number(content: str, color: str = WARM) -> Text:
    """被强调的数字（误差值、维度、次数）。"""
    return _text(content, 0.72, color, weight="BOLD")


def label(content: str, color: str = INK) -> Text:
    """图形旁的短标签（轴名、点名、向量名）。"""
    return _text(content, 0.30, color)


# --------------------------------------------------------------------------
# 混排
# --------------------------------------------------------------------------
def join(parts: Iterable, buff: float = 0.16) -> VGroup:
    """把若干已排好的文字横向并排，用于"中文 + 代码 + 中文"这类混排。

    不要用 ``Text`` 直接拼中英文和公式——排版系统不同，拼出来基线会跳。
    """
    g = VGroup(*parts)
    g.arrange(RIGHT, buff=buff, aligned_edge=DOWN)
    return g


__all__ = [
    "CJK_FONT",
    "CJK_FALLBACK",
    "MONO_FONT",
    "INK",
    "INK_DIM",
    "INK_FAINT",
    "CORE",
    "WARM",
    "GOOD",
    "BAD",
    "HEIGHT_TITLE",
    "HEIGHT_EYEBROW",
    "HEIGHT_BODY",
    "HEIGHT_CAPTION",
    "HEIGHT_SMALL",
    "HEIGHT_EQ",
    "heading",
    "eyebrow",
    "body",
    "caption",
    "small",
    "code",
    "key_number",
    "label",
    "join",
]
