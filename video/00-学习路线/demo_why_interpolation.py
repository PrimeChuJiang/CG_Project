"""第 0 集 · 为什么选择四元数：三元组装不下的那"一个分量"。

这一集只追一条线（和 ``blog/00-学习路线/00-01-demo-why-interpolation.md`` 一一对应）：

    三元组 → 缩放（kI）→ 旋转（单位圆上的和角公式）→ 3×3
           → 平移（3×3 做不到，因为它必须搬走原点）
           → 补一个 1 → 4×4 齐次矩阵 → w=1 是点 / w=0 是方向

**每一处代数变形都配一张图**：缩放是原方向上的拉伸，旋转是单位圆上的角度相加，
平移是整张纸跟着挪、原点自己也得走。图里的数字与公式里的数字来自同一个
``cgviz`` 调用，不存在"画个示意"。

几何约定：
* 坐标纸一律用 :func:`_plane` 造，**x/y 等比**——不等比的话"转 45°"在画面上
  就不是 45°，那正是这一集要讲的东西。
* 几何面板固定在左半区（原点落在 ``LEFT_O``），公式面板在右半区，
  正文带只用 y ∈ [-2.3, 2.2]（见 ``docs/pipeline.md`` 第四节）。
* 行向量约定：文章写 ``p' = p·M``，``cgviz`` 用列向量 ``M·p``，
  两者互为转置（``dsh verify`` 里有断言盯着这条），所以画面显示文章的形式、
  计算调用 cgviz，数字不会打架。
"""

from __future__ import annotations

import numpy as np
from manim import (
    DEGREES,
    DOWN,
    LEFT,
    RIGHT,
    TAU,
    UP,
    Arc,
    Arrow,
    Arrow3D,
    Axes,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    GrowArrow,
    Line,
    MathTex,
    ParametricFunction,
    Polygon,
    Square,
    ValueTracker,
    VGroup,
    smooth,
    linear,
)

from cgviz import mat, transform, vec

from manimations import Slide3DScene, SlideScene, typography as T
from manimations.components import Bullets, Equation, GrowArrow3D
from manimations.theme import (
    BAD,
    CORE,
    COOL,
    GOOD,
    INK,
    INK_DIM,
    INK_FAINT,
    WARM,
)

__all__ = [
    "WQ01_Cover",
    "WQ02_Triple",
    "WQ03_Scale",
    "WQ04_RotateGeom",
    "WQ05_RotateMatrix",
    "WQ06_ThreeAxes",
    "WQ07_Translation",
    "WQ08_Homogeneous",
    "WQ09_Summary",
]

RIGHT_X = 3.30  # 公式面板的中心横坐标


# ==========================================================================
# 版式工具
# ==========================================================================
def _plane(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    *,
    unit: float,
    origin: tuple[float, float],
) -> Axes:
    """一块**等比**坐标纸，原点被精确放在 ``origin``。

    只用一个 ``unit``（每单位数据对应的世界长度）同时决定 x_length 与 y_length，
    所以画面上的角度就是真实角度。先造再平移：``c2p`` 由数轴自身的点算出来，
    平移之后仍然对得上，于是每一页只需要说"原点落在哪"。
    """
    x0, x1 = x_range
    y0, y1 = y_range
    ax = Axes(
        x_range=[x0, x1, 1],
        y_range=[y0, y1, 1],
        x_length=(x1 - x0) * unit,
        y_length=(y1 - y0) * unit,
        axis_config={
            "include_ticks": False,
            "include_tip": True,
            "tip_width": 0.16,
            "tip_height": 0.16,
            "stroke_color": INK_FAINT,
            "stroke_width": 2.0,
        },
    )
    ax.shift(np.array([origin[0], origin[1], 0.0]) - ax.c2p(0, 0))
    return ax


def _arrow_between(ax: Axes, start, tip, color: str, *, width: float = 4.4) -> Arrow:
    """从数据点 ``start`` 指向 ``tip`` 的箭头（两端都按坐标纸换算）。"""
    return Arrow(
        ax.c2p(float(start[0]), float(start[1])),
        ax.c2p(float(tip[0]), float(tip[1])),
        buff=0,
        color=color,
        stroke_width=width,
        tip_length=0.2,
    )


def _vec_arrow(ax: Axes, tip, color: str, **kwargs) -> Arrow:
    """从原点出发的箭头。"""
    return _arrow_between(ax, (0.0, 0.0), tip, color, **kwargs)


def _eq(tex: str, *, color: str = WARM, note: str | None = None,
        height: float = 0.5, max_width: float = 5.7) -> Equation:
    """公式块：先按视觉高度排，再保证不撑破右半区。"""
    eq = Equation(tex, color=color, note=note, height=height)
    if eq.width > max_width:
        eq.scale_to_fit_width(max_width)
    return eq


def _small_tex(tex: str, color: str = INK, *, scale: float = 0.62) -> MathTex:
    return MathTex(tex, color=color).scale(scale)


def _axis_labels(ax: Axes, x_end, y_end) -> VGroup:
    """轴名：放在箭头**外侧**，别压在箭头上（压上去两者都是灰的，会糊成一团）。"""
    lx = T.small("x", INK_FAINT).next_to(ax.c2p(*x_end), DOWN + RIGHT, buff=0.08)
    ly = T.small("y", INK_FAINT).next_to(ax.c2p(*y_end), UP + RIGHT, buff=0.06)
    return VGroup(lx, ly)


