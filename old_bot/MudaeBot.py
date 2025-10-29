import discord
import asyncio
from datetime import datetime, timezone, timedelta
from discord.ext import tasks
from tomllib import load
from re import compile

MUDAE_ID = 432610292342587392

settings = load(open("./bot-settings.toml", "rb"))

channels_information = {}
utc_delta: int = settings["UTC_delta"]
TIME_ZONE: timezone = timezone(timedelta(hours=utc_delta))

for information in settings["channels_information"]:
    channels_information[information["id"]] = {
        "settings": information["settings"],
    }

wish_series = settings["wish_series"]

powers_pattern = compile(r"(\d+)%")

# Finds or not
kakera_description_pattern = compile(r"\*\*(\d+)\*\*")
find_tu_pattern = compile(r"\*\*=>\*\* \$tuarrange")
claim_in_tu_pattern = compile(r"__(.+)__.+\.")

# If it doesn't find it is available, finds 2 digits (hour and minute) or 1 digit (minute)
daily_in_tu_pattern = compile(r"\$daily\D+(\d\d)?.+(\d\d)")
rt_in_tu_pattern = compile(r"\$rt\D+(\d\d)?.+(\d\d)")
dk_in_tu_pattern = compile(r"\$dk\D+(\d\d)?.+(\d\d)")


class KakeraPower:
    def __init__(
        self,
        total: int,
        cost: int,
        value: int,
        delay: int,
        prefix: str,
        channel,
        dk=True,
    ) -> None:
        self._total: int = total
        self._cost: int = cost
        self._value: int = value
        self._delay: int = delay
        self._prefix: str = prefix
        self._channel = channel
        self._dk: bool = dk

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

    @property
    def total(self) -> int:
        return self._total

    @property
    def cost(self) -> int:
        return self._cost

    @property
    def value(self) -> int:
        return self._value

    @property
    def dk(self):
        return self._dk

    @tasks.loop(minutes=3)
    async def auto_regen(self) -> None:
        self += 1

    @tasks.loop(count=1)
    async def claim_dk(self) -> None:
        while True:
            try:
                await self._channel.send(f"{self._prefix}dk")
            except discord.errors.NotFound:
                continue
            break
        self._dk = False
        self._value = self._total

        print(f"Claimed dk on {self._channel.guild.name}.\n")
        await asyncio.sleep(86400)
        self._dk = True

    async def can_claim(self) -> bool:
        print(f"Cheking if you can claim kakera on {self._channel.guild.name}...")
        if not self._value >= self._cost:
            if self._dk:
                try:
                    self.claim_dk.start()
                except RuntimeError:
                    print(
                        f"... You can't claim kakera on {self._channel.guild.name}.\n"
                    )
                    return False
                print(f"... You can claim kakera on {self._channel.guild.name}.\n")
                return True
            print(f"... You can't claim kakera on {self._channel.guild.name}.\n")
            return False
        print(f"... You can claim kakera on {self._channel.guild.name}.\n")
        return True

    async def claim(self, message) -> None:
        print(f"Waiting {self._delay} to claim kakera on {self._channel.guild.name}.\n")
        await asyncio.sleep(self._delay)

        if not await self.can_claim():
            return
        # I don't know what causes this, that's why im not putting While True
        try:
            await message.components[0].children[0].click()
        except discord.errors.InvalidData:
            print(f"Could not claim Kakera {self._channel.guild.name}.\n")
            return

        print(f"Claimed Kakera on {self._channel.guild.name}.\n")
        self -= self.cost


class ClaimCooldown:
    def __init__(self, shifthour: int) -> None:
        self._shifthour: int = shifthour
        self._possible_hours: list[int] = [1, 3, 2]
        self._max_cooldown: timedelta = timedelta(hours=3)

    def get_current(self) -> float:
        time: datetime = datetime.now(tz=TIME_ZONE)
        time = time - timedelta(hours=self._shifthour)

        cooldown = timedelta(
            hours=self._possible_hours[time.hour % 3],
            minutes=40 - time.minute,
            seconds=-time.second,
        )

        if cooldown > self._max_cooldown:
            cooldown -= self._max_cooldown

        return cooldown.total_seconds()


