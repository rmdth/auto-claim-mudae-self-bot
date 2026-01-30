from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Cooldown:
    ready_at: float = 0.0

    def is_ready(self, current_time: float) -> bool:
        return current_time >= self.ready_at

    def remaining_seconds(self, current_time: float) -> float:
        return max(0.0, self.ready_at - current_time)

    def set_cooldown(self, seconds: float, current_time: float) -> None:
        self.ready_at = current_time + seconds


@dataclass
class KakeraUnit:
    KAKERA_PRIORITY: ClassVar[dict[str, int]] = {
        "kakera": 9,
        "kakeraT": 8,
        "kakeraG": 7,
        "kakeraY": 6,
        "kakeraO": 5,
        "kakeraR": 4,
        "kakeraW": 3,
        "kakeraL": 2,
        "kakeraP": 1,
    }
    claim_cost: int
    color: str
    channel_id: int
    message_id: int

    @property
    def priority(self) -> int:
        return self.KAKERA_PRIORITY.get(self.color, self.KAKERA_PRIORITY["kakera"] + 1)


@dataclass
class KakeraStock:
    max_value: int
    curr_value: int
    default_cost: int
    dk: Cooldown = field(default_factory=Cooldown)
    seen_units: list[KakeraUnit] = field(default_factory=list)

    def can_afford(self, cost: int) -> bool:
        return self.curr_value >= cost

    def claim(self, cost: int) -> None:
        self.curr_value = max(0, self.curr_value - cost)

    def regen(self) -> None:
        self.curr_value = min(self.max_value, self.curr_value + 1)

    def add_unit(self, unit: KakeraUnit) -> None:
        self.seen_units.append(unit)
        self.seen_units.sort(key=lambda x: x.priority)
