#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft 皮肤头部拆分工具 · 蓝图排版版

主界面（轻量）：
    源文件 / 编辑流程 / 启动流程 / 流程下拉 / 蓝图编辑器 / 资源管理器 / 设置
    源文件、编辑流程、启动流程 会用曲线连到流程下拉，像节点编辑器一样。

流程编辑器（曲线连线，数据流）：
    源文件 → 暂停 → 蓝图 → 放大 → 重命名 → 导出
    源文件输出整张皮肤。蓝图节点输入一张图，按蓝图里“有效 Result”的数量
    长出对应输出点，再加一个“图组”输出；节点高度随端口数量自动变化。
    只有连在流程线上的节点会被执行，孤立的节点不会弹窗、不会导出。

蓝图编辑器（箭头连线）：
    输入（示例图，只在设计时参照）→ 画布 → Result
    · 选区：在示例图上拖框拉出来的矩形素材，自动命名 选区1、选区2……
    · 画布：固定尺寸的板子；映射 = 某个选区贴在画布上的坐标，
      列表顺序就是叠放顺序（后面的盖住前面的）。
    · Result：命名模板写在这里，输出的是画布合成图。
    · 一个 Result 只接一个画布；N 个有效 Result = 流程里 N 个输出点 + 图组。

命名模板：
    {L*2}{"cm"}{_}{W*2}{"cm"}      示例：8cm_4cm
    L / W 是结果图（画布）的像素宽高；另有 Time / Text / Skin / Canvas /
    Result / Index 等变量。

依赖:
    pip install pillow

运行:
    python skin_head_gui.py
