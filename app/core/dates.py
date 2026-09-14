from datetime import UTC, date, datetime


def today_utc() -> date:
    return datetime.now(UTC).date()
