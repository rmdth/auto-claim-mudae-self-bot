from asyncio import sleep

from discord.errors import NotFound, InvalidData
from discord.ext import tasks

from ...cooldown.Cooldown import Cooldown
from ..Rolls import Rolls


class Rolling:
    def __init__(
        self,
        claim: Cooldown,
        rt: Cooldown,
    ) -> None:
        """
        Initializes and instance of Rolling.
        :param claim: Cooldown object for the claim
        :param rt: Cooldown object for the rt
        """
        self._claim: Cooldown = claim
        self._rt: Cooldown = rt

        self._regular_rolls_being_watched: list = []
        self._wished_rolls_being_watched: list = []

    @property
    def claim(self) -> Cooldown:
        return self._claim

    @property
    def rt(self) -> Cooldown:
        return self._rt

    @property
    def regular_rolls_being_watched(self) -> list:
        return self._regular_rolls_being_watched

    @property
    def wished_rolls_being_watched(self) -> list:
        return self._wished_rolls_being_watched

    @tasks.loop(hours=1)
    async def rolling(self, rolls_obj: Rolls, channel, prefix, command) -> None:
        print(f"Rolling on {channel.guild.name} with {rolls_obj.rolls} rolls...\n")
        for _ in range(rolls_obj.rolls):
            while True:
                try:
                    await channel.send(f"{prefix}{command}")
                except NotFound:
                    continue
                break
            await sleep(0.5)
            rolls_obj -= 1

        print(f"Finished rolling on {channel.guild.name}.\n")
        rolls_obj.reset_rolls()

    # @tasks.loop(count=1) # Uncomment IF errors
    async def claim_rt(self, channel, prefix: str = "$") -> None:
        while True:
            try:
                await channel.send(f"{prefix}rt")
            except NotFound:
                continue
            break

        print(f"Claimed rt on {channel.guild.name}\n")

        self.rt.set_cooldown.start()
        self.claim.reset()

    async def can_claim(self, channel, prefix: str) -> bool:
        if self.claim:
            print(f"You can claim on {channel.guild.name} !!!\n")
            return True

        if self.rt:
            print(f"Trying to claim rt on {channel.guild.name} !!!\n")
            await self.claim_rt(channel, prefix)
            return True

        print(f"You can't claim on {channel.guild.name} :(\n")
        return False

    def add_roll(
        self, rolls: list, message, prefix, minute_reset, shifthour, timezone, uptime
    ) -> None:
        rolls.append(message)

        try:
            self.decide_claim.start(
                message.channel, prefix, minute_reset, shifthour, timezone, uptime
            )
        except RuntimeError:
            pass

    @tasks.loop(count=1)
    async def decide_claim(
        self,
        channel,
        prefix: str,
        minute_reset: int,
        shifthour: int,
        timezone: int,
        uptime: float = 0.0,
    ):
        await sleep(uptime)

        if not await self.can_claim(channel, prefix):
            return

        print(f"Deciding claim for channel {channel.name}")

        roll_list = (
            self._wished_rolls_being_watched or self._regular_rolls_being_watched
        )

        if not roll_list:
            print(f"Nothing to claim on {channel.name} :( \n")
            return

        await Rolls.sort_by_highest_kakera(roll_list)
        await self.claim_roll(channel, roll_list, minute_reset, shifthour, timezone)

    async def claim_roll(
        self, channel, rolls, minute_reset, shifthour, timezone
    ) -> None:
        message = ""

        try:
            await rolls[0].components[0].children[0].click()
            message = f"{Rolls.get_roll_name_n_series(rolls[0])} claimed on {channel.guild.name}! \n"
            try:
                self.claim.set_cooldown.start(
                    Cooldown.next_claim(
                        timezone=timezone,
                        minute_reset=minute_reset,
                        shifthour=shifthour,
                    )
                )
            except RuntimeError:
                message = f"Trying to set cooldown when already on cooldown on {channel.guild.name} \n"
        except InvalidData:
            message = f"Failed to claim {Rolls.get_roll_name_n_series(rolls[0])} on {channel.guild.name} :( \n"

        print(message)
        self.clean_rolls(channel)

    def clean_rolls(self, channel) -> None:
        print(f"Cleaning rolls on {channel.guild.name}...")
        self._regular_rolls_being_watched.clear()
        self._wished_rolls_being_watched.clear()
