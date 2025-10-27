import time
from asyncio import sleep
from datetime import datetime, tzinfo

DAY_IN_SECONDS = 86400


class Cooldown:
    async def __init__(self, cooldown: float = 0, max_cooldown: float = DAY_IN_SECONDS):
        """
        Initializes a Cooldown instance.
        If a cooldown time is provided, it sets the cooldown immediately.
        :param cooldown: The initial cooldown time in seconds.
        :param max_cooldown: The maximum cooldown time in seconds.
        """

        if cooldown:
            await self.set_cooldown(cooldown)

        self.on_cooldown: bool = False
        self.cooldown_time: float = 0.0
        self.max_cooldown: float = max_cooldown

    def __bool__(self) -> bool:
        """
        Returns True if the cooldown is active, False otherwise.
        """
        return self.on_cooldown

    @staticmethod
    def last_hour(minute_reset: int, shifthour: int, time_zone: tzinfo) -> bool:
        time: datetime = datetime.now(tz=time_zone)

        adjusted_hour = time.hour - shifthour

        # 3 ofc is 180 minutes
        return (
            # True If the hour is divisible by 3 AND the minute is greater than the reset time
            not adjusted_hour % 3
            and time.minute > minute_reset
        ) or (
            # - 1 Just so we know IF is after the last hour AND the minute is less than the reset time
            not (adjusted_hour - 1) % 3
            and time.minute < minute_reset
        )

    async def set_cooldown(self, tempo: float = 0) -> None:
        """
        Sets the cooldown for the specified duration if one is provided
        else uses the maximum cooldown time.
        """

        if not tempo:
            tempo = self.max_cooldown

        self.on_cooldown = True
        self.cooldown_time = time.time() + tempo
        await sleep(tempo)
        self.on_cooldown = False

    def get_current_cooldown(self) -> float:
        """
        Returns the current cooldown time remaining.
        """
        if not self.on_cooldown:
            return 0.0
        return self.cooldown_time - time.time()
