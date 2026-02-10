from datetime import timedelta, timezone

from tomllib import load

from src.logging import setup_logging
from src.mudae_bot import MudaeBot

setup_logging()
settings = load(open("./bot-settings.toml", "rb"))

channels_information = settings["channels_information"]
utc_delta: float = settings["UTC_delta"]
TIME_ZONE: timezone = timezone(timedelta(hours=utc_delta))

bot = MudaeBot(
    timezone=TIME_ZONE,
    channels_information=channels_information,
)


bot.run(settings["token"], reconnect=True)
