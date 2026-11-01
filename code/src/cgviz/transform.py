"""仿射变换与齐次坐标：为什么 3D 里要做 4×4 的矩阵。

一个 3×3 矩阵只能表达**线性**变换（绕原点旋转、相对于轴向缩放、错切）。
平移不是线性变换——它把原点搬走了——所以塞不进 3×3。

解决办法是升一维：点用 ``(x, y, z, 1)``，向量用 ``(x, y, z, 0)``，
于是平移变成了一种"线性"的 4×4 操作。这一个 ``w`` 分量同时解释了
"为什么向量不受平移影响"和"为什么图形学管线里满是 4×4 矩阵"。

本章演示只用 2D，因为 2D 的仿射变换可以直接画在纸上；4×4 是同一套逻辑的主角升级。
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "affine2d",
    "rotation2d",
    "translate2d",
    "translate3d",
    "scale2d",
    "compose",
    "apply",
    "from_axis_angle4",
    "homogeneous4",
    "compose3d",
]


def affine2d(m: np.ndarray, t=(0.0, 0.0)) -> np.ndarray:
    """把 2×2 线性部分 ``m`` 与平移 ``t`` 打包成 3×3 齐次矩阵。"""
    a = np.asarray(m, dtype=np.float64).reshape(2, 2)
    out = np.eye(3)
    out[:2, :2] = a
    out[:2, 2] = np.asarray(t, dtype=np.float64).reshape(2)
    return out


def rotation2d(angle: float, center=None) -> np.ndarray:
    """绕 ``center``（默认原点）旋转 ``angle`` 弧度的 3×3 齐次矩阵。

    ``T(center) · R · T(-center)``——"先把物体搬到原点转，再搬回去"，
    这就是"绕任意点旋转"的全部内容，也是 :func:`compose` 存在的意义。
    """
    c, s = np.cos(angle), np.sin(angle)
    r = affine2d(np.array([[c, -s], [s, c]]))
    if center is None:
        return r
    cx, cy = float(center[0]), float(center[1])
    return compose(translate2d(cx, cy), r, translate2d(-cx, -cy))


def translate2d(dx: float, dy: float) -> np.ndarray:
    """2D 平移的 3×3 齐次矩阵。"""
    return affine2d(np.eye(2), (dx, dy))


def translate3d(dx: float, dy: float, dz: float) -> np.ndarray:
    """3D 平移的 4×4 齐次矩阵（列向量约定：``p' = M p``）。

    平移量只能待在第 4 列（``out[:3, 3]``）：前 3 列乘的是 ``x/y/z``，
    第 4 列乘的是 ``w``。点有 ``w = 1``，于是 ``p' = p + t``；
    方向有 ``w = 0``，同一列乘 0，什么也不会发生——这就是"平移不影响向量"。

    注意与文章里的写法互为**转置**：文章用行向量 ``p·M``，所以它的平移量在
    第 4 行。两者算出的坐标完全相同（``p·M = (Mᵀ p)ᵀ``），
    视频里显示文章的形式、计算走这里，:func:`apply` 与显示靠转置对齐。
    """
    out = np.eye(4)
    out[:3, 3] = [float(dx), float(dy), float(dz)]
    return out


def scale2d(sx: float, sy: float | None = None) -> np.ndarray:
    """2D 缩放；只给 ``sx`` 时为等比缩放。"""
    if sy is None:
        sy = sx
    return affine2d(np.diag([float(sx), float(sy)]))


def compose(*mats: np.ndarray) -> np.ndarray:
    """按**书写顺序**组合变换：``compose(A, B, C)`` 表示先 A、再 B、最后 C。

    数学上等价于 ``C @ B @ A``。矩阵乘法从右往左作用，这个函数帮你把
    "先做什么"写成从左往右，减少读代码时的脑内翻转。
    """
    out = np.eye(np.asarray(mats[0]).shape[0])
    for m in mats:
        out = np.asarray(m, dtype=np.float64) @ out
    return out


def apply(m: np.ndarray, p, w: float = 1.0) -> np.ndarray:
    """把齐次矩阵作用在一个点上并做透视除法（``w`` 除回去）。

    ``w=1`` 是点，受平移影响；``w=0`` 是向量（方向），只受线性部分影响。
    传入 ``w=0`` 时不要去读返回值的最后一个分量——它不是坐标。
    """
    a = np.asarray(m, dtype=np.float64)
    v = np.append(np.asarray(p, dtype=np.float64).reshape(-1), float(w))
    r = a @ v
    if r.size > 1 and abs(r[-1]) > 1e-12:
        return r[:-1] / r[-1]
    return r[:-1]


def homogeneous4(p, is_point: bool) -> np.ndarray:
    """3D 数据 → 4 维齐次坐标 ``(x, y, z, w)``。"""
    w = 1.0 if is_point else 0.0
    return np.append(np.asarray(p, dtype=np.float64).reshape(3), w)


def compose3d(*mats: np.ndarray) -> np.ndarray:
    """3D 仿射变换（4×4 齐次矩阵）的按序组合。"""
    out = np.eye(4)
    for m in mats:
        out = np.asarray(m, dtype=np.float64) @ out
    return out


def from_axis_angle4(axis, angle: float, translate=(0.0, 0.0, 0.0)) -> np.ndarray:
    """绕任意轴旋转 + 平移，打包成一个 4×4 齐次矩阵。"""
    from .mat import rotation_matrix_axis

    out = np.eye(4)
    out[:3, :3] = rotation_matrix_axis(axis, angle)
    out[:3, 3] = np.asarray(translate, dtype=np.float64).reshape(3)
    return out
