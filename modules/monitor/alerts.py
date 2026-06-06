"""
Thresholds, alert emission.
"""

def get_progress_bar_color(percentage: float) -> str:
    """Get stylesheet color code for progress bar based on utilization percentage.
    
    Thresholds:
      - Above 90%: Red (#E63946)
      - Above 75%: Amber (#FFB703)
      - Otherwise: Green (#2A9D8F)
    """
    if percentage > 90.0:
        return "#E63946"  # Red
    elif percentage > 75.0:
        return "#FFB703"  # Amber
    return "#2A9D8F"      # Green
