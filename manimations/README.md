# manimations

计算机图形学教学动画库。三层结构，越往下越稳定：

```
theme/       视觉语言：配色、字体、安全区、SlideScene 基类（分镜流程）
components/  可复用元件：公式面板、要点列表、3D 坐标系、旁白字幕、对比布局
scenes/      成片：video/ 下每篇博客的脚本从 scenes 里挑零件拼出来
```

`video/` 里的成片脚本通过 `from manimations.components import ...` 使用这里的能力；
它们不在本包内，因为成片是按博客组织的，见项目根 `README.md`。
