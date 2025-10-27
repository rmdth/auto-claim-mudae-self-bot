from re import compile as re_compile

from discord.errors import NotFound
from .Kakera import Kakera
from .Rolls import Rolls


class Channel:
    find_tu_pattern = re_compile(r"\*\*=>\*\* \$tuarrange")

    def __init__(
        self,
        kakera,
        rolls,
        prefix,
        wish_list,
        wish_series,
        wish_kakera=["kakera"],
        command: str = "mx",
        uptime: int = 44,
        delay: int = 0,
        shifthour: int = 0,
        minute_reset: int = 30,
    ):
        self._kakera: Kakera = kakera
        self._rolls: Rolls = rolls
        self._prefix: str = prefix
        self._command: str = command
        self._uptime: int = uptime
        self._delay: int = delay
        self._shifthour: int = shifthour
        self._minute_reset: int = minute_reset
        self._wish_kakera: list[str] = wish_kakera
        self._wish_list: list[str] = wish_list
        self._wish_series: list[str] = wish_series

    @staticmethod
    async def found_tu(channel):
        last_message = await channel.fetch_message(channel.last_message_id)
        if Channel.find_tu_pattern.search(last_message.content):
            return last_message
        return None

    async def get_tu(self, channel):
        while not (await self.found_tu(channel)):
            while True:
                try:
                    await channel.send(f"{self._prefix}tu")
                except NotFound:
                    continue
                break

    def get_roll_type(self, message, information) -> str:
        if "image" not in information or "author" not in information:
            return ""

        if "footer" in information and "text" in information["footer"]:
            if "/" in information["footer"]["text"]:
                return ""
            elif (
                message.components != []
                and self._wish_kakera in message.components[0].children[0].emoji.name
            ):
                return "kakera"

        return "roll"

    async def kakera_claim(self, message) -> None:
        # half = (Kakera.get_keys(message) > 9
        #     and "You are the owner")
        await self._kakera.claim(message, delay=self._delay)

    async def roll_claim(self, rolls, message) -> None:
        await self._rolls.rolling.add_roll(rolls, message=message, prefix=self._prefix)
