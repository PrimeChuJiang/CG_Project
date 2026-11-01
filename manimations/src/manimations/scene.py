"""分镜基类：把"一页幻灯片"的通用流程固化下来，子类只填内容。

一页的生命周期固定为五步，任何一集都长这样：

    _stage()    铺背景、网点、外框（静态，不参与动画）
    _chrome()   小标题 + 主标题 + 左上角着色条 + 旁白带
    _intro()    标题动画入场
    build()     ← 子类实现：正文的所有动画
    _outro()    整体淡出，不留黑屏突兀感

这样做的好处是：**序列帧永远对齐、视觉节奏永远一致**，写新的一集时只需要关心
"这一页要讲什么"，而不是"标题放哪、字号多大、旁白带多高"。
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
from manim import (
    DOWN,
    LEFT,
    UP,
    Add,
    Animation,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    Line,
    RoundedRectangle,
    ThreeDScene,
    VGroup,
    linear,
    smooth,
)

from . import typography as T
from .theme.palette import (
    AXIS_ISOMETRIC,
    BG,
    CORE,
    INK_FAINT,
    LAYOUT,
)


class SlideScene(ThreeDScene):
    """一页 2D 幻灯片。

    子类只需要：

    ```python
    class MySlide(SlideScene):
        eyebrow = "03 · 旋转"
        title = "矩阵插值为什么把模型压扁"

        def build(self) -> None:
            ...
    ```

    若想覆盖入场/退场动画，重写 :meth:`_intro` / :meth:`_outro`。
    """

    # ---- 子类可覆盖的排版属性 ----
    eyebrow: str = ""
    title: str = ""
    accent: str = CORE
    show_branding: bool = True
    """右下角是否显示项目水印。特写页（如纯公式推导）可以关掉。"""

    # ---- 子类必须实现 ----
    def build(self) -> None:
        """正文内容。所有 ``self.play`` 都写在这里。"""
        raise NotImplementedError(f"{type(self).__name__} 必须实现 build()")

    # ---- 生命周期 ----
    def construct(self) -> None:
        self._stage()
        self._chrome()
        self._intro()
        self.build()
        self._outro()

    # ------------------------------------------------------------------
    # 舞台
    # ------------------------------------------------------------------
    def _stage(self) -> None:
        """铺底：纯色背景 + 极淡网点 + 一圈内嵌细框（给画面一个"取景框"的暗示）。"""
        self.camera.background_color = BG
        self.frame_width = LAYOUT.frame_width
        self.frame_height = LAYOUT.frame_height
        self.add(self._backdrop())

    def _backdrop(self) -> VGroup:
        """背景网点。稀疏、极淡，只用来避免大面积纯色显得"空"。"""
        dots = VGroup()
        step = 0.75
        for x in np.arange(-7.0, 7.01, step):
            for y in np.arange(-4.0, 4.01, step):
                dots.add(
                    RoundedRectangle(width=0.018, height=0.018, corner_radius=0)
                    .set_fill(INK_FAINT, opacity=0.16)
                    .set_stroke(width=0)
                    .move_to([x, y, 0])
                )
        return dots

    # ------------------------------------------------------------------
    # 页眉与旁白带
    # ------------------------------------------------------------------
    def _chrome(self) -> None:
        self._eyebrow_mob = T.eyebrow(self.eyebrow) if self.eyebrow else None
        if self._eyebrow_mob is not None:
            self._eyebrow_mob.move_to([0, LAYOUT.eyebrow_y, 0])

        self._title_mob = T.heading(self.title) if self.title else None
        if self._title_mob is not None:
            max_w = LAYOUT.content_width
            if self._title_mob.width > max_w:
                self._title_mob.scale_to_fit_width(max_w)
            self._title_mob.move_to([0, LAYOUT.title_y, 0])

        # 标题左侧的着色短条：靠左对齐到标题文字，是"这一页的色彩身份"
        self._accent_bar = None
        if self._title_mob is not None:
            bar = RoundedRectangle(
                width=LAYOUT.accent_bar_len,
                height=LAYOUT.accent_bar_width,
                corner_radius=LAYOUT.accent_bar_width / 2,
            )
            bar.set_fill(self.accent, opacity=0.95).set_stroke(width=0)
            bar.next_to(self._title_mob, LEFT, buff=0.32)
            self._accent_bar = bar

        # 旁白带：一条细分割线，衬在画面下部
        self._rule = Line(
            start=[-LAYOUT.frame_width / 2 + LAYOUT.side_margin, -2.62, 0],
            end=[LAYOUT.frame_width / 2 - LAYOUT.side_margin, -2.62, 0],
            stroke_color=INK_FAINT,
            stroke_width=1.1,
        )
        self._rule.set_opacity(0.45)

        self._branding = None
        if self.show_branding:
            brand = T.small("CG · 从 0 开始", INK_FAINT)
            # 水印放右上角，**不要**放在底部旁白带里：
            # 放底部会和字幕抢同一行，于是只能"第一句旁白出现时把水印淡出"，
            # 观众看到的就是"一行字闪一下就消失"。挪到右上角后它可以从头待到尾。
            brand.move_to(
                [
                    LAYOUT.frame_width / 2 - LAYOUT.side_margin - brand.width / 2,
                    LAYOUT.eyebrow_y,
                    0,
                ]
            )
            self._branding = brand

    def _intro(self) -> None:
        """标题动画：着色条先出现，再把文字"写"出来。

        3D 页面额外做一步：把页眉钉在屏幕上（``add_fixed_in_frame_mobjects``），
        否则相机的 ``phi/theta`` 会把标题一起"转斜"。注意必须用 ``Add`` 而不是
        ``set_opacity(0)`` 来避免提前闪出——后者会让文字永远停在 0 透明度。
        """
        anims: list[Animation] = []
        if self._accent_bar is not None:
            anims.append(GrowFromCenter(self._accent_bar))
        if self._eyebrow_mob is not None:
            anims.append(FadeIn(self._eyebrow_mob, shift=0.12 * DOWN))
        if self._title_mob is not None:
            anims.append(FadeIn(self._title_mob, shift=0.10 * DOWN))
        anims.append(FadeIn(self._rule))
        if self._branding is not None:
            anims.append(FadeIn(self._branding, shift=0.05 * UP))

        if getattr(self, "_fix_ui_in_frame", False):
            fixed = [
                m
                for m in (
                    self._accent_bar,
                    self._eyebrow_mob,
                    self._title_mob,
                    self._rule,
                    self._branding,
                )
                if m is not None
            ]
            # 先登记为"钉屏"，再在动画里加入场景——顺序反了会提前渲染出来
            self.add_fixed_in_frame_mobjects(*fixed)
            anims = [Add(m) for m in fixed]

        if anims:
            self.play(*anims, run_time=0.9, rate_func=smooth)

        # 正文与旁白之上，保证不被场景内容遮挡
        self.bring_to_front(self._rule)
        if self._branding is not None:
            self.bring_to_front(self._branding)

    def _outro(self) -> None:
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.55, rate_func=linear)

    # ------------------------------------------------------------------
    # 正文可复用的动作
    # ------------------------------------------------------------------
    def build_chrome(self) -> None:
        """把页眉与旁白带真正加进场景（``_intro`` 只是准备动画）。

        注意：多数子类不需要调用它——:meth:`say` 会自动把旁白带顶到前台。
        只有在需要"页眉先于正文出现"时才手动调用。
        """
        for m in (self._eyebrow_mob, self._title_mob, self._accent_bar, self._rule, self._branding):
            if m is not None:
                self.add(m)

    def say(
        self,
        text: str,
        *,
        emphasis: Iterable[str] = (),
        wait: float = 1.0,
        run_time: float = 0.55,
        color: str | None = None,
    ) -> None:
        """显示一句旁白，并停留 ``wait`` 秒。

        旧的旁白会自动淡出，所以一页里可以连续调用多次，形成"边讲边推进"的节奏。

        Parameters
        ----------
        emphasis
            需要高亮成暖色的子串列表，例如 ``emphasis=["3 个自由度"]``。
        wait
            字幕停留时长；配合旁白朗读速度调整。
        """
        if hasattr(self, "_caption_mob") and self._caption_mob in self.mobjects:
            self.play(FadeOut(self._caption_mob), run_time=0.18)

        t2c = {word: T.WARM for word in emphasis} if emphasis else None
        txt = T.caption(text, color or T.INK_DIM, t2c=t2c)
        max_w = LAYOUT.content_width - 1.6
        if txt.width > max_w:
            txt.scale_to_fit_width(max_w)
        txt.move_to([0, LAYOUT.caption_y, 0])

        self.bring_to_front(txt)
        self._caption_mob = txt
        if getattr(self, "_fix_ui_in_frame", False):
            # 3D 页里文字必须钉在屏幕上，否则会跟着相机一起转、变成斜的。
            # add_fixed_in_frame_mobjects 会顺带 add()，所以先把透明度压到 0，
            # 淡入结束后再恢复满不透明（否则文字会一直停在 0）。
            txt.set_opacity(0)
            self.add_fixed_in_frame_mobjects(txt)
            self.play(FadeIn(txt, shift=0.08 * UP), run_time=run_time, rate_func=smooth)
            txt.set_opacity(1)
        else:
            self.play(FadeIn(txt, shift=0.08 * UP), run_time=run_time, rate_func=smooth)
        if wait > 0:
            self.wait(wait)

    def clear_caption(self) -> None:
        """手动撤掉当前旁白（一页结束时一般不需要，:meth:`_outro` 会统一清场）。"""
        mob = getattr(self, "_caption_mob", None)
        if mob is not None and mob in self.mobjects:
            self.play(FadeOut(mob), run_time=0.2)

    def write_in(self, *mobjects, run_time: float = 0.8) -> None:
        """让一组对象依次淡入（给正文内容用，比 ``Write`` 更适合图形）。"""
        self.play(
            *[FadeIn(m, shift=0.12 * UP) for m in mobjects],
            run_time=run_time,
            rate_func=smooth,
        )


class Slide3DScene(SlideScene):
    """一页 3D 幻灯片：默认等轴机位，并把相机焦距调近，避免 3D 内容只占画面一角。

    Manim 默认 ``focal_distance = 20``，透视相机下 3D 物体在 5 单位距离处
    只放大到约 32%，看起来"缩在中间"。这里统一调成 8，并相应收窄坐标轴范围
    （见 :mod:`manimations.components.axes`），让 3D 内容撑满正文区。
    """

    camera_focal_distance: float = 8.0
    camera_phi: float = AXIS_ISOMETRIC["phi"]
    camera_theta: float = AXIS_ISOMETRIC["theta"]

    # 3D 页面的文字类 UI 必须钉在屏幕上（见 _chrome / say）
    _fix_ui_in_frame: bool = True

    def _stage(self) -> None:
        super()._stage()
        self.camera.focal_distance = self.camera_focal_distance
        self.set_camera_orientation(phi=self.camera_phi, theta=self.camera_theta)

    def orbit_to(
        self,
        phi: float,
        theta: float,
        *,
        run_time: float = 1.6,
        rate_func: Any = smooth,
    ) -> None:
        """平滑转动相机到新机位。

        用 :meth:`Scene.add_updater` 手动插值，而不是 ``MoveCamera``：
        后者一次只能改一个角度，而教学里经常需要"边升边转"的组合运动。
        """
        cam = self.camera
        phi0, theta0 = float(cam.phi), float(cam.theta)
        dphi, dtheta = float(phi) - phi0, float(theta) - theta0
        elapsed = {"t": 0.0}

        def _updater(dt: float) -> None:
            elapsed["t"] += dt
            alpha = rate_func(min(1.0, elapsed["t"] / max(run_time, 1e-6)))
            cam.phi = phi0 + alpha * dphi
            cam.theta = theta0 + alpha * dtheta

        self.add_updater(_updater)
        self.wait(run_time)
        self.remove_updater(_updater)

    def flat(self, *mobjects: Any) -> VGroup:
        """把一组 2D 内容钉到屏幕空间（不参与相机旋转，也不被透视缩小）。

        3D 页里画矩阵、公式、卡片时**一定要用它**：否则这些 2D 图形会被相机
        按 ``phi/theta`` 斜着投影出去，看起来"躺在地上"，既不美观也读不清。

        原理（``ThreeDCamera.transform_points_pre_display``）：登记到
        ``fixed_in_frame_mobjects`` 的物件会**直接跳过投影**，坐标系就是屏幕
        世界坐标（高 8.4 × 宽 14.9）。所以既不需要"贴到相机平面"，也不需要缩放，
        内容按正常 2D 坐标摆好即可。
        """
        group = VGroup(*mobjects)
        # 只登记到相机的 fixed_in_frame 集合即可：VGroup 这类容器没有
        # ``fix_in_frame()`` 方法（那是 OpenGL 渲染器的接口），Cairo 下靠登记生效。
        self.add_fixed_in_frame_mobjects(group)
        return group


__all__ = ["SlideScene", "Slide3DScene"]
