import re
import zoneinfo
from datetime import datetime, date, timedelta, timezone, tzinfo
from typing import Optional, Tuple


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_timezone(tz_name: Optional[str] = None) -> tzinfo:
    """
    Safely resolve a timezone using zoneinfo.ZoneInfo.
    Falls back to the host system's local timezone, or UTC if resolving fails.
    """
    if tz_name and isinstance(tz_name, str):
        cleaned = tz_name.strip()
        if cleaned:
            try:
                return zoneinfo.ZoneInfo(cleaned)
            except Exception:
                pass

    # Safe fallback: host system local timezone or UTC
    try:
        local_tz = datetime.now().astimezone().tzinfo
        if local_tz is not None:
            return local_tz
    except Exception:
        pass

    return timezone.utc


def get_current_datetime(tz_name: Optional[str] = None) -> datetime:
    """
    Retrieve current timezone-aware timestamp for the student/system.
    Always uses actual runtime system time (never hardcoded).
    """
    tz = get_timezone(tz_name)
    return datetime.now(tz)


def get_today_str(tz_name: Optional[str] = None) -> str:
    """Return today's date in YYYY-MM-DD for the given timezone."""
    return get_current_datetime(tz_name).date().isoformat()


def get_day_of_week(date_str: str) -> str:
    """Return English day of week name (e.g. 'Monday') for YYYY-MM-DD."""
    dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    return dt.strftime("%A")


def calculate_days_remaining(exam_date_str: str, tz_name: Optional[str] = None) -> int:
    """Calculate days from today until exam date in given timezone."""
    today = get_current_datetime(tz_name).date()
    target = datetime.strptime(exam_date_str.strip(), "%Y-%m-%d").date()
    return (target - today).days


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes since midnight."""
    parts = time_str.strip().split(":")
    hours = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return hours * 60 + minutes


def minutes_to_time_str(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM string."""
    m = minutes % (24 * 60)
    hours = m // 60
    mins = m % 60
    return f"{hours:02d}:{mins:02d}"


def check_time_overlap(
    start_time_1: str,
    end_time_1: str,
    start_time_2: str,
    end_time_2: str
) -> bool:
    """
    Check if two time intervals overlap.
    Adjacent intervals (e.g. 10:00-11:00 and 11:00-12:00) do NOT overlap.
    Rule: start1 < end2 AND end1 > start2
    """
    s1 = time_to_minutes(start_time_1)
    e1 = time_to_minutes(end_time_1)
    s2 = time_to_minutes(start_time_2)
    e2 = time_to_minutes(end_time_2)

    return s1 < e2 and e1 > s2


def extract_relative_date_clue(prompt_text: str) -> Optional[str]:
    """Scan natural language prompt for explicit relative date expressions."""
    text = prompt_text.lower()

    # Exact ISO date check
    iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1)

    # Multi-word relative patterns first
    if "day after tomorrow" in text:
        return "day after tomorrow"
    if "tomorrow" in text:
        return "tomorrow"
    if "today" in text or "tonight" in text:
        return "today"

    # Next weekday (e.g. "next monday", "next friday")
    for wd in WEEKDAYS.keys():
        if f"next {wd}" in text:
            return f"next {wd}"

    # This weekday (e.g. "this monday", "this friday")
    for wd in WEEKDAYS.keys():
        if f"this {wd}" in text:
            return f"this {wd}"

    # Bare weekday mention (e.g. "on monday", "for friday")
    for wd in WEEKDAYS.keys():
        if re.search(rf"\b(on|for|by)\s+{wd}\b", text):
            return f"this {wd}"

    return None


def resolve_target_date(
    relative_str: Optional[str] = None,
    tz_name: Optional[str] = None,
    prompt_text: Optional[str] = None,
    base_date: Optional[date] = None
) -> Tuple[str, str]:
    """
    Deterministically resolve target date expression into ISO format (YYYY-MM-DD)
    and English weekday name.

    Conventions:
    - 'today': current date in student's timezone.
    - 'tomorrow': current date + 1 calendar day (properly crossing month/year boundaries).
    - 'day after tomorrow': current date + 2 calendar days.
    - 'this <weekday>': nearest future occurrence of <weekday> within the current 7-day cycle.
      If today is already that weekday, returns today.
    - 'next <weekday>': occurrence of <weekday> in the subsequent week:
      ((target_weekday - current_weekday) % 7) + 7 days.
    - ISO 'YYYY-MM-DD': parsed and validated.
    - If no date is given, checks `prompt_text` for clues; if none, defaults to tomorrow.

    Returns:
        (iso_date_str, weekday_name) e.g. ("2026-10-05", "Monday")
    """
    ref_dt = get_current_datetime(tz_name)
    current_d = base_date if base_date is not None else ref_dt.date()

    target_expr = (relative_str or "").strip().lower()

    if not target_expr and prompt_text:
        target_expr = (extract_relative_date_clue(prompt_text) or "").lower()

    # Check for direct ISO date format YYYY-MM-DD
    if re.match(r"^20\d{2}-\d{2}-\d{2}$", target_expr):
        try:
            parsed = datetime.strptime(target_expr, "%Y-%m-%d").date()
            return parsed.isoformat(), WEEKDAY_NAMES[parsed.weekday()]
        except ValueError:
            pass

    cur_wd = current_d.weekday()  # Monday is 0, Sunday is 6

    if target_expr in ["today", "tonight"]:
        resolved_d = current_d
    elif target_expr in ["tomorrow"]:
        resolved_d = current_d + timedelta(days=1)
    elif target_expr in ["day after tomorrow"]:
        resolved_d = current_d + timedelta(days=2)
    elif target_expr.startswith("this "):
        wd_part = target_expr.replace("this ", "").strip()
        if wd_part in WEEKDAYS:
            target_wd = WEEKDAYS[wd_part]
            days_ahead = (target_wd - cur_wd) % 7
            resolved_d = current_d + timedelta(days=days_ahead)
        else:
            resolved_d = current_d + timedelta(days=1)
    elif target_expr.startswith("next "):
        wd_part = target_expr.replace("next ", "").strip()
        if wd_part in WEEKDAYS:
            target_wd = WEEKDAYS[wd_part]
            # Next week's occurrence is at least 7 days ahead
            days_ahead = ((target_wd - cur_wd) % 7) + 7
            resolved_d = current_d + timedelta(days=days_ahead)
        else:
            resolved_d = current_d + timedelta(days=7)
    elif target_expr in WEEKDAYS:
        target_wd = WEEKDAYS[target_expr]
        days_ahead = (target_wd - cur_wd) % 7
        if days_ahead == 0:
            days_ahead = 7
        resolved_d = current_d + timedelta(days=days_ahead)
    else:
        # Default to tomorrow for upcoming study scheduling
        resolved_d = current_d + timedelta(days=1)

    return resolved_d.isoformat(), WEEKDAY_NAMES[resolved_d.weekday()]

