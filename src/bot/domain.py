from typing import Any, NamedTuple

from src.bot.shared.domain import ChannelMudaeSettings
from src.bot.states import ChannelStates


class Channel(NamedTuple):
    discord_channel: Any
    states: ChannelStates
    mudae_settings: ChannelMudaeSettings
