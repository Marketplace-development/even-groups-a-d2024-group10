from datetime import datetime, timedelta

def utc_to_plus_one(dt):
    if dt is None:  # Check of de datum geldig is
        return None
    return dt + timedelta(hours=1)

def format_datetime(value, format='%d-%m-%Y %H:%M'):
    """Format a datetime object using strftime."""
    if value is None:
        return ''
    return value.strftime(format)

