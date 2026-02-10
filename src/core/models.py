from bisect import insort
from dataclasses import dataclass, field
from typing import ClassVar

from discord.message import Message


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
        "kakeraP": 2,
        "kakeraT": 3,
        "kakeraG": 4,
        "kakeraY": 5,
        "kakeraO": 7,
        "kakeraR": 8,
        "kakeraW": 9,
        "kakeraL": 10,
    }
    claim_cost: int
    color: str
    message: Message
    wished: bool = False

    @property
    def priority(self) -> int:
        return self.KAKERA_PRIORITY.get(self.color, self.KAKERA_PRIORITY["kakera"] - 1)

    def is_wished(self, roll_preferences: "RollPreferences") -> bool:
        return self.color in roll_preferences.wish_kakera


@dataclass
class KakeraStock:
    kakera_max: int
    kakera_value: int
    kakera_cost: int

    dk: Cooldown = field(default_factory=Cooldown)
    claimable_kakera: list[KakeraUnit] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "KakeraStock":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def __isub__(self, cost: int) -> "KakeraStock":
        self.curr_value -= cost
        return self

    def available_claim(self, unit: KakeraUnit, current_time: float) -> str:
        if self.curr_value >= unit.claim_cost:
            return "claim"
        elif self.dk.is_ready(current_time):
            return "dk"
        return ""

    def reset(self) -> None:
        self.curr_value = self.kakera_max

    def regen(self) -> None:
        self.curr_value = min(self.kakera_max, self.curr_value + 1)

    def add(self, unit: KakeraUnit) -> None:
        insort(
            self.claimable_kakera,
            unit,
            key=lambda x: (x.wished, x.priority, -x.claim_cost),
        )


@dataclass(frozen=True)
class Roll:
    name: str
    series: str
    kakera_value: int
    key_amount: int
    message: Message
    wished: bool = False

    def __str__(self) -> str:
        return f"{self.name}\n{self.series}\nKeys: {self.key_amount}\n:${self.kakera_value}"

    def is_wished(self, roll_preferences: "RollPreferences") -> bool:
        return (
            self.name in roll_preferences.wish_list
            or self.series in roll_preferences.wish_series
        )

    def was_claimed(self) -> bool:
        return self.message.embeds[0].to_dict()["color"] == 6753288


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
