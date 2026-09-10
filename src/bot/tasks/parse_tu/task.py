from asyncio import create_task as asyncio_create_task
from typing import Any

from discord import ClientUser
from discord.client import Client

from src.bot.shared.domain import MUDAE_ID, ParsedTimeUpdate
from src.bot.tasks.parse_tu.logic import get_tu_information, is_my_tu_message
from src.shared.retry import retry


@retry()
async def fetch_tu_data(
    bot: Client, discord_channel: Any, prefix: str
) -> ParsedTimeUpdate:

    waiting_task = asyncio_create_task(
        bot.wait_for(
            "message",
            check=lambda message: (
                message.author.id == MUDAE_ID
                and message.channel.id == discord_channel.id
                and isinstance(bot.user, ClientUser)
                and is_my_tu_message(bot.user.name, message.content)
            ),
            timeout=1.5,
        )
    )
    await discord_channel.send(f"{prefix}tu")
    await waiting_task
    return get_tu_information(waiting_task.result().content)