def _stack(items, *, x: float = RIGHT_X, top: float = 2.05, gap: float = 0.34) -> VGroup:
    """把一组块从上往下摞在右半区，保证互不重叠。

    手写 y 坐标最容易出的错就是"两块挨太近"——Manim 不会报错，只会让公式
    叠在一起（WQ05 第一版就是这样）。这里按**每块自己的高度**推进 y，
    叠放顺序改了也不会重新算一遍坐标。
    """
    y = top
    for it in items:
        it.move_to([x, y - it.height / 2, 0])
        y -= it.height + gap
    return VGroup(*items)


# ==========================================================================
# 01 · 片头
# ==========================================================================
class WQ01_Cover(SlideScene):
    """封面：标题 + 一句承诺。"""

    eyebrow = "CG · 从 0 开始  /  第 0 集"
    title = "为什么选择四元数"

    def _chrome(self) -> None:
        # 封面自己排版，不用常规页眉
        self._eyebrow_mob = T.eyebrow(self.eyebrow, CORE)
        self._eyebrow_mob.move_to([0, 1.66, 0])
        self._title_mob = T.heading(self.title)
        self._title_mob.scale_to_fit_height(0.96)
        self._title_mob.move_to([0, 0.70, 0])
        self._accent_bar = None
        self._rule = Line([-2.9, -0.26, 0], [2.9, -0.26, 0], stroke_color=INK_FAINT, stroke_width=1.2)
        self._rule.set_opacity(0.5)
        self._subtitle = T.body("三元组 → 四元组：多出来的那个分量", INK_DIM)
        self._subtitle.move_to([0, -0.94, 0])
        self._branding = T.small("博客 → 视频 → 编码", INK_FAINT)
        self._branding.move_to([0, -2.3, 0])

    def _intro(self) -> None:
        self.play(FadeIn(self._eyebrow_mob, shift=0.2 * UP), run_time=0.7)
        self.play(FadeIn(self._title_mob, shift=0.16 * UP), run_time=0.9, rate_func=smooth)
        self.play(FadeIn(self._rule), FadeIn(self._subtitle, shift=0.1 * UP), run_time=0.7)
        self.play(FadeIn(self._branding), run_time=0.5)

    def build(self) -> None:
        self.say("这一集只追一个问题：三个数，为什么装不下一次平移。", wait=2.2)
        self.play(self._title_mob.animate.set_color(INK), run_time=0.4)
        self.wait(0.4)


# ==========================================================================
# 02 · 三元组：方向与长度都有，起点没有
# ==========================================================================
class WQ02_Triple(SlideScene):
    """几何：一个从原点出发的箭头，和它的一个"分身"。"""

    eyebrow = "01 · 三元组"
    title = "三个数，说清了方向，说不清起点"

    def build(self) -> None:
        p = np.array([2.0, 1.5, 0.0])
        ax = _plane((-0.5, 3.3), (-0.5, 2.4), unit=1.45, origin=(-5.4, -1.5))
        axis_names = _axis_labels(ax, (3.3, 0), (0, 2.4))
        origin = ax.c2p(0, 0)
        o_dot = Dot(origin, radius=0.055, color=INK)
        o_lab = MathTex("O", color=INK).scale(0.55).next_to(o_dot, DOWN + LEFT, buff=0.10)

        arrow = _vec_arrow(ax, p[:2], CORE)
        p_lab = _small_tex(r"\vec p", CORE).next_to(arrow.get_end(), UP + RIGHT, buff=0.12)
        norm = vec.length(p)

        # 分身：同一个箭头，换个起点。三元组说不出"它该从哪儿出发"。
        ghost = _vec_arrow(ax, p[:2], INK_FAINT)
        ghost.shift(ax.c2p(0.75, -0.15) - origin)
        ghost_lab = T.small("同一个三元组", INK_FAINT)
        ghost_lab.next_to(ghost.get_end(), RIGHT, buff=0.10)

        eq = _eq(r"\vec p=\begin{bmatrix}x & y & z\end{bmatrix}",
                 color=CORE, note="方向 + 长度，三个数里都有", height=0.62)

        num = MathTex(
            rf"x={p[0]:.1f},\quad y={p[1]:.1f},\quad z={p[2]:.1f}", color=INK
        ).scale(0.62)
        norm_tex = MathTex(rf"\|\vec p\|={norm:.3f}", color=WARM).scale(0.72)
        norm_lab = T.small("长度也只由这三个数决定", INK_DIM)
        _stack([eq, num, norm_tex, norm_lab], top=2.00, gap=0.38)

        self.play(FadeIn(ax), FadeIn(axis_names), run_time=0.8)
        self.play(FadeIn(o_dot), FadeIn(o_lab), run_time=0.4)
        self.play(GrowArrow(arrow), FadeIn(p_lab), run_time=0.9)
        self.play(FadeIn(eq), run_time=0.9)
        self.say("一个三元组：方向、长度，都在这三个数里。", wait=1.5)

        self.play(FadeIn(num), FadeIn(norm_tex), FadeIn(norm_lab), run_time=0.7)
        self.say("但线性代数里，所有向量都从原点出发。", wait=1.4, emphasis=["原点出发"])

        self.play(FadeIn(ghost), FadeIn(ghost_lab), run_time=0.9)
        self.say("把箭头搬到别处，三元组一个字都不用改。", wait=1.5)
        self.say("起点不在三元组里 —— 它被坐标系钉死在 O。", wait=1.9, emphasis=["钉死在 O"])
        self.wait(0.3)


