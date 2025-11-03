from asyncio import sleep

from discord.errors import NotFound, InvalidData
from discord.ext import tasks

from ...cooldown.Cooldown import Cooldown
from ..Rolls import Rolls

from ....constants import MUDAE_ID


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
        """
        Rolls the specified number of rolls.
        """
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
    async def claim_rt(self, bot, channel, prefix: str = "$") -> None:
        """
        Claims the rt.
        """
        while True:
            try:
                rt_message = await channel.send(f"{prefix}rt")
            except NotFound:
                continue
            while True:
                try:
                    await bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: print(
                            str(reaction.emoji) == "✅", user.id == MUDAE_ID
                        )
                        or (
                            reaction.message.id == rt_message.id
                            and user.id == MUDAE_ID
                            and str(reaction.emoji) == "✅"
                        ),
                        timeout=3,
                    )
                except TimeoutError:
                    continue
                break
            break

        print(f"Claimed rt on {channel.guild.name}\n")
        self.claim.reset()
        self.rt.set_cooldown.start()

    async def available_claim(self, channel) -> str:
        """
        Checks if the bot can claim.
        """
        if self.claim:
            print(f"You can claim on {channel.guild.name} !!!\n")
            return "claim"

        if self.rt:
            print(f"Available rt on {channel.guild.name} \n")
            return "rt"

        print(f"You can't claim on {channel.guild.name} :(\n")
        return ""

    def add_roll(
        self,
        bot,
        rolls: list,
        message,
        prefix,
        minute_reset,
        shifthour,
        timezone,
        uptime,
        wish: bool = False,
    ) -> None:
        rolls.append(message)

        try:
            self.check_claims.start(
                bot,
                message,
                prefix,
                minute_reset,
                shifthour,
                timezone,
                uptime,
            )
        except RuntimeError:
            pass

    @tasks.loop(count=1)
    async def check_claims(
        self,
        bot,
        message,
        prefix: str,
        minute_reset: int,
        shifthour: int,
        timezone: int,
        uptime: float = 0.0,
    ):

        channel = message.channel
        print(f"Waiting {uptime} to claim on {channel.name}")
        await sleep(uptime)
        if not (claim := await self.available_claim(channel)):
            return
        await self.prepare_rolls(
            bot,
            channel,
            minute_reset,
            shifthour,
            prefix,
            timezone,
            claim,
        )

    async def prepare_rolls(
        self,
        bot,
        channel,
        minute_reset,
        shifthour,
        prefix,
        timezone,
        claim: str,
        already_sorted: bool = False,
    ) -> None:
        if self._wished_rolls_being_watched:
            roll_list = self._wished_rolls_being_watched
            wish = True
        elif self._regular_rolls_being_watched:
            roll_list = self._regular_rolls_being_watched
            wish = False
        else:
            print(f"Nothing to claim on {channel.name} :( \n")
            return

        if not already_sorted:
            Rolls.sort_by_highest_kakera(roll_list)

        if claim == "rt" and wish:
            await self.claim_rt(bot, channel, prefix)

        await self.claim_roll(
            bot, roll_list, minute_reset, shifthour, prefix, timezone, claim, wish
        )

    async def claim_roll(
        self,
        bot,
        rolls: list,
        minute_reset: int,
        shifthour: int,
        prefix: str,
        timezone: int,
        claim: str,
        wish: bool,
    ) -> None:
        roll_to_claim = rolls.pop(0)
        channel = roll_to_claim.channel

        if Rolls.was_claimed(roll_to_claim):
            print(
                f"Someone already claimed {Rolls.get_roll_name_n_series(roll_to_claim)} on {channel.guild.name} :(\n"
            )
            print(f"Trying to claim another roll on {channel.guild.name}...")
            await self.prepare_rolls(
                bot,
                channel,
                minute_reset,
                shifthour,
                prefix,
                timezone,
                claim,
                already_sorted=True,
            )
            return

        if claim == "rt" and not wish:
            self.clean_rolls(channel)
            return

        message = ""
        try:
            await roll_to_claim.components[0].children[0].click()
            message = f"{Rolls.get_roll_name_n_series(roll_to_claim)} claimed on {channel.guild.name}! \n"
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
            message = f"Failed to claim {Rolls.get_roll_name_n_series(roll_to_claim)} on {channel.guild.name} :( \n"

        print(message)

        if claim == "claim" and wish and rolls:
            await self.prepare_rolls(
                bot,
                channel,
                minute_reset,
                shifthour,
                prefix,
                timezone,
                claim,
                already_sorted=True,
            )

        self.clean_rolls(channel)

    def clean_rolls(self, channel) -> None:
        print(f"Cleaning rolls on {channel.guild.name}...")
        self._regular_rolls_being_watched.clear()
        self._wished_rolls_being_watched.clear()
