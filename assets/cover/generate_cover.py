"""CG_Project 计划封面：一张 16:9 的"技术海报"，所有几何都由真实的投影算出来。

为什么不用 PS 拼一张：封面要能和成片、文章放在一起不违和，所以配色、字体、
安全区全部复用 ``manimations``；画面里的立方体是 ``cgviz`` 的旋转矩阵 + 一台
真实的透视相机投影出来的，改一个机位参数，整张图的透视会一致地跟着变。

渲染（交付 1920×1080）：

    .venv/Scripts/python -m manim render -s -r 1920,1080 --format png \
        --media_dir cover/build assets/cover/generate_cover.py ProjectCover

产物在 ``cover/build/images/generate_cover/ProjectCover_*.png``，
再复制成 ``cover/cg_project_cover.png`` 作为交付图。
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from manim import (
    DEGREES,
    DOWN,
    ORIGIN,
    RIGHT,
    UP,
    Arrow,
    Dot,
    ImageMobject,
    Line,
    Polygon,
    RESAMPLING_ALGORITHMS,
    RoundedRectangle,
    Scene,
    Text,
    VGroup,
)

from cgviz import mat
from manimations import typography as T
from manimations.theme import (
    BG,
    COOL,
    CORE,
    GOOD,
    INK,
    INK_DIM,
    INK_FAINT,
    WARM,
)

# --------------------------------------------------------------------------
# 画幅与版式
# --------------------------------------------------------------------------
FRAME_H = 8.4
FRAME_W = FRAME_H * 16.0 / 9.0
X0 = -6.42  # 左侧文字栏的左边界
TEXT_TOP = 3.34

CUBE_HALF = 0.85
CUBE_CENTER_Z = CUBE_HALF
CUBE_YAW = 16 * DEGREES
CUBE_ROT = mat.rotation_z(CUBE_YAW)


# --------------------------------------------------------------------------
# 透视相机：一台"在看立方体"的针孔相机，投影到 2D 画布
# --------------------------------------------------------------------------
class View:
    """把世界坐标投影到 Manim 的 2D 世界坐标（y 向上）。

    相机放在 ``forward * dist`` 的方向上，看向原点；``pitch`` 是俯角。
    用 ``focal / (dist - depth)`` 做透视除法，所以近处大、远处小——
    地板网格的灭点也就自然出现了，不用手摆。
    """

    def __init__(
        self,
        *,
        yaw: float = 45 * DEGREES,
        pitch: float = 25 * DEGREES,
        dist: float = 14.0,
        focal: float = 13.2,
        zoom: float = 1.58,
        anchor_world: tuple[float, float, float] = (0.0, 0.0, CUBE_CENTER_Z),
        anchor_screen: tuple[float, float] = (3.52, 0.62),
    ) -> None:
        cy, sy = np.cos(yaw), np.sin(yaw)
        cp, sp = np.cos(pitch), np.sin(pitch)
        self.right = np.array([-sy, cy, 0.0])
        self.up = np.array([-sp * cy, -sp * sy, cp])
        self.forward = np.array([cp * cy, cp * sy, sp])
        self.dist = dist
        self.focal = focal
        self.zoom = zoom
        self.anchor_world = np.array(anchor_world, dtype=float)
        self.anchor_screen = np.array([*anchor_screen, 0.0], dtype=float)

    def depth(self, points: np.ndarray) -> np.ndarray:
        return np.atleast_2d(points) @ self.forward

    def project(self, points) -> np.ndarray:
        p = np.atleast_2d(np.asarray(points, dtype=float)) - self.anchor_world
        s = self.focal / (self.dist - p @ self.forward)
        xy = np.stack([p @ self.right, p @ self.up], axis=1) * (self.zoom * s)[:, None]
        xy = xy + self.anchor_screen[:2]
        # Manim 的 Mobject 点坐标是三维的；z 统一给 0，表示"已经投到屏幕平面"。
        return np.column_stack([xy, np.zeros(len(xy))])


VIEW = View()
CAMERA_POS = VIEW.forward * VIEW.dist


# --------------------------------------------------------------------------
# 位图：背景、压暗、辉光、暗角（Manim 的矢量层画不出柔和渐变，用 numpy 生成）
# --------------------------------------------------------------------------
def _smoothstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _rgba(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    arr = np.empty((*alpha.shape, 4), dtype=np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    arr[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return arr


def _background(w: int = 1920, h: int = 1080) -> np.ndarray:
    """深色底 + 两团极淡的光。中心偏右偏蓝，左下偏暖，避免大面积死黑。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    u = xx / (w - 1)
    v = yy / (h - 1)

    base = np.array([14, 17, 22], dtype=float)
    top = np.array([20, 26, 34], dtype=float)
    img = base + (top - base) * ((1.0 - v) ** 1.5)[..., None]

    def glow(cx: float, cy: float, radius: float, amp: float, color: tuple[int, int, int]) -> None:
        nonlocal img
        d2 = ((u - cx) ** 2 + ((v - cy) * h / w) ** 2) / (radius**2)
        img = img + (amp * np.exp(-d2))[..., None] * np.array(color, dtype=float)

    glow(0.74, 0.44, 0.40, 0.13, (76, 201, 240))  # 立方体后面的冷光
    glow(0.76, 0.46, 0.18, 0.10, (76, 201, 240))  # 再叠一层窄的，边缘更亮
    glow(0.15, 0.92, 0.34, 0.05, (255, 183, 3))  # 左下一点点暖

    # 暗角：四角压暗，把视线推回中间
    r = np.sqrt(((u - 0.5) * 1.15) ** 2 + ((v - 0.5) * 0.9) ** 2) / 0.72
    img = img * (1.0 - 0.42 * np.clip(r, 0, 1) ** 2)[..., None]

    rng = np.random.default_rng(7)
    img = img + rng.normal(0.0, 0.7, (h, w, 1))
    return _rgba(img, np.ones((h, w)))