# ==========================================================================
# 03 · 缩放
# ==========================================================================
class WQ03_Scale(SlideScene):
    """几何：沿原方向拉长；代数：kI。"""

    eyebrow = "01 · 三元组 / 缩放"
    title = "缩放：就是一个对角矩阵"

    def build(self) -> None:
        p = np.array([2.0, 1.5, 0.0])
        k_final = 1.5
        ax = _plane((-0.5, 3.3), (-0.5, 2.4), unit=1.45, origin=(-5.4, -1.5))
        axis_names = _axis_labels(ax, (3.3, 0), (0, 2.4))
        origin = ax.c2p(0, 0)
        o_dot = Dot(origin, radius=0.05, color=INK)

        base = _vec_arrow(ax, p[:2], CORE)
        base_lab = _small_tex(r"\vec p", CORE).next_to(base.get_end(), UP + LEFT, buff=0.12)

        k = ValueTracker(1.0)
        scaled = _vec_arrow(ax, p[:2], WARM)
        scaled.add_updater(
            lambda m: m.put_start_and_end_on(
                origin, ax.c2p(k.get_value() * p[0], k.get_value() * p[1])
            )
        )
        k_lab = _small_tex(r"k\vec p", WARM)
        k_lab.add_updater(lambda m: m.next_to(scaled.get_end(), UP + RIGHT, buff=0.12))

        # 数字仍由 cgviz 算：缩放矩阵作用在同一点上
        p_scaled = transform.apply(transform.scale2d(k_final), p[:2])

        eq1 = _eq(r"\vec p'=k\vec p=kI\,\vec p", color=WARM, height=0.5)
        eq2 = _eq(
            r"=\begin{bmatrix}k&0&0\\0&k&0\\0&0&k\end{bmatrix}\vec p",
            color=WARM,
            note="缩放没有新东西：一个初等变换",
            height=1.12,
        )
        num = MathTex(
            rf"k={k_final:.2f}\ \Rightarrow\ "
            rf"\vec p'=\begin{{bmatrix}}{p_scaled[0]:.2f} & {p_scaled[1]:.2f}\end{{bmatrix}}",
            color=INK,
        ).scale(0.6)
        num_lab = T.small("方向不变，长度乘 k", INK_DIM)
        _stack([eq1, eq2, num, num_lab], top=2.05, gap=0.34)

        self.play(FadeIn(ax), FadeIn(axis_names), FadeIn(o_dot), run_time=0.8)
        self.play(GrowArrow(base), FadeIn(base_lab), run_time=0.8)
        self.say("缩放：方向不变，长度乘上一个常数 k。", wait=1.4)

        self.play(GrowArrow(scaled), FadeIn(k_lab), run_time=0.7)
        self.play(k.animate.set_value(k_final), run_time=1.6, rate_func=smooth)
        # 让原来的 p 压在 kp 之上：否则同向的暖色箭头会把蓝色的 p 完全盖住，
        # 观众就看不到"从 p 拉长到 kp"这件事了。
        self.bring_to_front(base, base_lab)
        self.say("画面上就是沿着同一条线拉长。", wait=1.3)

        self.play(FadeIn(eq1), run_time=0.7)
        self.play(FadeIn(eq2), run_time=0.8)
        self.say("写成矩阵，就是对角线上的 k。", wait=1.3, emphasis=["对角线"])

        self.play(FadeIn(num), FadeIn(num_lab), run_time=0.7)
        self.say("3×3 能做的第一件事，齐了。", wait=1.6)
        self.wait(0.3)


