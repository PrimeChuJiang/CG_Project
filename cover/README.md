# CG_Project 封面

`cg_project_cover.png` —— 1920×1080，用于博客、视频或项目页的整体系列封面。

## 这张图怎么来的

不是拿 PS 拼的，而是和成片共用同一套视觉系统：

- **配色 / 字体 / 安全区**全部来自 `manimations.theme` 与 `manimations.typography`
  （背景 `#0E1116`、主色 `#4CC9F0`、强调色 `#FFB703`）。
- 右侧立方体先由 `cgviz.mat.rotation_z` 旋转 16°，再用一台针孔相机
  （yaw 45°、pitch 25°、focal 13.2）投影到画面；地板网格用的是同一台相机，
  所以两者的透视严格一致，改机位参数会一起变。
- 地板网格画成带 alpha 蒙版的位图，而不是一根根矢量线：这样才能让网格在
  文字区自然淡出、只在立方体附近显现，不会在标题后面留下斜线。
- 右下角的 XYZ 坐标针只投影方向向量，和立方体保持同一机位。

## 重新生成

```bash
.venv/Scripts/python -m manim render -s -r 1920,1080 --format png \
    --media_dir cover/build assets/cover/generate_cover.py ProjectCover
```

产物在 `cover/build/images/generate_cover/ProjectCover_*.png`，
复制/转成 RGB 后覆盖本目录的 `cg_project_cover.png` 即可。
生成器源码在 [`../assets/cover/generate_cover.py`](../assets/cover/generate_cover.py)，
文件头的说明里写了机位、配色与版式约束。

`build/` 只是 Manim 的中间缓存，可以随时删掉。
