from asyncio import TimeoutError, sleep

from discord.errors import InvalidData, NotFound
from discord.ext import tasks

from mudaebot.channel.kakera.KakeraColors import KakeraColors
from mudaebot.channel.rolls.Rolls import Rolls

from ...constants import MUDAE_ID
from ...patterns import KAKERA_DK_CONFIRMATION_PATTERN
from ..cooldown.Cooldown import DAY_IN_SECONDS, Cooldown


class Kakera:
    @staticmethod
    def get_cost(user, message, cost) -> int:
        """
        Returns the cost of claiming the kakera.

        Args:
            user (discord.User): You.
            message (discord.Message): The message of the kakera.
            cost (int): The default cost of claiming kakera.

        Returns:
            int: The cost of claiming that kakera.
        """

        if KakeraColors.get_priority(message.components[0].children[0].emoji.name) == 1:
            cost = 0
        elif (
            Rolls.get_roll_kakera_keys(message) > 9
            and user.name in message.embeds[0].to_dict()["footer"]["text"]
        ):
            cost = cost // 2

        return cost

    def __init__(
        self,
        value: int,
        cost: int,
        total: int,
        dk: Cooldown,
        wish_kakera: list[str],
    ) -> None:
        self._value: int = value
        self._cost: int = cost
        self._total: int = total
        self._dk: Cooldown = dk
        self._wish_kakera: list[str] = wish_kakera or ["kakera"]
        self._kakera_being_watched: list = []

    @property
    def value(self) -> int:
        return self._value

    @property
    def cost(self) -> int:
        return self._cost

    @property
    def total(self) -> int:
        return self._total

    @property
    def dk(self) -> Cooldown:
        return self._dk

    @property
    def wish_kakera(self) -> list[str]:
        return self._wish_kakera

    @property
    def kakera_being_watched(self) -> list:
        return self._kakera_being_watched

    def __iadd__(self, n: int) -> "Kakera":
        if (self._value + n) <= self._total:
            self._value += n
        else:
            self._value = self._total

        return self

    def __isub__(self, n: int) -> "Kakera":
        if (self._value - n) > -1:
            self._value -= n
        else:
            self._value = 0

        return self

    @tasks.loop(minutes=3)
    async def auto_regen(self) -> None:
        self += 1

    @tasks.loop(count=1)
    async def claim_dk(
        self,
        bot,
        channel,
        prefix: str = "$",
        cooldown: float = DAY_IN_SECONDS,
    ) -> None:
        """
        Claims the dk.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            channel (discord.TextChannel): The channel to claim the dk.
            prefix (str): The prefix to use on the server.
            cooldown (float): The amount of seconds to for the next dk.

        Returns:
            None
        """
        print(f"Claiming dk on {channel.guild.name}...")
        while True:
            try:
                await channel.send(f"{prefix}dk")
            except NotFound:
                continue
            try:
                await bot.wait_for(
                    "message",
                    check=lambda message: (
                        message.channel.id == channel.id
                        and message.author.id == MUDAE_ID
                        and KAKERA_DK_CONFIRMATION_PATTERN.match(message.content)
                    )
                    or (
                        message.channel.id == channel.id
                        and message.author.id == MUDAE_ID
                        and "$dk" in message.content
                    ),
                    timeout=3.0,
                )
            except TimeoutError:
                continue
            break

        self.dk.set_cooldown.start(cooldown)
        self._value = self.total
        print(f"... Claimed dk on {channel.guild.name}.\n")

    @tasks.loop(count=1)
    async def check_kakera(
        self, bot, user, message, prefix, delay_kakera_kakera: int = 0
    ) -> None:
        """
        Waits given delay and prepares the kakera to be claimed.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            user (discord.User): You.
            message (discord.Message): The kakera message.
            prefix (str): The prefix to use on the server.
            delay_kakera_kakera (int): The delay before claiming the kakera.

        Returns:
            None
        """

        channel = message.channel
        print(
            f"Waiting {delay_kakera_kakera} to claim kakera on {channel.guild.name}. \n"
        )
        await sleep(delay_kakera_kakera)

        await self.prepare_kakera(bot, user, message, prefix)

    def append(self, bot, user, message, prefix, delay_kakera: int = 0):
        """
        Adds a kakera to the kakera_being_watched list.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            user (discord.User): You.
            message (discord.Message): The kakera message.
            prefix (str): The prefix to use on the server.
            delay_kakera (int): The delay before claiming the kakera.

        Returns:
            None
        """

        self.kakera_being_watched.append(message)
        print(
            f"Added {message.components[0].children[0].emoji.name} on {message.channel.guild.name}."
        )

        try:
            self.check_kakera.start(bot, user, message, prefix, delay_kakera)
        except RuntimeError:
            pass

    async def prepare_kakera(self, bot, user, message, prefix):
        """
        Sorts the kakera_being_watched list by highest value and calls claim.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            user (discord.User): You.
            message (discord.Message): The kakera message.
            prefix (str): The prefix to use on the server.

        Returns:
            None
        """
        KakeraColors.sort_by_highest_value(self.kakera_being_watched)

        await self.claim(bot, user, message.channel, prefix)
        self.clean_kakeras(message.channel)

    def can_claim(self, bot, channel, cost, prefix) -> bool:
        """
        Checks if you can claim kakera in the given channel.
        If you don't uses dk.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            channel (discord.TextChannel): The channel being checked.
            cost (int): The cost of claiming the kakera.
            prefix (str): The prefix to use on the server.

        Returns:
            bool: Whether you can claim the kakera or not.
        """
        print(f"Cheking if you can claim kakera on {channel.guild.name}...")
        if self.value >= cost:
            print(f"... You can claim kakera on {channel.guild.name}.\n")
            return True

        if self.dk:
            print(f"... You can kakera with dk on {channel.guild.name}...\n")
            try:
                self.claim_dk.start(bot, channel, prefix)
            except RuntimeError:
                print(
                    f"... Error? dk is already on cooldown on {channel.guild.name}.\n"
                )
                return False
            return True

        print(
            f"... You don't have enough kakera ({self.value}) on {channel.guild.name}.\n"
        )
        return False

    async def claim(self, bot, user, channel, prefix):
        """
        Claims kakera from the given message.

        Args:
            bot (discord.ext.commands.Bot): The bot client.
            user (discord.User): You.
            channel (discord.TextChannel): The channel where the kakera is.
            prefix (str): The prefix to use on the server.

        Returns:
            None
        """
        if not self._kakera_being_watched:
            print(f"There is no more kakera on {channel.guild.name}.\n")
            return

        message = self.kakera_being_watched.pop(0)

        cost = Kakera.get_cost(user, message, self.cost)

        if not self.can_claim(bot, channel, cost, prefix):
            return

        # I don't know what causes this, that's why im not putting While True
        try:
            await message.components[0].children[0].click()
        except InvalidData:
            print(f"Could not claim Kakera {channel.guild.name}.\n")
            return

        print(f"Claimed Kakera on {channel.guild.name}.\n")
        self -= cost

        await self.claim(bot, user, channel, prefix)

    def clean_kakeras(self, channel) -> None:
        """
        Clears the kakera_being_watched list.

        Args:
            channel (discord.TextChannel): The channel that is being cleaned.

        Returns:
            None
        """
        self.kakera_being_watched.clear()
        print(f"Cleaned Kakeras on {channel.guild.name}.\n")