"""

import math
import os
import re
import sys
import json
import base64
import traceback
import subprocess
import shutil
import zipfile
import ctypes
import urllib.request
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog

from PIL import Image, ImageTk, ImageDraw


# ====================================================================
# 常量与主题
# ====================================================================

ZOOM_MIN = 0.35
ZOOM_MAX = 2.5

APP_NAME = "BLUE"
APP_VERSION = "3.0.4beta"
APP_SUB = "图纸工坊 · Blueprint Layout & Usage Engine"
APP_TITLE = f"{APP_NAME} {APP_VERSION} — 图纸工坊"
APP_AUTHOR = "B站：拾贰Tuenztoo_"
APP_QQ = "2382488749"
APP_COST = "7.77"

THEMES = {
    "dark": {
        "BG":           "#16161a",
        "BG2":          "#1c1c22",
        "CARD":         "#222228",
        "CARD_HEADER":  "#292930",
        "FG":           "#e9e9ee",
        "ACCENT":       "#6cb4ff",
        "ACCENT_HOVER": "#8cc8ff",
        "ACCENT_FG":    "#0f1115",
        "MUTED":        "#85858f",
        "BORDER":       "#33333c",
        "HOVER":        "#2e2e37",
        "PORT_IMG":     "#6cb4ff",
        "PORT_TXT":     "#ffb86c",
        "OK":           "#7ee787",
        "DANGER":       "#ff7b72",
        "SHADOW":       "#0e0e12",
        "GRID":         "#232329",
        "BOARD":        "#2a2a32",
    },
    "light": {
        "BG":           "#eef0f4",
        "BG2":          "#f5f6fa",
        "CARD":         "#ffffff",
        "CARD_HEADER":  "#f7f8fa",
        "FG":           "#1a1a1f",
        "ACCENT":       "#0066cc",
        "ACCENT_HOVER": "#0055aa",
        "ACCENT_FG":    "#ffffff",
        "MUTED":        "#64646e",
        "BORDER":       "#d7d9e0",
        "HOVER":        "#e9ebf1",
        "PORT_IMG":     "#0066cc",
        "PORT_TXT":     "#b45309",
        "OK":           "#1a7f37",
        "DANGER":       "#c62828",
        "SHADOW":       "#c9ccd6",
        "GRID":         "#e4e6ec",
        "BOARD":        "#ffffff",
    },
    "sand": {
        "BG":           "#f3ede3",
        "BG2":          "#faf5ec",
        "CARD":         "#fffdf8",
        "CARD_HEADER":  "#f6ede0",
        "FG":           "#2b241c",
        "ACCENT":       "#b8642c",
        "ACCENT_HOVER": "#9c5120",
        "ACCENT_FG":    "#ffffff",
        "MUTED":        "#776a5c",
        "BORDER":       "#dfd2bf",
        "HOVER":        "#eee2d2",
        "PORT_IMG":     "#b8642c",
        "PORT_TXT":     "#8a5a12",
        "OK":           "#3f7d45",
        "DANGER":       "#b23a2e",
        "SHADOW":       "#d6c7b2",
        "GRID":         "#eadfce",
        "BOARD":        "#fffdf8",
    },
    "forest": {
        "BG":           "#0f1a16",
        "BG2":          "#14231d",
        "CARD":         "#192a23",
        "CARD_HEADER":  "#1e3229",
        "FG":           "#e8f1ea",
        "ACCENT":       "#62d39a",
        "ACCENT_HOVER": "#8de7b7",
        "ACCENT_FG":    "#0b1712",
        "MUTED":        "#8ba89a",
        "BORDER":       "#2b4539",
        "HOVER":        "#233b30",
        "PORT_IMG":     "#62d39a",
        "PORT_TXT":     "#e8b45c",
        "OK":           "#7ee787",
        "DANGER":       "#ff7b72",
        "SHADOW":       "#08100d",
        "GRID":         "#20352b",
        "BOARD":        "#1b2d25",
    },
    "sakura": {
        "BG":           "#fbf1f4",
        "BG2":          "#fff7f9",
        "CARD":         "#ffffff",
        "CARD_HEADER":  "#fbe8ef",
        "FG":           "#33232a",
        "ACCENT":       "#c94f7c",
        "ACCENT_HOVER": "#a93d66",
        "ACCENT_FG":    "#ffffff",
        "MUTED":        "#816a74",
        "BORDER":       "#ecd2dc",
        "HOVER":        "#f7e2e9",
        "PORT_IMG":     "#c94f7c",
        "PORT_TXT":     "#9a5b18",
        "OK":           "#2f7d4f",
        "DANGER":       "#b23a4a",
        "SHADOW":       "#e5cdd6",
        "GRID":         "#f5dde6",
        "BOARD":        "#ffffff",
    },
}

CHECKER_PRESETS = {
    "dark":  ("#3a3a44", "#2c2c35"),
    "light": ("#e8e8ec", "#d8d8dc"),
    "sand":  ("#eadcc8", "#dfcfb8"),
    "forest": ("#2b4638", "#21382c"),
    "sakura": ("#f7e1e9", "#edd0db"),
}

NODE_COLORS = {
    "source":    "#5aa9e6",
    "pause":     "#e0a53c",
    "blueprint": "#a78bfa",
    "make":      "#56cfe1",
    "break":     "#f78fb3",
    "upscale":   "#3fb6a0",
    "rename":    "#4caf7d",
    "export":    "#e8705f",
}

if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).resolve().parent
else:
    SCRIPT_DIR = Path(__file__).resolve().parent

SETTINGS_FILE = SCRIPT_DIR / "skin_head_settings.json"
WORKFLOWS_DIR = SCRIPT_DIR / "workflows"
BLUEPRINTS_DIR = SCRIPT_DIR / "blueprints"

for _d in (WORKFLOWS_DIR, BLUEPRINTS_DIR):
    try:
        _d.mkdir(exist_ok=True)
    except Exception:
        pass


# ====================================================================
# 小工具
# ====================================================================

def make_checker(w, h, c1, c2, cell=8):
    if w <= 0 or h <= 0:
        return Image.new("RGB", (max(1, w), max(1, h)), c1)
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=c2)
    return img


class IconButton(tk.Canvas):
    """细线图标按钮，避免用一串文字当工具栏。"""

    def __init__(self, parent, kind, command, bg, fg, hover_bg,
                 hover_fg=None, size=28, accent=None, tip=""):
        super().__init__(parent, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.kind = kind
        self.command = command
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg or fg
        self.size = size
        self.accent = accent or fg
        self.tip = tip
        self._tip = None
        self._tip_job = None
        self._anim_job = None
        self._cur_bg = bg
        self._cur_fg = fg
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self._draw(self.fg, self.bg)

    def _draw(self, color, bg):
        self.configure(bg=bg)
        self.delete("all")
        s = self.size
        p = 6
        w = 2
        # 圆角底板
        self.create_rectangle(1, 1, s - 2, s - 2, outline="", fill=bg)
        if self.kind == "plus":
            self.create_line(s / 2, p, s / 2, s - p, fill=color, width=w)
            self.create_line(p, s / 2, s - p, s / 2, fill=color, width=w)
        elif self.kind == "copy":
            self.create_rectangle(p + 3, p, s - p, s - p - 3,
                                  outline=color, width=w)
            self.create_rectangle(p, p + 4, s - p - 3, s - p,
                                  outline=color, width=w)
        elif self.kind == "trash":
            self.create_line(p, p + 4, s - p, p + 4, fill=color, width=w)
            self.create_line(s / 2 - 4, p + 1, s / 2 + 4, p + 1,
                             fill=color, width=w)
            self.create_line(p + 3, p + 4, p + 4, s - p,
                             fill=color, width=w)
            self.create_line(s - p - 3, p + 4, s - p - 4, s - p,
                             fill=color, width=w)
            self.create_line(p + 4, s - p, s - p - 4, s - p,
                             fill=color, width=w)
        elif self.kind == "folder":
            self.create_line(p, p + 4, p, s - p, s - p, s - p,
                             s - p, p + 8, fill=color, width=w)
            self.create_line(p, p + 4, s / 2 - 2, p + 4,
                             s / 2 + 1, p, s - p, p + 4, fill=color, width=w)
        elif self.kind == "open":
            self.create_line(p, p + 5, p, s - p, s - p, s - p,
                             fill=color, width=w)
            self.create_line(p, p + 5, s / 2 - 2, p + 5,
                             s / 2 + 2, p + 1, s - p, p + 5,
                             fill=color, width=w)
            self.create_line(s - p - 7, s - p - 9, s - p - 2, s - p - 9,
                             s - p - 2, s - p - 4, fill=color, width=w)
            self.create_line(s - p - 7, s - p - 9, s - p - 2, s - p - 4,
                             fill=color, width=w)
        elif self.kind == "save":
            self.create_rectangle(p, p, s - p, s - p,
                                  outline=color, width=w)
            self.create_rectangle(p + 3, p + 3, s - p - 4, s - p - 8,
                                  outline=color, width=1)
            self.create_rectangle(p + 4, s - p - 6, s - p - 4, s - p - 1,
                                  outline=color, width=1)
        elif self.kind == "min":
            self.create_line(p, s / 2, s - p, s / 2, fill=color, width=w)
        elif self.kind == "max":
            self.create_rectangle(p, p, s - p, s - p, outline=color, width=w)
        elif self.kind == "restore":
            self.create_rectangle(p + 3, p, s - p, s - p - 3,
                                  outline=color, width=w)
            self.create_rectangle(p, p + 3, s - p - 3, s - p,
                                  outline=color, width=w)
        elif self.kind == "close":
            self.create_line(p, p, s - p, s - p, fill=color, width=w)
            self.create_line(s - p, p, p, s - p, fill=color, width=w)

    def _enter(self, _e=None):
        self._animate(self.hover_fg, self.hover_bg)
        if self.tip:
            self._tip_job = self.after(350, self._show_tip)

    def _leave(self, _e=None):
        if self._tip_job:
            try:
                self.after_cancel(self._tip_job)
            except Exception:
                pass
            self._tip_job = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
        self._animate(self.fg, self.bg)

    def _animate(self, fg, bg, step=0, steps=7):
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        if step == 0:
            self._from_fg, self._from_bg = self._cur_fg, self._cur_bg
        t = step / steps
        e = 1 - (1 - t) ** 2
        c1 = self._mix(self._from_fg, fg, e)
        c2 = self._mix(self._from_bg, bg, e)
        self._cur_fg, self._cur_bg = c1, c2
        self._draw(c1, c2)
        if step < steps:
            self._anim_job = self.after(
                18, lambda: self._animate(fg, bg, step + 1, steps))

    @staticmethod
    def _mix(a, b, t):
        try:
            a = a.lstrip("#")
            b = b.lstrip("#")
            return "#%02x%02x%02x" % tuple(
                int(int(a[i:i + 2], 16) * (1 - t) +
                    int(b[i:i + 2], 16) * t) for i in (0, 2, 4))
        except Exception:
            return b

    def _show_tip(self):
        if self._tip is not None:
            return
        try:
            x = self.winfo_rootx() + 8
            y = self.winfo_rooty() + self.size + 4
            top = tk.Toplevel(self)
            top.overrideredirect(True)
            top.configure(bg="#1d1d24")
            tk.Label(top, text=self.tip, bg="#1d1d24", fg="#e9e9ee",
                     font=("Microsoft YaHei", 8), padx=8, pady=4).pack()
            top.geometry(f"+{x}+{y}")
            self._tip = top
        except Exception:
            pass


class SlimScrollbar(tk.Canvas):
    """自绘细滚动条：无箭头、无系统边框。"""

    def __init__(self, parent, command, bg, thumb, hover, width=9):
        super().__init__(parent, width=width, bg=bg,
                         highlightthickness=0, bd=0)
        self.command = command
        self.width = width
        self.bg = bg
        self.thumb = thumb
        self.hover = hover
        self._first = 0.0
        self._last = 1.0
        self._drag = None
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", lambda e: self._draw(self.hover))
        self.bind("<Leave>", lambda e: self._draw())

    def set(self, first, last):
        try:
            self._first = max(0.0, min(1.0, float(first)))
            self._last = max(0.0, min(1.0, float(last)))
        except (TypeError, ValueError):
            self._first, self._last = 0.0, 1.0
        self._draw()

    def _geom(self):
        h = max(1, self.winfo_height())
        y1 = int(self._first * h)
        y2 = max(y1 + 18, int(self._last * h))
        return h, y1, min(y2, h)

    def _draw(self, color=None):
        self.delete("all")
        h, y1, y2 = self._geom()
        if self._last - self._first >= 0.999:
            self.create_rectangle(2, 2, self.width - 2, h - 2,
                                  fill=self.bg, outline="")
            return
        self.create_rectangle(2, y1 + 1, self.width - 2, y2 - 1,
                              fill=color or self.thumb, outline="")
        self.create_rectangle(2, y1, self.width - 2, y1 + 6,
                              fill=color or self.thumb, outline="")
        self.create_rectangle(2, y2 - 6, self.width - 2, y2,
                              fill=color or self.thumb, outline="")

    def _press(self, event):
        h, y1, y2 = self._geom()
        if y1 <= event.y <= y2:
            self._drag = event.y - y1
        else:
            self.command("moveto", max(0.0, min(0.999, event.y / max(1, h))))
            self._drag = (y2 - y1) // 2

    def _motion(self, event):
        if self._drag is None:
            return
        h = max(1, self.winfo_height())
        frac = (event.y - self._drag) / h
        self.command("moveto", max(0.0, min(0.999, frac)))

    def _release(self, _event=None):
        self._drag = None


def flatten_on_bg(img, bg_rgb):
    """把 RGBA 图压到纯色背景上（导出时可选）。"""
    if img.mode == "RGB":
        return img
    bg = Image.new("RGB", img.size, tuple(bg_rgb))
    bg.paste(img, (0, 0), img)
    return bg


def sanitize_name(name):
    name = (name or "").strip()
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name)
    name = name.strip(" .")
    return name


def ask_import_name(parent, folder, base):
    """导入外部 JSON 时，保证 workflows/blueprints 里名字不冲突。"""
    name = sanitize_name(base) or "导入"
    while True:
        if not (Path(folder) / f"{name}.json").exists():
            return name
        new = simpledialog.askstring(
            "重名", f"{name}.json 已经存在，换个名字：",
            initialvalue=f"{name}_2", parent=parent)
        if not new:
            return None
        name = sanitize_name(new) or name


def fmt_num(v, max_digits=4):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(f - round(f)) < 1e-6:
        return str(int(round(f)))
    s = f"{f:.{max_digits}f}".rstrip("0").rstrip(".")
    return s if s else "0"


def open_in_file_manager(path):
    path = Path(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        messagebox.showerror("打开失败", f"无法打开：\n{path}\n\n{exc}")


def load_rgba(path):
    with Image.open(path) as im:
        return im.convert("RGBA")


# ====================================================================
# 图像数据模型
# ====================================================================

class ImageItem:
    """流程里流动的一张图。

    - name       名字（蓝图 Result 命名 / 重命名会改它）
    - image      PIL.Image
    - part       skin / custom（来源标记）
    - px_scale   放大倍数（图片像素 = 逻辑像素 × px_scale）
    - result     来自蓝图的哪个 Result（打包用）
    """

    __slots__ = ("name", "image", "part", "px_scale", "result")

    def __init__(self, name, image, part="custom", px_scale=1, result=""):
        self.name = name
        self.image = image
        self.part = part
        self.px_scale = max(1, int(px_scale))
        self.result = result

    @property
    def logic_w(self):
        return self.image.width / self.px_scale

    @property
    def logic_h(self):
        return self.image.height / self.px_scale

    def copy(self, name=None, result=None):
        return ImageItem(
            self.name if name is None else name,
            self.image,
            self.part,
            self.px_scale,
            self.result if result is None else result,
        )

    def scaled(self, factor):
        factor = max(1, int(factor))
        item = self.copy()
        item.image = self.image.resize(
            (self.image.width * factor, self.image.height * factor),
            Image.NEAREST)
        item.px_scale = self.px_scale * factor
        return item

    def __repr__(self):
        return f"<ImageItem {self.name!r} {self.image.size}>"


class Payload:
    """一组 ImageItem（流程里“图像”端口传的就是它）。"""

    def __init__(self, items=None):
        self.items = list(items or [])

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def add(self, item):
        self.items.append(item)

    def extend(self, other):
        if isinstance(other, Payload):
            self.items.extend(other.items)
        else:
            self.items.extend(other)
        return self

    def is_empty(self):
        return not self.items

    def __repr__(self):
        return f"<Payload {[it.name for it in self.items]}>"


def build_source_payload(skin_path):
    """整张皮肤原图作为唯一输入（不再预先拆分）。"""
    img = load_rgba(skin_path)
    scale = max(1, img.width // 64)
    return Payload([ImageItem(Path(skin_path).stem, img, "skin", scale)])


def logical_size(item):
    return int(round(item.logic_w)), int(round(item.logic_h))


def default_image_name(item, skin, index=1):
    """没有模板命名时的兜底：皮肤名_宽x高。"""
    w, h = logical_size(item)
    base = sanitize_name(item.name)
    if not base or base in ("1", "2", "eye") or item.part == "skin":
        base = sanitize_name(skin) or "image"
    return f"{base}_{w}x{h}"

# ====================================================================
# 命名模板引擎：{L*2}{"cm"}{_}{W*2}{"cm"}
# ====================================================================

class TemplateError(Exception):
    pass


VAR_HELP = (
    ("L", "结果图横向像素（画布宽）"),
    ("W", "结果图纵向像素（画布高）"),
    ("Time", "时间，例如 202610310303"),
    ("Text", "字符输入的文本"),
    ("Skin", "皮肤文件名"),
    ("Canvas", "画布名字"),
    ("Result", "Result 名字"),
    ("Index", "序号，从 1 开始"),
    ("Name", "图像 / 画布名字"),
)

_VAR_ALIASES = {
    "长": "L", "宽": "W", "时间": "Time", "名字": "Name", "名称": "Name",
    "文字": "Text", "皮肤": "Skin", "画布": "Canvas", "序号": "Index",
    "name": "Name", "text": "Text", "skin": "Skin", "time": "Time",
    "canvas": "Canvas", "index": "Index", "result": "Result",
    "px_l": "L", "px_w": "W",
}

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_NAME_RE = re.compile(r"[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*")
# 支持英文引号，也支持中文弯引号（方便直接粘贴示例）
_QUOTE_PAIRS = {'"': '"', "'": "'", "“": "”", "‘": "’"}


def _num(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    text = str(v).strip()
    try:
        return float(text)
    except ValueError:
        raise TemplateError(f"“{v}”不是数字")


def format_value(v):
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)


def _op_add(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return format_value(a) + format_value(b)
    return _num(a) + _num(b)


def _op_sub(a, b):
    return _num(a) - _num(b)


def _op_mul(a, b):
    return _num(a) * _num(b)


def _op_div(a, b):
    b = _num(b)
    if b == 0:
        raise TemplateError("除以 0")
    return _num(a) / b


def _op_mod(a, b):
    b = _num(b)
    if b == 0:
        raise TemplateError("对 0 取余")
    return _num(a) % b


def _f_round(args):
    if not args:
        raise TemplateError("round 需要参数")
    digits = int(_num(args[1])) if len(args) > 1 else 0
    return round(_num(args[0]), digits)


def _f_int(args):
    if not args:
        raise TemplateError("int 需要参数")
    return int(_num(args[0]))


def _f_str(args):
    if not args:
        raise TemplateError("str 需要参数")
    return format_value(args[0])


_FUNCS = {
    "round": (_f_round, (1, 2)),
    "int": (_f_int, (1,)),
    "str": (_f_str, (1,)),
    "abs": (lambda a: abs(_num(a[0])), (1,)),
    "floor": (lambda a: math.floor(_num(a[0])), (1,)),
    "ceil": (lambda a: math.ceil(_num(a[0])), (1,)),
    "upper": (lambda a: str(a[0]).upper(), (1,)),
    "lower": (lambda a: str(a[0]).lower(), (1,)),
    "max": (lambda a: max(_num(x) for x in a), (1, 9)),
    "min": (lambda a: min(_num(x) for x in a), (1, 9)),
}


def _call_func(name, args):
    entry = _FUNCS.get(name)
    if entry is None:
        raise TemplateError(f"未知函数：{name}")
    fn, (lo, hi) = entry
    if len(args) < lo or len(args) > hi:
        raise TemplateError(f"{name} 的参数个数不对")
    try:
        return fn(args)
    except TemplateError:
        raise
    except Exception as exc:
        raise TemplateError(f"{name} 计算失败：{exc}") from exc


class _ExprParser:
    def __init__(self, text, variables):
        self.text = text
        self.pos = 0
        self.variables = variables

    def error(self, msg):
        raise TemplateError(f"{msg}（表达式：{self.text.strip()}）")

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def ws(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def parse(self):
        self.ws()
        if self.pos >= len(self.text):
            return ""
        value = self.expr()
        self.ws()
        if self.pos < len(self.text):
            self.error(f"多余的字符：{self.text[self.pos:]}")
        return value

    def expr(self):
        value = self.term()
        while True:
            self.ws()
            ch = self.peek()
            if ch == "+":
                self.pos += 1
                value = _op_add(value, self.term())
            elif ch == "-":
                self.pos += 1
                value = _op_sub(value, self.term())
            else:
                return value

    def term(self):
        value = self.unary()
        while True:
            self.ws()
            ch = self.peek()
            if ch == "*":
                self.pos += 1
                value = _op_mul(value, self.unary())
            elif ch == "/":
                self.pos += 1
                value = _op_div(value, self.unary())
            elif ch == "%":
                self.pos += 1
                value = _op_mod(value, self.unary())
            else:
                return value

    def unary(self):
        self.ws()
        ch = self.peek()
        if ch == "-":
            self.pos += 1
            return -_num(self.unary())
        if ch == "+":
            self.pos += 1
            return self.unary()
        return self.atom()

    def atom(self):
        self.ws()
        text = self.text
        i = self.pos
        if i >= len(text):
            self.error("表达式不完整")
        ch = text[i]

        if ch in _QUOTE_PAIRS:
            end_ch = _QUOTE_PAIRS[ch]
            end = text.find(end_ch, i + 1)
            if end < 0:
                self.error("字符串没有闭合")
            self.pos = end + 1
            return text[i + 1:end]

        if ch.isdigit() or (ch == "." and i + 1 < len(text) and text[i + 1].isdigit()):
            m = _NUM_RE.match(text, i)
            self.pos = m.end()
            raw = m.group(0)
            return float(raw) if "." in raw else int(raw)

        if ch == "(":
            self.pos += 1
            value = self.expr()
            self.ws()
            if self.peek() != ")":
                self.error("缺少右括号")
            self.pos += 1
            return value

        m = _NAME_RE.match(text, i)
        if not m:
            self.error(f"看不懂的字符：{ch}")
        name = m.group(0)
        self.pos = m.end()
        self.ws()
        if self.peek() == "(":
            self.pos += 1
            args = []
            self.ws()
            if self.peek() == ")":
                self.pos += 1
            else:
                while True:
                    args.append(self.expr())
                    self.ws()
                    c = self.peek()
                    if c == ",":
                        self.pos += 1
                        continue
                    if c == ")":
                        self.pos += 1
                        break
                    self.error("函数参数缺少逗号或右括号")
            return _call_func(name, args)

        if name in self.variables:
            return self.variables[name]
        alias = _VAR_ALIASES.get(name)
        if alias and alias in self.variables:
            return self.variables[alias]
        raise TemplateError(f"未知变量：{name}")


def eval_expression(expr, variables):
    s = expr.strip()
    if not s:
        return ""
    # {_} / {-} 这种纯符号块当字面量，其它未知名字按变量报错
    if re.fullmatch(r"[_\-.#/\\]+", s):
        return s
    return _ExprParser(s, variables).parse()


def render_template(template, variables):
    template = "" if template is None else str(template)
    out = []
    i = 0
    n = len(template)
    while i < n:
        ch = template[i]
        if ch == "{":
            j = template.find("}", i + 1)
            if j < 0:
                raise TemplateError(f"大括号没有闭合：{template[i:]}")
            value = eval_expression(template[i + 1:j], variables)
            out.append(format_value(value))
            i = j + 1
        else:
            j = template.find("{", i)
            if j < 0:
                j = n
            out.append(template[i:j])
            i = j
    return "".join(out)


def item_variables(item, text, ctx, index=1):
    """重命名 / 导出 里一张图能用的变量（像素）。"""
    now = ctx.get("now") or datetime.now()
    w, h = logical_size(item)
    return {
        "L": w,
        "W": h,
        "Time": now.strftime("%Y%m%d%H%M"),
        "Date": now.strftime("%Y%m%d"),
        "Name": item.name,
        "Text": text or "",
        "Skin": ctx.get("skin", ""),
        "Part": item.part,
        "Index": index,
        "Result": item.result or "",
        "Canvas": item.name,
    }


def result_variables(canvas, result, text, ctx, index=1):
    """Result 命名能用的变量：L / W 是画布（结果图）像素。"""
    now = ctx.get("now") or datetime.now()
    return {
        "L": int(canvas.width),
        "W": int(canvas.height),
        "Time": now.strftime("%Y%m%d%H%M"),
        "Date": now.strftime("%Y%m%d"),
        "Name": canvas.name,
        "Canvas": canvas.name,
        "Text": text or "",
        "Skin": ctx.get("skin", ""),
        "Index": index,
        "Result": result.name,
    }


def template_sample_vars(text="示例"):
    """蓝图编辑器里的示例预览用。"""
    now = datetime.now()
    return {
        "L": 64, "W": 64,
        "Time": now.strftime("%Y%m%d%H%M"),
        "Date": now.strftime("%Y%m%d"),
        "Name": "画布 1", "Canvas": "画布 1", "Text": text,
        "Skin": "皮肤", "Index": 1, "Result": "result1",
    }


# ====================================================================
# 蓝图数据模型（v2）
#   输入：一张示例图（只在设计时当参照）
#   选区：在示例图上拉的矩形 (x, y, w, h)
#   画布：固定尺寸，映射 = 某个选区 + 画布坐标，按列表顺序叠放
#   Result：命名模板，一个 Result 只接一个画布
# ====================================================================

BP_VERSION = 2
DEFAULT_CANVAS_W = 64
DEFAULT_CANVAS_H = 64
DEFAULT_RESULT_TEMPLATE = '{Skin}{"_"}{L}{"x"}{W}'

DEFAULT_BLUEPRINT_JSON = r'''{
  "version": 2,
  "name": "基础",
  "ref_image": "基础_ref.png",
  "image_w": 64,
  "image_h": 64,
  "next_id": 9,
  "next_sel": 9,
  "next_map": 13,
  "next_rect": 4,
  "selections": [
    {
      "id": 1,
      "name": "11",
      "x": 0,
      "y": 8,
      "w": 24,
      "h": 8
    },
    {
      "id": 2,
      "name": "12",
      "x": 8,
      "y": 0,
      "w": 16,
      "h": 8
    },
    {
      "id": 3,
      "name": "13",
      "x": 24,
      "y": 8,
      "w": 8,
      "h": 8
    },
    {
      "id": 4,
      "name": "21",
      "x": 32,
      "y": 8,
      "w": 24,
      "h": 8
    },
    {
      "id": 5,
      "name": "23",
      "x": 56,
      "y": 8,
      "w": 8,
      "h": 8
    },
    {
      "id": 6,
      "name": "22",
      "x": 40,
      "y": 0,
      "w": 16,
      "h": 8
    },
    {
      "id": 7,
      "name": "选区7",
      "x": 9,
      "y": 13,
      "w": 2,
      "h": 2
    },
    {
      "id": 8,
      "name": "选区8",
      "x": 13,
      "y": 13,
      "w": 2,
      "h": 2
    }
  ],
  "nodes": [
    {
      "id": 1,
      "kind": "input",
      "name": "示例皮肤",
      "x": -48,
      "y": 300
    },
    {
      "id": 2,
      "kind": "canvas",
      "name": "画布 1",
      "x": 316.0,
      "y": 108.0,
      "width": 24,
      "height": 16,
      "mappings": [
        {
          "id": 1,
          "kind": "selection",
          "ref_id": 1,
          "x": 0,
          "y": 8
        },
        {
          "id": 2,
          "kind": "selection",
          "ref_id": 2,
          "x": 8,
          "y": 0
        },
        {
          "id": 3,
          "kind": "selection",
          "ref_id": 3,
          "x": 0,
          "y": 0
        },
        {
          "id": 4,
          "kind": "rect",
          "ref_id": 1,
          "x": 9,
          "y": 13
        },
        {
          "id": 8,
          "kind": "rect",
          "ref_id": 2,
          "x": 13,
          "y": 13
        },
        {
          "id": 10,
          "kind": "rect",
          "ref_id": 3,
          "x": 17,
          "y": 1
        }
      ]
    },
    {
      "id": 3,
      "kind": "result",
      "name": "result1",
      "x": 704,
      "y": 116,
      "template": ""
    },
    {
      "id": 4,
      "kind": "canvas",
      "name": "画布 2",
      "x": 312.0,
      "y": 268.0,
      "width": 24,
      "height": 16,
      "mappings": [
        {
          "id": 5,
          "kind": "selection",
          "ref_id": 4,
          "x": 0,
          "y": 8
        },
        {
          "id": 6,
          "kind": "selection",
          "ref_id": 5,
          "x": 0,
          "y": 0
        },
        {
          "id": 7,
          "kind": "selection",
          "ref_id": 6,
          "x": 8,
          "y": 0
        }
      ]
    },
    {
      "id": 5,
      "kind": "rect",
      "name": "矩形 1",
      "x": -52,
      "y": 132,
      "rects": [
        {
          "id": 1,
          "name": "矩形1",
          "w": 2,
          "h": 2,
          "color": "#ffffff"
        },
        {
          "id": 2,
          "name": "矩形2",
          "w": 2,
          "h": 2,
          "color": "#ffffff"
        },
        {
          "id": 3,
          "name": "矩形3",
          "w": 6,
          "h": 6,
          "color": "#ffffff"
        }
      ]
    },
    {
      "id": 6,
      "kind": "result",
      "name": "result2",
      "x": 704,
      "y": 276,
      "template": ""
    },
    {
      "id": 7,
      "kind": "canvas",
      "name": "画布 3",
      "x": 316,
      "y": 432,
      "width": 8,
      "height": 2,
      "mappings": [
        {
          "id": 11,
          "kind": "selection",
          "ref_id": 7,
          "x": 1,
          "y": 0
        },
        {
          "id": 12,
          "kind": "selection",
          "ref_id": 8,
          "x": 5,
          "y": 0
        }
      ]
    },
    {
      "id": 8,
      "kind": "result",
      "name": "result3",
      "x": 708,
      "y": 440,
      "template": ""
    }
  ],
  "edges": [
    [
      1,
      2
    ],
    [
      2,
      3
    ],
    [
      1,
      4
    ],
    [
      5,
      2
    ],
    [
      4,
      6
    ],
    [
      1,
      7
    ],
    [
      7,
      8
    ]
  ]
}'''

DEFAULT_WORKFLOW_JSON = r'''{
  "name": "默认流程",
  "next_id": 15,
  "nodes": [
    {
      "id": 1,
      "type": "source",
      "x": -48,
      "y": 84,
      "params": {
        "path": ""
      },
      "skip": false
    },
    {
      "id": 2,
      "type": "pause",
      "x": 256,
      "y": 48,
      "params": {
        "mode": "询问",
        "message": "输入这次结果的名字（可留空）",
        "default": "",
        "open_folder": false
      },
      "skip": false
    },
    {
      "id": 3,
      "type": "blueprint",
      "x": 584,
      "y": 48,
      "params": {
        "name": "基础"
      },
      "skip": false
    },
    {
      "id": 4,
      "type": "export",
      "x": 2176,
      "y": 84,
      "params": {
        "dir": "",
        "pattern": "",
        "overwrite": false
      },
      "skip": false
    },
    {
      "id": 6,
      "type": "rename",
      "x": 1496,
      "y": -72,
      "params": {
        "pattern": "{Text}{“_90cm_60cm_一层”}",
        "indexed": true
      },
      "skip": false
    },
    {
      "id": 7,
      "type": "rename",
      "x": 1508,
      "y": 60,
      "params": {
        "pattern": "{Text}{“_”}{L*4.125}{\"cm_\"}{W*4.125}{\"cm_二层\"}",
        "indexed": true
      },
      "skip": false
    },
    {
      "id": 9,
      "type": "pause",
      "x": 880,
      "y": 56,
      "params": {
        "mode": "提示",
        "message": "请改进二层皮肤",
        "default": "",
        "open_folder": true
      },
      "skip": false
    },
    {
      "id": 10,
      "type": "upscale",
      "x": 1840,
      "y": 152,
      "params": {
        "factor": 64
      },
      "skip": false
    },
    {
      "id": 11,
      "type": "break",
      "x": 1164,
      "y": 52,
      "params": {
        "count": 3
      },
      "skip": false
    },
    {
      "id": 13,
      "type": "rename",
      "x": 1508,
      "y": 192,
      "params": {
        "pattern": "{Text}{\"_eyes\"}",
        "indexed": true
      },
      "skip": false
    },
    {
      "id": 14,
      "type": "make",
      "x": 1836,
      "y": 0,
      "params": {
        "count": 3
      },
      "skip": false
    }
  ],
  "edges": [
    [
      1,
      "image",
      2,
      "image"
    ],
    [
      2,
      "image",
      3,
      "image"
    ],
    [
      2,
      "answer",
      3,
      "text"
    ],
    [
      2,
      "answer",
      6,
      "text"
    ],
    [
      2,
      "answer",
      7,
      "text"
    ],
    [
      2,
      "answer",
      4,
      "text"
    ],
    [
      3,
      "group",
      9,
      "image"
    ],
    [
      10,
      "image",
      4,
      "image"
    ],
    [
      9,
      "image",
      11,
      "group"
    ],
    [
      11,
      "out1",
      6,
      "image"
    ],
    [
      11,
      "out2",
      7,
      "image"
    ],
    [
      11,
      "out3",
      13,
      "image"
    ],
    [
      2,
      "answer",
      13,
      "text"
    ],
    [
      6,
      "image",
      14,
      "in1"
    ],
    [
      7,
      "image",
      14,
      "in2"
    ],
    [
      13,
      "image",
      14,
      "in3"
    ],
    [
      14,
      "group",
      10,
      "image"
    ]
  ]
}'''

DEFAULT_BLUEPRINT_REF_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAOAUlEQVR4nO1ba6xcVRX+9uOcOTNz751WikgMmugPSAPSgoC0ieEf/CSBVuQhVkGtqRGVP0aNBTUm8EOR0IoYMEEo0BCkESJI8REqFSqQ/gDfGjVKQwpt770zcx57L7PWPmfuzH1Dp2EKrGTnvPbZZ6+1117vo7AEfPy888mgDVLlDdJy8OW1cw6tVguHpyYR2Rq8I9RqNTgoFMZgx+5fVW+OJOilOtAC95VS0qIownSnjTiOA1GMkdZpd2CiCKMOdqkOShMUGRDcwMqDSLiCL+99+GGg0wGSBmBrQKcNaIurr70Gow5qqQ6XrT+PIpfDUVG+YHpEYALs+NlDgNFAox4Yim+mKaAMoAhqxUnquOYAGN7oggu888z70Iww32bUkpj5IjTngoyI+CWmRTge31tAhQUkInjvGH8Y3v+6XFgFeA1oXnzyIjS8qgQlE2a0QS/ZQxloXv4SmBDOFSBPMwSojkIML4hzW0iAjhLo227bMLZYBwVGpkSyBAdC7gs5wntoJoYjGA9o5xF5D+shx1EHdeVHP7zoQikfpH8FpE3vHp8fLfz0t/vUiMgAP7ArmNWr/S9PyUMrjSLryn1rrBCCicCqvwItUjMYTDwGOQ+nj44TLlpzBum+ZSKtoIzGo/teUEOUAXrgUimCRgGLLKy6ieRo4wTWKthIo3CZ9GXhX7XcOWnO5fCeVaeHdgTtnTTLneaBjWefRtz671267my5XlEzGEtqvTYexxgrNdGl684ZeGfjujNp4/oz6HVxgOpbaV61ihye1zPrImofwJ2/eRZIakCWibHzqfPPQNJoIY9Y/8+FylYQ+VB+oze2YyNKY2BZ5yGIJo8rPnKmKBewYC0XSPMZeVx+7hryVOCS9efQg3uelS9GbK/IC/OPyccH/vBHtaAW8J5Xr4C2EQ5NpXLv4b9N4YTT1iJrd5EVHqs+eDp2/b0jz7rtdq/1A7k8NCrgfQ5XFNKYa3zBrQuXp7h83Zo5VPjY+rPIJEmwPRhdpXHf759TxJpFeTnne0xk7hO7AhvXrZVxPKw0hkvXryVuCxH5kvVrSQf97nstTVPcu2sX7rrvfsRRArQP48///g92PvaL3osP7X4cL/3zH/Js2kOe7XziibDSbCswu1e2gPconEOWZchzJoSTreG8D7YFG1dzwGPHnhcUG5XcGGG+u3PvcyotRUwgQjjfsfd5ttj7IHzbeo9o/h0nELO24kn1Q9rNgZx1WIwHH/k5PCnoE1oYP1Tr9WmOxTjxxBNx51MvBquPt4WjWVwQEJvN5Y6vZSuw0AAoasyZ2P17gnAT9TtLzO3aE4ghY/FZeXXf08/PsHW5BQplFzV0SHmoi8/9EMt3oRqLPRs3kBYejWQcO3c9hCz97yJDAPH4CbjsogsR6widIwfnPK8msxD078c3A9TsG9d++mvkkAj1oLvYv+8RQLfhWdcpg/17F1c9WzbfRIc7OZK6RppNizbJnUKu2GfQiJnljUOaFMg1uxoJjNeInIfxXdx9x3cWHf/qq75KdbsSrpjE9h/cCKNyQGdQE2NqKL5AjhXIVAO5ttBqCpmJEaELTRqqDIYsBgc7ClNFDU1PcBQLzztdQxY1oVATX8mZDJ2og9ywFRlDFwYcOYjV0vEDTw0UNIaCrVH2SzQvVPBU3xAB7tp63YpNW79/qLoRFQmcTsT7Zzkme/h10LbWBKgg3Hbz9eDF4Vc7Hrh8y41Y9Z73gToFlDJwBT9T0JRDS/xIi6pbkgDGCQG9ypEbJhrfe8P4w/YjL8ArjQJGscU3BSg2dnhiZlne8+RUikhpxF2gTgBbyxMNYNV4E2DjCECWE4i0OFmabQ2vob1dOPzUB05ZFOyh8FEDKdsXan5bZDmgNn1mK2Upr/Q4rGmim05hxaoa9u57FNR9BbCdIEl9AvgGTl99nhy5kbXItMN01hZ93KxPIKc6dATcc8tm+UA0DeRN4IovbkceEXxm0c1SFNYjjg0iZaCcgeGtQAWsmRQLFGRly5FiVilK19rC5zUYk4gqNToHxysZUh2LyvSujXpc4J5tNy6Lb22KJnLtYJj6pgNvprD7yV0YSzqyIDIZWfky6MET4Ulp5gwLR2PIea+rArFpoB5PIM0Py+CPXXAuasbggt1PY1xN4zVfl0nmogsVjGU1xatfcgAbPZTA8/iUlFMMlh2rLPEvNIfneNVZa1l4lYixVKAhHEQcnPDdZXOA/esLv0SR51A8oGHWzFCv8QCBgM7p4OzwKuhJ7H/xSZBYKPzRCaxeczFcbuF1gVwV6Ez+D02ODbI86POSJqmJsfEEhw/zfjfiRhtGngohghAVJaJlkCUgXE2F+/CB7ZZguzBXMOcFr6UU0Pr1BWKsUVPwyOTFyFhkhZOIj4zFUR9WX6WRGTigAKkyQMorIBK4lA1sr4sDFCB1boAIrx58FcaOS4yhZ69Xky1jjmHc0iPtZ2KmRNW3D0HpI/MLnARvoWlpWVWBznyB1LMHR4I8M5YqJ+fZkeEPE7sfzOY1EHiv1eE1s3MNRjlYlSMmDohotJotKJfKnr/w188IEdjYq0UeY40xQT6sl5dz1gjMEcJ9xpXhtOCKsTAWY49CYIaP/A1uqmrlvVpuERcWcZ4gyudalwuBrcxNXnRxungCpddW0qi3AtyP919PWovG8EF+yGBlYNjUAK2ECA888ww2Xrsdulatip9lJle2xcyqhvsVZ2DA/qje4fnydhEuVLKJ5pjdyyIA5oEB1lvEmuYPVm22zS4oGCXIh0HDOEZ5mDLGGDwYGni3QqIvDClGWP+z6pzVoGNxwia8YRnFW7QNGw16pouBnn0jeIehLQbVBHkifF5NjkPmRnOwJOxpshqOty+vUn/oaAkIixC2Q0WgGeeo2iZhe4ZnQV2K3SICdXlg2VnhJgI2oDDYg4lRIV1mgqrJzKYeI8mBDw6fsZtbSyIhCKfJOKphdNRLqYX+c9mGJXrv03zFpm7wHWf6lEjzFrCiNTyU9rCMhysVxXIJkKYpsizvrRy7v1XI+8iRI1jZavUQDhOcIQBRBC2BURacbCvyEpH4/nEtRrfbEaJEkZU4Q0UgQV5sSxUiy/OAxCQph8onObrSiyaJ+hXJGJaFDaVKQDKRa4qQzEPYBQnQ7XYlYKEKJQRgHd/P/jzx8KES8b6XPUWiMnU5uTzLxBDhRGk3y2DisOJCkDiWsajiNmL20yDHkr9v0BIxxiGiDHfcej1qs9R6tRVIUdj3EiKDCGOVa1gyuP2OG5ZE/vw1Ww4JBwgBGBGhnF4+AcDR4Uz8Bt53jaQFZevo5BmiyGDn7cEc3rB5OzSlmKhzVDkFdacC9bUJJu0CE4zYzO124WjQsgvGEhtNpe0hVmLYGomuQ9tkaeTPvvqQ8q419GDE5z7/XZrOYmScLmengDQMsaE6icRk2HbrN0YqWWqHPSBHeu/+8VfmRXLzlq0jly3Twx6wYxbOtE3bRbNwbw0C5BxKW/DZ0nvzuCcAIcfV190yh9U3XLONismhf240YcM124jbQtdvC7jyszcNEAAjCvpYDczZ23fgOOCAd+AdeJuDwojD5dd+mzj0Pi9UIXoOnau+sD1y3P/DxXOMx8wXGDawmzsTkpkFUkAR8gnBT62IMfo1yu/AW1YGXLXpy2TjMaR5G7mbRtZ+DUXelpogjrg/uuvxRb/5iSu+TrWoJe9uu/WbqEvvFKqVHBN5ZYc94HRRoJ5oZEqh8BrdQqFIOaxHAyW3C4FDDIcGnNTPlDfLeqNjAfpoB7jre1tX9F/HrQl0rUZXKymyyHKLNNNIuwrddGkCSHZIZ1IHwPl/meExLDq3RzvApi9tHagvOHzoADJEaI63kGcasHWYyMCpRNJuy+GATP5JsBL95SoQjg4eK1BHO8AH3nsyJUlD/hMaW7kSk50UamwCJ7//VJh4AsbX4TlO7znzTOEPFMURaCN5QVIhcqw1B2YjuLwBzfl/SmFVgZqflklmOhZFRywPfBv3/+RbaiQ4IDMxNCJYitCenAashWpP4l9/eQmnrj4LrdYqdLkshlPdZbQ5lH4GHV6oZlncGIAMZ4K4qjSWspnAAUBOIeGp0IYaYhW6PdoBKrnGpSvyb0GJSlxM40/7fyfEMZwC4foD+aHC9AiQqwZWn3UhPKoSFy9BVWJjxvB2KK07suBKoioBqof4I4Yd1kBSRVT9RVJCjHSmdEGqN0LNSZXlkaNUg/Qh1JfX49xvD6rco9QSDU952aGNtMDwmqs5GHFJXlT5tZIAqiYEUlKIFWBQ4IdSGhaeBg7GWWjfQJF1hjjDYUDplEip2ywQwdffb6DWMCRmZ7/VnyqTwidhfamrExINpu/fdAL4sqglVH7wWg08LYsXQimulHr0JTqtaAJDM+94ol69QUA+1AYR/4ukMzGmCj+NEdwCfv7bUl5TnpYbmZOas0nX614WTAyucuX2ht/2Iq6OHFUZoFkQ9v9n1Jeqrn6a6NUFsB1gLVzfNFhQ9pBX1RbhWiL+EcsDBaffZwTlJ79wA3VSTp9zMddsdFj19n2ftYvuSu3zAz+6WR4MnQAvv3wAExMTvetmfabMfjbwhIr0NXiEDDRDtT2kAENS6VwmkUGpriiLRDWh/IzQbNg6lyNJ9WmeO0G4909jqHqaKf1g+SP1iDNoq6NF+JRTTiG2ArlxDcCBVw7KeQXvWjFDDPkgzXAHG0BPPf3sQIlsrwCjmh2XfKgMmg1kb6HSBrIOYfwkMxqWIOaBqqZgKRCh2Q1VpRVUv+T1qsC4IrWs/SFv0VTvhrXDm/b/AWbsqeV6bPGFAAAAAElFTkSuQmCC"



class Selection:
    __slots__ = ("id", "name", "x", "y", "w", "h")

    def __init__(self, sid, name, x, y, w, h):
        self.id = int(sid)
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.w = max(1, int(w))
        self.h = max(1, int(h))

    def box(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def describe(self):
        return f"{self.name}  ({self.x},{self.y}) {self.w}×{self.h}"

    def to_dict(self):
        return {"id": self.id, "name": self.name, "x": self.x, "y": self.y,
                "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("id", 0), d.get("name", "选区"), d.get("x", 0),
                   d.get("y", 0), d.get("w", 1), d.get("h", 1))


class Mapping:
    __slots__ = ("id", "kind", "ref_id", "x", "y", "rotation")

    def __init__(self, mid, kind="selection", ref_id=0, x=0, y=0, rotation=0):
        self.id = int(mid)
        self.kind = kind            # selection / rect
        self.ref_id = int(ref_id)
        self.x = int(x)
        self.y = int(y)
        self.rotation = int(rotation) % 360
        if self.rotation not in (90, 180, 270):
            self.rotation = 0

    def to_dict(self):
        return {"id": self.id, "kind": self.kind, "ref_id": self.ref_id,
                "x": self.x, "y": self.y, "rotation": self.rotation}

    @classmethod
    def from_dict(cls, d):
        rot = d.get("rotation", 0)
        if "kind" in d:
            return cls(d.get("id", 0), d.get("kind", "selection"),
                       d.get("ref_id", 0), d.get("x", 0), d.get("y", 0), rot)
        # 旧格式：只有 selection_id
        return cls(d.get("id", 0), "selection", d.get("selection_id", 0),
                   d.get("x", 0), d.get("y", 0), rot)


class RectItem:
    __slots__ = ("id", "name", "w", "h", "color")

    def __init__(self, rid, name, w, h, color="#ffffff"):
        self.id = int(rid)
        self.name = name
        self.w = max(1, int(w))
        self.h = max(1, int(h))
        self.color = color if re.fullmatch(r"#[0-9a-fA-F]{6}", color or "") \
            else "#ffffff"

    def to_dict(self):
        return {"id": self.id, "name": self.name, "w": self.w, "h": self.h,
                "color": self.color}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("id", 0), d.get("name", "矩形"), d.get("w", 8),
                   d.get("h", 8), d.get("color", "#ffffff"))


def parse_hex_color(color):
    c = (color or "#ffffff").lstrip("#")
    if len(c) != 6:
        c = "ffffff"
    try:
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    except ValueError:
        return (255, 255, 255, 255)


class BpNode:
    def __init__(self, nid, kind, name="", x=0.0, y=0.0):
        self.id = int(nid)
        self.kind = kind            # input / canvas / result / rect
        self.name = name
        self.x = float(x)
        self.y = float(y)
        # 画布
        self.width = DEFAULT_CANVAS_W
        self.height = DEFAULT_CANVAS_H
        self.mappings = []
        # Result
        self.template = ""
        # 矩形节点
        self.rects = []

    def to_dict(self):
        d = {"id": self.id, "kind": self.kind, "name": self.name,
             "x": self.x, "y": self.y}
        if self.kind == "canvas":
            d["width"] = self.width
            d["height"] = self.height
            d["mappings"] = [m.to_dict() for m in self.mappings]
        elif self.kind == "result":
            d["template"] = self.template
        elif self.kind == "rect":
            d["rects"] = [r.to_dict() for r in self.rects]
        return d

    @classmethod
    def from_dict(cls, d):
        n = cls(d.get("id", 0), d.get("kind", "canvas"),
                d.get("name", ""), d.get("x", 0), d.get("y", 0))
        n.width = max(1, int(d.get("width", DEFAULT_CANVAS_W)))
        n.height = max(1, int(d.get("height", DEFAULT_CANVAS_H)))
        n.mappings = [Mapping.from_dict(m) for m in d.get("mappings", [])]
        n.template = d.get("template", "")
        n.rects = [RectItem.from_dict(r) for r in d.get("rects", [])]
        return n


class Blueprint:
    def __init__(self, name="新蓝图"):
        self.name = name
        self.ref_image = ""       # 相对 blueprints/ 的示例图文件名
        self.image_w = 0
        self.image_h = 0
        self.selections = []
        self.nodes = {}
        self.edges = []           # [(from_id, to_id)]
        self.next_id = 1
        self.next_sel = 1
        self.next_map = 1
        self.next_rect = 1

    # ---------- 节点 ----------
    def _new_node(self, kind, x, y, name):
        node = BpNode(self.next_id, kind, name, x, y)
        self.next_id += 1
        self.nodes[node.id] = node
        return node

    def add_input(self, x=40, y=140, name="示例皮肤"):
        for n in self.nodes.values():
            if n.kind == "input":
                return n
        return self._new_node("input", x, y, name)

    def add_canvas(self, x=320, y=120, name=None):
        if not name:
            name = f"画布 {len(self.canvas_nodes()) + 1}"
        node = self._new_node("canvas", x, y, name)
        node.width = DEFAULT_CANVAS_W
        node.height = DEFAULT_CANVAS_H
        return node

    def add_result(self, x=700, y=140, name=None):
        if not name:
            existing = {n.name for n in self.result_nodes()}
            i = len(existing) + 1
            while f"result{i}" in existing:
                i += 1
            name = f"result{i}"
        node = self._new_node("result", x, y, name)
        node.template = DEFAULT_RESULT_TEMPLATE
        return node

    def add_rect_node(self, x=320, y=300, name=None):
        if not name:
            name = f"矩形 {len(self.rect_nodes()) + 1}"
        node = self._new_node("rect", x, y, name)
        self.add_rect(node, 8, 8, "#6cb4ff")
        return node

    def remove_node(self, nid):
        node = self.nodes.get(nid)
        if node is not None and node.kind == "rect":
            for rect in list(node.rects):
                self._drop_rect_mappings(rect.id)
        if nid in self.nodes:
            del self.nodes[nid]
            self.edges = [e for e in self.edges if nid not in e]

    def connect(self, a, b):
        if a == b or a not in self.nodes or b not in self.nodes:
            return False
        if self.would_cycle(a, b):
            return False
        src, dst = self.nodes[a], self.nodes[b]
        if src.kind in ("input", "rect") and dst.kind == "canvas":
            if src.kind == "input":
                # 画布只有一个图像输入；矩形节点可以接多个
                self.edges = [e for e in self.edges
                              if not (e[1] == b and self.nodes.get(e[0]) is not None
                                      and self.nodes[e[0]].kind == "input")]
        elif src.kind == "canvas" and dst.kind == "result":
            # 一个 Result 只接一个画布
            self.edges = [e for e in self.edges
                          if not (e[1] == b and self.nodes.get(e[0]) is not None
                                  and self.nodes[e[0]].kind == "canvas")]
        else:
            return False
        self.edges.append((a, b))
        return True

    def would_cycle(self, a, b):
        stack = [b]
        seen = set()
        while stack:
            cur = stack.pop()
            if cur == a:
                return True
            if cur in seen:
                continue
            seen.add(cur)
            for x, y in self.edges:
                if x == cur:
                    stack.append(y)
        return False

    def input_node(self):
        for n in self.nodes.values():
            if n.kind == "input":
                return n
        return None

    def canvas_nodes(self):
        return [n for n in self.nodes.values() if n.kind == "canvas"]

    def result_nodes(self):
        return [n for n in self.nodes.values() if n.kind == "result"]

    def canvas_of_result(self, rid):
        for a, b in self.edges:
            if b == rid:
                node = self.nodes.get(a)
                if node is not None and node.kind == "canvas":
                    return node
        return None

    def result_of_canvas(self, cid):
        for a, b in self.edges:
            if a == cid:
                node = self.nodes.get(b)
                if node is not None and node.kind == "result":
                    return node
        return None

    def result_ports(self):
        """有效 Result：接了一个画布。"""
        ports = []
        for n in self.result_nodes():
            if self.canvas_of_result(n.id) is not None:
                ports.append((n.id, n.name or f"result{n.id}"))
        return ports

    def prune_edges(self):
        keep = []
        for a, b in self.edges:
            na, nb = self.nodes.get(a), self.nodes.get(b)
            if na is None or nb is None:
                continue
            ok = ((na.kind in ("input", "rect") and nb.kind == "canvas")
                  or (na.kind == "canvas" and nb.kind == "result"))
            if ok:
                keep.append((a, b))
        self.edges = keep

    # ---------- 选区 ----------
    def add_selection(self, x, y, w, h, name=None):
        if not name:
            existing = {s.name for s in self.selections}
            i = self.next_sel
            while f"选区{i}" in existing:
                i += 1
            name = f"选区{i}"
        sel = Selection(self.next_sel, name, x, y, w, h)
        self.next_sel = max(self.next_sel, sel.id) + 1
        self.selections.append(sel)
        return sel

    def selection(self, sid):
        for s in self.selections:
            if s.id == sid:
                return s
        return None

    def remove_selection(self, sid):
        self.selections = [s for s in self.selections if s.id != sid]
        for canvas in self.canvas_nodes():
            canvas.mappings = [m for m in canvas.mappings
                               if not (m.kind == "selection" and m.ref_id == sid)]

    # ---------- 矩形 ----------
    def rect_nodes(self):
        return [n for n in self.nodes.values() if n.kind == "rect"]

    def add_rect(self, node, w=8, h=8, color="#ffffff", name=None):
        if not name:
            existing = {r.name for r in node.rects}
            i = self.next_rect
            while f"矩形{i}" in existing:
                i += 1
            name = f"矩形{i}"
        rect = RectItem(self.next_rect, name, w, h, color)
        self.next_rect = max(self.next_rect, rect.id) + 1
        node.rects.append(rect)
        return rect

    def find_rect(self, rid):
        for node in self.rect_nodes():
            for rect in node.rects:
                if rect.id == rid:
                    return node, rect
        return None, None

    def remove_rect(self, node, rid):
        node.rects = [r for r in node.rects if r.id != rid]
        self._drop_rect_mappings(rid)

    def _drop_rect_mappings(self, rid):
        for canvas in self.canvas_nodes():
            canvas.mappings = [m for m in canvas.mappings
                               if not (m.kind == "rect" and m.ref_id == rid)]

    def input_for_canvas(self, cid):
        for a, b in self.edges:
            if b == cid:
                node = self.nodes.get(a)
                if node is not None and node.kind == "input":
                    return node
        return None

    def materials_for(self, canvas):
        """画布能用的素材：连接的输入图选区 + 连接的矩形节点里的矩形。"""
        out = []
        if self.input_for_canvas(canvas.id) is not None:
            for sel in self.selections:
                out.append(("selection", sel.id, f"选区 · {sel.name}",
                            sel.w, sel.h))
        for a, b in self.edges:
            if b != canvas.id:
                continue
            node = self.nodes.get(a)
            if node is not None and node.kind == "rect":
                for rect in node.rects:
                    out.append(("rect", rect.id,
                                f"矩形 · {node.name}/{rect.name}",
                                rect.w, rect.h))
        return out

    def material_size(self, kind, ref_id, rotation=0):
        if kind == "rect":
            _node, rect = self.find_rect(ref_id)
            w, h = (rect.w, rect.h) if rect is not None else (0, 0)
        else:
            sel = self.selection(ref_id)
            w, h = (sel.w, sel.h) if sel is not None else (0, 0)
        if int(rotation) % 180 == 90:
            w, h = h, w
        return w, h

    # ---------- 映射 ----------
    def add_mapping(self, canvas, kind, ref_id, x=0, y=0):
        m = Mapping(self.next_map, kind, ref_id, x, y)
        self.next_map += 1
        canvas.mappings.append(m)
        return m

    def mapping(self, canvas, mid):
        for m in canvas.mappings:
            if m.id == mid:
                return m
        return None

    def remove_mapping(self, canvas, mid):
        canvas.mappings = [m for m in canvas.mappings if m.id != mid]

    def move_mapping(self, canvas, mid, delta):
        for i, m in enumerate(canvas.mappings):
            if m.id == mid:
                j = max(0, min(len(canvas.mappings) - 1, i + delta))
                if i != j:
                    canvas.mappings.insert(j, canvas.mappings.pop(i))
                return True
        return False

    # ---------- 序列化 ----------
    def to_dict(self):
        return {
            "version": BP_VERSION,
            "name": self.name,
            "ref_image": self.ref_image,
            "image_w": self.image_w,
            "image_h": self.image_h,
            "next_id": self.next_id,
            "next_sel": self.next_sel,
            "next_map": self.next_map,
            "next_rect": self.next_rect,
            "selections": [s.to_dict() for s in self.selections],
            "nodes": [n.to_dict() for n in sorted(self.nodes.values(),
                                                  key=lambda x: x.id)],
            "edges": [list(e) for e in self.edges],
        }

    @classmethod
    def from_dict(cls, d):
        bp = cls(d.get("name", "蓝图"))
        if int(d.get("version", 1)) < BP_VERSION:
            bp._migrate_v1(d)
            return bp
        bp.ref_image = d.get("ref_image", "") or ""
        bp.image_w = int(d.get("image_w", 0) or 0)
        bp.image_h = int(d.get("image_h", 0) or 0)
        bp.next_id = max(1, int(d.get("next_id", 1)))
        bp.next_sel = max(1, int(d.get("next_sel", 1)))
        bp.next_map = max(1, int(d.get("next_map", 1)))
        bp.next_rect = max(1, int(d.get("next_rect", 1)))
        bp.selections = [Selection.from_dict(x) for x in d.get("selections", [])]
        for nd in d.get("nodes", []):
            n = BpNode.from_dict(nd)
            bp.nodes[n.id] = n
            bp.next_id = max(bp.next_id, n.id + 1)
        for s in bp.selections:
            bp.next_sel = max(bp.next_sel, s.id + 1)
        for n in bp.canvas_nodes():
            for m in n.mappings:
                bp.next_map = max(bp.next_map, m.id + 1)
        for n in bp.rect_nodes():
            for r in n.rects:
                bp.next_rect = max(bp.next_rect, r.id + 1)
        bp.edges = [tuple(e) for e in d.get("edges", []) if len(e) == 2]
        bp.prune_edges()
        return bp

    def _migrate_v1(self, d):
        """旧版（筛选映射 + 画布命名）尽量保留节点和名字。"""
        old = {}
        for nd in d.get("nodes", []):
            if nd.get("kind") not in ("canvas", "result"):
                continue
            node = BpNode(nd.get("id", 0), nd.get("kind"),
                          nd.get("name", ""), nd.get("x", 0), nd.get("y", 0))
            node.width = DEFAULT_CANVAS_W
            node.height = DEFAULT_CANVAS_H
            node.template = nd.get("template", "") or ""
            old[node.id] = node
        for node in old.values():
            self.nodes[node.id] = node
        self.next_id = max([0] + [n.id for n in old.values()]) + 1
        inp = self.add_input(40, 140)
        for edge in d.get("edges", []):
            if len(edge) != 2:
                continue
            a, b = edge
            if a not in self.nodes and b in self.nodes:
                a = inp.id       # 旧输入节点被换成了新的
            na, nb = self.nodes.get(a), self.nodes.get(b)
            if na is None or nb is None:
                continue
            if na.kind == "input" and nb.kind == "canvas":
                self.edges.append((a, b))
            elif na.kind == "canvas" and nb.kind == "result":
                if not nb.template:
                    nb.template = na.template or DEFAULT_RESULT_TEMPLATE
                self.edges.append((a, b))
        self.prune_edges()


def make_default_blueprint(name="基础"):
    bp = Blueprint(name)
    inp = bp.add_input(40, 150)
    sel = bp.add_selection(0, 0, 32, 16, "头部一层")
    canvas = bp.add_canvas(330, 120, "画布 1")
    canvas.width, canvas.height = 32, 16
    bp.add_mapping(canvas, "selection", sel.id, 0, 0)
    res = bp.add_result(700, 150, "result1")
    res.template = DEFAULT_RESULT_TEMPLATE
    bp.connect(inp.id, canvas.id)
    bp.connect(canvas.id, res.id)
    return bp


def render_result_image(bp, canvas, image, scale):
    """把画布上的映射真正画出来。"""
    w = max(1, int(canvas.width))
    h = max(1, int(canvas.height))
    board = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for mapping in canvas.mappings:
        rot = int(getattr(mapping, "rotation", 0)) % 360
        if mapping.kind == "rect":
            _node, rect = bp.find_rect(mapping.ref_id)
            if rect is None:
                continue
            rw, rh = (rect.h, rect.w) if rot % 180 == 90 else (rect.w, rect.h)
            block = Image.new("RGBA", (rw, rh), parse_hex_color(rect.color))
            board.paste(block, (int(mapping.x), int(mapping.y)), block)
            continue
        sel = bp.selection(mapping.ref_id)
        if sel is None or image is None:
            continue
        x0 = int(round(sel.x * scale))
        y0 = int(round(sel.y * scale))
        x1 = int(round((sel.x + sel.w) * scale))
        y1 = int(round((sel.y + sel.h) * scale))
        if x1 <= x0 or y1 <= y0:
            continue
        crop = image.crop((x0, y0, x1, y1)).convert("RGBA")
        if rot:
            crop = crop.rotate(-rot, expand=True)
        board.paste(crop, (int(mapping.x), int(mapping.y)), crop)
    return board


def run_blueprint(bp, image, text, ctx):
    """执行蓝图。

    返回 (ports, group)
      ports: {result_id: Payload}  每个有效 Result 一张画布图
      group: Payload               所有结果打包
    """
    design_w = bp.image_w or image.width
    scale = (image.width / design_w) if design_w else 1.0
    ports = {}
    group_items = []
    for idx, (rid, label) in enumerate(bp.result_ports(), 1):
        canvas = bp.canvas_of_result(rid)
        if canvas is None:
            continue
        board = render_result_image(bp, canvas, image, scale)
        res_node = bp.nodes.get(rid)
        template = (res_node.template if res_node is not None else "") \
            or DEFAULT_RESULT_TEMPLATE
        variables = result_variables(canvas, res_node, text, ctx, idx)
        name = sanitize_name(render_template(template, variables))
        if not name:
            name = label
        item = ImageItem(name, board, "custom", 1, label)
        ports[rid] = Payload([item])
        group_items.append(item)
    return ports, Payload(group_items)


class BlueprintRepo:
    def __init__(self, folder):
        self.folder = Path(folder)
        self._cache = {}
        try:
            self.folder.mkdir(exist_ok=True)
        except Exception:
            pass

    def list(self):
        try:
            return sorted(p.stem for p in self.folder.glob("*.json"))
        except Exception:
            return []

    def path_of(self, name):
        return self.folder / f"{sanitize_name(name)}.json"

    def ref_path(self, name):
        return self.folder / f"{sanitize_name(name)}_ref.png"

    def load(self, name, force=False):
        if not name:
            return None
        path = self.path_of(name)
        if not path.exists():
            self._cache.pop(name, None)
            return None
        try:
            mtime = path.stat().st_mtime
        except Exception:
            mtime = 0
        cached = self._cache.get(name)
        if cached is not None and cached[0] == mtime and not force:
            return cached[1]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            bp = Blueprint.from_dict(data)
            bp.name = name
            self._cache[name] = (mtime, bp)
            return bp
        except Exception:
            traceback.print_exc()
            return None

    def save(self, bp):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.path_of(bp.name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bp.to_dict(), f, ensure_ascii=False, indent=2)
        self._cache.pop(bp.name, None)
        return path

    def delete(self, name):
        for path in (self.path_of(name), self.ref_path(name)):
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
        self._cache.pop(name, None)

    def ensure_default(self):
        names = self.list()
        if names:
            return "基础" if "基础" in names else names[0]
        try:
            bp = Blueprint.from_dict(json.loads(DEFAULT_BLUEPRINT_JSON))
            bp.name = "基础"
            self.save(bp)
            ref = bp.ref_image
            if ref and DEFAULT_BLUEPRINT_REF_B64:
                (self.folder / ref).write_bytes(
                    base64.b64decode(DEFAULT_BLUEPRINT_REF_B64))
            return "基础"
        except Exception:
            traceback.print_exc()
            bp = make_default_blueprint("基础")
            self.save(bp)
            return "基础"


BP_REPO = BlueprintRepo(BLUEPRINTS_DIR)



# ====================================================================
# 流程数据模型
# ====================================================================

# 参数格式：(名字, 标签, 默认值, 类型[, 选项])
NODE_TYPES = {
    "source": {
        "title": "源文件",
        "desc": "读取整张皮肤 PNG（蓝图里再拉框裁切）",
        "params": [
            ("path", "皮肤文件", "", "file"),
        ],
        "hint": "主界面选了源文件时，会优先使用主界面的源文件。",
    },
    "pause": {
        "title": "暂停",
        "desc": "停下来等你操作；询问模式会把回答送到“回答”输出",
        "params": [
            ("mode", "模式", "询问", "choice", ("提示", "询问")),
            ("message", "提示内容", "输入这次结果的名字", "text"),
            ("default", "默认值", "", "text"),
            ("open_folder", "自动打开", False, "bool"),
        ],
        "hint": "有图输入时，暂停会把当前图导出到 临时/暂停_…/；改完点继续会读回修改后的图。",
    },
    "blueprint": {
        "title": "蓝图",
        "desc": "按蓝图拼图，并给每个 Result 命名",
        "params": [
            ("name", "蓝图", "", "blueprint"),
        ],
        "hint": "输入一张图；每个有效 Result 一个输出点，外加一个图组输出。",
    },
    "upscale": {
        "title": "放大",
        "desc": "把图片像素放大 N 倍",
        "params": [
            ("factor", "倍数", 4, "int"),
        ],
        "hint": "在蓝图前放大，L / W 会跟着变；在蓝图后放大，名字不受影响。",
    },
    "rename": {
        "title": "重命名",
        "desc": "把图组里的图统一改名字",
        "params": [
            ("pattern", "命名模式", "{Skin}_{Name}", "text"),
            ("indexed", "重名时加序号", True, "bool"),
        ],
        "hint": "Text 只来自接在这个节点上的暂停“回答”，不连就是空。可用 {Skin} {Name} {Index} {Text} {L} {W} {Result}。",
    },
    "make": {
        "title": "Make 合并",
        "desc": "把多张图 / 多个组合并成一个图组",
        "params": [
            ("count", "输入数量", 2, "int"),
        ],
        "hint": "每个输入接一张图或一个组，输出一个图组；没连的输入会跳过。",
    },
    "break": {
        "title": "Break 拆分",
        "desc": "把图组拆成一张张图，输出数量自动匹配",
        "params": [],
        "hint": "接到图组后会自动出现对应数量的输出点（最多 64 个）。",
    },
    "export": {
        "title": "导出",
        "desc": "把图 / 图组写到文件夹",
        "params": [
            ("dir", "导出根目录", "", "dir"),
            ("pattern", "命名模式", "", "text"),
            ("overwrite", "同名覆盖", False, "bool"),
        ],
        "hint": "字符输入会当成文件夹名；图片按自己的 Result 命名导出。命名模式留空 = 用图自己的名字。",
    },
}

NODE_ORDER = ("source", "pause", "blueprint", "make", "break",
              "upscale", "rename", "export")

MAX_MAKE_INPUTS = 16
MAX_BREAK_PORTS = 64


class Port:
    __slots__ = ("key", "label", "kind")

    def __init__(self, key, label, kind="image"):
        self.key = key
        self.label = label
        self.kind = kind          # image / text

    def __repr__(self):
        return f"<Port {self.key}:{self.label}:{self.kind}>"


def blueprint_of(node):
    return BP_REPO.load((node.params or {}).get("name", ""))


def clamp_port_count(value, lo, hi, default):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def node_ports(node):
    """返回 (输入端口列表, 输出端口列表)。节点高度由端口数量决定。"""
    t = node.type
    if t == "source":
        return [], [Port("image", "图像", "image")]
    if t == "pause":
        outs = [Port("image", "继续", "image")]
        if (node.params or {}).get("mode", "询问") == "询问":
            outs.append(Port("answer", "回答", "text"))
        return [Port("image", "图像（可选）", "image")], outs
    if t == "blueprint":
        ins = [Port("image", "图像", "image"),
               Port("text", "字符", "text")]
        bp = blueprint_of(node)
        outs = []
        if bp is not None:
            for rid, label in bp.result_ports():
                outs.append(Port(f"res:{rid}", label, "image"))
        outs.append(Port("group", "图组", "image"))
        return ins, outs
    if t == "make":
        n = clamp_port_count((node.params or {}).get("count", 2),
                             1, MAX_MAKE_INPUTS, 2)
        ins = [Port(f"in{i}", f"图像{i}", "image")
               for i in range(1, n + 1)]
        return ins, [Port("group", "图组", "image")]
    if t == "break":
        n = clamp_port_count((node.params or {}).get("count", 1),
                             1, MAX_BREAK_PORTS, 1)
        outs = [Port(f"out{i}", f"图{i}", "image")
                for i in range(1, n + 1)]
        return [Port("group", "图组", "image")], outs
    if t == "rename":
        return ([Port("image", "图像", "image"),
                 Port("text", "Text", "text")],
                [Port("image", "图像", "image")])
    if t == "upscale":
        return ([Port("image", "图像", "image")],
                [Port("image", "图像", "image")])
    if t == "export":
        return ([Port("image", "图 / 图组", "image"),
                 Port("text", "文件夹名", "text")], [])
    return [], []


def node_defaults(ntype):
    params = {}
    for p in NODE_TYPES.get(ntype, {}).get("params", []):
        params[p[0]] = p[2]
    return params


def node_param_lines(node):
    """节点上显示的参数摘要。"""
    info = NODE_TYPES.get(node.type, {})
    lines = []
    for p in info.get("params", []):
        pname, plabel, pdefault = p[0], p[1], p[2]
        ptype = p[3] if len(p) > 3 else "text"
        value = (node.params or {}).get(pname, pdefault)
        if ptype == "bool":
            continue
        if ptype == "file":
            value = Path(str(value)).name if value else "未选择"
        elif ptype == "blueprint":
            value = value or "未选择"
            bp = BP_REPO.load(value) if value else None
            if bp is not None:
                value = f"{value}（{len(bp.result_ports())}R）"
        elif pname == "dir" and not value:
            value = "默认"
        elif pname == "pattern" and node.type == "export" and not value:
            value = "跟随图片名"
        if ptype == "choice":
            value = value
        text = f"{plabel}：{value}"
        if len(text) > 26:
            text = text[:25] + "…"
        lines.append(text)
    if node.type == "break":
        n = clamp_port_count((node.params or {}).get("count", 1),
                             1, MAX_BREAK_PORTS, 1)
        lines.append(f"输出：{n} 个（自动）")
    return lines


class WfNode:
    def __init__(self, nid, ntype, x=0.0, y=0.0, params=None, skip=False):
        self.id = nid
        self.type = ntype
        self.x = float(x)
        self.y = float(y)
        self.params = params if params is not None else node_defaults(ntype)
        self.skip = bool(skip)

    def to_dict(self):
        return {"id": self.id, "type": self.type, "x": self.x, "y": self.y,
                "params": self.params, "skip": self.skip}

    @classmethod
    def from_dict(cls, d):
        ntype = d.get("type", "source")
        params = node_defaults(ntype)
        params.update(d.get("params", {}) or {})
        return cls(d.get("id", 0), ntype, d.get("x", 0), d.get("y", 0),
                   params, d.get("skip", False))


class Workflow:
    def __init__(self, name="未命名"):
        self.name = name
        self.nodes = {}
        self.edges = []          # [(from_id, from_port, to_id, to_port)]
        self.next_id = 1

    def add_node(self, ntype, x=0.0, y=0.0, params=None):
        nid = self.next_id
        self.next_id += 1
        node = WfNode(nid, ntype, x, y, params)
        self.nodes[nid] = node
        return node

    def remove_node(self, nid):
        if nid in self.nodes:
            del self.nodes[nid]
            self.edges = [e for e in self.edges if nid not in (e[0], e[2])]
            self.sync_dynamic_ports()

    def connect(self, a, ap, b, bp):
        # 一个输入端口只留一根线
        self.edges = [e for e in self.edges
                      if not (e[2] == b and e[3] == bp)]
        self.edges.append((a, ap, b, bp))
        self.sync_dynamic_ports()

    def disconnect_input(self, nid, port=None):
        self.edges = [e for e in self.edges
                      if not (e[2] == nid and (port is None or e[3] == port))]
        self.sync_dynamic_ports()

    def disconnect_output(self, nid, port=None):
        self.edges = [e for e in self.edges
                      if not (e[0] == nid and (port is None or e[1] == port))]
        self.sync_dynamic_ports()

    def edge_to(self, nid, port):
        for e in self.edges:
            if e[2] == nid and e[3] == port:
                return e
        return None

    def edge_from(self, nid, port):
        for e in self.edges:
            if e[0] == nid and e[1] == port:
                return e
        return None

    def get_next(self, nid):
        for a, _ap, b, _bp in self.edges:
            if a == nid:
                return b
        return None

    def find_start(self):
        targets = {e[2] for e in self.edges}
        roots = [nid for nid in self.nodes if nid not in targets]
        if not roots:
            return None
        sources = [nid for nid in roots if self.nodes[nid].type == "source"]
        pool = sources or roots
        pool.sort(key=lambda n: (self.nodes[n].x, self.nodes[n].id))
        return pool[0]

    def topo_order(self):
        indeg = {nid: 0 for nid in self.nodes}
        adj = {nid: [] for nid in self.nodes}
        for a, _ap, b, _bp in self.edges:
            if a in self.nodes and b in self.nodes:
                indeg[b] += 1
                adj[a].append(b)
        ready = [nid for nid, d in indeg.items() if d == 0]
        ready.sort(key=lambda n: (self.nodes[n].x, n))
        order = []
        while ready:
            nid = ready.pop(0)
            order.append(nid)
            for nxt in adj[nid]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
                    ready.sort(key=lambda n: (self.nodes[n].x, n))
        if len(order) != len(self.nodes):
            raise RuntimeError("检测到循环连线，流程无法执行")
        return order

    def prune_edges(self):
        keep = []
        for e in self.edges:
            a, ap, b, bp = e
            na = self.nodes.get(a)
            nb = self.nodes.get(b)
            if na is None or nb is None:
                continue
            out_ports = {p.key: p for p in node_ports(na)[1]}
            in_ports = {p.key: p for p in node_ports(nb)[0]}
            p_out = out_ports.get(ap)
            p_in = in_ports.get(bp)
            if p_out is None or p_in is None:
                continue
            if p_out.kind != p_in.kind:
                continue
            keep.append(e)
        self.edges = keep

    # ---------- Make / Break 的自动端口 ----------
    def port_item_count(self, node, port_key, path=None):
        """静态推断某个输出端口会带几张图；推不出来返回 None。"""
        if node is None:
            return None
        path = set() if path is None else path
        if node.id in path:
            return None
        path = path | {node.id}
        t = node.type
        if t == "source":
            return 1
        if t == "blueprint":
            if port_key == "group":
                bp = blueprint_of(node)
                return len(bp.result_ports()) if bp is not None else 1
            return 1
        if t == "make":
            total = 0
            for port in node_ports(node)[0]:
                edge = self.edge_to(node.id, port.key)
                if edge is None:
                    continue
                src = self.nodes.get(edge[0])
                count = self.port_item_count(src, edge[1], path)
                if count is None:
                    return None
                total += count
            return total
        if t == "break":
            return 1
        if t in ("pause", "upscale", "rename"):
            edge = self.edge_to(node.id, "image")
            if edge is None:
                return 1
            return self.port_item_count(self.nodes.get(edge[0]),
                                        edge[1], path)
        return None

    def break_output_count(self, node):
        edge = self.edge_to(node.id, "group")
        if edge is None:
            return 1
        count = self.port_item_count(self.nodes.get(edge[0]),
                                     edge[1], set())
        if count is None:
            return 1
        return max(1, min(MAX_BREAK_PORTS, count))

    def sync_dynamic_ports(self):
        """Break 的输出数量跟着上游自动更新。"""
        for node in self.nodes.values():
            if node.type == "break":
                node.params["count"] = self.break_output_count(node)
        self.prune_edges()

    def to_dict(self):
        return {
            "name": self.name,
            "next_id": self.next_id,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [list(e) for e in self.edges],
        }

    @classmethod
    def from_dict(cls, d):
        wf = cls(d.get("name", "未命名"))
        wf.next_id = max(1, int(d.get("next_id", 1)))
        remap = {"archive": "export"}
        for nd in d.get("nodes", []):
            nd = dict(nd)
            nd["type"] = remap.get(nd.get("type"), nd.get("type", "source"))
            if nd["type"] not in NODE_TYPES:
                continue
            n = WfNode.from_dict(nd)
            wf.nodes[n.id] = n
            wf.next_id = max(wf.next_id, n.id + 1)
        raw_edges = []
        for e in d.get("edges", []):
            if len(e) == 2:
                raw_edges.append((e[0], "image", e[1], "image"))
            elif len(e) == 4:
                raw_edges.append(tuple(e))
        wf.edges = raw_edges
        wf.sync_dynamic_ports()
        return wf


def make_default_workflow(name, blueprint_name):
    wf = Workflow(name)
    src = wf.add_node("source", 0, 150, {"path": ""})
    pause = wf.add_node("pause", 300, 150, {
        "mode": "询问", "message": "输入这次结果的名字（可留空）", "default": ""})
    bp_node = wf.add_node("blueprint", 610, 110, {"name": blueprint_name})
    exp = wf.add_node("export", 920, 130, {
        "dir": "", "pattern": "", "overwrite": False})
    wf.connect(src.id, "image", pause.id, "image")
    wf.connect(pause.id, "image", bp_node.id, "image")
    wf.connect(pause.id, "answer", bp_node.id, "text")
    wf.connect(bp_node.id, "group", exp.id, "image")
    return wf


def load_workflow(name):
    path = WORKFLOWS_DIR / f"{sanitize_name(name)}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        wf = Workflow.from_dict(data)
        wf.name = name
        return wf
    except Exception:
        traceback.print_exc()
        return None


def save_workflow(wf):
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    path = WORKFLOWS_DIR / f"{sanitize_name(wf.name)}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def list_workflows():
    try:
        return sorted(p.stem for p in WORKFLOWS_DIR.glob("*.json"))
    except Exception:
        return []


def resolve_out_dir(text):
    p = Path(str(text).strip())
    if not p.is_absolute():
        p = SCRIPT_DIR / p
    return p


def initial_dir_for(text):
    raw = str(text or "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = SCRIPT_DIR / p
        if p.is_dir():
            return p
        if p.parent.is_dir():
            return p.parent
    return SCRIPT_DIR


# ====================================================================
# 流程执行器
# ====================================================================

class FlowRunner:
    def __init__(self, app, wf, parent=None, main_source=None, status=None):
        self.app = app
        self.wf = wf
        self.parent = parent
        self.main_source = Path(main_source) if main_source else None
        self.status = status or (lambda s: None)
        self.bg = tuple(app.settings.get("bg_color", (255, 255, 255)))
        self.bg_fill = bool(app.settings.get("bg_fill", False))
        self.values = {}
        self.root = None
        self.reachable = set()
        self.skipped_nodes = 0
        self.ctx = {
            "now": datetime.now(),
            "skin": "",
            "text": "",
        }
        self.exported = []

    # ---------- 主流程 ----------
    def run(self):
        if self.main_source is not None:
            if not self.main_source.exists():
                messagebox.showerror(
                    "源文件无效", f"找不到文件：\n{self.main_source}",
                    parent=self.parent)
                return False
            try:
                self.root = build_source_payload(self.main_source)
            except Exception as exc:
                messagebox.showerror("源文件读取失败", str(exc),
                                     parent=self.parent)
                return False
            self.ctx["skin"] = self.main_source.stem

        if not self.wf.nodes:
            messagebox.showerror("流程为空", "这个流程里还没有节点。",
                                 parent=self.parent)
            return False

        try:
            self.wf.sync_dynamic_ports()
            order = self._execution_order()
        except RuntimeError as exc:
            messagebox.showerror("无法执行", str(exc), parent=self.parent)
            return False

        for nid in order:
            node = self.wf.nodes[nid]
            info = NODE_TYPES.get(node.type, {})
            try:
                if node.skip and node.type not in ("make", "break"):
                    self.status(f"跳过：{info.get('title', node.type)}")
                    self._passthrough(node)
                    continue
                self.status(f"执行：{info.get('title', node.type)}")
                if self.parent is not None:
                    try:
                        self.parent.update_idletasks()
                    except Exception:
                        pass
                handler = getattr(self, "_run_" + node.type, None)
                if handler is None:
                    raise RuntimeError(f"未知节点类型：{node.type}")
                if handler(node) is False:
                    return False
            except TemplateError as exc:
                messagebox.showerror("命名模板出错", str(exc), parent=self.parent)
                return False
            except RuntimeError as exc:
                messagebox.showerror("执行失败", str(exc), parent=self.parent)
                return False
            except Exception as exc:
                traceback.print_exc()
                messagebox.showerror(
                    "执行失败", f"{node.type} 节点出错：\n{exc}",
                    parent=self.parent)
                return False

        self.status("完成")
        return True

    # ---------- 只执行连在流程线上的节点 ----------
    def _execution_order(self):
        targets = {e[2] for e in self.wf.edges}
        roots = [nid for nid in self.wf.nodes if nid not in targets]
        if not roots:
            raise RuntimeError("流程是环形的，找不到起点")

        def has_out(nid):
            return any(e[0] == nid for e in self.wf.edges)

        cand = roots
        if self.main_source is not None:
            with_out = [n for n in roots if has_out(n)]
            if with_out:
                cand = with_out
        else:
            sources = [n for n in roots
                       if self.wf.nodes[n].type == "source"]
            with_out = [n for n in sources if has_out(n)]
            if with_out:
                cand = with_out
            elif sources:
                cand = sources

        start = min(cand, key=lambda n: (self.wf.nodes[n].x, n))
        adj = {}
        for a, _ap, b, _bp in self.wf.edges:
            adj.setdefault(a, []).append(b)
        seen = {start}
        stack = [start]
        while stack:
            cur = stack.pop()
            for nxt in adj.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        self.reachable = seen

        order = [nid for nid in self.wf.topo_order() if nid in seen]
        self.skipped_nodes = len(self.wf.nodes) - len(order)
        if self.skipped_nodes:
            self.status(f"跳过 {self.skipped_nodes} 个没连在流程线上的节点")
        return order

    # ---------- 取值 / 存值 ----------
    def _in(self, node, key, kind="image"):
        edge = self.wf.edge_to(node.id, key)
        if edge is not None:
            return self.values.get((edge[0], edge[1]))
        if kind == "image":
            return self.root
        return ""

    def _out(self, node, key, value):
        self.values[(node.id, key)] = value

    def _passthrough(self, node):
        ins, outs = node_ports(node)
        for port in outs:
            if port.kind == "image":
                self._out(node, port.key, self._in(node, "image", "image"))
            else:
                self._out(node, port.key, self._in(node, port.key, "text"))

    def _need_payload(self, node, key="image", label="图像"):
        payload = self._in(node, key)
        if not isinstance(payload, Payload) or not payload.items:
            raise RuntimeError(
                f"{NODE_TYPES.get(node.type, {}).get('title', node.type)}"
                f"节点没有“{label}”输入。")
        return payload

    # ---------- 各节点 ----------
    def _run_source(self, node):
        if self.root is not None:
            self._out(node, "image", self.root)
            return True
        path = str((node.params or {}).get("path", "") or "").strip()
        if not path:
            raise RuntimeError("源文件节点还没有选择皮肤 PNG。")
        p = Path(path)
        if not p.exists():
            raise RuntimeError(f"找不到皮肤文件：\n{p}")
        payload = build_source_payload(p)
        self.ctx["skin"] = p.stem
        self.root = payload
        self._out(node, "image", payload)
        return True

    def _run_pause(self, node):
        p = node.params or {}
        image = self._in(node, "image")
        mode = p.get("mode", "询问")
        message = str(p.get("message", "") or "完成后点继续")
        payload = image if isinstance(image, Payload) else None
        folder = None
        if (self.wf.edge_to(node.id, "image") is not None
                and payload is not None and payload.items):
            try:
                folder = self._export_pause_images(node, payload)
            except Exception as exc:
                self.status(f"暂停图片导出失败：{exc}")
                folder = None
            if folder is not None and bool(p.get("open_folder", False)):
                open_in_file_manager(folder)
        ok, answer = self._pause_dialog(
            mode, message, str(p.get("default", "") or ""), folder)
        if not ok:
            self.status("已取消")
            return False
        if folder is not None:
            image = self._reload_pause_images(folder, payload)
        self.ctx["text"] = answer
        self._out(node, "image", image)
        self._out(node, "answer", answer)
        return True

    def _export_pause_images(self, node, payload):
        now = self.ctx.get("now") or datetime.now()
        base = SCRIPT_DIR / "临时"
        stem = sanitize_name(
            f"暂停_{self.wf.name}_{node.id}_{now.strftime('%H%M%S')}") or "暂停"
        folder = base / stem
        n = 2
        while folder.exists():
            folder = base / f"{stem}_{n}"
            n += 1
        folder.mkdir(parents=True, exist_ok=True)
        for i, item in enumerate(payload.items, 1):
            name = sanitize_name(item.name) or f"图{i}"
            item.image.convert("RGBA").save(folder / f"{i:02d}_{name}.png")
        return folder

    def _reload_pause_images(self, folder, payload):
        files = sorted(p for p in folder.glob("*.png") if p.is_file())
        if not files:
            self.status("暂停文件夹里没有 PNG，继续用原图")
            return payload
        items = []
        for i, path in enumerate(files):
            try:
                image = load_rgba(path)
            except Exception:
                continue
            old = payload.items[i] if i < len(payload.items) else None
            if old is not None:
                items.append(ImageItem(old.name, image, old.part,
                                       old.px_scale, old.result))
            else:
                items.append(ImageItem(path.stem, image))
        if not items:
            return payload
        return Payload(items)

    def _pause_dialog(self, mode, message, default, folder):
        T = self.app.T
        win = tk.Toplevel(self.parent)
        win.title("暂停")
        win.configure(bg=T("BG"))
        win.transient(self.parent)
        win.resizable(False, False)
        center_window(win, 560, 300 if folder is not None else 200)

        body = tk.Frame(win, bg=T("BG"))
        body.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(body, text=message, bg=T("BG"), fg=T("FG"),
                 font=self.app.F(11), wraplength=500, justify="left",
                 anchor="w").pack(fill="x")
        if folder is not None:
            tk.Label(body, text="当前图片已导出到这里，改完点继续：",
                     bg=T("BG"), fg=T("MUTED"), font=self.app.F(9),
                     anchor="w").pack(fill="x", pady=(14, 2))
            tk.Label(body, text=str(folder), bg=T("BG"), fg=T("ACCENT"),
                     font=self.app.F(9), wraplength=500, justify="left",
                     anchor="w").pack(fill="x")
            ttk.Button(body, text="打开文件夹",
                       command=lambda: open_in_file_manager(folder)).pack(
                           anchor="w", pady=(6, 0))

        answer_var = tk.StringVar(value=default)
        if mode != "提示":
            entry = tk.Entry(body, textvariable=answer_var, bg=T("BG2"),
                             fg=T("FG"), insertbackground=T("FG"),
                             relief="flat", highlightthickness=1,
                             highlightbackground=T("BORDER"),
                             highlightcolor=T("ACCENT"), font=self.app.F(10))
            entry.pack(fill="x", pady=(12, 0), ipady=4)
            entry.focus_set()
            entry.select_range(0, "end")

        result = {"ok": False, "answer": ""}
        row = tk.Frame(body, bg=T("BG"))
        row.pack(side="bottom", fill="x", pady=(14, 0))

        def ok():
            result["ok"] = True
            result["answer"] = answer_var.get()
            win.destroy()

        ttk.Button(row, text="继续" if mode == "提示" else "确定",
                   style="Accent.TButton", command=ok).pack(side="right")
        ttk.Button(row, text="取消", command=win.destroy).pack(
            side="right", padx=(0, 8))
        win.bind("<Return>", lambda e: ok())
        win.bind("<Escape>", lambda e: win.destroy())
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.grab_set()
        win.wait_window()
        return result["ok"], result["answer"]

    def _run_blueprint(self, node):
        name = str((node.params or {}).get("name", "") or "").strip()
        if not name:
            raise RuntimeError("蓝图节点还没有选择蓝图。")
        bp = BP_REPO.load(name, force=True)
        if bp is None:
            raise RuntimeError(f"蓝图不存在或读取失败：{name}")
        payload = self._need_payload(node)
        if len(payload.items) > 1:
            self.status("蓝图只取第一张图")
        item = payload.items[0]
        text = self._in(node, "text", "text") or ""
        if not isinstance(text, str):
            text = format_value(text)
        self.ctx["text"] = text
        if not self.ctx.get("skin"):
            self.ctx["skin"] = item.name
        ports, group = run_blueprint(bp, item.image, text, self.ctx)
        for rid, result_payload in ports.items():
            self._out(node, f"res:{rid}", result_payload)
        self._out(node, "group", group)
        return True

    def _run_make(self, node):
        ins, _outs = node_ports(node)
        merged = Payload()
        for port in ins:
            if self.wf.edge_to(node.id, port.key) is None:
                continue
            value = self._in(node, port.key)
            if isinstance(value, Payload):
                merged.extend(value)
        self._out(node, "group", merged)
        return True

    def _run_break(self, node):
        payload = None
        if self.wf.edge_to(node.id, "group") is not None:
            payload = self._in(node, "group")
        items = list(payload.items) if isinstance(payload, Payload) else []
        _ins, outs = node_ports(node)
        for i, port in enumerate(outs):
            if i >= len(items):
                self._out(node, port.key, Payload([]))
            elif i == len(outs) - 1:
                self._out(node, port.key, Payload(items[i:]))
            else:
                self._out(node, port.key, Payload([items[i]]))
        return True

    def _run_upscale(self, node):
        try:
            factor = int(float((node.params or {}).get("factor", 4)))
        except (TypeError, ValueError):
            factor = 4
        factor = max(1, min(64, factor))
        payload = self._need_payload(node)
        scaled = Payload([it.scaled(factor) for it in payload.items])
        self._out(node, "image", scaled)
        return True

    def _run_rename(self, node):
        payload = self._need_payload(node)
        pattern = str((node.params or {}).get("pattern", "") or "{Skin}_{Name}")
        indexed = bool((node.params or {}).get("indexed", True))
        text = self._in(node, "text", "text") or ""
        if not isinstance(text, str):
            text = format_value(text)
        out = Payload()
        used = {}
        for idx, item in enumerate(payload.items, 1):
            variables = item_variables(item, text, self.ctx, idx)
            name = sanitize_name(render_template(pattern, variables)) or item.name
            if name in used:
                used[name] += 1
                if indexed:
                    name = f"{name}_{used[name]}"
            else:
                used[name] = 1
            out.add(item.copy(name=name))
        self._out(node, "image", out)
        return True

    def _run_export(self, node):
        payload = self._need_payload(node)
        p = node.params or {}
        text = self._in(node, "text", "text") or ""
        if not isinstance(text, str):
            text = format_value(text)
        skin = self.ctx.get("skin", "") or "结果"

        dir_tpl = str(p.get("dir", "") or "").strip()
        base_vars = {
            "Skin": skin, "Text": text, "Name": skin,
            "Time": self.ctx["now"].strftime("%Y%m%d%H%M"),
            "Date": self.ctx["now"].strftime("%Y%m%d"),
        }
        if dir_tpl:
            base = resolve_out_dir(render_template(dir_tpl, base_vars))
        else:
            base = SCRIPT_DIR / "导出"
        text_name = sanitize_name(text)
        if text_name:
            outdir = base / text_name
        elif dir_tpl:
            outdir = base
        else:
            outdir = base / (sanitize_name(skin) or "结果")
        outdir.mkdir(parents=True, exist_ok=True)

        pattern = str(p.get("pattern", "") or "").strip()
        overwrite = bool(p.get("overwrite", False))
        used = {}
        written = []
        skipped = 0

        for idx, item in enumerate(payload.items, 1):
            variables = item_variables(item, text, self.ctx, idx)
            if pattern:
                name = render_template(pattern, variables)
            elif item.part == "skin" and item.name == skin:
                name = default_image_name(item, skin, idx)
            else:
                name = item.name or default_image_name(item, skin, idx)
            name = sanitize_name(name) or f"result{idx}"
            if item.result and len({it.result for it in payload.items}) > 1:
                if name in used:
                    name = f"{sanitize_name(item.result)}_{name}"
            if name in used:
                used[name] += 1
                name = f"{name}_{used[name]}"
            else:
                used[name] = 1
            if not name.lower().endswith(".png"):
                name += ".png"
            target = outdir / name
            if target.exists() and not overwrite:
                skipped += 1
                continue
            try:
                image = item.image
                if self.bg_fill:
                    image = flatten_on_bg(image, self.bg)
                image.save(target)
            except Exception as exc:
                raise RuntimeError(f"保存失败：{target}\n{exc}") from exc
            written.append(target)

        summary = f"已导出 {len(written)} 张到：\n{outdir}"
        if skipped:
            summary += f"\n\n跳过已存在：{skipped} 张（导出节点里可开“同名覆盖”）"
        self.exported.extend(written)
        self.status(f"导出 {len(written)} 张")
        if messagebox.askyesno("导出完成", summary + "\n\n打开文件夹？",
                               parent=self.parent):
            open_in_file_manager(outdir)
        return True



# ====================================================================
# 绘图小工具
# ====================================================================

def round_rect(canvas, x1, y1, x2, y2, r=10, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1,
        x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, splinesteps=18, **kw)


def curve_points(x1, y1, x2, y2):
    dx = x2 - x1
    c = max(14.0, min(90.0, abs(dx) * 0.55))
    return (x1, y1, x1 + c, y1, x2 - c, y2, x2, y2)


def truncate(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[:limit - 1] + "…"


def center_window(win, width, height):
    try:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
    except Exception:
        return
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 3)
    win.geometry(f"{width}x{height}+{x}+{y}")


# ====================================================================
# 流程编辑器（曲线连线）
# ====================================================================

class FlowEditor(tk.Toplevel):
    NODE_W = 266
    HEADER_H = 34
    PARAM_H = 19
    ROW_H = 25
    PAD = 12
    PORT_R = 6.5

    def __init__(self, app, flow_name):
        super().__init__(app.root)
        self.app = app
        self.flow_name = flow_name
        self.wf = load_workflow(flow_name)
        if self.wf is None:
            bp_name = BP_REPO.ensure_default()
            self.wf = make_default_workflow(flow_name, bp_name)
        self.dirty = False

        self.zoom = 1.0
        self.pan_x = -20.0
        self.pan_y = -20.0
        self.selected_id = None
        self.selected_ids = set()
        self.drag_mode = None
        self.drag_start = (0, 0)
        self.drag_node_id = None
        self.drag_offset = (0.0, 0.0)
        self.drag_origins = {}
        self.drag_start_world = (0.0, 0.0)
        self.pan_start = (0.0, 0.0)
        self.link_from = None       # (nid, port_key, kind)
        self.link_cursor = (0, 0)
        self.box_rect = None
        self.box_additive = False

        self.title(f"流程编辑器 — {flow_name}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        win_w = min(1440, max(1000, sw - 80))
        win_h = min(900, max(620, sh - 110))
        center_window(self, win_w, win_h)
        self.minsize(920, 600)
        self.configure(bg=app.T("BG"))
        self.transient(app.root)

        try:
            self._font_small = tkfont.Font(family=app._font_family, size=8)
            self._font_title = tkfont.Font(family=app._font_family, size=10,
                                           weight="bold")
        except Exception:
            self._font_small = self._font_title = None

        self._build()
        self.after(40, self._render)
        self.after(90, self._fit_view)

    def _fit_text(self, text, max_px, font=None):
        text = str(text)
        font = font or self._font_small
        if font is None:
            return truncate(text, 20)
        if font.measure(text) <= max_px:
            return text
        cut = text
        while cut and font.measure(cut + "…") > max_px:
            cut = cut[:-1]
        return (cut + "…") if cut else ""

    # ---------- 基础 ----------
    def _build(self):
        T = self.app.T
        BG, CARD, BORDER = T("BG"), T("CARD"), T("BORDER")
        MUTED, ACCENT = T("MUTED"), T("ACCENT")

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", side="top")

        ttk.Button(bar, text="保存", style="Accent.TButton",
                   command=self._on_save).pack(side="left", padx=(12, 6), pady=8)
        ttk.Button(bar, text="另存为…",
                   command=self._on_save_as).pack(side="left", padx=(0, 6), pady=8)
        ttk.Button(bar, text="打开…",
                   command=self._open_external).pack(side="left", padx=(0, 6),
                                                     pady=8)
        ttk.Button(bar, text="目录",
                   command=lambda: open_in_file_manager(WORKFLOWS_DIR)).pack(
                       side="left", padx=(0, 6), pady=8)
        ttk.Button(bar, text="刷新蓝图端口",
                   command=self._refresh_blueprints).pack(side="left",
                                                          padx=(0, 6), pady=8)
        tk.Label(bar,
                 text="中键拖动 = 平移　左键拖空白 = 框选　右键 = 菜单　"
                      "Alt+左键点圆点 = 删线　滚轮缩放",
                 bg=BG, fg=MUTED, font=self.app.F(8)).pack(
                     side="left", padx=(10, 0), pady=8)
        ttk.Button(bar, text="关闭",
                   command=self._on_close).pack(side="right", padx=12, pady=8)

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main, bg=T("BG2"), highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main, bg=CARD, width=330,
                         highlightthickness=1, highlightbackground=BORDER)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        head = tk.Frame(right, bg=CARD)
        head.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(head, text="参数", bg=CARD, fg=ACCENT,
                 font=self.app.F(11, "bold"), anchor="w").pack(side="left")
        self.node_name_var = tk.StringVar(value="")
        tk.Label(head, textvariable=self.node_name_var, bg=CARD, fg=MUTED,
                 font=self.app.F(8), anchor="e").pack(side="right")

        self.params_body = tk.Frame(right, bg=CARD)
        self.params_body.pack(fill="both", expand=True, padx=14, pady=(8, 12))

        c = self.canvas
        c.bind("<Button-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_motion)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Button-2>", self._middle_press)
        c.bind("<B2-Motion>", self._middle_motion)
        c.bind("<ButtonRelease-2>", self._middle_release)
        c.bind("<MouseWheel>", self._on_wheel)
        c.bind("<Button-4>", lambda e: self._on_wheel(e, up=True))
        c.bind("<Button-5>", lambda e: self._on_wheel(e, down=True))
        c.bind("<Button-3>", self._on_right_click)
        if sys.platform == "darwin":
            c.bind("<Control-Button-1>", self._on_right_click)
        c.bind("<Configure>", lambda e: self._render())
        self.bind("<Delete>", lambda e: self._delete_selected())
        self.bind("<Control-s>", lambda e: self._on_save())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_params()

    def w2s(self, x, y):
        return ((x - self.pan_x) * self.zoom,
                (y - self.pan_y) * self.zoom)

    def s2w(self, x, y):
        return (x / self.zoom + self.pan_x,
                y / self.zoom + self.pan_y)

    def _is_alt(self, event):
        state = getattr(event, "state", 0)
        if sys.platform.startswith("win"):
            return bool(state & 0x20000)
        return bool(state & 0x8)

    # ---------- 节点几何 ----------
    def _node_layout(self, node):
        ins, outs = node_ports(node)
        params = node_param_lines(node)
        if node.type == "source" and getattr(self.app, "source_path", None) and params:
            params[0] = "皮肤文件：主界面优先"
        rows = max(1, len(ins), len(outs))
        h = (self.HEADER_H + len(params) * self.PARAM_H
             + rows * self.ROW_H + self.PAD)
        top = node.y + self.HEADER_H + len(params) * self.PARAM_H + 6
        return self.NODE_W, h, params, ins, outs, top

    def _port_world(self, node, side, key):
        w, h, params, ins, outs, top = self._node_layout(node)
        ports = ins if side == "in" else outs
        for i, p in enumerate(ports):
            if p.key == key:
                cy = top + i * self.ROW_H + self.ROW_H / 2
                x = node.x if side == "in" else node.x + w
                return x, cy, p
        return None

    def _hit_node(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        for nid in reversed(list(self.wf.nodes.keys())):
            node = self.wf.nodes[nid]
            w, h, *_ = self._node_layout(node)
            if node.x <= wx <= node.x + w and node.y <= wy <= node.y + h:
                return nid
        return None

    def _hit_port(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        radius = max(self.PORT_R + 4, 10 / max(self.zoom, 0.3))
        for nid, node in self.wf.nodes.items():
            ins, outs = node_ports(node)
            for side, ports in (("in", ins), ("out", outs)):
                for p in ports:
                    pos = self._port_world(node, side, p.key)
                    if pos is None:
                        continue
                    px, py, _ = pos
                    if (wx - px) ** 2 + (wy - py) ** 2 <= radius ** 2:
                        return side, nid, p
        return None

    # ---------- 渲染 ----------
    def _render(self):
        try:
            self._render_inner()
        except Exception:
            traceback.print_exc()

    def _render_inner(self):
        c = self.canvas
        c.delete("all")
        self._draw_grid()
        for a, ap, b, bp in self.wf.edges:
            self._draw_edge(a, ap, b, bp)
        if self.drag_mode == "link" and self.link_from is not None:
            nid, key, _kind = self.link_from
            node = self.wf.nodes.get(nid)
            if node is not None:
                pos = self._port_world(node, "out", key)
                if pos is not None:
                    x1, y1 = self.w2s(pos[0], pos[1])
                    c.create_line(*curve_points(x1, y1, *self.link_cursor),
                                  smooth=True, width=2,
                                  fill=self.app.T("ACCENT"), dash=(5, 4))
                    x, y = self.link_cursor
                    c.create_oval(x - 4, y - 4, x + 4, y + 4,
                                  outline=self.app.T("ACCENT"), width=2)
        for node in self.wf.nodes.values():
            self._draw_node(node)
        if self.box_rect is not None:
            x0, y0, x1, y1 = self.box_rect
            c.create_rectangle(min(x0, x1), min(y0, y1),
                               max(x0, x1), max(y0, y1),
                               outline=self.app.T("ACCENT"), dash=(5, 3),
                               width=1.5)

    def _draw_grid(self):
        c = self.canvas
        step = 34 * self.zoom
        if step < 14:
            return
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 4 or h < 4:
            return
        color = self.app.T("GRID")
        ox = (-self.pan_x * self.zoom) % step
        oy = (-self.pan_y * self.zoom) % step
        x = ox
        while x < w:
            c.create_line(x, 0, x, h, fill=color)
            x += step
        y = oy
        while y < h:
            c.create_line(0, y, w, y, fill=color)
            y += step

    def _edge_color(self, from_node, port_key):
        _ins, outs = node_ports(from_node)
        for p in outs:
            if p.key == port_key:
                return self.app.T("PORT_TXT" if p.kind == "text" else "PORT_IMG")
        return self.app.T("BORDER")

    def _draw_edge(self, a, ap, b, bp):
        na = self.wf.nodes.get(a)
        nb = self.wf.nodes.get(b)
        if na is None or nb is None:
            return
        p1 = self._port_world(na, "out", ap)
        p2 = self._port_world(nb, "in", bp)
        if p1 is None or p2 is None:
            return
        x1, y1 = self.w2s(p1[0], p1[1])
        x2, y2 = self.w2s(p2[0], p2[1])
        color = self._edge_color(na, ap)
        self.canvas.create_line(*curve_points(x1, y1, x2, y2),
                                smooth=True, width=max(1.6, 2.2 * self.zoom),
                                fill=color)
        self.canvas.create_oval(x2 - 3, y2 - 3, x2 + 3, y2 + 3,
                                fill=color, outline="")

    def _draw_node(self, node):
        c = self.canvas
        T = self.app.T
        x, y = self.w2s(node.x, node.y)
        w, h, params, ins, outs, top = self._node_layout(node)
        w *= self.zoom
        h *= self.zoom
        top_px = (top - node.y) * self.zoom

        selected = node.id in self.selected_ids
        primary = (node.id == self.selected_id)
        border = T("ACCENT") if selected else T("BORDER")
        body = T("CARD")
        if node.skip:
            border = T("MUTED")

        type_color = NODE_COLORS.get(node.type, T("ACCENT"))
        title = NODE_TYPES.get(node.type, {}).get("title", node.type)

        # 阴影
        round_rect(c, x + 3, y + 4, x + w + 3, y + h + 4, 12 * self.zoom,
                   fill=T("SHADOW"), outline="")
        round_rect(c, x, y, x + w, y + h, 12 * self.zoom,
                   fill=body, outline=border,
                   width=(2.5 if primary else (2.0 if selected else 1.2)))
        # 左侧色条
        c.create_rectangle(x + 1, y + 10 * self.zoom, x + 1 + 4 * self.zoom,
                           y + h - 10 * self.zoom, fill=type_color, outline="")

        fam = self.app._font_family
        title_size = max(1, int(10 * self.zoom))
        title_text = title + ("（跳过）" if node.skip else "")
        c.create_text(x + 16 * self.zoom, y + (self.HEADER_H / 2) * self.zoom,
                      text=self._fit_text(title_text, self.NODE_W - 90,
                                          self._font_title),
                      fill=T("MUTED") if node.skip else type_color,
                      anchor="w", font=(fam, title_size, "bold"))

        c.create_line(x + 12 * self.zoom, y + self.HEADER_H * self.zoom,
                      x + w - 12 * self.zoom, y + self.HEADER_H * self.zoom,
                      fill=T("BORDER"))

        psize = max(1, int(8 * self.zoom))
        for i, line in enumerate(params):
            c.create_text(
                x + 14 * self.zoom,
                y + (self.HEADER_H + 6 + i * self.PARAM_H) * self.zoom,
                text=self._fit_text(line, self.NODE_W - 28),
                fill=T("FG"), anchor="nw", font=(fam, psize))

        r = max(3.0, self.PORT_R * self.zoom)
        for i, p in enumerate(ins):
            cy = y + top_px + (i * self.ROW_H + self.ROW_H / 2) * self.zoom
            color = T("PORT_TXT" if p.kind == "text" else "PORT_IMG")
            c.create_oval(x - r, cy - r, x + r, cy + r,
                          fill=T("BG2"), outline=color, width=2)
            c.create_text(x + 14 * self.zoom, cy,
                          text=self._fit_text(p.label, self.NODE_W / 2 - 24),
                          fill=color, anchor="w", font=(fam, psize))
        for i, p in enumerate(outs):
            cy = y + top_px + (i * self.ROW_H + self.ROW_H / 2) * self.zoom
            color = T("PORT_TXT" if p.kind == "text" else "PORT_IMG")
            c.create_oval(x + w - r, cy - r, x + w + r, cy + r,
                          fill=T("BG2"), outline=color, width=2)
            c.create_text(x + w - 14 * self.zoom, cy,
                          text=self._fit_text(p.label, self.NODE_W / 2 - 24),
                          fill=color, anchor="e", font=(fam, psize))

    # ---------- 鼠标 ----------
    def _on_press(self, event):
        try:
            self._handle_press(event)
        except Exception:
            traceback.print_exc()

    def _ctrl_down(self, event):
        return bool(getattr(event, "state", 0) & 0x0004)

    def _handle_press(self, event):
        sx, sy = event.x, event.y
        port = self._hit_port(sx, sy)
        if port is not None and self._is_alt(event):
            side, nid, p = port
            if side == "in":
                self.wf.disconnect_input(nid, p.key)
            else:
                self.wf.disconnect_output(nid, p.key)
            self.dirty = True
            self._render()
            return

        if port is not None and port[0] == "out":
            _side, nid, p = port
            self.drag_mode = "link"
            self.link_from = (nid, p.key, p.kind)
            self.link_cursor = (sx, sy)
            self._render()
            return

        nid = self._hit_node(sx, sy)
        if nid is not None:
            ctrl = self._ctrl_down(event)
            if ctrl:
                if nid in self.selected_ids:
                    self.selected_ids.discard(nid)
                    self.selected_id = next(iter(self.selected_ids), None)
                else:
                    self.selected_ids.add(nid)
                    self.selected_id = nid
            else:
                if nid not in self.selected_ids:
                    self.selected_ids = {nid}
                self.selected_id = nid
            self._build_params()
            if self.selected_ids:
                self.drag_mode = "node"
                self.drag_node_id = nid
                self.drag_start_world = self.s2w(sx, sy)
                self.drag_origins = {
                    i: (self.wf.nodes[i].x, self.wf.nodes[i].y)
                    for i in self.selected_ids if i in self.wf.nodes}
            self._render()
            return

        self.box_additive = self._ctrl_down(event)
        if not self.box_additive:
            self.selected_ids = set()
            self.selected_id = None
            self._build_params()
        self.drag_mode = "box"
        self.box_rect = (sx, sy, sx, sy)
        self._render()

    def _on_motion(self, event):
        sx, sy = event.x, event.y
        if self.drag_mode == "node":
            wx, wy = self.s2w(sx, sy)
            dx = wx - self.drag_start_world[0]
            dy = wy - self.drag_start_world[1]
            for nid, (x0, y0) in self.drag_origins.items():
                node = self.wf.nodes.get(nid)
                if node is None:
                    continue
                node.x = round((x0 + dx) / 4) * 4
                node.y = round((y0 + dy) / 4) * 4
            self.dirty = True
            self._render()
        elif self.drag_mode == "box":
            if self.box_rect is not None:
                self.box_rect = (self.box_rect[0], self.box_rect[1], sx, sy)
            self._render()
        elif self.drag_mode == "pan":
            self.pan_x = self.pan_start[0] - (sx - self.drag_start[0]) / self.zoom
            self.pan_y = self.pan_start[1] - (sy - self.drag_start[1]) / self.zoom
            self._render()
        elif self.drag_mode == "link":
            self.link_cursor = (sx, sy)
            self._render()

    def _finish_box(self):
        if self.box_rect is None:
            return
        x0, y0, x1, y1 = self.box_rect
        if abs(x1 - x0) < 3 and abs(y1 - y0) < 3:
            return
        wx0, wy0 = self.s2w(min(x0, x1), min(y0, y1))
        wx1, wy1 = self.s2w(max(x0, x1), max(y0, y1))
        hit = set()
        for nid, node in self.wf.nodes.items():
            w, h = self._node_layout(node)[:2]
            if (node.x < wx1 and node.x + w > wx0
                    and node.y < wy1 and node.y + h > wy0):
                hit.add(nid)
        if self.box_additive:
            self.selected_ids |= hit
        else:
            self.selected_ids = hit
        if self.selected_id not in self.selected_ids:
            self.selected_id = next(iter(hit), None)
        self._build_params()

    def _on_release(self, event):
        if self.drag_mode == "link" and self.link_from is not None:
            nid, key, kind = self.link_from
            port = self._hit_port(event.x, event.y)
            if port is not None and port[0] == "in":
                _side, target, p = port
                ok = (p.kind == kind and target != nid
                      and not self._would_cycle(nid, target))
                if ok:
                    self.wf.connect(nid, key, target, p.key)
                    self.dirty = True
                else:
                    self.app.toast("连不上：端口类型不同，或会绕成环")
        elif self.drag_mode == "box":
            self._finish_box()
        self.drag_mode = None
        self.link_from = None
        self.drag_origins = {}
        self.box_rect = None
        self._render()

    # ---------- 中键平移 ----------
    def _middle_press(self, event):
        self.drag_mode = "pan"
        self.drag_start = (event.x, event.y)
        self.pan_start = (self.pan_x, self.pan_y)
        self.canvas.configure(cursor="fleur")

    def _middle_motion(self, event):
        if self.drag_mode != "pan":
            return
        self.pan_x = self.pan_start[0] - (event.x - self.drag_start[0]) / self.zoom
        self.pan_y = self.pan_start[1] - (event.y - self.drag_start[1]) / self.zoom
        self._render()

    def _middle_release(self, _event):
        if self.drag_mode == "pan":
            self.drag_mode = None
        self.canvas.configure(cursor="")

    def _would_cycle(self, a, b):
        stack = [b]
        seen = set()
        while stack:
            cur = stack.pop()
            if cur == a:
                return True
            if cur in seen:
                continue
            seen.add(cur)
            for x, _xp, y, _yp in self.wf.edges:
                if x == cur:
                    stack.append(y)
        return False

    def _on_wheel(self, event, up=None, down=None):
        if up is None and down is None:
            delta = getattr(event, "delta", 0)
            if delta > 0:
                up = True
            elif delta < 0:
                down = True
            else:
                return
        old = self.zoom
        factor = 1.12 if up else 1 / 1.12
        new = max(ZOOM_MIN, min(ZOOM_MAX, old * factor))
        wx, wy = self.s2w(event.x, event.y)
        self.zoom = new
        self.pan_x = wx - event.x / new
        self.pan_y = wy - event.y / new
        self._render()

    def _on_right_click(self, event):
        nid = self._hit_node(event.x, event.y)
        menu = tk.Menu(self, tearoff=0)
        if nid is not None:
            if nid not in self.selected_ids:
                self.selected_ids = {nid}
                self.selected_id = nid
            node = self.wf.nodes[nid]
            self._build_params()
            self._render()
            menu.add_command(label="取消跳过" if node.skip else "跳过此节点",
                             command=lambda: self._toggle_skip(nid))
            menu.add_separator()
            menu.add_command(label="断开全部输入",
                             command=lambda: self._disconnect(nid, "in"))
            menu.add_command(label="断开全部输出",
                             command=lambda: self._disconnect(nid, "out"))
            menu.add_separator()
            if len(self.selected_ids) > 1:
                menu.add_command(
                    label=f"删除选中的 {len(self.selected_ids)} 个节点",
                    command=self._delete_selected)
            else:
                menu.add_command(label="删除节点",
                                 command=lambda: self._delete_node(nid))
        else:
            wx, wy = self.s2w(event.x, event.y)
            for nt in NODE_ORDER:
                info = NODE_TYPES[nt]
                menu.add_command(
                    label=f"添加：{info['title']}",
                    command=lambda t=nt, x=wx, y=wy: self._add_node(t, x, y))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _toggle_skip(self, nid):
        node = self.wf.nodes.get(nid)
        if node is not None:
            node.skip = not node.skip
            self.dirty = True
            self._build_params()
            self._render()

    def _disconnect(self, nid, side):
        if side == "in":
            self.wf.disconnect_input(nid)
        else:
            self.wf.disconnect_output(nid)
        self.dirty = True
        self._render()

    def _delete_selected(self):
        ids = set(self.selected_ids)
        if not ids and self.selected_id is not None:
            ids = {self.selected_id}
        for nid in ids:
            self.wf.remove_node(nid)
        self.selected_ids -= ids
        if self.selected_id in ids:
            self.selected_id = next(iter(self.selected_ids), None)
        self._build_params()
        if ids:
            self.dirty = True
            self._render()

    def _delete_node(self, nid):
        self.wf.remove_node(nid)
        self.selected_ids.discard(nid)
        if self.selected_id == nid:
            self.selected_id = next(iter(self.selected_ids), None)
            self._build_params()
        self.dirty = True
        self._render()

    def _add_node(self, ntype, x, y):
        node = self.wf.add_node(ntype, x, y, node_defaults(ntype))
        if ntype == "blueprint" and not node.params.get("name"):
            names = BP_REPO.list()
            if names:
                node.params["name"] = names[0]
        self.selected_id = node.id
        self.selected_ids = {node.id}
        self.dirty = True
        self._build_params()
        self._render()

    def _refresh_blueprints(self):
        for node in self.wf.nodes.values():
            if node.type == "blueprint":
                BP_REPO.load(node.params.get("name", ""), force=True)
        self.wf.sync_dynamic_ports()
        self._build_params()
        self._render()
        self.app.toast("蓝图端口已刷新")

    # ---------- 视图 ----------
    def _fit_view(self):
        nodes = list(self.wf.nodes.values())
        if not nodes:
            self.zoom = 1.0
            self.pan_x = self.pan_y = 0
            self._render()
            return
        min_x = min(n.x for n in nodes)
        min_y = min(n.y for n in nodes)
        max_x = max(n.x + self._node_layout(n)[0] for n in nodes)
        max_y = max(n.y + self._node_layout(n)[1] for n in nodes)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 120 or ch < 120:
            self.after(60, self._fit_view)
            return
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)
        self.zoom = max(ZOOM_MIN,
                        min(1.4, min(cw / span_x, ch / span_y) * 0.94))
        self.pan_x = min_x - (cw / self.zoom - span_x) / 2
        self.pan_y = min_y - (ch / self.zoom - span_y) / 2
        self._render()

    # ---------- 保存 ----------
    def _on_save(self):
        self.wf.sync_dynamic_ports()
        try:
            save_workflow(self.wf)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
            return False
        self.dirty = False
        self.app.refresh_workflow_list()
        self.app.toast(f"已保存流程：{self.wf.name}")
        return True

    def _on_save_as(self):
        name = simpledialog.askstring("另存为", "新的流程名称：", parent=self)
        if not name:
            return
        name = sanitize_name(name)
        if not name:
            return
        self.wf.name = name
        self.flow_name = name
        self.title(f"流程编辑器 — {name}")
        self._on_save()

    def _open_external(self):
        path = filedialog.askopenfilename(
            title="打开流程文件",
            filetypes=[("流程 JSON", "*.json"), ("所有文件", "*.*")],
            parent=self)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            wf = Workflow.from_dict(data)
        except Exception as exc:
            messagebox.showerror(
                "打开失败", f"这个文件不是有效的流程：\n{exc}", parent=self)
            return
        name = ask_import_name(self, WORKFLOWS_DIR,
                               wf.name or Path(path).stem)
        if not name:
            return
        wf.name = name
        try:
            save_workflow(wf)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
            return
        self.wf = wf
        self.flow_name = name
        self.title(f"流程编辑器 — {name}")
        self.dirty = False
        self.selected_ids = set()
        self.selected_id = None
        self._build_params()
        self.app.refresh_workflow_list()
        self._fit_view()
        self.app.toast(f"已导入流程：{name}")

    def _on_close(self):
        if self.dirty:
            choice = messagebox.askyesnocancel(
                "还没保存", "流程有改动，要保存吗？", parent=self)
            if choice is None:
                return
            if choice and not self._on_save():
                return
        self.destroy()

    # ---------- 参数面板 ----------
    def _build_params(self):
        for w in self.params_body.winfo_children():
            w.destroy()
        T = self.app.T
        CARD, FG, MUTED, BORDER = T("CARD"), T("FG"), T("MUTED"), T("BORDER")
        ACCENT, BG2 = T("ACCENT"), T("BG2")

        node = self.wf.nodes.get(self.selected_id)
        if node is None:
            self.node_name_var.set("")
            tk.Label(self.params_body, text="选择一个节点查看参数",
                     bg=CARD, fg=MUTED, font=self.app.F(9)).pack(anchor="w")
            tk.Label(self.params_body,
                     text="\n小提示：\n"
                          "· 中键拖动 = 平移，左键拖空白 = 框选\n"
                          "· 左键拖节点 = 移动（多选整组移动）\n"
                          "· 右键空白加节点，右键节点跳过 / 删除\n"
                          "· Alt+左键点圆点 = 删线\n"
                          "· 蓝图节点有几个 Result，就有几个输出点\n"
                          "· 导出根目录留空会写到 程序目录/导出/…",
                     bg=CARD, fg=MUTED, font=self.app.F(8),
                     justify="left", wraplength=280).pack(anchor="w", pady=(6, 0))
            return

        info = NODE_TYPES.get(node.type, {})
        self.node_name_var.set(
            f"已选 {len(self.selected_ids)} 个" if len(self.selected_ids) > 1
            else f"#{node.id}")

        if len(self.selected_ids) > 1:
            tk.Label(self.params_body,
                     text=f"已选 {len(self.selected_ids)} 个节点：拖动其中任意一个会整组移动，Delete 一起删除。",
                     bg=CARD, fg=ACCENT, font=self.app.F(8),
                     justify="left", wraplength=300).pack(fill="x", pady=(0, 8))

        title_row = tk.Frame(self.params_body, bg=CARD)
        title_row.pack(fill="x", pady=(0, 2))
        tk.Label(title_row, text="●", bg=CARD,
                 fg=NODE_COLORS.get(node.type, ACCENT),
                 font=self.app.F(11)).pack(side="left")
        tk.Label(title_row, text=info.get("title", node.type), bg=CARD,
                 fg=FG, font=self.app.F(11, "bold")).pack(side="left", padx=(4, 0))
        tk.Label(self.params_body, text=info.get("desc", ""), bg=CARD, fg=MUTED,
                 font=self.app.F(8), wraplength=290, justify="left",
                 anchor="w").pack(fill="x", pady=(0, 8))

        skip_var = tk.BooleanVar(value=node.skip)
        tk.Checkbutton(self.params_body, text="跳过此节点", variable=skip_var,
                       bg=CARD, fg=FG, selectcolor=BG2, activebackground=CARD,
                       activeforeground=FG, highlightthickness=0,
                       font=self.app.F(9),
                       command=lambda nid=node.id, v=skip_var:
                       self._set_skip(nid, v.get())).pack(anchor="w", pady=(0, 8))

        for p in info.get("params", []):
            pname = p[0]
            plabel = p[1]
            pdefault = p[2]
            ptype = p[3] if len(p) > 3 else "text"
            options = p[4] if len(p) > 4 else ()
            value = node.params.get(pname, pdefault)

            row = tk.Frame(self.params_body, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=plabel, bg=CARD, fg=FG, font=self.app.F(9),
                     width=8, anchor="w").pack(side="left")

            if ptype == "bool":
                var = tk.BooleanVar(value=bool(value))
                tk.Checkbutton(
                    row, variable=var, bg=CARD, fg=FG, selectcolor=BG2,
                    activebackground=CARD, highlightthickness=0,
                    command=lambda nid=node.id, pn=pname, vv=var:
                    self._set_param(nid, pn, vv.get())).pack(side="left")
            elif ptype == "choice":
                var = tk.StringVar(value=str(value))
                combo = ttk.Combobox(row, textvariable=var, values=list(options),
                                     state="readonly", width=12)
                combo.pack(side="left", fill="x", expand=True)
                combo.bind("<<ComboboxSelected>>",
                           lambda e, nid=node.id, pn=pname, vv=var:
                           self._set_param(nid, pn, vv.get()))
            elif ptype == "file":
                var = tk.StringVar(value=str(value))
                entry = tk.Entry(row, textvariable=var, bg=BG2, fg=FG,
                                 insertbackground=FG, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=self.app.F(9))
                entry.pack(side="left", fill="x", expand=True, ipady=3)

                def browse(v=var):
                    path = filedialog.askopenfilename(
                        title="选择皮肤 PNG",
                        filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
                        parent=self)
                    if path:
                        v.set(path)

                ttk.Button(row, text="…", width=3,
                           command=browse).pack(side="left", padx=(4, 0))
                var.trace_add("write",
                              lambda *a, nid=node.id, pn=pname, vv=var:
                              self._set_param(nid, pn, vv.get()))
            elif ptype == "dir":
                var = tk.StringVar(value=str(value))
                entry = tk.Entry(row, textvariable=var, bg=BG2, fg=FG,
                                 insertbackground=FG, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=self.app.F(9))
                entry.pack(side="left", fill="x", expand=True, ipady=3)

                def browse_dir(v=var):
                    path = filedialog.askdirectory(
                        title="选择导出文件夹", parent=self,
                        initialdir=str(initial_dir_for(v.get())))
                    if path:
                        v.set(path)

                ttk.Button(row, text="…", width=3,
                           command=browse_dir).pack(side="left", padx=(4, 0))
                var.trace_add("write",
                              lambda *a, nid=node.id, pn=pname, vv=var:
                              self._set_param(nid, pn, vv.get()))
            elif ptype == "blueprint":
                names = BP_REPO.list()
                var = tk.StringVar(value=str(value))
                combo = ttk.Combobox(row, textvariable=var, values=names,
                                     state="readonly", width=12)
                combo.pack(side="left", fill="x", expand=True)

                def pick_blueprint(_e=None, nid=node.id, vv=var):
                    self._set_param(nid, "name", vv.get())
                    self._build_params()

                combo.bind("<<ComboboxSelected>>", pick_blueprint)
                ttk.Button(row, text="编辑…", width=5,
                           command=lambda nid=node.id:
                           self._edit_blueprint(nid)).pack(side="left", padx=(4, 0))
            elif ptype in ("int", "float"):
                var = tk.StringVar(value=str(value))
                entry = tk.Entry(row, textvariable=var, bg=BG2, fg=FG,
                                 insertbackground=FG, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=self.app.F(9))
                entry.pack(side="left", fill="x", expand=True, ipady=3)
                var.trace_add("write",
                              lambda *a, nid=node.id, pn=pname, vv=var, t=ptype:
                              self._set_number(nid, pn, vv.get(), t))
            else:
                var = tk.StringVar(value=str(value))
                entry = tk.Entry(row, textvariable=var, bg=BG2, fg=FG,
                                 insertbackground=FG, relief="flat",
                                 highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=self.app.F(9))
                entry.pack(side="left", fill="x", expand=True, ipady=3)
                var.trace_add("write",
                              lambda *a, nid=node.id, pn=pname, vv=var:
                              self._set_param(nid, pn, vv.get()))

        if node.type == "blueprint":
            bp = blueprint_of(node)
            count = f"{len(bp.result_ports())} 个有效 Result" if bp else "蓝图未选择"
            tk.Label(self.params_body, text=count, bg=CARD, fg=ACCENT,
                     font=self.app.F(9, "bold"), anchor="w").pack(
                         fill="x", pady=(10, 0))
        if node.type == "break":
            n = len(node_ports(node)[1])
            tk.Label(self.params_body, text=f"当前输出：{n} 个（自动）",
                     bg=CARD, fg=ACCENT, font=self.app.F(9, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 0))
        if node.type == "make":
            n = len(node_ports(node)[0])
            tk.Label(self.params_body, text=f"当前输入：{n} 个",
                     bg=CARD, fg=ACCENT, font=self.app.F(9, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 0))

        hint = info.get("hint", "")
        if hint:
            tk.Label(self.params_body, text=hint, bg=CARD, fg=MUTED,
                     font=self.app.F(8), wraplength=290, justify="left",
                     anchor="w").pack(fill="x", pady=(10, 0))

    def _edit_blueprint(self, nid):
        node = self.wf.nodes.get(nid)
        if node is None:
            return
        name = node.params.get("name", "") or (BP_REPO.list() or [""])[0]
        if not name:
            self.app.toast("还没有蓝图，先在主界面打开蓝图编辑器新建一个")
            return
        editor = BlueprintEditor(self.app, name)
        self.wait_window(editor)
        BP_REPO.load(name, force=True)
        self._build_params()
        self._render()

    def _set_skip(self, nid, value):
        node = self.wf.nodes.get(nid)
        if node is not None:
            node.skip = bool(value)
            self.dirty = True
            self._render()

    def _set_param(self, nid, pname, value):
        node = self.wf.nodes.get(nid)
        if node is None:
            return
        node.params[pname] = value
        if node.type == "pause" and pname == "mode":
            self.wf.prune_edges()
        self.dirty = True
        self._render()

    def _set_number(self, nid, pname, text, ptype):
        try:
            value = int(text) if ptype == "int" else float(text)
        except (TypeError, ValueError):
            return
        node = self.wf.nodes.get(nid)
        if (node is not None and node.type == "make"
                and pname == "count"):
            value = max(1, min(MAX_MAKE_INPUTS, int(value)))
        self._set_param(nid, pname, value)
        if node is not None and node.type == "make" and pname == "count":
            self.wf.sync_dynamic_ports()
            self._render()


# 流程图里的节点颜色（蓝图编辑器里用同一套）
BP_NODE_COLORS = {
    "input": "#5aa9e6",
    "canvas": "#3fb6a0",
    "result": "#ff9e64",
    "rect": "#f78fb3",
}

BP_SELECT_COLORS = ("#6cb4ff", "#ffb86c", "#7ee787", "#f78fb3",
                    "#b48ead", "#56cfe1", "#ffd166", "#c3a6ff")


class BlueprintEditor(tk.Toplevel):
    """输入（示例图）→ 画布（贴图排版）→ Result（命名）。"""

    def __init__(self, app, name=None):
        super().__init__(app.root)
        self.app = app
        names = BP_REPO.list()
        self.bp_name = name or (names[0] if names else "基础")
        bp = BP_REPO.load(self.bp_name)
        if bp is None:
            bp = make_default_blueprint(self.bp_name)
            try:
                BP_REPO.save(bp)
            except Exception:
                pass
        self.bp = bp
        self.ref_image = self._load_ref_image()

        self.dirty = False
        self.selected_id = None
        self.selected_ids = set()
        self.sel_selection_id = None
        self.sel_mapping_id = None
        self._loading = False
        self._drag = None
        self._input_view = None      # (ox, oy, scale)
        self._board_view = None      # (ox, oy, scale)
        self._input_photo = None
        self._board_photo = None
        self._map_drag = None
        self._box_rect = None
        self._box_additive = False
        self._drag_origins = {}
        self._drag_start_world = (0.0, 0.0)

        self.zoom = 1.0
        self.pan_x = 20.0
        self.pan_y = 20.0
        self.drag_mode = None
        self.drag_start = (0, 0)
        self.drag_node_id = None
        self.drag_offset = (0.0, 0.0)
        self.pan_start = (0.0, 0.0)
        self.link_from = None
        self.link_cursor = (0, 0)

        self.title(f"蓝图编辑器 — {self.bp.name}")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        center_window(self, min(1440, max(1060, sw - 70)),
                      min(900, max(700, sh - 100)))
        self.minsize(1060, 700)
        self.configure(bg=app.T("BG"))
        self.transient(app.root)

        try:
            self._font_small = tkfont.Font(family=app._font_family, size=8)
            self._font_title = tkfont.Font(family=app._font_family, size=10,
                                           weight="bold")
        except Exception:
            self._font_small = self._font_title = None

        self._build()
        self.after(40, self._render)
        self.after(90, self._fit_view)

    # ---------- 数据辅助 ----------
    def _fit_text(self, text, max_px, font=None):
        text = str(text)
        font = font or self._font_small
        if font is None:
            return truncate(text, 20)
        if font.measure(text) <= max_px:
            return text
        cut = text
        while cut and font.measure(cut + "…") > max_px:
            cut = cut[:-1]
        return (cut + "…") if cut else ""

    def _load_ref_image(self):
        if not self.bp.ref_image:
            return None
        path = BP_REPO.folder / self.bp.ref_image
        if not path.exists():
            return None
        try:
            return load_rgba(path)
        except Exception:
            return None

    def _current_canvas(self):
        node = self.bp.nodes.get(self.selected_id)
        if node is not None and node.kind == "canvas":
            return node
        return None

    def _current_mapping(self):
        canvas = self._current_canvas()
        if canvas is None:
            return None
        return self.bp.mapping(canvas, self.sel_mapping_id)

    def _select_node(self, nid):
        changed = self.selected_id != nid
        self.selected_id = nid
        if changed:
            self.sel_mapping_id = None
            self._build_canvas_panel()
        self._render()

    # ---------- 构建 ----------
    def _build(self):
        T = self.app.T
        BG, BORDER, MUTED = T("BG"), T("BORDER"), T("MUTED")

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", side="top")

        tk.Label(bar, text="蓝图", bg=BG, fg=MUTED,
                 font=self.app.F(9)).pack(side="left", padx=(14, 6), pady=8)
        self.bp_var = tk.StringVar(value=self.bp_name)
        self.bp_combo = ttk.Combobox(bar, textvariable=self.bp_var, width=16,
                                     state="readonly",
                                     postcommand=self._refresh_bp_list)
        self.bp_combo.pack(side="left", pady=8)
        self.bp_combo.bind("<<ComboboxSelected>>", self._on_pick_blueprint)

        icon_bg = T("BG")
        icon_fg = T("MUTED")
        icon_hover = T("HOVER")
        for kind, cmd, tip in (
                ("plus", self._new_blueprint, "新建蓝图"),
                ("copy", self._save_as, "另存为"),
                ("trash", self._delete_blueprint, "删除蓝图"),
                ("open", self._open_external, "打开蓝图文件"),
                ("folder", lambda: open_in_file_manager(BLUEPRINTS_DIR),
                 "蓝图目录")):
            IconButton(bar, kind, cmd, icon_bg, icon_fg, icon_hover,
                       T("FG"), size=30, tip=tip).pack(
                           side="left", padx=(2, 0), pady=7)

        IconButton(bar, "save", self._save, icon_bg, T("ACCENT"),
                   icon_hover, T("ACCENT_HOVER"), size=30,
                   tip="保存蓝图").pack(side="left", padx=(8, 0), pady=7)

        self.summary_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self.summary_var, bg=BG, fg=MUTED,
                 font=self.app.F(9)).pack(side="left", padx=(14, 0), pady=8)

        IconButton(bar, "close", self._on_close, icon_bg, icon_fg,
                   T("DANGER"), "#ffffff", size=30, tip="关闭").pack(
                       side="right", padx=12, pady=7)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=0, minsize=474)

        self.canvas = tk.Canvas(body, bg=T("BG2"), highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        right = tk.Frame(body, bg=T("CARD"), width=474,
                         highlightthickness=1, highlightbackground=BORDER)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_propagate(False)

        # 右侧可滚动（窗口小的时候也能看到全部内容）
        self.panel_scroll = tk.Canvas(right, bg=T("CARD"),
                                      highlightthickness=0, bd=0)
        pscroll = SlimScrollbar(right, command=self.panel_scroll.yview,
                                bg=T("CARD"), thumb=T("BORDER"),
                                hover=T("ACCENT"))
        self.panel_scroll.configure(yscrollcommand=pscroll.set)
        pscroll.pack(side="right", fill="y")
        self.panel_scroll.pack(side="left", fill="both", expand=True)

        self.panel = tk.Frame(self.panel_scroll, bg=T("CARD"))
        self.panel_window = self.panel_scroll.create_window(
            (0, 0), window=self.panel, anchor="nw", width=450)
        self.panel.bind(
            "<Configure>",
            lambda e: self.panel_scroll.configure(
                scrollregion=self.panel_scroll.bbox("all")))
        self.panel_scroll.bind(
            "<Configure>",
            lambda e: self.panel_scroll.itemconfigure(
                self.panel_window, width=e.width))
        self.panel_scroll.bind(
            "<MouseWheel>",
            lambda e: self.panel_scroll.yview_scroll(int(-e.delta / 120),
                                                     "units"))
        self.panel.bind(
            "<MouseWheel>",
            lambda e: self.panel_scroll.yview_scroll(int(-e.delta / 120),
                                                     "units"))

        top = tk.Frame(self.panel, bg=T("CARD"))
        top.pack(fill="x", padx=14, pady=(12, 2))
        tk.Label(top, text="输入与选区", bg=T("CARD"), fg=T("ACCENT"),
                 font=self.app.F(10, "bold"), anchor="w").pack(side="left")
        self.img_info_var = tk.StringVar(value="")
        tk.Label(top, textvariable=self.img_info_var, bg=T("CARD"),
                 fg=MUTED, font=self.app.F(8)).pack(side="right")
        ttk.Button(top, text="放大", width=4,
                   command=self.open_input_fullscreen).pack(
                       side="right", padx=(0, 8))
        self.grid_var = tk.BooleanVar(
            value=bool(self.app.settings.get("grid", True)))
        tk.Checkbutton(top, text="网格", variable=self.grid_var, bg=T("CARD"),
                       fg=MUTED, selectcolor=T("BG2"),
                       activebackground=T("CARD"), activeforeground=T("FG"),
                       highlightthickness=0, font=self.app.F(8),
                       command=self._toggle_grid).pack(side="right",
                                                       padx=(0, 6))

        self.input_panel = tk.Frame(self.panel, bg=T("CARD"))
        self.input_panel.pack(fill="x", padx=14)

        sep = tk.Frame(self.panel, bg=BORDER, height=1)
        sep.pack(fill="x", padx=14, pady=8)

        bot = tk.Frame(self.panel, bg=T("CARD"))
        bot.pack(fill="x", padx=14, pady=(0, 14))
        bot_head = tk.Frame(bot, bg=T("CARD"))
        bot_head.pack(fill="x")
        self.bot_title_var = tk.StringVar(value="画布与映射")
        tk.Label(bot_head, textvariable=self.bot_title_var, bg=T("CARD"),
                 fg=T("ACCENT"), font=self.app.F(10, "bold"),
                 anchor="w").pack(side="left")
        ttk.Button(bot_head, text="放大编辑", width=7,
                   command=self.open_board_fullscreen).pack(side="right")
        self.canvas_panel = tk.Frame(bot, bg=T("CARD"))
        self.canvas_panel.pack(fill="x", pady=(4, 0))

        c = self.canvas
        c.bind("<Button-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_motion)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Button-2>", self._middle_press)
        c.bind("<B2-Motion>", self._middle_motion)
        c.bind("<ButtonRelease-2>", self._middle_release)
        c.bind("<MouseWheel>", self._on_wheel)
        c.bind("<Button-4>", lambda e: self._on_wheel(e, up=True))
        c.bind("<Button-5>", lambda e: self._on_wheel(e, down=True))
        c.bind("<Button-3>", self._on_right_click)
        if sys.platform == "darwin":
            c.bind("<Control-Button-1>", self._on_right_click)
        c.bind("<Configure>", lambda e: self._render())
        self.bind("<Delete>", lambda e: self._delete_selected())
        self.bind("<Control-s>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_input_panel()
        self._build_canvas_panel()
        self._update_summary()

    def _refresh_bp_list(self):
        self.bp_combo["values"] = BP_REPO.list()

    def _update_summary(self):
        ports = self.bp.result_ports()
        self.summary_var.set(
            f"{len(ports)}R · {len(self.bp.canvas_nodes())} 画布"
            f" · {len(self.bp.selections)} 选区"
            f" · 流程里蓝图节点有 {len(ports) + 1} 个输出点")
        self.title(f"蓝图编辑器 — {self.bp.name}")

    # ================= 右侧：输入与选区 =================
    def _build_input_panel(self):
        T = self.app.T
        CARD, FG, MUTED, BORDER = T("CARD"), T("FG"), T("MUTED"), T("BORDER")
        BG2, ACCENT, DANGER = T("BG2"), T("ACCENT"), T("DANGER")
        F = self.app.F

        for w in self.input_panel.winfo_children():
            w.destroy()

        row = tk.Frame(self.input_panel, bg=CARD)
        row.pack(fill="x", pady=(6, 4))
        ttk.Button(row, text="导入示例图…",
                   command=self._import_ref).pack(side="left")
        if self.ref_image is not None:
            tk.Label(row, text=f"{self.ref_image.width}×{self.ref_image.height}"
                               "  ·  只在设计时参照",
                     bg=CARD, fg=MUTED, font=F(8)).pack(side="left", padx=(8, 0))

        self.input_canvas = tk.Canvas(self.input_panel, bg=T("BG2"),
                                      height=142, highlightthickness=1,
                                      highlightbackground=BORDER)
        self.input_canvas.pack(fill="x", pady=(2, 4))
        self.input_canvas.bind("<Button-1>", self._input_press)
        self.input_canvas.bind("<B1-Motion>", self._input_motion)
        self.input_canvas.bind("<ButtonRelease-1>", self._input_release)
        self.input_canvas.bind("<Button-3>", self._input_right_click)
        self.input_canvas.bind("<Configure>",
                               lambda e: self._render_input_preview())

        list_head = tk.Frame(self.input_panel, bg=CARD)
        list_head.pack(fill="x")
        tk.Label(list_head, text="在图上拖框新建选区", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        self.sel_count_var = tk.StringVar(value="")
        tk.Label(list_head, textvariable=self.sel_count_var, bg=CARD,
                 fg=MUTED, font=F(8)).pack(side="right")

        self.sel_list = tk.Listbox(
            self.input_panel, bg=BG2, fg=FG, selectbackground=ACCENT,
            selectforeground=T("ACCENT_FG"), relief="flat", height=3,
            highlightthickness=1, highlightbackground=BORDER,
            activestyle="none", font=F(9), exportselection=False)
        self.sel_list.pack(fill="x", pady=(2, 2))
        self.sel_list.bind("<<ListboxSelect>>", self._on_sel_list_select)

        btns = tk.Frame(self.input_panel, bg=CARD)
        btns.pack(fill="x", pady=(0, 4))
        ttk.Button(btns, text="删除选区",
                   command=self._delete_selection).pack(side="left")

        form = tk.Frame(self.input_panel, bg=CARD)
        form.pack(fill="x", pady=(0, 2))
        self.sel_x_var = tk.StringVar()
        self.sel_y_var = tk.StringVar()
        self.sel_w_var = tk.StringVar()
        self.sel_h_var = tk.StringVar()
        tk.Label(form, text="名称", bg=CARD, fg=MUTED, font=F(8),
                 anchor="w").grid(row=0, column=0, sticky="w")
        self.sel_name_var = tk.StringVar(value="")
        e_name = tk.Entry(form, textvariable=self.sel_name_var, bg=BG2, fg=FG,
                          insertbackground=FG, relief="flat", width=10,
                          highlightthickness=1, highlightbackground=BORDER,
                          highlightcolor=ACCENT, font=F(9))
        e_name.grid(row=0, column=1, sticky="ew", ipady=2, padx=(2, 8))
        form.columnconfigure(1, weight=1)
        self.sel_name_var.trace_add("write", lambda *a: self._apply_sel_name())
        for i, (label, var) in enumerate((("X", self.sel_x_var),
                                          ("Y", self.sel_y_var),
                                          ("W", self.sel_w_var),
                                          ("H", self.sel_h_var))):
            tk.Label(form, text=label, bg=CARD, fg=MUTED,
                     font=F(8)).grid(row=0, column=2 + i * 2, sticky="w",
                                     padx=(0, 2))
            e = tk.Entry(form, textvariable=var, bg=BG2, fg=FG, width=3,
                         insertbackground=FG, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, font=F(9))
            e.grid(row=0, column=3 + i * 2, sticky="w", ipady=2,
                   padx=(0, 4))
            var.trace_add("write", lambda *a: self._apply_sel_geom())

        self.img_info_var.set(
            f"{self.ref_image.width}×{self.ref_image.height}"
            if self.ref_image is not None else "未导入示例图")
        self._refresh_selection_list()
        self._load_selection_vars()
        self.after(10, self._render_input_preview)

    def _refresh_selection_list(self):
        if not hasattr(self, "sel_list"):
            return
        self.sel_list.delete(0, "end")
        for sel in self.bp.selections:
            self.sel_list.insert(
                "end", f"{sel.name}   ({sel.x},{sel.y}) {sel.w}×{sel.h}")
        for i, sel in enumerate(self.bp.selections):
            if sel.id == self.sel_selection_id:
                self.sel_list.selection_set(i)
        self.sel_count_var.set(f"{len(self.bp.selections)} 个" if
                               self.bp.selections else "还没有选区")

    def _load_selection_vars(self):
        sel = self.bp.selection(self.sel_selection_id) if self.sel_selection_id else None
        self._loading = True
        try:
            if sel is None:
                self.sel_name_var.set("")
                self.sel_x_var.set("")
                self.sel_y_var.set("")
                self.sel_w_var.set("")
                self.sel_h_var.set("")
            else:
                self.sel_name_var.set(sel.name)
                self.sel_x_var.set(str(sel.x))
                self.sel_y_var.set(str(sel.y))
                self.sel_w_var.set(str(sel.w))
                self.sel_h_var.set(str(sel.h))
        finally:
            self._loading = False

    def _on_sel_list_select(self, _e=None):
        cur = self.sel_list.curselection()
        if not cur:
            return
        idx = int(cur[0])
        if 0 <= idx < len(self.bp.selections):
            self.sel_selection_id = self.bp.selections[idx].id
            self._load_selection_vars()
            self._render_input_preview()
            self._render_board()
            self._render()

    def _apply_sel_name(self):
        if self._loading:
            return
        sel = self.bp.selection(self.sel_selection_id) if self.sel_selection_id else None
        if sel is None:
            return
        sel.name = self.sel_name_var.get().strip() or sel.name
        self._refresh_selection_list()
        self._render_input_preview()
        self._render_board()
        self.dirty = True

    def _apply_sel_geom(self):
        if self._loading:
            return
        sel = self.bp.selection(self.sel_selection_id) if self.sel_selection_id else None
        if sel is None:
            return
        try:
            x = int(float(self.sel_x_var.get()))
            y = int(float(self.sel_y_var.get()))
            w = int(float(self.sel_w_var.get()))
            h = int(float(self.sel_h_var.get()))
        except ValueError:
            return
        iw = self.ref_image.width if self.ref_image else 64
        ih = self.ref_image.height if self.ref_image else 64
        w = max(1, min(iw, w))
        h = max(1, min(ih, h))
        x = max(0, min(iw - w, x))
        y = max(0, min(ih - h, y))
        sel.x, sel.y, sel.w, sel.h = x, y, w, h
        self.dirty = True
        self._render_input_preview()
        self._render_board()
        self._refresh_selection_list()

    def _rename_selection(self):
        sel = self.bp.selection(self.sel_selection_id) if self.sel_selection_id else None
        if sel is None:
            return
        name = simpledialog.askstring("重命名选区", "选区名字：",
                                      initialvalue=sel.name, parent=self)
        if not name:
            return
        sel.name = sanitize_name(name) or sel.name
        self._load_selection_vars()
        self._refresh_selection_list()
        self._render_input_preview()
        self._render_board()
        self.dirty = True

    def _delete_selection(self):
        sel = self.bp.selection(self.sel_selection_id) if self.sel_selection_id else None
        if sel is None:
            return
        self.bp.remove_selection(sel.id)
        self.sel_selection_id = None
        self.sel_mapping_id = None
        self.dirty = True
        self._refresh_selection_list()
        self._load_selection_vars()
        self._render_input_preview()
        self._build_canvas_panel()
        self._render()

    def _import_ref(self):
        path = filedialog.askopenfilename(
            title="选择示例皮肤 PNG",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
            parent=self)
        if not path:
            return
        try:
            im = load_rgba(path)
        except Exception as exc:
            messagebox.showerror("读取失败", str(exc), parent=self)
            return
        target = BP_REPO.ref_path(self.bp.name)
        try:
            im.save(target)
        except Exception as exc:
            messagebox.showerror("保存失败", f"复制示例图失败：\n{exc}",
                                 parent=self)
            return
        self.ref_image = im
        self.bp.ref_image = target.name
        self.bp.image_w, self.bp.image_h = im.size
        for sel in self.bp.selections:
            sel.w = min(sel.w, im.width)
            sel.h = min(sel.h, im.height)
            sel.x = max(0, min(im.width - sel.w, sel.x))
            sel.y = max(0, min(im.height - sel.h, sel.y))
        self.dirty = True
        self._build_input_panel()
        self._render_board()
        self._render()
        self._update_summary()

    # ---------- 示例图画布交互 ----------
    def _render_input_preview(self):
        if not hasattr(self, "input_canvas"):
            return
        c = self.input_canvas
        if not c.winfo_exists():
            return
        c.delete("all")
        T = self.app.T
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 20 or ch < 20:
            return
        if self.ref_image is None:
            c.create_text(cw / 2, ch / 2,
                          text="还没有示例图\n点上面「导入示例图…」",
                          fill=T("MUTED"), justify="center",
                          font=self.app.F(9))
            self._input_view = None
            return
        iw, ih = self.ref_image.size
        scale = min((cw - 12) / iw, (ch - 12) / ih)
        scale = max(0.2, scale)
        dw, dh = max(1, int(iw * scale)), max(1, int(ih * scale))
        ox = (cw - dw) // 2
        oy = (ch - dh) // 2
        photo = ImageTk.PhotoImage(
            self.ref_image.resize((dw, dh), Image.NEAREST))
        self._input_photo = photo
        c.create_image(ox, oy, image=photo, anchor="nw")
        c.create_rectangle(ox, oy, ox + dw, oy + dh, outline=T("BORDER"))
        self._draw_pixel_grid(c, ox, oy, scale, iw, ih, T)
        self._input_view = (ox, oy, scale)

        for sel in self.bp.selections:
            x1 = ox + sel.x * scale
            y1 = oy + sel.y * scale
            x2 = x1 + sel.w * scale
            y2 = y1 + sel.h * scale
            selected = sel.id == self.sel_selection_id
            color = T("ACCENT") if selected else T("PORT_TXT")
            c.create_rectangle(x1, y1, x2, y2, outline=color,
                               width=2 if selected else 1)
            if selected:
                font = self._font_small
                tw = (font.measure(sel.name) if font is not None
                      else len(sel.name) * 8) + 8
                c.create_rectangle(x1, y1, x1 + tw, y1 + 15,
                                   fill=color, outline="")
                c.create_text(x1 + 4, y1 + 2, text=sel.name, fill=T("BG"),
                              anchor="nw", font=self.app.F(8))
                c.create_rectangle(x2 - 6, y2 - 6, x2 + 1, y2 + 1,
                                   fill=color, outline="")

        drag = self._drag
        if drag and drag.get("mode") == "create" and drag.get("rect"):
            x1, y1, x2, y2 = drag["rect"]
            c.create_rectangle(x1, y1, x2, y2, outline=T("ACCENT"),
                               dash=(4, 3), width=2)

    def _to_image_xy(self, sx, sy):
        if self._input_view is None:
            return None
        ox, oy, s = self._input_view
        return (sx - ox) / s, (sy - oy) / s

    def _selection_hit(self, ix, iy):
        for sel in reversed(self.bp.selections):
            if (sel.x <= ix <= sel.x + sel.w
                    and sel.y <= iy <= sel.y + sel.h):
                return sel
        return None

    def _input_press(self, event):
        if self.ref_image is None or self._input_view is None:
            return
        pos = self._to_image_xy(event.x, event.y)
        if pos is None:
            return
        ix, iy = pos
        sel = self._selection_hit(ix, iy)
        if sel is not None:
            self.sel_selection_id = sel.id
            self._load_selection_vars()
            self._refresh_selection_list()
            x2 = sel.x + sel.w
            y2 = sel.y + sel.h
            ox, oy, s = self._input_view
            near = (abs(event.x - (ox + x2 * s)) <= 9
                    and abs(event.y - (oy + y2 * s)) <= 9)
            self._drag = {
                "mode": "resize" if near else "move",
                "sel": sel,
                "ix": ix, "iy": iy,
                "orig": (sel.x, sel.y, sel.w, sel.h),
            }
        else:
            ox, oy, s = self._input_view
            self._drag = {
                "mode": "create",
                "start": (ix, iy),
                "origin": (ox, oy),
                "scale": s,
                "rect": None,
            }
        self._render_input_preview()

    def _input_motion(self, event):
        drag = self._drag
        if drag is None:
            return
        iw = self.ref_image.width if self.ref_image else 64
        ih = self.ref_image.height if self.ref_image else 64
        pos = self._to_image_xy(event.x, event.y)
        if pos is None:
            return
        ix = max(0, min(iw, pos[0]))
        iy = max(0, min(ih, pos[1]))
        if drag["mode"] == "create":
            x0, y0 = drag["start"]
            ox, oy, s = self._input_view
            x0, x1 = int(round(min(x0, ix))), int(round(max(x0, ix)))
            y0, y1 = int(round(min(y0, iy))), int(round(max(y0, iy)))
            drag["rect"] = (ox + x0 * s, oy + y0 * s,
                            ox + x1 * s, oy + y1 * s)
            drag["box"] = (x0, y0, x1, y1)
            self._render_input_preview()
        elif drag["mode"] == "move":
            sel = drag["sel"]
            dx = int(round(ix - drag["ix"]))
            dy = int(round(iy - drag["iy"]))
            ox0, oy0, w0, h0 = drag["orig"]
            sel.x = max(0, min(iw - w0, ox0 + dx))
            sel.y = max(0, min(ih - h0, oy0 + dy))
            self.dirty = True
            self._render_input_preview()
            self._render_board()
            self._load_selection_vars()
        elif drag["mode"] == "resize":
            sel = drag["sel"]
            ox0, oy0, w0, h0 = drag["orig"]
            nx2 = max(ox0 + 1, min(iw, int(round(ix))))
            ny2 = max(oy0 + 1, min(ih, int(round(iy))))
            sel.w = max(1, nx2 - sel.x)
            sel.h = max(1, ny2 - sel.y)
            self.dirty = True
            self._render_input_preview()
            self._render_board()
            self._load_selection_vars()

    def _input_release(self, event):
        drag = self._drag
        self._drag = None
        if drag is None:
            return
        if drag.get("mode") == "create" and drag.get("box"):
            x0, y0, x1, y1 = drag["box"]
            w = int(round(x1 - x0))
            h = int(round(y1 - y0))
            if w >= 1 and h >= 1:
                sel = self.bp.add_selection(int(round(x0)), int(round(y0)),
                                            w, h)
                self.sel_selection_id = sel.id
                self.dirty = True
                self._refresh_selection_list()
                self._load_selection_vars()
                self._render_input_preview()
                self._update_summary()
        else:
            self._refresh_selection_list()
            self._load_selection_vars()
            self._render_input_preview()
            self._render_board()
        self._render()

    def _input_right_click(self, event):
        if self.ref_image is None or self._input_view is None:
            return
        pos = self._to_image_xy(event.x, event.y)
        if pos is None:
            return
        sel = self._selection_hit(*pos)
        menu = tk.Menu(self, tearoff=0)
        if sel is None:
            menu.add_command(label="导入示例图…", command=self._import_ref)
        else:
            self.sel_selection_id = sel.id
            self._load_selection_vars()
            self._refresh_selection_list()
            self._render_input_preview()
            menu.add_command(label="重命名…", command=self._rename_selection)
            menu.add_separator()
            menu.add_command(label="删除选区",
                             command=self._delete_selection)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ================= 右侧：画布与映射 =================
    def _build_canvas_panel(self):
        T = self.app.T
        CARD, FG, MUTED, BORDER = T("CARD"), T("FG"), T("MUTED"), T("BORDER")
        BG2, ACCENT, OK, DANGER = T("BG2"), T("ACCENT"), T("OK"), T("DANGER")
        F = self.app.F

        for w in self.canvas_panel.winfo_children():
            w.destroy()
        node = self.bp.nodes.get(self.selected_id)
        if hasattr(self, "bot_title_var"):
            self.bot_title_var.set({
                "canvas": "画布与映射",
                "rect": "矩形与颜色",
                "result": "Result 命名",
            }.get(node.kind if node is not None else None, "画布与映射"))

        if node is None:
            tk.Label(self.canvas_panel,
                     text="选中画布，这里能改尺寸、贴图位置和叠放顺序。\n"
                          "选中 Result，这里能改它的命名模板。",
                     bg=CARD, fg=MUTED, font=F(9), justify="left",
                     anchor="w", wraplength=430).pack(fill="x", pady=(6, 0))
            return

        if node.kind == "input":
            tk.Label(self.canvas_panel,
                     text="输入节点代表上面那张示例图。\n"
                          "画布从这里取选区素材，运行时会套到真实皮肤上。",
                     bg=CARD, fg=MUTED, font=F(9), justify="left",
                     anchor="w", wraplength=430).pack(fill="x", pady=(6, 0))
            return

        if node.kind == "result":
            self._build_result_panel(node)
            return

        if node.kind == "rect":
            self._build_rect_panel(node)
            return

        # ---- 画布 ----
        row = tk.Frame(self.canvas_panel, bg=CARD)
        row.pack(fill="x", pady=(4, 4))
        tk.Label(row, text="名称", bg=CARD, fg=MUTED, font=F(8),
                 width=4, anchor="w").pack(side="left")
        self.cv_name_var = tk.StringVar(value=node.name)
        tk.Entry(row, textvariable=self.cv_name_var, bg=BG2, fg=FG, width=12,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", fill="x", expand=True, ipady=2,
                                   padx=(0, 8))
        self.cv_name_var.trace_add(
            "write", lambda *a: self._apply_canvas_name(node))

        tk.Label(row, text="尺寸", bg=CARD, fg=MUTED, font=F(8)).pack(
            side="left")
        self.cv_w_var = tk.StringVar(value=str(node.width))
        self.cv_h_var = tk.StringVar(value=str(node.height))
        tk.Entry(row, textvariable=self.cv_w_var, bg=BG2, fg=FG, width=4,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", ipady=2, padx=(4, 0))
        tk.Label(row, text="×", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left", padx=3)
        tk.Entry(row, textvariable=self.cv_h_var, bg=BG2, fg=FG, width=4,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", ipady=2)
        tk.Label(row, text="px", bg=CARD, fg=MUTED, font=F(8)).pack(
            side="left", padx=(3, 0))
        self.cv_w_var.trace_add("write", lambda *a: self._apply_canvas_size(node))
        self.cv_h_var.trace_add("write", lambda *a: self._apply_canvas_size(node))

        self.board_canvas = tk.Canvas(self.canvas_panel, bg=T("BG2"),
                                      height=160, highlightthickness=1,
                                      highlightbackground=BORDER)
        self.board_canvas.pack(fill="x", pady=(2, 4))
        self.board_canvas.bind("<Button-1>", self._board_press)
        self.board_canvas.bind("<B1-Motion>", self._board_motion)
        self.board_canvas.bind("<ButtonRelease-1>", self._board_release)
        self.board_canvas.bind("<Configure>",
                               lambda e: self._render_board())

        head = tk.Frame(self.canvas_panel, bg=CARD)
        head.pack(fill="x")
        tk.Label(head, text="映射（从上到下 = 先贴到后贴）",
                 bg=CARD, fg=MUTED, font=F(8)).pack(side="left")
        self.map_count_var = tk.StringVar(value="")
        tk.Label(head, textvariable=self.map_count_var, bg=CARD,
                 fg=MUTED, font=F(8)).pack(side="right")

        mats_row = tk.Frame(self.canvas_panel, bg=CARD)
        mats_row.pack(fill="x", pady=(4, 2))
        tk.Label(mats_row, text="素材", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        self._material_choices = self.bp.materials_for(node)
        labels = [m[2] for m in self._material_choices]
        self.material_combo = ttk.Combobox(mats_row, values=labels,
                                           state="readonly")
        self.material_combo.pack(side="left", fill="x", expand=True,
                                 padx=(4, 4))
        if labels:
            chosen = 0
            for i, (kind, rid, *_rest) in enumerate(self._material_choices):
                if kind == "selection" and rid == self.sel_selection_id:
                    chosen = i
                    break
            self.material_combo.current(chosen)
        else:
            self.material_combo.set("（没有素材）")
            self.material_combo.configure(state="disabled")
        ttk.Button(mats_row, text="添加映射",
                   command=self._add_mapping).pack(side="left")

        self.map_list = tk.Listbox(
            self.canvas_panel, bg=BG2, fg=FG, selectbackground=ACCENT,
            selectforeground=T("ACCENT_FG"), relief="flat", height=3,
            highlightthickness=1, highlightbackground=BORDER,
            activestyle="none", font=F(9), exportselection=False)
        self.map_list.pack(fill="x", pady=(2, 2))
        self.map_list.bind("<<ListboxSelect>>", self._on_map_list_select)
        self.map_list.bind("<Button-1>", self._map_list_press)
        self.map_list.bind("<B1-Motion>", self._map_list_motion)
        self.map_list.bind("<ButtonRelease-1>", self._map_list_release)

        btns = tk.Frame(self.canvas_panel, bg=CARD)
        btns.pack(fill="x", pady=(0, 4))
        ttk.Button(btns, text="删除",
                   command=self._delete_mapping).pack(side="left")
        ttk.Button(btns, text="↑", width=3,
                   command=lambda: self._move_mapping(-1)).pack(side="left",
                                                               padx=(4, 0))
        ttk.Button(btns, text="↓", width=3,
                   command=lambda: self._move_mapping(1)).pack(side="left",
                                                              padx=(4, 0))
        ttk.Button(btns, text="旋转 90°",
                   command=self._rotate_mapping_90).pack(side="left",
                                                         padx=(10, 0))

        row3 = tk.Frame(self.canvas_panel, bg=CARD)
        row3.pack(fill="x", pady=(2, 0))
        self.mp_x_var = tk.StringVar()
        self.mp_y_var = tk.StringVar()
        tk.Label(row3, text="定位", bg=CARD, fg=MUTED, font=F(8),
                 width=4, anchor="w").pack(side="left")
        tk.Label(row3, text="X", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        tk.Entry(row3, textvariable=self.mp_x_var, bg=BG2, fg=FG, width=6,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", padx=(3, 8), ipady=2)
        tk.Label(row3, text="Y", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        tk.Entry(row3, textvariable=self.mp_y_var, bg=BG2, fg=FG, width=6,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", padx=(3, 8), ipady=2)
        tk.Label(row3, text="旋转", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        self.mp_rot_var = tk.StringVar(value="0°")
        self.mp_rot_combo = ttk.Combobox(
            row3, textvariable=self.mp_rot_var, width=4, state="readonly",
            values=("0°", "90°", "180°", "270°"))
        self.mp_rot_combo.pack(side="left", padx=(3, 0))
        self.mp_rot_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._apply_mapping_rotation())
        self.mp_x_var.trace_add("write", lambda *a: self._apply_mapping_xy())
        self.mp_y_var.trace_add("write", lambda *a: self._apply_mapping_xy())

        self.map_hint_var = tk.StringVar(value="")
        tk.Label(self.canvas_panel, textvariable=self.map_hint_var, bg=CARD,
                 fg=MUTED, font=F(8), anchor="w", justify="left",
                 wraplength=430).pack(fill="x", pady=(6, 0))
        result = self.bp.result_of_canvas(node.id)
        self.map_hint_var.set(
            f"接到 Result：{result.name}" if result else
            "注意：这个画布还没连到 Result，不会产生输出。")

        self._refresh_mapping_list()
        self._load_mapping_vars()
        self.after(10, self._render_board)

    def _build_result_panel(self, node):
        T = self.app.T
        CARD, FG, MUTED, BORDER = T("CARD"), T("FG"), T("MUTED"), T("BORDER")
        BG2, ACCENT, OK, DANGER = T("BG2"), T("ACCENT"), T("OK"), T("DANGER")
        F = self.app.F

        row = tk.Frame(self.canvas_panel, bg=CARD)
        row.pack(fill="x", pady=(4, 4))
        tk.Label(row, text="名称", bg=CARD, fg=MUTED, font=F(8),
                 width=4, anchor="w").pack(side="left")
        self.rs_name_var = tk.StringVar(value=node.name)
        tk.Entry(row, textvariable=self.rs_name_var, bg=BG2, fg=FG,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", fill="x", expand=True, ipady=2)

        def apply_name(*_a):
            node.name = self.rs_name_var.get() or node.name
            self.dirty = True
            self._update_summary()
            self._render()

        self.rs_name_var.trace_add("write", apply_name)

        tk.Label(self.canvas_panel, text="命名模板（结果图按这个命名）",
                 bg=CARD, fg=MUTED, font=F(8), anchor="w",
                 justify="left").pack(fill="x", pady=(4, 2))
        self.rs_tpl_var = tk.StringVar(value=node.template)
        tk.Entry(self.canvas_panel, textvariable=self.rs_tpl_var, bg=BG2,
                 fg=FG, insertbackground=FG, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, font=F(10)).pack(fill="x", ipady=4)
        self.rs_sample_var = tk.StringVar(value="")
        self.rs_sample_lbl = tk.Label(
            self.canvas_panel, textvariable=self.rs_sample_var, bg=CARD,
            fg=MUTED, font=F(8), anchor="w", justify="left", wraplength=430)
        self.rs_sample_lbl.pack(fill="x", pady=(3, 0))

        def update_sample():
            try:
                sample = render_template(self.rs_tpl_var.get(),
                                         template_sample_vars())
                self.rs_sample_var.set(f"示例（64×64 画布）：{sample}")
                self.rs_sample_lbl.configure(fg=MUTED)
            except TemplateError as exc:
                self.rs_sample_var.set(str(exc))
                self.rs_sample_lbl.configure(fg=DANGER)

        def apply_tpl(*_a):
            node.template = self.rs_tpl_var.get()
            self.dirty = True
            update_sample()

        self.rs_tpl_var.trace_add("write", apply_tpl)
        update_sample()

        tk.Label(self.canvas_panel,
                 text="变量：L / W（结果图像素）、Time、Text、Skin、"
                      "Canvas、Result、Index",
                 bg=CARD, fg=MUTED, font=F(8), anchor="w",
                 justify="left", wraplength=430).pack(fill="x", pady=(4, 8))

        canvas = self.bp.canvas_of_result(node.id)
        if canvas is None:
            tk.Label(self.canvas_panel,
                     text="这个 Result 还没接画布，流程里不会出现输出点。",
                     bg=CARD, fg=DANGER, font=F(8), anchor="w",
                     justify="left", wraplength=430).pack(fill="x")
        else:
            tk.Label(self.canvas_panel,
                     text=f"接入画布：{canvas.name}  ({canvas.width}×{canvas.height})",
                     bg=CARD, fg=OK, font=F(8), anchor="w",
                     justify="left", wraplength=430).pack(fill="x")

    def _build_rect_panel(self, node):
        T = self.app.T
        CARD, FG, MUTED, BORDER = T("CARD"), T("FG"), T("MUTED"), T("BORDER")
        BG2, ACCENT, DANGER = T("BG2"), T("ACCENT"), T("DANGER")
        F = self.app.F

        row = tk.Frame(self.canvas_panel, bg=CARD)
        row.pack(fill="x", pady=(4, 4))
        tk.Label(row, text="名称", bg=CARD, fg=MUTED, font=F(8),
                 width=4, anchor="w").pack(side="left")
        self.rn_name_var = tk.StringVar(value=node.name)
        tk.Entry(row, textvariable=self.rn_name_var, bg=BG2, fg=FG,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).pack(side="left", fill="x", expand=True, ipady=2)

        def apply_name(*_a):
            node.name = self.rn_name_var.get() or node.name
            self.dirty = True
            self._render()
            self._update_summary()

        self.rn_name_var.trace_add("write", apply_name)

        head = tk.Frame(self.canvas_panel, bg=CARD)
        head.pack(fill="x", pady=(2, 0))
        tk.Label(head, text="矩形（连到画布后，在画布素材里选）",
                 bg=CARD, fg=MUTED, font=F(8)).pack(side="left")
        self.rr_count_var = tk.StringVar()
        tk.Label(head, textvariable=self.rr_count_var, bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="right")

        self.rr_list = tk.Listbox(
            self.canvas_panel, bg=BG2, fg=FG, selectbackground=ACCENT,
            selectforeground=T("ACCENT_FG"), relief="flat", height=4,
            highlightthickness=1, highlightbackground=BORDER,
            activestyle="none", font=F(9), exportselection=False)
        self.rr_list.pack(fill="x", pady=(2, 2))
        self.rr_list.bind("<<ListboxSelect>>", self._on_rect_list_select)

        btns = tk.Frame(self.canvas_panel, bg=CARD)
        btns.pack(fill="x", pady=(0, 4))
        ttk.Button(btns, text="添加矩形",
                   command=lambda: self._add_rect(node)).pack(side="left")
        ttk.Button(btns, text="删除",
                   command=lambda: self._delete_rect(node)).pack(
                       side="left", padx=(4, 0))

        form = tk.Frame(self.canvas_panel, bg=CARD)
        form.pack(fill="x", pady=(2, 0))
        self.rr_name_var = tk.StringVar()
        self.rr_w_var = tk.StringVar()
        self.rr_h_var = tk.StringVar()
        self.rr_color_var = tk.StringVar(value="#6cb4ff")
        tk.Label(form, text="名称", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=0, column=0, sticky="w")
        tk.Entry(form, textvariable=self.rr_name_var, bg=BG2, fg=FG, width=8,
                 insertbackground=FG, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT,
                 font=F(9)).grid(row=0, column=1, sticky="w", ipady=2,
                                 padx=(2, 6))
        form.columnconfigure(1, weight=1)
        for i, (label, var) in enumerate((("W", self.rr_w_var),
                                          ("H", self.rr_h_var))):
            tk.Label(form, text=label, bg=CARD, fg=MUTED, font=F(8)).grid(
                row=0, column=2 + i * 2, sticky="w")
            tk.Entry(form, textvariable=var, bg=BG2, fg=FG, width=4,
                     insertbackground=FG, relief="flat", highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT,
                     font=F(9)).grid(row=0, column=3 + i * 2, sticky="w",
                                     ipady=2, padx=(2, 6))
        self.rr_swatch = tk.Label(form, bg="#6cb4ff", width=3, height=1,
                                  relief="solid", bd=1)
        self.rr_swatch.grid(row=0, column=6, sticky="w", padx=(0, 4))
        ttk.Button(form, text="颜色…", width=5,
                   command=self._pick_rect_color).grid(row=0, column=7,
                                                       sticky="w")

        for var in (self.rr_name_var, self.rr_w_var, self.rr_h_var):
            var.trace_add("write", lambda *a: self._apply_rect_fields())
        self.rr_color_var.trace_add("write",
                                    lambda *a: self._apply_rect_fields())

        tk.Label(self.canvas_panel,
                 text="提示：矩形可以当底色、边框、色块；映射顺序和选区共用。",
                 bg=CARD, fg=MUTED, font=F(8), anchor="w",
                 justify="left", wraplength=430).pack(fill="x", pady=(4, 0))

        self.rr_sel_rect_id = (node.rects[0].id if node.rects else None)
        self._refresh_rect_list(node)
        self._load_rect_fields(node)

    def _refresh_rect_list(self, node):
        if not hasattr(self, "rr_list"):
            return
        self.rr_list.delete(0, "end")
        for rect in node.rects:
            self.rr_list.insert(
                "end", f"{rect.name}  {rect.w}×{rect.h}  {rect.color}")
        for i, rect in enumerate(node.rects):
            if rect.id == self.rr_sel_rect_id:
                self.rr_list.selection_set(i)
        self.rr_count_var.set(f"{len(node.rects)} 个")

    def _load_rect_fields(self, node):
        rect = next((r for r in node.rects
                     if r.id == self.rr_sel_rect_id), None)
        self._loading = True
        try:
            if rect is None:
                self.rr_name_var.set("")
                self.rr_w_var.set("")
                self.rr_h_var.set("")
            else:
                self.rr_name_var.set(rect.name)
                self.rr_w_var.set(str(rect.w))
                self.rr_h_var.set(str(rect.h))
                self.rr_color_var.set(rect.color)
                self.rr_swatch.configure(bg=rect.color)
        finally:
            self._loading = False

    def _on_rect_list_select(self, _e=None):
        node = self.bp.nodes.get(self.selected_id)
        if node is None or node.kind != "rect":
            return
        cur = self.rr_list.curselection()
        if not cur:
            return
        idx = int(cur[0])
        if 0 <= idx < len(node.rects):
            self.rr_sel_rect_id = node.rects[idx].id
            self._load_rect_fields(node)

    def _add_rect(self, node):
        rect = self.bp.add_rect(
            node, 8, 8,
            self.rr_color_var.get() if hasattr(self, "rr_color_var")
            else "#6cb4ff")
        self.rr_sel_rect_id = rect.id
        self.dirty = True
        self._refresh_rect_list(node)
        self._load_rect_fields(node)
        self._build_canvas_panel()
        self._render()

    def _delete_rect(self, node):
        if self.rr_sel_rect_id is None:
            return
        self.bp.remove_rect(node, self.rr_sel_rect_id)
        self.rr_sel_rect_id = (node.rects[0].id if node.rects else None)
        self.dirty = True
        self._refresh_rect_list(node)
        self._load_rect_fields(node)
        self._build_canvas_panel()
        self._render()

    def _pick_rect_color(self):
        initial = self.rr_color_var.get() or "#6cb4ff"
        result = colorchooser.askcolor(color=initial, title="选择矩形颜色",
                                       parent=self)
        if result and result[1]:
            self.rr_color_var.set(result[1])
            self.rr_swatch.configure(bg=result[1])

    def _apply_rect_fields(self):
        if self._loading:
            return
        node = self.bp.nodes.get(self.selected_id)
        if node is None or node.kind != "rect":
            return
        rect = next((r for r in node.rects
                     if r.id == self.rr_sel_rect_id), None)
        if rect is None:
            return
        name = self.rr_name_var.get().strip()
        if name:
            rect.name = name
        try:
            rect.w = max(1, min(1024, int(float(self.rr_w_var.get()))))
            rect.h = max(1, min(1024, int(float(self.rr_h_var.get()))))
        except ValueError:
            pass
        color = self.rr_color_var.get()
        if re.fullmatch(r"#[0-9a-fA-F]{6}", color or ""):
            rect.color = color
        self.dirty = True
        self._refresh_rect_list(node)
        self._render_board()
        self._render()

    def _apply_canvas_name(self, node):
        if self._loading:
            return
        node.name = self.cv_name_var.get() or node.name
        self.dirty = True
        self._render()
        self._update_summary()

    def _apply_canvas_size(self, node):
        if self._loading:
            return
        try:
            w = max(1, min(1024, int(float(self.cv_w_var.get()))))
            h = max(1, min(1024, int(float(self.cv_h_var.get()))))
        except ValueError:
            return
        node.width, node.height = w, h
        self.dirty = True
        self._render_board()
        self._render()
        self._update_summary()

    # ---------- 选区列表 / 映射列表 ----------
    def _material_label(self, mp):
        if mp.kind == "rect":
            node, rect = self.bp.find_rect(mp.ref_id)
            if rect is None:
                return "（矩形已删）"
            return f"矩形 {node.name}/{rect.name}" if node else f"矩形 {rect.name}"
        sel = self.bp.selection(mp.ref_id)
        return f"选区 {sel.name}" if sel is not None else "（选区已删）"

    def _refresh_mapping_list(self):
        if not hasattr(self, "map_list"):
            return
        canvas = self._current_canvas()
        if canvas is None:
            return
        self.map_list.delete(0, "end")
        for i, mp in enumerate(canvas.mappings, 1):
            rot = f"  {mp.rotation}°" if getattr(mp, "rotation", 0) else ""
            self.map_list.insert(
                "end",
                f"{i}. {self._material_label(mp)}   @ {mp.x},{mp.y}{rot}")
        for i, mp in enumerate(canvas.mappings):
            if mp.id == self.sel_mapping_id:
                self.map_list.selection_set(i)
        self.map_count_var.set(f"{len(canvas.mappings)} 条")

    def _load_mapping_vars(self):
        mp = self._current_mapping()
        self._loading = True
        try:
            self.mp_x_var.set(str(mp.x) if mp else "")
            self.mp_y_var.set(str(mp.y) if mp else "")
            if hasattr(self, "mp_rot_var"):
                self.mp_rot_var.set(f"{mp.rotation}°" if mp else "0°")
        finally:
            self._loading = False

    def _on_map_list_select(self, _e=None):
        if not hasattr(self, "map_list"):
            return
        cur = self.map_list.curselection()
        if not cur:
            return
        canvas = self._current_canvas()
        if canvas is None:
            return
        idx = int(cur[0])
        if 0 <= idx < len(canvas.mappings):
            self.sel_mapping_id = canvas.mappings[idx].id
            self._load_mapping_vars()
            self._render_board()

    def _map_list_press(self, event):
        if not hasattr(self, "map_list"):
            return
        self._map_drag = {"last": self.map_list.nearest(event.y)}

    def _map_list_motion(self, event):
        canvas = self._current_canvas()
        if canvas is None or not self._map_drag:
            return
        idx = self.map_list.nearest(event.y)
        if idx == self._map_drag.get("last"):
            return
        cur = self.map_list.curselection()
        if not cur:
            return
        cur_idx = int(cur[0])
        if not (0 <= cur_idx < len(canvas.mappings)):
            return
        mp = canvas.mappings[cur_idx]
        if self.bp.move_mapping(canvas, mp.id, idx - cur_idx):
            self._map_drag["last"] = idx
            self.dirty = True
            self._refresh_mapping_list()
            self.map_list.selection_clear(0, "end")
            self.map_list.selection_set(idx)
            self.sel_mapping_id = mp.id
            self._render_board()
            self._render()

    def _map_list_release(self, _event=None):
        self._map_drag = None

    def _add_mapping(self):
        canvas = self._current_canvas()
        if canvas is None:
            return
        choices = getattr(self, "_material_choices", [])
        if not choices:
            self.app.toast("这个画布还没有素材：连上输入图，或者接一个矩形节点")
            return
        idx = self.material_combo.current()
        if not (0 <= idx < len(choices)):
            idx = 0
        kind, ref_id = choices[idx][0], choices[idx][1]
        mp = self.bp.add_mapping(canvas, kind, ref_id, 0, 0)
        self.sel_mapping_id = mp.id
        self.dirty = True
        self._refresh_mapping_list()
        self._load_mapping_vars()
        self._render_board()
        self._render()

    def _delete_mapping(self):
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        self.bp.remove_mapping(canvas, mp.id)
        self.sel_mapping_id = None
        self.dirty = True
        self._refresh_mapping_list()
        self._load_mapping_vars()
        self._render_board()
        self._render()

    def _move_mapping(self, delta):
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        if self.bp.move_mapping(canvas, mp.id, delta):
            self.dirty = True
            self._refresh_mapping_list()
            self._render_board()
            self._render()

    def _apply_mapping_xy(self):
        if self._loading:
            return
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        try:
            x = int(float(self.mp_x_var.get()))
            y = int(float(self.mp_y_var.get()))
        except ValueError:
            return
        mp.x = max(0, min(canvas.width, x))
        mp.y = max(0, min(canvas.height, y))
        self.dirty = True
        self._refresh_mapping_list()
        self._render_board()

    def _rotate_mapping_90(self):
        mp = self._current_mapping()
        if mp is None or not hasattr(self, "mp_rot_var"):
            return
        self.mp_rot_var.set(f"{(mp.rotation + 90) % 360}°")
        self._apply_mapping_rotation()

    def _apply_mapping_rotation(self):
        if self._loading or not hasattr(self, "mp_rot_var"):
            return
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        try:
            rot = int(self.mp_rot_var.get().rstrip("°")) % 360
        except ValueError:
            return
        mp.rotation = rot if rot in (90, 180, 270) else 0
        w, h = self.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
        mp.x = max(0, min(max(0, canvas.width - w), mp.x))
        mp.y = max(0, min(max(0, canvas.height - h), mp.y))
        self.dirty = True
        self._render_board()
        self._refresh_mapping_list()
        self._load_mapping_vars()
        self._render()

    # ---------- 画布预览交互 ----------
    def _render_board(self):
        if not hasattr(self, "board_canvas"):
            return
        c = self.board_canvas
        if not c.winfo_exists():
            return
        c.delete("all")
        T = self.app.T
        canvas = self._current_canvas()
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 20 or ch < 20:
            return
        if canvas is None:
            self._board_view = None
            c.create_text(cw / 2, ch / 2, text="选中画布后在这里排版",
                          fill=T("MUTED"), font=self.app.F(9))
            return

        s = min((cw - 16) / max(1, canvas.width),
                (ch - 16) / max(1, canvas.height))
        s = max(0.05, s)
        dw = max(1, int(canvas.width * s))
        dh = max(1, int(canvas.height * s))
        ox = (cw - dw) // 2
        oy = (ch - dh) // 2
        self._board_view = (ox, oy, s)

        c1, c2 = CHECKER_PRESETS[self.app.settings.get(
            "checker", self.app.settings.get("theme", "dark"))]
        checker = make_checker(dw, dh, c1, c2, cell=max(4, int(6 * s)))
        board = render_result_image(self.bp, canvas, self.ref_image, 1.0)
        board = board.resize((dw, dh), Image.NEAREST)
        checker = checker.convert("RGBA")
        checker.alpha_composite(board, (0, 0))
        photo = ImageTk.PhotoImage(checker)
        self._board_photo = photo
        c.create_image(ox, oy, image=photo, anchor="nw")
        c.create_rectangle(ox, oy, ox + dw, oy + dh, outline=T("BORDER"))
        self._draw_pixel_grid(c, ox, oy, s, canvas.width, canvas.height, T)

        for i, mp in enumerate(canvas.mappings, 1):
            w, h = self.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
            if w <= 0 or h <= 0:
                continue
            x1 = ox + mp.x * s
            y1 = oy + mp.y * s
            x2 = x1 + w * s
            y2 = y1 + h * s
            selected = mp.id == self.sel_mapping_id
            color = T("ACCENT") if selected else T("PORT_TXT")
            c.create_rectangle(x1, y1, x2, y2, outline=color,
                               width=2 if selected else 1, dash=None)
            c.create_text(x1 + 2, y1 + 2, text=str(i), fill=color,
                          anchor="nw", font=self.app.F(8, "bold"))

    def _board_press(self, event):
        canvas = self._current_canvas()
        if canvas is None or self._board_view is None:
            return
        ox, oy, s = self._board_view
        bx = (event.x - ox) / s
        by = (event.y - oy) / s
        hit = None
        for mp in reversed(canvas.mappings):
            w, h = self.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
            if w <= 0 or h <= 0:
                continue
            if mp.x <= bx <= mp.x + w and mp.y <= by <= mp.y + h:
                hit = mp
                break
        if hit is None:
            return
        self.sel_mapping_id = hit.id
        self._load_mapping_vars()
        self._refresh_mapping_list()
        self._drag = {"mode": "mapping", "mp": hit,
                      "bx": bx, "by": by, "orig": (hit.x, hit.y),
                      "canvas": canvas}
        self._render_board()

    def _board_motion(self, event):
        drag = self._drag
        if drag is None or drag.get("mode") != "mapping":
            return
        canvas = drag["canvas"]
        ox, oy, s = self._board_view
        bx = (event.x - ox) / s
        by = (event.y - oy) / s
        mp = drag["mp"]
        w, h = self.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
        dx = int(round(bx - drag["bx"]))
        dy = int(round(by - drag["by"]))
        x0, y0 = drag["orig"]
        max_x = max(0, canvas.width - w)
        max_y = max(0, canvas.height - h)
        mp.x = max(0, min(max_x, x0 + dx))
        mp.y = max(0, min(max_y, y0 + dy))
        self.dirty = True
        self._load_mapping_vars()
        self._render_board()

    def _board_release(self, _event=None):
        if self._drag and self._drag.get("mode") == "mapping":
            self._refresh_mapping_list()
            self._render()
        self._drag = None

    # ================= 左侧节点图 =================
    def w2s(self, x, y):
        return ((x - self.pan_x) * self.zoom,
                (y - self.pan_y) * self.zoom)

    def s2w(self, x, y):
        return (x / self.zoom + self.pan_x,
                y / self.zoom + self.pan_y)

    def _node_size(self, node):
        if node.kind == "input":
            return 222, 122
        if node.kind == "canvas":
            return 252, 152
        if node.kind == "rect":
            return 232, 150
        return 236, 136

    def _port_world(self, node, side):
        w, h = self._node_size(node)
        if node.kind == "input":
            return node.x + w, node.y + h / 2
        if node.kind == "result":
            return node.x, node.y + h / 2
        if node.kind == "rect":
            return node.x + w, node.y + h / 2
        return (node.x if side == "in" else node.x + w), node.y + h / 2

    def _node_at(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        for nid in reversed(list(self.bp.nodes.keys())):
            node = self.bp.nodes[nid]
            w, h = self._node_size(node)
            if node.x <= wx <= node.x + w and node.y <= wy <= node.y + h:
                return nid
        return None

    def _port_at(self, sx, sy):
        wx, wy = self.s2w(sx, sy)
        radius = max(11.0, 10 / max(self.zoom, 0.3))
        for nid, node in self.bp.nodes.items():
            if node.kind == "result":
                sides = ("in",)
            elif node.kind in ("input", "rect"):
                sides = ("out",)
            else:
                sides = ("in", "out")
            for side in sides:
                px, py = self._port_world(node, side)
                if (wx - px) ** 2 + (wy - py) ** 2 <= radius ** 2:
                    return side, nid
        return None

    def _render(self):
        try:
            self._render_inner()
        except Exception:
            traceback.print_exc()

    def _render_inner(self):
        c = self.canvas
        c.delete("all")
        self._draw_grid()
        for a, b in self.bp.edges:
            self._draw_edge(a, b)
        if self.drag_mode == "link" and self.link_from is not None:
            node = self.bp.nodes.get(self.link_from)
            if node is not None:
                px, py = self._port_world(node, "out")
                x1, y1 = self.w2s(px, py)
                c.create_line(x1, y1, *self.link_cursor, arrow="last",
                              arrowshape=(9, 11, 4), width=2,
                              fill=self.app.T("ACCENT"), dash=(5, 4))
        for node in self.bp.nodes.values():
            self._draw_node(node)
        if self._box_rect is not None:
            x0, y0, x1, y1 = self._box_rect
            c.create_rectangle(min(x0, x1), min(y0, y1),
                               max(x0, x1), max(y0, y1),
                               outline=self.app.T("ACCENT"), dash=(5, 3),
                               width=1.5)

    def _draw_grid(self):
        c = self.canvas
        step = 32 * self.zoom
        if step < 14:
            return
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 4 or h < 4:
            return
        color = self.app.T("GRID")
        ox = (-self.pan_x * self.zoom) % step
        oy = (-self.pan_y * self.zoom) % step
        x = ox
        while x < w:
            c.create_line(x, 0, x, h, fill=color)
            x += step
        y = oy
        while y < h:
            c.create_line(0, y, w, y, fill=color)
            y += step

    def _edge_color(self, a):
        node = self.bp.nodes.get(a)
        if node is None:
            return self.app.T("BORDER")
        if node.kind == "input":
            return self.app.T("PORT_IMG")
        if node.kind == "rect":
            return self.app.T("PORT_TXT")
        return self.app.T("OK")

    def _draw_edge(self, a, b):
        na = self.bp.nodes.get(a)
        nb = self.bp.nodes.get(b)
        if na is None or nb is None:
            return
        x1, y1 = self._port_world(na, "out")
        x2, y2 = self._port_world(nb, "in")
        sx1, sy1 = self.w2s(x1, y1)
        sx2, sy2 = self.w2s(x2, y2)
        color = self._edge_color(a)
        self.canvas.create_line(sx1, sy1, sx2, sy2, arrow="last",
                                arrowshape=(10, 12, 4),
                                width=max(1.6, 2.0 * self.zoom), fill=color)

    def _draw_node(self, node):
        c = self.canvas
        T = self.app.T
        fam = self.app._font_family
        z = self.zoom
        x, y = self.w2s(node.x, node.y)
        w, h = self._node_size(node)
        w *= z
        h *= z
        selected = node.id in self.selected_ids
        primary = (node.id == self.selected_id)
        color = BP_NODE_COLORS.get(node.kind, T("ACCENT"))

        connected = True
        if node.kind == "canvas":
            connected = bool([
                1 for a, b in self.bp.edges
                if a == node.id and self.bp.nodes.get(b) is not None
                and self.bp.nodes[b].kind == "result"])
        elif node.kind == "result":
            connected = self.bp.canvas_of_result(node.id) is not None
        elif node.kind == "rect":
            connected = any(a == node.id and self.bp.nodes.get(b) is not None
                            and self.bp.nodes[b].kind == "canvas"
                            for a, b in self.bp.edges)
        border = (T("ACCENT") if selected
                  else (T("BORDER") if connected else T("MUTED")))

        round_rect(c, x + 3, y + 4, x + w + 3, y + h + 4, 12 * z,
                   fill=T("SHADOW"), outline="")
        round_rect(c, x, y, x + w, y + h, 12 * z, fill=T("CARD"),
                   outline=border,
                   width=(2.5 if primary else (2.0 if selected else 1.2)))
        c.create_rectangle(x + 1, y + 10 * z, x + 1 + 4 * z,
                           y + h - 10 * z, fill=color, outline="")

        title = {"input": "输入", "canvas": "画布", "result": "Result",
                 "rect": "矩形"}[node.kind]
        c.create_text(x + 16 * z, y + 18 * z, text=title, fill=color,
                      anchor="w", font=(fam, max(1, int(10 * z)), "bold"))
        c.create_text(
            x + 16 * z, y + 40 * z,
            text=self._fit_text(node.name or "未命名", (w / z) - 32 if z else 200),
            fill=T("FG"), anchor="w",
            font=(fam, max(1, int(9 * z)), "bold"))
        c.create_line(x + 12 * z, y + 52 * z, x + w - 12 * z, y + 52 * z,
                      fill=T("BORDER"))

        line_size = max(1, int(8 * z))
        body_y = y + 64 * z
        lines = []
        if node.kind == "input":
            size = (f"{self.ref_image.width}×{self.ref_image.height}"
                    if self.ref_image is not None else "未导入示例图")
            lines.append(f"示例：{size}")
            lines.append(f"选区：{len(self.bp.selections)} 个")
        elif node.kind == "canvas":
            lines.append(f"尺寸：{node.width}×{node.height}")
            lines.append(f"映射：{len(node.mappings)} 条")
            res = self.bp.result_of_canvas(node.id)
            lines.append(f"Result：{res.name if res else '未接'}")
        elif node.kind == "rect":
            lines.append(f"矩形：{len(node.rects)} 个")
            if node.rects:
                r0 = node.rects[0]
                lines.append(f"例：{r0.w}×{r0.h} {r0.color}")
        else:
            lines.append(self._fit_text(node.template or "(空模板)",
                                        (w / z) - 32 if z else 200))
            canvas = self.bp.canvas_of_result(node.id)
            lines.append(f"画布：{canvas.name if canvas else '未接'}")

        for i, line in enumerate(lines):
            c.create_text(x + 16 * z, body_y + i * 20 * z, text=line,
                          fill=T("MUTED"), anchor="nw",
                          font=(fam, line_size))
        if node.kind == "rect" and node.rects:
            for i, rect in enumerate(node.rects[:4]):
                bx = x + 16 * z + i * 18 * z
                by = y + h - 24 * z
                c.create_rectangle(bx, by, bx + 14 * z, by + 14 * z,
                                   fill=rect.color, outline=T("BORDER"))
        if not connected:
            c.create_text(x + 16 * z, y + h - 16 * z, text="未接通",
                          fill=T("DANGER"), anchor="w",
                          font=(fam, line_size))

        r = max(3.0, 6.5 * z)
        if node.kind != "result":
            px, py = self._port_world(node, "out")
            sx, sy = self.w2s(px, py)
            col = (T("PORT_IMG") if node.kind == "input"
                   else (T("PORT_TXT") if node.kind == "rect" else T("OK")))
            c.create_oval(sx - r, sy - r, sx + r, sy + r,
                          fill=T("BG2"), outline=col, width=2)
        if node.kind not in ("input", "rect"):
            px, py = self._port_world(node, "in")
            sx, sy = self.w2s(px, py)
            col = T("PORT_IMG") if node.kind == "canvas" else T("OK")
            c.create_oval(sx - r, sy - r, sx + r, sy + r,
                          fill=T("BG2"), outline=col, width=2)

    # ---------- 节点图交互 ----------
    def _select_node(self, nid, additive=False):
        if additive and nid is not None:
            if nid in self.selected_ids:
                self.selected_ids.discard(nid)
            else:
                self.selected_ids.add(nid)
        elif nid is not None:
            if nid not in self.selected_ids:
                self.selected_ids = {nid}
        self.selected_id = (nid if nid in self.selected_ids
                            else next(iter(self.selected_ids), None))
        self.sel_mapping_id = None
        self._build_canvas_panel()
        self._render()

    def _on_press(self, event):
        port = self._port_at(event.x, event.y)
        if port is not None and port[0] == "out":
            self.drag_mode = "link"
            self.link_from = port[1]
            self.link_cursor = (event.x, event.y)
            self._render()
            return
        nid = self._node_at(event.x, event.y)
        if nid is not None:
            ctrl = bool(getattr(event, "state", 0) & 0x0004)
            self._select_node(nid, additive=ctrl)
            if self.selected_ids:
                self.drag_mode = "node"
                self.drag_node_id = nid
                self._drag_start_world = self.s2w(event.x, event.y)
                self._drag_origins = {
                    i: (self.bp.nodes[i].x, self.bp.nodes[i].y)
                    for i in self.selected_ids if i in self.bp.nodes}
            self._render()
            return
        self._box_additive = bool(getattr(event, "state", 0) & 0x0004)
        if not self._box_additive:
            self.selected_ids = set()
            self.selected_id = None
            self.sel_mapping_id = None
            self._build_canvas_panel()
        self.drag_mode = "box"
        self._box_rect = (event.x, event.y, event.x, event.y)
        self._render()

    def _on_motion(self, event):
        if self.drag_mode == "node":
            wx, wy = self.s2w(event.x, event.y)
            dx = wx - self._drag_start_world[0]
            dy = wy - self._drag_start_world[1]
            for nid, (x0, y0) in self._drag_origins.items():
                node = self.bp.nodes.get(nid)
                if node is None:
                    continue
                node.x = round((x0 + dx) / 4) * 4
                node.y = round((y0 + dy) / 4) * 4
            self.dirty = True
            self._render()
        elif self.drag_mode == "box":
            if self._box_rect is not None:
                self._box_rect = (self._box_rect[0], self._box_rect[1],
                                  event.x, event.y)
            self._render()
        elif self.drag_mode == "pan":
            self.pan_x = self.pan_start[0] - (event.x - self.drag_start[0]) / self.zoom
            self.pan_y = self.pan_start[1] - (event.y - self.drag_start[1]) / self.zoom
            self._render()
        elif self.drag_mode == "link":
            self.link_cursor = (event.x, event.y)
            self._render()

    def _finish_box(self):
        if self._box_rect is None:
            return
        x0, y0, x1, y1 = self._box_rect
        if abs(x1 - x0) < 3 and abs(y1 - y0) < 3:
            return
        wx0, wy0 = self.s2w(min(x0, x1), min(y0, y1))
        wx1, wy1 = self.s2w(max(x0, x1), max(y0, y1))
        hit = set()
        for nid, node in self.bp.nodes.items():
            w, h = self._node_size(node)
            if (node.x < wx1 and node.x + w > wx0
                    and node.y < wy1 and node.y + h > wy0):
                hit.add(nid)
        if self._box_additive:
            self.selected_ids |= hit
        else:
            self.selected_ids = hit
        if self.selected_id not in self.selected_ids:
            self.selected_id = next(iter(hit), None)
        self.sel_mapping_id = None
        self._build_canvas_panel()

    def _on_release(self, event):
        if self.drag_mode == "link" and self.link_from is not None:
            port = self._port_at(event.x, event.y)
            if port is not None and port[0] == "in":
                target = port[1]
                src = self.bp.nodes.get(self.link_from)
                dst = self.bp.nodes.get(target)
                if src is not None and dst is not None:
                    ok = ((src.kind in ("input", "rect") and dst.kind == "canvas")
                          or (src.kind == "canvas" and dst.kind == "result"))
                    if ok and self.bp.connect(self.link_from, target):
                        self.dirty = True
                        self._build_canvas_panel()
                        self._update_summary()
                    else:
                        self.app.toast("连不上：请输入/矩形 → 画布 → Result")
        elif self.drag_mode == "box":
            self._finish_box()
        self.drag_mode = None
        self.link_from = None
        self._drag_origins = {}
        self._box_rect = None
        self._render()

    # ---------- 中键平移 ----------
    def _middle_press(self, event):
        self.drag_mode = "pan"
        self.drag_start = (event.x, event.y)
        self.pan_start = (self.pan_x, self.pan_y)
        self.canvas.configure(cursor="fleur")

    def _middle_motion(self, event):
        if self.drag_mode != "pan":
            return
        self.pan_x = self.pan_start[0] - (event.x - self.drag_start[0]) / self.zoom
        self.pan_y = self.pan_start[1] - (event.y - self.drag_start[1]) / self.zoom
        self._render()

    def _middle_release(self, _event):
        if self.drag_mode == "pan":
            self.drag_mode = None
        self.canvas.configure(cursor="")

    def _on_wheel(self, event, up=None, down=None):
        if up is None and down is None:
            delta = getattr(event, "delta", 0)
            if delta > 0:
                up = True
            elif delta < 0:
                down = True
            else:
                return
        old = self.zoom
        factor = 1.12 if up else 1 / 1.12
        new = max(ZOOM_MIN, min(ZOOM_MAX, old * factor))
        wx, wy = self.s2w(event.x, event.y)
        self.zoom = new
        self.pan_x = wx - event.x / new
        self.pan_y = wy - event.y / new
        self._render()

    def _on_right_click(self, event):
        nid = self._node_at(event.x, event.y)
        menu = tk.Menu(self, tearoff=0)
        if nid is not None:
            if nid not in self.selected_ids:
                self.selected_ids = {nid}
                self.selected_id = nid
                self.sel_mapping_id = None
                self._build_canvas_panel()
            node = self.bp.nodes[nid]
            if node.kind == "input":
                menu.add_command(label="导入示例图…", command=self._import_ref)
            else:
                if len(self.selected_ids) > 1:
                    menu.add_command(
                        label=f"删除选中的 {len(self.selected_ids)} 个节点",
                        command=self._delete_selected)
                else:
                    menu.add_command(label="删除节点",
                                     command=lambda: self._delete_node(nid))
        else:
            wx, wy = self.s2w(event.x, event.y)
            menu.add_command(label="添加：画布",
                             command=lambda: self._add_node("canvas", wx, wy))
            menu.add_command(label="添加：Result",
                             command=lambda: self._add_node("result", wx, wy))
            menu.add_command(label="添加：矩形",
                             command=lambda: self._add_node("rect", wx, wy))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _delete_selected(self):
        ids = set(self.selected_ids)
        if not ids and self.selected_id is not None:
            ids = {self.selected_id}
        removed = False
        for nid in list(ids):
            node = self.bp.nodes.get(nid)
            if node is None or node.kind == "input":
                continue
            self.bp.remove_node(nid)
            self.selected_ids.discard(nid)
            removed = True
        if self.selected_id not in self.selected_ids:
            self.selected_id = next(iter(self.selected_ids), None)
        if removed:
            self.dirty = True
            self._build_canvas_panel()
            self._update_summary()
            self._render()

    def _add_node(self, kind, x, y):
        if kind == "canvas":
            node = self.bp.add_canvas(x, y)
            inp = self.bp.input_node()
            if inp is not None:
                self.bp.connect(inp.id, node.id)
        elif kind == "rect":
            node = self.bp.add_rect_node(x, y)
        else:
            node = self.bp.add_result(x, y)
        self.selected_id = node.id
        self.selected_ids = {node.id}
        self.dirty = True
        self._build_canvas_panel()
        self._update_summary()
        self._render()

    def _delete_node(self, nid):
        node = self.bp.nodes.get(nid)
        if node is None:
            return
        if node.kind == "input":
            self.app.toast("输入节点不能删除")
            return
        self.bp.remove_node(nid)
        self.selected_ids.discard(nid)
        if self.selected_id == nid:
            self.selected_id = next(iter(self.selected_ids), None)
        self.dirty = True
        self._build_canvas_panel()
        self._update_summary()
        self._render()

    def _fit_view(self):
        nodes = list(self.bp.nodes.values())
        if not nodes:
            self.zoom = 1.0
            self.pan_x = self.pan_y = 0
            self._render()
            return
        min_x = min(n.x for n in nodes)
        min_y = min(n.y for n in nodes)
        max_x = max(n.x + self._node_size(n)[0] for n in nodes)
        max_y = max(n.y + self._node_size(n)[1] for n in nodes)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 120 or ch < 120:
            self.after(60, self._fit_view)
            return
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)
        self.zoom = max(ZOOM_MIN, min(1.2, min(cw / span_x, ch / span_y) * 0.9))
        self.pan_x = min_x - (cw / self.zoom - span_x) / 2
        self.pan_y = min_y - (ch / self.zoom - span_y) / 2
        self._render()

    # ---------- 蓝图管理 ----------
    def _on_pick_blueprint(self, _e=None):
        name = self.bp_var.get()
        if name == self.bp.name:
            return
        if not self._maybe_save():
            self.bp_var.set(self.bp.name)
            return
        if not self._switch_to(name):
            self.bp_var.set(self.bp.name)

    def _switch_to(self, name):
        bp = BP_REPO.load(name)
        if bp is None:
            messagebox.showerror("读取失败", f"打不开蓝图：{name}", parent=self)
            return False
        self.bp = bp
        self.bp_name = name
        self.bp_var.set(name)
        self.ref_image = self._load_ref_image()
        self.selected_id = None
        self.sel_selection_id = None
        self.sel_mapping_id = None
        self.dirty = False
        self._build_input_panel()
        self._build_canvas_panel()
        self._update_summary()
        self._render()
        self._fit_view()
        return True

    def _maybe_save(self):
        if not self.dirty:
            return True
        choice = messagebox.askyesnocancel(
            "还没保存", "蓝图有改动，要保存吗？", parent=self)
        if choice is None:
            return False
        if choice:
            return self._save()
        self.dirty = False
        return True

    def _save(self):
        self.bp.prune_edges()
        self.bp.name = self.bp_name
        try:
            BP_REPO.save(self.bp)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
            return False
        self.dirty = False
        self._refresh_bp_list()
        self._update_summary()
        self.app.toast(f"已保存蓝图：{self.bp.name}")
        return True

    def _new_blueprint(self):
        if not self._maybe_save():
            return
        name = simpledialog.askstring("新建蓝图", "蓝图名称：", parent=self)
        if not name:
            return
        name = sanitize_name(name)
        if not name:
            return
        if BP_REPO.path_of(name).exists():
            messagebox.showwarning("已存在", f"蓝图 {name} 已经存在。",
                                   parent=self)
            return
        bp = make_default_blueprint(name)
        try:
            BP_REPO.save(bp)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
            return
        self._refresh_bp_list()
        self._switch_to(name)

    def _save_as(self):
        name = simpledialog.askstring("另存为", "新的蓝图名称：", parent=self)
        if not name:
            return
        name = sanitize_name(name)
        if not name:
            return
        if BP_REPO.path_of(name).exists():
            messagebox.showwarning("已存在", f"蓝图 {name} 已经存在。",
                                   parent=self)
            return
        old_ref = self.bp.ref_image
        if self.ref_image is not None:
            target = BP_REPO.ref_path(name)
            try:
                self.ref_image.save(target)
                self.bp.ref_image = target.name
            except Exception as exc:
                messagebox.showerror("保存失败", f"复制示例图失败：\n{exc}",
                                     parent=self)
                return
            if old_ref and old_ref != self.bp.ref_image:
                try:
                    (BP_REPO.folder / old_ref).unlink()
                except OSError:
                    pass
        self.bp_name = name
        self.bp.name = name
        self.bp_var.set(name)
        self._save()
        self._refresh_bp_list()

    def _open_external(self):
        path = filedialog.askopenfilename(
            title="打开蓝图文件",
            filetypes=[("蓝图 JSON", "*.json"), ("所有文件", "*.*")],
            parent=self)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            bp = Blueprint.from_dict(data)
        except Exception as exc:
            messagebox.showerror(
                "打开失败", f"这个文件不是有效的蓝图：\n{exc}", parent=self)
            return
        name = ask_import_name(self, BLUEPRINTS_DIR,
                               bp.name or Path(path).stem)
        if not name:
            return

        # 示例图：优先从 JSON 旁边的同名文件带过来
        ref_name = bp.ref_image
        new_ref = ""
        if ref_name:
            candidate = Path(path).parent / ref_name
            if candidate.exists():
                try:
                    image = load_rgba(candidate)
                    target = BP_REPO.ref_path(name)
                    image.save(target)
                    new_ref = target.name
                    bp.image_w, bp.image_h = image.size
                except Exception:
                    new_ref = ""
            elif (BLUEPRINTS_DIR / ref_name).exists():
                new_ref = ref_name
        bp.ref_image = new_ref
        bp.name = name
        try:
            BP_REPO.save(bp)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self)
            return
        self._refresh_bp_list()
        self._switch_to(name)
        self.app.toast(f"已导入蓝图：{name}")

    def _delete_blueprint(self):
        name = self.bp_name
        if not messagebox.askyesno(
                "删除蓝图",
                f"确定删除蓝图“{name}”？\n（引用它的流程节点会失效）",
                parent=self):
            return
        BP_REPO.delete(name)
        self.dirty = False
        self._refresh_bp_list()
        names = BP_REPO.list()
        if names:
            self._switch_to(names[0])
        else:
            bp = make_default_blueprint("基础")
            BP_REPO.save(bp)
            self._refresh_bp_list()
            self._switch_to("基础")

    # ---------- 全屏编辑 ----------
    def _draw_pixel_grid(self, c, ox, oy, scale, iw, ih, T):
        if not self.app.settings.get("grid", True):
            return
        step = 1
        while (iw // step + ih // step) > 32:
            step *= 2
        for gx in range(step, iw, step):
            x = ox + gx * scale
            c.create_line(x, oy, x, oy + ih * scale,
                          fill=T("GRID"), dash=(1, 3))
        for gy in range(step, ih, step):
            y = oy + gy * scale
            c.create_line(ox, y, ox + iw * scale, y,
                          fill=T("GRID"), dash=(1, 3))

    def _toggle_grid(self):
        self.app.settings["grid"] = bool(self.grid_var.get())
        self.app._save_settings()
        self._render_input_preview()
        self._render_board()
        for win in (getattr(self, "_fs_input", None),
                    getattr(self, "_fs_board", None)):
            if win is not None and win.winfo_exists():
                win.render()

    def open_input_fullscreen(self):
        win = getattr(self, "_fs_input", None)
        if win is not None and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        self._fs_input = FullscreenPreview(self, "input")

    def open_board_fullscreen(self):
        if self._current_canvas() is None:
            self.app.toast("先选中一个画布，再放大编辑")
            return
        win = getattr(self, "_fs_board", None)
        if win is not None and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        self._fs_board = FullscreenPreview(self, "board")

    def _on_close(self):
        if not self._maybe_save():
            return
        self.destroy()




# ====================================================================
# 全屏编辑（示例图选区 / 画布映射）
# ====================================================================

class FullscreenPreview(tk.Toplevel):
    """把示例图或画布放大到整个窗口来编辑。"""

    def __init__(self, editor, mode):
        super().__init__(editor)
        self.editor = editor
        self.app = editor.app
        self.mode = mode          # input / board
        self.view = None
        self.drag = None
        self._photo = None
        self._loading = False
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._pan_start = None
        self._pan_orig = (0.0, 0.0)
        self.sel_id = editor.sel_selection_id
        self.map_id = editor.sel_mapping_id

        T = self.app.T
        self.title("选区编辑 — 放大" if mode == "input" else "画布编辑 — 放大")
        try:
            self.state("zoomed")
        except Exception:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw - 40}x{sh - 80}+10+10")
        self.configure(bg=T("BG"))
        self.transient(editor)
        self.bind("<Escape>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

        body = tk.Frame(self, bg=T("BG"))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, bg=T("BG2"), highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.panel = tk.Frame(body, bg=T("CARD"), width=340,
                              highlightthickness=1,
                              highlightbackground=T("BORDER"))
        self.panel.pack(side="right", fill="y", padx=(10, 0))
        self.panel.pack_propagate(False)

        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-2>", self._middle_press)
        self.canvas.bind("<B2-Motion>", self._middle_motion)
        self.canvas.bind("<ButtonRelease-2>", self._middle_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._on_wheel(e, up=True))
        self.canvas.bind("<Button-5>", lambda e: self._on_wheel(e, down=True))
        self.canvas.bind("<Configure>", lambda e: self.render())

        if mode == "input":
            self._build_input_panel()
        else:
            self._build_board_panel()
        self.after(60, self.render)

    # ---------- 面板 ----------
    def _entry(self, parent, var, width=6):
        T = self.app.T
        return tk.Entry(parent, textvariable=var, bg=T("BG2"), fg=T("FG"),
                        insertbackground=T("FG"), relief="flat", width=width,
                        highlightthickness=1,
                        highlightbackground=T("BORDER"),
                        highlightcolor=T("ACCENT"), font=self.app.F(9))

    def _build_input_panel(self):
        T = self.app.T
        CARD, MUTED, FG = T("CARD"), T("MUTED"), T("FG")
        F = self.app.F

        tk.Label(self.panel, text="选区", bg=CARD, fg=T("ACCENT"),
                 font=F(11, "bold"), anchor="w").pack(fill="x", padx=16,
                                                      pady=(14, 6))
        self.listbox = tk.Listbox(
            self.panel, bg=T("BG2"), fg=FG, selectbackground=T("ACCENT"),
            selectforeground=T("ACCENT_FG"), relief="flat", height=14,
            highlightthickness=1, highlightbackground=T("BORDER"),
            activestyle="none", font=F(9), exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=16)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        row = tk.Frame(self.panel, bg=CARD)
        row.pack(fill="x", padx=16, pady=(8, 4))
        ttk.Button(row, text="删除选区", command=self._delete_selection).pack(
            side="left")
        ttk.Button(row, text="重命名…", command=self._rename_selection).pack(
            side="left", padx=(6, 0))

        form = tk.Frame(self.panel, bg=CARD)
        form.pack(fill="x", padx=16, pady=(4, 0))
        self.name_var = tk.StringVar()
        tk.Label(form, text="名称", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=0, column=0, sticky="w")
        self._entry(form, self.name_var, 12).grid(row=0, column=1,
                                                 columnspan=3, sticky="ew",
                                                 ipady=2, padx=(2, 0))
        form.columnconfigure(1, weight=1)
        tk.Label(form, text="X", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=1, column=0, sticky="w", pady=(4, 0))
        self.x_var = tk.StringVar()
        self._entry(form, self.x_var, 4).grid(row=1, column=1, sticky="w",
                                              ipady=2, padx=(2, 10))
        tk.Label(form, text="Y", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=1, column=2, sticky="w")
        self.y_var = tk.StringVar()
        self._entry(form, self.y_var, 4).grid(row=1, column=3, sticky="w",
                                              ipady=2, padx=(2, 0))
        tk.Label(form, text="W", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=2, column=0, sticky="w", pady=(4, 0))
        self.w_var = tk.StringVar()
        self._entry(form, self.w_var, 4).grid(row=2, column=1, sticky="w",
                                              ipady=2, padx=(2, 10))
        tk.Label(form, text="H", bg=CARD, fg=MUTED, font=F(8)).grid(
            row=2, column=2, sticky="w")
        self.h_var = tk.StringVar()
        self._entry(form, self.h_var, 4).grid(row=2, column=3, sticky="w",
                                              ipady=2, padx=(2, 0))
        for var in (self.name_var, self.x_var, self.y_var,
                    self.w_var, self.h_var):
            var.trace_add("write", lambda *a: self._apply_selection())

        tk.Label(self.panel,
                 text="在图上拖 = 新建选区；按住选区拖动；拖右下角改大小。\n"
                      "滚轮缩放，中键拖动画面。Esc 关闭。",
                 bg=CARD, fg=MUTED, font=F(8), anchor="w",
                 justify="left").pack(fill="x", padx=16, pady=(8, 0))
        ttk.Button(self.panel, text="关闭", command=self.close).pack(
            side="bottom", pady=14)
        self._refresh_list()

    def _build_board_panel(self):
        T = self.app.T
        CARD, MUTED, FG = T("CARD"), T("MUTED"), T("FG")
        F = self.app.F
        canvas = self.editor._current_canvas()

        tk.Label(self.panel, text="画布", bg=CARD, fg=T("ACCENT"),
                 font=F(11, "bold"), anchor="w").pack(fill="x", padx=16,
                                                      pady=(14, 6))
        size = tk.Frame(self.panel, bg=CARD)
        size.pack(fill="x", padx=16)
        tk.Label(size, text="尺寸", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        self.cw_var = tk.StringVar(
            value=str(canvas.width) if canvas else "")
        self.ch_var = tk.StringVar(
            value=str(canvas.height) if canvas else "")
        self._entry(size, self.cw_var, 4).pack(side="left", ipady=2,
                                               padx=(4, 0))
        tk.Label(size, text="×", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left", padx=3)
        self._entry(size, self.ch_var, 4).pack(side="left", ipady=2)
        self.cw_var.trace_add("write", lambda *a: self._apply_size())
        self.ch_var.trace_add("write", lambda *a: self._apply_size())

        mats = tk.Frame(self.panel, bg=CARD)
        mats.pack(fill="x", padx=16, pady=(8, 2))
        tk.Label(mats, text="素材", bg=CARD, fg=MUTED,
                 font=F(8)).pack(side="left")
        self.material_combo = ttk.Combobox(mats, state="readonly")
        self.material_combo.pack(side="left", fill="x", expand=True,
                                 padx=(4, 4))
        ttk.Button(mats, text="添加映射",
                   command=self._add_mapping).pack(side="left")

        self.listbox = tk.Listbox(
            self.panel, bg=T("BG2"), fg=FG, selectbackground=T("ACCENT"),
            selectforeground=T("ACCENT_FG"), relief="flat", height=12,
            highlightthickness=1, highlightbackground=T("BORDER"),
            activestyle="none", font=F(9), exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=16, pady=(4, 4))
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        row = tk.Frame(self.panel, bg=CARD)
        row.pack(fill="x", padx=16)
        ttk.Button(row, text="删除", command=self._delete_mapping).pack(
            side="left")
        ttk.Button(row, text="↑", width=3,
                   command=lambda: self._move_mapping(-1)).pack(
                       side="left", padx=(4, 0))
        ttk.Button(row, text="↓", width=3,
                   command=lambda: self._move_mapping(1)).pack(
                       side="left", padx=(4, 0))

        xy = tk.Frame(self.panel, bg=CARD)
        xy.pack(fill="x", padx=16, pady=(6, 0))
        tk.Label(xy, text="X", bg=CARD, fg=MUTED, font=F(8)).pack(side="left")
        self.mx_var = tk.StringVar()
        self._entry(xy, self.mx_var, 5).pack(side="left", ipady=2, padx=(3, 8))
        tk.Label(xy, text="Y", bg=CARD, fg=MUTED, font=F(8)).pack(side="left")
        self.my_var = tk.StringVar()
        self._entry(xy, self.my_var, 5).pack(side="left", ipady=2, padx=(3, 0))
        self.mx_var.trace_add("write", lambda *a: self._apply_xy())
        self.my_var.trace_add("write", lambda *a: self._apply_xy())

        tk.Label(self.panel,
                 text="在画布上拖动映射摆位置；列表顺序 = 叠放顺序。\n"
                      "滚轮缩放，中键拖动画面。Esc 关闭。",
                 bg=CARD, fg=MUTED, font=F(9), anchor="w",
                 justify="left").pack(fill="x", padx=16, pady=(8, 0))
        ttk.Button(self.panel, text="关闭", command=self.close).pack(
            side="bottom", pady=14)
        self._refresh_materials()
        self._refresh_list()

    # ---------- 数据同步 ----------
    def _current_canvas(self):
        return self.editor._current_canvas()

    def _current_mapping(self):
        canvas = self._current_canvas()
        if canvas is None:
            return None
        return self.editor.bp.mapping(canvas, self.map_id)

    def _refresh_list(self):
        if not hasattr(self, "listbox"):
            return
        self.listbox.delete(0, "end")
        if self.mode == "input":
            for sel in self.editor.bp.selections:
                self.listbox.insert(
                    "end", f"{sel.name}  ({sel.x},{sel.y}) {sel.w}×{sel.h}")
            for i, sel in enumerate(self.editor.bp.selections):
                if sel.id == self.sel_id:
                    self.listbox.selection_set(i)
        else:
            canvas = self._current_canvas()
            if canvas is None:
                return
            for i, mp in enumerate(canvas.mappings, 1):
                self.listbox.insert(
                    "end", f"{i}. {self.editor._material_label(mp)}"
                           f"   @ {mp.x},{mp.y}")
            for i, mp in enumerate(canvas.mappings):
                if mp.id == self.map_id:
                    self.listbox.selection_set(i)
        self._load_fields()

    def _load_fields(self):
        self._loading = True
        try:
            if self.mode == "input":
                sel = self.editor.bp.selection(self.sel_id)
                if sel is None:
                    for var in (self.name_var, self.x_var, self.y_var,
                                self.w_var, self.h_var):
                        var.set("")
                else:
                    self.name_var.set(sel.name)
                    self.x_var.set(str(sel.x))
                    self.y_var.set(str(sel.y))
                    self.w_var.set(str(sel.w))
                    self.h_var.set(str(sel.h))
            else:
                mp = self._current_mapping()
                if mp is None:
                    self.mx_var.set("")
                    self.my_var.set("")
                else:
                    self.mx_var.set(str(mp.x))
                    self.my_var.set(str(mp.y))
        finally:
            self._loading = False

    def _apply_selection(self):
        if self._loading:
            return
        bp = self.editor.bp
        sel = bp.selection(self.sel_id)
        if sel is None:
            return
        name = self.name_var.get().strip()
        if name:
            sel.name = name
        try:
            x = int(float(self.x_var.get() or 0))
            y = int(float(self.y_var.get() or 0))
            w = int(float(self.w_var.get() or 1))
            h = int(float(self.h_var.get() or 1))
        except ValueError:
            return
        iw = (self.editor.ref_image.width if self.editor.ref_image else 64)
        ih = (self.editor.ref_image.height if self.editor.ref_image else 64)
        w = max(1, min(iw, w))
        h = max(1, min(ih, h))
        sel.x = max(0, min(iw - w, x))
        sel.y = max(0, min(ih - h, y))
        sel.w, sel.h = w, h
        self._refresh_list()
        self._sync_editor()

    def _apply_size(self):
        if self._loading:
            return
        canvas = self._current_canvas()
        if canvas is None:
            return
        try:
            canvas.width = max(1, min(1024, int(float(self.cw_var.get()))))
            canvas.height = max(1, min(1024, int(float(self.ch_var.get()))))
        except ValueError:
            return
        self._sync_editor()

    def _apply_xy(self):
        if self._loading:
            return
        mp = self._current_mapping()
        canvas = self._current_canvas()
        if mp is None or canvas is None:
            return
        try:
            x = int(float(self.mx_var.get() or 0))
            y = int(float(self.my_var.get() or 0))
        except ValueError:
            return
        mp.x = max(0, min(canvas.width, x))
        mp.y = max(0, min(canvas.height, y))
        self.render()
        self.editor._render_board()
        self._refresh_list()

    def _sync_editor(self):
        self.render()
        self.editor._build_canvas_panel()
        self.editor._render_input_preview()
        self.editor._render_board()
        self.editor._render()
        self.editor.dirty = True

    def _on_list_select(self, _e=None):
        cur = self.listbox.curselection()
        if not cur:
            return
        idx = int(cur[0])
        if self.mode == "input":
            if 0 <= idx < len(self.editor.bp.selections):
                self.sel_id = self.editor.bp.selections[idx].id
                self.editor.sel_selection_id = self.sel_id
                self.editor._load_selection_vars()
                self.editor._refresh_selection_list()
        else:
            canvas = self._current_canvas()
            if canvas is not None and 0 <= idx < len(canvas.mappings):
                self.map_id = canvas.mappings[idx].id
                self.editor.sel_mapping_id = self.map_id
                self.editor._load_mapping_vars()
        self._load_fields()
        self.render()
        self.editor._render_input_preview()
        self.editor._render_board()

    def _delete_selection(self):
        if self.mode != "input" or self.sel_id is None:
            return
        self.editor.bp.remove_selection(self.sel_id)
        self.sel_id = None
        self.editor.sel_selection_id = None
        self.editor._refresh_selection_list()
        self.editor._load_selection_vars()
        self._refresh_list()
        self._sync_editor()

    def _rename_selection(self):
        if self.mode != "input":
            return
        sel = self.editor.bp.selection(self.sel_id)
        if sel is None:
            return
        name = simpledialog.askstring("重命名选区", "选区名字：",
                                      initialvalue=sel.name, parent=self)
        if not name:
            return
        sel.name = sanitize_name(name) or sel.name
        self._refresh_list()
        self._sync_editor()

    def _refresh_materials(self):
        canvas = self._current_canvas()
        if canvas is None:
            return
        choices = self.editor.bp.materials_for(canvas)
        self._choices = choices
        labels = [c[2] for c in choices]
        self.material_combo["values"] = labels
        if labels:
            self.material_combo.current(0)
        else:
            self.material_combo.set("（没有素材）")

    def _add_mapping(self):
        canvas = self._current_canvas()
        if canvas is None:
            return
        choices = getattr(self, "_choices", [])
        if not choices:
            return
        idx = self.material_combo.current()
        if not (0 <= idx < len(choices)):
            idx = 0
        kind, ref_id = choices[idx][0], choices[idx][1]
        mp = self.editor.bp.add_mapping(canvas, kind, ref_id, 0, 0)
        self.map_id = mp.id
        self.editor.sel_mapping_id = mp.id
        self.editor.dirty = True
        self.editor._refresh_mapping_list()
        self.editor._load_mapping_vars()
        self._refresh_list()
        self._sync_editor()

    def _delete_mapping(self):
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        self.editor.bp.remove_mapping(canvas, mp.id)
        self.map_id = None
        self.editor.sel_mapping_id = None
        self.editor.dirty = True
        self.editor._refresh_mapping_list()
        self.editor._load_mapping_vars()
        self._refresh_list()
        self._sync_editor()

    def _move_mapping(self, delta):
        canvas = self._current_canvas()
        mp = self._current_mapping()
        if canvas is None or mp is None:
            return
        if self.editor.bp.move_mapping(canvas, mp.id, delta):
            self.editor.dirty = True
            self.editor._refresh_mapping_list()
            self._refresh_list()
            self._sync_editor()

    # ---------- 渲染 ----------
    def render(self):
        if not self.canvas.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        T = self.app.T
        cw = c.winfo_width()
        ch = c.winfo_height()
        if cw < 30 or ch < 30:
            return
        if self.mode == "input":
            self._render_input(c, cw, ch, T)
        else:
            self._render_board(c, cw, ch, T)

    def _render_input(self, c, cw, ch, T):
        image = self.editor.ref_image
        if image is None:
            c.create_text(cw / 2, ch / 2,
                          text="还没有示例图\n回编辑器导入一张",
                          fill=T("MUTED"), justify="center",
                          font=self.app.F(11))
            self.view = None
            return
        iw, ih = image.size
        base = min((cw - 40) / iw, (ch - 40) / ih)
        scale = max(0.05, base * self.zoom)
        dw, dh = max(1, int(iw * scale)), max(1, int(ih * scale))
        ox = int((cw - dw) / 2 + self.pan_x)
        oy = int((ch - dh) / 2 + self.pan_y)
        photo = ImageTk.PhotoImage(image.resize((dw, dh), Image.NEAREST))
        self._photo = photo
        c.create_image(ox, oy, image=photo, anchor="nw")
        c.create_rectangle(ox, oy, ox + dw, oy + dh, outline=T("BORDER"))
        self.view = (ox, oy, scale)
        if self.app.settings.get("grid", True) and scale >= 7 and iw <= 256 and ih <= 256:
            for gx in range(1, iw):
                x = int(round(ox + gx * scale))
                c.create_line(x, oy, x, oy + dh, fill=T("GRID"), dash=(1, 3))
            for gy in range(1, ih):
                y = int(round(oy + gy * scale))
                c.create_line(ox, y, ox + dw, y, fill=T("GRID"), dash=(1, 3))
        for sel in self.editor.bp.selections:
            x1 = ox + sel.x * scale
            y1 = oy + sel.y * scale
            x2 = x1 + sel.w * scale
            y2 = y1 + sel.h * scale
            selected = sel.id == self.sel_id
            color = T("ACCENT") if selected else T("PORT_TXT")
            c.create_rectangle(x1, y1, x2, y2, outline=color,
                               width=2 if selected else 1)
            if selected:
                tw = (self.editor._font_small.measure(sel.name)
                      if self.editor._font_small else len(sel.name) * 8) + 8
                c.create_rectangle(x1, y1, x1 + tw, y1 + 16,
                                   fill=color, outline="")
                c.create_text(x1 + 4, y1 + 2, text=sel.name, fill=T("BG"),
                              anchor="nw", font=self.app.F(8))
                c.create_rectangle(x2 - 7, y2 - 7, x2 + 1, y2 + 1,
                                   fill=color, outline="")
        drag = self.drag
        if drag and drag.get("mode") == "create" and drag.get("rect"):
            x1, y1, x2, y2 = drag["rect"]
            c.create_rectangle(x1, y1, x2, y2, outline=T("ACCENT"),
                               dash=(5, 3), width=2)

    def _render_board(self, c, cw, ch, T):
        canvas = self._current_canvas()
        if canvas is None:
            c.create_text(cw / 2, ch / 2, text="没有选中画布",
                          fill=T("MUTED"), font=self.app.F(11))
            self.view = None
            return
        scale = min((cw - 60) / max(1, canvas.width),
                    (ch - 60) / max(1, canvas.height))
        scale = max(0.05, scale * self.zoom)
        dw = max(1, int(canvas.width * scale))
        dh = max(1, int(canvas.height * scale))
        ox = int((cw - dw) / 2 + self.pan_x)
        oy = int((ch - dh) / 2 + self.pan_y)
        self.view = (ox, oy, scale)
        c1, c2 = CHECKER_PRESETS[self.app.settings.get(
            "theme", "dark")]
        checker = make_checker(dw, dh, c1, c2, cell=max(6, int(8 * scale)))
        board = render_result_image(self.editor.bp, canvas,
                                    self.editor.ref_image, 1.0)
        board = board.resize((dw, dh), Image.NEAREST)
        checker = checker.convert("RGBA")
        checker.alpha_composite(board, (0, 0))
        photo = ImageTk.PhotoImage(checker)
        self._photo = photo
        c.create_image(ox, oy, image=photo, anchor="nw")
        c.create_rectangle(ox, oy, ox + dw, oy + dh, outline=T("BORDER"))
        if self.app.settings.get("grid", True) and scale >= 7 and canvas.width <= 256 and canvas.height <= 256:
            for gx in range(1, canvas.width):
                x = int(round(ox + gx * scale))
                c.create_line(x, oy, x, oy + dh, fill=T("GRID"), dash=(1, 3))
            for gy in range(1, canvas.height):
                y = int(round(oy + gy * scale))
                c.create_line(ox, y, ox + dw, y, fill=T("GRID"), dash=(1, 3))
        for i, mp in enumerate(canvas.mappings, 1):
            w, h = self.editor.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
            if w <= 0 or h <= 0:
                continue
            x1 = ox + mp.x * scale
            y1 = oy + mp.y * scale
            x2 = x1 + w * scale
            y2 = y1 + h * scale
            selected = mp.id == self.map_id
            color = T("ACCENT") if selected else T("PORT_TXT")
            c.create_rectangle(x1, y1, x2, y2, outline=color,
                               width=2 if selected else 1)
            c.create_text(x1 + 3, y1 + 3, text=str(i), fill=color,
                          anchor="nw", font=self.app.F(9, "bold"))

    # ---------- 交互 ----------
    def _on_wheel(self, event, up=None, down=None):
        if self.view is None:
            return
        if up is None and down is None:
            delta = getattr(event, "delta", 0)
            if delta > 0:
                up = True
            elif delta < 0:
                down = True
            else:
                return
        if self.mode == "input":
            if self.editor.ref_image is None:
                return
            iw, ih = self.editor.ref_image.size
            margin = 40
        else:
            canvas = self._current_canvas()
            if canvas is None:
                return
            iw, ih = canvas.width, canvas.height
            margin = 60
        ox, oy, s = self.view
        px = (event.x - ox) / s
        py = (event.y - oy) / s
        factor = 1.12 if up else 1 / 1.12
        new_zoom = max(0.3, min(16.0, self.zoom * factor))
        if abs(new_zoom - self.zoom) < 1e-9:
            return
        self.zoom = new_zoom
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        base = min((cw - margin) / max(1, iw), (ch - margin) / max(1, ih))
        s2 = base * self.zoom
        self.pan_x = (event.x - px * s2) - (cw - iw * s2) / 2
        self.pan_y = (event.y - py * s2) - (ch - ih * s2) / 2
        self.render()

    def _middle_press(self, event):
        self._pan_start = (event.x, event.y)
        self._pan_orig = (self.pan_x, self.pan_y)
        self.canvas.configure(cursor="fleur")

    def _middle_motion(self, event):
        if self._pan_start is None:
            return
        self.pan_x = self._pan_orig[0] + (event.x - self._pan_start[0])
        self.pan_y = self._pan_orig[1] + (event.y - self._pan_start[1])
        self.render()

    def _middle_release(self, _event):
        self._pan_start = None
        self.canvas.configure(cursor="")

    def _to_image(self, x, y):
        if self.view is None:
            return None
        ox, oy, s = self.view
        return (x - ox) / s, (y - oy) / s

    def _on_press(self, event):
        if self.mode == "input":
            self._input_press(event)
        else:
            self._board_press(event)

    def _on_motion(self, event):
        if self.mode == "input":
            self._input_motion(event)
        else:
            self._board_motion(event)

    def _on_release(self, event):
        if self.mode == "input":
            self._input_release(event)
        else:
            self._board_release(event)

    def _input_press(self, event):
        if self.editor.ref_image is None or self.view is None:
            return
        pos = self._to_image(event.x, event.y)
        if pos is None:
            return
        ix, iy = pos
        hit = None
        for sel in reversed(self.editor.bp.selections):
            if (sel.x <= ix <= sel.x + sel.w
                    and sel.y <= iy <= sel.y + sel.h):
                hit = sel
                break
        if hit is not None:
            self.sel_id = hit.id
            self.editor.sel_selection_id = hit.id
            self.editor._load_selection_vars()
            self.editor._refresh_selection_list()
            ox, oy, s = self.view
            near = (abs(event.x - (ox + (hit.x + hit.w) * s)) <= 10
                    and abs(event.y - (oy + (hit.y + hit.h) * s)) <= 10)
            self.drag = {"mode": "resize" if near else "move", "sel": hit,
                         "ix": ix, "iy": iy,
                         "orig": (hit.x, hit.y, hit.w, hit.h)}
        else:
            self.drag = {"mode": "create", "start": (ix, iy)}
        self._refresh_list()
        self.render()

    def _input_motion(self, event):
        drag = self.drag
        if drag is None or self.view is None:
            return
        pos = self._to_image(event.x, event.y)
        if pos is None:
            return
        iw = self.editor.ref_image.width
        ih = self.editor.ref_image.height
        ix = max(0, min(iw, pos[0]))
        iy = max(0, min(ih, pos[1]))
        if drag["mode"] == "create":
            x0, y0 = drag["start"]
            ox, oy, s = self.view
            x0, x1 = int(round(min(x0, ix))), int(round(max(x0, ix)))
            y0, y1 = int(round(min(y0, iy))), int(round(max(y0, iy)))
            drag["rect"] = (ox + x0 * s, oy + y0 * s,
                            ox + x1 * s, oy + y1 * s)
            drag["box"] = (x0, y0, x1, y1)
            self.render()
        elif drag["mode"] == "move":
            sel = drag["sel"]
            x0, y0, w0, h0 = drag["orig"]
            dx = int(round(ix - drag["ix"]))
            dy = int(round(iy - drag["iy"]))
            sel.x = max(0, min(iw - w0, x0 + dx))
            sel.y = max(0, min(ih - h0, y0 + dy))
            self._load_fields()
            self.render()
        elif drag["mode"] == "resize":
            sel = drag["sel"]
            x0, y0, w0, h0 = drag["orig"]
            nx = max(sel.x + 1, min(iw, int(round(ix))))
            ny = max(sel.y + 1, min(ih, int(round(iy))))
            sel.w = max(1, nx - sel.x)
            sel.h = max(1, ny - sel.y)
            self._load_fields()
            self.render()

    def _input_release(self, event):
        drag = self.drag
        self.drag = None
        if drag is None:
            return
        if drag.get("mode") == "create" and drag.get("box"):
            x0, y0, x1, y1 = drag["box"]
            if x1 - x0 >= 1 and y1 - y0 >= 1:
                sel = self.editor.bp.add_selection(
                    int(round(x0)), int(round(y0)),
                    int(round(x1 - x0)), int(round(y1 - y0)))
                self.sel_id = sel.id
                self.editor.sel_selection_id = sel.id
        self._refresh_list()
        self.render()
        self._sync_editor()

    def _board_press(self, event):
        canvas = self._current_canvas()
        if canvas is None or self.view is None:
            return
        pos = self._to_image(event.x, event.y)
        if pos is None:
            return
        bx, by = pos
        hit = None
        for mp in reversed(canvas.mappings):
            w, h = self.editor.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
            if w <= 0 or h <= 0:
                continue
            if mp.x <= bx <= mp.x + w and mp.y <= by <= mp.y + h:
                hit = mp
                break
        if hit is None:
            return
        self.map_id = hit.id
        self.editor.sel_mapping_id = hit.id
        self.editor._load_mapping_vars()
        self.editor._refresh_mapping_list()
        self.drag = {"mode": "mapping", "mp": hit, "bx": bx, "by": by,
                     "orig": (hit.x, hit.y), "canvas": canvas}
        self._refresh_list()
        self.render()

    def _board_motion(self, event):
        drag = self.drag
        if drag is None or drag.get("mode") != "mapping" or self.view is None:
            return
        pos = self._to_image(event.x, event.y)
        if pos is None:
            return
        canvas = drag["canvas"]
        mp = drag["mp"]
        w, h = self.editor.bp.material_size(mp.kind, mp.ref_id, mp.rotation)
        dx = int(round(pos[0] - drag["bx"]))
        dy = int(round(pos[1] - drag["by"]))
        x0, y0 = drag["orig"]
        mp.x = max(0, min(max(0, canvas.width - w), x0 + dx))
        mp.y = max(0, min(max(0, canvas.height - h), y0 + dy))
        self._load_fields()
        self.render()

    def _board_release(self, _event):
        if self.drag and self.drag.get("mode") == "mapping":
            self._refresh_list()
            self._sync_editor()
        self.drag = None

    def close(self):
        self.editor._build_canvas_panel()
        self.editor._build_input_panel()
        self.editor._render_input_preview()
        self.editor._render_board()
        self.editor._render()
        self.destroy()


# ====================================================================
# 资源管理器
# ====================================================================

class AssetManager(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("资源管理器")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        center_window(self, min(1200, max(900, sw - 120)),
                      min(780, max(560, sh - 120)))
        self.minsize(820, 520)
        self.configure(bg=app.T("BG"))
        self.transient(app.root)

        self.current_folder = None
        self.selected_file = None
        self.thumb_refs = []
        self._build()
        self.refresh_folders()

    def _build(self):
        T = self.app.T
        BG, CARD = T("BG"), T("CARD")
        CARD_HEADER, FG = T("CARD_HEADER"), T("FG")
        ACCENT, MUTED, BORDER = T("ACCENT"), T("MUTED"), T("BORDER")
        BG2 = T("BG2")

        top = tk.Frame(self, bg=CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        top.pack(fill="x", padx=16, pady=(16, 10))
        self.path_var = tk.StringVar(value="当前文件夹：")
        tk.Label(top, textvariable=self.path_var, bg=CARD, fg=FG,
                 anchor="w", font=self.app.F(9, "bold")).pack(
                     fill="x", padx=12, pady=(8, 0))
        tk.Label(top, text=f"程序目录  ·  {SCRIPT_DIR}", bg=CARD, fg=MUTED,
                 anchor="w", font=self.app.F(8)).pack(
                     fill="x", padx=12, pady=(0, 8))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=4)

        left = tk.Frame(body, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        left.pack(side="left", fill="y")
        lh = tk.Frame(left, bg=CARD_HEADER, height=32)
        lh.pack(fill="x")
        lh.pack_propagate(False)
        tk.Label(lh, text="文件夹", bg=CARD_HEADER, fg=ACCENT,
                 font=self.app.F(10, "bold"), anchor="w").pack(
                     side="left", padx=12)

        lb_frame = tk.Frame(left, bg=CARD)
        lb_frame.pack(fill="both", expand=True, padx=6, pady=6)
        fscroll = SlimScrollbar(lb_frame, command=lambda *a: None,
                                bg=CARD, thumb=BORDER, hover=ACCENT)
        fscroll.pack(side="right", fill="y")
        self.folder_lb = tk.Listbox(
            lb_frame, bg=CARD, fg=FG, width=26, selectbackground=ACCENT,
            selectforeground=T("ACCENT_FG"), relief="flat",
            highlightthickness=0, activestyle="none", font=self.app.F(9),
            yscrollcommand=fscroll.set)
        self.folder_lb.pack(side="left", fill="both", expand=True)
        fscroll.command = self.folder_lb.yview
        self.folder_lb.bind("<<ListboxSelect>>", self._on_select_folder)
        self.folder_lb.bind("<Double-Button-1>", self._on_open_folder)

        right = tk.Frame(body, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
        rh = tk.Frame(right, bg=CARD_HEADER, height=32)
        rh.pack(fill="x")
        rh.pack_propagate(False)
        tk.Label(rh, text="文件（单击选中，双击打开所在文件夹）",
                 bg=CARD_HEADER, fg=ACCENT, font=self.app.F(10, "bold"),
                 anchor="w").pack(side="left", padx=12)

        canvas_frame = tk.Frame(right, bg=CARD)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.file_canvas = tk.Canvas(canvas_frame, bg=BG2,
                                     highlightthickness=0, bd=0)
        scrollbar = SlimScrollbar(canvas_frame,
                                  command=self.file_canvas.yview,
                                  bg=BG2, thumb=BORDER, hover=ACCENT)
        self.file_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.file_canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.file_canvas, bg=BG2)
        self.canvas_window = self.file_canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: self.file_canvas.configure(
                scrollregion=self.file_canvas.bbox("all")))
        self.file_canvas.bind(
            "<Configure>",
            lambda e: self.file_canvas.itemconfig(self.canvas_window,
                                                  width=e.width))
        self.file_canvas.bind(
            "<MouseWheel>",
            lambda e: self.file_canvas.yview_scroll(int(-e.delta / 120), "units"))
        self.inner.bind(
            "<MouseWheel>",
            lambda e: self.file_canvas.yview_scroll(int(-e.delta / 120), "units"))

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=16, pady=(8, 16))
        self.status_var = tk.StringVar(value="请选择一个文件夹")
        tk.Label(bottom, textvariable=self.status_var, bg=BG, fg=MUTED,
                 anchor="w", font=self.app.F(9)).pack(
                     side="left", fill="x", expand=True)

        ttk.Button(bottom, text="选择文件夹…",
                   command=self.browse_folder).pack(side="right", padx=4)
        ttk.Button(bottom, text="打开文件夹",
                   command=self.open_current).pack(side="right", padx=4)
        ttk.Button(bottom, text="刷新列表",
                   command=self.refresh_folders).pack(side="right", padx=4)

    def default_folder(self):
        folder = SCRIPT_DIR / "导出"
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return folder

    def refresh_folders(self):
        self.folder_lb.delete(0, "end")
        skip = {"workflows", "blueprints", "__pycache__", ".git"}
        try:
            folders = sorted([d.name for d in SCRIPT_DIR.iterdir()
                              if d.is_dir() and d.name not in skip
                              and not d.name.startswith(".")])
        except Exception:
            folders = []
        for name in folders:
            self.folder_lb.insert("end", name)
        target = self.current_folder
        if target is None or not Path(target).exists():
            target = self.default_folder()
        if target.parent == SCRIPT_DIR:
            for i, name in enumerate(folders):
                if name == target.name:
                    self.folder_lb.selection_clear(0, "end")
                    self.folder_lb.selection_set(i)
                    break
        if target.exists():
            self.load_folder(target)
        else:
            self.status_var.set(f"共 {len(folders)} 个文件夹")

    def browse_folder(self):
        initial = self.current_folder or self.default_folder()
        path = filedialog.askdirectory(
            title="选择要浏览的文件夹", initialdir=str(initial),
            parent=self)
        if not path:
            return
        folder = Path(path)
        names = [self.folder_lb.get(i) for i in range(self.folder_lb.size())]
        self.folder_lb.selection_clear(0, "end")
        if folder.parent == SCRIPT_DIR and folder.name in names:
            self.folder_lb.selection_set(names.index(folder.name))
        self.load_folder(folder)

    def clear_inner(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.thumb_refs.clear()

    def _on_select_folder(self, _e=None):
        sel = self.folder_lb.curselection()
        if not sel:
            return
        self.load_folder(SCRIPT_DIR / self.folder_lb.get(sel[0]))

    def _on_open_folder(self, _e=None):
        sel = self.folder_lb.curselection()
        if sel:
            open_in_file_manager(SCRIPT_DIR / self.folder_lb.get(sel[0]))

    def load_folder(self, folder):
        T = self.app.T
        CARD, FG, MUTED = T("CARD"), T("FG"), T("MUTED")
        BORDER, ACCENT = T("BORDER"), T("ACCENT")
        folder = Path(folder) if folder is not None else None
        self.current_folder = folder
        self.selected_file = None
        self.clear_inner()

        if folder is None or not folder.exists():
            self.path_var.set("当前文件夹：")
            self.status_var.set("请选择一个文件夹")
            return
        self.path_var.set(f"当前文件夹：{folder}")
        try:
            files = sorted(
                [f for f in folder.rglob("*.png") if f.is_file()],
                key=lambda p: str(p.relative_to(folder)).lower())
        except Exception as exc:
            self.status_var.set(f"读取失败：{exc}")
            return
        total = len(files)
        if total > 800:
            files = files[:800]
        if not files:
            self.status_var.set(f"{folder.name} 里没有 PNG（含子文件夹）")
            return
        self.status_var.set(
            f"{folder.name}  ·  {total} 个 PNG（含子文件夹）  ·  单击选中")

        cols = 4
        for c in range(cols):
            self.inner.columnconfigure(c, weight=1)
        for idx, fp in enumerate(files):
            row, col = divmod(idx, cols)
            cell = tk.Frame(self.inner, bg=CARD, highlightthickness=2,
                            highlightbackground=BORDER)
            cell.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            img_lbl = None
            try:
                with Image.open(fp) as im:
                    im = im.convert("RGBA")
                    ow, oh = im.size
                    scale = min(170 / max(ow, 1), 130 / max(oh, 1), 4)
                    thumb = im.resize(
                        (max(1, int(ow * scale)), max(1, int(oh * scale))),
                        Image.NEAREST)
                photo = ImageTk.PhotoImage(thumb)
                self.thumb_refs.append(photo)
                img_lbl = tk.Label(cell, image=photo, bg=CARD, cursor="hand2")
                img_lbl.pack(padx=4, pady=(6, 2))
            except Exception as exc:
                img_lbl = tk.Label(cell, text=f"无法加载\n{exc}", bg=CARD,
                                   fg=MUTED, width=20, height=6)
                img_lbl.pack(padx=4, pady=(6, 2))
            try:
                with Image.open(fp) as im:
                    size_txt = f"{im.size[0]}×{im.size[1]}"
            except Exception:
                size_txt = "?"
            try:
                rel = str(fp.relative_to(folder))
            except Exception:
                rel = fp.name
            label = fp.name if fp.parent == folder else rel
            name_lbl = tk.Label(cell, text=label, bg=CARD, fg=FG,
                                font=self.app.F(9, "bold"), wraplength=180)
            name_lbl.pack()
            size_lbl = tk.Label(cell, text=size_txt, bg=CARD, fg=MUTED,
                                font=self.app.F(8))
            size_lbl.pack(pady=(0, 6))

            widgets = [w for w in (cell, img_lbl, name_lbl, size_lbl)
                       if w is not None]

            def onclick(_e=None, path=fp, frame=cell, shown=rel):
                self.selected_file = path
                for w in self.inner.winfo_children():
                    if isinstance(w, tk.Frame):
                        w.configure(highlightbackground=BORDER)
                frame.configure(highlightbackground=ACCENT)
                self.status_var.set(f"已选中：{shown}")

            def ondbl(_e=None, path=fp):
                open_in_file_manager(path.parent)

            for w in widgets:
                w.bind("<Button-1>", onclick)
                w.bind("<Double-Button-1>", ondbl)

    def open_current(self):
        if self.selected_file is not None:
            target = self.selected_file.parent
        elif self.current_folder is not None:
            target = self.current_folder
        else:
            target = SCRIPT_DIR
        open_in_file_manager(Path(target))


# ====================================================================
# 设置
# ====================================================================

def open_settings_window(app):
    T = app.T
    BG, BG2, CARD = T("BG"), T("BG2"), T("CARD")
    CARD_HEADER, FG, ACCENT = T("CARD_HEADER"), T("FG"), T("ACCENT")
    ACCENT_FG, ACCENT_H = T("ACCENT_FG"), T("ACCENT_HOVER")
    HOVER, MUTED, BORDER = T("HOVER"), T("MUTED"), T("BORDER")

    win = tk.Toplevel(app.root)
    win.title("设置")
    win.configure(bg=BG)
    center_window(win, 560, 700)
    win.resizable(False, False)
    win.transient(app.root)
    win.grab_set()

    def make_card(title):
        card = tk.Frame(win, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", padx=18, pady=(0, 12))
        hdr = tk.Frame(card, bg=CARD_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, bg=CARD_HEADER, fg=ACCENT,
                 font=app.F(10, "bold"), anchor="w").pack(
                     fill="x", padx=12, pady=6)
        body = tk.Frame(card, bg=CARD)
        body.pack(fill="x", padx=12, pady=10)
        return body

    def make_segment(parent, options, current, on_change):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x")
        buttons = {}

        def refresh(val):
            for v, b in buttons.items():
                if v == val:
                    b.configure(bg=ACCENT, fg=ACCENT_FG,
                                activebackground=ACCENT_H,
                                activeforeground=ACCENT_FG)
                else:
                    b.configure(bg=BG2, fg=FG, activebackground=HOVER,
                                activeforeground=FG)

        def click(val):
            refresh(val)
            on_change(val)

        for val, label in options:
            b = tk.Button(row, text=label, relief="flat", bd=0, padx=16,
                          pady=6, cursor="hand2", font=app.F(9),
                          command=lambda v=val: click(v))
            b.pack(side="left", padx=(0, 8))
            buttons[val] = b
        refresh(current)

    tk.Frame(win, bg=BG, height=18).pack(fill="x")
    btns = tk.Frame(win, bg=BG)
    btns.pack(side="bottom", fill="x", padx=18, pady=(8, 16))

    body1 = make_card("界面主题")
    theme_var = tk.StringVar(value=app.settings["theme"])
    make_segment(body1, (("dark", "深色"), ("light", "浅色"),
                         ("sand", "暖沙"), ("forest", "森林"),
                         ("sakura", "樱粉")),
                 app.settings["theme"], lambda v: theme_var.set(v))

    body2 = make_card("导出背景")
    fill_var = tk.StringVar(value="fill" if app.settings.get("bg_fill")
                            else "none")
    state = {"hex": app.settings["bg_color_hex"]}
    row = tk.Frame(body2, bg=CARD)
    row.pack(fill="x")
    swatch = tk.Label(row, bg=state["hex"], width=4, height=2,
                      relief="solid", bd=1)
    swatch.pack(side="left")
    hex_text = tk.Label(row, text=state["hex"], bg=CARD, fg=MUTED,
                        font=app.F(9))
    hex_text.pack(side="left", padx=(10, 0))

    def pick_color():
        result = colorchooser.askcolor(color=state["hex"],
                                       title="选择导出背景色", parent=win)
        if result and result[1]:
            state["hex"] = result[1]
            swatch.configure(bg=state["hex"])
            hex_text.configure(text=state["hex"])

    ttk.Button(row, text="选择颜色…", command=pick_color).pack(
        side="left", padx=(14, 0))
    make_segment(body2, (("none", "透明背景"), ("fill", "填充颜色")),
                 fill_var.get(), lambda v: fill_var.set(v))
    tk.Label(body2, text="填充颜色只在导出时生效；透明背景会保留 PNG 透明区域。",
             bg=CARD, fg=MUTED, font=app.F(8), anchor="w",
             justify="left", wraplength=370).pack(fill="x", pady=(8, 0))

    body3 = make_card("软件更新")
    tk.Label(body3, text=f"当前版本  {APP_VERSION}", bg=CARD, fg=FG,
             font=app.F(10, "bold"), anchor="w").pack(fill="x")

    repo_row = tk.Frame(body3, bg=CARD)
    repo_row.pack(fill="x", pady=(6, 4))
    tk.Label(repo_row, text="更新源", bg=CARD, fg=MUTED,
             font=app.F(8)).pack(side="left")
    repo_var = tk.StringVar(value=app.settings.get("update_repo", ""))
    tk.Entry(repo_row, textvariable=repo_var, bg=BG2, fg=FG,
             insertbackground=FG, relief="flat", highlightthickness=1,
             highlightbackground=BORDER, highlightcolor=ACCENT,
             font=app.F(9)).pack(side="left", fill="x", expand=True,
                                  padx=(8, 4), ipady=2)
    tk.Label(body3,
             text="填 GitHub 仓库，例如 Tuenztoo/BLUE。用 GitHub Releases 免费发更新，"
                  "不需要自己买服务器。",
             bg=CARD, fg=MUTED, font=app.F(8), anchor="w",
             justify="left", wraplength=460).pack(fill="x", pady=(0, 6))

    def install_zip(path):
        if not getattr(sys, "frozen", False):
            messagebox.showinfo(
                "更新", "当前是源码运行，不能自动替换程序。\n"
                        "请用打包后的 BLUE.exe，或直接更新源码。",
                parent=win)
            return
        cache = SCRIPT_DIR / "更新缓存"
        try:
            shutil.rmtree(cache, ignore_errors=True)
            cache.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    name = info.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/"):
                        raise ValueError("更新包里有非法路径")
                    z.extract(info, cache)
            base = cache
            if (base / "BLUE").is_dir() and (base / "BLUE" / "BLUE.exe").exists():
                base = base / "BLUE"
            if not (base / "BLUE.exe").exists():
                raise ValueError("更新包里没有找到 BLUE.exe")
            if not (base / "_internal").is_dir():
                raise ValueError("更新包不完整：缺少 _internal 文件夹")
        except Exception as exc:
            shutil.rmtree(cache, ignore_errors=True)
            messagebox.showerror("更新包无效", str(exc), parent=win)
            return
        if not messagebox.askyesno(
                "确认更新",
                "更新会关闭当前 BLUE，然后替换程序文件。\n\n"
                "blueprints、workflows、skin_head_settings.json、"
                "导出、临时 都会保留。\n\n继续？",
                parent=win):
            shutil.rmtree(cache, ignore_errors=True)
            return
        src = "更新缓存\\BLUE" if base.name == "BLUE" else "更新缓存"
        bat = SCRIPT_DIR / "更新.bat"
        bat.write_text(
            "@echo off\r\n"
            "chcp 65001 >nul\r\n"
            "cd /d \"%~dp0\"\r\n"
            "timeout /t 2 /nobreak >nul\r\n"
            "taskkill /f /im BLUE.exe >nul 2>nul\r\n"
            f"robocopy \"{src}\" \".\" /E /XD blueprints workflows 导出 临时 "
            "/XF skin_head_settings.json 更新.bat >nul\r\n"
            "start \"\" \"BLUE.exe\"\r\n"
            "rd /s /q \"更新缓存\"\r\n"
            "del \"%~f0\"\r\n",
            encoding="utf-8")
        try:
            app._save_settings()
            subprocess.Popen(
                ["cmd.exe", "/c", str(bat)],
                cwd=str(SCRIPT_DIR),
                creationflags=getattr(subprocess, "DETACHED_PROCESS", 8))
        except Exception as exc:
            messagebox.showerror("启动更新失败", str(exc), parent=win)
            return
        win.destroy()
        app.on_close()

    def import_update():
        path = filedialog.askopenfilename(
            parent=win, title="选择 BLUE 更新包",
            filetypes=[("BLUE 更新包", "*.zip")])
        if path:
            install_zip(path)

    def check_update():
        repo = repo_var.get().strip().strip("/")
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            messagebox.showinfo(
                "检查更新",
                "先填 GitHub 仓库，例如 Tuenztoo/BLUE。\n"
                "免费做法：建一个 public 仓库，在 Releases 里上传 "
                "BLUE_x.x.xbeta_win64.zip。",
                parent=win)
            return
        app.settings["update_repo"] = repo
        app._save_settings()
        api = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            req = urllib.request.Request(
                api, headers={"User-Agent": "BLUE-updater",
                              "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            messagebox.showerror(
                "检查更新失败",
                f"连不上 GitHub Releases。\n\n{exc}\n\n"
                "确认仓库是 public，且已经发过 Release。",
                parent=win)
            return

        def vtuple(s):
            nums = re.findall(r"\d+", str(s))[:3]
            return tuple(int(x) for x in nums) + (0,) * (3 - len(nums))

        tag = data.get("tag_name", "")
        if vtuple(tag) <= vtuple(APP_VERSION):
            messagebox.showinfo("检查更新", f"已经是最新版本 {APP_VERSION}。",
                                parent=win)
            return
        asset = None
        for item in data.get("assets", []):
            name = (item.get("name") or "").lower()
            if name.endswith(".zip") and ("blue" in name or "win64" in name):
                asset = item
                break
        if asset is None:
            messagebox.showinfo(
                "检查更新", f"发现 {tag}，但没有找到 win64 的 zip 更新包。",
                parent=win)
            return
        if not messagebox.askyesno(
                "发现新版本",
                f"当前 {APP_VERSION}，最新 {tag}。\n\n"
                f"下载 {asset.get('name')} 并更新？\n"
                "蓝图、流程、设置都会保留。",
                parent=win):
            return
        tmp = SCRIPT_DIR / "更新包.zip"
        try:
            app.status_var.set("正在下载更新…")
            req = urllib.request.Request(
                asset["browser_download_url"],
                headers={"User-Agent": "BLUE-updater"})
            with urllib.request.urlopen(req, timeout=60) as resp, \
                    open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
        except Exception as exc:
            try:
                tmp.unlink()
            except Exception:
                pass
            app.status_var.set("就绪")
            messagebox.showerror("下载失败", str(exc), parent=win)
            return
        install_zip(tmp)

    ttk.Button(body3, text="检查更新", command=check_update).pack(
        side="left", pady=(2, 0))
    ttk.Button(body3, text="导入本地更新包…", command=import_update).pack(
        side="left", padx=(8, 0), pady=(2, 0))

    def apply_and_close():
        old_theme = app.settings["theme"]
        app.settings["theme"] = theme_var.get()
        app.settings["bg_fill"] = (fill_var.get() == "fill")
        hx = state["hex"]
        if re.fullmatch(r"#[0-9a-fA-F]{6}", hx or ""):
            app.settings["bg_color_hex"] = hx.lower()
            app.settings["bg_color"] = tuple(
                int(hx[i:i + 2], 16) for i in (1, 3, 5))
        app._save_settings()
        win.destroy()
        if app.settings["theme"] != old_theme:
            app.rebuild_ui()
        else:
            app.toast("设置已保存")

    ttk.Button(btns, text="应用并关闭", style="Accent.TButton",
               command=apply_and_close).pack(side="right")
    ttk.Button(btns, text="取消", command=win.destroy).pack(
        side="right", padx=(0, 8))


# ====================================================================
# 主界面
# ====================================================================

class SkinHeadApp:
    def __init__(self, root):
        self.root = root
        self.source_path = None
        self._layout_job = None
        self._status_reset_job = None
        self._running = False
        self._combo_window = None

        try:
            families = set(tkfont.families(root))
        except Exception:
            families = set()
        self._font_family = "TkDefaultFont"
        for cand in ("Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",
                     "Hiragino Sans GB", "Noto Sans CJK SC",
                     "Source Han Sans SC", "WenQuanYi Micro Hei",
                     "Segoe UI", "Helvetica"):
            if cand in families:
                self._font_family = cand
                break

        self._fonts = {}
        for name, size, weight in (("f8", 8, "normal"), ("f9", 9, "normal"),
                                   ("f10", 10, "normal"),
                                   ("f10b", 10, "bold"),
                                   ("f12b", 12, "bold"),
                                   ("f16b", 16, "bold")):
            try:
                self._fonts[name] = tkfont.Font(
                    family=self._font_family, size=size, weight=weight)
            except Exception:
                self._fonts[name] = None

        self.settings = {
            "theme": "light",
            "bg_color": (255, 255, 255),
            "bg_color_hex": "#ffffff",
            "bg_fill": False,
            "grid": True,
            "update_repo": "",
            "last_flow": "",
            "last_source": "",
        }
        self._load_settings()

        self.workflow_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="就绪")
        self.source_var = tk.StringVar(value="")
        self.flow_hint_var = tk.StringVar(value="")

        root.title(APP_TITLE)
        self._fullscreen = False
        self._chrome_offset = None
        self._hwnd = None
        self._round_job = None
        root.bind("<Escape>", self._exit_fullscreen)
        center_window(root, 940, 444)
        root.minsize(880, 420)
        _sw, _sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self._base_geometry = (f"940x444+{max(0, (_sw - 940) // 2)}"
                               f"+{max(0, (_sh - 444) // 3)}")

        path = self.settings.get("last_source", "")
        if path and Path(path).exists():
            self.source_path = Path(path)
            self._update_source_label()

        self._ensure_first_workflow()
        self.build_ui()
        self.root.after(80, self._apply_native_chrome)

    # ---------- 主题 / 字体 ----------
    def T(self, key):
        return THEMES[self.settings["theme"]][key]

    def F(self, size=10, weight="normal"):
        return (self._font_family, size, weight)

    def _measure(self, text, font_name="f9"):
        font = self._fonts.get(font_name)
        if font is None:
            return len(str(text)) * 8
        return font.measure(str(text))

    def _fit(self, text, max_px, font_name="f9"):
        text = str(text)
        if self._measure(text, font_name) <= max_px:
            return text
        cut = text
        while cut and self._measure(cut + "…", font_name) > max_px:
            cut = cut[:-1]
        return (cut + "…") if cut else ""

    def toast(self, message):
        self.status_var.set(message)
        if self._status_reset_job is not None:
            try:
                self.root.after_cancel(self._status_reset_job)
            except Exception:
                pass
        self._status_reset_job = self.root.after(
            6000, lambda: self.status_var.set("就绪"))

    # ---------- 设置存取 ----------
    def _load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except Exception:
            data = {}
        if data.get("theme") in THEMES:
            self.settings["theme"] = data["theme"]
        hx = data.get("bg_color_hex")
        if isinstance(hx, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", hx):
            self.settings["bg_color_hex"] = hx.lower()
            self.settings["bg_color"] = tuple(
                int(hx[i:i + 2], 16) for i in (1, 3, 5))
        self.settings["bg_fill"] = bool(data.get("bg_fill", False))
        self.settings["grid"] = bool(data.get("grid", True))
        self.settings["update_repo"] = data.get("update_repo", "") or ""
        self.settings["last_flow"] = data.get("last_flow", "") or ""
        self.settings["last_source"] = data.get("last_source", "") or ""

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "theme": self.settings["theme"],
                    "bg_color_hex": self.settings["bg_color_hex"],
                    "bg_fill": self.settings["bg_fill"],
                    "grid": self.settings.get("grid", True),
                    "update_repo": self.settings.get("update_repo", ""),
                    "last_flow": self.workflow_var.get(),
                    "last_source": str(self.source_path or ""),
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg2 = self.T("BG2")
        card = self.T("CARD")
        fg = self.T("FG")
        border = self.T("BORDER")
        accent = self.T("ACCENT")
        accent_h = self.T("ACCENT_HOVER")
        accent_fg = self.T("ACCENT_FG")
        muted = self.T("MUTED")
        hover = self.T("HOVER")
        fam = self._font_family

        style.configure("TButton", background=card, foreground=fg,
                        bordercolor=border, focuscolor=card, borderwidth=1,
                        relief="flat", padding=(12, 7), font=(fam, 9))
        style.map("TButton",
                  background=[("disabled", card), ("pressed", hover),
                              ("active", hover)],
                  foreground=[("disabled", muted), ("pressed", fg),
                              ("active", fg)],
                  bordercolor=[("active", accent), ("pressed", accent)])
        style.configure("Accent.TButton", background=accent,
                        foreground=accent_fg, bordercolor=accent,
                        focuscolor=accent, borderwidth=1, relief="flat",
                        padding=(14, 8), font=(fam, 9, "bold"))
        style.map("Accent.TButton",
                  background=[("disabled", bg2), ("pressed", accent_h),
                              ("active", accent_h)],
                  foreground=[("disabled", muted), ("pressed", accent_fg),
                              ("active", accent_fg)],
                  bordercolor=[("disabled", border), ("active", accent_h)])
        style.configure("TCombobox", fieldbackground=card, background=card,
                        foreground=fg, arrowcolor=fg, bordercolor=border,
                        lightcolor=card, darkcolor=card,
                        selectbackground=card, selectforeground=fg,
                        padding=(6, 3), font=(fam, 9))
        style.map("TCombobox",
                  fieldbackground=[("readonly", card), ("disabled", bg2)],
                  foreground=[("readonly", fg), ("disabled", muted)],
                  bordercolor=[("focus", accent), ("active", accent)])

    # ---------- 首次运行 ----------
    def _ensure_first_workflow(self):
        bp_name = BP_REPO.ensure_default()
        if list_workflows():
            return
        try:
            data = json.loads(DEFAULT_WORKFLOW_JSON)
            for node in data.get("nodes", []):
                if node.get("type") == "blueprint":
                    node.setdefault("params", {})["name"] = bp_name
            wf = Workflow.from_dict(data)
            wf.name = "默认流程"
            save_workflow(wf)
        except Exception:
            traceback.print_exc()
            wf = make_default_workflow("默认流程", bp_name)
            try:
                save_workflow(wf)
            except Exception:
                traceback.print_exc()

    # ---------- 构建界面 ----------
    # ---------- 自绘窗口控制 ----------
    def _apply_native_chrome(self):
        """Windows：无边框 + 任务栏入口 + 圆角。"""
        if sys.platform != "win32":
            try:
                self.root.overrideredirect(True)
            except Exception:
                pass
            return
        try:
            geo = self.root.geometry()
            if geo.startswith("0x0") or geo.startswith("1x1"):
                geo = getattr(self, "_base_geometry", "940x444")
            if not self.root.overrideredirect():
                self.root.overrideredirect(True)
            self.root.geometry(geo)
            self.root.update_idletasks()
            u = ctypes.windll.user32
            u.GetParent.restype = ctypes.c_void_p
            u.GetParent.argtypes = [ctypes.c_void_p]
            hwnd = u.GetParent(ctypes.c_void_p(self.root.winfo_id()))
            if not hwnd:
                hwnd = self.root.winfo_id()
            self._hwnd = hwnd
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            ex = u.GetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
            u.SetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE,
                             (ex | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW)
            self._apply_round_region()
            if not getattr(self, "_chrome_ready", False):
                self._chrome_ready = True
                self.root.bind("<Configure>", self._schedule_round, add="+")
                self.root.bind(
                    "<Map>",
                    lambda e: self.root.after(60, self._apply_native_chrome),
                    add="+")
        except Exception:
            try:
                self.root.overrideredirect(True)
            except Exception:
                pass

    def _schedule_round(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        if self._round_job is not None:
            try:
                self.root.after_cancel(self._round_job)
            except Exception:
                pass
        self._round_job = self.root.after(80, self._apply_round_region)

    def _apply_round_region(self):
        self._round_job = None
        if not self._hwnd:
            return
        try:
            w = max(1, self.root.winfo_width())
            h = max(1, self.root.winfo_height())
            r = 0 if self._fullscreen else 18
            g = ctypes.windll.gdi32
            u = ctypes.windll.user32
            g.CreateRoundRectRgn.restype = ctypes.c_void_p
            rgn = g.CreateRoundRectRgn(0, 0, w + 1, h + 1, r, r)
            u.SetWindowRgn(ctypes.c_void_p(self._hwnd),
                           ctypes.c_void_p(rgn), True)
        except Exception:
            pass

    def _chrome_press(self, event):
        if self._fullscreen:
            return
        self._chrome_offset = (event.x_root - self.root.winfo_x(),
                               event.y_root - self.root.winfo_y())

    def _chrome_drag(self, event):
        if self._chrome_offset is None or self._fullscreen:
            return
        dx, dy = self._chrome_offset
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _minimize(self):
        try:
            if self._hwnd:
                ctypes.windll.user32.ShowWindow(
                    ctypes.c_void_p(self._hwnd), 6)
            else:
                self.root.iconify()
        except Exception:
            pass

    def _restore_chrome(self):
        try:
            if self.root.state() == "normal":
                self.root.overrideredirect(True)
            else:
                self.root.after(120, self._restore_chrome)
        except Exception:
            pass

    def _toggle_fullscreen(self):
        if not self._fullscreen:
            self._prev_geom = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
            self._fullscreen = True
        else:
            self.root.geometry(getattr(self, "_prev_geom", "940x444"))
            self._fullscreen = False
        if hasattr(self, "_max_btn"):
            self._max_btn.kind = "restore" if self._fullscreen else "max"
            self._max_btn._draw(self._max_btn.fg, self._max_btn.bg)

    def _exit_fullscreen(self, _event=None):
        if self._fullscreen:
            self._toggle_fullscreen()

    def build_ui(self):
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel):
                continue
            w.destroy()
        self._setup_style()
        root = self.root
        root.configure(bg=self.T("BG"))

        # 自绘标题栏：去掉系统标题栏，最小化/全屏/退出都自己画
        tb = tk.Frame(root, bg=self.T("CARD"), height=36)
        tb.pack(side="top", fill="x")
        tb.pack_propagate(False)
        tb.bind("<Button-1>", self._chrome_press)
        tb.bind("<B1-Motion>", self._chrome_drag)
        tb.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        try:
            ico = ImageTk.PhotoImage(
                Image.open(SCRIPT_DIR / "app_icon.png").resize(
                    (18, 18), Image.LANCZOS))
            self._title_icon = ico
            il = tk.Label(tb, image=ico, bg=self.T("CARD"), bd=0)
            il.pack(side="left", padx=(12, 6))
            il.bind("<Button-1>", self._chrome_press)
            il.bind("<B1-Motion>", self._chrome_drag)
            il.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        except Exception:
            pass
        name = tk.Label(tb, text=APP_NAME, bg=self.T("CARD"),
                        fg=self.T("FG"), font=(self._font_family, 10, "bold"))
        name.pack(side="left")
        name.bind("<Button-1>", self._chrome_press)
        name.bind("<B1-Motion>", self._chrome_drag)
        name.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        ver = tk.Label(tb, text=f"  {APP_VERSION}", bg=self.T("CARD"),
                       fg=self.T("MUTED"), font=(self._font_family, 8))
        ver.pack(side="left")
        ver.bind("<Button-1>", self._chrome_press)
        ver.bind("<B1-Motion>", self._chrome_drag)
        ver.bind("<Double-Button-1>", lambda e: self._toggle_fullscreen())
        tk.Label(tb, text="图纸工坊", bg=self.T("CARD"),
                 fg=self.T("MUTED"), font=(self._font_family, 8)).pack(
                     side="left", padx=(10, 0))

        IconButton(tb, "close", self.on_close, self.T("CARD"),
                   self.T("MUTED"), self.T("DANGER"), "#ffffff", size=28,
                   tip="退出").pack(side="right", padx=(0, 2), pady=4)
        self._max_btn = IconButton(
            tb, "max", self._toggle_fullscreen, self.T("CARD"),
            self.T("MUTED"), self.T("HOVER"), self.T("FG"), size=28,
            tip="全屏")
        self._max_btn.pack(side="right", padx=(0, 2), pady=4)
        IconButton(tb, "min", self._minimize, self.T("CARD"),
                   self.T("MUTED"), self.T("HOVER"), self.T("FG"), size=28,
                   tip="最小化").pack(side="right", pady=4)

        status = tk.Frame(root, bg=self.T("BG"), height=30)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        tk.Label(status, textvariable=self.status_var, bg=self.T("BG"),
                 fg=self.T("MUTED"), anchor="w",
                 font=self.F(8)).pack(side="left", padx=24, pady=6)
        tk.Label(status, text="皮肤  →  流程  →  蓝图排版  →  导出",
                 bg=self.T("BG"), fg=self.T("MUTED"), anchor="e",
                 font=self.F(8)).pack(side="right", padx=24, pady=6)

        self.hub = tk.Canvas(root, bg=self.T("BG"),
                             highlightthickness=0, bd=0)
        self.hub.pack(fill="both", expand=True)

        self.flow_combo = ttk.Combobox(
            self.hub, textvariable=self.workflow_var, state="readonly",
            postcommand=self.refresh_workflow_list, font=self.F(9))
        self.flow_combo.bind("<<ComboboxSelected>>", self._on_flow_selected)

        self.refresh_workflow_list()
        self._update_source_label()
        self.hub.bind("<Configure>", self._on_hub_configure)
        self.root.after(10, self._draw_hub)

    def rebuild_ui(self):
        self.build_ui()

    def _on_hub_configure(self, _event=None):
        if self._layout_job is not None:
            try:
                self.root.after_cancel(self._layout_job)
            except Exception:
                pass
        self._layout_job = self.root.after(16, self._draw_hub)

    # ---------- 主界面绘制 ----------
    def _hub_bind(self, name, command, normal_fill, hover_fill):
        c = self.hub
        c.tag_bind(name, "<Button-1>", lambda e: command())
        c.tag_bind(name, "<Enter>", lambda e: (
            self._hub_hover(name, hover_fill),
            c.configure(cursor="hand2")))
        c.tag_bind(name, "<Leave>", lambda e: (
            self._hub_hover(name, normal_fill),
            c.configure(cursor="arrow")))

    def _hub_hover(self, tag, target, step=0):
        if not hasattr(self, "_hub_jobs"):
            self._hub_jobs = {}
        old = self._hub_jobs.get(tag)
        if old is not None:
            try:
                self.root.after_cancel(old)
            except Exception:
                pass
        c = self.hub
        try:
            cur = c.itemcget(tag + "_bg", "fill")
        except Exception:
            return
        if step == 0:
            self._hub_from = getattr(self, "_hub_from", {})
            self._hub_from[tag] = cur
        a = self._hub_from.get(tag, cur)
        t = step / 7
        e = 1 - (1 - t) ** 2
        c.itemconfigure(tag + "_bg", fill=IconButton._mix(a, target, e))
        if step < 7:
            self._hub_jobs[tag] = self.root.after(
                18, lambda: self._hub_hover(tag, target, step + 1))

    def _draw_hub(self, _event=None):
        self._layout_job = None
        c = self.hub
        if not c.winfo_exists():
            return
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 200 or H < 160:
            return
        c.delete("all")
        T = self.T
        ACCENT = T("ACCENT")
        CARD = T("CARD")
        BORDER = T("BORDER")
        FG = T("FG")
        MUTED = T("MUTED")
        HOVER = T("HOVER")
        BG2 = T("BG2")

        # 标题
        c.create_rectangle(48, 24, 53, 47, fill=ACCENT, outline="")
        c.create_text(64, 34, text=APP_NAME, anchor="w", fill=FG,
                      font=self.F(16, "bold"))
        c.create_text(64 + self._measure(APP_NAME, "f16b") + 10, 37,
                      text=f"v{APP_VERSION}", anchor="w", fill=MUTED,
                      font=self.F(8))
        c.create_text(64, 55, text=APP_SUB, anchor="w", fill=MUTED,
                      font=self.F(8))

        # 右上：关于 / 教学文档 / 设置
        pills = [("tool_about", "关于", self.open_about),
                 ("tool_doc", "教学文档", self.open_tutorial),
                 ("tool_set", "设置",
                  lambda: open_settings_window(self))]
        right = W - 48
        for name, label, command in reversed(pills):
            pw = self._measure(label, "f9") + 30
            x = right - pw
            y = 20
            h = 30
            round_rect(c, x, y, x + pw, y + h, 15, fill=CARD,
                       outline=BORDER, tags=(name, name + "_bg"))
            c.create_text(x + pw / 2, y + h / 2, text=label, fill=FG,
                          font=self.F(9), tags=(name,))
            self._hub_bind(name, command, CARD, HOVER)
            right = x - 8

        # 分隔线
        c.create_line(48, 78, W - 48, 78, fill=BORDER)

        # 内容布局
        left_w = 330
        flow_w = 330
        gap = 84
        content_w = left_w + gap + flow_w
        x0 = max(48, (W - content_w) // 2)
        left_x = x0
        flow_x = x0 + left_w + gap
        content_h = 232
        top = max(96, 78 + (H - 78 - content_h) // 2)

        src_y = top
        src_h = 96
        edit_y = top + 112
        run_y = top + 178
        action_h = 54
        flow_y = top + 57
        flow_h = 118

        # 阴影 + 卡片
        def card(x, y, w, h, fill, outline, r=16, tags=()):
            round_rect(c, x + 2, y + 4, x + w + 2, y + h + 4, r,
                       fill=T("SHADOW"), outline="")
            return round_rect(c, x, y, x + w, y + h, r, fill=fill,
                              outline=outline, width=1.2, tags=tags)

        # 源文件
        card(left_x, src_y, left_w, src_h, CARD, BORDER, 16,
             tags=("src", "src_bg"))
        c.create_text(left_x + 18, src_y + 26, text="源文件", anchor="w",
                      fill=ACCENT, font=self.F(10, "bold"), tags=("src",))
        c.create_text(left_x + left_w - 18, src_y + 26, text="主界面优先",
                      anchor="e", fill=MUTED, font=self.F(8), tags=("src",))
        name, hint = self._source_texts()
        c.create_text(left_x + 18, src_y + 52, text=name, anchor="w",
                      fill=FG if self.source_path else MUTED,
                      font=self.F(10, "bold"), tags=("src",))
        c.create_text(left_x + 18, src_y + 72, text=hint, anchor="w",
                      fill=MUTED, font=self.F(8), tags=("src",))
        pick_x = left_x + left_w - 36
        pick_y = src_y + 58
        c.create_oval(pick_x - 16, pick_y - 16, pick_x + 16, pick_y + 16,
                      fill=BG2, outline=BORDER, tags=("pick", "pick_bg"))
        c.create_text(pick_x, pick_y - 1, text="…", fill=FG,
                      font=self.F(12, "bold"), tags=("pick",))
        self._hub_bind("pick", self.pick_source, BG2, HOVER)
        self._hub_bind("src", self.pick_source, CARD, HOVER)

        # 编辑流程 / 启动流程
        card(left_x, edit_y, left_w, action_h, CARD, BORDER, 14,
             tags=("edit", "edit_bg"))
        c.create_text(left_x + 20, edit_y + action_h / 2, text="✎", fill=FG,
                      font=self.F(11, "bold"), tags=("edit",))
        c.create_text(left_x + 44, edit_y + action_h / 2, text="编辑流程",
                      anchor="w", fill=FG, font=self.F(10, "bold"),
                      tags=("edit",))
        c.create_text(left_x + left_w - 18, edit_y + action_h / 2,
                      text="改节点和连线", anchor="e", fill=MUTED,
                      font=self.F(8), tags=("edit",))
        self._hub_bind("edit", self.open_flow_editor, CARD, HOVER)

        card(left_x, run_y, left_w, action_h, ACCENT, ACCENT, 14,
             tags=("run", "run_bg"))
        c.create_text(left_x + 20, run_y + action_h / 2, text="▶",
                      fill=T("ACCENT_FG"), font=self.F(11, "bold"),
                      tags=("run",))
        c.create_text(left_x + 44, run_y + action_h / 2, text="启动流程",
                      anchor="w", fill=T("ACCENT_FG"),
                      font=self.F(10, "bold"), tags=("run",))
        c.create_text(left_x + left_w - 18, run_y + action_h / 2,
                      text="用当前源文件跑一遍", anchor="e",
                      fill=T("ACCENT_FG"), font=self.F(8), tags=("run",))
        self._hub_bind("run", self.run_selected_flow, ACCENT,
                       T("ACCENT_HOVER"))

        # 流程卡片
        card(flow_x, flow_y, flow_w, flow_h, CARD, BORDER, 16)
        c.create_text(flow_x + 18, flow_y + 24, text="流程", anchor="w",
                      fill=ACCENT, font=self.F(10, "bold"))
        c.create_text(flow_x + flow_w - 18, flow_y + 24, text="选择要跑哪条",
                      anchor="e", fill=MUTED, font=self.F(8))
        c.create_window(flow_x + 16, flow_y + 40,
                        window=self.flow_combo, anchor="nw",
                        width=flow_w - 92, height=30)
        plus_x = flow_x + flow_w - 46
        plus_y = flow_y + 55
        c.create_oval(plus_x - 15, plus_y - 15, plus_x + 15, plus_y + 15,
                      fill=BG2, outline=BORDER, tags=("plus", "plus_bg"))
        c.create_text(plus_x, plus_y - 1, text="+", fill=FG,
                      font=self.F(12, "bold"), tags=("plus",))
        self._hub_bind("plus", self.new_workflow, BG2, HOVER)
        c.create_text(flow_x + 18, flow_y + 92,
                      text=self._fit(self.flow_hint_var.get(),
                                     flow_w - 36, "f8"),
                      anchor="w", fill=MUTED, font=self.F(8))

        # 流程卡片下面的两个工具
        tools_y = flow_y + flow_h + 10
        gap2 = 10
        bw = (flow_w - gap2) / 2
        for i, (name, label, command) in enumerate((
                ("tool_bp", "蓝图编辑器", self.open_blueprint_editor),
                ("tool_am", "资源管理器", self.open_asset_manager))):
            bx = flow_x + i * (bw + gap2)
            round_rect(c, bx, tools_y, bx + bw, tools_y + 36, 12,
                       fill=CARD, outline=BORDER,
                       tags=(name, name + "_bg"))
            c.create_text(bx + bw / 2, tools_y + 18, text=label, fill=FG,
                          font=self.F(9), tags=(name,))
            self._hub_bind(name, command, CARD, HOVER)

        # 曲线：源文件 / 编辑 / 启动 → 流程
        ports = [(flow_x - 6, flow_y + 30, T("PORT_IMG")),
                 (flow_x - 6, flow_y + 59, T("PORT_TXT")),
                 (flow_x - 6, flow_y + 88, T("OK"))]
        starts = [(left_x + left_w, src_y + 48),
                  (left_x + left_w, edit_y + action_h / 2),
                  (left_x + left_w, run_y + action_h / 2)]
        for (x1, y1), (x2, y2, color) in zip(starts, ports):
            c.create_line(*curve_points(x1, y1, x2, y2), smooth=True,
                          width=2, fill=color)
            c.create_oval(x2 - 4, y2 - 4, x2 + 4, y2 + 4, fill=T("BG"),
                          outline=color, width=2)
            c.create_oval(x1 - 4, y1 - 4, x1 + 4, y1 + 4, fill=T("BG"),
                          outline=color, width=2)

    def _source_texts(self):
        if self.source_path is None:
            return self._fit("未选择皮肤", 240, "f10"), self._fit(
                "点右边 … 选一个 PNG，或直接用流程里的源文件节点", 238, "f8")
        name = self.source_path.name
        return (self._fit(name, 240, "f10"),
                self._fit("点右边 … 换一个", 238, "f8"))

    # ---------- 源文件 ----------
    def pick_source(self):
        path = filedialog.askopenfilename(
            title="选择 Minecraft 皮肤",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
            parent=self.root)
        if not path:
            return
        try:
            load_rgba(path)
        except Exception as exc:
            messagebox.showerror("打不开", f"这个文件读不了：\n{exc}",
                                 parent=self.root)
            return
        self.source_path = Path(path)
        self.settings["last_source"] = path
        self._update_source_label()
        self._save_settings()
        self._draw_hub()
        self.toast(f"源文件：{Path(path).name}")

    def _update_source_label(self):
        if self.source_path is None:
            self.source_var.set("未选择皮肤")
        else:
            self.source_var.set(self.source_path.name)

    # ---------- 流程列表 ----------
    def refresh_workflow_list(self):
        names = list_workflows()
        try:
            self.flow_combo["values"] = names
        except Exception:
            return
        current = self.workflow_var.get()
        if current not in names:
            preferred = self.settings.get("last_flow", "")
            if preferred in names:
                current = preferred
            else:
                current = names[0] if names else ""
            self.workflow_var.set(current)
        self._update_flow_hint()
        if hasattr(self, "hub") and self.hub.winfo_exists():
            self._draw_hub()

    def _update_flow_hint(self):
        name = self.workflow_var.get()
        if not name:
            self.flow_hint_var.set("还没有流程，点“编辑流程”新建")
            return
        wf = load_workflow(name)
        count = len(wf.nodes) if wf is not None else 0
        self.flow_hint_var.set(f"{count} 个节点 · {name}.json")

    def _on_flow_selected(self, _event=None):
        self.settings["last_flow"] = self.workflow_var.get()
        self._save_settings()
        self._update_flow_hint()
        self._draw_hub()

    # ---------- 打开编辑器 ----------
    def open_flow_editor(self):
        name = self.workflow_var.get()
        if not name:
            self.new_workflow()
            return
        editor = FlowEditor(self, name)
        self.wait_window(editor)
        self.refresh_workflow_list()
        self._update_flow_hint()
        self._draw_hub()

    def new_workflow(self):
        name = simpledialog.askstring("新建流程", "流程名称：", parent=self.root)
        if not name:
            return
        name = sanitize_name(name)
        if not name:
            return
        if (WORKFLOWS_DIR / f"{name}.json").exists():
            messagebox.showwarning("已存在", f"流程 {name} 已经存在。",
                                   parent=self.root)
            return
        bp_name = BP_REPO.ensure_default()
        wf = make_default_workflow(name, bp_name)
        try:
            save_workflow(wf)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=self.root)
            return
        self.refresh_workflow_list()
        self.workflow_var.set(name)
        self.settings["last_flow"] = name
        self._save_settings()
        editor = FlowEditor(self, name)
        self.wait_window(editor)
        self.refresh_workflow_list()

    def run_selected_flow(self):
        if self._running:
            return
        name = self.workflow_var.get()
        if not name:
            messagebox.showinfo("提示", "还没有流程，先点“编辑流程”新建一个。",
                                parent=self.root)
            return
        wf = load_workflow(name)
        if wf is None:
            messagebox.showerror("读取失败", f"打不开流程：{name}",
                                 parent=self.root)
            return
        self._running = True
        runner = None
        ok = False
        try:
            runner = FlowRunner(self, wf, self.root,
                                main_source=self.source_path, status=self.toast)
            ok = runner.run()
        except Exception as exc:
            traceback.print_exc()
            messagebox.showerror("执行失败", str(exc), parent=self.root)
        finally:
            self._running = False
        if ok:
            if runner.skipped_nodes:
                self.toast(f"完成（跳过 {runner.skipped_nodes} 个没连线的节点）")
            elif runner.exported:
                self.toast(f"完成：导出 {len(runner.exported)} 张")
            else:
                messagebox.showinfo("完成", f"流程“{name}”执行完了。",
                                    parent=self.root)
        else:
            self.toast("流程已中止")

    def open_about(self):
        T = self.T
        win = tk.Toplevel(self.root)
        win.title(f"关于 {APP_NAME}")
        win.configure(bg=T("BG"))
        center_window(win, 540, 480)
        win.transient(self.root)
        win.resizable(False, False)

        head = tk.Frame(win, bg=T("BG"))
        head.pack(fill="x", padx=30, pady=(26, 0))
        tk.Label(head, text=APP_NAME, bg=T("BG"), fg=T("FG"),
                 font=self.F(26, "bold")).pack(side="left")
        tk.Label(head, text=f"v{APP_VERSION}", bg=T("BG"), fg=T("MUTED"),
                 font=self.F(9)).pack(side="left", padx=(10, 0), pady=(10, 0))
        tk.Label(win, text="图纸工坊", bg=T("BG"), fg=T("ACCENT"),
                 font=self.F(11, "bold"), anchor="w").pack(
                     fill="x", padx=30, pady=(2, 0))
        tk.Label(win, text="Blueprint Layout & Usage Engine",
                 bg=T("BG"), fg=T("MUTED"), font=self.F(9),
                 anchor="w").pack(fill="x", padx=30)

        card = tk.Frame(win, bg=T("CARD"), highlightthickness=1,
                        highlightbackground=T("BORDER"))
        card.pack(fill="x", padx=30, pady=18)
        rows = [
            ("作者", APP_AUTHOR),
            ("开发", "用 DeepSeek 开发的免费项目"),
            ("交流", f"QQ {APP_QQ}（欢迎商讨）"),
            ("本次耗费", f"¥{APP_COST}"),
            ("版本", APP_VERSION),
        ]
        for i, (key, value) in enumerate(rows):
            row = tk.Frame(card, bg=T("CARD"))
            top = 12 if i == 0 else 6
            bottom = 12 if i == len(rows) - 1 else 0
            row.pack(fill="x", padx=16, pady=(top, bottom))
            tk.Label(row, text=key, bg=T("CARD"), fg=T("MUTED"),
                     font=self.F(9), width=10, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=T("CARD"), fg=T("FG"),
                     font=self.F(9), anchor="w", justify="left",
                     wraplength=350).pack(side="left")

        tk.Label(win, text="免费使用，欢迎交流；请勿倒卖。",
                 bg=T("BG"), fg=T("MUTED"), font=self.F(8)).pack()

        row = tk.Frame(win, bg=T("BG"))
        row.pack(side="bottom", fill="x", padx=30, pady=20)

        def copy_qq():
            win.clipboard_clear()
            win.clipboard_append(APP_QQ)
            self.toast("QQ 已复制")

        ttk.Button(row, text="关闭", command=win.destroy).pack(side="right")
        ttk.Button(row, text="复制 QQ", command=copy_qq).pack(
            side="right", padx=(0, 8))

    def open_tutorial(self):
        T = self.T
        win = tk.Toplevel(self.root)
        win.title(f"教学文档 — {APP_NAME} {APP_VERSION}")
        win.configure(bg=T("BG"))
        center_window(win, 940, 720)
        win.transient(self.root)

        head = tk.Frame(win, bg=T("BG"))
        head.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(head, text="教学文档", bg=T("BG"), fg=T("FG"),
                 font=self.F(18, "bold")).pack(side="left")
        tk.Label(head, text=f"{APP_NAME} {APP_VERSION}", bg=T("BG"),
                 fg=T("MUTED"), font=self.F(9)).pack(side="left",
                                                     padx=(10, 0))
        ttk.Button(head, text="关闭", command=win.destroy).pack(side="right")

        body = tk.Frame(win, bg=T("BG"))
        body.pack(fill="both", expand=True, padx=24, pady=(0, 18))
        scroll = SlimScrollbar(body, command=lambda *a: None,
                               bg=T("BG"), thumb=T("BORDER"),
                               hover=T("ACCENT"))
        scroll.pack(side="right", fill="y")
        text = tk.Text(body, bg=T("CARD"), fg=T("FG"), relief="flat",
                       wrap="word", padx=26, pady=18, bd=0,
                       highlightthickness=1, highlightbackground=T("BORDER"),
                       font=self.F(10), yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.command = text.yview

        text.tag_configure("h1", font=self.F(17, "bold"),
                           foreground=T("ACCENT"), spacing1=18, spacing3=8)
        text.tag_configure("h2", font=self.F(12, "bold"),
                           foreground=T("FG"), spacing1=16, spacing3=4)
        text.tag_configure("body", font=self.F(10), spacing3=5,
                           lmargin1=4, lmargin2=4)
        text.tag_configure("bullet", font=self.F(10), spacing3=3,
                           lmargin1=18, lmargin2=32)
        text.tag_configure("mono", font=("Consolas", 9),
                           background=T("BG2"), lmargin1=18, lmargin2=18,
                           spacing1=4, spacing3=10)
        text.tag_configure("note", font=self.F(9), foreground=T("MUTED"),
                           spacing3=4, lmargin1=4, lmargin2=4)

        self._fill_tutorial(text)
        text.configure(state="disabled")
        text.see("1.0")

    def _fill_tutorial(self, text):
        def h1(s):
            text.insert("end", s + "\n", ("h1",))

        def h2(s):
            text.insert("end", s + "\n", ("h2",))

        def p(s):
            text.insert("end", s + "\n", ("body",))

        def b(s):
            text.insert("end", "· " + s + "\n", ("bullet",))

        def mono(s):
            text.insert("end", s.strip("\n") + "\n", ("mono",))

        def note(s):
            text.insert("end", s + "\n", ("note",))

        h1("BLUE 是什么")
        p("BLUE 是一个“图纸”工具：你先创建图纸（输入、选区、画布、映射、"
          "Result 命名），再在流程里使用图纸，把皮肤图合成、拆组、改名、导出。"
          "图纸可以保存、打开、分享；流程只是决定这次怎么用图纸。")
        note("BLUE = Blueprint Layout & Usage Engine（图纸工坊）。"
             "当前版本 " + APP_VERSION + "。")

        h1("30 秒上手")
        p("1. 主界面点「源文件」右边的 …，选一张皮肤 PNG。")
        p("2. 在「流程」下拉里选一条流程（第一次用就用「默认流程」）。")
        p("3. 点「启动流程」。")
        p("4. 遇到暂停：询问模式填名字，提示模式点继续；有图的暂停会把图放到 "
          "临时/ 里，可以先改再继续（见下面「暂停修改图片」）。")
        p("5. 跑完去 程序目录/导出/<文件夹名>/ 拿图。")

        h1("主界面")
        b("源文件：选皮肤 PNG。选了之后，流程里「源文件」节点留空也会优先用它。")
        b("编辑流程：打开流程编辑器。")
        b("启动流程：按当前流程跑一遍。")
        b("流程下拉 + 右边的 +：切换 / 新建流程。")
        b("流程卡片下面是「蓝图编辑器」和「资源管理器」。")
        b("右上角是「关于」「教学文档」「设置」。默认浅色主题，设置里可切深色。")

        h1("流程编辑器")
        p("曲线连接、带类型端口的节点图。只有从起点能连到的节点才会执行，"
          "画布外孤立的节点不会弹窗、不会导出。")
        h2("鼠标与快捷键")
        b("中键拖动 = 平移整个网格。")
        b("左键单击 = 选中；左键拖空白 = 框选多选。")
        b("左键拖节点 = 移动；多选时拖任意一个会整组移动。")
        b("Ctrl + 左键 = 加选 / 取消选中；Delete = 删除选中的节点。")
        b("滚轮 = 缩放；右键空白 = 添加节点的菜单；右键节点 = 跳过 / 删除。")
        b("Alt + 左键点端口圆点 = 删掉这个端口上的线。")

        h2("节点")
        mono("""源文件     → 整张皮肤原图
