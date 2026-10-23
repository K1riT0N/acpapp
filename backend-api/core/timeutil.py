"""'Now' and 'today' for Nadd, always in the shops' time zone (Asia/Bangkok).

The server itself may run in UTC, so never call date.today() or datetime.now() without a time zone.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo("Asia/Bangkok")

DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]  # 0 = Sunday
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def now() -> datetime:
    return datetime.now(BANGKOK)


def today() -> date:
    return now().date()


def day_of_week(d: date) -> int:
    """0 = Sunday ... 6 = Saturday, the numbering used by business_hours (Python's weekday() starts on Monday)."""
    return (d.weekday() + 1) % 7


def fmt_date(d: date) -> str:
    """'Thu 24 Sep', same as the prototype's fmtDate."""
    return f"{DAY_NAMES[day_of_week(d)][:3]} {d.day} {MONTHS[d.month - 1][:3]}"


def fmt_date_long(d: date) -> str:
    """'Thursday 24 September', same as the prototype's fmtDateLong."""
    return f"{DAY_NAMES[day_of_week(d)]} {d.day} {MONTHS[d.month - 1]}"


def month_name(d: date) -> str:
    return MONTHS[d.month - 1]


def baht(amount: int) -> str:
    """'฿1,260', same as the prototype's baht()."""
    return f"฿{amount:,}"


def add_months(d: date, n: int) -> date:
    """Same day n months later; if that month is shorter, its last day (31 Jan + 1 month = 28 Feb)."""
    month_index = d.month - 1 + n
    year, month = d.year + month_index // 12, month_index % 12 + 1
    next_month_first = date(year + (month == 12), month % 12 + 1, 1)
    last_day = (next_month_first - timedelta(days=1)).day
    return date(year, month, min(d.day, last_day))
