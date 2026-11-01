"""cgviz —— 计算机图形学算法核。

这里的每个函数都是"可被可视化的真相来源"（single source of truth）：
博客里推导的公式在这里有一份可执行实现，Manim 动画调用同一份实现，
因此视频里看到的图形与实际算法结果永远一致。

模块地图
--------
vec        : 点与向量、点积、叉积、长度、归一化、夹角
mat        : 旋转矩阵、正交性检查、欧拉角
quat       : 四元数及其与旋转矩阵的互转、球面线性插值 (slerp)
interp     : 线性插值、矩阵插值（以及它为什么坏）、slerp 路径采样
transform  : 2D/3D 仿射变换、齐次坐标、组合变换
"""

from . import interp, mat, quat, transform, vec

__all__ = ["vec", "mat", "quat", "interp", "transform"]
