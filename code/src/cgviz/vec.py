"""点、向量与它们之间的运算。

图形学里第一件容易混淆的事：**点（point）和向量（vector）不是同一种东西**。

* 向量表示"方向 + 长度"，没有位置；它能平移、缩放、相加，但**不能**被当作位置来平移。
* 点表示空间中的一个位置；它没有"长度"，两点相减得到的是向量。

在第 0 章我们只需要一条规则：*两点之差是向量，向量不能和点相加得到点。*
真正把两者统一起来的是齐次坐标（见 :mod:`cgviz.transform`）：给向量补 0，给点补 1。
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "as_vec3",
    "add",
    "sub",
    "scale",
    "dot",
    "cross",
    "length",
    "normalize",
    "angle_between",
    "deg",
    "homogeneous",
]


def as_vec3(v) -> np.ndarray:
    """把任意长度 ≤3 的序列补成 float64 的 3 维向量 ``(x, y, z)``。"""
    arr = np.asarray(v, dtype=np.float64).reshape(-1)
    if arr.size > 3:
        raise ValueError(f"期望至多 3 个分量，收到 {arr.size} 个")
    out = np.zeros(3, dtype=np.float64)
    out[: arr.size] = arr
    return out


def add(a, b) -> np.ndarray:
    """向量 + 向量 = 向量。"""
    return as_vec3(a) + as_vec3(b)


def sub(a, b) -> np.ndarray:
    """差：**点 - 点 = 向量**，向量 - 向量 = 向量。

    这是"点与向量不同"的直接后果：两个位置相减，得到的是从 b 指向 a 的位移。
    """
    return as_vec3(a) - as_vec3(b)


def scale(v, s: float) -> np.ndarray:
    """数乘：只改变长度与朝向，不改变"位置"（向量本来就没有位置）。"""
    return as_vec3(v) * float(s)


def dot(a, b) -> float:
    """点积。几何意义：``|a||b|cosθ``，也就是 b 在 a 方向上的投影长度乘 |a|。"""
    return float(np.dot(as_vec3(a), as_vec3(b)))


def cross(a, b) -> np.ndarray:
    """叉积。结果垂直于 a、b，长度等于两者张成的平行四边形面积。"""
    return np.cross(as_vec3(a), as_vec3(b))


def length(v) -> float:
    """向量长度（欧几里得范数）。"""
    return float(np.linalg.norm(as_vec3(v)))


def normalize(v) -> np.ndarray:
    """单位化。零向量无法单位化，这里显式报错而不是悄悄返回 NaN。"""
    n = length(v)
    if n == 0.0:
        raise ValueError("零向量没有方向，无法归一化")
    return as_vec3(v) / n


def angle_between(a, b) -> float:
    """两向量夹角，单位**弧度**。用 ``|a·b| / (|a||b|)`` 再做 clamp，
    避免浮点误差让 arccos 收到 1.0000000002 而报错。"""
    denom = length(a) * length(b)
    if denom == 0.0:
        raise ValueError("零向量没有夹角")
    c = max(-1.0, min(1.0, dot(a, b) / denom))
    return float(np.arccos(c))


def deg(radians: float) -> float:
    """弧度转角度，方便在讲解里显示人类可读的数字。"""
    return float(np.degrees(radians))


def homogeneous(v, is_point: bool) -> np.ndarray:
    """把 3 维数据升到齐次坐标 ``(x, y, z, w)``。

    ``w = 1`` → 点，会被平移影响；``w = 0`` → 向量，平移对它无效。
    这一个数字就是"点与向量"分家的全部秘密。
    """
    w = 1.0 if is_point else 0.0
    return np.append(as_vec3(v), w)
