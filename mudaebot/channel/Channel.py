from asyncio import TimeoutError

from discord.errors import NotFound

from .cooldown.Cooldown import Cooldown
from .kakera.Kakera import Kakera
from .kakera.KakeraColors import KakeraColors
from .rolls.Rolls import Rolls

from ..constants import MUDAE_ID
from ..patterns import (
    CURRENT_CLAIM_IN_TU_PATTERN,
    CURRENT_CLAIM_TIME_PATTERN,
    CURRENT_ROLLS_IN_TU_PATTERN,
    DAILY_IN_TU_PATTERN,
    DK_IN_TU_PATTERN,
    FIND_TU_PATTERN,
    KAKERA_IN_TU_PATTERN,
    RT_IN_TU_PATTERN,
)


class Channel:
    find_tu_pattern = FIND_TU_PATTERN

    # Find means available
    current_claim_in_tu_pattern = CURRENT_CLAIM_IN_TU_PATTERN

    # Always finds. Only use after checking curr_claim
    current_claim_time_pattern = CURRENT_CLAIM_TIME_PATTERN

    # None means available IF len 2 (hours and minutes), len 1 (minutes)
    daily_in_tu_pattern = DAILY_IN_TU_PATTERN
    rt_in_tu_pattern = RT_IN_TU_PATTERN
    dk_in_tu_pattern = DK_IN_TU_PATTERN

    # [0] = Kakera Value, [1] = Kakera Cost. None means something changed.
    kakera_in_tu_pattern = KAKERA_IN_TU_PATTERN

    # [0] = Current available_regular_claims rolls_for_guilds.
    # [1] Could be used to start rolling... Not for now.
    current_rolls_in_tu_pattern = CURRENT_ROLLS_IN_TU_PATTERN

    @staticmethod
    async def found_tu(bot, channel):
        try:
            last_message = await bot.wait_for(
                "message",
                check=lambda message: message.channel == channel
                and message.author.id == MUDAE_ID,
                timeout=1,
            )
        except TimeoutError:
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
    def get_current_claim(message) -> list[str]:
        """
        Something means available else []
        """
        return Channel.current_claim_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_current_claim_time(message) -> list[tuple[str, str]]:
        """
        Always returns the time. Only use after checking curr_claim_status
        """
        return Channel.current_claim_time_pattern.findall(message.content)

    @staticmethod
    def get_daily(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)

        """
        return Channel.daily_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_rt(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)
        """
        return Channel.rt_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_dk(message) -> list[str]:
        """
        [] means available IF len 2 (hours and minutes), len 1 (minutes)
        """
        return Channel.dk_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_kakera(message) -> list[str]:
        """
        [0] = Kakera Value, [1] = Kakera Cost. None means BIGGG EROOR!!!
        """
        return Channel.kakera_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_rolls(message) -> list[str]:
        """
        [0] = Current available_regular_claims rolls_for_guilds.
        [1] Could be used to start rolling... But not for now.
        """
        return Channel.current_rolls_in_tu_pattern.findall(message.content)

    @staticmethod
    def get_msg_time(tempo: list[tuple[str, str]]) -> int:
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
                return str(message.components[0].children[0].emoji.name)

        return "roll"

    def __init__(
        self,
        kakera,
        rolls,
        timezone,
        prefix,
        command: str = "mx",
        delay_rolls: int = 44,
        delay_kakera: int = 0,
        shifthour: int = 0,
        minute_reset: int = 30,
        last_claim_threshold_in_seconds: int = 3600,
    ) -> None:
        self._kakera: Kakera = kakera
        self._rolls: Rolls = rolls
        self._prefix: str = prefix
        self._timezone = timezone
        self._command: str = command
        self._delay_rolls: int = delay_rolls
        self._delay_kakera: int = delay_kakera
        self._shifthour: int = shifthour
        self._minute_reset: int = minute_reset
        self._last_claim_threshold_in_seconds: int = last_claim_threshold_in_seconds

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
    def delay_rolls(self) -> int:
        return self._delay_rolls

    @property
    def delay(self) -> int:
        return self._delay_kakera

    @property
    def shifthour(self) -> int:
        return self._shifthour

    @property
    def minute_reset(self) -> int:
        return self._minute_reset

    async def should_i_claim(self, bot, user, message) -> None:
        if not message.embeds:
            return

        embed = message.embeds[0].to_dict()
        roll_type = Channel.get_roll_type(message, embed, self._kakera.wish_kakera)
        if not roll_type:
            return

        if "kakera" in roll_type:
            self.add_kakera(bot, user, message)
            return

        char_name = Rolls.get_roll_name(message)
        char_series = Rolls.get_roll_series(message)

        if (
            str(user.id) in message.content
            or char_name in self._rolls.wish_list
            or char_series in self._rolls.wish_series
        ):
            print(
                f"Added {char_name} of {char_series} found in {message.guild}: {message.channel.name} to wished_claims.\n"
            )

            self._rolls.rolling.add_roll(
                bot=bot,
                rolls=self._rolls.rolling.wished_rolls_being_watched,
                message=message,
                prefix=self._prefix,
                minute_reset=self._minute_reset,
                shifthour=self._shifthour,
                timezone=self._timezone,
                delay_rolls=self._delay_rolls,
            )
            return

        if Cooldown.next_claim(
            self._timezone, self._minute_reset, self._shifthour
        ) < self._last_claim_threshold_in_seconds or Rolls.is_minimum_kakera(
            message, self._rolls.min_kakera_value
        ):
            print(
                f"Added {char_name} of {char_series} found in {message.guild}: {message.channel.name} to regular_claims.\n"
            )
            self._rolls.rolling.add_roll(
                bot=bot,
                rolls=self._rolls.rolling.regular_rolls_being_watched,
                message=message,
                prefix=self._prefix,
                minute_reset=self._minute_reset,
                shifthour=self._shifthour,
                timezone=self._timezone,
                delay_rolls=self._delay_rolls,
            )

    def add_kakera(self, bot, user, message) -> None:
        self._kakera.append(
            bot,
            user,
            message,
            self._prefix,
            delay_kakera=self._delay_kakera,
        )
