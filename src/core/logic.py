from datetime import datetime, timedelta


def next_claim(now: datetime, minute_reset: int = 0, shifthour: int = 0) -> float:
    """
    Calculate the time in seconds until the next claim is available. Specific to a 3-hour cycle. Will need another function for premium users.
    """
    if not 0 <= minute_reset <= 59:
        raise ValueError("minute_reset must be between 0 and 59 inclusive")

    shifted_now = now - timedelta(hours=shifthour)

    if (
        shifted_now.hour % 3 == 1
        and shifted_now.minute == minute_reset
        and shifted_now.second == 0
        and shifted_now.microsecond == 0
    ):
        return 0.0

    time = shifted_now.replace(minute=0, second=0, microsecond=0)
    hours_to_add = (1 - time.hour) % 3
    time += timedelta(hours=hours_to_add)
    time = time.replace(minute=minute_reset)

    if time <= shifted_now:
        time += timedelta(hours=3)

    actual_time = time + timedelta(hours=shifthour)
    return (actual_time - now).total_seconds()
