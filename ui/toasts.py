"""
ui/toasts.py
-------------
Lightweight toast popups for polite, temporary notifications within the FocusWell app.

Usage:
    from ui.toasts import show_toast
    show_toast(root, "✅ Settings saved", 1500)

Features:
- Appears bottom-right of the parent window
- Auto-dismisses after the specified duration
- No window decorations (borderless, topmost)
"""

import tkinter as tk


def show_toast(root: tk.Tk, message: str, duration_ms: int = 2000) -> None:
    """
    Display a small toast popup at the bottom-right corner of the main window.

    Args:
        root (tk.Tk): The main Tkinter window.
        message (str): The text message to display.
        duration_ms (int): How long the toast stays visible (in milliseconds).
    """
    # Ensure geometry is up-to-date
    root.update_idletasks()

    # Create popup window
    toast = tk.Toplevel(root)
    toast.overrideredirect(True)  # No title bar or borders
    toast.attributes("-topmost", True)

    # Position near bottom-right of the root window
    width, height = 260, 80
    x = root.winfo_rootx() + root.winfo_width() - width - 20
    y = root.winfo_rooty() + root.winfo_height() - height - 40
    toast.geometry(f"{width}x{height}+{x}+{y}")

    # Style
    label = tk.Label(
        toast,
        text=message,
        bg="#333333",
        fg="#FFFFFF",
        wraplength=240,
        font=("Segoe UI", 10),
        padx=10,
        pady=10,
    )
    label.pack(fill="both", expand=True)

    # Auto-destroy after duration
    toast.after(duration_ms, toast.destroy)
