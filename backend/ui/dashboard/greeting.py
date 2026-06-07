"""
Time-aware greeting text.
"""
from datetime import datetime
import arrow

def get_greeting() -> str:
    """Returns a greeting based on the current hour of the day.
    
    Before 12:00 -> "Good Morning"
    12:00 - 16:59 -> "Good Afternoon"
    17:00 - 21:59 -> "Good Evening"
    22:00 onwards -> "Good Night"
    """
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
    """Returns the current date formatted like 'Saturday, 7 June 2026' using Arrow."""
    return arrow.now().format("dddd, D MMMM YYYY")
