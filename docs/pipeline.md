# 工作流：一篇文章怎么变成一部片子

这篇文档讲"日常怎么用这个工程"。只想先跑起来，看根目录 `README.md` 的「快速开始」；
想自己加一集、改版式、或者想知道某些反直觉的坑，再读这里。

## 一、日常循环（五步）

```
① 你写文章            blog/01-数学基础/01-01-points.md
② 建分镜骨架          video/01-数学基础/01-01-points.py   ← 复制 demo 的结构
③ 编码区补算法        code/src/cgviz/vec.py               ← 缺什么补什么
④ 静态检查 + 抽帧调版式  dsh lint / dsh stills
⑤ 确认后才整片渲        dsh render --quality final
```

③ 的规矩：**如果分镜里需要一个数字或一条曲线，而这个数字不是 `cgviz` 算出来的，
就先停下来去补 `cgviz`。** 这条规矩是整个工程能长期不自相矛盾的原因。

④ 的规矩：**不要在没看过画面的情况下渲整片。** 一页 20 秒的片子要画 600 帧，
改完一个标签位置就重渲一次，时间全浪费在等上面。

## 二、一页幻灯片的结构

`SlideScene` 把一页的生命周期写死，子类只填 `build()`：

```
_stage()   背景网点、画幅、3D 机位与焦距
_chrome()  小标题、主标题、左侧着色条、旁白分割线、右下水印
_intro()   标题入场（0.9 秒）
build()    ← 你写的正文
_outro()   整体淡出（0.55 秒）
```

写一页 = 声明四个属性 + 实现 `build()`：

```python
from manimations import SlideScene, typography as T
from manimations.components import Equation
from manimations.theme import GOOD

class MySlide(SlideScene):
    eyebrow = "01 · 向量"          # 标题上方的小字
    title = "点减点，为什么得到向量？"
    accent = GOOD                  # 标题左侧着色条的颜色

    def build(self) -> None:
        eq = Equation(r"\vec{v} = P_1 - P_0", note="两点之差是一个方向")
        eq.move_to([0, 0.5, 0])
        self.write_in(eq)
        self.say("位置相减，留下的不是位置，是位移。", wait=2.0)
```

`say()` 做三件事：淡出上一句旁白、在底部带显示新旁白、按 `wait` 停留。
一页里可以连续调用，形成"边讲边推进"的节奏。

## 三、3D 页面：两个必须记住的机制

### 1. 文字不会自动钉屏

`ThreeDScene` 里 `self.add()` 的物件**仍然会跟着相机 `phi/theta` 一起倾斜**。
所以你往 3D 页里放标题、标签、读数，必须显式登记：

```python
label = T.small("正交基", CORE).move_to([0, 2.2, 0])
self.add_fixed_in_frame_mobjects(label)
```

基类已经替你处理了页眉与旁白（`:meth:`SlideScene.say`` 内部会判断
`_fix_ui_in_frame`），但**正文里自己加的文字要自己钉**。

### 2. 钉屏之后，坐标系就是屏幕空间

`ThreeDCamera.transform_points_pre_display` 对登记过的物件**直接跳过投影**，
所以它们按普通 2D 坐标（画幅 8.4 × 14.9）摆放即可——不需要"贴到相机平面"，
也不需要额外缩放。基类把它包成了 `flat()`：

```python
board = self.flat(grid, formula, caption)   # 全部钉屏
board.save_state()
self.play(Add(board))
```

3D 页里画矩阵、公式、卡片时**一定要用它**，否则这些 2D 图形会被相机斜着投影出去，
看起来"躺在地上"，既不美观也读不清。

## 四、构图约束（数值版）

| 区域 | y 范围 | 放什么 |
| --- | --- | --- |
| 页眉 | 3.0 – 3.8 | 小标题 + 主标题（自动排版） |
| 正文 | **-2.3 – 2.2** | 几何、公式、卡片；左右安全边距 0.9 |
| 旁白 | -3.4 | `say()` 专用 |

**几何要先算再画。** 最典型的一次翻车：让房子绕远处的点旋转 55°，
结果它被抬高了 4 个单位、直接穿过标题。这不是手滑，是几何必然——

> 绕距离 `r` 的旋转中心转 `θ`，点会沿半径 `r` 的圆弧移动，
> 纵向最大抬升约 `r·sin θ`。正文带只有 4.5 个单位高，
> 所以 `r·sinθ > 2` 基本就会顶出画面。

