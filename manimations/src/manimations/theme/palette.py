"""视觉语言：一套配色、一套字体、一套安全区，所有成片共用。

改这里就能整体换肤，不用动任何一集成片脚本。规则尽量少而明确：

* 配色语义固定：CORE 蓝＝"被讲解的东西"，WARM 橙＝公式与强调，GOOD 绿＝正确结果，
  BAD 红＝错误/警告；其余一律用中性灰阶，避免画面变彩虹。
* 文字只用 :mod:`manimations.typography` 里的工厂函数产出，保证字号/字重一致。
* 安全区见 :data:`LAYOUT`，标题与旁白各占一条带，正文只能待在中间。
"""

from __future__ import annotations

from dataclasses import dataclass

from manim import DEGREES

# 注意：这里**不要**写 config.pixel_width / frame_rate。
# 库在 import 时改这些全局配置，会把用户在命令行给的 -ql / -qh 覆盖掉，
# 表现得就像"选低质量却渲了 1080p60"。质量档位交给 dsh render 决定，
# 库只负责"与分辨率无关"的东西：配色、安全区、字体、构图。


QUALITY_PRESETS: dict[str, dict[str, int]] = {
    # 快速检查用：480p / 15fps，渲一集约半分钟
    "preview": {"pixel_width": 854, "pixel_height": 480, "frame_rate": 15},
    # 发布用：1080p / 60fps
    "standard": {"pixel_width": 1920, "pixel_height": 1080, "frame_rate": 60},
}


# --------------------------------------------------------------------------
# 配色
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Palette:
    bg: str = "#0E1116"  # 背景，不用纯黑
    bg_alt: str = "#161B22"  # 卡片/面板底色
    ink: str = "#F2F5F7"  # 主文字
    ink_dim: str = "#A7B0BC"  # 次要文字、注释、旁白
    ink_faint: str = "#5C6672"  # 网格、坐标轴、装饰线
    core: str = "#4CC9F0"  # 主色：被讲解的对象（向量、几何体）
    warm: str = "#FFB703"  # 公式、结论、强调
    good: str = "#06D6A0"  # 正确 / 通过
    bad: str = "#EF476F"  # 错误 / 警告 / 失效
    cool: str = "#7B8CDE"  # 第二强调色，用于对比组


COLORS = Palette()

# 语义别名：写场景时用这些名字，读起来就是意图
BG = COLORS.bg
BG_ALT = COLORS.bg_alt
INK = COLORS.ink
INK_DIM = COLORS.ink_dim
INK_FAINT = COLORS.ink_faint
CORE = COLORS.core
WARM = COLORS.warm
GOOD = COLORS.good
BAD = COLORS.bad
COOL = COLORS.cool


# --------------------------------------------------------------------------
# 安全区与间距
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Layout:
    """画面分区。Manim 默认画幅是"高 8 × 宽 14.22"，原点在中心。

    标题在上带，旁白在下带，正文只允许待在中间，这样任何一集的视觉重心都稳定。
    """

    frame_height: float = 8.4  # 纵向放松一点，给标题和旁白留白
    title_y: float = 3.16  # 标题基线 y
    eyebrow_y: float = 3.72  # 小标题（章 / 节）的 y
    content_top: float = 2.72  # 正文可用区上界
    content_bottom: float = -2.52  # 正文可用区下界
    caption_y: float = -3.36  # 旁白文字中心 y
    side_margin: float = 0.9  # 左右安全边距
    accent_bar_len: float = 0.34
    accent_bar_width: float = 0.075

    @property
    def frame_width(self) -> float:
        """按 16:9 由高度推宽度。"""
        return self.frame_height * 16.0 / 9.0

    @property
    def content_width(self) -> float:
        """正文可用宽度（去掉左右安全边距）。"""
        return self.frame_width - 2 * self.side_margin

    @property
    def content_height(self) -> float:
        """正文可用高度。"""
        return self.content_top - self.content_bottom


LAYOUT = Layout()

# 常用机位，避免到处写 68 * DEGREES
AXIS_ISOMETRIC: dict[str, float] = {"phi": 68 * DEGREES, "theta": -48 * DEGREES}
AXIS_FRONT: dict[str, float] = {"phi": 60 * DEGREES, "theta": -90 * DEGREES}

__all__ = [
    "QUALITY_PRESETS",
    "Palette",
    "COLORS",
    "BG",
    "BG_ALT",
    "INK",
    "INK_DIM",
    "INK_FAINT",
    "CORE",
    "WARM",
    "GOOD",
    "BAD",
    "COOL",
    "Layout",
    "LAYOUT",
    "AXIS_ISOMETRIC",
    "AXIS_FRONT",
]
