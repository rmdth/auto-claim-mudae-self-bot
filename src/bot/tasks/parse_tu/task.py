from typing import Any

from src.bot.bot import MUDAE_ID
from src.bot.shared.domain import ParsedTimeUpdate
from src.bot.tasks.parse_tu.logic import get_tu_information, is_tu_message
from src.shared.retry import retry


@retry()
async def fetch_tu_data(
    bot: Any, discord_channel: Any, prefix: str
) -> ParsedTimeUpdate:

    await discord_channel.send(f"{prefix}tu")
    tu_message = await bot.wait_for(
        "message",
        check=lambda message: (
            message.author.id == MUDAE_ID
            and message.channel.id == discord_channel.id
            and is_tu_message(message.content)
        ),
        timeout=1.5,
    )
    return get_tu_information(tu_message.content)
