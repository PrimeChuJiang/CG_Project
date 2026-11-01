"""四元数：用 4 个数表示旋转，附带球面线性插值 (slerp)。

约定：四元数存为 ``(w, x, y, z)``，``w`` 是标量部。单位四元数
``q = w + x i + y j + z k`` 与旋转矩阵一一对应（双覆盖：``q`` 与 ``-q`` 是同一次旋转）。

为什么 4 个数比 9 个数好？不是因为数字少，而是因为**约束是简单的**：
单位四元数只需要 ``w²+x²+y²+z² = 1``（活在一个 3 维球面 S³ 上），
插值时沿着球面走就不会"离开合法旋转的集合"。矩阵插值做不到这一点。
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "from_axis_angle",
    "from_matrix",
    "to_matrix",
    "normalize",
    "conjugate",
    "mul",
    "angle",
    "slerp",
    "between_rotations",
    "axis_angle_of",
    "Quat",
]

Quat = np.ndarray


def from_axis_angle(axis, angle: float) -> Quat:
    """轴角 → 单位四元数：``q = (cos(θ/2), sin(θ/2)·u)``。

    为什么是 **θ/2** 而不是 θ？因为四元数旋转是"双侧"作用 ``q v q*``，
    两侧各贡献一半角度。这也是"四元数要转两圈才回到原位"（720° 周期）的来源。
    """
    from .vec import normalize

    u = normalize(axis)
    s = np.sin(angle / 2.0)
    return np.array([np.cos(angle / 2.0), u[0] * s, u[1] * s, u[2] * s], dtype=np.float64)


def normalize(q) -> Quat:
    """归一化到单位球面 S³。反向旋转/插值误差都可能让它离开球面。"""
    a = np.asarray(q, dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(a))
    if n == 0.0:
        raise ValueError("四元数 (0,0,0,0) 无法归一化")
    return a / n


def conjugate(q) -> Quat:
    """共轭：``(w, -x, -y, -z)``。对单位四元数来说共轭就是逆，代表反向旋转。"""
    a = np.asarray(q, dtype=np.float64)
    return np.array([a[0], -a[1], -a[2], -a[3]], dtype=np.float64)


def mul(a, b) -> Quat:
    """四元数乘法（Hamilton 积）。**不满足交换律**：先 A 后 B ≠ 先 B 后 A。"""
    aw, ax, ay, az = np.asarray(a, dtype=np.float64)
    bw, bx, by, bz = np.asarray(b, dtype=np.float64)
    return np.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=np.float64,
    )


def angle(q) -> float:
    """该四元数对应的旋转角（弧度）。用 2·atan2(|向量部|, w) 更稳，避免 arccos 在
    接近 ±1 处的数值不稳。"""
    w = float(np.clip(q[0], -1.0, 1.0))
    v = float(np.linalg.norm(np.asarray(q[1:], dtype=np.float64)))
    return 2.0 * float(np.arctan2(v, w))


def to_matrix(q) -> np.ndarray:
    """单位四元数 → 3×3 旋转矩阵。"""
    w, x, y, z = normalize(q)
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def from_matrix(m) -> Quat:
    """3×3 旋转矩阵 → 单位四元数（Shepperd 分支法，数值上比公式直算稳）。

    四个分支里选 |w|、|x|、|y|、|z| 最大的一支做除法，避免除以接近 0 的量。
    """
    r = np.asarray(m, dtype=np.float64)
    trace = float(r[0, 0] + r[1, 1] + r[2, 2])
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0  # s = 4w
        w = 0.25 * s
        x = (r[2, 1] - r[1, 2]) / s
        y = (r[0, 2] - r[2, 0]) / s
        z = (r[1, 0] - r[0, 1]) / s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2.0  # s = 4x
        w = (r[2, 1] - r[1, 2]) / s
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / s
        z = (r[0, 2] + r[2, 0]) / s
    elif r[1, 1] > r[2, 2]:
        s = np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2.0  # s = 4y
        w = (r[0, 2] - r[2, 0]) / s
        x = (r[0, 1] + r[1, 0]) / s
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / s
    else:
        s = np.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2.0  # s = 4z
        w = (r[1, 0] - r[0, 1]) / s
        x = (r[0, 2] + r[2, 0]) / s
        y = (r[1, 2] + r[2, 1]) / s
        z = 0.25 * s
    return normalize(np.array([w, x, y, z], dtype=np.float64))


def slerp(q0, q1, t: float) -> Quat:
    """球面线性插值：在 S³ 上沿大圆弧匀速前进。

    实现要点：

    1. 取 ``dot`` 的绝对值并翻转 ``q1``，保证走**短弧**——``q`` 与 ``-q`` 是同一个旋转，
       不处理会绕远路（转 350° 而不是 10°）。
    2. ``dot`` 接近 1 时两四元数几乎重合，``sin(ω)`` 会趋于 0 导致除零，
       此时退化为线性插值（两者已无区别）。
    """
    a = normalize(q0)
    b = normalize(q1)
    d = float(np.dot(a, b))
    if d < 0.0:
        b = -b
        d = -d
    d = min(1.0, max(-1.0, d))
    if d > 0.9995:
        return normalize(a + (b - a) * float(t))
    omega = np.arccos(d)
    sin_omega = np.sin(omega)
    wa = np.sin((1.0 - float(t)) * omega) / sin_omega
    wb = np.sin(float(t) * omega) / sin_omega
    return wa * a + wb * b


def between_rotations(m0, m1, t: float) -> np.ndarray:
    """两个旋转矩阵之间的 slerp：矩阵 → 四元数 → 球面插值 → 矩阵。

    这是"用四元数做旋转插值"的最短实用路径，视频里对比的就是它和矩阵直插的区别。
    """
    return to_matrix(slerp(from_matrix(m0), from_matrix(m1), t))


def axis_angle_of(q) -> tuple[np.ndarray, float]:
    """单位四元数 → (单位轴, 角度)。角度为 0 时轴无定义，回退到 +Z。"""
    a = normalize(q)
    ang = angle(a)
    s = np.linalg.norm(a[1:])
    if s < 1e-12:
        return np.array([0.0, 0.0, 1.0]), 0.0
    return a[1:] / s, ang