# ==========================================================================
# 04 · 旋转的几何：单位圆上的角度相加
# ==========================================================================
class WQ04_RotateGeom(SlideScene):
    """几何：单位圆 + 两个角；代数：和角公式。"""

    eyebrow = "02 · 旋转"
    title = "绕 z 转：把 x-y 平面单独拿出来"

    def build(self) -> None:
        alpha = 30.0 * DEGREES
        theta = 45.0 * DEGREES
        unit = 1.85
        origin_xy = (-4.55, -0.45)
        ax = _plane((-0.35, 1.35), (-0.30, 1.40), unit=unit, origin=origin_xy)
        axis_names = _axis_labels(ax, (1.35, 0), (0, 1.40))
        o = ax.c2p(0, 0)

        circle = Circle(radius=unit, color=INK_FAINT, stroke_width=1.6).move_to(o)
        # set_opacity 会连填充一起打开，把圆变成实心盘；只调描边。
        circle.set_stroke(opacity=0.5)
        x_line = DashedLine(o, ax.c2p(1.35, 0), stroke_color=INK_FAINT, stroke_width=1.2)
        x_line.set_stroke(opacity=0.35)

        v0 = np.array([np.cos(alpha), np.sin(alpha), 0.0])
        v1 = mat.rotation_z(theta) @ v0

        p_arrow = _vec_arrow(ax, v0[:2], CORE)
        p_lab = _small_tex(r"\vec p", CORE).next_to(p_arrow.get_end(), RIGHT, buff=0.12)

        p1_arrow = _vec_arrow(ax, v1[:2], WARM)
        p1_lab = _small_tex(r"\vec p\,'", WARM).next_to(p1_arrow.get_end(), RIGHT, buff=0.12)

        arc_a = Arc(radius=0.5 * unit, start_angle=0, angle=alpha, arc_center=o,
                    color=CORE, stroke_width=3.0)
        arc_a_lab = _small_tex(r"\alpha", CORE).move_to(
            o + (0.5 * unit + 0.30) * np.array([np.cos(alpha / 2), np.sin(alpha / 2), 0])
        )
        arc_t = Arc(radius=0.74 * unit, start_angle=alpha, angle=theta, arc_center=o,
                    color=WARM, stroke_width=3.0)
        arc_t_lab = _small_tex(r"\theta", WARM).move_to(
            o + (0.74 * unit + 0.32) * np.array([np.cos(alpha + theta / 2),
                                                 np.sin(alpha + theta / 2), 0])
        )

        # 两条投影虚线：把 p' 的 x、y 分量落到轴上
        drop_x = DashedLine(p1_arrow.get_end(), ax.c2p(v1[0], 0),
                            stroke_color=WARM, stroke_width=1.2)
        drop_y = DashedLine(p1_arrow.get_end(), ax.c2p(0, v1[1]),
                            stroke_color=WARM, stroke_width=1.2)
        drop_x.set_stroke(opacity=0.45)
        drop_y.set_stroke(opacity=0.45)
        x_lab = _small_tex(r"x'", WARM).next_to(ax.c2p(v1[0], 0), DOWN, buff=0.10)
        y_lab = _small_tex(r"y'", WARM)
        # 别用 next_to(…, LEFT)：y 轴就在 x=0，标签会正好骑在轴上
        y_lab.move_to(ax.c2p(-0.24, v1[1]))

        # 右：和角公式
        eq1 = _eq(r"x'=\cos(\alpha+\theta)=\cos\alpha\cos\theta-\sin\alpha\sin\theta",
                  color=INK, height=0.42)
        eq2 = _eq(r"y'=\sin(\alpha+\theta)=\sin\alpha\cos\theta+\cos\alpha\sin\theta",
                  color=INK, height=0.42)
        given = MathTex(r"\alpha=30^\circ,\quad\theta=45^\circ", color=INK_DIM).scale(0.62)
        result = MathTex(
            rf"x'={v1[0]:.3f},\quad y'={v1[1]:.3f}", color=WARM
        ).scale(0.68)
        result_note = T.small("在图上就是 p' 的那两条投影", INK_DIM)
        norm_tex = MathTex(rf"\|\vec p\,'\|={vec.length(v1):.3f}", color=GOOD).scale(0.64)
        norm_note = T.small("长度没变：p' 还在圆上", GOOD)
        _stack([eq1, eq2, given, result, result_note, norm_tex, norm_note], top=2.02, gap=0.26)

        self.play(FadeIn(ax), FadeIn(axis_names), FadeIn(circle), FadeIn(x_line), run_time=1.0)
        self.say("把视线压到 x-y 平面：绕 z 转，就是在圆上走一段弧。", wait=1.5)

        self.play(GrowArrow(p_arrow), FadeIn(p_lab), run_time=0.8)
        self.play(Create(arc_a), FadeIn(arc_a_lab), run_time=0.7)
        self.say("p 和 x 轴的夹角是 α。", wait=1.2, emphasis=["α"])

        self.play(FadeIn(eq1), FadeIn(eq2), run_time=0.9)
        self.say("再转 θ，角度就变成 α+θ —— 和角公式出场。", wait=1.6)

        self.play(GrowArrow(p1_arrow), FadeIn(p1_lab), Create(arc_t), FadeIn(arc_t_lab),
                  run_time=1.4, rate_func=smooth)
        self.play(Create(drop_x), Create(drop_y), FadeIn(x_lab), FadeIn(y_lab), run_time=0.7)
        self.play(FadeIn(given), FadeIn(result), FadeIn(result_note), run_time=0.7)
        self.play(FadeIn(norm_tex), FadeIn(norm_note), run_time=0.5)
        self.say("长度一点没变：p' 还在圆上。", wait=1.5, emphasis=["还在圆上"])
        self.say("拆开和角公式，两对三角函数各乘一次。", wait=1.9)
        self.wait(0.3)


