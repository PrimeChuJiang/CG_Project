# cgviz

计算机图形学算法核。博客里推导的公式在这里有一份可执行实现，Manim 动画调用**同一份**实现，
所以视频里看到的几何图形与实际算出来的数字永远一致。

```python
from cgviz import quat, interp, mat

m0 = mat.rotation_z(0.0)
m1 = mat.rotation_z(1.2)

interp.max_error(interp.matrix_path(m0, m1))  # ≈ 0.55，矩阵直插中途离开了旋转矩阵集合
interp.max_error(interp.slerp_path(m0, m1))   # ≈ 1e-16，始终是合法旋转
```

| 模块 | 内容 | 对应视频 |
| --- | --- | --- |
| `vec` | 点与向量、点积、叉积、齐次坐标 `w` | 01 点与向量 |
| `mat` | 绕轴旋转矩阵、欧拉角、正交性误差 | 03 旋转矩阵与万向锁 |
| `quat` | 四元数、互转、slerp | 05 四元数 |
| `interp` | 线性插值、矩阵插值（错误示范）、slerp 路径 | 04 插值 |
| `transform` | 2D/3D 仿射变换、齐次坐标、组合变换 | 02 仿射变换 |

`code/openGL-练习/` 是留给我自己写 OpenGL 练习的地方，不属于本包。
