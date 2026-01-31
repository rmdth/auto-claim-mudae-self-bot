"""Shared regular expression patterns for the Mudae bot."""

from datetime import timedelta
from re import MULTILINE
from re import compile as re_compile

from src.core.models import Roll

_FIND_TU_PATTERN = re_compile(r"\*\*=>\*\* \$tuarrange")

_CURRENT_ROLLS_IN_TU_PATTERN = re_compile(r"\*\*(\d+)\*\* roll")

_CURRENT_CLAIM_IN_TU_PATTERN = re_compile(r"__(.+)__.+\.")
_CURRENT_CLAIM_TIME_PATTERN = re_compile(r",\D+(\d+)?\D+(\d+).+min")

_DAILY_IN_TU_PATTERN = re_compile(r"\$daily\D+?(\d+)?\D+?(\d+)?\D+?$", flags=MULTILINE)
_RT_IN_TU_PATTERN = re_compile(r"\$rt\D+(\d+)?\D+(\d+)")
_DK_IN_TU_PATTERN = re_compile(r"\$dk\D+(\d+)?\D+(\d+)")

_KAKERA_IN_TU_PATTERN = re_compile(r"(\d+)%")
_KAKERA_COLOR_PATTERN = re_compile(r":(\w+):")
_KAKERA_DK_CONFIRMATION_PATTERN = re_compile(
    r"\*\*\+\d+\*\*<:kakera:469835869059153940>kakera"
)

_ROLL_KAKERA_PATTERN = re_compile(r"\*\*(.+)\*\*")
_ROLL_CHAR_PATTERN = re_compile(r"(.+)\s")
_ROLL_SERIES_PATTERN = re_compile(r"(.+)\s")
_ROLL_KEYS_PATTERN = re_compile(r"\(.+(\d).+\)")


def get_current_claim(content: str) -> list[str]:
    """
    Something means available else []
    """
    return _CURRENT_CLAIM_IN_TU_PATTERN.findall(content)


def list_to_timedelta(time_list: list[tuple[str, str]]) -> timedelta:
    time: timedelta = timedelta()
    if not time_list[0]:
        return time

    # Weird check because of how the regex works.
    if not time_list[0][0] == "":
        time = timedelta(hours=int(time_list[0][0]), minutes=int(time_list[0][1]))
        return time

    time = timedelta(minutes=int(time_list[0][1]))

    return time


def get_current_claim_time(content: str) -> list[tuple[str, str]]:
    """
    Always returns the time. Only use after checking curr_claim_status
    """
    return _CURRENT_CLAIM_TIME_PATTERN.findall(content)


def get_daily_cooldown(content: str) -> list[tuple[str, str]] | None:
    """
    [] means available IF len 2 (hours and minutes), len 1 (minutes)
    """
    poop = _DAILY_IN_TU_PATTERN.findall(content)
    if any(poop[0]):
        return poop
    return []


def get_rt_cooldown(content: str) -> list[tuple[str, str]]:
    """
    [] means available IF len 2 (hours and minutes), len 1 (minutes)
    """
    return _RT_IN_TU_PATTERN.findall(content)


def get_dk_cooldown(content: str) -> list[tuple[str, str]]:
    """
    [] means available IF len 2 (hours and minutes), len 1 (minutes)
    """
    return _DK_IN_TU_PATTERN.findall(content)


def get_curr_kakera_and_default_cost(content: str) -> list[tuple[str, str]]:
    """
    [0] = Kakera Value, [1] = Kakera Cost. None means BIGGG EROOR!!!
    """
    return _KAKERA_IN_TU_PATTERN.findall(content)


def get_current_rolls(content: str) -> list[tuple[str, str]]:
    return _CURRENT_ROLLS_IN_TU_PATTERN.findall(content)


def get_kakera_cost(default_cost: int) -> int:
    return default_cost
