"""
main.py
--------
FocusWell — Wellness Assistant

Launches the main application:
  1. Loads or initializes user settings (via Setup Wizard if first run)
  2. Applies hydration profile
  3. Starts the app loop (1s tick)
  4. Builds the Home UI (Focus Timer, Hydration, Planner)
  5. Provides access to Settings via menu
"""

import sys
import tkinter as tk
from tkinter import ttk

from ui.app_window import create_app_window
from core.loop import AppLoop
from features.focus.view import build as build_focus
from ui.tabs import open_settings_window
from core.settings import load_settings
from ui.wizard import run_first_time_wizard
from features.hydration import controller as hc


def _climate_from_temperature(t: float) -> str:
    """Map temperature (°C) to climate category."""
    return "cool" if t <= 10 else ("hot" if t >= 25 else "temperate")


def main() -> None:
    """Main entry point for the FocusWell application."""
    window = create_app_window("FocusWell - Wellness Assistant")

    # 1) Load settings or run setup wizard
    settings = load_settings()
    settings, cancelled = (
        run_first_time_wizard(window, existing=settings)
        if not settings.is_complete()
        else (settings, False)
    )
    if cancelled:
        try:
            window.destroy()
        except Exception:
            pass
        sys.exit(0)

    # Apply hydration profile and reset daily intake
    climate = _climate_from_temperature(settings.temperature_c or 20.0)
    hc.set_profile(
        sex=settings.sex,
        weight_kg=settings.weight_kg,
        climate=climate,
        activity=settings.activity,
    )
    hc.reset_today()

    # 2) App loop (1s tick)
    app_loop = AppLoop(window, interval_ms=1000)
    app_loop.start()

    # 3) Build Home (Focus, Hydration, Planner)
    home_wrapper = ttk.Frame(window, padding=8)
    home_wrapper.pack(fill="both", expand=True)
    build_focus(home_wrapper, app_loop.add_tick_listener)

    # 4) Menu → Settings
    menubar = tk.Menu(window)
    window.config(menu=menubar)
    settings_menu = tk.Menu(menubar, tearoff=False)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    settings_menu.add_command(
        label="Open Settings…",
        command=lambda: open_settings_window(window),
    )

    window.mainloop()


if __name__ == "__main__":
    main()
