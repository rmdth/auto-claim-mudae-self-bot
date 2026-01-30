from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Cooldown:
    ready_at: float = 0.0

    def is_ready(self, current_time: float) -> bool:
        return current_time >= self.ready_at

    def remaining_seconds(self, current_time: float) -> float:
        return max(0.0, self.ready_at - current_time)

    def set_cooldown(self, seconds: float, current_time: float) -> None:
        self.ready_at = current_time + seconds

    @staticmethod
    def next_claim(now: datetime, minute_reset: int = 0, shifthour: int = 0) -> float:
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


@dataclass
class Kakera:
    pass
