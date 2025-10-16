"""
features/focus/view.py
----------------------
Home screen: Focus Timer + Hydration + Calendar/Tasks

- Card-based (color-blocking) layout with proper contrast
- Theme switch: Dark / Light / Custom (custom colors apply only in Custom mode)
- Hydration progress in green with smooth animation
- Toast notifications at bottom-right
- Dark-mode visibility fix for Combobox / Entry / Spinbox
"""

from __future__ import annotations
import re
import tkinter as tk
from tkinter import ttk, colorchooser
from typing import Callable, Optional, Dict
from datetime import datetime, timedelta, timezone

from ui.toasts import show_toast
from features.focus.controller import (
    FocusController,
    DEMO_WORK_SEC, DEMO_BREAK_SEC,
    DEFAULT_WORK_SEC, DEFAULT_BREAK_SEC,
)
from features.hydration import controller as hc
from features.planner import controller as pc
from core.settings import load_settings

# optional: customtkinter
try:
    import customtkinter as ctk
    _HAS_CTK = True
except Exception:
    _HAS_CTK = False

# optional: tkcalendar
try:
    from tkcalendar import Calendar
    _HAS_TKCAL = True
except Exception:
    _HAS_TKCAL = False

# optional: IANA timezones
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


# ---------- time helpers ----------
def _fmt_mmss(sec: int) -> str:
    m, s = sec // 60, sec % 60
    return f"{m:02d}:{s:02d}"

_OFFSET_PAT = re.compile(r'^(?:UTC)?\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?$')

def _parse_utc_offset(tz_str: str) -> Optional[timezone]:
    if not tz_str: return None
    m = _OFFSET_PAT.match(tz_str.strip())
    if not m: return None
    sign, hh, mm = m.groups()
    h, m_ = int(hh), int(mm) if mm else 0
    if h > 23 or m_ > 59: return None
    delta = timedelta(hours=h, minutes=m_)
    if sign == "-": delta = -delta
    return timezone(delta)

def _current_tzinfo():
    try:
        tz_name = (load_settings().timezone or "").strip()
    except Exception:
        tz_name = ""
    if not tz_name: return None
    if ZoneInfo is not None:
        try: return ZoneInfo(tz_name)
        except Exception: pass
    return _parse_utc_offset(tz_name)

def _now_parts() -> tuple[str, str]:
    tz = _current_tzinfo()
    now = datetime.now(tz) if tz else datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


# ---------- palette & styling ----------
def _luma(hex_color: str) -> float:
    try:
        c = hex_color.lstrip("#")
        r,g,b = int(c[0:2],16)/255, int(c[2:4],16)/255, int(c[4:6],16)/255
        return 0.2126*r + 0.7152*g + 0.0722*b
    except: return 0.5

def _palette(mode: str, custom_bg: str|None=None, custom_fg: str|None=None) -> Dict[str,str]:
    if mode == "Dark":
        bg, text = "#000000", "#FFFFFF"
        surface, surface2 = "#111213", "#181A1B"
        muted, accent = "#B3B3B3", "#2563EB"
    elif mode == "Light":
        bg, text = "#FFFFFF", "#111111"
        surface, surface2 = "#F5F6F7", "#EEEFF2"
        muted, accent = "#555555", "#2563EB"
    else:  # Custom
        bg = custom_bg or "#FFFFFF"
        text = custom_fg or ("#FFFFFF" if _luma(bg) < 0.35 else "#111111")
        surface, surface2 = bg, bg
        muted, accent = (text if _luma(bg) < 0.35 else "#333333"), "#2563EB"

    return {"bg": bg, "surface": surface, "surface2": surface2, "text": text, "muted": muted, "accent": accent, "ok": "#22C55E"}

