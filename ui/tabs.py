"""
ui/tabs.py
----------
Settings window with a simple Time Zone picker (city-based), and hydration goal inputs.

Behavior:
- If the system has tzdata and ZoneInfo(tz) works → save the IANA time zone.
- If not (common on Windows without tzdata) → save the CURRENT UTC offset string (+HH:MM).
- Home reads the saved timezone dynamically and updates immediately.

Also updates the Hydration profile (sex, weight, temperature→climate, activity)
and resets the daily intake to match the new profile.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, timezone, date
from typing import List, Tuple, Dict, Optional

from core.settings import load_settings, save_settings, AppSettings
from features.hydration import controller as hc

# Try IANA time zones (requires tzdata on Windows)
try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

# -----------------------------
# Curated city list (IANA tz)
# -----------------------------
# Format: (IANA tz, "City, Country")
CITIES: List[Tuple[str, str]] = [
    # Europe
    ("Europe/Athens",       "Athens, Greece"),
    ("Europe/London",       "London, United Kingdom"),
    ("Europe/Paris",        "Paris, France"),
    ("Europe/Berlin",       "Berlin, Germany"),
    ("Europe/Madrid",       "Madrid, Spain"),
    ("Europe/Rome",         "Rome, Italy"),
    ("Europe/Amsterdam",    "Amsterdam, Netherlands"),
    ("Europe/Zurich",       "Zurich, Switzerland"),
    ("Europe/Stockholm",    "Stockholm, Sweden"),
    ("Europe/Oslo",         "Oslo, Norway"),
    ("Europe/Helsinki",     "Helsinki, Finland"),
    ("Europe/Istanbul",     "Istanbul, Türkiye"),
    ("Europe/Bucharest",    "Bucharest, Romania"),
    ("Europe/Warsaw",       "Warsaw, Poland"),
    ("Europe/Vienna",       "Vienna, Austria"),
    ("Europe/Dublin",       "Dublin, Ireland"),
    ("UTC",                 "UTC"),
    # America
    ("America/New_York",    "New York, USA"),
    ("America/Chicago",     "Chicago, USA"),
    ("America/Denver",      "Denver, USA"),
    ("America/Los_Angeles", "Los Angeles, USA"),
    ("America/Toronto",     "Toronto, Canada"),
    ("America/Mexico_City", "Mexico City, Mexico"),
    ("America/Sao_Paulo",   "São Paulo, Brazil"),
    # Asia
    ("Asia/Dubai",          "Dubai, UAE"),
    ("Asia/Riyadh",         "Riyadh, Saudi Arabia"),
    ("Asia/Tehran",         "Tehran, Iran"),
    ("Asia/Karachi",        "Karachi, Pakistan"),
    ("Asia/Kolkata",        "Kolkata, India"),
    ("Asia/Bangkok",        "Bangkok, Thailand"),
    ("Asia/Singapore",      "Singapore, Singapore"),
    ("Asia/Hong_Kong",      "Hong Kong, China"),
    ("Asia/Shanghai",       "Shanghai, China"),
    ("Asia/Tokyo",          "Tokyo, Japan"),
    ("Asia/Seoul",          "Seoul, South Korea"),
    # Africa
    ("Africa/Cairo",        "Cairo, Egypt"),
    ("Africa/Nairobi",      "Nairobi, Kenya"),
    ("Africa/Johannesburg", "Johannesburg, South Africa"),
    ("Africa/Casablanca",   "Casablanca, Morocco"),
    # Oceania
    ("Australia/Sydney",    "Sydney, Australia"),
    ("Australia/Melbourne", "Melbourne, Australia"),
    ("Pacific/Auckland",    "Auckland, New Zealand"),
]

# -----------------------------
# Fallback rules (no tzdata)
# -----------------------------
# rule: "EU" (DST), "US" (DST), "NONE" (fixed or simplified)
CITY_RULES: Dict[str, Tuple[str, float]] = {
    # Europe (EU DST)
    "Europe/Athens":      ("EU",  2),
    "Europe/Paris":       ("EU",  1),
    "Europe/Berlin":      ("EU",  1),
    "Europe/Madrid":      ("EU",  1),
    "Europe/Rome":        ("EU",  1),
    "Europe/Amsterdam":   ("EU",  1),
    "Europe/Zurich":      ("EU",  1),
    "Europe/Stockholm":   ("EU",  1),
    "Europe/Oslo":        ("EU",  1),
    "Europe/Helsinki":    ("EU",  2),
    "Europe/Bucharest":   ("EU",  2),
    "Europe/Warsaw":      ("EU",  1),
    "Europe/Vienna":      ("EU",  1),
    "Europe/Dublin":      ("EU",  0),
    "Europe/Istanbul":    ("NONE", 3),  # permanent +3
    "Europe/London":      ("EU",  0),
    "UTC":                ("NONE", 0),
    # America (US DST)
    "America/New_York":    ("US", -5),
    "America/Chicago":     ("US", -6),
    "America/Denver":      ("US", -7),
    "America/Los_Angeles": ("US", -8),
    "America/Toronto":     ("US", -5),
    "America/Mexico_City": ("US", -6),   # simplified
    "America/Sao_Paulo":   ("NONE", -3), # no DST now
    # Asia / Africa / Oceania (fixed offsets for simplicity)
    "Asia/Dubai":          ("NONE", 4),
    "Asia/Riyadh":         ("NONE", 3),
    "Asia/Tehran":         ("NONE", 3.5),
    "Asia/Karachi":        ("NONE", 5),
    "Asia/Kolkata":        ("NONE", 5.5),
    "Asia/Bangkok":        ("NONE", 7),
    "Asia/Singapore":      ("NONE", 8),
    "Asia/Hong_Kong":      ("NONE", 8),
    "Asia/Shanghai":       ("NONE", 8),
    "Asia/Tokyo":          ("NONE", 9),
    "Asia/Seoul":          ("NONE", 9),
    "Africa/Cairo":        ("NONE", 2),
    "Africa/Nairobi":      ("NONE", 3),
    "Africa/Johannesburg": ("NONE", 2),
    "Africa/Casablanca":   ("NONE", 1),
    "Australia/Sydney":    ("NONE", 10),  # simplified
    "Australia/Melbourne": ("NONE", 10),
    "Pacific/Auckland":    ("NONE", 12),
}

# -----------------------------
# DST helpers (fallback)
# -----------------------------
def _last_sunday(year: int, month: int) -> date:
    if month == 12:
        d = date(year + 1, 1, 1)
    else:
        d = date(year, month + 1, 1)
    d -= timedelta(days=1)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d

def _eu_is_dst(d: date) -> bool:
    start = _last_sunday(d.year, 3)   # last Sunday of March
    end   = _last_sunday(d.year, 10)  # last Sunday of October
    return start <= d < end

def _us_is_dst(d: date) -> bool:
    # 2nd Sunday in March
    d1 = date(d.year, 3, 1)
    while d1.weekday() != 6: d1 += timedelta(days=1)
    second_sun_march = d1 + timedelta(days=7)
    # 1st Sunday in November
    d2 = date(d.year, 11, 1)
    while d2.weekday() != 6: d2 += timedelta(days=1)
    first_sun_nov = d2
    return second_sun_march <= d < first_sun_nov

def _city_to_current_offset_str(tz_name: str, today: Optional[date] = None) -> str:
    if tz_name == "UTC":
        return "+00:00"
    rule, base = CITY_RULES.get(tz_name, ("NONE", 0))
    today = today or date.today()
    hours = base
    if rule == "EU" and _eu_is_dst(today):
        hours = base + 1
    elif rule == "US" and _us_is_dst(today):
        hours = base + 1
    sign = "+" if hours >= 0 else "-"
    ah = abs(hours); hh = int(ah); mm = int(round((ah - hh) * 60))
    return f"{sign}{hh:02d}:{mm:02d}"

def _format_city_display(tz: str, label: str) -> str:
    gmt = ""
    if ZoneInfo is not None:
        try:
            off = datetime.now(ZoneInfo(tz)).utcoffset() or timedelta(0)
            sign = "+" if off >= timedelta(0) else "-"
            off = abs(off); hh = off.seconds // 3600; mm = (off.seconds // 60) % 60
            gmt = f" — GMT{sign}{hh:02d}:{mm:02d}"
        except Exception:
            pass
    return f"{label} ({tz}){gmt}"

def _tzinfo_from_offset_str(s: str) -> timezone:
    sign = 1 if s.startswith("+") else -1
    hh = int(s[1:3]); mm = int(s[4:6])
    return timezone(sign * timedelta(hours=hh, minutes=mm))

# -----------------------------
# UI
# -----------------------------
def open_settings_window(root: tk.Tk) -> dict:
    win = tk.Toplevel(root)
    win.title("Settings")
    win.geometry("680x600")
    win.minsize(660, 560)

    notebook = ttk.Notebook(win); notebook.pack(fill="both", expand=True)

    settings_tab = ttk.Frame(notebook); notebook.add(settings_tab, text="Settings")
    wrapper = ttk.Frame(settings_tab, padding=16); wrapper.pack(fill="both", expand=True)

    ttk.Label(wrapper, text="App Settings ⚙️", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

    current = load_settings()

    # ------- Hydration Inputs -------
    form = ttk.LabelFrame(wrapper, text="Hydration Goal Inputs", padding=12)
    form.pack(fill="x")

    ttk.Label(form, text="Sex:").grid(row=0, column=0, sticky="w")
    sex_var = tk.StringVar(value=current.sex)
    ttk.Combobox(form, textvariable=sex_var, values=["female", "male"], state="readonly", width=12)\
        .grid(row=0, column=1, sticky="w", padx=(6, 16))

    ttk.Label(form, text="Weight (kg):").grid(row=0, column=2, sticky="w")
    weight_var = tk.StringVar(value="" if current.weight_kg is None else str(current.weight_kg))
    ttk.Entry(form, textvariable=weight_var, width=12).grid(row=0, column=3, sticky="w")

    ttk.Label(form, text="Ambient temperature (°C):").grid(row=1, column=0, sticky="w", pady=(8, 0))
    temp_var = tk.StringVar(value="" if current.temperature_c is None else str(current.temperature_c))
    ttk.Entry(form, textvariable=temp_var, width=12).grid(row=1, column=1, sticky="w", pady=(8, 0))

    ttk.Label(form, text="Activity level:").grid(row=1, column=2, sticky="w", pady=(8, 0))
    activity_var = tk.StringVar(value=current.activity)
    ttk.Combobox(form, textvariable=activity_var, values=["low", "moderate", "high"], state="readonly", width=12)\
        .grid(row=1, column=3, sticky="w", pady=(8, 0))

    # ------- Time Zone (City only) -------
    tz_group = ttk.LabelFrame(wrapper, text="Time Zone (select city)", padding=12)
    tz_group.pack(fill="both", pady=(16, 0))

    # Search + list
    top_bar = ttk.Frame(tz_group); top_bar.pack(fill="x")
    ttk.Label(top_bar, text="Search:").pack(side="left")
    search_var = tk.StringVar(); ttk.Entry(top_bar, textvariable=search_var, width=28).pack(side="left", padx=(6, 0))

    city_list = tk.Listbox(tz_group, height=12, exportselection=False)
    city_list.pack(side="left", fill="both", expand=True, pady=(8,0))
    scroll = ttk.Scrollbar(tz_group, orient="vertical", command=city_list.yview)
    scroll.pack(side="left", fill="y", pady=(8,0))
    city_list.configure(yscrollcommand=scroll.set)

    preview_var = tk.StringVar(value="")
    ttk.Label(tz_group, textvariable=preview_var, font=("Consolas", 10)).pack(anchor="w", pady=(8,0))

    # Populate list
    def _reload_list():
        q = (search_var.get() or "").strip().lower()
        city_list.delete(0, "end")
        for tz, label in CITIES:
            display = _format_city_display(tz, label)
            if not q or q in label.lower() or q in tz.lower():
                city_list.insert("end", display)

    _reload_list()

    def _select_from_current():
        cur = (current.timezone or "").strip()
        if not cur:
            return
        for i in range(city_list.size()):
            txt = city_list.get(i)
            if f"({cur})" in txt:
                city_list.selection_set(i); city_list.see(i)
                # preview with IANA or with fallback offset
                try:
                    now_txt = datetime.now(ZoneInfo(cur)).strftime("%Y-%m-%d  %H:%M:%S") if ZoneInfo else None
                except Exception:
                    now_txt = None
                if not now_txt:
                    off = _city_to_current_offset_str(cur)
                    now_txt = datetime.now(_tzinfo_from_offset_str(off)).strftime("%Y-%m-%d  %H:%M:%S")
                preview_var.set(f"Preview: {txt.split(' — ')[0]} → {now_txt}")
                return

    _select_from_current()

    def _on_search_change(*_):
        _reload_list()

    search_var.trace_add("write", _on_search_change)

    def _on_select(_evt=None):
        sel = city_list.curselection()
        if not sel:
            preview_var.set(""); return
        text = city_list.get(sel[0])
        tz = text.split("(")[-1].split(")")[0]
        # Preview: try IANA, else use offset
        now_txt = None
        if ZoneInfo is not None:
            try:
                now_txt = datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d  %H:%M:%S")
            except Exception:
                now_txt = None
        if not now_txt:
            off = _city_to_current_offset_str(tz)
            now_txt = datetime.now(_tzinfo_from_offset_str(off)).strftime("%Y-%m-%d  %H:%M:%S")
        preview_var.set(f"Preview: {text.split(' — ')[0]} → {now_txt}")

    city_list.bind("<<ListboxSelect>>", _on_select)

    # ------- Buttons -------
    btns = ttk.Frame(wrapper); btns.pack(fill="x", pady=(16, 0))
    apply_btn = ttk.Button(btns, text="Apply & Save")
    close_btn = ttk.Button(btns, text="Close", command=win.destroy)
    close_btn.pack(side="right"); apply_btn.pack(side="right", padx=(0, 8))

    # Helpers
    def _parse_float(s: str) -> Optional[float]:
        try: return float((s or "").replace(",", "."))
        except Exception: return None

    def on_apply():
        # Validate hydration fields
        sex = (sex_var.get() or "").strip()
        w = _parse_float(weight_var.get())
        t = _parse_float(temp_var.get())
        act = (activity_var.get() or "").strip()

        if sex not in ("male", "female"):
            messagebox.showerror("Invalid", "Choose sex (male or female).", parent=win); return
        if not w or w <= 0:
            messagebox.showerror("Invalid", "Enter a valid weight (kg).", parent=win); return
        if t is None:
            messagebox.showerror("Invalid", "Enter ambient temperature (°C).", parent=win); return
        if act not in ("low", "moderate", "high"):
            messagebox.showerror("Invalid", "Choose an activity level.", parent=win); return

        # Selected city
        sel = city_list.curselection()
        if not sel:
            messagebox.showerror("Time Zone", "Select a city (e.g., Athens, Greece).", parent=win); return
        text = city_list.get(sel[0])
        tz = text.split("(")[-1].split(")")[0]

        # If we can instantiate ZoneInfo(tz) NOW → save IANA, else save current offset
        final_tz = None
        if ZoneInfo is not None:
            try:
                ZoneInfo(tz)  # probe
                final_tz = tz
            except Exception:
                final_tz = None
        if final_tz is None:
            final_tz = _city_to_current_offset_str(tz)

        # Hydration: update profile + reset (consistent with Home)
        climate = "cool" if (t or 0) <= 10 else ("hot" if (t or 0) >= 25 else "temperate")
        hc.set_profile(sex=sex, weight_kg=w, climate=climate, activity=act)
        hc.reset_today()

        # Save settings
        new_settings = AppSettings(sex=sex, weight_kg=w, temperature_c=t, activity=act, timezone=final_tz)
        save_settings(new_settings)

        messagebox.showinfo("Saved", f"Settings updated.\nTime Zone set to: {final_tz}", parent=win)

    apply_btn.configure(command=on_apply)

    return {"window": win, "notebook": notebook, "settings": settings_tab}
