# tests/test_hydration_controller.py
from features.hydration import controller as hc

def test_hydration_goal_computation():
    hc.reset_today()
    hc.set_profile(sex="male", weight_kg=80, climate="hot", activity="high")

    # Expected: 80 * 35 = 2800 * 1.20 * 1.15 = 3864 ml
    assert hc.get_goal_ml() == 3864
    assert hc.get_goal_glasses() == 3864 // hc.GLASS_ML
    assert hc.get_total_ml() == 0
    assert hc.get_progress_ratio() == 0.0

    hc.add_glass()
    assert hc.get_total_ml() == hc.GLASS_ML
    assert 0.0 < hc.get_progress_ratio() <= 1.0

def test_hydration_goal_clamped_limits():
    hc.reset_today()

    # Too low: should clamp to at least 1200 ml
    hc.set_profile(sex="female", weight_kg=30, climate="cool", activity="low")
    assert hc.get_goal_ml() >= 1200

    # Too high: should clamp to at most 6000 ml
    hc.set_profile(sex="male", weight_kg=200, climate="hot", activity="high")
    assert hc.get_goal_ml() <= 6000
