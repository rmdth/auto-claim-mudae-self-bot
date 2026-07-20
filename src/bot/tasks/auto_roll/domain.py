from typing import NamedTuple, Protocol

from src.bot.domain import Channel


class BotWithChannels(Protocol):
    channels: dict[int, Channel]


class AutoRollContext(NamedTuple):
    channels: dict[int, Channel]
