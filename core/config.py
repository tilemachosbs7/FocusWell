"""
core/config.py
---------------
Global configuration for FocusWell.

This file centralizes all feature toggles and reminder intervals/messages
used across the app (eye care, hydration, stretching, and focus timer).

Editing these values allows you to customize the reminder frequency
and messages without modifying any logic in other modules.
"""

# ============================================================
# Wellness nudges (used by AppLoop)
# ============================================================

# Feature toggles
ENABLE_EYE_CARE = False          # 👀 20-20-20 eye-care rule
ENABLE_HYDRATION_NUDGE = False   # 💧 gentle sip reminder
ENABLE_STRETCH_NUDGE = False     # 🧘 stand & stretch reminder

# Reminder intervals (in seconds)
# Defines how often each nudge appears.
EYE_BREAK_INTERVAL_SEC       = 20 * 60   # every 20 minutes
HYDRATION_NUDGE_INTERVAL_SEC = 60 * 60   # every 60 minutes
STRETCH_NUDGE_INTERVAL_SEC   = 45 * 60   # every 45 minutes

# Reminder messages (shown in toast popups)
EYE_BREAK_MESSAGE       = "👀 20-20-20: look 20 ft away for 20 seconds."
HYDRATION_NUDGE_MESSAGE = "💧 Hydration break — take a small sip (≈250 ml)."
STRETCH_NUDGE_MESSAGE   = "🧘 Stand up and stretch for 30 seconds."

# ============================================================
# Focus-timer inline reminders (during WORK phase)
# ============================================================

# These reminders trigger while the focus timer is active (WORK phase only).
FOCUS_EYE_REMINDER_SEC      = 20 * 60
FOCUS_EYE_REMINDER_MESSAGE  = "👀 20-20-20: rest your eyes briefly."

FOCUS_HYDRATION_REMINDER_SEC     = 60 * 60
FOCUS_HYDRATION_REMINDER_MESSAGE = "💧 Mini hydration: a quick sip."
