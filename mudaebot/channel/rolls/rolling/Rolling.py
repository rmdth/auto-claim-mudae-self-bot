from asyncio import sleep

from discord.errors import InvalidData, NotFound
from discord.ext import tasks

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

        Args:
            claim (Cooldown): Cooldown object for the claim.
            rt (Cooldown): Cooldown object for the rt.
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

        Args:
            rolls_obj (Rolls): The Rolls object.
            channel (discord.TextChannel): The Discord channel to roll in.
            prefix (str): The prefix being used on the server.
            command (str): The command to roll.
        """
        print(f"Rolling on {channel.guild.name} with {rolls_obj.rolls} rolls...")
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

        Args:
            bot (discord.Client): The Discord bot instance.
            channel (discord.TextChannel): The Discord channel to claim the rt in.
            prefix (str): The prefix being used on the server.
        """
        print(f"Claiming rt on {channel.guild.name}...")
        while True:
            try:
                rt_message = await channel.send(f"{prefix}rt")
            except NotFound:
                continue
            while True:
                try:
                    await bot.wait_for(
                        "reaction_add",
                        check=lambda reaction, user: (
                            reaction.message.id == rt_message.id
                            and user.id == MUDAE_ID
                            and str(reaction.emoji) == "✅"
                        ),
                        timeout=3.0,
                    )
                except TimeoutError:
                    continue
                break
            break

        print(f"... Claimed rt on {channel.guild.name}\n")
        self.claim.reset()
        self.rt.set_cooldown.start()

    def available_claim(self, channel, wish: bool) -> str:
        """
        Checks if the bot can claim.

        Args:
            channel (discord.TextChannel): The Discord channel to check.
            wish (bool): Whether the roll is wished or not.

        Returns:
            str: The claim type.
        """
        print(f"Checking if you can claim on {channel.guild.name}...")
        if self.claim:
            print(f"... You can claim on {channel.guild.name} !!!\n")
            return "claim"

        if self.rt and wish:
            print(f"... You have rt on {channel.guild.name} \n")
            return "rt"

        print(f"... You can't claim on {channel.guild.name} :(\n")
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
        delay_rolls,
    ) -> None:
        """
        Adds roll to the given list and starts the check claims loop.

        Args:
            bot (discord.Client): The Discord bot instance.
            rolls (list): The list of rolls.
            message (discord.Message): The message to add.
            prefix (str): The prefix being used on the server.
            minute_reset (int): The minute when the claim cooldown resets.
            shifthour (int): The hour to shift the cooldown.
            timezone (tzinfo): The timezone of the Client.
            delay_rolls (float): The delay between rolls.
        """
        rolls.append(message)

        try:
            self.check_claims.start(
                bot,
                message,
                prefix,
                minute_reset,
                shifthour,
                timezone,
                delay_rolls=delay_rolls,
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
        timezone,
        delay_rolls: float = 0.0,
    ):
        """
        Waits given delay before preparing claims.

        Args:
            bot (discord.Client): The Discord bot instance.
            message (discord.Message): The message to add.
            prefix (str): The prefix being used on the server.
            minute_reset (int): The minute when the claim cooldown resets.
            shifthour (int): The hour to shift the cooldown.
            timezone (tzinfo): The timezone of the Client.
            delay_rolls (float): The delay between rolls.
        """
        channel = message.channel

        print(f"Waiting {delay_rolls} to claim on {channel.name}. \n")
        await sleep(delay_rolls)
        await self.prepare_rolls(
            bot, channel, minute_reset, shifthour, prefix, timezone
        )

    async def prepare_rolls(
        self,
        bot,
        channel,
        minute_reset,
        shifthour,
        prefix,
        timezone,
        already_sorted: bool = False,
    ) -> None:
        """
        Checks if there are claims, if it can claim and sorts them.

        Args:
            bot (discord.Client): The Discord bot instance.
            channel (discord.TextChannel): The Discord channel to check.
            minute_reset (int): The minute when the claim cooldown resets.
            shifthour (int): The hour to shift the cooldown.
            prefix (str): The prefix to use for the claim command.
            timezone (tzinfo): The timezone of the Client.
            already_sorted (bool): Whether the rolls are already sorted.
        """

        roll_list = (
            self._wished_rolls_being_watched or self._regular_rolls_being_watched
        )

        if not roll_list:
            print(f"Nothing to claim on {channel.name} :( \n")
            return

        claim = self.available_claim(channel, bool(self._wished_rolls_being_watched))
        if not claim:
            self.clean_rolls(channel)
            return

        if not already_sorted:
            Rolls.sort_by_highest_kakera(roll_list)

        await self.claim_roll(
            bot, roll_list, minute_reset, shifthour, prefix, timezone, claim
        )

    async def claim_roll(
        self,
        bot,
        rolls: list,
        minute_reset: int,
        shifthour: int,
        prefix: str,
        timezone,
        claim: str,
    ) -> None:
        """
        Claims the roll.

        Args:
            bot (discord.Client): The Discord bot instance.
            rolls (list): The list of rolls.
            minute_reset (int): The minute when the claim cooldown resets.
            shifthour (int): The hour to shift the cooldown.
            prefix (str): The prefix being used on the server.
            timezone (tzinfo): The timezone of the Client.
            claim (str): The claim type.
        """
        roll_to_claim = rolls.pop(0)
        channel = roll_to_claim.channel

        if Rolls.was_claimed(roll_to_claim) and (
            self._wished_rolls_being_watched or self._regular_rolls_being_watched
        ):
            print(
                f"Someone already claimed {Rolls.get_roll_name_n_series(roll_to_claim)} on {channel.guild.name} :(\n"
            )
            print(f"Trying to claim the next roll on {channel.guild.name}...")
            await self.claim_roll(
                bot,
                self._wished_rolls_being_watched or self._regular_rolls_being_watched,
                minute_reset,
                shifthour,
                prefix,
                timezone,
                claim,
            )
            return

        message = ""

        if claim == "rt" and self.rt:
            await self.claim_rt(bot, channel, prefix)
        else:
            message = "You used rt on ur own, restart the bot"

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

        if claim == "claim" and self._wished_rolls_being_watched and self.rt:
            print(
                f"Trying to see if the next wish can be claimed with rt on {channel.guild.name}..."
            )
            await self.claim_roll(
                bot=bot,
                rolls=self._wished_rolls_being_watched,
                minute_reset=minute_reset,
                shifthour=shifthour,
                prefix=prefix,
                timezone=timezone,
                claim="rt",
            )

        self.clean_rolls(channel)

    def clean_rolls(self, channel) -> None:
        """
        Cleans the rolls.

        Args:
            channel (discord.TextChannel): The Discord channel you are cleaning rolls on.

        """
        self._regular_rolls_being_watched.clear()
        self._wished_rolls_being_watched.clear()
        print(f"Cleaned rolls on {channel.name}.\n")