暂停       → 继续 / 回答；有图时把当前图写到 临时/ 供修改
蓝图       → 每个有效 Result 一个输出 + 一个图组输出
Make 合并  → 多个输入（1~16）合成一个图组
Break 拆分 → 一个图组拆成多张图，输出数量自动
放大       → 像素放大 N 倍
重命名     → 按模板改名字，可接自己的 Text
导出       → 按文件夹名 + 图片自己的名字写文件""")
        p("蓝图节点的高度会随 Result 数量变化；Make / Break 的高度随端口数量变化。")
        p("「跳过」对普通节点是透传；Make / Break 是结构节点，勾了跳过仍会执行。")

        h2("Make / Break 怎么用")
        b("Make：参数里设「输入数量」（1~16），节点会长出 图像1…图像N。"
          "每个输入可以接一张图，也可以接一个组；没连的输入直接跳过，"
          "不会拿源文件顶替。")
        b("Break：接一个图组，输出点数量自动跟着上游算——蓝图图组按 Result 数、"
          "Make 按实际连上的图片数、单张图就是 1 个。")
        b("典型用法一：蓝图 3 个 Result，把 result1 + result2 用 Make 合成组再导出。")
        b("典型用法二：蓝图图组接到 Break，拆开后每张图分别接重命名 / 放大 / 导出。")
        b("Break 的输出数会在连线、打开流程、刷新蓝图端口和运行前重新同步；"
          "上游变少时多出来的线会被清掉。最多 64 个输出点。")

        h2("暂停修改图片")
        p("暂停节点接了图像输入后，暂停时会把当前图（一张或一个图组）写到：")
        mono("临时/暂停_<流程名>_<节点号>_<时间>/01_名字.png")
        b("节点参数里勾「自动打开」，暂停时会自动弹出这个文件夹；"
          "对话框里也有「打开文件夹」按钮。")
        b("用画图 / PS 改这些 PNG，改完点「继续」，程序会按文件名顺序读回来，"
          "后面的节点用的就是改过的图。")
        b("不勾「自动打开」也会落盘，只是不弹文件夹。")
        b("没有接图像输入的暂停（纯文字询问）不会建文件夹。")
        b("临时/ 里的文件不会自动删，确认没用了可以手动清。")

        h2("暂停的 Text")
        p("暂停（询问模式）的「回答」是一个文本输出，接给谁，谁就能用 {Text}。"
          "重命名、蓝图、导出各有自己的 Text 输入：接哪个暂停，就用哪一次的回答；"
          "不接就是空，不会去拿别的暂停的回答。")
        mono("""暂停 A「回答」→ 重命名 1（{Text}_头部）
