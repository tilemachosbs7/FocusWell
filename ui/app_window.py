"""
core/app_window.py
-------------------
Creates and configures the main application window for FocusWell.

Features:
- Modern default size (1280x800) with responsive layout
- Built-in dark/light background handling
- Centering on screen for polished look
- Can be imported and reused across different UI modules
"""

import tkinter as tk
from tkinter import ttk


def create_app_window(
    title: str = "FocusWell",
    size: str = "1280x800",
    theme: str = "light"
) -> tk.Tk:
    """
    Create and return the main Tkinter window.

    Args:
        title (str): Title of the application window.
        size (str): Default geometry (e.g., "1280x800").
        theme (str): "light" or "dark" mode base color.

    Returns:
        tk.Tk: Configured main window.
    """
    window = tk.Tk()
    window.title(title)
    window.geometry(size)
    window.minsize(960, 600)

    # --- Background / theme colors ---
    if theme.lower() == "dark":
        bg_color = "#000000"
        fg_color = "#FFFFFF"
    else:
        bg_color = "#FFFFFF"
        fg_color = "#000000"

    window.configure(bg=bg_color)

    # --- Apply base ttk style for consistent theming ---
    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
    style.configure("TButton", background=bg_color, foreground=fg_color)

    # --- Optional centering on screen ---
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

    return window
