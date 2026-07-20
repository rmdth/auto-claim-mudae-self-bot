from asyncio import Lock
from dataclasses import dataclass, field
from enum import StrEnum, auto
from time import time
from typing import TypedDict

from src.ui import update_log_debug


def _time_remaining(num: float) -> str:
    update_log_debug(f"num={num}")
    rem = num - time()
    if rem <= 0:
        return "READY"

    hours, rest = divmod(rem, 3600)
    minutes, _ = divmod(rest, 60)

    strs = []
    if hours:
        strs.append(f"{int(hours)}h")
    if minutes:
        strs.append(f"{int(minutes)} min")
    return " ".join(strs)


@dataclass(slots=True)
class RollState:
    curr_rolls: int
    max_rolls: int
    delay_claim_roll: float
    claim_in: float
    reset_in: float
    reset_max_cd: float
    wished_rolls: frozenset[str]
    wished_series: frozenset[str]
    watched_rolls: list = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)

    def print(self) -> str:
        return f"""ROLLS
current amount: {self.curr_rolls}
claim in: {_time_remaining(self.claim_in)}
reset in: {_time_remaining(self.reset_in)}
"""


@dataclass(slots=True)
class KakeraState:
    power: int
    max: int
    delay_claim_kakera: float
    claim_cost: int
    reset_in: float
    reset_max_cd: float
    wished_kakera: frozenset[str]
    watched_kakera: list = field(default_factory=list)
    lock: Lock = Lock()

    # @property
    # def claim_in(self) -> float:
    #     return float("inf") if self.power >= self.claim_cost else float("-inf")
    def print(self) -> str:
        return f"""KAKERA
power: {self.power}
reset in: {_time_remaining(self.reset_in)}
"""


@dataclass(slots=True)
class DailyState:
    claim_in: float

    def print(self) -> str:
        update_log_debug(f"daily state claim_in={self.claim_in}")
        return f"""DAILY
claim in: {_time_remaining(self.claim_in)}"""


class ChannelState(StrEnum):
    ROLL = auto()
    KAKERA = auto()


class ChannelStates(TypedDict):
    roll: RollState
    kakera: KakeraState


class BotState(StrEnum):
    DAILY = auto()


class BotStates(TypedDict):
    daily: DailyState


StateType = ChannelState | BotState
State = RollState | KakeraState | DailyState
