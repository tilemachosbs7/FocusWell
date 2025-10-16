"""
ui/wizard.py
------------
First-run Setup Wizard for FocusWell.

This modal window appears before the main Home UI.
It collects essential information (sex, weight, temperature, activity)
used to calculate the hydration goal.

Returns:
    (settings, cancelled)
If the user cancels, `cancelled=True` so the main app can exit gracefully.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple

from core.settings import AppSettings, save_settings
from features.hydration import controller as hc


def _climate_from_temperature(temp_c: float) -> str:
    """Convert ambient temperature (°C) into a climate category."""
    if temp_c <= 10:
        return "cool"
    if temp_c >= 25:
        return "hot"
    return "temperate"


def run_first_time_wizard(root: tk.Tk, existing: Optional[AppSettings] = None) -> Tuple[Optional[AppSettings], bool]:
    """
    Launch the initial setup wizard.

    Args:
        root (tk.Tk): Main application window.
        existing (Optional[AppSettings]): Pre-loaded settings if any.

    Returns:
        Tuple[Optional[AppSettings], bool]:
            - AppSettings if completed successfully
            - (None, True) if the user cancelled
    """
    s = existing or AppSettings()

    dlg = tk.Toplevel(root)
    dlg.title("Initial Setup")
    dlg.transient(root)
    dlg.grab_set()
    dlg.resizable(False, False)

    root.update_idletasks()
    dlg.geometry(f"+{root.winfo_rootx() + 120}+{root.winfo_rooty() + 120}")

    cancelled = {"v": False}

    frame = ttk.Frame(dlg, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Welcome to FocusWell — Initial Setup",
        font=("Segoe UI", 13, "bold"),
    ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

    # --- Inputs ---
    ttk.Label(frame, text="Sex:").grid(row=1, column=0, sticky="w")
    sex_var = tk.StringVar(value=s.sex)
    ttk.Combobox(frame, textvariable=sex_var, values=["female", "male"], state="readonly", width=10)\
        .grid(row=1, column=1, sticky="w", padx=(6, 16))

    ttk.Label(frame, text="Weight (kg):").grid(row=1, column=2, sticky="w")
    weight_var = tk.StringVar(value="" if s.weight_kg is None else str(s.weight_kg))
    ttk.Entry(frame, textvariable=weight_var, width=8).grid(row=1, column=3, sticky="w")

    ttk.Label(frame, text="Ambient temperature (°C):").grid(row=2, column=0, sticky="w", pady=(8, 0))
    temp_var = tk.StringVar(value="" if s.temperature_c is None else str(s.temperature_c))
    ttk.Entry(frame, textvariable=temp_var, width=8).grid(row=2, column=1, sticky="w", pady=(8, 0))

    ttk.Label(frame, text="Activity level:").grid(row=2, column=2, sticky="w", pady=(8, 0))
    activity_var = tk.StringVar(value=s.activity)
    ttk.Combobox(frame, textvariable=activity_var, values=["low", "moderate", "high"], state="readonly", width=12)\
        .grid(row=2, column=3, sticky="w", pady=(8, 0))

    ttk.Label(
        frame,
        text="These values help compute your daily hydration goal.\nYou can edit them later in Settings.",
        foreground="#555",
    ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 6))

    btns = ttk.Frame(frame)
    btns.grid(row=4, column=0, columnspan=4, sticky="e", pady=(12, 0))
    ok_btn = ttk.Button(btns, text="Continue")
    cancel_btn = ttk.Button(btns, text="Exit")

    def _parse_float(s: str) -> Optional[float]:
        try:
            return float((s or "").replace(",", "."))
        except Exception:
            return None

    def on_cancel() -> None:
        cancelled["v"] = True
        try:
            dlg.grab_release()
        except Exception:
            pass
        dlg.destroy()

    def on_continue() -> None:
        nonlocal s
        sex = sex_var.get().strip()
        w = _parse_float(weight_var.get().strip())
        t = _parse_float(temp_var.get().strip())
        activity = activity_var.get().strip()

        # Validation
        if sex not in ("male", "female"):
            messagebox.showerror("Invalid", "Please choose sex (male/female).", parent=dlg); return
        if not w or w <= 0:
            messagebox.showerror("Invalid", "Please enter a valid weight (kg).", parent=dlg); return
        if t is None:
            messagebox.showerror("Invalid", "Please enter ambient temperature (°C).", parent=dlg); return
        if activity not in ("low", "moderate", "high"):
            messagebox.showerror("Invalid", "Please choose activity level.", parent=dlg); return

        climate = _climate_from_temperature(t)
        hc.set_profile(sex=sex, weight_kg=w, climate=climate, activity=activity)
        hc.reset_today()

        s = AppSettings(sex=sex, weight_kg=w, temperature_c=t, activity=activity)
        save_settings(s)

        try:
            dlg.grab_release()
        except Exception:
            pass
        dlg.destroy()

    ok_btn.configure(command=on_continue)
    cancel_btn.configure(command=on_cancel)
    cancel_btn.pack(side="right")
    ok_btn.pack(side="right", padx=(0, 6))

    dlg.bind("<Return>", lambda e: on_continue())
    dlg.bind("<Escape>", lambda e: on_cancel())

    dlg.wait_window()
    return (None, True) if cancelled["v"] else (s, False)