def _apply_styles(root: tk.Tk, pal: Dict[str,str]) -> None:
    style = ttk.Style(root)
    try:
        base = "clam" if "clam" in style.theme_names() else style.theme_use()
        style.theme_use(base)
    except Exception:
        pass

    try: root.configure(bg=pal["bg"])
    except Exception: pass

    style.configure(".", background=pal["bg"], foreground=pal["text"], font=("Segoe UI", 10))
    style.configure("Header.TFrame", background=pal["bg"])

    style.configure("Card.TFrame", background=pal["surface"], relief="flat", borderwidth=0)
    style.configure("Card2.TFrame", background=pal["surface2"], relief="flat", borderwidth=0)
    style.configure("Card.TLabel", background=pal["surface"], foreground=pal["text"])
    style.configure("Card2.TLabel", background=pal["surface2"], foreground=pal["text"])
    style.configure("Muted.TLabel", background=pal["bg"], foreground=pal["muted"])

    style.configure("Card.TLabelframe", background=pal["surface"], foreground=pal["text"])
    style.configure("Card.TLabelframe.Label", background=pal["surface"], foreground=pal["text"], font=("Segoe UI", 10, "bold"))

    style.configure("Accent.TButton", background=pal["accent"], foreground="#FFFFFF")
    style.map("Accent.TButton", background=[("active", pal["accent"])], foreground=[("active", "#FFFFFF")])

    style.configure("Green.Horizontal.TProgressbar", troughcolor=pal["surface"], background=pal["ok"])

    # Dark-mode visibility fixes for input widgets
    style.configure("TCombobox", fieldbackground=pal["surface2"], background=pal["surface2"], foreground=pal["text"])
    style.map("TCombobox", fieldbackground=[("readonly", pal["surface2"])], foreground=[("readonly", pal["text"])])
    style.configure("TEntry", fieldbackground=pal["surface2"], foreground=pal["text"])
    style.configure("TSpinbox", fieldbackground=pal["surface2"], foreground=pal["text"])

def _style_calendar(cal: 'Calendar', pal: Dict[str,str]) -> None:
    try:
        cal.configure(
            background=pal["surface"],
            foreground=pal["text"],
            disabledforeground=pal["muted"],
            bordercolor=pal["surface"],
            headersbackground=pal["surface"],
            headersforeground=pal["text"],
            selectbackground=pal["accent"] if _luma(pal["bg"]) >= 0.5 else "#334155",
            selectforeground="#FFFFFF" if _luma(pal["bg"]) >= 0.5 else "#EDEDED",
            weekendbackground=pal["surface"],
            weekendforeground=pal["text"],
            othermonthbackground=pal["surface"],
            othermonthwebackground=pal["surface"],
            othermonthforeground=pal["muted"],
            othermonthweforeground=pal["muted"],
            tooltipbackground=pal["surface"],
            tooltipforeground=pal["text"],
        )
    except Exception:
        pass

def _animate(current: float, target: float, step: float) -> float:
    if abs(target-current) <= step: return target
    return current + step if target > current else current - step


