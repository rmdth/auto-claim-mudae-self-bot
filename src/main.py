import asyncio
from tomllib import load

from src.bot import MudaeBot, prepare_tasks
from src.ui import listen_keys, live, setup_logging, setup_ui, update_log_debug


async def main():
    with open("./bot-settings.toml", "rb") as f:
        settings = load(f)
        token = settings.get("user_token", "0")
        channels_information = settings.get("channels_information", ())
        tasks = prepare_tasks(tuple(settings.get("tasks", ())))
        update_log_debug(f"{tasks}")
        setup_logging()
        setup_ui(tuple(channel["id"] for channel in channels_information))

    mudae_bot = MudaeBot(tasks=tasks, channels_information=tuple(channels_information))

    with live:
        asyncio.create_task(listen_keys(mudae_bot))
        await mudae_bot.start(token, reconnect=True)
