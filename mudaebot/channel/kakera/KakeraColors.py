from ...patterns import KAKERA_COLOR_PATTERN


class KakeraColors:
    _PRIORITY: dict[str, int] = {
        "kakera": 9,
        "kakeraT": 8,
        "kakeraG": 7,
        "kakeraY": 6,
        "kakeraO": 5,
        "kakeraR": 4,
        "kakeraW": 3,
        "kakeraL": 2,
        "kakeraP": 1,
    }
    _DEFAULT_PRIORITY: int = _PRIORITY["kakera"] + 1

    @staticmethod
    def get_color(emoji_name: str) -> str:
        return KAKERA_COLOR_PATTERN.findall(emoji_name)[0]

    def __init__(self, color: str = "kakera") -> None:
        self._color: str = color

    @property
    def color(self) -> str:
        return self._color

    def priority(self) -> int:
        return self._PRIORITY.get(self._color, self._DEFAULT_PRIORITY)

    def __lt__(self, other: "KakeraColors") -> bool:
        return self.priority() < other.priority()