def _radial_glow(size: int = 960, color: tuple[int, int, int] = (76, 201, 240), amp: float = 0.30) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    r = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    alpha = amp * np.exp(-(r / 0.55) ** 2)
    img = np.tile(np.array(color, dtype=float), (size, size, 1))
    return _rgba(img, alpha)


def _vignette(w: int = 1920, h: int = 1080) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    u, v = xx / (w - 1), yy / (h - 1)
    r = np.sqrt(((u - 0.5) * 1.1) ** 2 + ((v - 0.5) * 0.92) ** 2) / 0.68
    alpha = 0.55 * np.clip(r, 0, 1) ** 2.2
    return _rgba(np.zeros((h, w, 3)), alpha)


def _image(arr: np.ndarray, width: float, height: float, center=ORIGIN) -> ImageMobject:
    img = ImageMobject(arr)
    img.set_width(width).set_height(height).move_to(center)
    img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["bicubic"])
    return img


# --------------------------------------------------------------------------
# 地板网格：三维直线在透视下仍是直线，所以只投两端点。
# 画成位图而不是矢量，是为了把"文字区不上网格"做成一张连续的 alpha 蒙版：
# 矢量线做不到沿一条软边淡出，只能整条一起透明。
# --------------------------------------------------------------------------
def _floor_grid_image(view: View, w: int = 1920, h: int = 1080, ss: int = 2) -> np.ndarray:
    W, H = w * ss, h * ss
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def to_px(p: np.ndarray) -> tuple[float, float]:
        return (
            (p[0] + FRAME_W / 2) / FRAME_W * W,
            (FRAME_H / 2 - p[1]) / FRAME_H * H,
        )

    span = 12.0
    step = 0.8
    for c in np.arange(-span, span + 1e-9, step):
        major = abs(c % 4.0) < 1e-6
        opacity = 0.26 if major else 0.13
        width = (3.0 if major else 2.1) * ss
        for p0, p1 in (
            ([c, -span, 0.0], [c, span, 0.0]),
            ([-span, c, 0.0], [span, c, 0.0]),
        ):
            a, b = view.project([p0, p1])
            pa, pb = to_px(a), to_px(b)
            # 先画一层宽的淡线当辉光，再画细的实线
            draw.line([pa, pb], fill=(92, 102, 114, int(255 * opacity * 0.30)), width=10 * ss)
            draw.line([pa, pb], fill=(92, 102, 114, int(255 * opacity)), width=int(width))

    arr = np.array(layer).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    u = xx / (W - 1)
    v = yy / (H - 1)
    wx = (u - 0.5) * FRAME_W
    wy = (0.5 - v) * FRAME_H
    # 文字区（左侧）彻底让开；离立方体越远越淡，网格就不会铺满整张图
    fade = _smoothstep(-0.6, 1.3, wx)
    fade *= 1.0 - 0.30 * _smoothstep(6.0, 11.0, np.sqrt((wx - 3.5) ** 2 + (wy - 0.5) ** 2))
    arr[..., 3] *= fade

    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    return np.array(out)


