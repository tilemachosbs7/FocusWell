"""
features/focus/controller.py
-----------------------------
Core logic for the Focus Timer feature.

Manages the "Work → Break" cycle according to user-defined routine.
Provides callbacks to the UI (view) for updates and phase changes.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

# ---- Demo durations (for quick testing)
DEMO_WORK_SEC = 10
DEMO_BREAK_SEC = 5

# ---- Default production durations
DEFAULT_WORK_SEC = 25 * 60
DEFAULT_BREAK_SEC = 5 * 60

Phase = str  # "IDLE" | "WORK" | "BREAK"


@dataclass
class FocusState:
    """Represents the current state of the focus timer."""
    phase: Phase = "IDLE"
    running: bool = False
    remaining_sec: int = 0
    routine: Tuple[int, int] = (DEMO_WORK_SEC, DEMO_BREAK_SEC)  # (work, break)


class FocusController:
    """
    Handles timer logic: starting, pausing, resetting, and switching phases.
    """

    def __init__(self) -> None:
        self._state = FocusState()
        self._on_update: Optional[Callable[[], None]] = None
        self._on_phase_change: Optional[Callable[[Phase], None]] = None

    # ----- Callbacks to View -----
    def set_on_update(self, cb: Callable[[], None]) -> None:
        """Register callback to update the UI each time the timer state changes."""
        self._on_update = cb

    def set_on_phase_change(self, cb: Callable[[Phase], None]) -> None:
        """Register callback triggered when phase changes (WORK ↔ BREAK)."""
        self._on_phase_change = cb

    # ----- Public API -----
    def set_routine(self, work_sec: int, break_sec: int) -> None:
        """Define durations for work and break sessions."""
        self._state.routine = (work_sec, break_sec)
        if self._state.phase in ("IDLE", "WORK"):
            self._state.remaining_sec = work_sec
            self._state.phase = "WORK"
        else:
            self._state.remaining_sec = break_sec
        self._emit_update()

    def start(self) -> None:
        """Start or resume the timer."""
        if self._state.phase == "IDLE":
            self._state.phase = "WORK"
            self._state.remaining_sec = self._state.routine[0]
            self._emit_phase_change()
        self._state.running = True
        self._emit_update()

    def pause(self) -> None:
        """Pause the timer."""
        self._state.running = False
        self._emit_update()

    def reset(self) -> None:
        """Reset to IDLE state."""
        self._state.running = False
        self._state.phase = "IDLE"
        self._state.remaining_sec = 0
        self._emit_update()

    def on_tick(self, _total_seconds: int) -> None:
        """Called every second by AppLoop to decrease remaining time."""
        if not self._state.running:
            return
        if self._state.remaining_sec > 0:
            self._state.remaining_sec -= 1
            self._emit_update()
            if self._state.remaining_sec == 0:
                self._switch_phase()

    # ----- Getters -----
    def get_phase(self) -> Phase:
        return self._state.phase

    def is_running(self) -> bool:
        return self._state.running

    def get_remaining_sec(self) -> int:
        return self._state.remaining_sec

    def get_routine(self) -> Tuple[int, int]:
        return self._state.routine

    # ----- Internal -----
    def _switch_phase(self) -> None:
        """Switch between work and break phases."""
        work_sec, break_sec = self._state.routine
        if self._state.phase == "WORK":
            self._state.phase = "BREAK"
            self._state.remaining_sec = break_sec
        else:
            self._state.phase = "WORK"
            self._state.remaining_sec = work_sec
        self._emit_phase_change()
        self._emit_update()

    def _emit_update(self) -> None:
        if self._on_update:
            try:
                self._on_update()
            except Exception:
                pass

    def _emit_phase_change(self) -> None:
        if self._on_phase_change:
            try:
                self._on_phase_change(self._state.phase)
            except Exception:
                pass
