# CG_Project · 从 0 开始学计算机图形学

学习路径：**scratchapixel → OpenGL → Unreal**。
这个工程把"学"拆成三块，互相咬合：

| 板块 | 目录 | 谁负责 | 产出 |
| --- | --- | --- | --- |
| 博客 | `blog/` | **你** | 把学到的、想通的内容写成 md，一讲一篇 |
| 视频 | `video/` + `manimations/` | 编码区 | 读文章 → 写分镜 → 渲成片 |
| 编码 | `code/` | 编码区 | `cgviz` 算法核 + 留给你自己的 OpenGL 练习区 |

三者的关系不是"三个文件夹"，而是一条流水线：

```
你写 blog/01-数学基础/01-01-points.md
        │
        ├─→ 编码区写 video/01-数学基础/01-01-points.py（分镜）
        │        └─→ 图形数据全部来自 code/src/cgviz/（真实算法，不是示意图）
        │                 └─→ 渲出 output/videos/*.mp4
        │
        └─→ blog 文章里挂上成片，一篇讲次闭环
```

**为什么坚持"图形由真实算法驱动"**：视频里那根"正交性误差 0.62"的曲线、
那个被压扁的模型，都是 `cgviz` 当场算出来喂给 Manim 的。所以视频不可能和文章
对不上——一旦对不上，渲染就会失败或数字就变了。这比"照着文章画个示意图"可靠得多。

## 快速开始

```bash
# 1. 装环境（uv 会按 pyproject.toml 建 .venv 并装好 manim / cgviz / manimations）
uv sync --all-packages

# 2. 体检：Python、Manim、ffmpeg、MiKTeX、中文字体
.venv/Scripts/python -m manimations check

# 3. 渲染一集（preview 档约 1 分钟；standard 档 1080p60）
.venv/Scripts/python -m manimations render demo_why_interpolation

# 4. 抽帧检查画面（比反复重渲整集快得多）
.venv/Scripts/python -m manimations frames Demo05_MatInterp -t 2 4 6

# 5. 重建博客目录
.venv/Scripts/python -m manimations index
```

> Windows 上 `dsh` 这个命令名可能和别的东西冲突，所以统一用
> `python -m manimations`；两者完全等价。

## 目录结构

```
CG_Project/
├── blog/                     ← 板块一：你写文章的地方
│   ├── 00-学习路线/README.md   学习路线清单（唯一的总目录，yaml 里定义每一讲）
│   ├── 00-学习路线/00-01-demo-why-interpolation.md   样板篇（文章 ↔ 视频 ↔ 代码 全对齐）
│   ├── 01-数学基础/ … 05-Unreal/
│   └── _templates/           写作约定与文章模板
│
├── video/                    ← 板块二：分镜脚本（一讲一文件）
│   ├── 00-学习路线/demo_why_interpolation.py   七页分镜，演示整条流水线
│   └── _legacy/              早期的试验脚本
│
├── code/                     ← 板块三：编码区
│   ├── src/cgviz/            算法核：vec / mat / quat / interp / transform
│   └── openGL-练习/          留给你自己写 OpenGL 代码，编码区不代笔
│
├── manimations/              教学动画库（不是板块，是三板块的公共资源）
│   └── src/manimations/
│       ├── theme/            配色、版式、安全区
│       ├── scene.py          SlideScene / Slide3DScene：一页幻灯片的固定生命周期
│       ├── typography.py     文字工厂：中文正文与 LaTeX 公式统一视觉高度
│       ├── components/       Card / Equation / Compare / Bullets / cg_axes / plane2d
│       └── cli.py            dsh：check / render / frames / index / new-blog
│
├── output/videos/            交付目录（媒体文件）
├── media/                    Manim 渲染缓存（可删，已 gitignore）
└── assets/                   静态素材（字体、贴图等）
```

## 三个约定

1. **一篇一个文件，文件名带讲次编号。** `blog/01-数学基础/01-01-points.md` 与
   `video/01-数学基础/01-01-points.py` 用同一个 `01-01`。
   **只管文件名，不管内容**：文章写什么、分不分小节、什么语气，全由你定
   （见 `blog/_templates/writing-guide.md`）。
