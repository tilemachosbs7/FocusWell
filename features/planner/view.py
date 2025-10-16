"""
features/focus/view.py
----------------------
Main "Home" screen of FocusWell:
- Displays real-time clock, Focus timer, and mini Hydration panel.
- Integrates a calendar with per-day task list and time picker.
- Handles eye and hydration reminders during active WORK sessions.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from datetime import datetime

from ui.toasts import show_toast
from features.focus.controller import (
    FocusController,
    DEMO_WORK_SEC,
    DEMO_BREAK_SEC,
    DEFAULT_WORK_SEC,
    DEFAULT_BREAK_SEC,
)
from features.hydration import controller as hc
from features.planner import controller as pc
from core.config import (
    FOCUS_EYE_REMINDER_SEC,
    FOCUS_EYE_REMINDER_MESSAGE,
    FOCUS_HYDRATION_REMINDER_SEC,
    FOCUS_HYDRATION_REMINDER_MESSAGE,
)

try:
    from tkcalendar import Calendar
    _HAS_TKCAL = True
except Exception:
    _HAS_TKCAL = False


def _fmt_mmss(sec: int) -> str:
    """Format seconds → MM:SS."""
    return f"{sec // 60:02d}:{sec % 60:02d}"


def _generate_time_slots(step_minutes: int = 30) -> list[str]:
    """Generate a list of HH:MM slots (00:00–23:30)."""
    slots: list[str] = []
    for h in range(24):
        for m in range(0, 60, step_minutes):
            slots.append(f"{h:02d}:{m:02d}")
    return slots


def build(parent: ttk.Frame, add_tick_listener: Callable[[Callable[[int], None]], None]) -> None:
    """
    Build the main Focus page.

    Layout:
    - Top row: Clock + Focus Timer (left) | Mini Hydration panel (right)
    - Bottom: Calendar + Time picker + Task list (below)
    - Eye and Hydration reminders active only during WORK phase.
    """
    pc.init_storage()
    ctrl = FocusController()

    wrapper = ttk.Frame(parent, padding=16)
    wrapper.pack(fill="both", expand=True)

    # ====== TOP ======
    top = ttk.Frame(wrapper)
    top.pack(fill="x", pady=(0, 12))

    # ---- LEFT: Clock + Timer ----
    left = ttk.Frame(top)
    left.pack(side="left", fill="x", expand=True)

    dt_var = tk.StringVar(value="")
    clock_row = ttk.Frame(left)
    clock_row.pack(fill="x")
    ttk.Label(clock_row, text="Now:", font=("Segoe UI", 10, "bold")).pack(side="left")
    ttk.Label(clock_row, textvariable=dt_var, font=("Consolas", 11)).pack(side="left", padx=(6, 12))

    timer_box = ttk.Frame(left)
    timer_box.pack(fill="x", pady=(6, 0))

    ttk.Label(timer_box, text="Focus Timer ⏱️", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

    phase_var = tk.StringVar(value="IDLE")
    time_var = tk.StringVar(value="00:00")

    ttk.Label(timer_box, text="Phase:").grid(row=1, column=0, sticky="w")
    ttk.Label(timer_box, textvariable=phase_var, font=("Segoe UI", 12, "bold")).grid(row=1, column=1, sticky="w", padx=(8, 0))
    ttk.Label(timer_box, text="Remaining:").grid(row=2, column=0, sticky="w")
    ttk.Label(timer_box, textvariable=time_var, font=("Consolas", 16)).grid(row=2, column=1, sticky="w", padx=(8, 0))

    routines = {
        "Demo 10/5": (DEMO_WORK_SEC, DEMO_BREAK_SEC),
        "Pomodoro 25/5": (DEFAULT_WORK_SEC, DEFAULT_BREAK_SEC),
        "Deep 50/10": (50 * 60, 10 * 60),
    }
    routine_var = tk.StringVar(value="Pomodoro 25/5")
    ttk.Label(timer_box, text="Routine:").grid(row=3, column=0, sticky="w", pady=(6, 0))
    routine_cb = ttk.Combobox(timer_box, textvariable=routine_var, values=list(routines.keys()), state="readonly", width=18)
    routine_cb.grid(row=3, column=1, sticky="w", pady=(6, 0))

    # Control buttons
    btns = ttk.Frame(timer_box)
    btns.grid(row=4, column=0, columnspan=4, sticky="w", pady=10)
    start_btn = ttk.Button(btns, text="Start")
    pause_btn = ttk.Button(btns, text="Pause", state="disabled")
    reset_btn = ttk.Button(btns, text="Reset", state="disabled")
    start_btn.pack(side="left")
    pause_btn.pack(side="left", padx=8)
    reset_btn.pack(side="left")

    # Reminder label (right side of header)
    reminder_var = tk.StringVar(value="")
    ttk.Label(top, textvariable=reminder_var, foreground="#0A66C2").pack(side="right", anchor="ne")

    # ---- RIGHT: Mini Hydration ----
    right = ttk.LabelFrame(top, text="Hydration 💧", padding=12)
    right.pack(side="right", padx=(12, 0))

    hyd_info_var = tk.StringVar()
    ttk.Label(right, textvariable=hyd_info_var).pack(anchor="w")
    hyd_progress = ttk.Progressbar(right, maximum=100, length=220)
    hyd_progress.pack(fill="x", pady=6)

    def _refresh_hydration():
        total = hc.get_total_glasses()
        goal = hc.get_goal_glasses()
        ratio = hc.get_progress_ratio()
        hyd_progress["value"] = int(ratio * 100)
        hyd_info_var.set(f"Drank {total}/{goal} glasses ({int(ratio*100)}%)")

    def _add_glass():
        hc.add_glass()
        _refresh_hydration()
        show_toast(parent.winfo_toplevel(), "➕ Added 250 ml", 1200)

    ttk.Button(right, text="+1 glass", command=_add_glass).pack(anchor="w")
    _refresh_hydration()

    # ====== BOTTOM ======
    bottom = ttk.Frame(wrapper)
    bottom.pack(fill="both", expand=True)

    # Calendar + Time picker
    cal_section = ttk.Frame(bottom)
    cal_section.pack(fill="x")

    selected_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    cal_frame = ttk.Frame(cal_section)
    cal_frame.pack(side="left", padx=(0, 12), pady=(0, 6))

    if _HAS_TKCAL:
        cal = Calendar(cal_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.selection_set(selected_date.get())
        cal.pack(pady=4)

        def _on_date_change(_evt=None):
            selected_date.set(cal.get_date())
            refresh_day_tasks()

        cal.bind("<<CalendarSelected>>", _on_date_change)
    else:
        ttk.Label(cal_frame, text="(Install tkcalendar for calendar view)", foreground="#A00").pack(anchor="w")
        ttk.Entry(cal_frame, textvariable=selected_date, width=12).pack(anchor="w")
        ttk.Label(cal_frame, text="Format: YYYY-MM-DD").pack(anchor="w")

    # Time Picker
    time_picker_frame = ttk.LabelFrame(cal_section, text="Time Picker", padding=8)
    time_picker_frame.pack(side="left", padx=(0, 12))

    selected_time = tk.StringVar(value="09:00")
    ttk.Label(time_picker_frame, text="Selected:").pack(anchor="w")
    ttk.Label(time_picker_frame, textvariable=selected_time, font=("Consolas", 11)).pack(anchor="w", pady=(0, 6))

    times_list = tk.Listbox(time_picker_frame, height=10, exportselection=False)
    for slot in _generate_time_slots(30):
        times_list.insert("end", slot)
    times_list.pack(side="left")
    sb = ttk.Scrollbar(time_picker_frame, orient="vertical", command=times_list.yview)
    sb.pack(side="left", fill="y")
    times_list.configure(yscrollcommand=sb.set)

    # Default select 09:00
    try:
        idx = list(_generate_time_slots(30)).index("09:00")
        times_list.selection_set(idx)
        times_list.see(idx)
    except ValueError:
        pass

    def _on_time_select(_evt=None):
        sel = times_list.curselection()
        if sel:
            selected_time.set(times_list.get(sel[0]))

    times_list.bind("<<ListboxSelect>>", _on_time_select)

    # ---- Day Tasks ----
    day_frame = ttk.LabelFrame(bottom, text="Tasks of the selected day", padding=12)
    day_frame.pack(fill="both", expand=True, pady=(6, 0))

    add_row = ttk.Frame(day_frame)
    add_row.pack(fill="x", pady=(0, 8))
    day_entry_var = tk.StringVar()
    ttk.Entry(add_row, textvariable=day_entry_var).pack(side="left", fill="x", expand=True)
    ttk.Button(add_row, text="Add", command=lambda: _add_day_task()).pack(side="left", padx=6)

    list_container = ttk.Frame(day_frame)
    list_container.pack(fill="both", expand=True)

    def _add_day_task():
        title = day_entry_var.get().strip()
        if not title:
            show_toast(parent.winfo_toplevel(), "Enter a task title", 1500)
            return
        pc.add_task(title, due_date=selected_date.get(), due_time=selected_time.get())
        day_entry_var.set("")
        refresh_day_tasks()
        show_toast(parent.winfo_toplevel(), "🆕 Task added!", 1200)

    def _set_time_for_task(task_id: int):
        pc.update_task_time(task_id, selected_time.get())
        refresh_day_tasks()
        show_toast(parent.winfo_toplevel(), f"⏰ Time set to {selected_time.get()}", 1200)

    def _clear_time_for_task(task_id: int):
        pc.update_task_time(task_id, None)
        refresh_day_tasks()
        show_toast(parent.winfo_toplevel(), "🧹 Time cleared", 1200)

    def refresh_day_tasks():
        for w in list_container.winfo_children():
            w.destroy()

        tasks = pc.list_tasks_by_date(selected_date.get())
        if not tasks:
            ttk.Label(list_container, text=f"(No tasks for {selected_date.get()})").pack(anchor="w", pady=4)
            return

        hdr = ttk.Frame(list_container)
        hdr.pack(fill="x", pady=(0, 6))
        ttk.Label(hdr, text="Done", width=6).pack(side="left")
        ttk.Label(hdr, text="Time", width=8).pack(side="left")
        ttk.Label(hdr, text="Title", width=40).pack(side="left")
        ttk.Label(hdr, text="Actions").pack(side="left", padx=8)

        for task in tasks:
            row = ttk.Frame(list_container)
            row.pack(fill="x", pady=2)
            done_var = tk.BooleanVar(value=task.done)

            def make_toggle_handler(task_id: int, var: tk.BooleanVar):
                return lambda: (pc.toggle_done(task_id, var.get()), refresh_day_tasks())

            ttk.Checkbutton(row, variable=done_var, command=make_toggle_handler(task.id, done_var)).pack(side="left", ipadx=4, padx=(0, 6))
            ttk.Label(row, text=(task.due_time or "--:--"), width=8, font=("Consolas", 10)).pack(side="left")
            ttk.Label(row, text=task.title, width=40).pack(side="left")

            actions = ttk.Frame(row)
            actions.pack(side="left", padx=8)
            ttk.Button(actions, text="Set time from picker", command=lambda tid=task.id: _set_time_for_task(tid)).pack(side="left")
            ttk.Button(actions, text="Clear time", command=lambda tid=task.id: _clear_time_for_task(tid)).pack(side="left", padx=(6, 0))

    # ====== Controller + Tick ======
    def _update_buttons(running: bool):
        if running:
            start_btn.configure(state="disabled")
            pause_btn.configure(state="normal")
            reset_btn.configure(state="normal")
        else:
            label = "Resume" if ctrl.get_phase() != "IDLE" and ctrl.get_remaining_sec() > 0 else "Start"
            start_btn.configure(text=label, state="normal")
            pause_btn.configure(state="disabled")
            reset_btn.configure(state="normal" if ctrl.get_phase() != "IDLE" else "disabled")

    def on_update_ui():
        phase_var.set(ctrl.get_phase())
        time_var.set(_fmt_mmss(ctrl.get_remaining_sec()))
        _update_buttons(ctrl.is_running())

    def on_phase_change(phase: str):
        msg = "🧠 Work phase started" if phase == "WORK" else "☕ Break phase — relax!"
        show_toast(parent.winfo_toplevel(), msg, 2000)
        reminder_var.set("")

    ctrl.set_on_update(on_update_ui)
    ctrl.set_on_phase_change(on_phase_change)

    def _apply_routine():
        work, brk = routines[routine_var.get()]
        ctrl.set_routine(work, brk)

    start_btn.configure(command=lambda: (_apply_routine(), ctrl.start(), _update_buttons(True)))
    pause_btn.configure(command=lambda: (ctrl.pause(), _update_buttons(False)))
    reset_btn.configure(command=lambda: (ctrl.reset(), phase_var.set("IDLE"), time_var.set("00:00"), _update_buttons(False), reminder_var.set("")))
    routine_cb.bind("<<ComboboxSelected>>", lambda e: _apply_routine())

    last_eye = {"v": -1}
    last_hyd = {"v": -1}

    def _on_tick(_total_seconds: int):
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        dt_var.set(now)

        if not ctrl.is_running() or ctrl.get_phase() != "WORK":
            return

        work_total = ctrl.get_routine()[0]
        elapsed = max(work_total - ctrl.get_remaining_sec(), 0)

        if FOCUS_EYE_REMINDER_SEC > 0:
            eye_period = elapsed // FOCUS_EYE_REMINDER_SEC
            if eye_period > 0 and eye_period != last_eye["v"]:
                last_eye["v"] = eye_period
                reminder_var.set(FOCUS_EYE_REMINDER_MESSAGE)
                show_toast(parent.winfo_toplevel(), FOCUS_EYE_REMINDER_MESSAGE, 2500)

        if FOCUS_HYDRATION_REMINDER_SEC > 0:
            hyd_period = elapsed // FOCUS_HYDRATION_REMINDER_SEC
            if hyd_period > 0 and hyd_period != last_hyd["v"]:
                last_hyd["v"] = hyd_period
                reminder_var.set(FOCUS_HYDRATION_REMINDER_MESSAGE)
                show_toast(parent.winfo_toplevel(), FOCUS_HYDRATION_REMINDER_MESSAGE, 2500)

    add_tick_listener(ctrl.on_tick)
    add_tick_listener(_on_tick)

    # Initial state
    on_update_ui()
    _on_tick(0)
    refresh_day_tasks()