# --------------------------------------------------------------------------
# 立方体：12 条棱按深度调透明度，可见面按法线剔除
# --------------------------------------------------------------------------
def _cube(view: View) -> VGroup:
    h = CUBE_HALF

    def corner(sx: float, sy: float, z: float) -> np.ndarray:
        """立方体先绕 Z 转 16°：这条旋转来自 cgviz，不是手掰的透视。"""
        return CUBE_ROT @ np.array([sx * h, sy * h, z], dtype=float)

    verts = np.array(
        [corner(sx, sy, z) for z in (0.0, 2 * h) for sy in (-1, 1) for sx in (-1, 1)]
    )
    screen = view.project(verts)
    depths = view.depth(verts)
    d_lo, d_hi = depths.min(), depths.max()

    group = VGroup()

    # --- 可见面：法线朝向相机的面才填色，面本身几乎透明，只给一点点体积感
    faces = [
        ((1, 0, 0), [corner(h, -h, 0), corner(h, h, 0), corner(h, h, 2 * h), corner(h, -h, 2 * h)]),
        ((-1, 0, 0), [corner(-h, -h, 0), corner(-h, -h, 2 * h), corner(-h, h, 2 * h), corner(-h, h, 0)]),
        ((0, 1, 0), [corner(-h, h, 0), corner(-h, h, 2 * h), corner(h, h, 2 * h), corner(h, h, 0)]),
        ((0, -1, 0), [corner(-h, -h, 0), corner(h, -h, 0), corner(h, -h, 2 * h), corner(-h, -h, 2 * h)]),
        ((0, 0, 1), [corner(-h, -h, 2 * h), corner(h, -h, 2 * h), corner(h, h, 2 * h), corner(-h, h, 2 * h)]),
        ((0, 0, -1), [corner(-h, -h, 0), corner(-h, h, 0), corner(h, h, 0), corner(h, -h, 0)]),
    ]
    visible = []
    for normal, corners in faces:
        n = CUBE_ROT @ np.array(normal, dtype=float)
        c = np.mean(corners, axis=0)
        if n @ (CAMERA_POS - c) > 0:
            visible.append((c @ view.forward, n, corners))
    for depth, normal, corners in sorted(visible):
        pts = view.project(corners)
        # 顶面最亮、侧面稍暗，法线的 z 分量决定这一点
        opacity = 0.06 + 0.05 * max(0.0, float(normal[2]))
        group.add(Polygon(*pts, stroke_width=0, fill_color=CORE, fill_opacity=opacity))

    # --- 棱：远的细暗、近的粗亮；每条都叠一层宽而淡的"辉光"
    # 注意：判据必须用**旋转前**的整数坐标。绕 Z 转 16° 之后，沿 x/y 的棱
    # 在 x、y 两个分量上都变了，按"只差一个分量"筛会只剩 4 条竖棱。
    base = [
        (sx, sy, z)
        for z in (0.0, 2 * h)
        for sy in (-1, 1)
        for sx in (-1, 1)
    ]
    edges = [
        (i, j)
        for i in range(8)
        for j in range(i + 1, 8)
        if sum(a != b for a, b in zip(base[i], base[j])) == 1
    ]
    for a, b in edges:
        d = 0.5 * (depths[a] + depths[b])
        t = (d - d_lo) / (d_hi - d_lo)
        t = float(np.clip(t, 0.0, 1.0))
        p0, p1 = screen[a], screen[b]
        group.add(
            Line(p0, p1, stroke_color=CORE, stroke_width=9.0).set_stroke(opacity=0.05 + 0.05 * t)
        )
        group.add(
            Line(p0, p1, stroke_color=CORE, stroke_width=2.4).set_stroke(opacity=0.16 + 0.80 * t**1.35)
        )

    # --- 顶点：近处亮、远处弱，让画面有"对焦"的感觉
    for i, p in enumerate(screen):
        t = float(np.clip((depths[i] - d_lo) / (d_hi - d_lo), 0.0, 1.0))
        group.add(Dot(p, radius=0.032 + 0.012 * t, color=CORE).set_opacity(0.35 + 0.6 * t))

    return group


# --------------------------------------------------------------------------
# 文字
# --------------------------------------------------------------------------
def _cjk(content: str, height: float, color: str = INK, weight: str = "BOLD", **kwargs) -> Text:
    t = Text(content, font=T.CJK_FONT, weight=weight, color=color, font_size=48, **kwargs)
    t.scale_to_fit_height(height)
    return t


def _mono(content: str, height: float, color: str = INK, weight: str = "NORMAL") -> Text:
    t = Text(content, font=T.MONO_FONT, weight=weight, color=color, font_size=48)
    t.scale_to_fit_height(height)
    return t