# ---------- main UI ----------
def build(parent: ttk.Frame, add_tick_listener: Callable[[Callable[[int], None]], None]) -> None:
    pc.init_storage()
    ctrl = FocusController()
    locals_container: dict[str, object] = {}

    # time / focus state
    date_var = tk.StringVar(); time_var = tk.StringVar()
    _update_now(date_var, time_var)
    phase_var = tk.StringVar(value="IDLE")
    remain_var = tk.StringVar(value="00:00")

    # hydration progress animation
    _prog_actual = {"v": 0.0}
    _prog_target = {"v": int(hc.get_progress_ratio()*100)}

    # theme state — DEFAULT LIGHT MODE
    theme_var = tk.StringVar(value="Light")      # "Dark" | "Light" | "Custom"
    _bg_custom = {"v": None}
    _fg_custom = {"v": None}

    # header
    header = ttk.Frame(parent, style="Header.TFrame", padding=(16, 10))
    header.pack(fill="x")
    ttk.Label(header, text="FocusWell — Home", font=("Segoe UI", 14, "bold")).pack(side="left")

    theme_box = ttk.Combobox(header, textvariable=theme_var, values=["Dark", "Light", "Custom"], width=8, state="readonly")
    theme_box.pack(side="right", padx=(6, 0))

    def _apply_theme(*_):
        mode = theme_var.get()
        if _HAS_CTK:
            ctk.set_appearance_mode("Dark" if mode == "Dark" else "Light")
        pal = _palette(mode, _bg_custom["v"] if mode == "Custom" else None, _fg_custom["v"] if mode == "Custom" else None)
        _apply_styles(parent.winfo_toplevel(), pal)
        cal = locals_container.get("cal_widget")
        if _HAS_TKCAL and cal is not None:
            _style_calendar(cal, pal)

    def _pick_colors():
        if theme_var.get() != "Custom":
            theme_var.set("Custom")
        bg = colorchooser.askcolor(title="Choose background color")
        if bg and bg[1]: _bg_custom["v"] = bg[1]
        fg = colorchooser.askcolor(title="Choose text color")
        if fg and fg[1]: _fg_custom["v"] = fg[1]
        _apply_theme()

    ttk.Button(header, text="🎨 Colors…", command=_pick_colors).pack(side="right", padx=(10, 0))
    theme_box.bind("<<ComboboxSelected>>", _apply_theme)
    _apply_theme()

    # body (cards)
    wrapper = ttk.Frame(parent, padding=16); wrapper.pack(fill="both", expand=True)
    top = ttk.Frame(wrapper); top.pack(fill="x", pady=(0,12))

    # Card 1: Clock + Timer
    card1 = ttk.Frame(top, style="Card.TFrame", padding=16)
    card1.pack(side="left", fill="x", expand=True)

    ttk.Label(card1, text="🕒 Current time (Settings > Time Zone)", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    ttk.Label(card1, textvariable=time_var, style="Card.TLabel", font=("Consolas", 32, "bold")).pack(anchor="w")
    ttk.Label(card1, textvariable=date_var, style="Card.TLabel", font=("Consolas", 11)).pack(anchor="w", pady=(0, 8))

    timer_box = ttk.Frame(card1, style="Card.TFrame"); timer_box.pack(fill="x", pady=(6,0))
    ttk.Label(timer_box, text="Focus Timer ⏱️", style="Card.TLabel", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,8))
    ttk.Label(timer_box, text="Phase:", style="Card.TLabel").grid(row=1, column=0, sticky="w")
    ttk.Label(timer_box, textvariable=phase_var, style="Card.TLabel", font=("Segoe UI", 12, "bold")).grid(row=1, column=1, sticky="w", padx=(8,0))
    ttk.Label(timer_box, text="Time remaining:", style="Card.TLabel").grid(row=2, column=0, sticky="w")
    ttk.Label(timer_box, textvariable=remain_var, style="Card.TLabel", font=("Consolas", 16)).grid(row=2, column=1, sticky="w", padx=(8,0))

    routines = {
        "Demo 10/5 (quick test)": (DEMO_WORK_SEC, DEMO_BREAK_SEC),
        "Pomodoro 25/5 (standard)": (DEFAULT_WORK_SEC, DEFAULT_BREAK_SEC),
        "Deep work 50/10": (50*60, 10*60),
    }
    routine_var = tk.StringVar(value="Pomodoro 25/5 (standard)")
    ttk.Label(timer_box, text="Routine (work/break):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=(6,0))
    ttk.Combobox(timer_box, textvariable=routine_var, values=list(routines.keys()), state="readonly", width=22).grid(row=3, column=1, sticky="w", pady=(6,0))

    btns = ttk.Frame(timer_box, style="Card.TFrame"); btns.grid(row=4, column=0, columnspan=4, sticky="w", pady=10)
    start_btn = ttk.Button(btns, text="Start focus", style="Accent.TButton")
    pause_btn = ttk.Button(btns, text="Pause", state="disabled")
    reset_btn = ttk.Button(btns, text="Reset", state="disabled")
    start_btn.pack(side="left"); pause_btn.pack(side="left", padx=8); reset_btn.pack(side="left")

    # Card 2: Hydration
    card2 = ttk.Frame(top, style="Card2.TFrame", padding=16)
    card2.pack(side="right", fill="y", padx=(12,0))
    ttk.Label(card2, text="Hydration 💧", style="Card2.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,4))
    hyd_info_var = tk.StringVar()
    ttk.Label(card2, textvariable=hyd_info_var, style="Card2.TLabel").pack(anchor="w")
    hyd_progress = ttk.Progressbar(card2, maximum=100, mode="determinate", style="Green.Horizontal.TProgressbar")
    hyd_progress.pack(fill="x", pady=6)

    def _refresh_hydration():
        ratio = hc.get_progress_ratio()
        _prog_target["v"] = int(ratio*100)
        hyd_info_var.set(f"Goal: {hc.get_goal_glasses()} glasses • Progress: {hc.get_total_glasses()} / {hc.get_goal_glasses()} ({int(ratio*100)}%)")

    def _add_glass():
        hc.add_glass(); _refresh_hydration()
        show_toast(parent.winfo_toplevel(), "➕ +250 ml added", 1000)

    ttk.Button(card2, text="+1 glass (≈250 ml)", command=_add_glass).pack(anchor="w")
    _refresh_hydration()
    add_listener = getattr(hc, "add_change_listener", None) or getattr(hc, "add_on_change_listener", None)
    if callable(add_listener): add_listener(_refresh_hydration)

    # Bottom: Calendar + Lists
    bottom = ttk.Frame(wrapper); bottom.pack(fill="both", expand=True)
    selected_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    cal_card = ttk.Frame(bottom, style="Card.TFrame", padding=12)
    cal_card.pack(side="left", fill="y", padx=(0,12))
    ttk.Label(cal_card, text="📅 Calendar", style="Card.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")

    if _HAS_TKCAL:
        cal = Calendar(cal_card, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.selection_set(selected_date.get()); cal.pack(pady=4)
        locals_container["cal_widget"] = cal
        def _on_date(_evt=None):
            selected_date.set(cal.get_date()); refresh_day(); refresh_next()
        cal.bind("<<CalendarSelected>>", _on_date)
        _apply_theme()
    else:
        ttk.Entry(cal_card, textvariable=selected_date, width=12).pack(anchor="w")
        ttk.Label(cal_card, text="Format: YYYY-MM-DD", style="Card.TLabel").pack(anchor="w")

    lists_card = ttk.Frame(bottom, style="Card.TFrame", padding=12)
    lists_card.pack(side="left", fill="both", expand=True)

    day_frame = ttk.LabelFrame(lists_card, text="Tasks on selected date", style="Card.TLabelframe", padding=12)
    day_frame.pack(fill="x")

    add_row = ttk.Frame(day_frame, style="Card.TFrame"); add_row.pack(fill="x", pady=(0,8))
    title_var = tk.StringVar()
    ttk.Entry(add_row, textvariable=title_var).pack(side="left", fill="x", expand=True)

    def _ask_time(root: tk.Tk, title: str="Pick a time", initial: str="09:00") -> Optional[str]:
        dlg = tk.Toplevel(root); dlg.title(title); dlg.transient(root); dlg.grab_set(); dlg.resizable(False, False)
        vh = tk.StringVar(value=initial.split(':')[0]); vm = tk.StringVar(value=initial.split(':')[1])
        frm = ttk.Frame(dlg, padding=12); frm.pack()
        ttk.Label(frm, text="Hour").grid(row=0, column=0)
        ttk.Spinbox(frm, from_=0, to=23, textvariable=vh, width=3, wrap=True, justify="center").grid(row=0, column=1, padx=4)
        ttk.Label(frm, text=":").grid(row=0, column=2)
        ttk.Spinbox(frm, from_=0, to=59, textvariable=vm, width=3, wrap=True, justify="center").grid(row=0, column=3, padx=4)
        res = {"v": None}
        def ok():
            try:
                h = max(0, min(23, int(vh.get()))); m = max(0, min(59, int(vm.get())))
                res["v"] = f"{h:02d}:{m:02d}"; dlg.destroy()
            except: dlg.destroy()
        ttk.Button(frm, text="OK", command=ok).grid(row=1, column=0, columnspan=4, pady=(10,0))
        dlg.bind("<Return>", lambda e: ok()); dlg.wait_window(); return res["v"]

    def _add_with_time():
        t = title_var.get().strip()
        if not t: show_toast(parent.winfo_toplevel(), "Please enter a task title", 1500); return
        picked = _ask_time(parent.winfo_toplevel(), "Set time for task", "09:00")
        if not picked: return
        pc.add_task(t, due_date=selected_date.get(), due_time=picked)
        title_var.set(""); refresh_day(); refresh_next()
        show_toast(parent.winfo_toplevel(), f"🆕 Task added at {picked}", 1200)

    ttk.Button(add_row, text="Add task & time", command=_add_with_time).pack(side="left", padx=6)

    day_list = ttk.Frame(day_frame, style="Card.TFrame"); day_list.pack(fill="x")

    next_frame = ttk.LabelFrame(lists_card, text="Next tasks (after selected date)", style="Card.TLabelframe", padding=12)
    next_frame.pack(fill="both", expand=True, pady=(8,0))
    next_list = ttk.Frame(next_frame, style="Card.TFrame"); next_list.pack(fill="both", expand=True)

    def _set_time(task_id: int):
        picked = _ask_time(parent.winfo_toplevel(), "Set new time", "09:00")
        if not picked: return
        pc.update_task_time(task_id, picked); refresh_day(); refresh_next()
        show_toast(parent.winfo_toplevel(), f"⏰ Time set to {picked}", 1200)

    def _clear_time(task_id: int):
        pc.update_task_time(task_id, None); refresh_day(); refresh_next()
        show_toast(parent.winfo_toplevel(), "🧹 Time cleared", 1200)

    def _row(container: ttk.Frame, task):
        row = ttk.Frame(container, style="Card.TFrame"); row.pack(fill="x", pady=2)
        done_v = tk.BooleanVar(value=task.done)
        def toggle(): pc.toggle_done(task.id, done_v.get()); refresh_day(); refresh_next()
        ttk.Checkbutton(row, variable=done_v, command=toggle).pack(side="left", ipadx=4, padx=(0,6))
        ttk.Label(row, text=(task.due_date or "—"), width=12, font=("Consolas", 10), style="Card.TLabel").pack(side="left")
        ttk.Label(row, text=(task.due_time or "—"), width=6, font=("Consolas", 10), style="Card.TLabel").pack(side="left")
        ttk.Label(row, text=task.title, width=40, style="Card.TLabel").pack(side="left")
        act = ttk.Frame(row, style="Card.TFrame"); act.pack(side="left", padx=6)
        ttk.Button(act, text="Set time", command=lambda tid=task.id: _set_time(tid)).pack(side="left", padx=(0,6))
        ttk.Button(act, text="Clear time", command=lambda tid=task.id: _clear_time(tid)).pack(side="left", padx=(0,6))
        ttk.Button(act, text="Delete task", command=lambda tid=task.id: (pc.delete_task(tid), refresh_day(), refresh_next(), show_toast(parent.winfo_toplevel(), "🗑️ Task deleted", 1000))).pack(side="left")

    def refresh_day():
        for w in day_list.winfo_children(): w.destroy()
        items = pc.list_tasks_by_date(selected_date.get())
        if not items:
            ttk.Label(day_list, text=f"(No tasks on {selected_date.get()})", style="Card.TLabel").pack(anchor="w", pady=4); return
        hdr = ttk.Frame(day_list, style="Card.TFrame"); hdr.pack(fill="x", pady=(0,6))
        ttk.Label(hdr, text="Done", width=6, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Date", width=8, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Time", width=6, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Title", width=40, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Actions", style="Card.TLabel").pack(side="left", padx=8)
        for t in items: _row(day_list, t)

    def refresh_next():
        for w in next_list.winfo_children(): w.destroy()
        items = pc.list_tasks_after_date(selected_date.get(), limit=100)
        if not items:
            ttk.Label(next_list, text="(No upcoming tasks)", style="Card.TLabel").pack(anchor="w", pady=4); return
        hdr = ttk.Frame(next_list, style="Card.TFrame"); hdr.pack(fill="x", pady=(0,6))
        ttk.Label(hdr, text="Done", width=6, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Date", width=8, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Time", width=6, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Title", width=40, style="Card.TLabel").pack(side="left")
        ttk.Label(hdr, text="Actions", style="Card.TLabel").pack(side="left", padx=8)
        for t in items: _row(next_list, t)

    refresh_day(); refresh_next()

    # focus wiring
    def _on_update():
        phase_var.set(ctrl.get_phase())
        remain_var.set(_fmt_mmss(ctrl.get_remaining_sec()))
        running = ctrl.is_running()
        pause_btn.configure(state="normal" if running else "disabled")
        reset_btn.configure(state="normal" if ctrl.get_phase()!="IDLE" else "disabled")

    def _on_phase_change(ph: str):
        if ph == "WORK": show_toast(parent.winfo_toplevel(), "🟢 Work phase started", 1800)
        elif ph == "BREAK": show_toast(parent.winfo_toplevel(), "🟡 Break phase — relax", 1800)

    ctrl.set_on_update(_on_update); ctrl.set_on_phase_change(_on_phase_change)
    start_btn.configure(command=lambda: (ctrl.set_routine(*routines[routine_var.get()]), ctrl.start()))
    pause_btn.configure(command=lambda: ctrl.pause())
    reset_btn.configure(command=lambda: ctrl.reset())

    # ✅ CRITICAL: connect controller to the global 1s loop so time actually ticks
    add_tick_listener(ctrl.on_tick)

    # live clock + smooth hydration bar
    def _tick(total_seconds: int):
        _update_now(date_var, time_var)
        # Focus controller is ticked via add_tick_listener(ctrl.on_tick) above.

        cur, tgt = _prog_actual["v"], _prog_target["v"]
        new_val = _animate(cur, tgt, step=2.5)
        _prog_actual["v"] = new_val
        hyd_progress["value"] = new_val
        if abs(tgt - new_val) > 0.1:
            parent.after(16, lambda: _tick(total_seconds))

    add_tick_listener(_tick)
    _on_update()


def _update_now(dv: tk.StringVar, tv: tk.StringVar):
    d,t = _now_parts()
    dv.set(d); tv.set(t)
