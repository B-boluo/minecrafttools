import re
import tkinter as tk
from tkinter import Scrollbar, Canvas, font
import json
import os
import atexit
from ctypes import windll
import math
import ctypes
import sys

# ========== 单实例互斥体 ==========
MUTEX_NAME = "MC_Coord_Converter_SingleInstance"
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
if mutex == 0:
    ctypes.windll.user32.MessageBoxW(0, "无法创建互斥体", "错误", 0)
    sys.exit(1)
if ctypes.windll.kernel32.GetLastError() == 183:
    # ★★★ 修改1：窗口标题改为 "AAtexts" ★★★
    hwnd = ctypes.windll.user32.FindWindowW(None, "AAtexts")
    if hwnd:
        if ctypes.windll.user32.IsIconic(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, 9)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    sys.exit(0)

# ========== DPI 缩放处理 ==========
windll.shcore.SetProcessDpiAwareness(1)
scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

# ========== 数据持久化 ==========
SAVE_FILE = "mc_coords_history.json"

def load_history():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [{"note": item["note"], "ow": tuple(item["ow"]), "net": tuple(item["net"])} for item in data]
        except:
            return []
    return []

def save_history():
    data = [{"note": item["note"], "ow": list(item["ow"]), "net": list(item["net"])} for item in history]
    try:
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

atexit.register(save_history)

# ========== 核心解析 ==========
def parse_full_cmd(cmd):
    cmd = cmd.strip()
    pattern = r'/execute in (minecraft:\w+) run tp @s ([\d.-]+) ([\d.-]+) ([\d.-]+) ([\d.-]+) ([\d.-]+)'
    m = re.match(pattern, cmd)
    if not m:
        return None
    dim = m.group(1)
    x, y, z, _, _ = map(float, m.groups()[1:])
    matched_str = m.group(0)
    remainder = cmd[len(matched_str):].strip()
    note = remainder if remainder else ""
    return dim, x, y, z, note

def parse_manual_input(text):
    text = text.strip()
    pattern = r'^([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)(?:\s+(.*))?$'
    m = re.match(pattern, text)
    if not m:
        return None
    x = float(m.group(1))
    y = float(m.group(2))
    z = float(m.group(3))
    note = m.group(4) if m.group(4) is not None else ""
    return x, y, z, note

def convert(dim, x, y, z):
    if dim in ("minecraft:overworld", "主世界"):
        return (x, y, z), (x/8, y, z/8)
    elif dim in ("minecraft:the_nether", "下界"):
        return (x*8, y, z*8), (x, y, z)
    else:
        return None

def fmt_int(t):
    return f"{round(t[0])} ~ {round(t[2])}"

# ========== GUI ==========
root = tk.Tk()
# ★★★ 修改2：窗口标题改为 "AAtexts" ★★★
root.title("AAtexts")

BASE_WIDTH = 280
window_width = int(BASE_WIDTH * scale_factor)
root.geometry(f"{window_width}x200")
root.resizable(False, False)

BG_COLOR = "white"
FG_COLOR = "black"
SEP_COLOR = "#CCCCCC"

FONT_FAMILY = "微软雅黑"
BASE_FONT_SIZE = 7
BASE_HEADER_SIZE = 6
BASE_BUTTON_SIZE = 6

FONT_SIZE = max(6, math.ceil(BASE_FONT_SIZE * scale_factor))
HEADER_SIZE = max(6, math.ceil(BASE_HEADER_SIZE * scale_factor))
BUTTON_SIZE = max(6, math.ceil(BASE_BUTTON_SIZE * scale_factor))

FONT = (FONT_FAMILY, FONT_SIZE, "normal")
FONT_BUTTON = (FONT_FAMILY, BUTTON_SIZE, "normal")
FONT_HEADER = (FONT_FAMILY, HEADER_SIZE, "normal")

root.configure(bg=BG_COLOR)

font_obj = font.Font(family=FONT_FAMILY, size=FONT_SIZE)
font_header_obj = font.Font(family=FONT_FAMILY, size=HEADER_SIZE)

# ---------- 最大输入长度 ----------
REF_STRING = "/execute in minecraft:the_nether run tp @s 100005.08 192.20 100006.81 -6.17 57.25"
MAX_INPUT_LEN = len(REF_STRING) + 10

# ---------- 历史数据 ----------
history = load_history()

