import logging
from asyncio import TimeoutError, sleep
from datetime import datetime, timezone
from typing import Any, Callable

from discord.errors import InvalidData, NotFound
from discord.ext import tasks
from discord.message import Message

from src.core.constants import MAX_MUDAE_COOLDOWN, MUDAE_ID
from src.core.logic import next_claim
from src.core.models import (
    ChannelSettings,
    Cooldown,
    KakeraStock,
    KakeraUnit,
    Roll,
    Rolling,
)
from src.core.parsers import (
    _KAKERA_DK_CONFIRMATION_PATTERN,
    get_tu_information,
    is_tu_message,
)
from src.core.utils import retry

logger = logging.getLogger(__name__)


class MudaeChannel:
    def __init__(
        self,
        discord_channel: Any,
        settings: ChannelSettings,
    ) -> None:
        self._channel = discord_channel
        self.settings: ChannelSettings = settings

    def __getattr__(self, name: str) -> Any:
        return getattr(self._channel, name)

    def set_rolling(self, rolling: Rolling) -> None:
        self.rolling: Rolling = rolling
        self._rolling.start()

    def set_kakera_stock(self, kakera_stock: KakeraStock) -> None:
        self.kakera_stock: KakeraStock = kakera_stock

    def set_mode(
        self,
        mode: str,
        decider: Callable[[str], Callable[[Roll | KakeraUnit, int, bool, str], bool]],
    ) -> None:
        self.should_claim: Callable[[Roll | KakeraUnit, int, bool, str], bool] = (
            decider(mode)
        )

    @retry(delay=0, exceptions=(NotFound,))
    async def roll(self) -> None:
        await self._channel.send(f"{self.settings.prefix}{self.settings.command}")

    @tasks.loop(hours=1)
    async def _rolling(self) -> None:
        logger.info(
            f"Rolling on {self._channel.guild.name} with {self.rolling.rolls} rolls..."
        )
        for _ in range(self.rolling.rolls):
            await sleep(0.5)
            await self.roll()
        logger.info(
            f"Finished rolling on {self._channel.guild.name} with {self.rolling.rolls} rolls."
        )
        self.rolling.reset()

    def available_claim(
        self, unit: KakeraUnit | Roll | None, timezone: timezone
    ) -> str:
        if not unit:
            return ""
        elif isinstance(unit, KakeraUnit):
            return self.kakera_stock.available_claim(
                unit, datetime.now(tz=timezone).timestamp()
            )
        elif isinstance(unit, Roll):
            return self.rolling.available_claim(datetime.now(tz=timezone).timestamp())

    def add(self, unit: KakeraUnit | Roll, bot: Any, timezone: timezone) -> None:
        if isinstance(unit, KakeraUnit):
            self.kakera_stock.add(unit)
            logger.info(f"Watching {unit.color} on {self._channel.guild.name}")
            try:
                self._check_kakera.start(bot, timezone)
            except RuntimeError:
                pass
            return

        self.rolling.add(unit)
        logger.info(f"Watching {unit} on {self._channel.guild.name}")

        try:
            self._check_rolls.start(bot, timezone)
        except RuntimeError:
            pass

    @tasks.loop(count=1)
    async def _check_kakera(self, bot: Any, timezone: timezone) -> None:
        logger.info(
            f"Waiting {self.settings.delay_kakera}s before claiming kakera on {self._channel.guild.name}..."
        )
        await sleep(self.settings.delay_kakera)
        kakera_to_claim: KakeraUnit = self.kakera_stock.claimable_kakera.pop()

        current_time = datetime.now(tz=timezone).timestamp()
        if self.kakera_stock.available_claim(
            kakera_to_claim, current_time
        ) == "dk" and self.dk.is_ready(current_time):
            await self.claim_dk(bot, timezone)

        await self.claim_kakera(kakera_to_claim)
        logger.info(
            f"Checking if there is more kakera to claim on {self._channel.guild.name}..."
        )

        if self.kakera_stock.claimable_kakera and self.kakera_stock.dk.is_ready(
            current_time
        ):
            candidate = self.kakera_stock.claimable_kakera.pop()
            if self.should_claim(candidate, 0, False, "dk"):
                await self.claim_kakera(candidate)
        logger.info(f"... Can't claim any more kakera on {self._channel.guild.name}.")

        self.kakera_stock.claimable_kakera.clear()

    @retry(delay=0, exceptions=(NotFound, InvalidData))
    async def claim_kakera(self, kakera: KakeraUnit) -> None:
        await kakera.message.components[0].children[0].click()
        self.kakera_stock -= kakera.claim_cost
        logger.info(
            f"... Successfully claimed {kakera.color} on {self._channel.guild.name}."
        )

    @tasks.loop(count=1)
    async def _check_rolls(self, bot: Any, timezone: timezone) -> None:
        logger.info(
            f"Waiting {self.settings.delay_rolls}s before claiming rolls on {self._channel.guild.name}..."
        )
        await sleep(self.settings.delay_rolls)
        roll_to_claim: Roll = self.rolling.claimable_rolls.pop()
        if roll_to_claim.was_claimed():
            logger.info(
                f"... {roll_to_claim.name} was already claimed on {self._channel.guild.name}."
            )
            return

        current_time = datetime.now(tz=timezone).timestamp()
        if self.rolling.available_claim(
            current_time
        ) == "rt" and self.rolling.rt.is_ready(current_time):
            await self.claim_rt(bot, timezone)

        await self.claim_roll(roll_to_claim.message, timezone)
        logger.info(
            f"Checking if can claim more rolls on {self._channel.guild.name}..."
        )
        if self.rolling.claimable_rolls and self.rolling.rt.is_ready(current_time):
            candidate = self.rolling.claimable_rolls.pop()
            if self.should_claim(
                candidate,
                self.settings.roll_preferences.min_kakera_value,
                self.rolling.claim.remaining_seconds(current_time)
                <= self.settings.last_claim_threshold_in_seconds,
                "rt",
            ):
                await self.claim_roll(candidate.message, timezone)
        self.rolling.claimable_rolls.clear()
        logger.debug(f"Cleared claimable rolls on {self._channel.guild.name}")

    @retry(delay=0, exceptions=(NotFound, RuntimeError, InvalidData))
    async def claim_roll(self, roll: Message, timezone: timezone) -> None:
        await roll.components[0].children[0].click()
        self.rolling.claim.set_cooldown(
            next_claim(
                datetime.now(tz=timezone),
                self.settings.minute_reset,
                self.settings.shifthour,
            ),
            datetime.now(tz=timezone).timestamp(),
        )
        logger.info(
            f"... Successfully claimed {roll.embeds[0].title} on {self._channel.guild.name}."
        )

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def fetch_tu_data(self, bot: Any, current_time: float) -> dict[str, Any]:
        await self._channel.send(f"{self.settings.prefix}tu")

        tu_message = await bot.wait_for(
            "message",
            check=lambda message: message.author.id == MUDAE_ID
            and message.channel.id == self._channel.id
            and is_tu_message(message.content),
            timeout=1.5,
        )

        return get_tu_information(tu_message.content, current_time)

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def claim_dk(self, bot, timezone: timezone) -> None:
        await self._channel.send(f"{self.settings.prefix}dk")
        logger.info(f"Claiming dk on {self._channel.guild.name}...")

        await bot.wait_for(
            "message",
            check=lambda message: message.channel.id == self._channel.id
            and message.author.id == MUDAE_ID
            and (
                _KAKERA_DK_CONFIRMATION_PATTERN.match(message.content)
                or "dk" in message.content
            ),
            timeout=1.0,
        )
        self.kakera_stock.dk.set_cooldown(
            self.settings.dk_max_cooldown_in_seconds,
            datetime.now(tz=timezone).timestamp(),
        )
        logger.info(f"... Successfully claimed dk on {self._channel.guild.name}.")

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def claim_rt(self, bot, timezone) -> None:
        sent_message = await self._channel.send(f"{self.settings.prefix}rt")
        logger.info(f"Claiming rt on {self._channel.guild.name}...")

        await bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: (
                reaction.message.id == sent_message.id
                and user.id == MUDAE_ID
                and str(reaction.emoji) == "✅"
            ),
            timeout=1.0,
        )
        self.rolling.rt.set_cooldown(
            self.settings.rt_max_cooldown_in_seconds,
            datetime.now(tz=timezone).timestamp(),
        )
        logger.info(f"... Successfully claimed rt on {self._channel.guild.name}.")

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def claim_daily(self, bot: Any, daily: Cooldown, timezone: timezone) -> None:
        sent_message = await self._channel.send(f"{self.settings.prefix}daily")
        logger.info(f"Claiming daily on {self._channel.guild.name}...")

        await bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: (
                reaction.message.id == sent_message.id
                and user.id == MUDAE_ID
                and str(reaction.emoji) == "✅"
            ),
            timeout=1.0,
        )
        daily.set_cooldown(
            MAX_MUDAE_COOLDOWN,
            datetime.now(tz=timezone).timestamp(),
        )
        logger.info(f"... Successfully claimed daily on {self._channel.guild.name}.")
