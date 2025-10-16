"""
features/hydration/controller.py
--------------------------------
Dynamic hydration goal calculator based on:
- gender
- body weight
- climate/temperature
- physical activity level

Includes change listeners to automatically refresh the UI and
reset hydration state when settings change.
"""

from dataclasses import dataclass
from typing import Callable, List

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
GLASS_ML = 250

# Baseline daily intake (IOM guidelines)
_MALE_BASE_ML = 3700
_FEMALE_BASE_ML = 2700

# Climate multipliers
_CLIMATE_FACTORS = {"cool": 0.90, "temperate": 1.00, "hot": 1.20}

# Activity multipliers
_ACTIVITY_FACTORS = {"low": 0.95, "moderate": 1.00, "high": 1.15}


# ------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------
@dataclass
class HydrationProfile:
    sex: str = "female"            # "male" | "female"
    weight_kg: float | None = None
    climate: str = "temperate"     # "cool" | "temperate" | "hot"
    activity: str = "moderate"     # "low" | "moderate" | "high"


@dataclass
class HydrationState:
    goal_ml: int
    total_ml: int
    profile: HydrationProfile


# ------------------------------------------------------------
# Goal computation
# ------------------------------------------------------------
def _compute_goal_ml(profile: HydrationProfile) -> int:
    """
    Compute daily hydration goal (ml) based on profile.
    """
    # 1) Weight-based (≈35 ml/kg) or baseline per gender
    if profile.weight_kg and profile.weight_kg > 0:
        base = profile.weight_kg * 35.0
    else:
        base = _MALE_BASE_ML if profile.sex.lower() == "male" else _FEMALE_BASE_ML

    # 2) Adjust for climate
    base *= _CLIMATE_FACTORS.get(profile.climate, 1.0)

    # 3) Adjust for activity
    base *= _ACTIVITY_FACTORS.get(profile.activity, 1.0)

    # 4) Clamp to safe limits (1.2–6.0 L)
    goal = int(round(base))
    goal = max(1200, min(goal, 6000))
    return goal


# ------------------------------------------------------------
# Internal state & listeners
# ------------------------------------------------------------
_profile = HydrationProfile()
_state = HydrationState(goal_ml=_compute_goal_ml(_profile), total_ml=0, profile=_profile)

_listeners: List[Callable[[], None]] = []


def _emit_change():
    for cb in list(_listeners):
        try:
            cb()
        except Exception:
            pass


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------
def add_change_listener(cb: Callable[[], None]) -> None:
    """UI can register here for auto-refresh on hydration state change."""
    if cb not in _listeners:
        _listeners.append(cb)

def remove_change_listener(cb: Callable[[], None]) -> None:
    if cb in _listeners:
        _listeners.remove(cb)

# Backward compatibility
add_on_change_listener = add_change_listener
remove_on_change_listener = remove_change_listener


def set_profile(
    sex: str | None = None,
    weight_kg: float | None = None,
    climate: str | None = None,
    activity: str | None = None,
) -> None:
    """Update profile and recompute hydration goal."""
    if sex is not None:
        _state.profile.sex = sex.lower().strip() or _state.profile.sex
    if weight_kg is not None:
        try:
            w = float(weight_kg)
            _state.profile.weight_kg = w if w > 0 else None
        except Exception:
            pass
    if climate is not None:
        c = climate.lower().strip()
        if c in _CLIMATE_FACTORS:
            _state.profile.climate = c
    if activity is not None:
        a = activity.lower().strip()
        if a in _ACTIVITY_FACTORS:
            _state.profile.activity = a

    _state.goal_ml = _compute_goal_ml(_state.profile)
    _emit_change()

def get_profile() -> HydrationProfile:
    return _state.profile

def get_goal_ml() -> int:
    return _state.goal_ml

def get_goal_glasses() -> int:
    return _state.goal_ml // GLASS_ML

def get_total_ml() -> int:
    return _state.total_ml

def get_total_glasses() -> int:
    return _state.total_ml // GLASS_ML

def get_progress_ratio() -> float:
    if _state.goal_ml <= 0:
        return 0.0
    return min(_state.total_ml / _state.goal_ml, 1.0)

def add_glass() -> None:
    """Add one glass (250 ml) and notify listeners."""
    _state.total_ml += GLASS_ML
    if _state.total_ml > 10_000:
        _state.total_ml = 10_000
    _emit_change()

def reset_today() -> None:
    """Reset daily intake (e.g., new day)."""
    _state.total_ml = 0
    _emit_change()
