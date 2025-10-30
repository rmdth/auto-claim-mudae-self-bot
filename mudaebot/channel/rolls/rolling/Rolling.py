from asyncio import sleep

from discord.errors import NotFound, InvalidData
from discord.ext import tasks

from main import bot

from ....constants import MUDAE_ID

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
                        "raw_reaction_add",
                        check=lambda payload: payload.message_id == rt_message.id
                        and payload.user_id == MUDAE_ID
                        and str(payload.emoji) == "✅",
                        timeout=1,
                    )
                    break
                except TimeoutError:
                    continue
            break

        print(f"Claimed rt on {channel.guild.name}\n")
        self.claim.reset()
        self.rt.set_cooldown.start()

    async def can_claim(self, bot, message, prefix: str) -> bool:
        """
        Checks if the bot can claim.
        """
        channel = message.channel

        if self.claim:
            print(f"You can claim on {channel.guild.name} !!!\n")
            return True

        if self.rt:
            print(f"Trying to claim rt on {channel.guild.name} !!!\n")
            await self.claim_rt(bot, channel, prefix)
            return True

        print(f"You can't claim on {channel.guild.name} :(\n")
        return False

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
    ) -> None:
        rolls.append(message)

        try:
            self.decide_claim.start(
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
    async def decide_claim(
        self,
        bot,
        message,
        prefix: str,
        minute_reset: int,
        shifthour: int,
        timezone: int,
        uptime: float = 0.0,
    ):

        if not await self.can_claim(bot, message, prefix):
            return

        await sleep(uptime)
        channel = message.channel
        print(f"Deciding claim for channel {channel.name}")

        roll_list = (
            self._wished_rolls_being_watched or self._regular_rolls_being_watched
        )

        if not roll_list:
            print(f"Nothing to claim on {channel.name} :( \n")
            return

        await Rolls.sort_by_highest_kakera(roll_list)
        await self.claim_roll(roll_list, minute_reset, shifthour, timezone)

    async def claim_roll(self, rolls, minute_reset, shifthour, timezone) -> None:
        roll_to_claim = rolls[0]
        channel = roll_to_claim.channel

        if roll_to_claim.embeds[0].to_dict()["color"] == 6753288:
            print(
                f"Someone already claimed {Rolls.get_roll_name_n_series(roll_to_claim)} on {channel.guild.name} :(\n"
            )
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
        self.clean_rolls(channel)

    def clean_rolls(self, channel) -> None:
        print(f"Cleaning rolls on {channel.guild.name}...")
        self._regular_rolls_being_watched.clear()
        self._wished_rolls_being_watched.clear()
