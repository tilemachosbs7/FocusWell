# tests/test_focus_controller.py
from features.focus.controller import FocusController

def test_focus_timer_cycle():
    ctrl = FocusController()
    ctrl.set_routine(3, 2)  # 3s work, 2s break

    assert ctrl.get_phase() == "WORK"
    assert ctrl.get_remaining_sec() == 3
    assert not ctrl.is_running()

    ctrl.start()
    assert ctrl.is_running()

    # Simulate 3 seconds → end of WORK → switch to BREAK
    for i in range(3):
        ctrl.on_tick(i + 1)
    assert ctrl.get_phase() == "BREAK"
    assert ctrl.get_remaining_sec() == 2

    # Simulate 2 seconds → end of BREAK → back to WORK
    for i in range(2):
        ctrl.on_tick(10 + i)
    assert ctrl.get_phase() == "WORK"
    assert ctrl.get_remaining_sec() == 3

    ctrl.pause()
    assert not ctrl.is_running()

    ctrl.reset()
    assert ctrl.get_phase() == "IDLE"
    assert ctrl.get_remaining_sec() == 0
