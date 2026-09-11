from datetime import date, datetime, timezone

def today_utc() -> date:
    return datetime.now(timezone.utc).date()