from bisect import insort
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


@dataclass(frozen=True)
class KakeraUnit:
    KAKERA_PRIORITY: ClassVar[dict[str, int]] = {
        "kakera": 1,
        "kakeraT": 2,
        "kakeraG": 3,
        "kakeraY": 4,
        "kakeraO": 5,
        "kakeraR": 6,
        "kakeraW": 7,
        "kakeraL": 8,
        "kakeraP": 9,
    }
    claim_cost: int
    color: str
    channel_id: int
    message_id: int

    @property
    def priority(self) -> int:
        return self.KAKERA_PRIORITY.get(self.color, self.KAKERA_PRIORITY["kakera"] - 1)


@dataclass
class KakeraStock:
    max_value: int
    curr_value: int
    default_cost: int

    dk: Cooldown = field(default_factory=Cooldown)
    seen_units: list[KakeraUnit] = field(default_factory=list)

    def __isub__(self, cost: int) -> "KakeraStock":
        self.curr_value -= cost
        return self

    def can_afford(self, cost: int) -> bool:
        return self.curr_value >= cost

    def regen(self) -> None:
        self.curr_value = min(self.max_value, self.curr_value + 1)

    def add_unit(self, unit: KakeraUnit) -> None:
        insort(self.seen_units, unit, key=lambda x: (x.priority, -x.claim_cost))

    def get_best_one(self) -> KakeraUnit | None:
        return self.seen_units.pop() if self.seen_units else None


@dataclass(frozen=True)
class Roll:
    name: str
    series: str
    kakera_value: int
    channel_id: int
    message_id: int

    def __str__(self) -> str:
        return (
            f"{self.name}\n{self.series}\nKeys: {self.key_amount}\n${self.kakera_value}"
        )


@dataclass
class Rolling:
    rolls: int
    max_rolls: int
    wish_rolls: list[Roll] = field(default_factory=list)
    regular_rolls: list[Roll] = field(default_factory=list)
    claim: Cooldown = field(default_factory=Cooldown)
    rt: Cooldown = field(default_factory=Cooldown)

    def __isub__(self, amount: int) -> "Rolling":
        self.rolls = max(0, self.rolls - amount)
        return self

    def reset(self) -> None:
        self.rolls = self.max_rolls


@dataclass(frozen=True)
class RollPreferences:
    wish_chars: list[str]
    wish_series: list[str]

    min_kakera_value: int

    def is_wished(self, roll: Roll) -> bool:
        return roll.name in self.wish_chars or roll.series in self.wish_series

    def meets_min_kakera(self, roll: Roll) -> bool:
        return roll.kakera_value >= self.min_kakera_value


@dataclass(frozen=True)
class ChannelSettings:
    prefix: str
    command: str
    shifthour: int
    minute_reset: int
    delay_rolls: float
    delay_kakera: float
    last_claim_threshold_in_seconds: float