2. **视频不画假图。** 任何几何形状、任何数字，都必须来自 `cgviz` 的真实计算。
   需要新概念，就先补 `cgviz`，再写分镜。
3. **`code/openGL-练习/` 是你的手写区。** 编码区只提供 `cgviz`（算法与数学）与
   `manimations`（可视化），不会替你在练习区写代码。

## 首支样片

`video/00-学习路线/demo_why_interpolation.py` 是七页的分镜样板，主题为
「为什么需要四元数（插值视角）」，对应文章 `blog/00-学习路线/00-01-demo-why-interpolation.md`。
它刻意把四个最容易被糊弄过去的点都做成了可验证的画面：

| 页 | 讲什么 | 数据来源 |
| --- | --- | --- |
| 01 | 片头 | — |
| 02 | 平移与旋转不可交换 | `cgviz.transform.compose` |
| 03 | 9 个数只有 3 个自由度 | `cgviz.mat.orthogonality_error` |
| 04 | 万向锁：α−γ 分不开 | `cgviz.mat.euler_xyz` |
| 05 | 矩阵插值把骨架捏弯 | `cgviz.interp.matrix_path` |
| 06 | 四元数 = 在 S³ 球面上插值 | `cgviz.quat.slerp` |
| 07 | 结论 ↔ 代码映射 | 上面所有函数的实测值 |

## 常用命令

| 想干什么 | 命令 |
| --- | --- |
| 检查环境 | `python -m manimations check` |
| 校验数学不变量 | `python -m manimations verify` |
| 开渲前静态检查 | `python -m manimations lint` |
| 检查缺字形（方块字） | `python -m manimations glyphs` |
| 渲染全部页（交付档） | `python -m manimations render demo_why_interpolation` |
| 只渲某几页 | `python -m manimations render demo_why_interpolation Demo05_MatInterp` |
| 快速预览档 | 同上加 `--quality preview`（480p/15fps） |
| 调版式时抽单帧 | `python -m manimations stills demo_why_interpolation -n 6 14 24` |
| 从成片抽帧 | `python -m manimations frames Demo05_MatInterp -t 6.9 12.3` |
| 新建一篇 | `python -m manimations new-blog 01-数学基础 01-01 points-and-vectors --title "点与向量"` |
| 重建目录 | `python -m manimations index` |

渲染档位：`preview`（480p15，调版式）、`hd`（720p30）、`standard`（1080p60）、
`final`（1080p30，默认交付档）。

三个"开渲前"的好习惯：

1. `lint` —— 抓漏导入、重名类，别拿渲染时间当编译器用；
2. `glyphs` —— 抓"会渲染成方块"的字符。中文走系统字体，缺字形时 Manim **不报错**，
   只画一个占位框（框里印着码位，比如 `20 80`），只有盯成片才发现；
3. `verify` —— 确认 `cgviz` 的数学结论还成立（它断言的就是文章里写的那些数）。
4. `stills` —— 用单帧代替整片，改完一个标签就看一眼。

三个反直觉的坑：

* `manim -s` 出的是**最后一帧**，而每页结尾都会淡出，所以 `-s` 拿到的是黑图。
* **别并行跑多个 `manim render`**：MiKTeX 并发编译公式时会互锁，表现为"卡住不报错"，
  而且两个进程抢 CPU 会让单帧耗时翻十倍。
* 改了 `manimations` 的代码后必须 `--disable_caching`，否则 Manim 会复用旧分段，
  看起来像"改了没生效"。`dsh render` 已经默认带上这个开关。

## 环境说明

* Python 3.14 / Manim 0.22（Cairo 渲染器）
* 字体：Noto Sans SC（正文）、Cascadia Mono（代码）、MiKTeX + dvisvgm（公式）。
  注意 Noto Sans SC 缺少下标 ₀₁、上标 ᵀ 等字形，这类符号要用 LaTeX 排。
* 画幅：16:9，世界坐标固定为 8.4 × 14.9。`SlideScene` 会把 `frame_height` 设为 8.4
  并按 16:9 推宽度，所以所有安全区都是相对量，换分辨率不会跑版。

