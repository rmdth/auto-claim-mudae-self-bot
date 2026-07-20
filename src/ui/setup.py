from collections import deque
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


def setup_ui(channel_ids: tuple[int, ...]) -> None:
    global channel_page_uis, max_pages, page_id_map
    for i, channel_id in enumerate(channel_ids):
        page_id_map[i] = channel_id
        channel_page_uis[channel_id] = ChannelUIInfo({}, deque(maxlen=15))

    max_pages = len(page_id_map)