# ---------- 刷新显示 ----------
def refresh_display():
    for widget in inner_frame.winfo_children():
        widget.destroy()

    del_btn_width = int(32 * scale_factor)

    # 计算各列最大宽度（备注完整显示）
    max_ow_width = 0
    max_net_width = 0
    max_note_width = 0
    for text in ("备注", "主世界", "下界"):
        w = font_header_obj.measure(text)
        if text == "备注":
            max_note_width = max(max_note_width, w)
        elif text == "主世界":
            max_ow_width = max(max_ow_width, w)
        elif text == "下界":
            max_net_width = max(max_net_width, w)

    for rec in history:
        note = rec["note"] if rec["note"] else "-"
        ow_str = fmt_int(rec["ow"])
        net_str = fmt_int(rec["net"])
        max_note_width = max(max_note_width, font_obj.measure(note))
        max_ow_width = max(max_ow_width, font_obj.measure(ow_str))
        max_net_width = max(max_net_width, font_obj.measure(net_str))

    PAD = int(8 * scale_factor)
    col_widths = [
        max_note_width + PAD,
        max_ow_width + PAD,
        max_net_width + PAD
    ]
    total_content_width = sum(col_widths) + del_btn_width + int(6 * scale_factor)
    inner_frame.config(width=total_content_width)

    # 表头
    header_frame = tk.Frame(inner_frame, bg=BG_COLOR)
    header_frame.pack(fill="x", pady=0)
    headers = ("备注", "主世界", "下界")
    for i, text in enumerate(headers):
        label = tk.Label(header_frame, text=text, font=FONT_HEADER, anchor="w",
                         fg=FG_COLOR, bg=BG_COLOR, borderwidth=0, highlightthickness=0)
        label.grid(row=0, column=i, padx=int(2 * scale_factor), pady=0, sticky="w")
        header_frame.columnconfigure(i, weight=0, minsize=col_widths[i])
    dummy = tk.Label(header_frame, text="", width=2, bg=BG_COLOR, borderwidth=0)
    dummy.grid(row=0, column=len(headers), padx=int(2 * scale_factor), pady=0, sticky="e")
    header_frame.columnconfigure(len(headers), minsize=del_btn_width)

    if not history:
        lbl = tk.Label(inner_frame, text="无记录", font=FONT, fg="gray", bg=BG_COLOR)
        lbl.pack(pady=int(10 * scale_factor))
        # 更新画布并调整高度
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        root.after(10, adjust_window_height)
        return

    for idx, rec in enumerate(history):
        if idx > 0:
            sep = tk.Frame(inner_frame, height=1, bg=SEP_COLOR)
            sep.pack(fill="x", pady=0)

        note = rec["note"] if rec["note"] else "-"
        ow_str = fmt_int(rec["ow"])
        net_str = fmt_int(rec["net"])
        row_data = (note, ow_str, net_str)

        row_frame = tk.Frame(inner_frame, bg=BG_COLOR)
        row_frame.pack(fill="x", pady=0)
        for i, text in enumerate(row_data):
            label = tk.Label(row_frame, text=text, font=FONT, anchor="w",
                             fg=FG_COLOR, bg=BG_COLOR, borderwidth=0, highlightthickness=0)
            label.grid(row=0, column=i, padx=int(2 * scale_factor), pady=0, sticky="w")
            row_frame.columnconfigure(i, weight=0, minsize=col_widths[i])
        btn = tk.Button(row_frame, text="×", font=FONT_BUTTON, width=2,
                        command=lambda i=idx: delete_record(i),
                        fg=FG_COLOR, bg="#DDDDDD", activebackground="#CCCCCC",
                        borderwidth=0, highlightthickness=0)
        btn.grid(row=0, column=len(headers), padx=int(2 * scale_factor), pady=0, sticky="e")
        row_frame.columnconfigure(len(headers), minsize=del_btn_width)

    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    root.after(10, adjust_window_height)

def adjust_window_height():
    """根据内容自适应窗口高度（无纵向滚动条）"""
    root.update_idletasks()
    # 获取inner_frame的实际高度
    inner_h = inner_frame.winfo_height()
    # 获取顶部部件的高度
    top_h = top_frame.winfo_height()
    dim_h = dim_frame.winfo_height()
    # 获取水平滚动条的高度
    h_scroll_h = h_scroll.winfo_height()

    # ★★★ 核心修复：设置Canvas高度等于内容高度，使所有行可见 ★★★
    canvas.config(height=inner_h)

    # 边距
    pad_top = int(3 * scale_factor)
    pad_bottom = int(2 * scale_factor)
    # 总高度 = 顶部frame + 单选frame + canvas_frame（包含inner_h + 滚动条高度） + 边距
    total_h = top_h + dim_h + inner_h + h_scroll_h + pad_top + pad_bottom + 20  # 额外余量
    if total_h < 150:
        total_h = 150
    root.geometry(f"{window_width}x{int(total_h)}")

def delete_record(idx):
    if 0 <= idx < len(history):
        del history[idx]
        save_history()
        refresh_display()

# ---------- 主容器 ----------
root.pack_propagate(0)

# 第一行：输入框 + ✔ 按钮
top_frame = tk.Frame(root, bg=BG_COLOR)
top_frame.pack(side="top", pady=int(3 * scale_factor), fill="x", padx=int(3 * scale_factor))

