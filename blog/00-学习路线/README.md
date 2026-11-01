# 学习路线：从 0 到渲染器

> 这份清单是博客与视频的"总目录"。`kind` 决定这一讲属于哪类内容：
>
> | kind | 含义 | 谁来产出 |
> | --- | --- | --- |
> | `blog` | 需要我先写/整理成文章 | 用户 |
> | `video` | 需要我根据文章做成分镜与成片 | 编码区 |
> | `code` | 需要算法核里有可执行实现 | 编码区 |
>
> 一条讲可以同时有 `blog` 与 `video`：文章讲清楚"为什么"，视频负责"看得见"。

```yaml
project: CG_Project
platform_path: [scratchapixel, opengl, unreal]

stages:
  - id: 00
    name: 学习路线与工具链
    goal: 把"写文章 → 出视频 → 写代码"的闭环跑通，验证字体、公式、几何渲染都可用。
    topics:
      - id: 00-01
        slug: demo-why-interpolation
        title: 为什么选择四元数（三元组装不下平移）
        kind: [blog, video, code]
        status: done
        note: 样板篇：同一套「三元组 → 四元组」贯穿文章、分镜、算法核三处。

  - id: 01
    name: 数学基础
    goal: 补齐图形学真正会用到的那部分线性代数与几何直觉，不追求数学系的完备性。
    topics:
      - id: 01-01
        slug: points-and-vectors
        title: 点、向量，以及为什么它们不是同一种东西
        kind: [blog, video, code]
        status: next
        note: 齐次坐标的 w 分量从这里开始埋伏笔。
      - id: 01-02
        slug: coordinate-systems
        title: 坐标系、基与手性
        kind: [blog, video]
        status: planned
      - id: 01-03
        slug: affine-transforms
        title: 仿射变换：为什么矩阵是 4×4
        kind: [blog, video, code]
        status: planned
      - id: 01-04
        slug: rotation-representations
        title: 旋转的三种写法：欧拉角、矩阵、轴角
        kind: [blog, video, code]
        status: planned
      - id: 01-05
        slug: gimbal-lock
        title: 万向锁到底锁住了什么
        kind: [blog, video]
        status: planned
      - id: 01-06
        slug: quaternions
        title: 四元数：从 S³ 球面理解旋转
        kind: [blog, video, code]
        status: planned
      - id: 01-07
        slug: interpolation
        title: 插值：lerp、slerp 与"离开合法集合"
        kind: [blog, video, code]
        status: planned

  - id: 02
    name: 光线追踪（scratchapixel 主线）
    goal: 从"针孔相机 + 光线与球求交"开始，手写一个能出图的光线追踪器。
    topics:
      - id: 02-01
        slug: pinhole-camera
        title: 针孔相机模型与光线生成
        kind: [blog, video, code]
        status: planned
      - id: 02-02
        slug: ray-sphere
        title: 光线与球体求交：二次方程怎么来的
        kind: [blog, video, code]
        status: planned
      - id: 02-03
        slug: ray-triangle
        title: 光线与三角形求交：重心坐标与 Möller–Trumbore
        kind: [blog, video, code]
        status: planned
      - id: 02-04
        slug: shading-models
        title: 从 Lambert 到 Blinn-Phong：着色模型在近似什么
        kind: [blog, video, code]
        status: planned

  - id: 03
    name: 光栅化与图形管线
    goal: 理解 GPU 在替我们做什么：顶点变换、裁剪、光栅化、深度测试。
    topics:
      - id: 03-01
        slug: rasterization-basics
        title: 三角形怎么变成像素：光栅化的最小实现
        kind: [blog, video, code]
        status: planned
      - id: 03-02
        slug: perspective-projection
        title: 透视投影：除法的来源与 4×4 矩阵的最后一列
        kind: [blog, video, code]
        status: planned
      - id: 03-03
        slug: depth-buffer
        title: 深度测试与 z-fighting
        kind: [blog, video]
        status: planned

  - id: 04
    name: OpenGL 上手
    goal: 自己写代码把上面的数学落到 GPU 上（这部分代码由我写，编码区不代笔）。
    topics:
      - id: 04-01
        slug: gl-hello-triangle
        title: 第一个三角形：VAO、VBO、Shader 各是什么
        kind: [blog]
        status: planned
      - id: 04-02
        slug: gl-transform-pipeline
        title: MVP 矩阵与坐标空间
        kind: [blog]
        status: planned

  - id: 05
    name: Unreal
    goal: 把前面积累的概念映射到引擎的抽象上（材质、光照、后处理）。
    topics:
      - id: 05-01
        slug: unreal-rendering-basics
        title: Unreal 渲染管线速览：和我手写的渲染器差在哪
        kind: [blog]
        status: planned

conventions:
  blog_dir: blog/<stage>-<主题>/
  video_dir: video/<stage>-<主题>/
  code_dir: code/src/cgviz/
  video_output: output/videos/
```

## 怎么推进

1. **用户**在 `blog/` 下写文章（可用 `_templates/post.md`），一篇文章对应一讲。
2. **编码区**读文章，在 `video/` 下写分镜脚本，图形数据一律来自 `code/src/cgviz/`。
3. **编码区**渲染到 `output/videos/`，并在文章的 `video:` 字段里填上文件名。
4. 遇到新概念就先补 `cgviz` 里的实现——视频永远调用真实算法，不画"示意性假图"。