# ==========================================================================
# 05 · 旋转的矩阵：右乘一个 2×2
# ==========================================================================
class WQ05_RotateMatrix(SlideScene):
    """几何：单位正方形转 45°；代数：2×2 → 3×3。"""

    eyebrow = "02 · 旋转 / 矩阵"
    title = "同一个旋转，写成右乘一个矩阵"

    def build(self) -> None:
        theta = 45.0 * DEGREES
        unit = 1.75
        origin_xy = (-4.9, -1.55)
        ax = _plane((-0.95, 1.25), (-0.35, 1.55), unit=unit, origin=origin_xy)
        axis_names = _axis_labels(ax, (1.25, 0), (0, 1.55))
        o = ax.c2p(0, 0)

        square = Polygon(
            ax.c2p(0, 0), ax.c2p(1, 0), ax.c2p(1, 1), ax.c2p(0, 1), color=INK_DIM
        )
        square.set_fill(INK_FAINT, opacity=0.10).set_stroke(INK_DIM, width=1.8, opacity=0.8)

        # 图像 = 同一个矩阵作用在四个顶点上（由 cgviz 算，不手写坐标）
        rot = mat.rotation_z(theta)
        corners = [rot @ np.array([x, y, 0.0]) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1))]
        image = Polygon(*[ax.c2p(c[0], c[1]) for c in corners], color=CORE)
        image.set_fill(CORE, opacity=0.14).set_stroke(CORE, width=2.8)

        arc = Arc(radius=unit, start_angle=0, angle=theta, arc_center=o,
                  color=WARM, stroke_width=2.4)
        arc_lab = _small_tex(r"\theta", WARM).move_to(
            o + (unit + 0.30) * np.array([np.cos(theta / 2), np.sin(theta / 2), 0])
        )

        eq_xy = _eq(r"x'=x\cos\theta-y\sin\theta,\qquad y'=x\sin\theta+y\cos\theta",
                    color=INK, height=0.38)
        eq3 = _eq(
            r"\begin{bmatrix}x'&y'\end{bmatrix}"
            r"=\begin{bmatrix}x&y\end{bmatrix}"
            r"\begin{bmatrix}\cos\theta&\sin\theta\\-\sin\theta&\cos\theta\end{bmatrix}",
            color=WARM,
            note="右边这个矩阵，就是「绕 z 转 θ」",
            height=0.90,
        )
        eq4 = _eq(
            r"R_z(\theta)=\begin{bmatrix}\cos\theta&\sin\theta&0\\"
            r"-\sin\theta&\cos\theta&0\\0&0&1\end{bmatrix}",
            color=WARM,
            note="升到三维：第三维原样不动，所以填 1",
            height=1.05,
        )
        _stack([eq_xy, eq3, eq4], top=2.00, gap=0.32)

        self.play(FadeIn(ax), FadeIn(axis_names), FadeIn(square), run_time=0.8)
        self.say("单位方格是「整个平面」的缩影。", wait=1.2)
        self.play(FadeIn(image), Create(arc), FadeIn(arc_lab), run_time=1.3, rate_func=smooth)
        self.say("同一个矩阵，把整个方格一起转过去。", wait=1.4, emphasis=["一起转"])

        self.play(FadeIn(eq_xy), run_time=0.8)
        self.say("化简出来的两条式子，正好是它的两行。", wait=1.3)
        self.play(FadeIn(eq3), run_time=0.9)
        self.say("写成矩阵乘法，就是右乘这个 2×2。", wait=1.5, emphasis=["右乘"])
        self.play(FadeIn(eq4), run_time=0.9)
        self.say("补上第三维的 1，就是三维里的绕 z 旋转。", wait=1.9)
        self.wait(0.3)


