import logging
from datetime import timedelta
from re import MULTILINE
from re import compile as re_compile
from typing import Any

from discord import Message

from src.core.models import Cooldown, KakeraUnit, Roll

logger = logging.getLogger(__name__)

_KAKERA_DK_CONFIRMATION_PATTERN = re_compile(
    r"\*\*\+\d+\*\*<:kakera:469835869059153940>kakera"
)


_FIND_TU_PATTERN = re_compile(r"\*\*=>\*\* \$tuarrange")


def is_tu_message(content: str) -> bool:
    logger.debug("TU message received is:  %s", content)
    return bool(_FIND_TU_PATTERN.search(content))


_CURRENT_CLAIM_IN_TU_PATTERN = re_compile(r"__(.+)__.+\.")


def available_claim(content: str) -> bool:
    return bool(_CURRENT_CLAIM_IN_TU_PATTERN.findall(content))


_CURRENT_CLAIM_TIME_PATTERN = re_compile(r",\D+(\d+)?\D+(\d+).+min")


def get_claim_timedelta(content: str) -> timedelta:
    """
    Always returns the time. Only use after checking curr_claim_status
    """
    hours, minutes = _CURRENT_CLAIM_TIME_PATTERN.findall(content)[0]

    return timedelta(hours=int(hours), minutes=int(minutes))


_DAILY_IN_TU_PATTERN = re_compile(r"\$daily\D+?(\d+)?\D+?(\d+)?\D+?$", flags=MULTILINE)


def get_daily_timedelta(content: str) -> timedelta:
    """
    [] means available IF len 2 (hours and minutes), len 1 (minutes)
    """
    hours, minutes = _DAILY_IN_TU_PATTERN.findall(content)[0]

    return timedelta(hours=int(hours), minutes=int(minutes))


_RT_IN_TU_PATTERN = re_compile(r"\$rt\D+(\d+)?\D+(\d+)")


def get_rt_timedelta(content: str) -> timedelta:
    """
    [] means available IF len 2 (hours and minutes), len 1 (minutes)
    """
    hours, minutes = _RT_IN_TU_PATTERN.findall(content)[0]

    return timedelta(hours=int(hours), minutes=int(minutes))


_DK_IN_TU_PATTERN = re_compile(r"\$dk\D+(\d+)?\D+(\d+)")


def get_dk_timedelta(content: str) -> timedelta:
    hours, minutes = _DK_IN_TU_PATTERN.findall(content)[0]

    return timedelta(hours=int(hours), minutes=int(minutes))


_KAKERA_IN_TU_PATTERN = re_compile(r"(\d+)%")


def get_kakera_and_kakera_default_cost(content: str) -> tuple[int, int]:
    kakera_value, kakera_cost, _ = _KAKERA_IN_TU_PATTERN.findall(content)[0]

    return int(kakera_value), int(kakera_cost)


_CURRENT_ROLLS_IN_TU_PATTERN = re_compile(r"\*\*(\d+)\*\* roll")


def get_rolls(content: str) -> int:
    return int(_CURRENT_ROLLS_IN_TU_PATTERN.findall(content)[0])


def get_tu_information(content: str, current_time: float) -> dict[str, Any]:
    kakera_value, kakera_cost = get_kakera_and_kakera_default_cost(content)
    return {
        "daily": Cooldown(get_daily_timedelta(content).total_seconds() + current_time),
        "rt": Cooldown(get_rt_timedelta(content).total_seconds() + current_time),
        "dk": Cooldown(get_dk_timedelta(content).total_seconds() + current_time),
        "kakera_value": kakera_value,
        "kakera_cost": kakera_cost,
        "rolls": get_rolls(content),
    }


def get_kakera_cost(
    embed: dict, kakera_cost: int, color: str, key_amount: int, user_name: str
) -> int:
    cost = kakera_cost
    if key_amount > 9 and user_name in embed["footer"]["text"]:
        cost = cost // 2
    elif color == "kakeraP":
        cost = 0
    return cost


def parse_message(
    embed: dict,
    roll_type: str,
    kakera_cost: int,
    user_name: str,
    message: Any,
) -> Roll | KakeraUnit | None:
    if roll_type == "roll":
        return create_roll(embed, message)
    elif roll_type == "kakera":
        return create_kakera_unit(embed, kakera_cost, user_name, message)
    return None


_ROLL_KAKERA_PATTERN = re_compile(r"\*\*(.+)\*\*")
_ROLL_SERIES_PATTERN = re_compile(r"(.+)\s")
_ROLL_KEYS_PATTERN = re_compile(r"\(.+(\d).+\)")


def create_roll(embed: dict, message: Any) -> Roll:
    return Roll(
        name=embed["author"]["name"],
        series=_ROLL_SERIES_PATTERN.findall(embed["description"])[0],
        kakera_value=int(
            _ROLL_KAKERA_PATTERN.findall(embed["description"])[0].replace(".", "")
        ),
        key_amount=int((_ROLL_KEYS_PATTERN.findall(embed["description"]) or [0])[0]),
        message=message,
    )


_KAKERA_COLOR_PATTERN = re_compile(r":(\w+):")


def create_kakera_unit(
    embed: dict, kakera_cost: int, user_name: str, message: Message
) -> KakeraUnit:
    color = message.components[0].children[0].emoji.name
    logger.debug("kakera color is: %s", color)
    cost = get_kakera_cost(
        embed,
        kakera_cost,
        color,
        int(_ROLL_KEYS_PATTERN.findall(embed["description"])[0]),
        user_name,
    )
    return KakeraUnit(
        claim_cost=cost,
        color=color,
        message=message,
    )
