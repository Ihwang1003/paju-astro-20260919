# -*- coding: utf-8 -*-
"""Altitude / observing-window helper for a fixed date & location.

All the deep-sky objects in this list have fixed J2000 RA/Dec, so we can
compute a real altitude curve for the night of 2026-09-19/20 at Paju and
tell the user exactly when each object is usable tonight (>= ALT_THRESHOLD)
rather than a vague "best season" text. This is precise enough for planning
purposes (~1 minute resolution) without needing any external ephemeris
library.
"""
import math
from datetime import datetime, timedelta, timezone

LAT_DEG = 37.76
LON_DEG = 126.78
ALT_THRESHOLD_DEG = 20.0  # "usable" altitude given typical horizon obstructions

KST = timezone(timedelta(hours=9))
SESSION_START = datetime(2026, 9, 19, 20, 0, tzinfo=KST)
SESSION_END = datetime(2026, 9, 20, 6, 0, tzinfo=KST)
SESSION_HOURS = (SESSION_END - SESSION_START).total_seconds() / 3600.0  # 10.0

ALDEBARAN_RA = 4.5987   # 04h35m55s
ALDEBARAN_DEC = 16.5093  # +16 30 33


def julian_date(dt_utc):
    y, m = dt_utc.year, dt_utc.month
    d = dt_utc.day + (dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5


def gmst_hours(jd):
    T = (jd - 2451545.0) / 36525.0
    gmst_deg = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
                + 0.000387933 * T * T - (T ** 3) / 38710000.0)
    return (gmst_deg % 360.0) / 15.0


def altitude_deg(dt_kst, ra_h, dec_deg):
    dt_utc = dt_kst.astimezone(timezone.utc)
    jd = julian_date(dt_utc)
    lst_h = (gmst_hours(jd) + LON_DEG / 15.0) % 24.0
    H_deg = (lst_h - ra_h) * 15.0
    H = math.radians(((H_deg + 180) % 360) - 180)
    lat = math.radians(LAT_DEG)
    dec = math.radians(dec_deg)
    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(H)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def clock_str(hours_after_start):
    """hours_after_start (float, 0..~10) -> 'HH:MM' clock string, wrapping past midnight."""
    hours_after_start = max(0.0, min(SESSION_HOURS, hours_after_start))
    t = SESSION_START + timedelta(hours=hours_after_start)
    return t.strftime("%H:%M")


def compute_window(ra_h, dec_deg, threshold=ALT_THRESHOLD_DEG, step_min=5):
    """Sample altitude across the session and return
    (window_start_h, window_end_h, max_alt, max_alt_h, samples) where the
    window is the contiguous >=threshold interval overlapping/starting the
    session that matters for "how long do I still have tonight"."""
    n = int(SESSION_HOURS * 60 / step_min) + 1
    samples = []
    for i in range(n):
        h = i * step_min / 60.0
        t = SESSION_START + timedelta(hours=h)
        alt = altitude_deg(t, ra_h, dec_deg)
        samples.append((h, alt))

    above = [h for h, a in samples if a >= threshold]
    max_h, max_alt = max(samples, key=lambda p: p[1])

    if not above:
        return None, None, max_alt, max_h, samples

    # find contiguous run containing (or nearest after) t=0
    runs = []
    run_start = above[0]
    prev = above[0]
    for h in above[1:]:
        if h - prev > step_min / 60.0 + 1e-6:
            runs.append((run_start, prev))
            run_start = h
        prev = h
    runs.append((run_start, prev))

    # prefer the run that covers t=0; else the first run after t=0
    chosen = None
    for s, e in runs:
        if s <= 1e-6:
            chosen = (s, e)
            break
    if chosen is None:
        chosen = runs[0]

    start_h = max(0.0, chosen[0])
    end_h = chosen[1]
    # if the run reaches (near) the session end, treat as "through session end"
    if end_h >= SESSION_HOURS - step_min / 60.0:
        end_h = SESSION_HOURS
    return start_h, end_h, max_alt, max_h, samples


def describe_window(start_h, end_h, max_alt, max_h):
    if start_h is None:
        return (f"이날 세션 중 고도 {ALT_THRESHOLD_DEG:.0f}° 확보 어려움 "
                f"(최대고도 {max_alt:.0f}°, {clock_str(max_h)}경)"), 99.0
    if start_h <= 1e-6 and end_h >= SESSION_HOURS - 1e-6:
        return "20:00~06:00 밤새 관측 가능", end_h
    if start_h <= 1e-6:
        return f"20:00~{clock_str(end_h)} 관측 가능 (이후 고도 {ALT_THRESHOLD_DEG:.0f}° 미만)", end_h
    if end_h >= SESSION_HOURS - 1e-6:
        return f"{clock_str(start_h)}부터 새벽까지 관측 가능", end_h
    return f"{clock_str(start_h)}~{clock_str(end_h)} 관측 가능", end_h


def observing_window_for(ra_h, dec_deg):
    """Returns (text, sort_key_hours)."""
    start_h, end_h, max_alt, max_h, _ = compute_window(ra_h, dec_deg)
    return describe_window(start_h, end_h, max_alt, max_h)
