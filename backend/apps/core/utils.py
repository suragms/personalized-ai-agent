"""Small shared utilities (dates, text, math)."""
import re
from datetime import date, timedelta

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def start_of_week(day: date | None = None) -> date:
    """ISO week start (Monday) for the given day (defaults to today)."""
    day = day or date.today()
    return day - timedelta(days=day.weekday())


def daterange(start: date, end: date, inclusive: bool = True):
    """Yield consecutive dates from start to end."""
    stop = end + (timedelta(days=1) if inclusive else timedelta(days=0))
    current = start
    while current < stop:
        yield current
        current += timedelta(days=1)


def slugify(text: str) -> str:
    """Lowercase alphanumeric slug used for filenames and keys."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def linear_projection(ys: list[float], target: float) -> float | None:
    """Estimate how many future periods are needed to reach `target`,
    fitting a simple least-squares line to `ys`. Returns None when the
    trend is flat or the target is already reached (trending 0)."""
    n = len(ys)
    if n < 2:
        return None
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=False))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0:
        return None
    slope = num / den
    if slope <= 0:
        return None
    remaining = target - ys[-1]
    if remaining <= 0:
        return 0.0
    return remaining / slope