暂停 B「回答」→ 重命名 2（{Text}_眼睛）""")

        h2("导出节点")
        b("「文件夹名」输入 = 导出的文件夹名。不接就用皮肤文件名。")
        b("图片文件名用图片自己的名字（蓝图 Result 的命名模板）。")
        b("「命名模式」留空即可；写了会覆盖图片自己的名字。")
        b("同名默认跳过，勾「同名覆盖」才会覆盖。")

        h1("蓝图编辑器")
        p("左边是节点区：输入（示例图）→ 画布 → Result；矩形节点也连到画布。"
          "右边上面是输入与选区，下面是画布 / 矩形 / Result 的属性。")
        h2("输入与选区")
        b("输入是一张示例图，只用于设计时拉框参照，运行时不参与。")
        b("在示例图上按住拖 = 新建选区；按住已有选区拖动；拖右下角改大小。")
        b("选区坐标吸附到整数像素；自动命名 选区1、选区2……，可以改名，"
          "也能直接输入 X / Y / W / H。")
        b("顶部「放大」把示例图铺满屏幕来拉框，滚轮缩放、中键拖动，Esc 关闭。")
        h2("画布与映射")
        b("画布尺寸由你输入，单位是像素。")
        b("「素材」下拉里会列出：连到画布上的输入图选区 + 连到画布上的矩形节点里的矩形。")
        b("「添加映射」把素材贴到 (0,0)，然后在画布预览里拖动摆位置；X / Y 也能手输。")
        b("映射列表的顺序就是叠放顺序（后面的盖住前面的），可以拖动排序或用 ↑ ↓。")
        b("画布区右上角「放大编辑」把画布铺满屏幕，方便摆位。")
        h2("矩形节点")
        b("右键空白 → 添加：矩形。节点里可以放多个矩形，每个有名称、宽、高、颜色。")
        b("矩形节点用橙色端口连到画布，之后就能在画布的「素材」里选到它。")
        b("矩形可以当底色、边框、色块；映射顺序和选区共用。")
        h2("Result")
        b("一个 Result 只接一个画布；N 个有效 Result = 流程里 N 个输出点 + 一个图组。")
        b("命名模板写在 Result 上，导出 / 重命名时按这个模板起名。")

        h2("Result 命名变量")
        p("公用（整次运行 / 整个蓝图节点）：")
        b("Skin：皮肤文件名；Time：202610310303；Date：20261031。")
        b("Text：这个蓝图节点「字符」输入的文字；同一个蓝图节点下所有 Result 共用。")
        p("私有（每个 Result 自己算）：")
        b("L / W：这个 Result 对应画布的像素宽 / 高；要厘米就自己乘，"
          "例如 {L*3.75}cm。")
        b("Canvas / Name：这个 Result 接的画布名；Result：Result 名；"
          "Index：第几个 Result（从 1 开始）。")
        p("写法：")
        mono("""{Skin}{"_"}{L}{"x"}{W}
{Skin}_{Result}_{L}x{W}
{Text}{"_"}{W*6.1875}{"cm"}""")
        b("可以用 + - * / %、括号，以及 round / int / floor / ceil / abs / str / "
          "upper / lower / max / min。")
        b('字符串用 "cm" 或中文引号 “cm”；{_} 这种纯符号块直接当字面量。')
        b("小写别名 {text}、{skin}、{canvas}、{result}、{index} 也能用；"
          "中文别名 {长}、{宽}、{时间}、{文字} 也可以。")

        h2("全屏编辑")
        p("示例图和画布都能全屏编辑：左边大图，右边保留列表、坐标、宽高、颜色等属性。"
          "滚轮缩放、中键拖动画面，Esc 关闭后自动同步回蓝图。")

        h1("导出规则")
        b("导出节点的「文件夹名」输入 = 文件夹；不接 = 皮肤文件名。")
        b("设了「导出根目录」：<根目录>/<文件夹名>/；没设就是 程序目录/导出/<文件夹名>/。")
        b("图片文件名用图片自己的 Result 命名；同名时第二张会加它来自的 Result 名做前缀。")
        b("命名模式留空即可；写了 {Result}、{L}、{Text} 等可以临时覆盖文件名。")
        b("设置里勾「填充颜色」会把透明区域压到所选背景色；默认保留透明。")

        h1("分享与打开")
        b("流程编辑器、蓝图编辑器都有「打开…」：选别人分享的 JSON，"
          "导入到 workflows/ 或 blueprints/ 并直接打开；重名会让你改名。")
        b("「目录」直接打开对应文件夹，方便拿文件分享。")
        b("蓝图 JSON 里的示例图是可选的；分享时没带示例图也能正常运行，"
          "只是设计时没有参照图。")
        b("分享流程时，记得把流程里用到的蓝图 JSON 也一起发。")

        h1("设置")
        b("主题：浅色 / 深色。")
        b("填充颜色：导出时把透明区域压到指定颜色；默认不填充，保留透明。")
        b("设置保存在 skin_head_settings.json。")

        h1("常见问题")
        h2("暂停问了两次 / 孤立节点也执行？")
        p("只有从起点连得到的节点会执行；画布外孤立的暂停不会执行。"
          "如果确实有两个暂停连在线上，就会各问一次。")
        h2("暂停后找不到图片文件？")
        p("暂停本身不直接写 导出/；有图输入的暂停会把图写到 临时/暂停_…/，"
          "点继续后流程继续往导出走，导出节点执行后才会在 导出/ 下出现文件。")
        h2("导出没有文件？")
        p("检查：导出节点是否连在暂停后面、是否点了继续（不是取消）、"
          "导出节点是否报错、命名是否被同名跳过。")
        h2("文件名后面多了 result2_？")
        p("两个 Result 的命名模板撞名了，程序给第二张加了它来自的 Result 名前缀。"
          "把模板改成带 {Result} 或 {Index} 就能区分。")
        h2("蓝图节点没有输出点？")
        p("蓝图里需要至少一个有效 Result（接了画布、有映射），"
          "然后打开流程或点「刷新蓝图端口」。")
        h2("Break 的输出数量和想的不一样？")
        p("Break 跟着上游实际会带几张图算：蓝图图组按 Result 数、Make 按实际连上的"
          "图片数、单张图 = 1。改完蓝图或 Make 后点「刷新蓝图端口」，或重新打开流程。")
        h2("旧流程重命名里的 {Text} 变空了？")
        p("重命名的 Text 现在只取接在它自己 Text 口上的暂停回答；"
          "把对应暂停的「回答」连到重命名的 Text 口即可。")
        h2("临时/ 和 导出/ 在哪？")
        p("都在程序目录（exe 所在目录，或脚本所在目录）。")

        h1("关于")
        p(f"{APP_NAME} {APP_VERSION} · 图纸工坊")
        p(f"作者：{APP_AUTHOR}")
        p(f"开发：用 DeepSeek 开发的免费项目；交流 QQ {APP_QQ}。")
        p(f"本次开发耗费：¥{APP_COST}。免费使用，欢迎交流，请勿倒卖。")

    def open_blueprint_editor(self):
        editor = BlueprintEditor(self)
        self.wait_window(editor)
        self.toast("蓝图编辑器已关闭")

    def open_asset_manager(self):
        AssetManager(self)

    def on_close(self):
        self._save_settings()
        try:
            self.root.destroy()
        except Exception:
            pass



# ====================================================================
# 入口
# ====================================================================

def main():
    root = tk.Tk()
    app = SkinHeadApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()







































