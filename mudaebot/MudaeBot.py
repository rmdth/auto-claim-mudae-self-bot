from asyncio import gather, sleep
from datetime import timezone


import discord
from discord.ext import tasks


from .constants import MUDAE_ID
from .channel.Channel import Channel
from .channel.rolls.Rolls import Rolls
from .channel.rolls.rolling.Rolling import Rolling
from .channel.kakera.Kakera import Kakera
from .channel.cooldown.Cooldown import Cooldown

MAX_MUDAE_COOLDOWN: int = 72000


class MudaeBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timezone: timezone = kwargs.get("timezone", timezone.utc)
        self.channels_information: dict[int, dict] = kwargs.get(
            "channels_information", {}
        )
        self.channels: dict[int, Channel] = {}

        if not self.channels_information:
            raise ValueError("Channels dictionary is empty.")

    async def setup_hook(self) -> None:
        self.setup.start()

    async def on_ready(self) -> None:
        assert self.user is not None
        print(f"Logged on as {self.user} (ID: {self.user.id})!")

    async def on_message(self, message: discord.Message) -> None:
        try:
            self.channels[message.channel.id]
        except KeyError:
            return

        if message.author.id != MUDAE_ID:
            return

        if message.embeds:
            await self.channels[message.channel.id].should_i_claim(
                self, self.user, message
            )

    @tasks.loop(count=1)
    async def setup(self) -> None:
        await gather(
            *(
                self.setup_channels(information)
                for information in self.channels_information.values()
            )
        )
        await sleep(1)

    async def setup_channels(self, information: dict) -> None:
        channel = self.get_channel(information["id"])

        if channel is None:
            print(f"Channel {information['id']} not found.")
            return

        tu = await Channel.get_tu(
            self,
            channel,
            information["settings"]["prefix"],
        )

        claim = Channel.get_current_claim(tu)
        if not claim:
            claim = Cooldown(
                cooldown=Channel.get_msg_time(Channel.get_current_claim_time(tu)),
                max_cooldown=10800,
            )
        else:
            claim = Cooldown(max_cooldown=10800)

        rt = Channel.get_rt(tu)
        if not rt:
            rt = Cooldown(
                max_cooldown=information["settings"]["max_rt_cooldown_in_seconds"]
            )
        else:
            rt = Cooldown(
                cooldown=Channel.get_msg_time(rt),
                max_cooldown=information["settings"]["max_rt_cooldown_in_seconds"],
            )

        rolling = Rolling(claim, rt)
        rolls = Channel.get_rolls(tu)
        rolls = Rolls(
            rolling,
            information["settings"]["wish_list"],
            information["settings"]["wish_series"],
            rolls=int(rolls[0]) if rolls else 0,
            max_rolls=information["settings"]["max_rolls"],
            min_kakera_value=information["settings"]["min_kakera_value"],
        )

        dk = Channel.get_dk(tu)
        if not dk:
            dk = Cooldown(max_cooldown=MAX_MUDAE_COOLDOWN)
        else:
            dk = Cooldown(
                cooldown=Channel.get_msg_time(dk),
                max_cooldown=MAX_MUDAE_COOLDOWN,
            )

        kakera = Channel.get_kakera(tu)
        kakera = Kakera(
            int(kakera[0]),
            int(kakera[1]),
            information["settings"]["kakera_power_total"],
            dk,
            information["settings"]["wish_kakera"],
        )

        self.channels[information["id"]] = Channel(
            kakera,
            rolls,
            self.timezone,
            information["settings"]["prefix"],
            information["settings"]["command"],
            information["settings"]["uptime"],
            information["settings"]["delay"],
            information["settings"]["shifthour"],
            information["settings"]["restart_time_minute"],
            information["settings"]["last_claim_threshold_in_seconds"],
        )
        self.channels[information["id"]].kakera.auto_regen.start()
        self.channels[information["id"]].rolls.rolling.rolling.start(
            self.channels[information["id"]].rolls,
            channel,
            self.channels[information["id"]].prefix,
            self.channels[information["id"]].command,
        )

    @setup.before_loop
    async def wait_for_ready(self) -> None:
        await self.wait_until_ready()