改这种动画前，先用几行 numpy 把关键位置算一遍（本项目的做法见
`video/00-学习路线/demo_why_interpolation.py` 里 `Demo02` 的注释），
不要靠改了再看。

## 五、快速看画面：`stills` 与 `frames`

```bash
# 按"第几个动画之后"截图（推荐：改完立刻看）
python -m manimations stills demo_why_interpolation --scene Demo03_DegreesOfFreedom -n 6 14 24

# 更好：拼成一张联系表，用一张图验收多帧（并排还能看出对齐/错位问题）
python -m manimations sheet demo_why_interpolation --scene Demo03_DegreesOfFreedom -n 6 14 24

# 从已经渲好的成片里按秒抽帧
python -m manimations frames Demo05_MatInterp -t 6.9 12.3
```

两者的差别很重要：

* `stills` 直接跑场景到指定动画处，**不需要先有视频**，但要重跑前面的动画；
* `frames` 从 mp4 里抽，几乎瞬间，但只对已经渲过的内容有效。

两个反直觉的点：

* **`manim -s` 出的是最后一帧**，而每页结尾都会淡出，所以拿到的往往是黑图。
  检查画面一律用上面两条命令。
* `stills` 并没有真正"跳过"前面的动画——Manim 仍然逐帧推进状态，只是不编码视频。
  所以它省的是编码时间（以及一次只出一张图的磁盘），不是绘图时间。
  一页 20 秒的片子，抽一张靠后的帧仍可能要十几秒。

## 六、算法核 ↔ 动画的对应

`code/src/cgviz/` 的每个函数都假设"结果会被画出来"，所以返回数值而不是打印：

| 想要画面上的东西 | 调这个 | 返回 |
| --- | --- | --- |
| 正交性误差曲线 | `cgviz.interp.error_curve(path)` | `np.ndarray` |
| 一组插值矩阵 | `cgviz.interp.slerp_path(m0, m1)` | `[(t, 3×3), …]` |
| 基向量转到哪了 | `cgviz.mat.rotation_matrix_axis(axis, θ) @ e_k` | 3 维向量 |
| 变换顺序的差异 | `cgviz.transform.compose(...)` / `apply(...)` | 3×3 齐次矩阵 |
| 平移后的点 / 不变的方向 | `cgviz.transform.translate3d(a,b,c)` + `apply(M, p, w=1/0)` | 4×4 齐次矩阵 |

**同一组数字只允许有一个来源。** 本项目的 0.83 同时出现在：文章公式、
`dsh verify` 的断言、视频里的读数。三处引用同一个实验（绕 Z 轴 0°→100°），
任何一处改了口径，`verify` 会先失败。

行向量约定另有一套规矩：文章写 `p' = p·M`（平移在第 4 行），
`cgviz` 用列向量 `M·p`（平移在第 4 列）。两者互为转置、数值相同，
画面显示文章的形式、计算走 cgviz，`verify` 里有一条断言盯着这个转置关系，
所以公式和读数不会各说各话。

