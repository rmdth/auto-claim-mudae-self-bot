from typing import NamedTuple

from discord.client import Client

from src.bot.domain import Channel
from src.bot.states import DailyState


class DailyContext(NamedTuple):
    bot: Client
    channels: dict[int, Channel]
    daily_state: DailyState
