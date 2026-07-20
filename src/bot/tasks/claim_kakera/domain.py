from typing import Any, NamedTuple

from discord.client import Client

from src.bot.shared.domain import KakeraMessage
from src.bot.states import KakeraState
from src.bot.tasks.shared.domain import Preference


class ClaimKakeraContext(NamedTuple):
    bot: Client
    discord_channel: Any
    prefix: str
    kakera_state: KakeraState
    kakera_message: KakeraMessage
    preferences: tuple[Preference, ...]


class PrefContext(NamedTuple):
    kakera_message: KakeraMessage

    wished: bool


class Kakera(NamedTuple):
    kakera_message: KakeraMessage
    claim_cost: int
    is_wished: bool
    priority: int
