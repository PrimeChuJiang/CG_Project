"""插值：线性插值、(错误的) 矩阵插值、以及旋转的正确插值。

本模块的核心不是"提供插值函数"，而是**用可量化的证据说明为什么需要 slerp**。
视频里的那根"正交性误差"曲线，就是调用 :func:`matrix_path` 与 :func:`slerp_path` 画出来的。
"""

from __future__ import annotations

import numpy as np

from .mat import orthogonality_error
from .quat import between_rotations

__all__ = ["lerp", "matrix_path", "slerp_path", "error_curve", "sample"]

Frame = tuple[float, np.ndarray]


def lerp(a, b, t: float) -> np.ndarray:
    """标量或数组的线性插值：``a + t(b - a)``，``t ∈ [0, 1]``。"""
    return np.asarray(a) + float(t) * (np.asarray(b) - np.asarray(a))


def sample(n: int) -> np.ndarray:
    """在 ``[0, 1]`` 上取 ``n + 1`` 个均匀参数，含两端。"""
    return np.linspace(0.0, 1.0, int(n) + 1)


def matrix_path(m0, m1, n: int = 81) -> list[Frame]:
    """在两个旋转矩阵之间做**直接线性插值**（错误示范）。

    每一帧的矩阵是 ``(1-t) M0 + t M1``。它看起来"连续"，但只在两端是旋转矩阵，
    中途不再是——几何上模型会沿某个方向被压扁再弹回来。
    """
    a = np.asarray(m0, dtype=np.float64)
    b = np.asarray(m1, dtype=np.float64)
    return [(float(t), (1.0 - float(t)) * a + float(t) * b) for t in sample(n)]


def slerp_path(m0, m1, n: int = 81) -> list[Frame]:
    """在两个旋转矩阵之间做**经由四元数的球面插值**（正确做法）。

    每一帧都是货真价实的旋转矩阵，转动速度恒定。
    """
    a = np.asarray(m0, dtype=np.float64)
    b = np.asarray(m1, dtype=np.float64)
    return [(float(t), between_rotations(a, b, float(t))) for t in sample(n)]


def error_curve(path: list[Frame]) -> np.ndarray:
    """对一条矩阵路径计算每帧的正交性误差 ``‖RᵀR - I‖``。

    这是视频里那条曲线的数据来源：矩阵直插会鼓起一个峰，slerp 则贴着 0。
    """
    return np.array([orthogonality_error(m) for _, m in path], dtype=np.float64)


def max_error(path: list[Frame]) -> float:
    """整条路径上"离旋转矩阵最远"的偏离量，用于把一个概念压缩成一个数字。"""
    return float(np.max(error_curve(path)))
