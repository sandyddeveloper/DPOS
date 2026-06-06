"""
Human-readable time, relative dates.
"""
from datetime import datetime
import arrow

def get_greeting() -> str:
    """Returns a greeting based on the current hour of the day."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    elif hour < 22:
        return "Good Evening"
    else:
        return "Good Night"

def get_formatted_date() -> str:
    """Returns the current date formatted like 'Saturday, 7 June 2026'."""
    return arrow.now().format("dddd, D MMMM YYYY")

def format_relative_time(dt: datetime) -> str:
    """Returns a human-readable relative time string (e.g. '3 minutes ago')."""
    if not dt:
        return ""
    try:
        return arrow.get(dt).humanize()
    except Exception:
        return str(dt)
