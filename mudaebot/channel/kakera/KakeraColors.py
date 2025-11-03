class KakeraColors:
    _PRIORITY: dict[str, int] = {
        "": 8,
        "T": 7,
        "G": 6,
        "Y": 5,
        "O": 4,
        "R": 3,
        "W": 2,
        "L": 1,
        "P": 0,
    }
    _DEFAULT_PRIORITY: int = _PRIORITY[""] + 1

    def __init__(self, color: str = "") -> None:
        self.color = color.upper()

    def priority(self) -> int:
        return self._PRIORITY.get(self.color, self._DEFAULT_PRIORITY)

    def __lt__(self, other: "KakeraColors") -> bool:
        return self.priority() < other.priority()
