from datetime import date, datetime, timedelta


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def workdays_between(start: date, end: date) -> int:
    """Number of weekdays (Mon-Fri) strictly between start and end (inclusive of end, exclusive of start)."""
    if end < start:
        return 0
    days = (end - start).days
    count = 0
    for i in range(1, days + 1):
        d = start + timedelta(days=i)
        if d.weekday() < 5:
            count += 1
    return count


def workdays_since(s: str | None, ref: date | None = None) -> int | None:
    ref = ref or date.today()
    d = parse_date(s)
    if not d:
        return None
    return workdays_between(d, ref)
