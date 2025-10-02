"""
Date and time utility functions
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def format_datetime(
    dt: datetime, 
    format_string: str = "%Y-%m-%d %H:%M:%S",
    timezone_name: Optional[str] = None
) -> str:
    """Format datetime to string with optional timezone conversion"""
    if not dt:
        return ""
    
    # Convert to specified timezone if provided
    if timezone_name:
        try:
            tz = pytz.timezone(timezone_name)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(tz)
        except Exception:
            pass  # Use original datetime if timezone conversion fails
    
    return dt.strftime(format_string)


def parse_datetime(
    date_string: str, 
    format_string: str = "%Y-%m-%d %H:%M:%S",
    timezone_name: Optional[str] = None
) -> Optional[datetime]:
    """Parse datetime string with optional timezone"""
    if not date_string:
        return None
    
    try:
        dt = datetime.strptime(date_string, format_string)
        
        # Add timezone if specified
        if timezone_name:
            try:
                tz = pytz.timezone(timezone_name)
                dt = tz.localize(dt)
            except Exception:
                dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except ValueError:
        return None


def get_timezone(timezone_name: str) -> Optional[timezone]:
    """Get timezone object by name"""
    try:
        return pytz.timezone(timezone_name)
    except Exception:
        return None


def days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate days between two dates"""
    if not start_date or not end_date:
        return 0
    
    # Ensure both dates are timezone-aware or naive
    if start_date.tzinfo is None and end_date.tzinfo is not None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    elif start_date.tzinfo is not None and end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    delta = end_date - start_date
    return delta.days


def hours_between(start_time: datetime, end_time: datetime) -> float:
    """Calculate hours between two datetimes"""
    if not start_time or not end_time:
        return 0.0
    
    # Ensure both times are timezone-aware or naive
    if start_time.tzinfo is None and end_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    elif start_time.tzinfo is not None and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    delta = end_time - start_time
    return delta.total_seconds() / 3600


def add_days(dt: datetime, days: int) -> datetime:
    """Add days to datetime"""
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to datetime"""
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Add minutes to datetime"""
    return dt + timedelta(minutes=minutes)


def start_of_day(dt: datetime) -> datetime:
    """Get start of day (00:00:00)"""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """Get end of day (23:59:59.999999)"""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_week(dt: datetime) -> datetime:
    """Get start of week (Monday 00:00:00)"""
    days_since_monday = dt.weekday()
    monday = dt - timedelta(days=days_since_monday)
    return start_of_day(monday)


def end_of_week(dt: datetime) -> datetime:
    """Get end of week (Sunday 23:59:59.999999)"""
    days_until_sunday = 6 - dt.weekday()
    sunday = dt + timedelta(days=days_until_sunday)
    return end_of_day(sunday)


def start_of_month(dt: datetime) -> datetime:
    """Get start of month (1st day 00:00:00)"""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(dt: datetime) -> datetime:
    """Get end of month (last day 23:59:59.999999)"""
    # Get first day of next month, then subtract one day
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    
    last_day = next_month - timedelta(days=1)
    return end_of_day(last_day)


def is_weekend(dt: datetime) -> bool:
    """Check if datetime is on weekend (Saturday or Sunday)"""
    return dt.weekday() >= 5


def is_business_day(dt: datetime) -> bool:
    """Check if datetime is on business day (Monday to Friday)"""
    return dt.weekday() < 5


def get_age_in_years(birth_date: datetime, reference_date: Optional[datetime] = None) -> int:
    """Calculate age in years"""
    if not birth_date:
        return 0
    
    if reference_date is None:
        reference_date = utc_now()
    
    age = reference_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(0, age)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 0:
        return "0 seconds"
    
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f} minutes"
    
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f} hours"
    
    days = hours / 24
    return f"{days:.1f} days"


def get_relative_time(dt: datetime, reference_time: Optional[datetime] = None) -> str:
    """Get relative time string (e.g., '2 hours ago', 'in 3 days')"""
    if not dt:
        return "unknown"
    
    if reference_time is None:
        reference_time = utc_now()
    
    # Ensure both times have timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    
    delta = dt - reference_time
    total_seconds = delta.total_seconds()
    
    if total_seconds == 0:
        return "now"
    
    future = total_seconds > 0
    total_seconds = abs(total_seconds)
    
    if total_seconds < 60:
        unit = "second" if total_seconds == 1 else "seconds"
        value = int(total_seconds)
    elif total_seconds < 3600:  # Less than 1 hour
        value = int(total_seconds / 60)
        unit = "minute" if value == 1 else "minutes"
    elif total_seconds < 86400:  # Less than 1 day
        value = int(total_seconds / 3600)
        unit = "hour" if value == 1 else "hours"
    elif total_seconds < 2592000:  # Less than 30 days
        value = int(total_seconds / 86400)
        unit = "day" if value == 1 else "days"
    elif total_seconds < 31536000:  # Less than 1 year
        value = int(total_seconds / 2592000)
        unit = "month" if value == 1 else "months"
    else:
        value = int(total_seconds / 31536000)
        unit = "year" if value == 1 else "years"
    
    if future:
        return f"in {value} {unit}"
    else:
        return f"{value} {unit} ago"


def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> Optional[datetime]:
    """Convert datetime from one timezone to another"""
    try:
        from_timezone = pytz.timezone(from_tz)
        to_timezone = pytz.timezone(to_tz)
        
        # If datetime is naive, localize it to from_tz
        if dt.tzinfo is None:
            dt = from_timezone.localize(dt)
        
        # Convert to target timezone
        return dt.astimezone(to_timezone)
    except Exception:
        return None


def get_common_timezones() -> list[str]:
    """Get list of common timezone names"""
    return [
        'UTC',
        'US/Eastern',
        'US/Central',
        'US/Mountain',
        'US/Pacific',
        'Europe/London',
        'Europe/Paris',
        'Europe/Berlin',
        'Asia/Tokyo',
        'Asia/Shanghai',
        'Asia/Kolkata',
        'Australia/Sydney',
        'America/New_York',
        'America/Chicago',
        'America/Denver',
        'America/Los_Angeles',
    ]