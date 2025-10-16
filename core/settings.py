"""
core/settings.py
----------------
Persistent user settings storage (JSON-based) for FocusWell.

Defines the AppSettings dataclass used to keep user preferences
such as gender, weight, temperature, activity level, and timezone.

Provides simple load/save helpers to serialize/deserialize the settings
to `settings.json` located one level above the /core folder.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import os
from typing import Optional

# ------------------------------------------------------------
# Path to settings file (one level above /core)
# ------------------------------------------------------------
_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
_SETTINGS_PATH = os.path.normpath(_SETTINGS_PATH)

# ------------------------------------------------------------
# Dataclass: AppSettings
# ------------------------------------------------------------
@dataclass
class AppSettings:
    sex: str = "female"                 # "male" | "female"
    weight_kg: Optional[float] = None   # e.g. 68.0
    temperature_c: Optional[float] = None  # ambient temperature
    activity: str = "moderate"          # "low" | "moderate" | "high"
    timezone: str = ""                  # IANA tz, e.g., "Europe/Athens"

    def is_complete(self) -> bool:
        """
        Return True if all required fields are properly filled.
        """
        return (
            self.sex in ("male", "female")
            and isinstance(self.weight_kg, (int, float)) and (self.weight_kg or 0) > 0
            and isinstance(self.temperature_c, (int, float))
            and self.activity in ("low", "moderate", "high")
        )

# ------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    """Ensure that the parent directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

# ------------------------------------------------------------
# Public API: load / save
# ------------------------------------------------------------
def load_settings() -> AppSettings:
    """
    Load user settings from JSON file.
    Returns default settings if the file is missing or invalid.
    """
    try:
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppSettings(**data)
    except Exception:
        return AppSettings()

def save_settings(s: AppSettings) -> None:
    """
    Save current settings to JSON (UTF-8, pretty formatted).
    """
    _ensure_dir(_SETTINGS_PATH)
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, ensure_ascii=False, indent=2)
