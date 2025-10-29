from asyncio import TimeoutError
from re import compile as re_compile

from discord.errors import NotFound

from ..constants import MUDAE_ID
from .kakera.Kakera import Kakera
from .rolls.Rolls import Rolls


class Channel:
    find_tu_pattern = re_compile(r"\*\*=>\*\* \$tuarrange")

    # Find means available
    current_claim_in_tu_pattern = re_compile(r"__(.+)__.+\.")

    # Always finds. Only use after checking curr_claim
    current_claim_time_pattern = re_compile(r",\D+(\d+)?\D+(\d+)\D+\.")

    # None means available IF len 2 (hours and minutes), len 1 (minutes)
    daily_in_tu_pattern = re_compile(r"\$daily\D+(\d\d+)?\D+(\d+)")
    rt_in_tu_pattern = re_compile(r"\$rt\D+(\d|)?\D+(\d+)")
    dk_in_tu_pattern = re_compile(r"\$dk\D+(\d+)?\D+(\d+)")

    # [0] = Kakera Value, [1] = Kakera Cost. None means something changed.
    kakera_in_tu_pattern = re_compile(r"(\d+)%")

    # [0] = Current available_regular_claims rolls_for_guilds.
    # [1] Could be used to start rolling... Not for now.
    current_rolls_in_tu_pattern = re_compile(r"\*\*(\d+)\*\* roll")

    @staticmethod
    async def found_tu(bot, channel):
        try:
            await bot.wait_for(
                "message",
                check=lambda message: message.channel == channel
                and message.author.id == MUDAE_ID,
                timeout=0.5,
            )
        except TimeoutError:
            return None

        try:
            last_message = await channel.fetch_message(channel.last_message_id)
        except NotFound:
            return None

        if Channel.find_tu_pattern.search(last_message.content):
            return last_message

        return None

    @staticmethod
    async def get_tu(bot, channel, prefix: str):
        tu = None
        while not (tu := await Channel.found_tu(bot, channel)):
            while True:
                try:
                    await channel.send(f"{prefix}tu")
                except NotFound:
                    continue
                break

        return tu

    @staticmethod
    async def get_current_claim(message) -> list[str]:
        """
        Something means available else []
        """
        return Channel.current_claim_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_current_claim_time(message) -> list[str]:
        """
        Always returns the time. Only use after checking curr_claim_status
        """
        return Channel.current_claim_time_pattern.findall(message.content)

    @staticmethod
    async def get_daily(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)

        """
        return Channel.daily_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_rt(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)
        """
        return Channel.rt_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_dk(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)
        """
        return Channel.dk_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_kakera(message) -> list[str]:
        """
        [0] = Kakera Value, [1] = Kakera Cost. None means BIGGG EROOR!!!
        """
        return Channel.kakera_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_rolls(message) -> list[str]:
        """
        [0] = Current available_regular_claims rolls_for_guilds.
        [1] Could be used to start rolling... But not for now.
        """
        return Channel.current_rolls_in_tu_pattern.findall(message.content)

    @staticmethod
    async def get_msg_time(tempo: list[tuple[str, str]]) -> int:
        if not tempo[0]:
            return 0

        tempo: tuple[str, str] = tempo[0]
        if not tempo[0] == "":
            return int(tempo[0]) * 3600 + int(tempo[1]) * 60

        return int(tempo[1]) * 60

    @staticmethod
    def get_roll_type(message, information, wish_kakera: list[str]) -> str:
        if "image" not in information or "author" not in information:
            return ""

        if "footer" in information and "text" in information["footer"]:
            if "/" in information["footer"]["text"]:
                return ""
            elif message.components != [] and any(
                kakera in message.components[0].children[0].emoji.name
                for kakera in wish_kakera
            ):
                return "kakera"

        return "roll"

    def __init__(
        self,
        kakera,
        rolls,
        timezone,
        prefix,
        command: str = "mx",
        uptime: int = 44,
        delay: int = 0,
        shifthour: int = 0,
        minute_reset: int = 30,
    ) -> None:
        self._kakera: Kakera = kakera
        self._rolls: Rolls = rolls
        self._prefix: str = prefix
        self._command: str = command
        self._uptime: int = uptime
        self._delay: int = delay
        self._shifthour: int = shifthour
        self._minute_reset: int = minute_reset

    @property
    def kakera(self) -> Kakera:
        return self._kakera

    @property
    def rolls(self) -> Rolls:
        return self._rolls

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def command(self) -> str:
        return self._command

    @property
    def uptime(self) -> int:
        return self._uptime

    @property
    def delay(self) -> int:
        return self._delay

    @property
    def shifthour(self) -> int:
        return self._shifthour

    @property
    def minute_reset(self) -> int:
        return self._minute_reset

    async def should_i_claim(self, user_id: int, message) -> None:
        if not message.embeds:
            return

        embed = message.embeds[0].to_dict()
        roll_type = Channel.get_roll_type(message, embed, self._kakera.wish_kakera)
        if not roll_type:
            return

        if roll_type == "kakera":
            await self.kakera_claim(message)

        char_name = embed["author"]["name"]
        description = embed["description"]

        if (
            str(user_id) in message.content
            or char_name in self._rolls.wish_list
            or description in self._rolls.wish_series
        ):
            print(
                f"Added {char_name} of {description} found in {message.guild}: {message.channel.name} to wished_claims.\n"
            )

            await self.roll_claim(
                self._rolls.rolling.wished_rolls_being_watched, message
            )

        print(
            self._rolls.rolling.claim.is_cooldown_less_than(),
            await Rolls.is_minimum_kakera(message, self._rolls.min_kakera_value),
        )
        if (
            self._rolls.rolling.claim.is_cooldown_less_than()
            or await Rolls.is_minimum_kakera(message, self._rolls.min_kakera_value)
        ):
            print(
                f"Added {char_name} of {description} found in {message.guild}: {message.channel.name} to regular_claims.\n"
            )
            await self.roll_claim(
                self._rolls.rolling.regular_rolls_being_watched, message
            )

    async def kakera_claim(self, message) -> None:
        # half = (Kakera.get_keys(message) > 9
        #     and "You are the owner")
        await self._kakera.claim(message, self._prefix, delay=self._delay)

    async def roll_claim(self, rolls, message) -> None:
        await self._rolls.rolling.add_roll(
            rolls,
            message=message,
            prefix=self._prefix,
            minute_reset=self._minute_reset,
            shifthour=self._shifthour,
            uptime=self._uptime,
            timezone=self._timezone,
        )
