from typing import Any, NamedTuple

from discord.client import Client

from src.bot.shared.domain import RollMessage
from src.bot.states.domain import RollState
from src.bot.tasks.shared.domain import Preference


class PrefContext(NamedTuple):
    r: RollMessage
    wished: bool
    minute_reset: int
    shifthour: int


class ClaimRollContext(NamedTuple):
    bot: Client
    user_name: str
    discord_channel: Any
    prefix: str
    roll_state: RollState
    roll_message: RollMessage
    minute_reset: int
    shifthour: int
    preferences: tuple[Preference, ...]


class Roll(NamedTuple):
    roll_message: RollMessage
    is_wished: bool