# ==========================================================================
# 06 · 三根轴：三次绕轴旋转的组合
# ==========================================================================
class WQ06_ThreeAxes(Slide3DScene):
    """几何：三个坐标平面各一个圆；代数：三个 3×3，颜色一一对应。"""

    eyebrow = "02 · 旋转 / 三轴"
    title = "任意旋转 = 三次绕轴旋转"
    accent = GOOD

    def build(self) -> None:
        centre = np.array([-3.70, -0.55, 0.0])
        r = 1.80

        # 不要 ThreeDAxes：它会画满整个 range、竖线一直顶到标题带。
        # 这里只要三根短箭头，正文区装得下就行。z 轴在 phi=68° 下几乎不缩短
        # （投影长度 ≈ 0.93 倍），所以它比 x/y 更容易顶到标题，别画太长。
        axis_arrows = VGroup(
            *[
                Arrow3D(
                    centre,
                    centre + 2.4 * np.array(v, dtype=np.float64),
                    color=INK_FAINT,
                    thickness=0.022,
                    base_radius=0.042,
                )
                for v in ([1, 0, 0], [0, 1, 0])
            ],
            # z 轴单独短一截：phi=68° 下它几乎不缩短，2.4 会穿过标题
            Arrow3D(centre, centre + 1.65 * np.array([0.0, 0.0, 1.0]),
                    color=INK_FAINT, thickness=0.022, base_radius=0.042),
        )

        def ring(func, color: str) -> ParametricFunction:
            c = ParametricFunction(func, t_range=[0, TAU, TAU / 128])
            c.set_stroke(color, width=2.6, opacity=0.85)
            return c

        rings = VGroup(
            # x-y 平面 → 绕 z
            ring(lambda t: centre + r * np.array([np.cos(t), np.sin(t), 0.0]), CORE),
            # y-z 平面 → 绕 x
            ring(lambda t: centre + r * np.array([0.0, np.cos(t), np.sin(t)]), GOOD),
            # z-x 平面 → 绕 y
            ring(lambda t: centre + r * np.array([np.cos(t), 0.0, np.sin(t)]), COOL),
        )

        ang = ValueTracker(0.0)
        spoke = Arrow3D(centre, centre + np.array([r, 0.0, 0.0]),
                        color=WARM, thickness=0.032, base_radius=0.05)
        # 不要每帧重建 Arrow3D（构造很贵）；复用同一根，只改端点。
        spoke.add_updater(
            lambda m: m.put_start_and_end_on(
                centre, centre + mat.rotation_z(ang.get_value()) @ np.array([r, 0.0, 0.0])
            )
        )

        z_head = T.small("绕 z · x-y 平面内转", CORE, weight="BOLD")
        x_head = T.small("绕 x · y-z 平面内转", GOOD, weight="BOLD")
        y_head = T.small("绕 y · z-x 平面内转", COOL, weight="BOLD")

        def matrix_block(head, tex: str, color: str) -> VGroup:
            m = MathTex(tex, color=color)
            m.scale_to_fit_height(0.78)
            block = VGroup(head, m).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
            return block

        mz = matrix_block(
            z_head,
            r"R_z(\gamma)=\begin{bmatrix}\cos\gamma&\sin\gamma&0\\"
            r"-\sin\gamma&\cos\gamma&0\\0&0&1\end{bmatrix}",
            CORE,
        )
        mx = matrix_block(
            x_head,
            r"R_x(\alpha)=\begin{bmatrix}1&0&0\\0&\cos\alpha&\sin\alpha\\"
            r"0&-\sin\alpha&\cos\alpha\end{bmatrix}",
            GOOD,
        )
        my = matrix_block(
            y_head,
            r"R_y(\beta)=\begin{bmatrix}\cos\beta&0&-\sin\beta\\0&1&0\\"
            r"\sin\beta&0&\cos\beta\end{bmatrix}",
            COOL,
        )
        blocks = VGroup(mz, mx, my)
        _stack(blocks, x=RIGHT_X + 0.30, top=2.02, gap=0.24)

        # 3D 页里的 2D 内容必须钉屏，否则会被相机压成"躺在地上"的斜投影
        self.flat(blocks)

        self.play(FadeIn(axis_arrows), run_time=0.8)
        self.play(*[Create(c) for c in rings], run_time=1.6)
        self.say("三个坐标平面，各配一个 3×3。", wait=1.4)

        self.play(GrowArrow3D(spoke), run_time=0.9)
        self.play(ang.animate.set_value(55 * DEGREES), run_time=2.0, rate_func=linear)
        self.say("在 x-y 平面里转，第三维 z 一点不动。", wait=1.6, emphasis=["一点不动"])

        self.play(FadeIn(mz), run_time=0.7)
        self.say("所以 R_z 的第三行第三列就是 1。", wait=1.4, emphasis=["就是 1"])
        self.play(FadeIn(mx), FadeIn(my), run_time=0.9)
        self.say("绕 x、绕 y 同理：各自只动两个分量。", wait=1.5)
        self.say("三个角各转一次，按顺序乘起来，就是任意姿态。", wait=2.0, emphasis=["按顺序"])
        self.wait(0.3)


# ==========================================================================
# 07 · 平移：原点必须搬家
# ==========================================================================
class WQ07_Translation(SlideScene):
    """几何：整张纸平移；代数：常数项 1·a。"""

    eyebrow = "03 · 平移"
    title = "平移：3×3 做不到的一件事"

    def build(self) -> None:
        p = np.array([1.6, 0.7, 0.0])
        t = np.array([0.9, 1.1, 0.0])  # 与 p 不同向，画面才不会三条箭头糊成一条
        moved = transform.apply(transform.translate2d(t[0], t[1]), p[:2])

        ax = _plane((-0.5, 3.0), (-0.4, 2.0), unit=1.3, origin=(-5.55, -1.75))
        axis_names = _axis_labels(ax, (3.0, 0), (0, 2.0))
        o = ax.c2p(0, 0)
        o_dot = Dot(o, radius=0.055, color=INK)
        o_lab = MathTex("O", color=INK).scale(0.55).next_to(o_dot, DOWN + LEFT, buff=0.10)

        p_arrow = _vec_arrow(ax, p[:2], CORE)
        p_lab = _small_tex(r"\vec p", CORE).next_to(p_arrow.get_end(), UP + LEFT, buff=0.12)

        # 平移：每个点都往前走同一个 t —— 画两段 t 就够看出"整张纸在挪"
        t_arrow = _arrow_between(ax, (0.0, 0.0), t[:2], WARM, width=3.2)
        t_lab = _small_tex(r"\vec t", WARM).next_to(t_arrow.get_end(), DOWN, buff=0.08)
        moved_arrow = _arrow_between(ax, t[:2], moved, WARM)
        moved_lab = _small_tex(r"\vec p+\vec t", WARM).next_to(moved_arrow.get_end(), UP, buff=0.12)
        hop = _arrow_between(ax, p[:2], moved, WARM, width=2.2)
        hop.set_stroke(opacity=0.85)

        eq_x = _eq(r"x'=x\cdot 1+y\cdot 0+z\cdot 0+1\cdot a",
                   color=INK, note="把 a 写成 1·a：那个 1 就是线索", height=0.46)
        eq_mat = _eq(
            r"\begin{bmatrix}x'&y'&z'\end{bmatrix}"
            r"=\begin{bmatrix}x&y&z&1\end{bmatrix}"
            r"\begin{bmatrix}1&0&0\\0&1&0\\0&0&1\\a&b&c\end{bmatrix}",
            color=WARM,
            height=1.40,
        )
        warn = T.small("任何 3×3 都把 O 留在原地", BAD, weight="BOLD")
        warn2 = T.small("可平移要求 O 也走一段 t —— 矛盾", BAD)
        _stack([eq_x, eq_mat, warn, warn2], top=2.02, gap=0.34)

        self.play(FadeIn(ax), FadeIn(axis_names), FadeIn(o_dot), FadeIn(o_lab), run_time=0.8)
        self.play(GrowArrow(p_arrow), FadeIn(p_lab), run_time=0.8)
        self.say("现在想把 p 搬到 p+t。", wait=1.2)

        self.play(GrowArrow(t_arrow), FadeIn(t_lab), run_time=0.7)
        self.play(GrowArrow(hop), GrowArrow(moved_arrow), FadeIn(moved_lab), run_time=1.2)
        self.say("注意：每个点都往前走同一个 t。", wait=1.5, emphasis=["每个点"])

        self.play(FadeIn(warn), FadeIn(warn2), run_time=0.8)
        self.say("3×3 是线性变换，它只会把原点留在原点。", wait=1.6, emphasis=["留在原点"])

        self.play(FadeIn(eq_x), run_time=0.8)
        self.say("于是把 a 写成 1·a：常数要乘一个 1 才能进矩阵。", wait=1.9, emphasis=["1·a"])
        self.play(FadeIn(eq_mat), run_time=0.9)
        self.say("矩阵从 3×3 变成 4×3，三维输出、四维输入。", wait=1.9)
        self.wait(0.3)


