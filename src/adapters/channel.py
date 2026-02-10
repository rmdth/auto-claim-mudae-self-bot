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
        for _ in range(self.rolling.rolls):
            await self.roll()
            await sleep(0.5)
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
            self._check_kakera.start(bot, timezone)
            return

        self.rolling.add(unit)

        try:
            self._check_rolls.start(bot, timezone)
        except RuntimeError:
            pass

    @tasks.loop(count=1)
    async def _check_kakera(self, bot: Any, timezone: timezone) -> None:
        await sleep(self.settings.delay_kakera)
        kakera_to_claim: KakeraUnit = self.kakera_stock.claimable_kakera.pop()

        current_time = datetime.now(tz=timezone).timestamp()
        if self.kakera_stock.available_claim(
            kakera_to_claim, current_time
        ) == "dk" and self.dk.is_ready(current_time):
            await self.claim_dk(bot, timezone)

        await self.claim_kakera(kakera_to_claim)
        if self.kakera_stock.claimable_kakera and self.kakera_stock.dk.is_ready(
            current_time
        ):
            candidate = self.kakera_stock.claimable_kakera.pop()
            if self.should_claim(candidate, 0, False, "dk"):
                await self.claim_kakera(candidate)

        self.kakera_stock.claimable_kakera.clear()

    @retry(delay=0, exceptions=(NotFound, InvalidData))
    async def claim_kakera(self, kakera: KakeraUnit) -> None:
        await kakera.message.components[0].children[0].click()
        self.kakera_stock -= kakera.claim_cost

    @tasks.loop(count=1)
    async def _check_rolls(self, bot: Any, timezone: timezone) -> None:
        await sleep(self.settings.delay_rolls)
        roll_to_claim: Roll = self.rolling.claimable_rolls.pop()
        if roll_to_claim.was_claimed:
            return

        current_time = datetime.now(tz=timezone).timestamp()
        if self.rolling.available_claim(
            current_time
        ) == "rt" and self.rolling.rt.is_ready(current_time):
            await self.claim_rt(bot, timezone)

        await self.claim_roll(roll_to_claim.message, timezone)
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

    @retry(delay=0, exceptions=(NotFound, RuntimeError, InvalidData))
    async def claim_roll(self, roll: Message, timezone: timezone) -> None:
        await roll.components[0].children[0].click()
        self.rolling.claim.set_cooldown(
            next_claim(
                datetime.now(tz=self._timezone),
                self.settings.minute_reset,
                self.settings.shifthour,
            ),
            datetime.now(tz=timezone).timestamp(),
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
        self.dk.set_cooldown(
            self.settings.dk_max_cooldown_in_seconds,
            datetime.now(tz=timezone).timestamp(),
        )

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def claim_rt(self, bot, timezone) -> None:
        sent_message = await self._channel.send(f"{self.settings.prefix}rt")

        await bot.wait_for(
            "reaction_add",
            check=lambda reaction, user: (
                reaction.message.id == sent_message.id
                and user.id == MUDAE_ID
                and str(reaction.emoji) == "✅"
            ),
            timeout=1.0,
        )
        self.rt.set_cooldown(
            self.settings.rt_max_cooldown_in_seconds,
            datetime.now(tz=timezone).timestamp(),
        )

    @retry(delay=0, exceptions=(TimeoutError, NotFound))
    async def claim_daily(self, bot: Any, daily: Cooldown, timezone: timezone) -> None:
        sent_message = await self._channel.send(f"{self.settings.prefix} daily")

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
