import time
from asyncio import sleep
from datetime import datetime, timedelta

from discord.ext import tasks

DAY_IN_SECONDS = 86400
HOUR_IN_SECONDS = 3600


class Cooldown:
    @staticmethod
    def next_claim(timezone=None, minute_reset: int = 0, shifthour: int = 0) -> float:
        if not 0 <= minute_reset <= 59:
            raise ValueError("minute_   reset must be between 0 and 59 inclusive")

        now = datetime.now(tz=timezone) if timezone else datetime.now()
        shifted_now = now - timedelta(hours=shifthour)

        if (
            shifted_now.hour % 3 == 0
            and shifted_now.minute == minute_reset
            and shifted_now.second == 0
            and shifted_now.microsecond == 0
        ):
            return 0.0

        time = shifted_now.replace(minute=0, second=0, microsecond=0)
        hours_to_add = (-time.hour) % 3
        time += timedelta(hours=hours_to_add)
        time = time.replace(minute=minute_reset)

        if time <= shifted_now:
            time += timedelta(hours=3)

        actual_time = time + timedelta(hours=shifthour)
        return (actual_time - now).total_seconds()

    def __init__(
        self,
        cooldown: float = 0,
        max_cooldown: float = DAY_IN_SECONDS,
    ) -> None:
        """
        Initializes a Cooldown instance.
        If a cooldown time is provided, it sets the cooldown immediately.
        :param cooldown: The initial cooldown time in seconds.
        :param max_cooldown: The maximum cooldown time in seconds.
        """
        if cooldown:
            self.on_cooldown = True
            self.set_cooldown.start(cooldown)
        else:
            self.on_cooldown = False

        self.cooldown_completes: float = 0.0
        self.max_cooldown: float = max_cooldown

    def __bool__(self) -> bool:
        """
        Returns True if the cooldown is active, False otherwise.
        """
        return not self.on_cooldown

    def reset(self) -> None:
        self.on_cooldown = False

    def is_cooldown_less_than(self, tempo: float = HOUR_IN_SECONDS) -> bool:
        if self.get_current_cooldown() < tempo:
            return True

        return False

    @tasks.loop(count=1)
    async def set_cooldown(self, tempo: float = 0) -> None:
        """
        Sets the cooldown for the specified duration if one is provided
        else uses the maximum cooldown time.
        """

        if not tempo:
            tempo = self.max_cooldown

        self.on_cooldown = True
        self.cooldown_completes = time.time() + tempo
        await sleep(tempo)
        self.on_cooldown = False

    def get_current_cooldown(self) -> float:
        """
        Returns the current cooldown time remaining.
        """
        if not self.on_cooldown:
            return 0.0
        return self.cooldown_completes - time.time()