# ==========================================================================
# 08 · 升一维：4×4 与 w 的含义
# ==========================================================================
class WQ08_Homogeneous(SlideScene):
    """几何：点被搬走，方向不动；代数：4×4，w=1 / w=0。"""

    eyebrow = "03 · 平移 / 升维"
    title = "补一个 1：从 3×4 到 4×4"

    def build(self) -> None:
        p = np.array([1.6, 0.7, 0.0])
        t = np.array([0.9, 1.1, 0.0])
        m4 = transform.translate3d(t[0], t[1], t[2])
        as_point = transform.apply(m4, p, 1.0)
        as_dir = transform.apply(m4, p, 0.0)

        ax = _plane((-0.5, 3.0), (-0.4, 2.0), unit=1.3, origin=(-5.55, -1.75))
        axis_names = _axis_labels(ax, (3.0, 0), (0, 2.0))
        o = ax.c2p(0, 0)

        # 方向：一根箭头，变换前后**一模一样**（图片里它不动，所以只画一次）
        dir_arrow = _vec_arrow(ax, as_dir[:2], CORE)
        dir_lab = T.small("方向 w = 0：不动", CORE)
        dir_lab.next_to(dir_arrow.get_end(), DOWN + RIGHT, buff=0.10)

        # 点：一个圆点，正好压在箭头的末端（两者坐标相同），然后被 t 带走
        ghost = Dot(ax.c2p(*(p[:2])), radius=0.075, color=WARM)
        ghost.set_fill(WARM, opacity=0.3).set_stroke(opacity=0)
        start_dot = Dot(ax.c2p(*(p[:2])), radius=0.075, color=WARM)
        moved_lab = T.small("点 w = 1：走 t", WARM)
        moved_lab.next_to(ax.c2p(*(as_point[:2])), UP + RIGHT, buff=0.12)
        t_arrow = _arrow_between(ax, p[:2], as_point[:2], WARM, width=2.4)
        t_lab = _small_tex(r"\vec t", WARM)
        t_lab.next_to(t_arrow.get_center(), RIGHT, buff=0.10)

        eq_expand = _eq(
            r"\begin{bmatrix}1&0&0\\0&1&0\\0&0&1\\a&b&c\end{bmatrix}"
            r"\;\rightarrow\;"
            r"\begin{bmatrix}1&0&0&0\\0&1&0&0\\0&0&1&0\\a&b&c&1\end{bmatrix}",
            color=WARM,
            note="补上第四列：除了最后一个 1，全是 0",
            height=1.20,
        )
        eq_pt = MathTex(
            rf"\begin{{bmatrix}}{p[0]:.1f}&{p[1]:.1f}&0&1\end{{bmatrix}}"
            rf"\mapsto\begin{{bmatrix}}{as_point[0]:.1f}&{as_point[1]:.1f}&0&1\end{{bmatrix}}",
            color=WARM,
        ).scale(0.58)
        eq_dir = MathTex(
            rf"\begin{{bmatrix}}{p[0]:.1f}&{p[1]:.1f}&0&0\end{{bmatrix}}"
            rf"\mapsto\begin{{bmatrix}}{as_dir[0]:.1f}&{as_dir[1]:.1f}&0&0\end{{bmatrix}}",
            color=CORE,
        ).scale(0.58)
        note = T.small("第四列只做一件事：把 w 原样送回去", INK_DIM)
        _stack([eq_expand, eq_pt, eq_dir, note], top=2.02, gap=0.34)

        self.play(FadeIn(ax), FadeIn(axis_names), run_time=0.7)
        self.play(FadeIn(eq_expand), run_time=0.9)
        self.say("3×4 不够整齐：补上第四列，变成 4×4。", wait=1.5)

        self.play(GrowArrow(dir_arrow), FadeIn(dir_lab), run_time=0.8)
        self.play(FadeIn(ghost), FadeIn(start_dot), run_time=0.5)
        self.say("同一个三元组：w=0 时它是方向，箭头一动不动。", wait=1.2, emphasis=["一动不动"])

        self.play(GrowArrow(t_arrow), FadeIn(t_lab), run_time=0.8)
        self.play(start_dot.animate.move_to(ax.c2p(*(as_point[:2]))), run_time=1.5, rate_func=smooth)
        self.play(FadeIn(moved_lab), run_time=0.5)
        self.say("w=1 时它是点：加不加 t，只看这一个数字。", wait=1.8, emphasis=["一个数字"])

        self.play(FadeIn(eq_pt), run_time=0.7)
        self.play(FadeIn(eq_dir), FadeIn(note), run_time=0.8)
        self.say("一个分量，分开了「点」和「方向」。", wait=2.0, emphasis=["点", "方向"])
        self.wait(0.3)


