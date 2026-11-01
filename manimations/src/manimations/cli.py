"""``dsh`` —— 这个工程自己的命令行工具。

四个子命令对应三板块之间的四种搬运：

```
dsh check                 体检：Python / Manim / ffmpeg / LaTeX / 中文字体
dsh render <脚本> [页名…]   把分镜脚本渲成 mp4，并复制到 output/videos/
dsh frames <页名|mp4> -t 3  从成片里抽几帧 PNG，用来检查画面而不是靠盲猜
dsh index                 扫描 blog/ 生成博客目录（含视频链接）
```

设计原则：**不重复 Manim 的能力，只补它缺的那几步**。渲染仍然交给
``manim render``，这里只负责路径推导、质量档位、产物归档和结果提示。
"""

from __future__ import annotations

import argparse
import numpy as np
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VIDEO_DIR = ROOT / "video"
BLOG_DIR = ROOT / "blog"
MEDIA_DIR = ROOT / "media"
OUTPUT_DIR = ROOT / "output" / "videos"

# 档位：预览要快，交付要稳。1080p60 的编码时间大约是 1080p30 的两倍，
# 而教学视频里 30fps 已经足够（没有高速运动镜头），所以交付默认用 final。
QUALITY_FLAGS: dict[str, tuple[list[str], str]] = {
    "preview": (["-ql"], "480p15"),
    "hd": (["-qm"], "720p30"),
    "standard": (["-qh"], "1080p60"),
    "final": (["-r", "1920,1080", "--fps", "30"], "1080p30"),
}


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------
def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:  # noqa: BLE001
        return False, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out.strip()


def cmd_check(args: argparse.Namespace) -> int:
    """检查工具链。任何一项失败都会以非零码退出，便于在 CI 里用。"""
    checks: list[tuple[str, bool, str]] = []

    checks.append(("Python", sys.version_info >= (3, 13), sys.version.split()[0]))

    ok, out = _run([sys.executable, "-c", "import manim;print(manim.__version__)"])
    checks.append(("Manim", ok, out if ok else "导入失败"))

    ok, out = _run([sys.executable, "-c", "import cgviz, manimations;print('ok')"])
    checks.append(("cgviz / manimations", ok, "可导入" if ok else out))

    for name, exe in (("ffmpeg", "ffmpeg"), ("dvisvgm", "dvisvgm"), ("latex", "latex")):
        path = shutil.which(exe)
        checks.append((name, path is not None, path or "未在 PATH 上"))

    # 中文字体：Pango 找得到才说明 Text 不会退化成方框
    font_probe = (
        "from manim import Text;"
        "t=Text('测试', font='Noto Sans SC');"
        "print('ok', t.font if hasattr(t,'font') else 'Noto Sans SC')"
    )
    ok, out = _run([sys.executable, "-c", font_probe])
    checks.append(("中文正文字体", ok, "Noto Sans SC" if ok else "缺失（回退到雅黑）"))

    width = max(len(n) for n, _, _ in checks) + 2
    failed = 0
    for name, good, detail in checks:
        mark = "OK  " if good else "FAIL"
        if not good:
            failed += 1
        print(f"[{mark}] {name.ljust(width)} {detail}")

    print()
    if failed:
        print(f"{failed} 项未通过。缺失的依赖先装上，再谈渲染。")
        return 1
    print("工具链完整：文字、公式、几何、视频编码四条链路都通。")
    return 0


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------
def _find_scene_file(target: str) -> Path:
    """把 ``00-学习路线/demo_why_interpolation.py`` 或裸模块名解析成绝对路径。"""
    p = Path(target)
    if p.suffix == ".py" and p.exists():
        return p.resolve()
    for cand in VIDEO_DIR.rglob(f"{p.stem or target}.py"):
        return cand.resolve()
    raise SystemExit(f"找不到分镜脚本：{target}（应在 {VIDEO_DIR} 下）")