class Rolls:
    def __init__(
        self,
        quantity: int,
        wished: list,
        prefix: str,
        command: str,
        delay: int,
        min_kakera_value: int,
        minute_reset: int,
        shifthour: int,
        rt_cooldown_in_seconds: int,
        channel,
        claim=True,
        rt=True,
    ) -> None:
        self._quantity: int = quantity
        self._wished: list = wished
        self._prefix: str = prefix
        self._command: str = command
        self._delay: int = delay
        self._min_kakera_value: int = min_kakera_value
        self._minute_reset: int = minute_reset
        self._shifthour: int = shifthour
        self._rt_cooldown: int = rt_cooldown_in_seconds
        self._rt: bool = rt
        self._claim: bool = claim
        self._claim_cooldown: ClaimCooldown = ClaimCooldown(shifthour)
        self._available_wished_claims: list = []
        self._available_regular_claims: list = []
        self._channel = channel
        self._negative_hours_adjust: list[int] = [2, 0, 1]
        self._hours_adjust: list[int] = [1, 3, 2]

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def wished(self) -> list[str]:
        return self._wished

    @property
    def min_kakera_value(self) -> int:
        return self._min_kakera_value

    @property
    def delay(self) -> int:
        return self._delay

    @property
    def minute_reset(self) -> int:
        return self._minute_reset

    @property
    def rt_cooldown_in_seconds(self) -> int:
        return self._rt_cooldown

    @property
    def claim(self) -> bool:
        return self._claim

    @property
    def rt(self) -> bool:
        return self._rt

    @property
    def available_wished_claims(self) -> list:
        return self._available_wished_claims

    @property
    def available_regular_claims(self) -> list:
        return self._available_regular_claims

    @tasks.loop(count=1)
    async def claim_rt(self) -> None:
        self._rt = False

        while True:
            try:
                await self._channel.send(f"{self._prefix}rt")
            except discord.errors.NotFound:
                continue
            break

        print(f"Claimed rt on {self._channel.guild.name}\n")
        await asyncio.sleep(self._rt_cooldown)
        self._rt = True

    @tasks.loop(count=1)
    async def claim_cooldown(self) -> None:
        self._claim = False
        await asyncio.sleep(self._claim_cooldown.get_current())
        self._claim = True

    @tasks.loop(count=1)
    async def check_claims(self) -> None:
        await asyncio.sleep(self._delay)
        print(f"Checking Claims on {self._channel.guild.name}...")
        await self.claim_rolls()

    @tasks.loop(hours=1)
    async def rolling(self) -> None:
        print(f"Rolling on {self._channel.guild.name}...")
        for _ in range(self._quantity):
            while True:
                try:
                    await self._channel.send(f"{self._prefix}{self._command}")
                except discord.errors.NotFound:
                    continue
                break
            await asyncio.sleep(0.5)

    async def add_roll(self, roll_list, message) -> None:
        roll_list.append(message)
        try:
            await self.check_claims.start()
        except RuntimeError:
            pass

    async def claim_rolls(self) -> None:
        if not await self.can_claim():
            return

        roll_list = self._available_wished_claims or self._available_regular_claims

        if not roll_list:
            return

        message = ""

        await self.sort_by_highest_kakera_value(roll_list)

        # I don't know what causes this, that's why im not putting While True
        try:
            await roll_list[0].components[0].children[0].click()
            message = f"{roll_list[0].embeds[0].to_dict()['author']['name']} was claimed on {self._channel.guild.name}"
            try:
                self.claim_cooldown.start()
            except RuntimeError:
                pass
        except discord.errors.InvalidData:
            message = f"Could not claim {roll_list[0].embeds[0].to_dict()['author']['name']} on {self._channel.guild.name}."

        print(message)
        self.clean_claims()

    async def can_claim(self) -> bool:
        print(f"Cheking if you can claim rolls on {self._channel.guild.name}...")
        if not self._claim:
            if self._rt:
                self.claim_rt.start()
                print(f"... You can claim rolls on {self._channel.guild.name}\n")
                return True
            print(f"... You can't claim rolls on {self._channel.guild.name}\n")
            return False
        print(f"... You can claim rolls on {self._channel.guild.name}\n")
        return True

    def clean_claims(self) -> None:
        print(f"Cleaning claims on {self._channel.guild.name}.")
        self._available_regular_claims = []
        self._available_wished_claims = []

    async def clean_wish(self) -> None:
        """
        Change the wished list and the toml file.
        """
        raise NotImplementedError

    def last_claim(self) -> bool:
        time: datetime = datetime.now(tz=TIME_ZONE)

        adjusted_hour = time.hour - self._shifthour

        return (not adjusted_hour % 3 and time.minute > self._minute_reset) or (
            not (adjusted_hour - 1) % 3 and time.minute < self._minute_reset
        )

    async def sort_by_highest_kakera_value(self, some_list: list) -> None:
        some_list.sort(
            reverse=True,
            key=lambda item: int(
                kakera_description_pattern.findall(
                    item.embeds[0].to_dict()["description"]
                )[0]
            ),
        )


class MudaeBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.kakera_for_guilds: dict[int, KakeraPower] = {}
        self.rolls_for_guilds: dict[int, Rolls] = {}

    async def setup_hook(self) -> None:
        self.setup.start()

    async def on_ready(self) -> None:
        assert self.user is not None
        print(f"Logged on as {self.user} (ID: {self.user.id})!")

    async def found_tu(self, channel) -> int:  # TODO
        last_message = await channel.fetch_message(channel.last_message_id)
        if find_tu_pattern.search(last_message.content):
            return last_message.id
        return 0

    async def get_tu(self, channel, prefix) -> int:  # TODO
        tu_id = 0
        while not (output := await self.found_tu(channel)):
            while True:
                try:
                    await channel.send(f"{prefix}tu")
                except discord.errors.NotFound:
                    continue
                break

        return output

    def is_valid_roll(self, message, information) -> str:
        if (
            "image" not in information
            or "author" not in information
            # or list(embed.get("author", {}).keys()) != ["name"]
        ):
            # Not a valid roll if no image or author or if author keys don't match
            return ""

        # Check if there's a footer with pagination, which would indicate it's not a roll
        if "footer" in information and "text" in information["footer"]:
            if "/" in information["footer"]["text"]:
                return ""
            elif (
                message.components != []
                and "kakera" in message.components[0].children[0].emoji.name
            ):
                return "kakera"

        # All checks passed, it seems to be a valid roll
        return "roll"

    async def should_i_claim(self, m: discord.Message) -> None:
        if not m.embeds:
            return

        embed = m.embeds[0].to_dict()
        roll_type = self.is_valid_roll(m, embed)
        if not roll_type:
            return

        channel_id = m.channel.id

        if roll_type == "kakera":
            await self.kakera_for_guilds[channel_id].claim(m)
            return

        char_name = embed["author"]["name"]
        description = embed["description"]

        rolls = self.rolls_for_guilds[channel_id]

        if (
            str(self.user.id) in m.content
            or char_name in self.rolls_for_guilds[channel_id].wished
            or description in wish_series
        ):
            print(
                f"Added {char_name} of {description} found in {m.guild}: {m.channel.name} to wished_claims.\n"
            )

            await rolls.add_roll(rolls.available_wished_claims, m)

        if (
            self.rolls_for_guilds[channel_id].last_claim()
            or int(kakera_description_pattern.findall(description)[0])
            > self.rolls_for_guilds[channel_id].min_kakera_value
        ):
            print(
                f"Added {char_name} of {description}found in {m.guild}: {m.channel.name} To regular_claims.\n"
            )
            await rolls.add_roll(rolls.available_regular_claims, m)

    async def on_message(self, message: discord.Message):
        try:
            channels_information[message.channel.id]
        except KeyError:
            return

        if message.author.id != MUDAE_ID:
            return

        if message.embeds:
            await self.should_i_claim(message)

    @tasks.loop(count=1)
    async def setup(self) -> None:
        for id in channels_information:
            channel = self.get_channel(id)

            settings = channels_information[id]["settings"]
            self.kakera_for_guilds[id] = KakeraPower(
                total=settings["kakera_power_total"],
                cost=settings["kakera_power_cost"],
                value=settings["kakera_power_value"],
                delay=settings["delay"],
                prefix=settings["prefix"],
                channel=channel,
            )
            self.rolls_for_guilds[id] = Rolls(
                quantity=settings["rolls"],
                wished=settings["wish_list"],
                prefix=settings["prefix"],
                command=settings["command"],
                min_kakera_value=settings["min_kakera_value"],
                delay=settings["delay"],
                minute_reset=settings["restart_time_minute"],
                shifthour=settings["shifthour"],
                rt_cooldown_in_seconds=settings["rt_cooldown_in_seconds"],
                channel=channel,
            )
            self.kakera_for_guilds[id].auto_regen.start()
            self.rolls_for_guilds[id].rolling.start()

    @setup.before_loop
    async def wait_for_ready(self):
        await self.wait_until_ready()


bot = MudaeBot()
bot.run(settings["token"], reconnect=True)
