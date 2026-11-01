"""静态检查：在渲染之前抓出"名字写错 / 没导入"这一类低级错误。

为什么需要它：一集要渲一两分钟，而 Manim 只在跑到出事那一页时才抛
``NameError``，等于拿渲染时间当编译器用。这类错误**完全可以在开渲前静态查出来**。

检查范围刻意做窄，只报高置信度的问题（宁漏勿错）：

* 未定义的名字（不在当前作用域、不在模块全局、不是内置名）
* ``from manim import (...)`` 里重复导入同一个名字
* 同一文件里重复的类名（Manim 只认最后一个，会静默丢页）
* 分镜类缺少 ``build()``

用法：``python -m manimations lint video``
"""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Problem", "lint_file", "lint_paths"]

BASE_CLASSES = {"SlideScene", "Slide3DScene"}


@dataclass
class Problem:
    """一条检查结果。``path`` 用字符串是为了方便跨文件拼接与打印。"""

    path: str
    line: int
    kind: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.kind}] {self.message}"


# --------------------------------------------------------------------------
# 名字收集
# --------------------------------------------------------------------------
def _module_names(tree: ast.Module) -> set[str]:
    """模块级可见的名字。

    只处理模块级语句**本身**，不深入函数体——否则函数里的局部变量会被误当成全局名，
    让"忘了 import"的检查形同虚设。
    """
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.For, ast.While, ast.If, ast.With)):
            # 模块级控制流里绑定的名字也算可见（保守但正确）
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
        else:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    names.add(sub.id)
    return names


def _local_names(func: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> set[str]:
    """一个函数内部会绑定的所有名字（参数、赋值、循环、异常、嵌套 def、推导式）。"""
    args = func.args
    names = {a.arg for a in args.args + args.kwonlyargs + args.posonlyargs}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)

    for sub in ast.walk(func):
        if sub is func:
            continue
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            names.add(sub.id)
        elif isinstance(sub, ast.Import):
            for alias in sub.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(sub, ast.ImportFrom):
            for alias in sub.names:
                names.add(alias.asname or alias.name)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(sub.name)
            names.update(_local_names(sub))
        elif isinstance(sub, ast.Lambda):
            names.update(_local_names(sub))
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            names.add(sub.name)
        elif isinstance(sub, ast.comprehension):
            for target in ast.walk(sub.target):
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


# --------------------------------------------------------------------------
# 检查
# --------------------------------------------------------------------------
def _dup_imports(tree: ast.Module, path: str) -> list[Problem]:
    problems: list[Problem] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        seen: set[str] = set()
        for alias in node.names:
            local = alias.asname or alias.name
            if local in seen:
                problems.append(Problem(path, node.lineno, "dup-import", f"重复导入 {local}"))
            seen.add(local)
    return problems


def _dup_classes(tree: ast.Module, path: str) -> list[Problem]:
    problems: list[Problem] = []
    seen: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name in seen:
                problems.append(
                    Problem(
                        path,
                        node.lineno,
                        "dup-class",
                        f"类名 {node.name} 重复（第 {seen[node.name]} 行已定义）；Manim 只会渲染最后一个",
                    )
                )
            seen[node.name] = node.lineno
    return problems


def _undefined_names(tree: ast.Module, path: str) -> list[Problem]:
    """用"作用域栈 + 全局集合"做朴素解析。

    不追求完整实现 Python 的作用域规则（例如类体作用域的特殊规则），
    但足以覆盖"忘了 import manim 里的常量"这类真实翻车场景。
    """
    module_names = _module_names(tree)
    builtins_names = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    problems: list[Problem] = []

    def resolve(loads: list[ast.Name], scopes: list[set[str]]) -> None:
        for node in loads:
            if node.id in builtins_names:
                continue
            if node.id in module_names:
                continue
            if any(node.id in s for s in scopes):
                continue
            problems.append(Problem(path, node.lineno, "undefined", f"未定义的名字 {node.id}"))

    def collect_loads(body: list[ast.stmt]) -> list[ast.Name]:
        loads: list[ast.Name] = []
        for stmt in body:
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                    loads.append(sub)
        return loads

    def visit_function(func: ast.FunctionDef | ast.AsyncFunctionDef, scopes: list[set[str]]) -> None:
        inner = _local_names(func)
        for stmt in func.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit_function(stmt, [*scopes, inner])
            else:
                resolve(collect_loads([stmt]), [*scopes, inner])

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_function(node, [])
        elif isinstance(node, ast.ClassDef):
            class_scope: set[str] = {node.name}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visit_function(item, [class_scope])
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        for sub in ast.walk(target):
                            if isinstance(sub, ast.Name):
                                class_scope.add(sub.id)
                elif not isinstance(item, ast.ClassDef):
                    resolve(collect_loads([item]), [class_scope])
        else:
            resolve(collect_loads([node]), [])

    return problems


def _missing_build(tree: ast.Module, path: str) -> list[Problem]:
    """分镜类必须能提供 ``build()``：自己实现，或者从同文件里的父类继承。

    基类 ``SlideScene`` 本身是个"必须覆盖"的模板方法，所以只检查直接写
    ``build()`` 与否会误报；这里允许"父类在本文件里已实现"的情况，
    这样 ``Slide3DScene(SlideScene)`` 这种纯扩展不会被冤枉。
    """
    providers: set[str] = set()
    problems: list[Problem] = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
        has_build = any(
            isinstance(item, ast.FunctionDef) and item.name == "build" for item in node.body
        )
        if has_build:
            providers.add(node.name)
        elif bases & BASE_CLASSES and not (bases & providers):
            problems.append(
                Problem(path, node.lineno, "missing-build", f"{node.name} 没有实现 build()")
            )
    return problems


def _has_star_import(tree: ast.Module) -> bool:
    """``from manim import *`` 会让所有名字都"可能存在"，此时无法静态判断未定义名。"""
    return any(
        isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)
        for node in tree.body
    )


def lint_file(path: str | Path) -> list[Problem]:
    """检查单个文件；返回空列表表示通过。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(p))
    except SyntaxError as exc:
        return [Problem(str(p), exc.lineno or 0, "syntax", exc.msg)]

    problems: list[Problem] = []
    problems.extend(_dup_imports(tree, str(p)))
    problems.extend(_dup_classes(tree, str(p)))
    if not _has_star_import(tree):
        problems.extend(_undefined_names(tree, str(p)))
    problems.extend(_missing_build(tree, str(p)))
    # 同一行同一个名字可能被 ast.walk 重复计入（父节点也会遍历到子节点），去重
    unique: list[Problem] = []
    for item in problems:
        if item not in unique:
            unique.append(item)
    return unique


def lint_paths(paths: list[str]) -> list[Problem]:
    """检查一组文件或目录（目录递归取 ``*.py``）。"""
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.is_file():
            files.append(p)
        else:
            files.extend(sorted(Path.cwd().rglob(f"{raw}.py")))
    problems: list[Problem] = []
    for f in files:
        problems.extend(lint_file(f))
    return problems
