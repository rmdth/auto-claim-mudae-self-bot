from asyncio import TimeoutError, sleep

from discord.errors import NotFound, InvalidData
from discord.ext import tasks

from ...constants import MUDAE_ID
from ..cooldown.Cooldown import DAY_IN_SECONDS, Cooldown
from ...patterns import KAKERA_DK_CONFIRMATION_PATTERN


class Kakera:

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
    def wish_kakera(self) -> list[str]:
        return self._wish_kakera

    def __iadd__(self, n: int) -> None:
        if (self._value + n) <= self._total:
            self._value += n
        else:
            self._value = self._total

    def __isub__(self, n: int) -> None:
        if (self._value - n) > -1:
            self._value -= n
        else:
            self._value = 0

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
                    timeout=1,
                )
            except TimeoutError:
                continue
            break

        self._value = self._total
        print(f"Claimed dk on {channel.guild.name}.\n")
        self._dk.set_cooldown.start(cooldown)

    async def can_claim(self, bot, channel, cost, prefix) -> bool:
        """
        Checks if you can claim kakera in the given channel.
        If you don't uses dk.
        :param channel: The Discord channel to check.
        :param key: Whether the user has 10 keys to reduce the cost.
        """
        print(f"Cheking if you can claim kakera on {channel.guild.name}...")
        if self._value >= cost:
            print(f"... You can claim kakera on {channel.guild.name}.\n")
            return True

        if self._dk:
            print(f"... You can claim kakera on {channel.guild.name}.\n")
            await self.claim_dk(bot, channel, prefix)
            return True

        print(
            f"... You don't have enough kakera ({self._value}) on {channel.guild.name}.\n"
        )
        return False

    async def claim(
        self, bot, message, prefix, to_reduce: int = 0, delay: float = 0
    ) -> None:
        """
        Claims kakera from the given message.
        :param message: The Discord message to claim kakera from.
        :param prefix: The prefix to use for the claim command.
        :param half: Whether to claim half of the kakera.
        :param delay: The delay in seconds before claiming kakera.
        """
        channel = message.channel

        await sleep(delay)
        print(f"Waiting {delay} to claim kakera on {channel.guild.name}.\n")

        cost = self._cost - to_reduce

        if not await self.can_claim(bot, channel, cost, prefix):
            print(f"Can't claim kakera on {channel.guild.name} :(")
            return

        # I don't know what causes this, that's why im not putting While True
        try:
            await message.components[0].children[0].click()
        except InvalidData:
            print(f"Could not claim Kakera {channel.guild.name}.\n")
            return

        print(f"Claimed Kakera on {channel.guild.name}.\n")
        self -= cost