entry_input = tk.Entry(top_frame, font=FONT, fg=FG_COLOR, bg="white",
                       insertbackground=FG_COLOR, relief="flat")
entry_input.pack(side="left", fill="x", expand=True, padx=(0, int(2 * scale_factor)))
entry_input.delete(0, tk.END)

def truncate_input():
    current = entry_input.get()
    if len(current) > MAX_INPUT_LEN:
        root.after_idle(lambda: entry_input.delete(MAX_INPUT_LEN, tk.END))

def on_key_release(event):
    truncate_input()
    update_radio_state()

def on_paste(event):
    try:
        clipboard = root.clipboard_get()
    except:
        return "break"
    if len(clipboard) > MAX_INPUT_LEN:
        clipboard = clipboard[:MAX_INPUT_LEN]
    entry_input.delete(0, tk.END)
    entry_input.insert(0, clipboard)
    update_radio_state()
    return "break"

entry_input.bind("<KeyRelease>", on_key_release)
entry_input.bind("<<Paste>>", on_paste)
entry_input.bind("<Control-v>", on_paste)
entry_input.bind("<Control-V>", on_paste)

btn_convert = tk.Button(top_frame, text="✔", font=FONT_BUTTON, width=3,
                        fg=FG_COLOR, bg="#DDDDDD", activebackground="#CCCCCC")
btn_convert.pack(side="left")

# 第二行：维度单选按钮
dim_frame = tk.Frame(root, bg=BG_COLOR)
dim_frame.pack(side="top", pady=int(2 * scale_factor), anchor="center")

dim_var = tk.StringVar(value="主世界")

rb_overworld = tk.Radiobutton(dim_frame, text="主世界", variable=dim_var, value="主世界",
                              font=FONT, fg=FG_COLOR, bg=BG_COLOR, selectcolor="lightblue",
                              activebackground=BG_COLOR, relief="flat")
rb_overworld.pack(side="left", padx=int(2 * scale_factor))

rb_nether = tk.Radiobutton(dim_frame, text="下界", variable=dim_var, value="下界",
                           font=FONT, fg=FG_COLOR, bg=BG_COLOR, selectcolor="lightcoral",
                           activebackground=BG_COLOR, relief="flat")
rb_nether.pack(side="left", padx=int(2 * scale_factor))

# 第三行：仅水平滚动区域（无纵向滚动条）
canvas_frame = tk.Frame(root, bg=BG_COLOR)
canvas_frame.pack(side="top", fill="x", padx=int(3 * scale_factor), pady=int(2 * scale_factor))

canvas = Canvas(canvas_frame, bg=BG_COLOR, highlightthickness=0)
h_scroll = Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
canvas.configure(xscrollcommand=h_scroll.set)

h_scroll.pack(side="bottom", fill="x")
canvas.pack(side="left", fill="x")

inner_frame = tk.Frame(canvas, bg=BG_COLOR)
canvas.create_window((0, 0), window=inner_frame, anchor="nw")

# 水平滚动绑定 Shift+滚轮
def on_shift_mousewheel(event):
    if event.delta:
        canvas.xview_scroll(int(-event.delta / abs(event.delta)), "units")
    elif event.num == 4:
        canvas.xview_scroll(-1, "units")
    elif event.num == 5:
        canvas.xview_scroll(1, "units")

canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
canvas.bind("<Shift-Button-4>", on_shift_mousewheel)
canvas.bind("<Shift-Button-5>", on_shift_mousewheel)

# ---------- 动态启用/禁用单选按钮 ----------
def update_radio_state(event=None):
    text = entry_input.get().strip()
    manual = parse_manual_input(text)
    if manual is not None:
        rb_overworld.config(state="normal")
        rb_nether.config(state="normal")
    else:
        rb_overworld.config(state="disabled")
        rb_nether.config(state="disabled")

update_radio_state()

# ---------- 换算函数 ----------
def do_convert():
    text = entry_input.get().strip()
    if not text:
        return
    parsed = parse_full_cmd(text)
    if parsed:
        dim, x, y, z, note = parsed
        result = convert(dim, x, y, z)
        if result:
            ow, net = result
            history.append({"note": note, "ow": ow, "net": net})
            save_history()
            refresh_display()
            return
    parsed = parse_manual_input(text)
    if parsed:
        x, y, z, note = parsed
        dim = dim_var.get()
        result = convert(dim, x, y, z)
        if result:
            ow, net = result
            history.append({"note": note, "ow": ow, "net": net})
            save_history()
            refresh_display()
            return

btn_convert.config(command=do_convert)
entry_input.bind("<Return>", lambda e: do_convert())

# ---------- 窗口关闭保存 ----------
def on_closing():
    save_history()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# ---------- 初始刷新 ----------
refresh_display()

root.mainloop()
