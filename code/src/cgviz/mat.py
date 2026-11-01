"""旋转矩阵、正交性、欧拉角。

本章反复要用的两个事实：

1. 一个 3×3 旋转矩阵有 9 个数，但自由旋转只有 3 个自由度。
   所以 9 个数之间必须满足 6 个约束（三列两两正交且长度为 1）。
2. 矩阵层面的"线性插值"会离开旋转矩阵的集合：插值中途的矩阵不再正交，
   几何上表现为模型被压扁。这是矩阵表示旋转的根本痛点，也是四元数出场的理由。
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "rotation_matrix_axis",
    "rotation_x",
    "rotation_y",
    "rotation_z",
    "euler_xyz",
    "orthogonality_error",
    "is_orthonormal",
    "column_vectors",
]


def _unit_axis(axis) -> np.ndarray:
    from .vec import normalize

    return normalize(axis)


def rotation_x(angle: float) -> np.ndarray:
    """绕 X 轴旋转 ``angle`` 弧度（右手系：从 +X 看向原点，逆时针为正）。"""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rotation_y(angle: float) -> np.ndarray:
    """绕 Y 轴旋转 ``angle`` 弧度。"""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def rotation_z(angle: float) -> np.ndarray:
    """绕 Z 轴旋转 ``angle`` 弧度。"""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def rotation_matrix_axis(axis, angle: float) -> np.ndarray:
    """绕任意单位轴 ``axis`` 旋转 ``angle`` 弧度的旋转矩阵（Rodrigues 公式）。

    ``R = I cosθ + sinθ [u]× + (1 - cosθ) u uᵀ``

    这个式子本身就说明了"旋转只有 3 个自由度"：轴方向 2 个（单位向量在球面上）
    + 角度 1 个。9 个数是冗余的编码，不是 9 个独立信息。
    """
    u = _unit_axis(axis)
    k = np.array(
        [[0.0, -u[2], u[1]], [u[2], 0.0, -u[0]], [-u[1], u[0], 0.0]],
        dtype=np.float64,
    )
    outer = np.outer(u, u)
    return np.eye(3) * np.cos(angle) + np.sin(angle) * k + (1.0 - np.cos(angle)) * outer


def euler_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    """欧拉角 XYZ 顺序：``R = Rz(rz) Ry(ry) Rx(rx)``（先转 X，最后转 Z）。

    注意顺序不可交换，这正是后面要讲"万向锁"的根源。
    """
    return rotation_z(rz) @ rotation_y(ry) @ rotation_x(rx)


def column_vectors(m) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """取出旋转矩阵的三列，即基向量 ``e1、e2、e3`` 旋转后的像。"""
    a = np.asarray(m, dtype=np.float64)
    return a[:, 0].copy(), a[:, 1].copy(), a[:, 2].copy()


def orthogonality_error(m) -> float:
    """衡量"离旋转矩阵有多远"：``‖RᵀR - I‖``。

    真正的旋转矩阵必须是正交阵（``RᵀR = I``），所以这个值应当接近 0。
    对两个旋转矩阵做线性插值时，这个值会在中途明显变大——那就是模型被压扁的证据。
    """
    a = np.asarray(m, dtype=np.float64)
    return float(np.linalg.norm(a.T @ a - np.eye(3)))


def is_orthonormal(m, tol: float = 1e-6) -> bool:
    """:func:`orthogonality_error` 在容差内即认为仍是旋转矩阵。"""
    return orthogonality_error(m) < tol
