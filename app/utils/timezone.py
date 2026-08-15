"""
Display-time helper: the DB always stores UTC (best practice — never store
local time), and we convert to IST only at render time.
"""
from datetime import timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def to_ist(dt):
    """Convert a stored (naive-UTC or aware) datetime to IST for display."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)