# ==========================================================================
# 09 · 收束：4×4 的四块
# ==========================================================================
class WQ09_Summary(SlideScene):
    """把 4×4 切成四块：旋转/缩放、w 列、平移行、那个 1。"""

    eyebrow = "04 · 收束"
    title = "三元组负责形状，第四维负责位置"
    accent = GOOD

    def build(self) -> None:
        cell, gap = 0.62, 0.05
        step = cell + gap
        x0, y0 = -5.10, 1.15  # 左上角格子的中心

        def cell_center(r: int, c: int) -> np.ndarray:
            return np.array([x0 + c * step, y0 - r * step, 0.0])

        block = Square(side_length=3 * cell + 2 * gap)
        block.move_to(cell_center(1, 1))
        block.set_fill(CORE, opacity=0.12).set_stroke(CORE, width=1.8, opacity=0.75)
        block_lab = MathTex("R", color=CORE).scale(1.0).move_to(block)

        # 第 4 列：w。三个 0 + 一个 1
        col_cells = VGroup()
        for r in range(3):
            sq = Square(side_length=cell).move_to(cell_center(r, 3))
            sq.set_fill(INK_FAINT, opacity=0.10).set_stroke(INK_FAINT, width=1.0, opacity=0.55)
            col_cells.add(VGroup(sq, MathTex("0", color=INK_DIM).scale(0.46)
                                 .move_to(cell_center(r, 3))))
        corner = Square(side_length=cell).move_to(cell_center(3, 3))
        corner.set_fill(INK_FAINT, opacity=0.10).set_stroke(INK_FAINT, width=1.0, opacity=0.55)
        corner = VGroup(corner, MathTex("1", color=INK).scale(0.46).move_to(cell_center(3, 3)))

        # 第 4 行：平移
        row_cells = VGroup()
        for c, sym in enumerate(("a", "b", "c")):
            sq = Square(side_length=cell).move_to(cell_center(3, c))
            sq.set_fill(WARM, opacity=0.14).set_stroke(WARM, width=1.0, opacity=0.6)
            row_cells.add(VGroup(sq, MathTex(sym, color=WARM).scale(0.46)
                                 .move_to(cell_center(3, c))))

        # 图例竖排放在网格正下方：横排会横穿整个画幅（第一版就被切到画外了）
        legend = VGroup()
        for color, text in (
            (CORE, "3×3：旋转 / 缩放"),
            (WARM, "第 4 行：平移"),
            (INK_FAINT, "第 4 列：w 原样返回"),
        ):
            chip = Square(side_length=0.17)
            chip.set_fill(color, opacity=0.5).set_stroke(color, width=1.0, opacity=0.8)
            label = T.small(text, INK_DIM)
            legend.add(VGroup(chip, label).arrange(RIGHT, buff=0.14, aligned_edge=DOWN))
        legend.arrange(DOWN, buff=0.10, aligned_edge=LEFT)
        legend.shift([-5.45 - legend.get_left()[0], -1.72 - legend.get_center()[1], 0])

        points = Bullets(
            [
                "缩放、旋转：3×3 就够，原点不动",
                "平移：原点必须搬家，3×3 做不到",
                "补一个 1 → 4×4，多出一行平移",
                "w=1 是点，w=0 是方向",
            ],
            marker_color=GOOD,
            text_color=INK,
        )
        points.fit(6.1).move_to([3.05, 0.35, 0])

        closing = T.small("下一步：把向量换成点，看点在坐标系之间怎么流动", INK_DIM)
        closing.move_to([3.05, -1.95, 0])

        self.play(FadeIn(block), FadeIn(block_lab), run_time=0.9)
        self.say("一个 4×4，可以切成四块来看。", wait=1.4)
        self.play(FadeIn(col_cells), FadeIn(corner), run_time=0.7)
        self.say("最后一列只负责把 w 送回去。", wait=1.4)
        self.play(FadeIn(row_cells), run_time=0.7)
        self.say("最后一行，才是平移真正住的地方。", wait=1.5, emphasis=["最后一行"])
        self.play(FadeIn(legend), run_time=0.7)

        self.play(FadeIn(points, shift=0.15 * UP), run_time=0.9)
        self.say("三元组能做的，3×3 全包了；它做不了的，只能靠第四维。", wait=2.0)
        self.play(FadeIn(closing), run_time=0.6)
        self.say("这笔账，就是后面所有坐标空间变换的起点。", wait=2.2)
        self.wait(0.4)
