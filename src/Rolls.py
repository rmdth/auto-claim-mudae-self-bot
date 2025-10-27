from re import compile as re_compile
from .Rolling import Rolling


class Rolls:
    # get_series_pattern = re_compile(r"") TODO
    get_kakera_pattern = re_compile(r"\*\*(\d+)\*\*")

    def __init__(self, rolling, rolls: int = 0, max_rolls: int = 8):
        """
        :param rolling: The Rolling class instance
        :param rolls: The number of rolls to perform, default = 0
        :param max_rolls: The maximum number of rolls to perform, default = 8
        """
        self._rolls: int = max_rolls if not rolls else rolls
        self._max_rolls: int = max_rolls
        self._rolling: Rolling = rolling

    @property
    def rolls(self) -> int:
        return self._rolls

    @property
    def max_rolls(self) -> int:
        return self._max_rolls

    @property
    def rolling(self) -> Rolling:
        return self._rolling
        return self._rolling

    def __isub__(self) -> int:
        return self._rolls - 1 if self._rolls > 0 else 0

    @staticmethod
    def get_roll_name(message) -> str:
        return message.embeds[0].to_dict()["author"]["name"]

    @staticmethod
    def get_roll_series(message) -> str:
        return message.embeds[0].to_dict()["author"]["description"]

    @staticmethod
    def get_roll_name_n_series(message) -> str:
        return Rolls.get_roll_name(message) + " - " + Rolls.get_roll_series(message)

    @staticmethod
    def get_roll_kakera(message) -> int:
        return Rolls.get_kakera_pattern.findall(
            message.embeds[0].to_dict()["description"]
        )[0]

    @classmethod
    async def sort_by_highest_kakera(cls, rolls: list) -> None:
        rolls.sort(reverse=True, key=lambda roll: cls.get_roll_kakera(roll))
