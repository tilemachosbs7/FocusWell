"""
core/loop.py
----------------
Central scheduler: 1 tick per second without blocking the Tkinter UI.

This loop:
  • starts/stops a periodic tick via `root.after`,
  • notifies registered listeners with the app uptime (in seconds),
  • optionally triggers wellness nudges (eye care / hydration / stretch) based on core.config.
"""

import tkinter as tk
from typing import Callable, List

from ui.toasts import show_toast
from core.config import (
    ENABLE_EYE_CARE,
    ENABLE_HYDRATION_NUDGE,
    ENABLE_STRETCH_NUDGE,
    EYE_BREAK_INTERVAL_SEC,
    EYE_BREAK_MESSAGE,
    HYDRATION_NUDGE_INTERVAL_SEC,
    HYDRATION_NUDGE_MESSAGE,
    STRETCH_NUDGE_INTERVAL_SEC,
    STRETCH_NUDGE_MESSAGE,
)

class AppLoop:
    """
    Lightweight application scheduler.

    Args:
        root: The Tkinter root window.
        interval_ms: Tick interval in milliseconds (default: 1000).

    Notes:
        • No threads are used; scheduling relies on `root.after`, keeping the UI responsive.
        • Each registered listener is called with the total uptime (seconds).
    """

    def __init__(self, root: tk.Tk, interval_ms: int = 1000) -> None:
        self.root = root
        self.interval_ms = interval_ms
        self._running = False
        self._seconds_since_start = 0

        print(
            f"[AppLoop] EYE={ENABLE_EYE_CARE} | HYDRATION={ENABLE_HYDRATION_NUDGE} | STRETCH={ENABLE_STRETCH_NUDGE}"
        )

        # Per-nudge counters
        self._sec_eye = 0
        self._sec_hydration = 0
        self._sec_stretch = 0

        self._tick_listeners: List[Callable[[int], None]] = []

    # ---------------- Listener registration ----------------
    def add_tick_listener(self, cb: Callable[[int], None]) -> None:
        """Register a listener to be called every tick with uptime seconds."""
        if cb not in self._tick_listeners:
            self._tick_listeners.append(cb)

    def remove_tick_listener(self, cb: Callable[[int], None]) -> None:
        """Remove a previously registered listener."""
        if cb in self._tick_listeners:
            self._tick_listeners.remove(cb)

    # ---------------- Loop control ----------------
    def start(self) -> None:
        """Start the loop (no-op if already running)."""
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        """Pause the loop (counters are preserved)."""
        self._running = False

    def is_running(self) -> bool:
        """Return True if the loop is currently running."""
        return self._running

    def uptime(self) -> int:
        """Total seconds since the loop started."""
        return self._seconds_since_start

    # ---------------- Internal scheduling ----------------
    def _tick(self) -> None:
        """Execute one tick and schedule the next via `root.after`."""
        if not self._running:
            return

        self._seconds_since_start += 1

        # Optional wellness nudges (config-driven)
        if ENABLE_EYE_CARE:
            self._sec_eye += 1
            if self._sec_eye >= EYE_BREAK_INTERVAL_SEC:
                show_toast(self.root, EYE_BREAK_MESSAGE, 3000)
                self._sec_eye = 0

        if ENABLE_HYDRATION_NUDGE:
            self._sec_hydration += 1
            if self._sec_hydration >= HYDRATION_NUDGE_INTERVAL_SEC:
                show_toast(self.root, HYDRATION_NUDGE_MESSAGE, 3000)
                self._sec_hydration = 0

        if ENABLE_STRETCH_NUDGE:
            self._sec_stretch += 1
            if self._sec_stretch >= STRETCH_NUDGE_INTERVAL_SEC:
                show_toast(self.root, STRETCH_NUDGE_MESSAGE, 3000)
                self._sec_stretch = 0

        # Notify listeners (e.g., focus timer, hydration UI, etc.)
        for cb in list(self._tick_listeners):
            try:
                cb(self._seconds_since_start)
            except Exception:
                # Guard against third-party listener exceptions
                pass

        # Schedule next tick
        self.root.after(self.interval_ms, self._tick)