def _discover_scenes(script: Path) -> list[str]:
    """导入分镜脚本，按名字顺序列出其中定义的场景类。

    为什么不把 ``"*"`` 直接丢给 manim？因为 manim 会把 ``*`` 当成文件通配符去
    展开目录，结果报"xx.py is not in the script"并退回交互式选择。
    自己解析一遍还有一个额外好处：页名列表本身就是这一集的分镜大纲。
    """
    import importlib.util

    from manim import Scene

    spec = importlib.util.spec_from_file_location(f"_dsh_{script.stem}", script)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法作为模块加载：{script}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(script.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    names = [
        name
        for name, obj in vars(module).items()
        if isinstance(obj, type)
        and issubclass(obj, Scene)
        and obj.__module__ == module.__name__
        and getattr(obj, "__abstractmethods__", None) is None
    ]
    return sorted(names)


def cmd_render(args: argparse.Namespace) -> int:
    script = _find_scene_file(args.script)
    quality_args, spec = QUALITY_FLAGS[args.quality]

    scenes = list(args.scenes)
    if not scenes:
        scenes = _discover_scenes(script)
    if not scenes:
        raise SystemExit(f"{script.name} 里没有可渲染的 Scene 子类")

    print(f"共 {len(scenes)} 页：" + "、".join(scenes))
    cmd = [
        sys.executable,
        "-m",
        "manim",
        "render",
        "--media_dir",
        str(MEDIA_DIR),
        "--format",
        "mp4",
        *quality_args,
        "--disable_caching",
        str(script),
        *scenes,
    ]
    print(f"$ {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, cwd=script.parent)
    if proc.returncode != 0:
        return proc.returncode

    # 把产物归档到 output/videos/：Manim 的 media 目录结构不适合当交付目录。
    # 只取本次档位对应的目录（480p15 / 1080p30 / …），否则会把上一档的旧文件
    # 也复制一遍并贴上本次的后缀——那比不归档更糟，因为文件名会说谎。
    # 还要按**本次渲染的页名**过滤：一集被重写后，media 里仍留着上一次的旧页
    # （Demo01_Title 这类），只按目录匹配会把它们一起归档进去。
    module = script.stem
    wanted = set(scenes)
    produced = sorted(
        p
        for p in (MEDIA_DIR / "videos" / module / spec).glob("*.mp4")
        if p.stem in wanted
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for mp4 in produced:
        dest = OUTPUT_DIR / f"{module}__{mp4.stem}__{spec}.mp4"
        shutil.copy2(mp4, dest)
        print(f"归档 {dest.relative_to(ROOT)}  ({dest.stat().st_size / 1e6:.1f} MB)")
    if not produced:
        print(f"未找到渲染产物（{MEDIA_DIR / 'videos' / module / spec}），检查 media 目录。")
        return 1
    return 0


# --------------------------------------------------------------------------
# frames
# --------------------------------------------------------------------------
def _resolve_mp4(target: str) -> Path:
    """按名字片段找视频；有多个候选时取**最新**的那个。

    之前按文件名排序取第一个，结果是 ``__1080p30`` 永远排在 ``__480p15`` 前面，
    刚渲好的 480p 预览永远抽不到——看起来像"改了代码没生效"，其实是读的旧片。
    """
    p = Path(target)
    if p.suffix == ".mp4" and p.exists():
        return p.resolve()
    hits = list(OUTPUT_DIR.glob(f"*{target}*.mp4")) + list(MEDIA_DIR.glob(f"**/*{target}*.mp4"))
    if not hits:
        raise SystemExit(f"找不到视频：{target}")
    return max(hits, key=lambda h: h.stat().st_mtime).resolve()


def cmd_frames(args: argparse.Namespace) -> int:
    """按秒抽帧。默认在 40%~90% 之间均匀取 3 帧（片头片尾通常是空的）。"""
    mp4 = _resolve_mp4(args.video)
    duration = _duration(mp4)
    times = args.at or [duration * f for f in (0.35, 0.6, 0.85)]
    out_dir = Path(args.out) if args.out else mp4.parent / f"{mp4.stem}_frames"
    if not out_dir.is_absolute():
        out_dir = (ROOT / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, t in enumerate(times, start=1):
        if t >= duration:
            # 超过时长时 ffmpeg 会"成功退出但不产出文件"，所以必须自己拦。
            print(f"跳过 {t:.1f}s：超出视频时长 {duration:.1f}s")
            continue
        dest = out_dir / f"{i:02d}_{t:.1f}s.png"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(mp4),
            "-frames:v", "1", "-q:v", "2", str(dest),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stderr[-800:])
            return proc.returncode
        if not dest.exists():
            print(f"抽帧失败：{t:.1f}s 没有产出文件")
            continue
        print(f"抽帧 {dest.relative_to(ROOT)}")

    made = len(list(out_dir.glob("*.png")))
    print(f"\n目录：{out_dir}（现有 {made} 张）")
    return 0 if made else 1


def _duration(mp4: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(mp4)],
        capture_output=True, text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 1.0


# --------------------------------------------------------------------------
# stills
# --------------------------------------------------------------------------
def _render_stills(
    script: Path,
    scenes: list[str],
    at: list[int],
    *,
    quality: str,
    out_dir: Path,
    quiet: bool = False,
) -> list[tuple[str, int, Path]]:
    """渲染若干单帧并归档。返回 ``[(页名, 动画序号, 图片路径), …]``。

    比整页渲染快一个数量级，因为 Manim 的 ``-s`` 会把 ``skip_animations`` 打开，
    前面的动画只推进状态、不落帧；配合 ``-n N,N``（跑到第 N 个动画就抛
    EndSceneEarlyException），就能精确停在"某个动作刚结束"的那一刻。

    为什么不用 ``manim -s`` 直接截？那样截到的是**整个场景的最后一帧**，
    而每页结尾都会淡出，拿到的是黑图。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    made_files: list[tuple[str, int, Path]] = []
    for scene in scenes:
        for n in at:
            cmd = [
                sys.executable, "-m", "manim", "render",
                "--media_dir", str(MEDIA_DIR),
                "--format", "png", quality,
                "--disable_caching",
                "-n", f"{n},{n}",
                str(script), scene,
            ]
            sw = time.perf_counter()
            proc = subprocess.run(cmd, cwd=script.parent, capture_output=True, text=True)
            elapsed = time.perf_counter() - sw
            if proc.returncode != 0:
                tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
                print(f"✗ {scene} @{n}: " + " / ".join(tail))
                continue

            # Manim 把图写到 media/images/<module>/<scene>_...png，挑最新的一张
            made = sorted(
                MEDIA_DIR.glob(f"images/**/{scene}*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not made:
                print(f"✗ {scene} @{n}: 没找到输出 PNG")
                continue
            dest = out_dir / f"{scene}__after{n:03d}.png"
            shutil.copy2(made[0], dest)
            made_files.append((scene, n, dest))
            if not quiet:
                print(f"✓ {dest.name}  ({elapsed:.1f}s)")
    return made_files


def cmd_stills(args: argparse.Namespace) -> int:
    """按动画序号抽单帧，用来调版式。"""
    script = _find_scene_file(args.script)
    scenes = list(args.scene) or _discover_scenes(script)
    if not scenes:
        raise SystemExit(f"{script.name} 里没有可渲染的 Scene 子类")

    out_dir = Path(args.out) if args.out else ROOT / ".cache" / "stills" / script.stem
    if not out_dir.is_absolute():
        out_dir = (ROOT / out_dir).resolve()

    at = list(args.at) if args.at else list(range(2, args.step * args.count + 1, args.step))
    quality = {"preview": "-ql", "hd": "-qm"}[args.quality]

    made = _render_stills(script, scenes, at, quality=quality, out_dir=out_dir)
    if not made:
        print("一张都没出。先跑 dsh lint，再确认页名与动画序号是否正确。")
        return 1
    print(f"\n共 {len(made)} 张，目录：{out_dir}")
    return 0


# --------------------------------------------------------------------------
# sheet
# --------------------------------------------------------------------------
def cmd_sheet(args: argparse.Namespace) -> int:
    """把若干单帧拼成一张联系表（contact sheet）——用一张图验收多帧。

    为什么值得单独做：验收画面是这条流水线里最费 token 的动作（每看一帧约 1.5k）。
    拼成一张后，六帧只算一次图像输入，而且**并排对比**比逐张翻更容易发现
    错位、重叠、大小不一致这类问题。
    """
    from PIL import Image, ImageDraw

    script = _find_scene_file(args.script)
    scenes = list(args.scene) or _discover_scenes(script)[:1]
    at = list(args.at) if args.at else list(range(2, args.step * args.count + 1, args.step))
    quality = {"preview": "-ql", "hd": "-qm"}[args.quality]

    tmp = ROOT / ".cache" / "sheet" / script.stem
    made = _render_stills(script, scenes, at, quality=quality, out_dir=tmp, quiet=True)
    if not made:
        print("一张都没出，无法拼图。先跑 dsh lint。")
        return 1

    cols = max(1, min(args.cols, len(made)))
    rows = (len(made) + cols - 1) // cols
    tile_w = args.width
    pad = 10
    label_h = 26

    tiles = [Image.open(p).convert("RGB") for _, _, p in made]
    scale = tile_w / tiles[0].width
    tile_h = int(tiles[0].height * scale)

    sheet = Image.new("RGB", (cols * tile_w + (cols + 1) * pad, rows * (tile_h + label_h) + (rows + 1) * pad), "#0b0d12")
    draw = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont

        font = ImageFont.truetype("C:/Windows/Fonts/NotoSansSC-VF.ttf", 16)
    except OSError:
        font = ImageFont.load_default()

    for i, ((scene, n, _), tile) in enumerate(zip(made, tiles)):
        r, c = divmod(i, cols)
        x = pad + c * (tile_w + pad)
        y = pad + r * (tile_h + label_h + pad)
        sheet.paste(tile.resize((tile_w, tile_h), Image.LANCZOS), (x, y))
        draw.text((x + 4, y + tile_h + 3), f"{scene}  @ after {n}", fill="#9aa4b2", font=font)

    out = Path(args.out) if args.out else tmp / f"sheet__{'__'.join(scenes)}.png"
    if not out.is_absolute():
        out = (ROOT / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"联系表：{out.relative_to(ROOT)}  ({len(made)} 帧，{sheet.width}×{sheet.height})")
    return 0


# --------------------------------------------------------------------------
# index
# --------------------------------------------------------------------------
def _post_summary(md: Path) -> tuple[str, str]:
    """抽出标题与一句摘要，**不要求文章有任何固定格式**。

    取法：标题 = 第一个 ``# `` 行；摘要 = 正文里第一段非空、非标题、非代码块的文字，
    截到 60 字。作者没有写"一句话"这种约定也没关系——有就用自己的，没有就用首段。
    """
    lines = md.read_text(encoding="utf-8").splitlines()
    title = md.stem
    summary = ""
    in_code = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if title == md.stem and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            body = stripped.lstrip("> ").strip()
            if body.startswith("一句话"):
                body = body.split("：", 1)[-1].strip()
            if body:
                summary = body
                break
            continue
        # 段落可能跨行：把连续的正文行拼成一段再取句，否则会在行尾被截断
        para: list[str] = [stripped]
        for follow in lines[i + 1 :]:
            nxt = follow.strip()
            if not nxt or nxt.startswith(("#", "```", ">", "|", "-", "*", "!")):
                break
            para.append(nxt)
        summary = "".join(para)
        break
    # 优先取第一句（到句号为止），避免在句中截断；句子过长才硬截
    for mark in ("。", "！", "？"):
        idx = summary.find(mark)
        if 0 <= idx < 90:
            summary = summary[: idx + len(mark)].strip()
            break
    if len(summary) > 90:
        summary = summary[:90].rstrip() + "…"
    return title, summary


def _video_key(slug: str) -> str:
    """把文章文件名映射成分镜模块名。

    ``00-01-demo-why-interpolation`` → ``demo_why_interpolation``
    （去掉讲次编号，连字符换成下划线）。这样文章与视频靠命名就能对上，
    不需要额外维护一张映射表。
    """
    parts = slug.split("-", 2)
    stem = parts[2] if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() else slug
    return stem.replace("-", "_")


def cmd_index(args: argparse.Namespace) -> int:
    """生成 blog/README.md：按阶段列出所有文章，并标出对应的成片。"""
    lines = ["# 博客目录", "", "由 `dsh index` 生成，不要手改。", ""]
    total = 0
    for stage_dir in sorted(p for p in BLOG_DIR.iterdir() if p.is_dir() and not p.name.startswith("_")):
        posts = sorted(md for md in stage_dir.glob("*.md") if md.name != "README.md")
        if not posts:
            continue
        lines.append(f"## {stage_dir.name}")
        lines.append("")
        lines.append("| 文章 | 摘要 | 视频 |")
        lines.append("| --- | --- | --- |")
        for md in posts:
            title, summary = _post_summary(md)
            key = _video_key(md.stem)
            # 交付档优先（1080p30 / final），其次预览档；都没有就留空
            videos = (
                sorted(OUTPUT_DIR.glob(f"*{key}*__1080p30*.mp4"))
                or sorted(OUTPUT_DIR.glob(f"*{key}*__final*.mp4"))
                or sorted(OUTPUT_DIR.glob(f"*{key}*__480p15*.mp4"))
                or sorted(OUTPUT_DIR.glob(f"*{key}*.mp4"))
            )
            # 一集通常有多页成片，逐页列文件名会把目录撑爆；
            # 多页时只报"模块名 + 页数"，单页时才给具体文件名。
            if not videos:
                video_cell = "—"
            elif len(videos) == 1:
                video_cell = f"`{videos[0].name}`"
            else:
                video_cell = f"`{key}`（{len(videos)} 页）"
            lines.append(f"| [{title}]({stage_dir.name}/{md.name}) | {summary} | {video_cell} |")
            total += 1
        lines.append("")
    (BLOG_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 blog/README.md（{total} 篇）")
    return 0


# --------------------------------------------------------------------------
# new-blog
# --------------------------------------------------------------------------
def cmd_new_blog(args: argparse.Namespace) -> int:
    """新建一篇空文章。

    刻意**不**套任何结构模板：博客是给人复习用的，不是给流水线做接口的。
    这里只写一行标题，正文怎么写、分不分小节，由作者自己决定。
    """
    dest = BLOG_DIR / args.stage / f"{args.id}-{args.slug}.md"
    if dest.exists() and not args.force:
        raise SystemExit(f"已存在：{dest}（加 --force 覆盖）")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"# {args.title}\n\n", encoding="utf-8")
    print(f"新建 {dest.relative_to(ROOT)}（只有标题，正文随你写）")
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------
def cmd_verify(args: argparse.Namespace) -> int:
    """校验算法核的数学不变量。

    这里断言的都是"视频里讲过的结论"：如果哪天改了 cgviz 导致结论不成立，
    这一条命令会先失败，而不是等渲完一整集才发现画面在说错话。
    """
    from cgviz import interp, mat, quat, transform, vec

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    # 1. 齐次坐标：点带 1、向量带 0，平移只影响点
    t = np.eye(4)
    t[:3, 3] = [1.0, 2.0, 3.0]
    p = t @ vec.homogeneous([0, 0, 0], True)
    d = t @ vec.homogeneous([0, 0, 0], False)
    check("平移只作用于点（w=1），不影响向量（w=0）", p[3] == 1.0 and d[3] == 0.0 and np.allclose(d[:3], 0))

    # 2. 旋转矩阵必须正交
    r = mat.rotation_matrix_axis([1.0, 2.0, 3.0], 0.7)
    check("绕轴旋转矩阵的正交性误差 < 1e-12", mat.orthogonality_error(r) < 1e-12,
          f"{mat.orthogonality_error(r):.2e}")

    # 3. 四元数 ↔ 矩阵 往返
    q = quat.from_axis_angle([0.3, -1.0, 0.5], 1.1)
    rt = quat.to_matrix(quat.from_matrix(quat.to_matrix(q)))
    check("四元数 → 矩阵 → 四元数 → 矩阵 往返一致", np.allclose(rt, quat.to_matrix(q), atol=1e-12))

    # 4. 矩阵直插会离开合法集合，slerp 不会（本片的核心结论）
    # 这个 0.83 是"绕 Z 轴 0°→100°、t=0.5 处"的实测值，也是文章与视频里引用的同一个数。
    m0, m1 = mat.rotation_z(0.0), mat.rotation_z(np.radians(100))
    naive = interp.max_error(interp.matrix_path(m0, m1))
    proper = interp.max_error(interp.slerp_path(m0, m1))
    check("矩阵直插的最大正交性误差 ≈ 0.83（绕 Z 转 100°）", 0.80 < naive < 0.86, f"{naive:.3f}")
    check("slerp 全程保持正交（误差 < 1e-9）", proper < 1e-9, f"{proper:.2e}")

    # 5. 万向锁：俯仰 90° 时 α 与 γ 只以 α−γ 出现
    a, g = 0.7, 0.2
    r1 = mat.euler_xyz(g, np.pi / 2, a)
    r2 = mat.euler_xyz(0.0, np.pi / 2, a - g)
    check("万向锁：R(g, 90°, a) == R(0, 90°, a−g)", np.allclose(r1, r2, atol=1e-12))

    # 6. 2D 旋转：三角恒等式与矩阵是同一件事（00-01「旋转」一节的整段推导）
    alpha, theta = np.radians(30.0), np.radians(45.0)
    p2 = np.array([np.cos(alpha), np.sin(alpha), 0.0])
    r2 = mat.rotation_z(theta) @ p2
    check("绕 z 转 θ：p 正好落到 (cos(α+θ), sin(α+θ))",
          np.allclose(r2[:2], [np.cos(alpha + theta), np.sin(alpha + theta)], atol=1e-12))
    check("旋转保持长度：|p'| = |p| = 1", abs(vec.length(r2) - 1.0) < 1e-12, f"{vec.length(r2):.6f}")

    # 7. 文章用行向量 p·M；cgviz 用列向量 M·p。两者只差一个转置，数值必须相同。
    row2d = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])
    check("行向量写法 p·M 与 cgviz 的 Mᵀ·p 给出同一坐标",
          np.allclose(p2[:2] @ row2d, r2[:2], atol=1e-12))

    # 8. 三根轴的行向量矩阵都必须是「列向量矩阵的转置」，否则旋转方向会反过来。
    #    这一步专门拦"某一个矩阵的符号抄错"——只有同时正交、又固定自己的轴还不够，
    #    三根轴必须共用同一套手性。
    row_x = np.array([[1.0, 0.0, 0.0],
                      [0.0, np.cos(theta), np.sin(theta)],
                      [0.0, -np.sin(theta), np.cos(theta)]])
    row_y = np.array([[np.cos(theta), 0.0, -np.sin(theta)],
                      [0.0, 1.0, 0.0],
                      [np.sin(theta), 0.0, np.cos(theta)]])
    row_z = np.array([[np.cos(theta), np.sin(theta), 0.0],
                      [-np.sin(theta), np.cos(theta), 0.0],
                      [0.0, 0.0, 1.0]])
    check("绕 x/y/z 的行向量矩阵都是 R_k(θ)ᵀ（三根轴同一套手性）",
          np.allclose(row_x, mat.rotation_x(theta).T, atol=1e-12)
          and np.allclose(row_y, mat.rotation_y(theta).T, atol=1e-12)
          and np.allclose(row_z, mat.rotation_z(theta).T, atol=1e-12))
    check("每根轴的旋转都固定自己的轴（绕 z 转不改 z）",
          all(
              np.allclose(m @ e, e, atol=1e-12)
              for m, e in (
                  (mat.rotation_x(theta), np.array([1.0, 0.0, 0.0])),
                  (mat.rotation_y(theta), np.array([0.0, 1.0, 0.0])),
                  (mat.rotation_z(theta), np.array([0.0, 0.0, 1.0])),
              )
          ))

    # 9. 平移：4×4 齐次矩阵把点搬走，方向不动（w 的全部作用）
    t4 = transform.translate3d(1.5, -0.5, 2.0)
    pt = transform.apply(t4, [0.3, 0.4, 0.5], 1.0)
    dv = transform.apply(t4, [0.3, 0.4, 0.5], 0.0)
    check("4×4 平移：点 (w=1) 走 t，方向 (w=0) 不动",
          np.allclose(pt, [1.8, -0.1, 2.5]) and np.allclose(dv, [0.3, 0.4, 0.5]),
          f"p'={np.round(pt, 3).tolist()}")

    # 10. 线性变换一定把原点留在原点——这正是 3×3 做不了平移的原因
    check("3×3 线性变换固定原点，平移却把原点搬到 (1, 2)",
          all(np.allclose(m @ np.zeros(3), np.zeros(3))
              for m in (mat.rotation_x(0.4), mat.rotation_z(1.1), mat.euler_xyz(0.2, 0.5, -0.7)))
          and np.allclose(transform.apply(transform.translate2d(1.0, 2.0), [0.0, 0.0]), [1.0, 2.0]))

    # 11. 三个轴旋转的顺序不可交换（顺序本身就是结果的一部分）
    a1, b1, c1 = 0.6, 0.3, 0.9
    order_zyx = mat.rotation_z(c1) @ mat.rotation_y(b1) @ mat.rotation_x(a1)
    order_xyz = mat.rotation_x(a1) @ mat.rotation_y(b1) @ mat.rotation_z(c1)
    check("Rz·Ry·Rx ≠ Rx·Ry·Rz（顺序是结果的一部分）",
          not np.allclose(order_zyx, order_xyz, atol=1e-3),
          f"差 {float(np.linalg.norm(order_zyx - order_xyz)):.3f}")

    width = max(len(n) for n, _, _ in checks) + 2
    failed = 0
    print("算法核不变量校验")
    for name, ok, detail in checks:
        mark = "OK  " if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{mark}] {name.ljust(width)} {detail}")
    print()
    if failed:
        print(f"{failed}/{len(checks)} 项失败：算法核与文章结论已经不一致，先修 cgviz。")
        return 1
    print(f"{len(checks)}/{len(checks)} 项通过：文章里写的结论，代码仍然成立。")
    return 0


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------
def cmd_lint(args: argparse.Namespace) -> int:
    """开渲前的静态检查：未定义名字、重复类名、缺 build()。"""
    from .lint import lint_paths

    targets = args.paths or [str(VIDEO_DIR)]
    problems = lint_paths(targets)
    if not problems:
        print(f"检查通过：{', '.join(targets)}")
        return 0
    for p in problems:
        print(p)
    print(f"\n{len(problems)} 个问题。先修掉，再渲染——每个问题都会让一整轮渲染白跑。")
    return 1


# --------------------------------------------------------------------------
# glyphs
# --------------------------------------------------------------------------
def cmd_glyphs(args: argparse.Namespace) -> int:
    """检查源文件里的中文字符串，找出当前字体缺字形的字符（会渲染成方块）。"""
    from .glyphs import scan_paths

    targets = args.paths or [str(VIDEO_DIR)]
    problems = scan_paths(targets, font_path=Path(args.font) if args.font else None)
    if not problems:
        print(f"检查通过：{', '.join(targets)} 里没有缺字形的字符")
        return 0
    for p in problems:
        print(p)
    print(f"\n{len(problems)} 处会渲染成方块。改成 LaTeX（MathTex）或换成字体里有的字符。")
    return 1


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    # Windows 控制台默认 GBK，中文输出会变问号；这里强制走 UTF-8
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="dsh", description="CG_Project 的三板块工具链")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="检查工具链")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("verify", help="校验算法核的数学不变量")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("lint", help="开渲前静态检查分镜脚本")
    p.add_argument("paths", nargs="*", help="文件或目录；省略则检查整个 video/")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("render", help="渲染分镜脚本")
    p.add_argument("script", help="video/ 下的脚本路径或模块名")
    p.add_argument("scenes", nargs="*", help="要渲染的页名；省略则全部")
    p.add_argument("--quality", choices=sorted(QUALITY_FLAGS), default="final")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("frames", help="从成片抽帧")
    p.add_argument("video", help="output/videos 下的文件名片段或 mp4 路径")
    p.add_argument("-t", "--at", type=float, nargs="*", help="抽帧时间点（秒）")
    p.add_argument("-o", "--out", help="输出目录")
    p.set_defaults(func=cmd_frames)

    p = sub.add_parser("stills", help="按动画序号抽单帧，调版式用")
    p.add_argument("script", help="video/ 下的脚本路径或模块名")
    p.add_argument("--scene", action="append", default=[], help="页名，可重复；省略则全部")
    p.add_argument("-n", "--at", type=int, nargs="*", help="在第 N 个动画后截图（可给多个）")
    p.add_argument("--step", type=int, default=4, help="自动取序号时的步长（默认 4）")
    p.add_argument("--count", type=int, default=6, help="自动取多少张（默认 6）")
    p.add_argument("--quality", choices=["preview", "hd"], default="hd")
    p.add_argument("-o", "--out", help="输出目录")
    p.set_defaults(func=cmd_stills)

    p = sub.add_parser("glyphs", help="检查中文字符串是否有缺字形")
    p.add_argument("paths", nargs="*", help="文件或目录；省略则检查整个 video/")
    p.add_argument("--font", help="指定字体文件（默认 Noto Sans SC）")
    p.set_defaults(func=cmd_glyphs)

    p = sub.add_parser("sheet", help="把多帧拼成一张联系表，一次看多帧")
    p.add_argument("script", help="video/ 下的脚本路径或模块名")
    p.add_argument("--scene", action="append", default=[], help="页名，可重复；省略则第一页")
    p.add_argument("-n", "--at", type=int, nargs="*", help="在第 N 个动画后截图（可给多个）")
    p.add_argument("--step", type=int, default=4, help="自动取序号时的步长（默认 4）")
    p.add_argument("--count", type=int, default=6, help="自动取多少帧（默认 6）")
    p.add_argument("--cols", type=int, default=2, help="每行几帧（默认 2）")
    p.add_argument("--width", type=int, default=860, help="单帧像素宽（默认 860）")
    p.add_argument("--quality", choices=["preview", "hd"], default="hd")
    p.add_argument("-o", "--out", help="输出图片路径")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("index", help="生成博客目录")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("new-blog", help="按模板新建文章")
    p.add_argument("stage", help="blog/ 下的阶段目录名，如 01-数学基础")
    p.add_argument("id", help="讲次编号，如 01-01")
    p.add_argument("slug", help="英文短名，如 points-and-vectors")
    p.add_argument("--title", default="<标题>")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new_blog)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
