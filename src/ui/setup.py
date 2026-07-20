from collections import deque
from tomllib import load
from typing import MutableSequence

from attr import dataclass


@dataclass(slots=True)
class ChannelUIInfo:
    statuses: dict[str, str]
    roll_queue: MutableSequence[str]


page = 0
max_pages: int

page_id_map: dict[int, int] = {}

bot_status: dict[str, str] = {}
channel_page_uis: dict[int, ChannelUIInfo] = {}

with open("./bot-settings.toml", "rb") as f:
    settings = load(f)
    MUDAE_LOG_LENGTH = settings.get("mudae_log_length", 15)


def setup_ui(channel_ids: tuple[int, ...]) -> None:
    global channel_page_uis, max_pages, page_id_map
    for i, channel_id in enumerate(channel_ids):
        page_id_map[i] = channel_id
        channel_page_uis[channel_id] = ChannelUIInfo({}, deque(maxlen=MUDAE_LOG_LENGTH))

    max_pages = len(page_id_map)
