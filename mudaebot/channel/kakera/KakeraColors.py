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
    def get_priority(color: str) -> int:
        return KakeraColors._PRIORITY.get(color, KakeraColors._DEFAULT_PRIORITY)

    @staticmethod
    def sort_by_highest_value(kakeras: list) -> None:
        kakeras.sort(
            key=lambda message: KakeraColors.get_priority(
                message.components[0].children[0].emoji.name
            )
        )
