from manim import *
import os
os.environ["PATH"] += os.pathsep + r"C:\Program Files\MiKTeX\miktex\bin\x64"

class MathVectorTransform3D(ThreeDScene):
    def construct(self):
        # 1. 创建并添加 3D 坐标轴
        axes = ThreeDAxes()
        # 调整看进去的 3D 视角
        self.set_camera_orientation(phi=75 * DEGREES, theta=-45 * DEGREES)
        self.add(axes)

        # 2. 调用 MiKTeX 渲染 LaTeX 矩阵公式
        matrix_text = MathTex(
            r"M = \begin{bmatrix} 0 & -1 & 0 \\ 2 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}",
            color=YELLOW
        ).to_corner(UL)
        
        # 将文本固定在屏幕图层上
        self.add_fixed_in_frame_mobjects(matrix_text)
        self.play(Write(matrix_text))

        # 3. 创建初始向量 v1 = [1, 1, 2]（蓝色）
        v1 = Vector([1, 1, 2], color=BLUE)
        v1_label = MathTex(r"\vec{v}_1", color=BLUE).next_to(v1.get_end(), UR)
        
        # 播放向量生长和标签写入的动画
        self.play(GrowArrow(v1), Write(v1_label))
        self.wait(1)

        # 4. 定义变换矩阵 M
        M = np.array([
            [0, -1, 0],
            [2, 0, 0],
            [0,  0, 1]
        ])

        # 5. 让向量随着矩阵连续空间弯曲飞过去
        self.play(
            v1.animate.apply_matrix(M),
            v1_label.animate.move_to(axes.c2p(-1, 2, 2) + UR), 
            run_time=3 
        )
        self.wait(2)