def _left(mob, x: float, y: float):
    mob.move_to([x + mob.width / 2, y, 0])
    return mob


def _brand() -> VGroup:
    name = _mono("CG_Project", 0.36, CORE, weight="BOLD")
    name.move_to([X0 + name.width / 2, TEXT_TOP, 0])
    sep = Line([0, 0, 0], [0, 0.30, 0], stroke_color=INK_FAINT, stroke_width=1.0)
    sep.set_stroke(opacity=0.55)
    sep.next_to(name, RIGHT, buff=0.26)
    sep.align_to(name, UP).shift(DOWN * 0.03)
    tag = _cjk("学习计划", 0.25, INK_DIM, weight="MEDIUM")
    tag.next_to(sep, RIGHT, buff=0.24)
    tag.align_to(name, DOWN)
    return VGroup(name, sep, tag)


def _headline() -> VGroup:
    line1 = _cjk("从 0 开始", 1.0, INK, t2c={"0": WARM})
    line2 = _cjk("学计算机图形学", 1.0, INK)
    line1.move_to([X0 + line1.width / 2, 1.78, 0])
    line2.move_to([X0 + line2.width / 2, 0.70, 0])
    return VGroup(line1, line2)


def _body_copy() -> VGroup:
    rule = Line([X0, 0, 0], [X0 + 2.9, 0, 0], stroke_color=WARM, stroke_width=2.6)
    rule.set_stroke(opacity=0.95)
    rule.move_to([X0 + 1.45, -0.34, 0])

    parts = []
    for i, word in enumerate(("scratchapixel", "OpenGL", "Unreal")):
        parts.append(_mono(word, 0.27, INK_DIM))
        if i < 2:
            parts.append(_mono("→", 0.27, CORE))
    road = VGroup(*parts).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
    _left(road, X0, -1.02)
    return VGroup(rule, road)


# --------------------------------------------------------------------------
# 右下角：一个建模软件式的 XYZ 小坐标针
# --------------------------------------------------------------------------
def _axis_gizmo(view: View) -> VGroup:
    # 这里的 (x, y) 是**屏幕坐标**；只有方向向量走一次投影，才能和立方体的机位一致。
    origin = np.array([5.62, -2.46, 0.0])
    base = view.project([[0.0, 0.0, 0.0]])[0]
    group = VGroup()
    for name, vec, color in (
        ("x", [1.0, 0.0, 0.0], CORE),
        ("y", [0.0, 1.0, 0.0], GOOD),
        ("z", [0.0, 0.0, 1.0], COOL),
    ):
        d = view.project([vec])[0] - base
        d = d / np.linalg.norm(d)
        tip = origin + d * 0.72
        group.add(
            Arrow(
                origin,
                tip,
                buff=0,
                color=color,
                stroke_width=2.0,
                tip_length=0.11,
                max_tip_length_to_length_ratio=0.4,
            )
        )
        label = _mono(name, 0.17, color)
        label.move_to(tip + d * 0.17)
        group.add(label)
    group.add(Dot(origin, radius=0.035, color=INK_DIM))
    return group


# --------------------------------------------------------------------------
# 场景
# --------------------------------------------------------------------------
class ProjectCover(Scene):
    """静态封面：不播动画，直接铺满一帧（用 ``-s`` 出最后一张）。"""

    def construct(self) -> None:
        # 注意：Scene.frame_width / frame_height 在这个 Manim 版本里只是普通属性，
        # 不会传到相机；真正决定坐标映射的是 camera 上的这两个字段。
        self.camera.frame_width = FRAME_W
        self.camera.frame_height = FRAME_H
        self.camera.background_color = BG

        self.add(_image(_background(), FRAME_W, FRAME_H))
        self.add(_image(_floor_grid_image(VIEW), FRAME_W, FRAME_H))
        self.add(
            _image(
                _radial_glow(amp=0.13),
                7.2,
                7.2,
                center=VIEW.anchor_screen,
            )
        )
        self.add(_cube(VIEW))
        self.add(_image(_vignette(), FRAME_W, FRAME_H))

        self.add(_brand())
        self.add(_headline())
        self.add(_body_copy())
        self.add(_axis_gizmo(VIEW))

        frame = RoundedRectangle(
            width=FRAME_W - 0.62,
            height=FRAME_H - 0.62,
            corner_radius=0.16,
            stroke_color=INK_FAINT,
            stroke_width=1.0,
        )
        frame.set_stroke(opacity=0.16)
        self.add(frame)