## 七、踩过的坑（都在这个工程里真实发生过）

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 选 `-ql` 却渲成了 1080p60 | 库在 import 时写了 `config.pixel_*`，覆盖了命令行 | 库里不写分辨率；质量档位交给 `dsh render` |
| 改了库、画面没变 | Manim 缓存复用了旧分段 | 渲染一律 `--disable_caching` |
| 3D 页标题是斜的 | `ThreeDScene.add()` 不钉屏 | `add_fixed_in_frame_mobjects` / `flat()` |
| 3D 页公式"躺在地上" | 2D 内容被相机投影 | 同上 |
| `Arrow3D` 用 `GrowArrow` 崩 | `GrowArrow` 内部调 `scale(scale_tips=True)` | 用 `GrowArrow3D` |
| 圆变成了实心盘 | `set_opacity()` 把填充也打开了 | 只调 `set_stroke(opacity=…)` |
| 下标 ₀₁、上标 ᵀ 变成方块 | Noto Sans SC 没有这些字形 | 用 LaTeX（`MathTex("q_0")`） |
| 两个 manim 进程"卡住不报错" | MiKTeX 并发编译互锁 | 串行渲染 |
| `manim ... "*"` 报 "not in the script" | `*` 被当成文件通配符 | `dsh render` 自己发现场景类并显式传入 |
| 一页慢到 4 秒/帧 | 两个渲染进程同时跑，互相抢 CPU | 一次只跑一个 |
| 读数闪烁出"0.880"这种不存在的数字 | `Text` 做 `Transform`，字形数/宽度不同 → 中途叠影 | 数字读数用 `MathTex`（等宽、字形数固定） |
| 3D 坐标轴竖线穿过标题 | `ThreeDAxes` 会画满整个 range，一直顶到画幅边 | 这页不需要轴就别加；或缩短 `z_range` |
| `dsh frames -t 30` 报成功但没图 | 超过视频时长时 ffmpeg 会"成功退出但不产出" | 命令已改为先判时长并跳过 + 校验产物 |
| `output/` 里 1080p 文件其实是 480p | 归档时按 `videos/<模块>/*/*.mp4` 全局匹配，把旧档也复制了 | 只归档本次档位目录；文件名不再说谎 |
| 字幕里出现带 `20 80` 的小方块 | 下标 `₀₁`（U+2080/2081）Noto Sans SC 没有字形，Pango 画出"缺字形"占位框（框里是码位） | 字幕用 ASCII `q0/q1`；`dsh glyphs` 专门查这个 |
| 右下角"CG · 从 0 开始"闪一下就没了 | 水印原本放在旁白同一行，只能靠"第一句旁白出现时淡出"避让 | 水印挪到右上角，从头待到尾 |
| 抽帧老是拿到旧画面 | `frames` 按文件名排序取第一个，`__1080p30` 永远排在 `__480p15` 前面 | 改为取**最新修改**的那个文件 |
| 两段公式叠在一起 | 手写 y 坐标（或 `arrange` 后再 `move_to`）时只按公式本体算高度，忘了下面还有 `note` | 用按"每块实际高度"推进的 `_stack()`；别靠目测留间距 |
| 矩阵里的数字比正文小一圈 | `MathTex` 按**整体高度**缩放：3 行矩阵塞进 0.6 的高度，每行只剩 1/5 | 矩阵块按"行数 × 0.35"给高度（`_eq(height=…)` 要比单行公式大得多） |
| z 轴戳进标题带 | `phi=68°` 下 z 轴投影长度 ≈ 0.93 倍，比 x/y 长得多；2.4 的箭头能画到 y≈2.6 | 自己画的 3D 轴里 **z 轴单独缩短**（2.4 → 1.65），不要三根等长 |
| 轴名压在箭头尖上 | `next_to(…, DOWN)` 正好落在箭头三角的位置，两个都是灰的就糊成一团 | 轴名放箭头外侧：`DOWN + RIGHT` / `UP + RIGHT` |
| 横排图例左边被切到画外 | 图例按字数估宽度必然估小，`move_to` 只保证"中心"在图内 | 拼好后按 `get_left()` 反推平移量，或干脆竖排 |
| 重写一集后 `output/` 里又多出旧页的视频 | 归档只按"档位目录"匹配，media 里上一版留下的旧页也被复制过去 | 归档改为按**本次渲染的页名**过滤（已修，见 `cmd_render`）；手写脚本时别用目录通配 |

## 八、加一集的完整流程

```bash
# 1. 新建文章骨架
python -m manimations new-blog 01-数学基础 01-01 points-and-vectors --title "点与向量"

# 2. 复制分镜骨架，改类名与封面文案
cp video/00-学习路线/demo_why_interpolation.py video/01-数学基础/01-01-points-and-vectors.py

# 3. 开渲前检查
python -m manimations lint

# 4. 反复调版式：抽帧看，不要整片渲
python -m manimations stills 01-01-points-and-vectors -n 4 8 12 16

# 5. 版式确认后出交付版（1080p30），并重建博客目录
python -m manimations render 01-01-points-and-vectors --quality final
python -m manimations index
```

渲染档位：

| 档位 | 分辨率 | 用途 |
| --- | --- | --- |
| `preview` | 854×480 @15 | 只看节奏与版式，最快 |
| `hd` | 1280×720 @30 | 内部审片 |
| `standard` | 1920×1080 @60 | 有高速运动的片子才需要 60fps |
| `final` | 1920×1080 @30 | 默认交付档（教学视频没有高速镜头，30fps 足够，编码时间减半） |

## 九、改版式而不是改每一集

只动 `manimations/src/manimations/theme/palette.py`：

* `Palette` 的 9 个颜色是全部语义色，改这里所有成片一起变；
* `Layout` 的 `content_top/bottom`、`caption_y`、`side_margin` 是所有构图的比例基准；
* 字号在 `typography.py` 的 `HEIGHT_*` 常量里，按"视觉高度"而不是像素定义。

改完不用动任何一集脚本——这正是把这些数抽出来的原因。
