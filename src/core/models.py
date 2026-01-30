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


        shifted_now = now - timedelta(hours=shifthour)





    def regen(self) -> None:
        self.curr_value = min(self.max_value, self.curr_value + 1)

