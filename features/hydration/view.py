"""
features/hydration/view.py
--------------------------
Hydration UI:
- Profile/goal controls (sex • weight • climate • activity)
- Live progress in ml and glasses
- Buttons for adding one glass and resetting daily intake
- Auto-refresh via controller change listeners
"""

import tkinter as tk
from tkinter import ttk
from features.hydration import controller as hc
from ui.toasts import show_toast


def build(parent: ttk.Frame) -> None:
    wrapper = ttk.Frame(parent, padding=16)
    wrapper.pack(fill="both", expand=True)

    ttk.Label(wrapper, text="Hydration Coach 💧", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

    # --- Profile / Goal ---
    prof_frame = ttk.LabelFrame(wrapper, text="Goal settings (sex • weight • climate • activity)", padding=12)
    prof_frame.pack(fill="x")

    p = hc.get_profile()
    sex_var = tk.StringVar(value=p.sex)
    weight_var = tk.StringVar(value=str(p.weight_kg or ""))
    climate_var = tk.StringVar(value=p.climate)
    activity_var = tk.StringVar(value=p.activity)

    ttk.Label(prof_frame, text="Sex:").grid(row=0, column=0, sticky="w")
    sex_cb = ttk.Combobox(prof_frame, textvariable=sex_var, values=["female", "male"], width=10, state="readonly")
    sex_cb.grid(row=0, column=1, sticky="w", padx=(6, 12))

    ttk.Label(prof_frame, text="Weight (kg):").grid(row=0, column=2, sticky="w")
    ttk.Entry(prof_frame, textvariable=weight_var, width=8).grid(row=0, column=3, sticky="w", padx=(6, 12))

    ttk.Label(prof_frame, text="Climate:").grid(row=0, column=4, sticky="w")
    climate_cb = ttk.Combobox(prof_frame, textvariable=climate_var, values=["cool", "temperate", "hot"], width=12, state="readonly")
    climate_cb.grid(row=0, column=5, sticky="w", padx=(6, 12))

    ttk.Label(prof_frame, text="Activity:").grid(row=0, column=6, sticky="w")
    activity_cb = ttk.Combobox(prof_frame, textvariable=activity_var, values=["low", "moderate", "high"], width=12, state="readonly")
    activity_cb.grid(row=0, column=7, sticky="w", padx=(6, 12))

    def apply_goal():
        try:
            w = float(weight_var.get()) if weight_var.get().strip() else None
        except Exception:
            w = None
        hc.set_profile(sex=sex_var.get(), weight_kg=w, climate=climate_var.get(), activity=activity_var.get())
        refresh()
        show_toast(parent.winfo_toplevel(), "✅ Hydration goal updated", 1400)

    ttk.Button(prof_frame, text="Update goal", command=apply_goal).grid(row=0, column=8, sticky="w")

    # --- Progress ---
    info_var = tk.StringVar()
    ttk.Label(wrapper, textvariable=info_var).pack(anchor="w", pady=(12, 6))

    # Use green style to match the Home screen
    progress = ttk.Progressbar(wrapper, mode="determinate", maximum=100, style="Green.Horizontal.TProgressbar")
    progress.pack(fill="x")

    def refresh():
        goal_ml = hc.get_goal_ml()
        total_ml = hc.get_total_ml()
        ratio = hc.get_progress_ratio()
        info_var.set(
            f"Goal: {goal_ml} ml  •  Intake: {total_ml} ml  "
            f"({hc.get_total_glasses()}/{hc.get_goal_glasses()} glasses, {int(ratio*100)}%)"
        )
        progress["value"] = int(ratio * 100)

    # --- Actions ---
    btns = ttk.Frame(wrapper)
    btns.pack(anchor="w", pady=(10, 0))
    ttk.Button(btns, text="+1 glass (≈250 ml)", command=lambda: (hc.add_glass(), refresh(), show_toast(parent.winfo_toplevel(), "➕ +250 ml", 1000))).pack(side="left")
    ttk.Button(btns, text="Reset", command=lambda: (hc.reset_today(), refresh(), show_toast(parent.winfo_toplevel(), "🔄 Reset", 1000))).pack(side="left", padx=8)

    # Auto-refresh when the model changes
    hc.add_change_listener(refresh)

    refresh()
