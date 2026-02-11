import logging
from asyncio import sleep
from datetime import datetime, timezone
from random import choice

import discord
from discord.ext import tasks

from src.adapters.channel import MudaeChannel
from src.core.constants import MAX_MUDAE_COOLDOWN, MUDAE_ID
from src.core.logic import get_roll_type
from src.core.models import ChannelSettings, Cooldown, KakeraStock, Rolling
from src.core.parsers import parse_message

logger = logging.getLogger(__name__)


class MudaeBot(discord.Client):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timezone: timezone = kwargs.get("timezone", timezone.utc)
        self.channels_information: list[dict] = kwargs.get("channels_information", {})
        self.channels: dict[int, MudaeChannel] = {}

        self.daily: Cooldown = Cooldown()

        if not self.channels_information:
            raise ValueError("Channels dictionary is empty.")

    @tasks.loop(hours=1)
    async def _claim_daily(self) -> None:
        await sleep(MAX_MUDAE_COOLDOWN)

        await self.channels[choice(list(self.channels.keys()))].claim_daily(
            self, self.daily, self.timezone
        )

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

        if message.author.id != MUDAE_ID or not message.embeds:
            return

        embed = message.embeds[0].to_dict()
        roll_type = get_roll_type(embed, message.components[0].children[0].emoji.name)

        if not (
            unit := parse_message(
                embed,
                roll_type,
                self.channels[message.channel.id].kakera_stock.kakera_cost,
                self.user.name,
                message,
            )
        ):
            return

        if not (
            available_claim := self.channels[message.channel.id].available_claim(
                unit, self.timezone
            )
        ):
            return

        if not self.channels[message.channel.id].should_claim(
            unit,
            self.channels[
                message.channel.id
            ].settings.roll_preferences.min_kakera_value,
            self.channels[message.channel.id].rolling.claim.remaining_seconds(
                datetime.now(tz=self.timezone).timestamp()
            )
            <= self.channels[
                message.channel.id
            ].settings.last_claim_threshold_in_seconds,
            available_claim,
        ):
            return

        self.channels[message.channel.id].add(unit, self, self.timezone)

    @tasks.loop(count=1)
    async def setup(self) -> None:
        for settings in self.channels_information:
            id = settings["id"]
            discord_channel = self.get_channel(id)

            if discord_channel is None:
                print(f"Channel {id} not found.")
                continue

            mudae_channel = MudaeChannel(
                discord_channel, ChannelSettings.from_dict(settings)
            )
            self.channels[id] = mudae_channel

            data = await mudae_channel.fetch_tu_data(
                self, datetime.now(tz=self.timezone).timestamp()
            )
            data["max_rolls"] = settings["max_rolls"]
            data["kakera_max"] = settings["kakera_max"]

            kakera_stock = KakeraStock.from_dict(data)
            rolling = Rolling.from_dict(data)

            mudae_channel.set_kakera_stock(kakera_stock)
            mudae_channel.set_rolling(rolling)

            self.daily = data["daily"]
            try:
                self._claim_daily.start()
            except RuntimeError:
                pass

    @setup.before_loop
    async def wait_for_ready(self) -> None:
        await self.wait_until_ready()
