from re import MULTILINE, Pattern
from re import compile as re_compile
from time import time

from src.bot.shared.domain import ParsedTimeUpdate

_CURRENT_CLAIM_PATTERN = re_compile(r"__(.+)__.+\.")
_CURRENT_CLAIM_TIME_PATTERN = re_compile(r",\D+(\d+)?\D+(\d+).+min")
_DAILY_IN_TU_PATTERN = re_compile(r"\$daily\D+?(\d+)?\D+?(\d+)?\D+?$", flags=MULTILINE)


def is_tu_message(content: str) -> bool:
    return "**=>** $tuarrange" in content


def has_current_claim(content: str) -> bool:
    return bool(_CURRENT_CLAIM_PATTERN.findall(content))


def get_time_in(pattern: Pattern, content: str) -> float:
    hours, minutes = pattern.findall(content)[0]
    return float(hours or 0) * 3600 + float(minutes or 0) * 60 + time()


def get_claim_in(content: str) -> float:
    if has_current_claim(content):
        return 0
    return get_time_in(_CURRENT_CLAIM_TIME_PATTERN, content)


def get_daily_in(content: str) -> float:
    return get_time_in(_DAILY_IN_TU_PATTERN, content)


_RT_IN_TU_PATTERN = re_compile(r"\$rt[ (:.a-zA-Z*]+(\d+)?[ (:.a-zA-Z*]+(\d+)?")


def get_rt_in(content: str) -> float:
    return get_time_in(_RT_IN_TU_PATTERN, content)


_DK_IN_TU_PATTERN = re_compile(r"\$dk[ (:.a-zA-Z*]+(\d+)?[ (:.a-zA-Z*]+(\d+)?")


def get_dk_in(content: str) -> float:
    return get_time_in(_DK_IN_TU_PATTERN, content)


_KAKERA_IN_TU_PATTERN = re_compile(r"(\d+)%")


def get_curr_kakera_power_and_cost(content: str) -> tuple[int, int]:
    curr_kakera_power, kakera_claim_cost, _ = _KAKERA_IN_TU_PATTERN.findall(content)
    return int(curr_kakera_power), int(kakera_claim_cost)


_CURRENT_ROLLS_IN_TU_PATTERN = re_compile(r"\*\*(\d+)\*\* roll")


def get_rolls(content: str) -> int:
    return int(_CURRENT_ROLLS_IN_TU_PATTERN.findall(content)[0])


def get_tu_information(content: str) -> ParsedTimeUpdate:
    curr_kakera_power, kakera_claim_cost = get_curr_kakera_power_and_cost(content)
    return ParsedTimeUpdate(
        get_claim_in(content),
        get_daily_in(content),
        get_rt_in(content),
        get_dk_in(content),
        curr_kakera_power,
        kakera_claim_cost,
        get_rolls(content),
    )
