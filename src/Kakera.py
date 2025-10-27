from asyncio import sleep

from discord.errors import NotFound, InvalidData
from discord.ext import tasks

from .Cooldown import DAY_IN_SECONDS, Cooldown


class Kakera:
    def __init__(
        self,
        value: int,
        cost: int,
        total: int,
        dk: Cooldown,
    ):
        self._value: int = value
        self._cost: int = cost
        self._total: int = total
        self._dk: Cooldown = dk

    @property
    def value(self) -> int:
        return self._value

    @property
    def cost(self) -> int:
        return self._cost

    @property
    def total(self) -> int:
        return self._total

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
        self, channel, prefix: str = "$", cooldown=DAY_IN_SECONDS
    ) -> None:
        while True:
            try:
                await channel.send(f"{prefix}dk")
            except NotFound:
                continue
            break

        self._value = self._total
        print(f"Claimed dk on {channel.guild.name}.\n")
        await self._dk.set_cooldown(cooldown)

    async def can_claim(self, channel, cost) -> bool:
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

        if not self._dk.on_cooldown:
            print(f"... You can claim kakera on {channel.guild.name}.\n")
            await self._dk.set_cooldown()
            return True

        print(
            f"... You don't have enough kakera ({self._value}) on {channel.guild.name}.\n"
        )
        return False

    async def claim(self, message, half: bool = False, delay=0) -> None:
        """
        Claims kakera from the given message.
        :param message: The Discord message to claim kakera from.
        :param half: Whether to claim half of the kakera.
        :param delay: The delay in seconds before claiming kakera.
        """
        channel = message.channel
        print(f"Waiting {delay} to claim kakera on {channel.guild.name}.\n")
        await sleep(delay)

        # I don't know if Mudae rounds to floor or ceil.
        cost = self._cost // 2 if half else self._cost

        if not await self.can_claim(channel, cost):
            return

        # I don't know what causes this, that's why im not putting While True
        try:
            await message.components[0].children[0].click()
        except InvalidData:
            print(f"Could not claim Kakera {channel.guild.name}.\n")
            return

        print(f"Claimed Kakera on {channel.guild.name}.\n")
        self -= cost
