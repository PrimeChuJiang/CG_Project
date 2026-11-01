"""字形覆盖检查：找出"会渲染成方块"的字符。

为什么需要它：中文正文走 Pango + 系统字体，而 Noto Sans SC **并不覆盖**
所有看起来"很基础"的符号——下标 ₀₁、上标 ᵀ、带圈的箭头、部分数学符号都可能缺字形。
缺字形时 Manim 不会报错，只会在画面上画一个方框（tofu），而这类问题只有
盯着成片才看得见。所以在渲染之前先扫一遍字符串，比事后逐帧找便宜得多。

用法：``python -m manimations glyphs``（默认扫整个 ``video/``）
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

__all__ = ["GlyphProblem", "scan_paths", "missing_glyphs"]

# 常见中文字体位置。按优先级尝试，找不到就报"无法检查"而不是假装通过。
FONT_CANDIDATES: tuple[str, ...] = (
    "C:/Windows/Fonts/NotoSansSC-VF.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
)


@dataclass
class GlyphProblem:
    path: str
    line: int
    text: str
    missing: list[str]

    def __str__(self) -> str:
        chars = " ".join(f"{c!r}(U+{ord(c):04X})" for c in self.missing)
        return f"{self.path}:{self.line}: 缺字形 {chars}  在字符串 {self.text!r}"


def _load_cmap(font_path: Path) -> set[int]:
    from fontTools.ttLib import TTFont

    font = TTFont(str(font_path), fontNumber=0, lazy=True)
    codepoints: set[int] = set()
    for table in font["cmap"].tables:
        codepoints.update(table.cmap.keys())
    font.close()
    return codepoints


def missing_glyphs(chars: set[str], font_path: Path | None = None) -> list[str]:
    """返回 ``chars`` 里字体并不包含的那些字符。"""
    path = font_path or _default_font()
    cmap = _load_cmap(path)
    return sorted(c for c in chars if c.strip() and ord(c) not in cmap)


def _default_font() -> Path:
    for cand in FONT_CANDIDATES:
        p = Path(cand)
        if p.exists():
            return p
    raise SystemExit(
        "找不到可检查的字体（试过：" + "、".join(FONT_CANDIDATES) + "）。"
        "装一个 Noto Sans SC 再跑。"
    )


def _string_literals(node: ast.AST) -> list[tuple[int, str]]:
    """收集一个语句里所有字符串字面量（含 f-string 的固定片段）。"""
    out: list[tuple[int, str]] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append((getattr(sub, "lineno", 0), sub.value))
        elif isinstance(sub, ast.JoinedStr):
            for part in sub.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    out.append((getattr(part, "lineno", 0), part.value))
    return out


def scan_paths(paths: list[str], *, font_path: Path | None = None) -> list[GlyphProblem]:
    """扫描源文件里的中文字符串，报告缺字形的那些。

    只检查含非 ASCII 的字符串——纯英文/代码标识符不用管。
    """
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        files.extend(sorted(p.rglob("*.py")) if p.is_dir() else [p])

    problems: list[GlyphProblem] = []
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            for lineno, text in _string_literals(node):
                if all(ord(c) < 128 for c in text):
                    continue
                miss = missing_glyphs(set(text), font_path)
                if miss:
                    problems.append(GlyphProblem(str(f), lineno, text, miss))
    # 同一处可能因为 ast.walk 重复访问，去重
    unique: list[GlyphProblem] = []
    for p in problems:
        if p not in unique:
            unique.append(p)
    return unique
