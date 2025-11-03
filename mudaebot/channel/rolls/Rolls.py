from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rolling.Rolling import Rolling


from ...patterns import ROLL_CHAR_PATTERN, ROLL_KAKERA_PATTERN, KAKERA_KEYS_PATTERN


class Rolls:
    get_kakera_pattern = ROLL_KAKERA_PATTERN
    get_char_pattern = ROLL_CHAR_PATTERN
    get_kakera_keys_pattern = KAKERA_KEYS_PATTERN

    @staticmethod
    def get_roll_name(message) -> str:
        return (
            message.embeds[0].to_dict()["author"]["name"]
            if message.embeds[0].to_dict()["author"]["name"]
            else ""
        )

    @staticmethod
    def get_roll_series(message) -> str:
        return (
            Rolls.get_char_pattern.findall(message.embeds[0].to_dict()["description"])[
                0
            ]
            if Rolls.get_char_pattern.findall(
                message.embeds[0].to_dict()["description"]
            )
            else ""
        )

    @staticmethod
    def get_roll_name_n_series(message) -> str:
        return Rolls.get_roll_name(message) + " - " + Rolls.get_roll_series(message)

    @staticmethod
    def get_roll_kakera(message) -> int:
        return int(
            Rolls.get_kakera_pattern.findall(
                message.embeds[0].to_dict()["description"]
            )[0]
        )

    @staticmethod
    def get_roll_kakera_keys(message) -> int:
        return int(
            Rolls.get_kakera_keys_pattern.findall(
                message.embeds[0].to_dict()["description"]
            )[0]
            if Rolls.get_kakera_keys_pattern.findall(
                message.embeds[0].to_dict()["description"]
            )
            else 0
        )

    @staticmethod
    async def is_minimum_kakera(message, value) -> bool:
        return Rolls.get_roll_kakera(message) >= value

    @staticmethod
    async def was_claimed(message) -> bool:
        return message.embeds[0].to_dict()["color"] == 6753288

    @classmethod
    async def sort_by_highest_kakera(cls, rolls: list) -> None:
        rolls.sort(reverse=True, key=lambda roll: cls.get_roll_kakera(roll))

    def __init__(
        self,
        rolling,
        wish_list,
        wish_series,
        rolls: int = 0,
        max_rolls: int = 8,
        min_kakera_value: int = 0,
    ) -> None:
        """
        :param rolling: The Rolling class instance
        :param wish_list: The list of wished rolls
        :param wish_series: The list of wished series
        :param rolls: The number of rolls to perform, default = 0
        :param max_rolls: The maximum number of rolls to perform, default = 8
        """
        self._rolling: Rolling = rolling
        self._wish_list: list[str] = wish_list
        self._wish_series: list[str] = wish_series
        self._rolls: int = rolls
        self._max_rolls: int = max_rolls
        self._min_kakera_value: int = min_kakera_value

    @property
    def rolls(self) -> int:
        return self._rolls

    @property
    def max_rolls(self) -> int:
        return self._max_rolls

    @property
    def rolling(self) -> Rolling:
        return self._rolling

    @property
    def wish_list(self) -> list[str]:
        return self._wish_list

    @property
    def wish_series(self) -> list[str]:
        return self._wish_series

    @property
    def min_kakera_value(self) -> int:
        return self._min_kakera_value

    def __isub__(self, one: int) -> Rolls:
        self._rolls = self._rolls - one if self._rolls > 0 else 0
        return self

    def reset_rolls(self) -> None:
        self._rolls = self._max_rolls
