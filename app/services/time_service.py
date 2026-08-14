from zoneinfo import ZoneInfo
from datetime import datetime, date

GHANA_TZ = ZoneInfo("Africa/Accra")

def get_current_time():
    """Returns the current datetime in Africa/Accra timezone."""
    return datetime.now(GHANA_TZ)

def get_current_date():
    """Returns the current date in Africa/Accra timezone."""
    return get_current_time().date()

def utc_to_ghana(utc_dt):
    """Converts a UTC datetime to Africa/Accra datetime."""
    if not utc_dt:
        return None
    if utc_dt.tzinfo is None:
        # Assume naive datetime from DB is UTC
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(GHANA_TZ)

def to_utc(dt):
    """Converts a naive or aware datetime to UTC."""
    if dt.tzinfo is None:
        # If naive, assume it was meant to be GHANA_TZ (our app's default for input)
        dt = dt.replace(tzinfo=GHANA_TZ)
    return dt.astimezone(ZoneInfo("UTC"))

def parse_date(date_string):
    """Parses a YYYY-MM-DD string into a Python date object."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def format_date(d):
    """Formats a date object to YYYY-MM-DD."""
    if not d:
        return ""
    return d.strftime('%Y-%m-%d')

def format_datetime(dt):
    """Formats a datetime to a readable string in Ghana time."""
    if not dt:
        return ""
    ghana_dt = utc_to_ghana(dt) if dt.tzinfo is None or dt.tzinfo.key == 'UTC' else dt
    return ghana_dt.strftime('%Y-%m-%d %H:%M:%S')
