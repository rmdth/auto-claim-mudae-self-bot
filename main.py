from tomllib import load
from datetime import timezone, timedelta

from mudaebot.MudaeBot import MudaeBot

settings = load(open("./bot-settings.toml", "rb"))

channels_information = {}
utc_delta: float = settings["UTC_delta"]
TIME_ZONE: timezone = timezone(timedelta(hours=utc_delta))


for information in settings["channels_information"]:
    channels_information[information["id"]] = {
        "id": information["id"],
        "settings": information["settings"],
    }

bot = MudaeBot(
    timezone=TIME_ZONE,
    channels_information=channels_information,
)


bot.run(settings["token"], reconnect=True)
