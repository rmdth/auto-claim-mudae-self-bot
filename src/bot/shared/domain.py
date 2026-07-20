from enum import StrEnum, auto
from typing import NamedTuple, TypedDict

from discord.message import Message

MUDAE_ID: int = 432610292342587392
MAX_MUDAE_COOLDOWN: int = 72000


class ChannelInformation(TypedDict):
    id: int
    max_rolls: int
    prefix: str
    command: str
    shifthour: int
    minute_reset: int
    delay_claim_roll: int
    delay_claim_kakera: int
    rt_max_cd: int
    dk_max_cd: int
    max_kakera_power: int
    # min_roll_claim_kakera_threshold: int
    wished_rolls: frozenset[str]
    wished_series: frozenset[str]
    wished_kakera: frozenset[str]


class ChannelMudaeSettings(NamedTuple):
    prefix: str
    command: str
    shifthour: int
    minute_reset: int


class MessageType(StrEnum):
    ROLL = auto()
    KAKERA = auto()


class RollMessage(NamedTuple):
    message: Message
    character: str
    series: str
    kakera_value: int
    key_amount: int

    def print(self) -> str:
        return f"[{self.kakera_value}♦️] {self.character} - {self.series}"


class KakeraMessage(NamedTuple):
    message: Message
    color: str
    key_amount: int
    is_owned_char: bool

    def print(self) -> str:
        return f"[{self.key_amount}🗝️] {self.color}"


MudaeMessage = RollMessage | KakeraMessage


class ParsedTimeUpdate(NamedTuple):
    claim_in: float
    daily_in: float
    rt_in: float
    dk_in: float
    curr_kakera_power: int
    kakera_claim_cost: int
    rolls_available: int


class MudaeInfo(NamedTuple):
    parsed_tu: ParsedTimeUpdate
    max_rolls: int
    delay_claim_roll: float
    max_kakera_power: int
    delay_claim_kakera: float
    rt_max_cd: float
    dk_max_cd: float
    wished_rolls: frozenset[str]
    wished_series: frozenset[str]
    wished_kakera: frozenset[str]


class ClaimMethod(StrEnum):
    CLAIM = auto()
    RESET = auto()
